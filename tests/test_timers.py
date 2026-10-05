import html
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from urllib.parse import parse_qs, urlencode
from xml.etree.ElementTree import Element, SubElement, tostring
from zoneinfo import ZoneInfo

import httpx
import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from ownership_support import owned_rows
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from test_foundation import csrf_value, login
from test_foundation import setup as setup

from e2web.db import AuditLog, Grant, Receiver, TimerAction, User, WebSession, migrate
from e2web.openwebif import OpenWebifClient, ReceiverError, TimerOutcomeUnknown
from e2web.security import cipher, now
from e2web.timers import local_timestamp

REFERENCE = "1:0:19:283D:3FB:1:C00000:0:0:0:"
GROUP = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.test.tv" ORDER BY bouquet'


def timer_row(**changes):
    return {
        "serviceref": REFERENCE,
        "servicename": "Das Erste HD",
        "name": "Tagesschau",
        "description": "Nachrichten",
        "begin": now() + 3600,
        "end": now() + 5400,
        "eit": 42,
        "disabled": 0,
        "justplay": 0,
        "afterevent": 3,
        "dirname": "/media/hdd/movie/",
        "repeated": 0,
        "state": 0,
        "cancelled": False,
        "tags": "Nachrichten HD",
        "always_zap": 1,
        "pipzap": 0,
        "autoadjust": 1,
        "allow_duplicate": 1,
        "vpsplugin_enabled": True,
        "vpsplugin_overwrite": True,
        "vpsplugin_time": now() + 3500,
        "recordingtype": "scrambled",
        **changes,
    }


class MockReceiver:
    def __init__(self, *, xml=False):
        self.xml = xml
        self.timers = []
        self.requests = []
        self.writes = []
        self.conflict = False
        self.lost_reply = False
        self.event_begin = now() + 7200
        self.event_id = 99

    def timer_xml(self):
        root = Element("e2timerlist")
        mapping = {
            "serviceref": "e2servicereference",
            "servicename": "e2servicename",
            "name": "e2name",
            "description": "e2description",
            "eit": "e2eit",
            "begin": "e2timebegin",
            "end": "e2timeend",
            "disabled": "e2disabled",
            "repeated": "e2repeated",
            "justplay": "e2justplay",
            "afterevent": "e2afterevent",
            "dirname": "e2location",
            "tags": "e2tags",
            "state": "e2state",
            "cancelled": "e2cancled",
            "always_zap": "e2alwayszap",
            "pipzap": "e2pipzap",
            "filename": "e2filename",
        }
        for timer in self.timers:
            row = SubElement(root, "e2timer")
            for key, tag in mapping.items():
                SubElement(row, tag).text = str(timer.get(key, ""))
        return tostring(root)

    def __call__(self, request):
        self.requests.append((request.method, request.url.path, request.url.host))
        method = request.url.path.rsplit("/", 1)[-1]
        if self.xml and request.url.path.startswith("/api/"):
            return httpx.Response(404)
        if request.method == "GET":
            if method == "timerlist":
                if self.xml:
                    return httpx.Response(200, content=self.timer_xml())
                return httpx.Response(
                    200,
                    json={
                        "result": True,
                        "timers": self.timers,
                        "locations": ["/media/hdd/movie/"],
                        "default": "/media/hdd/movie/",
                    },
                )
            if method == "getlocations":
                if not self.xml:
                    return httpx.Response(200, json={"locations": ["/media/hdd/movie/"]})
                return httpx.Response(
                    200,
                    content="<e2locations><e2location>/media/hdd/movie/</e2location></e2locations>",
                )
            if method == "getservices":
                if self.xml:
                    root = Element("e2servicelist")
                    row = SubElement(root, "e2service")
                    SubElement(row, "e2servicereference").text = REFERENCE
                    SubElement(row, "e2servicename").text = "Das Erste HD"
                    return httpx.Response(200, content=tostring(root))
                return httpx.Response(
                    200,
                    json={
                        "services": [{"servicereference": REFERENCE, "servicename": "Das Erste HD"}]
                    },
                )
            if method == "epgservice":
                return httpx.Response(
                    200,
                    json={
                        "events": [
                            {
                                "id": self.event_id,
                                "begin_timestamp": self.event_begin,
                                "duration_sec": 1800,
                                "title": "Aus dem EPG",
                                "shortdesc": "Beschreibung",
                                "longdesc": "Details",
                                "sref": REFERENCE,
                                "sname": "Das Erste HD",
                            }
                        ]
                    },
                )
            raise AssertionError(request.url.path)
        assert request.method == "POST"
        params = {
            k: v[0] for k, v in parse_qs(request.content.decode(), keep_blank_values=True).items()
        }
        self.writes.append((method, params, request.url.host))
        if self.conflict:
            if method == "timerchange":
                # OpenWebif may modify the entry before its sanity/conflict check returns false.
                self.timers[0]["name"] = params["name"]
            return httpx.Response(
                200,
                json={
                    "result": False,
                    "message": "Timer Conflict",
                    "conflicts": [{"name": "Andere Aufnahme", "servicename": "ZDF"}],
                },
            )
        if method == "timerdelete":
            self.timers = [
                t
                for t in self.timers
                if not (
                    t["serviceref"] == params["sRef"]
                    and t["begin"] == int(params["begin"])
                    and t["end"] == int(params["end"])
                )
            ]
        else:
            previous = {}
            if method == "timerchange" and (not self.xml or params.get("deleteOldOnSave") == "1"):
                previous = next(
                    t
                    for t in self.timers
                    if t["serviceref"] == params["channelOld"]
                    and t["begin"] == int(params["beginOld"])
                    and t["end"] == int(params["endOld"])
                )
                self.timers = [
                    t
                    for t in self.timers
                    if not (
                        t["serviceref"] == params["channelOld"]
                        and t["begin"] == int(params["beginOld"])
                        and t["end"] == int(params["endOld"])
                    )
                ]
            row = timer_row(
                **previous,
            )
            row.update(
                serviceref=params["sRef"],
                name=params["name"],
                description=params["description"],
                dirname=params.get("dirname", ""),
                tags=params.get("tags", ""),
            )
            for key in ("begin", "end", "disabled", "repeated", "afterevent", "justplay", "eit"):
                row[key] = int(params.get(key, 0))
            self.timers.append(row)
        if self.lost_reply:
            raise httpx.ReadTimeout("private-address-with-secret", request=request)
        if self.xml:
            return httpx.Response(
                200,
                content="<e2simplexmlresult><e2state>True</e2state><e2statetext>OK</e2statetext></e2simplexmlresult>",
            )
        return httpx.Response(200, json={"result": True, "message": "OK"})


def install_mock(app, **kwargs):
    box = MockReceiver(**kwargs)
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    return box


def new_url(**changes):
    return "/timer/new?" + urlencode(
        {"receiver_id": 1, "reference": REFERENCE, "group": GROUP, **changes}
    )


def existing_url(path, row, *, receiver_id=1):
    return (
        path
        + "?"
        + urlencode(
            {
                "receiver_id": receiver_id,
                "reference": row["serviceref"],
                "begin": row["begin"],
                "end": row["end"],
            }
        )
    )


def input_value(page, key):
    return html.unescape(re.search(rf'name="{key}"[^>]*value="([^"]*)"', page.text)[1])


def form_values(page, **changes):
    values = {key: input_value(page, key) for key in ("action_token", "name", "begin", "end")}
    values.update(
        csrf_token=csrf_value(page),
        description="Beschreibung",
        directory="/media/hdd/movie/",
        weekdays=[],
        before="0",
        after="0",
        begin_fold="",
        end_fold="",
    )
    return {**values, **changes}


def test_timer_crud_explicit_submit_single_use_and_preserved_options(setup):
    _, engine, app = setup
    box = install_mock(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get(new_url())
        assert page.status_code == 200 and not box.writes
        form = form_values(page, name="Mein Timer", weekdays=["0", "2", "4"])
        assert client.post("/timer/save", data={**form, "csrf_token": "invalid"}).status_code == 403
        assert not box.writes
        result = client.post("/timer/save", data=form, follow_redirects=False)
        assert result.status_code == 303 and result.headers["location"] == "/timer?done=added"
        assert box.writes[0][1]["repeated"] == "21"
        assert box.writes[0][1]["justplay"] == "0" and box.writes[0][1]["afterevent"] == "0"
        assert box.writes[0][2] == "192.0.2.50"
        assert client.post("/timer/save", data=form).status_code == 409
        assert len(box.writes) == 1
        row = box.timers[0]
        old = row.copy()
        page = client.get(existing_url("/timer/edit", row))
        assert page.status_code == 200
        form = form_values(page, name="Geändert", disabled="on", weekdays=["0", "1", "2", "3", "4"])
        assert client.post("/timer/save", data=form, follow_redirects=False).status_code == 303
        params = box.writes[-1][1]
        for key in (
            "always_zap",
            "pipzap",
            "autoadjust",
            "allow_duplicate",
            "vpsplugin_time",
            "recordingtype",
        ):
            assert params[key] == str(old[key])
        assert params["vpsplugin_enabled"] == "1" and params["vpsplugin_overwrite"] == "1"
        assert params["tags"] == old["tags"] and params["eit"] == str(old["eit"])
        assert params["channelOld"] == REFERENCE and params["beginOld"] == str(old["begin"])
        assert params["disabled"] == "1" and params["repeated"] == "31"
        assert client.get("/timer").status_code == 200
        page = client.get("/timer")
        assert not len(box.writes) > 2
        deletion = {
            "csrf_token": csrf_value(page),
            "action_token": input_value(page, "action_token"),
            "confirmed": "true",
        }
        assert (
            client.post("/timer/delete", data=deletion, follow_redirects=False).status_code == 303
        )
        assert not box.timers and set(box.writes[-1][1]) == {"sRef", "begin", "end"}
        assert client.post("/timer/delete", data=deletion).status_code == 409
    with Session(engine) as db:
        assert [
            log.action for log in db.scalars(select(AuditLog)) if log.action.startswith("timer.")
        ] == ["timer.add.success", "timer.edit.success", "timer.delete.success"]
        assert not db.scalar(select(TimerAction).where(TimerAction.locked_receiver_id.is_not(None)))


@pytest.mark.parametrize("xml", [False, True])
def test_running_timer_can_be_edited_without_creating_a_duplicate(setup, xml):
    _, _, app = setup
    box = install_mock(app, xml=xml)
    original = timer_row(
        state=2, begin=now() - 900, end=now() + 2700, filename="/media/hdd/movie/live"
    )
    box.timers = [original.copy()]
    owned_rows(app, box.timers)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer")
        assert '<h1>Timer <span class="heading-receiver">VU+ Duo 4K</span></h1>' in page.text
        assert '<p class="timer-description">Nachrichten</p>' in page.text
        assert "<summary>Beschreibung</summary>" not in page.text
        edit = client.get(existing_url("/timer/edit", original))
        assert edit.status_code == 200 and not box.writes
        assert (
            client.post(
                "/timer/save",
                data=form_values(edit, name="Laufender Timer geändert"),
                follow_redirects=False,
            ).status_code
            == 303
        )
        assert len(box.timers) == 1 and box.timers[0]["state"] == 2
        assert box.timers[0]["filename"] == original["filename"]
        assert box.timers[0]["name"] == "Laufender Timer geändert"
        assert len(box.writes) == 1 and box.writes[0][0] == "timerchange"
        assert box.writes[0][1]["deleteOldOnSave"] == "1"
        box.timers[0]["description"] = "   "
        empty = client.get("/timer")
        assert 'class="timer-description"' not in empty.text


def test_epg_draft_is_read_only_until_submit_and_applies_margins(setup):
    _, _, app = setup
    box = install_mock(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        epg = client.get("/epg?" + urlencode({"reference": REFERENCE, "day": "all"}))
        href = html.unescape(re.search(r'href="([^"]*/timer/new\?[^"]+)"', epg.text)[1])
        page = client.get(href)
        assert "Aus dem EPG" in page.text and not box.writes
        form = form_values(page, before="3", after="5")
        assert client.post("/timer/save", data=form, follow_redirects=False).status_code == 303
        params = box.writes[0][1]
        assert int(params["begin"]) == box.event_begin - 180
        assert int(params["end"]) == box.event_begin + 1800 + 300
        assert params["eit"] == "99"


def test_changed_epg_and_forged_sender_are_rejected_without_writes(setup):
    _, _, app = setup
    box = install_mock(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert client.get(new_url(reference="unknown")).status_code == 409
        page = client.get(new_url(event_id=99, event_begin=box.event_begin))
        form = form_values(page)
        box.event_begin += 900
        assert client.post("/timer/save", data=form).status_code == 409
        assert not box.writes


def test_epg_event_zero_keeps_its_id_in_the_timer_link(setup):
    _, _, app = setup
    box = install_mock(app)
    box.event_id = 0
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/epg?" + urlencode({"reference": REFERENCE, "day": "all"}))
        href = html.unescape(re.search(r'href="([^"]*/timer/new\?[^"]+)"', page.text)[1])
        assert "event_id=0" in href
        draft = client.get(href)
        assert draft.status_code == 200 and "Aus dem EPG" in draft.text
        assert not box.writes


@pytest.mark.parametrize(
    "change", ["receiver_selection", "grant", "receiver_config", "receiver_disabled"]
)
def test_stale_authority_or_receiver_form_never_writes(setup, change):
    _, engine, app = setup
    box = install_mock(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get(new_url())
        form = form_values(page)
        with Session(engine) as db:
            if change == "receiver_selection":
                db.add(Grant(user_id=2, receiver_id=2))
                db.scalar(select(WebSession)).receiver_id = 2
            elif change == "grant":
                db.execute(delete(Grant).where(Grant.user_id == 2))
            elif change == "receiver_config":
                db.get(Receiver, 1).hostname = "192.0.2.99"
            else:
                db.get(Receiver, 1).enabled = False
            db.commit()
        assert client.post("/timer/save", data=form).status_code == 409
        assert not box.writes


def test_stale_timer_and_running_transition_require_new_confirmation(setup):
    _, _, app = setup
    box = install_mock(app)
    box.timers = [timer_row()]
    owned_rows(app, box.timers)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get(existing_url("/timer/edit", box.timers[0]))
        box.timers[0]["name"] = "Am Receiver geändert"
        assert client.post("/timer/save", data=form_values(page)).status_code == 409
        page = client.get("/timer")
        box.timers[0]["state"] = 2
        form = {
            "csrf_token": csrf_value(page),
            "action_token": input_value(page, "action_token"),
            "confirmed": "true",
        }
        assert client.post("/timer/delete", data=form).status_code == 409
        assert not box.writes
        page = client.get("/timer")
        assert "Beendet auch die laufende Aufnahme." in page.text
        form = {
            "csrf_token": csrf_value(page),
            "action_token": input_value(page, "action_token"),
            "confirmed": "true",
        }
        assert client.post("/timer/delete", data=form, follow_redirects=False).status_code == 303
        assert not box.timers


def test_lost_write_reply_is_not_retried_or_replayed(setup):
    _, engine, app = setup
    box = install_mock(app)
    box.lost_reply = True
    with TestClient(app) as client:
        login(client, "user", "User-123")
        form = form_values(client.get(new_url()))
        result = client.post("/timer/save", data=form)
        assert result.status_code == 502 and "Der Ausgang ist unklar" in result.text
        assert "private-address-with-secret" not in result.text
        assert len(box.writes) == 1 and len(box.timers) == 1
        assert client.post("/timer/save", data=form).status_code == 409
        assert len(box.writes) == 1
        page = client.get(new_url())
        form = form_values(page, begin=form["begin"], end=form["end"])
        assert client.post("/timer/save", data=form).status_code == 409
        assert len(box.writes) == 1
    with Session(engine) as db:
        assert db.scalar(select(AuditLog.action).where(AuditLog.action == "timer.add.unknown"))


def test_conflict_reopens_add_draft_but_edit_requires_refresh(setup):
    _, _, app = setup
    box = install_mock(app)
    box.conflict = True
    with TestClient(app) as client:
        login(client, "user", "User-123")
        first = client.get(new_url())
        result = client.post("/timer/save", data=form_values(first))
        assert result.status_code == 409 and "Timerkonflikt" in result.text
        assert input_value(result, "action_token") != input_value(first, "action_token")
        assert not box.timers
        box.timers = [timer_row()]
        owned_rows(app, box.timers)
        page = client.get(existing_url("/timer/edit", box.timers[0]))
        result = client.post("/timer/save", data=form_values(page, name="Trotz Konflikt geändert"))
        assert result.status_code == 409 and "bereits Timerdaten geändert" in result.text
        assert "Andere Aufnahme" in result.text and 'action="/timer/save"' not in result.text
        assert box.timers[0]["name"] == "Trotz Konflikt geändert"


def test_per_receiver_lease_blocks_concurrent_write_and_expires(setup):
    _, engine, app = setup
    box = install_mock(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        first = client.get(new_url())
        second = client.get(new_url())
        with Session(engine) as db:
            action = db.scalar(select(TimerAction).order_by(TimerAction.created_at))
            action.used_at = now()
            action.locked_receiver_id, action.lock_until = 1, now() + 300
            db.commit()
        form = form_values(second)
        result = client.post("/timer/save", data=form)
        assert result.status_code == 409 and "läuft bereits" in result.text
        assert not box.writes
        with Session(engine) as db:
            action = db.scalar(select(TimerAction).where(TimerAction.locked_receiver_id == 1))
            action.lock_until = now() - 1
            db.commit()
        assert client.post("/timer/save", data=form, follow_redirects=False).status_code == 303
        assert len(box.writes) == 1
        assert input_value(first, "action_token") != input_value(second, "action_token")


def test_xml_timer_read_add_edit_delete(setup):
    cfg, engine, app = setup
    box = install_mock(app, xml=True)
    box.timers = [timer_row(name="XML <script>alert(1)</script>", repeated=127, cancelled=True)]
    with Session(engine) as db:
        receiver = db.get(Receiver, 1)
        adapter = app.state.client_factory(receiver, cfg)
        listing = adapter.timer_list()
        assert listing.xml and listing.timers[0].repeat_label == "Täglich"
        assert listing.timers[0].cancelled and adapter.timer_locations() == ["/media/hdd/movie/"]
        assert adapter.write_timer(
            "timeradd",
            {
                "sRef": REFERENCE,
                "name": "XML neu",
                "description": "",
                "begin": str(now() + 9000),
                "end": str(now() + 9600),
                "disabled": "0",
                "justplay": "0",
                "afterevent": "0",
                "repeated": "0",
                "eit": "0",
            },
            xml=listing.xml,
        ).success
    owned_rows(app, box.timers)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer")
        assert "XML &lt;script&gt;" in page.text and "<script>alert(1)</script>" not in page.text
        assert "Bearbeiten</a>" in page.text
        edit = client.get(existing_url("/timer/edit", box.timers[0]))
        assert edit.status_code == 200
        assert (
            client.post(
                "/timer/save",
                data=form_values(edit, name="XML geändert", weekdays=[str(n) for n in range(7)]),
                follow_redirects=False,
            ).status_code
            == 303
        )
        assert box.writes[-1][0] == "timerchange"
        assert box.writes[-1][1]["deleteOldOnSave"] == "1"
        assert len(box.timers) == 2
        assert sum(t["name"] == "XML geändert" for t in box.timers) == 1
        assert box.writes[-1][1]["afterevent"] == "3"
        assert box.writes[-1][1]["tags"].startswith("Nachrichten HD e2web-owner-")
        page = client.get("/timer")
        assert (
            client.post(
                "/timer/delete",
                data={
                    "csrf_token": csrf_value(page),
                    "action_token": input_value(page, "action_token"),
                    "confirmed": "true",
                },
                follow_redirects=False,
            ).status_code
            == 303
        )
    assert all(path.startswith("/web/") for method, path, _ in box.requests if method == "POST")


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(404),
        httpx.Response(500),
        httpx.Response(200, json={"result": "true"}),
        httpx.Response(200, content="invalid"),
    ],
)
def test_invalid_write_acknowledgement_never_falls_back(setup, response):
    cfg, engine, _ = setup
    seen = []

    def handler(request):
        seen.append((request.method, request.url.path))
        return response

    with Session(engine) as db:
        adapter = OpenWebifClient(db.get(Receiver, 1), cfg, transport=httpx.MockTransport(handler))
        with pytest.raises(TimerOutcomeUnknown):
            adapter.write_timer(
                "timerdelete", {"sRef": REFERENCE, "begin": "1", "end": "2"}, xml=False
            )
    assert seen == [("POST", "/api/timerdelete")]


@pytest.mark.parametrize("value", ["2026-03-29T02:30:00", "2026-10-25T02:30:00"])
def test_dst_nonexistent_and_ambiguous_local_times_require_resolution(value):
    with pytest.raises(ValueError, match="Zeitumstellung"):
        local_timestamp(value, ZoneInfo("Europe/Berlin"))


def test_dst_fold_and_seconds_are_preserved():
    tz = ZoneInfo("Europe/Berlin")
    first = local_timestamp("2026-10-25T02:30:17", tz, fold="0")
    second = local_timestamp("2026-10-25T02:30:17", tz, fold="1")
    assert second - first == 3600
    assert local_timestamp("2026-10-25T02:30:17", tz, original=second) == second
    assert datetime.fromtimestamp(second, tz).second == 17


def test_validation_does_not_consume_action_or_mutate_receiver(setup):
    _, _, app = setup
    box = install_mock(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get(new_url())
        form = form_values(page)
        result = client.post("/timer/save", data={**form, "directory": "/invented"})
        assert result.status_code == 400 and not box.writes
        result = client.post("/timer/save", data={**form, "end": form["begin"]})
        assert result.status_code == 400 and not box.writes
        assert client.post("/timer/save", data=form, follow_redirects=False).status_code == 303


def test_action_is_bound_to_its_session(setup):
    _, _, app = setup
    box = install_mock(app)
    with TestClient(app) as first, TestClient(app) as second:
        login(first, "user", "User-123")
        login(second, "user", "User-123")
        form = form_values(first.get(new_url()))
        form["csrf_token"] = csrf_value(second.get("/timer"))
        assert second.post("/timer/save", data=form).status_code == 403
        assert not box.writes


def test_malformed_timer_data_is_rejected(setup):
    cfg, engine, _ = setup
    with Session(engine) as db:
        adapter = OpenWebifClient(
            db.get(Receiver, 1),
            cfg,
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json={"timers": [timer_row(repeated=255)]})
            ),
        )
        with pytest.raises(ReceiverError, match="Timerformat"):
            adapter.timer_list()


def test_parallel_sessions_and_logout_keep_inflight_receiver_lease(setup):
    _, engine, app = setup
    box = MockReceiver()
    started, release = threading.Event(), threading.Event()

    def handler(request):
        if request.method == "POST":
            started.set()
            assert release.wait(5)
        return box(request)

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(handler))
    with TestClient(app) as first, TestClient(app) as second:
        login(first, "user", "User-123")
        login(second, "user", "User-123")
        first_page, second_page = first.get(new_url()), second.get(new_url())
        with ThreadPoolExecutor(max_workers=1) as pool:
            task = pool.submit(
                first.post, "/timer/save", data=form_values(first_page), follow_redirects=False
            )
            try:
                assert started.wait(3)
                assert (
                    first.post(
                        "/logout",
                        data={"csrf_token": csrf_value(first_page)},
                        follow_redirects=False,
                    ).status_code
                    == 303
                )
                with Session(engine) as db:
                    action = db.scalar(
                        select(TimerAction).where(TimerAction.locked_receiver_id == 1)
                    )
                    assert action and action.session_hash is None
                assert second.post("/timer/save", data=form_values(second_page)).status_code == 409
                assert not box.writes
            finally:
                release.set()
            assert task.result(timeout=5).status_code == 303
        assert len(box.writes) == 1
    with Session(engine) as db:
        assert not db.scalar(select(TimerAction).where(TimerAction.locked_receiver_id.is_not(None)))


def test_upgrade_from_0001_preserves_accounts_grants_and_receiver_key(setup):
    cfg, engine, _ = setup
    original_key = cfg.key_path.read_bytes()
    with Session(engine) as db:
        receiver = db.get(Receiver, 1)
        receiver.encrypted_password = cipher(cfg).encrypt(b"unchanged-receiver-password").decode()
        db.commit()
        encrypted = receiver.encrypted_password
        original_hash = db.get(User, 1).password_hash
    from pathlib import Path

    import e2web.db as db_module

    alembic = AlembicConfig()
    alembic.set_main_option("script_location", str(Path(db_module.__file__).parent / "migrations"))
    with engine.begin() as connection:
        alembic.attributes["connection"] = connection
        command.downgrade(alembic, "0001")
    migrate(cfg)
    with Session(engine) as db:
        assert db.get(User, 1).password_hash == original_hash
        assert db.get(Grant, (2, 1))
        assert db.get(Receiver, 1).encrypted_password == encrypted
        assert not list(db.scalars(select(TimerAction)))
    assert cfg.key_path.read_bytes() == original_key
