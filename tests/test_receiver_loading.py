from functools import partial
from urllib.parse import urlencode

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_catalog import adapter
from test_foundation import login
from test_foundation import setup as setup
from test_recordings import ROOT
from test_timer_layout import SelectorReceiver
from test_timers import REFERENCE, existing_url, timer_row

from e2web.db import Grant, TimerAction, User
from e2web.openwebif import OpenWebifClient, ReceiverError


def page_url(path):
    if path == "/epg":
        return path + "?" + urlencode({"reference": REFERENCE, "name": "Das Erste HD"})
    if path == "/timer/edit":
        return existing_url(path, timer_row())
    return path


@pytest.mark.parametrize(
    "path", ["/timer", "/aufnahmen", "/sender", "/epg", "/timer/new", "/timer/edit"]
)
def test_browser_navigation_renders_before_any_receiver_query(setup, path):
    _, engine, app = setup

    def no_receiver_io(*args):
        pytest.fail("Der erste HTML-Aufruf darf nicht auf den Receiver zugreifen.")

    app.state.client_factory = no_receiver_io
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get(page_url(path), headers={"Accept": "text/html"})
        assert page.status_code == 200
        assert "Lade Daten von Receiver..." in page.text
        assert "VU+ Duo 4K" in page.text
        assert "Enigma2 Timer" in page.text and "data-page-content" in page.text
        assert 'data-receiver-id="1"' in page.text
        assert "load=direct" in page.text
        assert page.headers["cache-control"] == "no-store"
    with Session(engine) as db:
        assert not list(db.scalars(select(TimerAction)))


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize("path", ["/timer", "/aufnahmen", "/sender", "/timer/new", "/timer/edit"])
def test_data_request_delivers_the_complete_authorized_page(setup, xml, path):
    _, _, app = setup
    box = SelectorReceiver(xml=xml)
    box.timers = [timer_row(tags="e2web-owner-user")]
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get(
            page_url(path),
            headers={"Accept": "text/html", "X-Receiver-Data": "1", "X-Receiver-Id": "1"},
        )
        assert page.status_code == 200
        assert "data-receiver-load" not in page.text
        assert "Lade Daten von Receiver..." not in page.text
        assert "data-page-content" in page.text
        assert "Aufnahmeliste nicht erreichbar" not in page.text
        assert "Timerentwurf konnte nicht geladen werden" not in page.text
        assert box.requests and not box.writes


def test_pending_data_cannot_use_another_receiver_or_a_revoked_session(setup):
    _, engine, app = setup
    box = SelectorReceiver()
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    headers = {"Accept": "text/html", "X-Receiver-Data": "1", "X-Receiver-Id": "1"}
    with TestClient(app, follow_redirects=False) as client:
        login(client, "user", "User-123")
        shell = client.get("/aufnahmen", headers={"Accept": "text/html"})
        assert shell.status_code == 200 and not box.requests
        wrong = client.get("/aufnahmen", headers={**headers, "X-Receiver-Id": "2"})
        assert wrong.status_code == 409 and wrong.headers["X-Receiver-Changed"] == "1"
        assert not box.requests
        with Session(engine) as db:
            db.get(User, 2).active = False
            db.commit()
        denied = client.get("/aufnahmen", headers=headers)
        assert denied.status_code == 303 and denied.headers["location"] == "/login"
        assert not box.requests


def test_read_only_timer_forms_are_denied_without_receiver_queries(setup):
    _, engine, app = setup
    with Session(engine) as db:
        db.get(Grant, (2, 1)).can_write = False
        db.commit()
    box = SelectorReceiver()
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        for path in ("/timer/new", "/timer/edit"):
            page = client.get(page_url(path), headers={"Accept": "text/html"})
            assert page.status_code == 403 and "nur Leserechte" in page.text
            assert "data-receiver-load" not in page.text
        assert not box.requests


def test_direct_loading_for_disabled_javascript_and_readable_receiver_error(setup):
    _, _, app = setup
    box = SelectorReceiver()

    def fail(request):
        return httpx.Response(503)

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(fail))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer?load=direct", headers={"Accept": "text/html"})
        assert "data-receiver-load" not in page.text
        assert "Timerliste nicht erreichbar" in page.text
        assert 'role="alert"' in page.text
        assert not box.writes


@pytest.mark.parametrize(
    "reply",
    [
        {"result": True, "settings": [["config.usage.default_path", "/media/usb"]]},
        {"settings": [{"name": "config.usage.default_path", "value": "/media/usb/"}]},
        "<e2settings><e2setting><e2settingname>config.usage.default_path</e2settingname>"
        "<e2settingvalue>/media/usb/</e2settingvalue></e2setting></e2settings>",
    ],
)
def test_configured_recording_default_uses_settings_json_or_xml(tmp_path, reply):
    calls = []

    def response(request):
        calls.append(request.url.path)
        assert request.method == "GET" and request.url.path.endswith("/settings")
        if isinstance(reply, dict):
            return httpx.Response(200, json=reply)
        if request.url.path.startswith("/api/"):
            return httpx.Response(404)
        return httpx.Response(200, text=reply)

    assert adapter(tmp_path, response).default_recording_location() == "/media/usb/"
    expected = ["/api/settings"] if isinstance(reply, dict) else ["/api/settings", "/web/settings"]
    assert calls == expected


@pytest.mark.parametrize(
    "values",
    [[], [""], ["<default>"], ["relative/path"], ["/media/hdd/../private"], [ROOT, "/other/"]],
)
def test_unavailable_or_ambiguous_default_is_never_guessed(tmp_path, values):
    def response(request):
        return httpx.Response(
            200,
            json={
                "settings": [["config.movielist.last_videodir", ROOT]]
                + [["config.usage.default_path", value] for value in values]
            },
        )

    with pytest.raises(ReceiverError, match="Standardaufnahmeordner"):
        adapter(tmp_path, response).default_recording_location()
