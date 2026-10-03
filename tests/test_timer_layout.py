import html
import re
from functools import partial
from html.parser import HTMLParser

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_foundation import login
from test_foundation import setup as setup
from test_recordings import FILENAME, ROOT, MovieReceiver, movie_row
from test_timers import GROUP, REFERENCE, form_values, input_value, timer_row

from e2web.db import Grant
from e2web.openwebif import OpenWebifClient, bouquet_reference
from e2web.security import now

TV_SECOND = GROUP.replace("test.tv", "second.tv")
RADIO_GROUP = GROUP.replace("1:7:1:", "1:7:2:").replace("test.tv", "radio.radio")
SECOND = "1:0:19:283E:3FB:1:C00000:0:0:0:"
RADIO = "1:0:2:2840:3FB:1:C00000:0:0:0:"


class SelectParser(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.selects = {}
        self.current = None
        self.option = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "select":
            self.current = attrs.get("name")
            self.selects[self.current] = []
        elif tag == "option" and self.current:
            self.option = {
                "value": attrs.get("value", ""),
                "selected": "selected" in attrs,
                "text": "",
            }
            self.selects[self.current].append(self.option)

    def handle_endtag(self, tag):
        if tag == "select":
            self.current = None
        elif tag == "option":
            self.option = None

    def handle_data(self, data):
        if self.option is not None:
            self.option["text"] += data


class SelectorReceiver(MovieReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.paths = [ROOT + "Andere/", ROOT]
        self.catalog = {
            "tv": [
                {"reference": GROUP, "name": "Fernsehen"},
                {"reference": TV_SECOND, "name": "Weitere TV-Sender"},
            ],
            "radio": [{"reference": RADIO_GROUP, "name": "Radio"}],
        }
        self.channels = {
            GROUP: [
                {"reference": "1:64:1:0:0:0:0:0:0:0:", "name": "Gruppenüberschrift"},
                {"reference": REFERENCE, "name": "Das Erste HD"},
                {"reference": SECOND, "name": "ZDF HD"},
                {"reference": TV_SECOND, "name": "Untergruppe"},
            ],
            TV_SECOND: [{"reference": SECOND, "name": "ZDF HD"}],
            RADIO_GROUP: [{"reference": RADIO, "name": "Deutschlandfunk & Kultur"}],
        }
        self.movie_queries = []

    def __call__(self, request):
        if request.url.path.endswith("movielist"):
            self.movie_queries.append(request.url.params.get("dirname"))
        if request.url.path.endswith("getservices"):
            self.requests.append((request.method, request.url.path, request.url.host))
            if self.xml and request.url.path.startswith("/api/"):
                return httpx.Response(404)
            reference = request.url.params.get("sRef")
            rows = (
                self.catalog["tv"]
                if not reference
                else self.catalog["radio"]
                if reference == bouquet_reference("radio")
                else self.channels.get(reference, [])
            )
            if self.xml:
                from xml.etree.ElementTree import Element, SubElement, tostring

                root = Element("e2servicelist")
                for entry in rows:
                    row = SubElement(root, "e2service")
                    SubElement(row, "e2servicereference").text = entry["reference"]
                    SubElement(row, "e2servicename").text = entry["name"]
                return httpx.Response(200, content=tostring(root))
            return httpx.Response(
                200,
                json={
                    "services": [
                        {"servicereference": r["reference"], "servicename": r["name"]} for r in rows
                    ]
                },
            )
        response = super().__call__(request)
        if self.xml and self.conflict and request.method == "POST":
            return httpx.Response(
                200,
                text="<e2simplexmlresult><e2state>False</e2state>"
                "<e2statetext>Timer Conflict</e2statetext></e2simplexmlresult>",
            )
        return response


def install_selector(app, **kwargs):
    box = SelectorReceiver(**kwargs)
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    return box


@pytest.mark.parametrize("xml", [False, True])
def test_direct_timer_form_has_tv_radio_bouquets_first_channel_and_real_default(setup, xml):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        timer_page = client.get("/timer")
        assert 'href="/timer/new?receiver_id=1"' in timer_page.text
        page = client.get("/timer/new")
        assert page.status_code == 200
        selects = SelectParser(page.text).selects
        assert [r["value"] for r in selects["bouquet"]] == [GROUP, TV_SECOND, RADIO_GROUP]
        assert [r["value"] for r in selects["reference"]] == [REFERENCE, SECOND]
        assert selects["bouquet"][0]["selected"] and selects["reference"][0]["selected"]
        assert [r["value"] for r in selects["directory"] if r["selected"]] == [ROOT]
        assert all(r["value"] for r in selects["directory"])
        assert "Standardpfad des Receivers" not in page.text
        assert input_value(page, "name") == "Das Erste HD"
        assert 'optgroup label="TV"' in page.text and 'optgroup label="Radio"' in page.text
        assert not box.writes
        form = form_values(page)
        assert client.post("/timer/save", data=form, follow_redirects=False).status_code == 303
        assert box.writes[0][1]["sRef"] == REFERENCE
        assert box.writes[0][1]["dirname"] == ROOT


@pytest.mark.parametrize("xml", [False, True])
def test_direct_radio_selection_is_read_only_until_explicit_save_and_keeps_conflict_values(
    setup, xml
):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer/new")
        result = client.get("/timer/channels", params={"receiver_id": 1, "bouquet": RADIO_GROUP})
        assert result.status_code == 200 and result.json()["services"] == box.channels[RADIO_GROUP]
        assert not box.writes
        form = form_values(
            page,
            bouquet=RADIO_GROUP,
            reference=RADIO,
            name="Eigene Radiosendung",
            description="Eine Beschreibung",
            weekdays=["1", "3"],
        )
        box.conflict = True
        conflict = client.post("/timer/save", data=form)
        assert conflict.status_code == 409
        assert "Timerkonflikt" in conflict.text
        assert input_value(conflict, "name") == "Eigene Radiosendung"
        assert "Eine Beschreibung" in conflict.text
        selects = SelectParser(conflict.text).selects
        assert [r["value"] for r in selects["bouquet"] if r["selected"]] == [RADIO_GROUP]
        assert [r["value"] for r in selects["reference"] if r["selected"]] == [RADIO]
        box.conflict = False
        fresh = {**form, "action_token": input_value(conflict, "action_token")}
        assert client.post("/timer/save", data=fresh, follow_redirects=False).status_code == 303
        assert box.writes[-1][1]["sRef"] == RADIO
        assert box.writes[-1][1]["repeated"] == "10"


@pytest.mark.parametrize("bad", ["bouquet", "channel", "marker", "changed"])
def test_direct_timer_selection_is_rechecked_before_write(setup, bad):
    _, _, app = setup
    box = install_selector(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        form = form_values(client.get("/timer/new"), bouquet=GROUP, reference=REFERENCE)
        if bad == "bouquet":
            form["bouquet"] = "forged"
        elif bad == "channel":
            form["reference"] = RADIO
        elif bad == "marker":
            form["reference"] = box.channels[GROUP][0]["reference"]
        else:
            box.channels[GROUP] = []
        assert client.post("/timer/save", data=form).status_code in {400, 409}
        assert not box.writes


@pytest.mark.parametrize("empty", ["first", "all"])
def test_empty_bouquets_render_without_creating_timer(setup, empty):
    _, _, app = setup
    box = install_selector(app)
    if empty == "first":
        box.channels[GROUP] = []
    else:
        box.catalog = {"tv": [], "radio": []}
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer/new")
        assert page.status_code == 200 and "Keine aufnehmbaren Sender verfügbar" in page.text
        assert "disabled>Timer speichern" in page.text
        assert not box.writes


def test_bouquet_endpoint_obeys_receiver_binding_and_read_permissions(setup):
    _, engine, app = setup
    box = install_selector(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert (
            client.get("/timer/channels", params={"receiver_id": 2, "bouquet": GROUP}).status_code
            == 409
        )
        assert (
            client.get(
                "/timer/channels", params={"receiver_id": 1, "bouquet": "forged"}
            ).status_code
            == 409
        )
        with Session(engine) as db:
            db.get(Grant, (2, 1)).can_write = False
            db.commit()
        assert client.get("/timer/new").status_code == 403
        assert (
            client.get("/timer/channels", params={"receiver_id": 1, "bouquet": GROUP}).status_code
            == 403
        )
        assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
def test_timer_blocks_counts_and_file_rows_with_sizes_update(setup, xml):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    box.movies.append(
        movie_row(
            filename=ROOT + "other.ts",
            serviceref="1:0:0:0:0:0:0:0:0:0:" + ROOT + "other.ts",
            filesize=2 * 1024**3,
        )
    )
    box.timers = [
        timer_row(
            state=2, begin=now() - 100, end=now() + 100, filename=FILENAME.removesuffix(".ts")
        ),
        timer_row(
            name="Zweiter laufender Timer",
            state=2,
            begin=now() - 200,
            end=now() + 200,
            filename=ROOT + "other",
        ),
        timer_row(state=1, begin=now() + 2000, end=now() + 3000),
        timer_row(disabled=1, begin=now() + 4000, end=now() + 5000),
        timer_row(state=3, begin=now() - 5000, end=now() - 4000, filename=ROOT + "other.ts"),
    ]
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        assert "Laufend (2)" in page.text and "Anstehend (2)" in page.text
        assert "Erledigte Timer (1)" in page.text
        assert "Nachrichten + A &amp; B.ts" in page.text and "1.0 GiB" in page.text
        assert "2.0 GiB" in page.text
        assert "Noch keine Datei vorhanden" not in page.text
        assert page.text.count('class="recording-file-row') == 2
        assert page.text.count('class="recording-file-row recording-active-row"') == 2
        assert len([p for p in box.movie_queries if p == ROOT]) == (2 if xml else 1)
        box.movies[0]["filesize"] *= 3
        box.timers[1]["state"] = 3
        page = client.get("/timer?live_receiver=2")
        assert (
            "3.0 GiB" in page.text
            and "Laufend (1)" in page.text
            and "Erledigte Timer (2)" in page.text
        )
        assert "other.ts" not in page.text and "2.0 GiB" not in page.text
        assert page.text.count('class="recording-file-row') == 1


@pytest.mark.parametrize("xml", [False, True])
def test_nonrunning_timer_files_hidden_without_recording_queries_and_follow_status(setup, xml):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    box.timers = [
        timer_row(name="Serientimer", repeated=127, filename=FILENAME, state=0),
        timer_row(
            name="Vorbereitet",
            filename=ROOT + "prepared",
            state=1,
            begin=now() + 8000,
            end=now() + 9000,
        ),
        timer_row(
            name="Deaktiviert",
            filename=ROOT + "disabled",
            disabled=1,
            begin=now() + 10000,
            end=now() + 11000,
        ),
        timer_row(
            name="Erledigt",
            filename=ROOT + "finished",
            state=3,
            begin=now() - 2000,
            end=now() - 1000,
        ),
    ]
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        assert page.status_code == 200
        assert 'class="recording-file-row' not in page.text
        assert "Noch keine Datei vorhanden" not in page.text
        assert "Nachrichten + A &amp; B.ts" not in page.text
        assert not box.movie_queries
        box.timers[0]["state"] = 2
        page = client.get("/timer?live_receiver=2")
        assert "Nachrichten + A &amp; B.ts" in page.text and "1.0 GiB" in page.text
        assert page.text.count('class="recording-file-row') == 1
        box.timers[0]["state"] = 0  # A repeating timer returns to its next occurrence.
        box.movie_queries.clear()
        page = client.get("/timer?live_receiver=2")
        assert 'class="recording-file-row' not in page.text
        assert "Nachrichten + A &amp; B.ts" not in page.text
        assert not box.movie_queries


def test_timer_file_failures_do_not_hide_timer_actions_or_guess_size(setup):
    _, _, app = setup
    box = install_selector(app)
    box.timers = [timer_row(state=2, filename=ROOT + "missing")]
    box.movies = []
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        assert "missing.ts" in page.text and "Unbekannt" in page.text
        assert "Bearbeiten</a>" in page.text
        box.timers[0]["filename"] = "../invalid"
        box.movie_queries.clear()
        page = client.get("/timer")
        assert not box.movie_queries and "Bearbeiten</a>" in page.text


def test_interface_has_no_informal_address_or_removed_sender_sentence(setup):
    _, _, app = setup
    install_selector(app)
    with TestClient(app) as client:
        login_page = client.get("/login")
        assert "deinem" not in login_page.text
        login(client)
        for path in [
            "/timer",
            "/timer/new",
            "/sender",
            "/aufnahmen",
            "/admin/users",
            "/admin/receivers",
        ]:
            response = client.get(path)
            assert response.status_code == 200
            text = html.unescape(re.sub(r"<[^>]*>", " ", response.text))
            assert not re.search(r"\b(?:du|dich|dein\w*|wähle|prüfe|öffne|lege)\b", text, re.I)
        assert "Wähle eine Liste, um ihre Sender anzuzeigen." not in client.get("/sender").text


@pytest.mark.parametrize("xml", [False, True])
def test_timer_file_size_with_receiver_directory_alias_and_multiple_files(setup, xml):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    box.timers = [
        timer_row(state=2, filename=FILENAME.replace("/media/hdd/", "/hdd/").removesuffix(".ts"))
    ]
    original_factory = app.state.client_factory

    def alias_transport(request):
        if request.url.path.endswith("movielist"):
            path = request.url.params.get("dirname", "")
            if path.startswith("/hdd/"):
                request = httpx.Request(
                    request.method,
                    request.url.copy_set_param("dirname", "/media" + path),
                    headers=request.headers,
                )
        return box(request)

    app.state.client_factory = partial(
        OpenWebifClient, transport=httpx.MockTransport(alias_transport)
    )
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        assert "1.0 GiB" in page.text and "Nachrichten + A &amp; B.ts" in page.text
        assert not box.writes
    app.state.client_factory = original_factory


def test_empty_timer_sections_keep_counts_and_zap_has_no_file(setup):
    _, _, app = setup
    box = install_selector(app)
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        assert "Laufend (0)" in page.text and "Anstehend (0)" in page.text
        assert "Derzeit läuft keine Aufnahme." in page.text
        box.timers = [timer_row(state=2, justplay=1, filename=ROOT + "ignored")]
        box.movie_queries.clear()
        page = client.get("/timer")
        assert "Umschalt-Timer – keine Aufnahmedatei" in page.text
        assert "Laufend (1)" in page.text and not box.movie_queries


def test_timer_file_metadata_outage_keeps_list_and_actions(setup):
    _, _, app = setup
    box = install_selector(app)
    box.timers = [timer_row(state=2, filename=ROOT + "live")]

    def offline(request):
        if request.url.path.endswith("movielist"):
            return httpx.Response(503)
        return box(request)

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(offline))
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        assert page.status_code == 200
        assert "Dateigrößen konnten nicht vollständig geladen werden." in page.text
        assert "Bearbeiten</a>" in page.text and 'action="/timer/delete"' in page.text
        assert "live.ts" in page.text and "Unbekannt" in page.text
        assert "Timerliste nicht erreichbar" not in page.text


@pytest.mark.parametrize("xml", [False, True])
def test_missing_real_timer_default_requires_path_choice_without_assuming_first_bookmark(
    setup, xml
):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    box.paths = [ROOT]

    def no_default(request):
        if request.url.path.endswith("getcurrlocation"):
            return httpx.Response(503)
        response = box(request)
        if not xml and request.url.path.endswith(("timerlist", "getlocations")):
            data = response.json()
            data["default"] = ""
            return httpx.Response(200, json=data)
        return response

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(no_default))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer/new")
        assert page.status_code == 200
        assert "Der Standardaufnahmepfad konnte nicht ermittelt werden." in page.text
        paths = SelectParser(page.text).selects["directory"]
        assert [row["value"] for row in paths if row["selected"]] == [""]
        assert any(row["value"] == ROOT for row in paths)
        values = form_values(page)
        values["directory"] = ""
        rejected = client.post("/timer/save", data=values)
        assert rejected.status_code == 400
        assert not box.writes
        saved = client.post(
            "/timer/save", data={**form_values(rejected), "directory": ROOT}, follow_redirects=False
        )
        assert saved.status_code == 303
        assert box.writes[-1][1]["dirname"] == ROOT
