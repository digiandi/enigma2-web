from functools import partial

import httpx
import pytest
from fastapi.testclient import TestClient
from test_catalog import adapter
from test_foundation import login
from test_foundation import setup as setup
from test_recordings import ROOT
from test_timer_layout import SelectorReceiver, SelectParser
from test_timers import form_values

from e2web.openwebif import OpenWebifClient, ReceiverError


def install_current_location_receiver(app, *, xml, location):
    box = SelectorReceiver(xml=xml)

    def response(request):
        if request.url.path.endswith("getcurrlocation"):
            if request.url.path.startswith("/api/"):
                return httpx.Response(404)
            return httpx.Response(
                200, text=f"<e2locations><e2location>{location}</e2location></e2locations>"
            )
        result = box(request)
        if not xml and request.url.path.endswith(("timerlist", "getlocations")):
            data = result.json()
            data.pop("default", None)
            return httpx.Response(200, json=data)
        return result

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(response))
    return box


@pytest.mark.parametrize("xml", [False, True])
def test_current_location_xml_container_loads_form_and_saves_real_default(setup, xml):
    _, _, app = setup
    box = install_current_location_receiver(app, xml=xml, location=ROOT)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer/new")
        assert page.status_code == 200
        assert "Timerentwurf konnte nicht geladen werden" not in page.text
        paths = SelectParser(page.text).selects["directory"]
        assert [r["value"] for r in paths if r["selected"]] == [ROOT]
        assert "Standardpfad des Receivers" not in page.text
        result = client.post("/timer/save", data=form_values(page), follow_redirects=False)
        assert result.status_code == 303
        assert box.writes[-1][1]["dirname"] == ROOT


@pytest.mark.parametrize(
    "reply",
    [
        f"<e2location>{ROOT}</e2location>",
        f"<e2locations><e2location>{ROOT}</e2location></e2locations>",
        {"result": True, "location": ROOT},
    ],
)
def test_current_location_accepts_json_and_both_xml_shapes(tmp_path, reply):
    def response(request):
        if isinstance(reply, dict):
            return httpx.Response(200, json=reply)
        if request.url.path.startswith("/api/"):
            return httpx.Response(404)
        return httpx.Response(200, text=reply)

    assert adapter(tmp_path, response).current_recording_location() == ROOT


@pytest.mark.parametrize(
    "reply",
    [
        "<e2locations />",
        f"<e2locations><e2location>{ROOT}</e2location><e2location>/another/</e2location></e2locations>",
        "<e2locations><e2location>relative/path</e2location></e2locations>",
        "<e2locations><e2location>/media/hdd/../private/</e2location></e2locations>",
        {"result": False, "location": ROOT},
    ],
)
def test_invalid_or_ambiguous_current_location_never_selects_a_path(tmp_path, reply):
    def response(request):
        if isinstance(reply, dict):
            return httpx.Response(200, json=reply)
        if request.url.path.startswith("/api/"):
            return httpx.Response(404)
        return httpx.Response(200, text=reply)

    with pytest.raises(ReceiverError):
        adapter(tmp_path, response).current_recording_location()


def test_dedicated_locations_default_is_selected_without_current_location_endpoint(setup):
    _, _, app = setup
    box = SelectorReceiver()

    def response(request):
        if request.url.path.endswith("timerlist"):
            data = box(request).json()
            data.pop("default", None)
            data.pop("locations", None)
            return httpx.Response(200, json=data)
        assert not request.url.path.endswith("getcurrlocation")
        return box(request)

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(response))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer/new")
        assert page.status_code == 200
        paths = SelectParser(page.text).selects["directory"]
        assert [row["value"] for row in paths if row["selected"]] == [ROOT]
        saved = client.post("/timer/save", data=form_values(page), follow_redirects=False)
        assert saved.status_code == 303
        assert box.writes[-1][1]["dirname"] == ROOT


def test_no_path_from_any_receiver_endpoint_gives_readable_error_without_writes(setup):
    _, _, app = setup
    box = SelectorReceiver()

    def response(request):
        if request.url.path.endswith("getcurrlocation"):
            return httpx.Response(503)
        data = box(request)
        if request.url.path.endswith(("timerlist", "getlocations")):
            payload = data.json()
            payload["default"] = ""
            payload["locations"] = []
            return httpx.Response(200, json=payload)
        return data

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(response))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer/new")
        assert page.status_code == 502
        assert "Der Standardaufnahmepfad konnte nicht ermittelt werden." in page.text
        assert not box.writes
