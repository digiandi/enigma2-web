import copy
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_foundation import login
from test_foundation import setup as setup
from test_timer_layout import (
    GROUP,
    RADIO,
    RADIO_GROUP,
    SECOND,
    SelectParser,
    install_selector,
)
from test_timers import REFERENCE, existing_url, form_values, input_value, timer_row

from e2web.db import Grant, TimerAction
from e2web.security import token_hash
from e2web.timer_selection import COPY_SOURCE


def copy_url(row, **kwargs):
    return existing_url("/timer/new", row, **kwargs) + "&copy=1"


def copied_values(page, **changes):
    selects = SelectParser(page.text).selects
    values = {
        key: next(row["value"] for row in selects[key] if row["selected"])
        for key in ("bouquet", "reference", "directory", "afterevent")
    }
    values["disabled"] = "on" if re.search(r'name="disabled"[^>]*checked', page.text) else ""
    values["justplay"] = "on" if re.search(r'name="justplay"[^>]*checked', page.text) else ""
    values["weekdays"] = re.findall(r'name="weekdays" value="(\d)" checked', page.text)
    return form_values(page, **{**values, **changes})


def local_value(timestamp):
    return datetime.fromtimestamp(timestamp, ZoneInfo("Europe/Berlin")).strftime(
        "%Y-%m-%dT%H:%M:%S"
    )


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize("radio", [False, True])
def test_copy_prefills_source_and_saves_an_independent_editable_timer(setup, xml, radio):
    _, engine, app = setup
    box = install_selector(app, xml=xml)
    source = timer_row(
        serviceref=RADIO if radio else REFERENCE,
        servicename="Deutschlandfunk & Kultur" if radio else "Das Erste HD",
        name='Vorlage <Plan> "Titel"',
        description="Beschreibung\nZweite Zeile & Details",
        dirname="/media/hdd/movie/Eigener Ordner/",
        repeated=21,
        disabled=1,
        justplay=1,
        tags="Musik Nachrichten e2web-owner-admin e2web-owner-alt",
    )
    box.timers = [source]
    original = copy.deepcopy(source)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get(copy_url(source))
        assert page.status_code == 200 and "Timer erstellen" in page.text
        assert "Timer bearbeiten" not in page.text
        assert input_value(page, "name") == source["name"]
        assert "Beschreibung\nZweite Zeile &amp; Details" in page.text
        assert input_value(page, "begin") == local_value(source["begin"])
        assert input_value(page, "end") == local_value(source["end"])
        values = copied_values(page)
        assert values["reference"] == source["serviceref"]
        assert values["bouquet"] == (RADIO_GROUP if radio else GROUP)
        assert values["directory"] == source["dirname"]
        assert values["weekdays"] == ["0", "2", "4"]
        assert values["disabled"] == values["justplay"] == "on"
        assert values["afterevent"] == "3"
        with Session(engine) as db:
            action = db.get(TimerAction, token_hash(values["action_token"]))
            payload = json.loads(action.payload)
            assert action.kind == "add" and payload["copying"]
            assert "identity" not in payload and "fingerprint" not in payload
            assert payload["settings"]["tags"] == "Musik Nachrichten"
            assert payload["settings"]["always_zap"] == "1"
            assert payload["settings"]["pipzap"] == "0"
        assert not box.writes and source == original
        values.update(
            name="Neue Sendung",
            description="Neue Beschreibung",
            begin=local_value(source["begin"] + 7200),
            end=local_value(source["end"] + 9000),
            bouquet=GROUP if radio else RADIO_GROUP,
            reference=SECOND if radio else RADIO,
            directory="/media/hdd/movie/",
            weekdays=["1", "3"],
            disabled="",
            justplay="",
            afterevent="1",
        )
        assert client.post("/timer/save", data=values, follow_redirects=False).status_code == 303
        assert len(box.writes) == 1 and box.writes[0][0] == "timeradd"
        params = box.writes[0][1]
        assert params["sRef"] == values["reference"]
        assert params["name"] == values["name"] and params["description"] == values["description"]
        assert params["begin"] == str(source["begin"] + 7200)
        assert params["end"] == str(source["end"] + 9000)
        assert params["dirname"] == values["directory"] and params["repeated"] == "10"
        assert params["disabled"] == params["justplay"] == "0" and params["afterevent"] == "1"
        assert params["tags"] == "Musik Nachrichten e2web-owner-user"
        assert params["always_zap"] == "1" and params["pipzap"] == "0"
        assert (
            not {"channelOld", "beginOld", "endOld", "deleteOldOnSave", "filename", "state"}
            & params.keys()
        )
        if not xml:
            assert params["autoadjust"] == params["allow_duplicate"] == "1"
            assert params["vpsplugin_enabled"] == params["vpsplugin_overwrite"] == "1"
            assert params["vpsplugin_time"] == str(source["vpsplugin_time"])
            assert params["recordingtype"] == "scrambled"
        assert source == original and len(box.timers) == 2
        assert client.post("/timer/save", data=values).status_code == 409
        assert len(box.writes) == 1


@pytest.mark.parametrize("state", [0, 1])
def test_copy_button_is_between_edit_and_delete_only_for_upcoming_timers(setup, state):
    _, _, app = setup
    box = install_selector(app)
    box.timers = [
        timer_row(name="Anstehender Timer", state=state),
        timer_row(name="Laufender Timer", state=2),
        timer_row(name="Erledigter Timer", state=3),
    ]
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        row = re.search(r'data-search-name="Anstehender Timer".*?</tr>', page.text, re.S)[0]
        assert (
            row.index(">Bearbeiten</a>") < row.index(">Kopieren</a>") < row.index(">Löschen</span>")
        )
        assert page.text.count(">Kopieren</a>") == 1
        assert not box.writes


def test_copy_is_creation_for_a_writer_and_denied_with_read_only_access(setup):
    _, engine, app = setup
    box = install_selector(app)
    source = timer_row(tags="e2web-owner-admin")
    box.timers = [source]
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer")
        assert ">Kopieren</a>" in page.text and ">Bearbeiten</a>" not in page.text
        assert 'action="/timer/delete"' not in page.text
        assert client.get(copy_url(source)).status_code == 200
        with Session(engine) as db:
            db.get(Grant, (2, 1)).can_write = False
            db.commit()
        assert ">Kopieren</a>" not in client.get("/timer").text
        before = len(box.requests)
        assert client.get(copy_url(source)).status_code == 403
        assert len(box.requests) == before and not box.writes


@pytest.mark.parametrize(
    "bad", ["running", "finished", "missing", "ambiguous", "changed", "receiver", "identity"]
)
def test_stale_or_invalid_copy_selection_never_creates_a_timer(setup, bad):
    _, _, app = setup
    box = install_selector(app)
    source = timer_row()
    box.timers = [copy.deepcopy(source)]
    url = copy_url(source)
    if bad in {"running", "finished"}:
        box.timers[0]["state"] = 2 if bad == "running" else 3
    elif bad == "missing":
        box.timers = []
    elif bad == "ambiguous":
        box.timers.append(copy.deepcopy(source))
    elif bad == "changed":
        box.timers[0]["end"] += 60
    elif bad == "receiver":
        url = copy_url(source, receiver_id=2)
    else:
        url = "/timer/new?copy=1"
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert client.get(url).status_code in {400, 409}
        assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
def test_source_outside_bouquets_still_copies_and_allows_source_or_other_channels(setup, xml):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    source = timer_row(serviceref=REFERENCE + "Sendername", name="Vorlage außerhalb der Bouquets")
    box.catalog = {"tv": [], "radio": []}
    box.timers = [source]
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get(copy_url(source))
        values = copied_values(page)
        assert values["bouquet"] == COPY_SOURCE and values["reference"] == source["serviceref"]
        assert (
            client.get(
                "/timer/channels", params={"receiver_id": 1, "bouquet": COPY_SOURCE}
            ).status_code
            == 409
        )
        header = {"X-Timer-Action": values["action_token"]}
        response = client.get(
            "/timer/channels", params={"receiver_id": 1, "bouquet": COPY_SOURCE}, headers=header
        )
        assert (
            response.status_code == 200
            and response.json()["services"][0]["reference"] == source["serviceref"]
        )
        values.update(
            begin=local_value(source["begin"] + 7200), end=local_value(source["end"] + 7200)
        )
        assert client.post("/timer/save", data=values, follow_redirects=False).status_code == 303
        assert len(box.writes) == 1 and box.writes[0][1]["sRef"] == source["serviceref"]


def test_copy_source_channel_is_bound_to_its_session_and_cannot_be_replaced(setup):
    _, _, app = setup
    box = install_selector(app)
    source = timer_row()
    box.timers = [source]
    with TestClient(app) as first, TestClient(app) as second:
        login(first, "user", "User-123")
        login(second, "user", "User-123")
        values = copied_values(first.get(copy_url(source)))
        response = second.get(
            "/timer/channels",
            params={"receiver_id": 1, "bouquet": COPY_SOURCE},
            headers={"X-Timer-Action": values["action_token"]},
        )
        assert response.status_code == 403
        values.update(bouquet=COPY_SOURCE, reference=SECOND)
        assert first.post("/timer/save", data=values).status_code == 409
        assert not box.writes


def test_duplicate_copy_retains_the_draft_and_saves_once_after_adjustment(setup):
    _, _, app = setup
    box = install_selector(app)
    source = timer_row(name="Vorlage", description="Beschreibung")
    box.timers = [source]
    original = copy.deepcopy(source)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        values = copied_values(client.get(copy_url(source)))
        duplicate = client.post("/timer/save", data=values)
        assert duplicate.status_code == 409 and "existiert bereits" in duplicate.text
        assert 'action="/timer/save"' in duplicate.text and not box.writes
        fresh = copied_values(
            duplicate,
            begin=local_value(source["begin"] + 7200),
            end=local_value(source["end"] + 7200),
        )
        assert fresh["action_token"] != values["action_token"]
        assert client.post("/timer/save", data=fresh, follow_redirects=False).status_code == 303
        assert len(box.writes) == 1 and source == original


@pytest.mark.parametrize("xml", [False, True])
def test_receiver_conflict_keeps_the_editable_copy_without_changing_its_source(setup, xml):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    source = timer_row()
    box.timers = [source]
    original = copy.deepcopy(source)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        values = copied_values(
            client.get(copy_url(source)),
            name="Kopie",
            begin=local_value(source["begin"] + 7200),
            end=local_value(source["end"] + 7200),
        )
        box.conflict = True
        conflict = client.post("/timer/save", data=values)
        assert conflict.status_code == 409 and "Timerkonflikt" in conflict.text
        assert input_value(conflict, "name") == "Kopie" and "data-timer-copy" in conflict.text
        assert source == original and len(box.writes) == 1 and box.writes[0][0] == "timeradd"


def test_copy_snapshot_remains_independent_when_source_is_removed_and_rights_are_rechecked(setup):
    _, engine, app = setup
    box = install_selector(app)
    source = timer_row()
    box.timers = [source]
    with TestClient(app) as client:
        login(client, "user", "User-123")
        values = copied_values(client.get(copy_url(source)))
        box.timers = []
        assert client.post("/timer/save", data=values, follow_redirects=False).status_code == 303
        values = copied_values(client.get(copy_url(box.timers[0])))
        with Session(engine) as db:
            db.get(Grant, (2, 1)).can_write = False
            db.commit()
        assert client.post("/timer/save", data=values).status_code == 403
        assert len(box.writes) == 1


def test_copy_preserves_the_second_dst_occurrence_and_seconds(setup):
    _, _, app = setup
    box = install_selector(app)
    timezone = ZoneInfo("Europe/Berlin")
    begin = int(datetime(2026, 10, 25, 2, 30, 17, tzinfo=timezone, fold=1).timestamp())
    source = timer_row(begin=begin, end=begin + 600)
    box.timers = [source]
    with TestClient(app) as client:
        login(client, "user", "User-123")
        values = copied_values(
            client.get(copy_url(source)), end=local_value(source["end"] + 60), end_fold="1"
        )
        assert client.post("/timer/save", data=values, follow_redirects=False).status_code == 303
        assert box.writes[0][1]["begin"] == str(begin)
        assert box.writes[0][1]["end"] == str(begin + 660)


@pytest.mark.parametrize("xml", [False, True])
def test_copy_navigation_loads_immediately_and_supports_direct_loading(setup, xml):
    _, _, app = setup
    box = install_selector(app, xml=xml)
    source = timer_row()
    box.timers = [source]
    factory = app.state.client_factory

    def no_receiver_io(*args):
        pytest.fail("Die Kopierseite muss vor der Receiverantwort erscheinen.")

    with TestClient(app) as client:
        login(client, "user", "User-123")
        app.state.client_factory = no_receiver_io
        shell = client.get(copy_url(source), headers={"Accept": "text/html"})
        assert shell.status_code == 200 and "Lade Daten von Receiver..." in shell.text
        app.state.client_factory = factory
        data = client.get(
            copy_url(source),
            headers={"Accept": "text/html", "X-Receiver-Data": "1", "X-Receiver-Id": "1"},
        )
        assert data.status_code == 200 and "data-timer-copy" in data.text
        direct = client.get(copy_url(source) + "&load=direct", headers={"Accept": "text/html"})
        assert direct.status_code == 200 and input_value(direct, "name") == source["name"]
        assert not box.writes
