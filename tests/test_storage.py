import re
from functools import partial

import httpx
import pytest
from fastapi.testclient import TestClient
from test_catalog import adapter
from test_foundation import login
from test_foundation import setup as setup
from test_recordings import ROOT, MovieReceiver, movie_row

from e2web.openwebif import OpenWebifClient


@pytest.mark.parametrize(
    ("directory", "disks", "expected"),
    [
        (ROOT, [{"mount": "/media/hdd", "free": "120.4 GB"}], "120.4 GB"),
        (ROOT + "Serien/", [{"mount": "/media/hdd/", "free": "0 MB"}], "0 MB"),
        ("/media/usb/", [{"mount": "/media/usb", "free": "42,5 GB"}], "42,5 GB"),
        ("/media/usb2/", [{"mount": "/media/usb", "free": "42 GB"}], None),
        ("/media/net/Archiv/", [{"mount": "/media/hdd", "free": "42 GB"}], None),
        ("/hdd/movie/", [{"mount": "/media/hdd", "free": "42 GB"}], None),
        (
            ROOT + "Archiv/",
            [
                {"mount": "/media/hdd", "free": "42 GB"},
                {"mount": ROOT + "Archiv", "free": "12 GB"},
            ],
            "12 GB",
        ),
        (
            ROOT + "Archiv/",
            [
                {"mount": "/media/hdd", "free": "42 GB"},
                {"mount": ROOT + "Archiv", "free": "-1 MB"},
            ],
            None,
        ),
        (
            ROOT,
            [{"mount": "/media/hdd", "free": "42 GB"}, {"mount": "/media/hdd", "free": "12 GB"}],
            None,
        ),
        (ROOT, [{"model": "Disk", "capacity": "500 GB", "free": "42 GB"}], None),
        (ROOT, [{"mount": "/media/hdd/../usb", "free": "42 GB"}], None),
    ],
)
def test_storage_matches_the_folder_filesystem_without_guessing(
    tmp_path, directory, disks, expected
):
    seen = []

    def api(request):
        seen.append(request)
        assert request.method == "GET" and request.url.path == "/api/deviceinfo"
        assert not request.url.query
        return httpx.Response(200, json={"hdd": disks})

    client = adapter(tmp_path, api)
    assert client.recording_free_space(directory) == expected
    assert len(seen) == 1
    assert seen[0].extensions["timeout"]["read"] == 90


@pytest.mark.parametrize(
    "free", [None, "", "-1 MB", "unknown", "NaN GB", 123, True, "<b>12 GB</b>"]
)
def test_unavailable_or_invalid_free_space_is_unknown(tmp_path, free):
    client = adapter(
        tmp_path,
        lambda request: httpx.Response(200, json={"hdd": [{"mount": "/media/hdd", "free": free}]}),
    )
    assert client.recording_free_space(ROOT) is None


@pytest.mark.parametrize("payload", [{}, {"hdd": None}, {"hdd": {}}, {"hdd": [None]}, []])
def test_missing_storage_information_is_unknown(tmp_path, payload):
    client = adapter(tmp_path, lambda request: httpx.Response(200, json=payload))
    assert client.recording_free_space(ROOT) is None


def test_legacy_xml_without_mount_information_is_unknown(tmp_path):
    seen = []

    def api(request):
        seen.append(request.url.path)
        if request.url.path.startswith("/api/"):
            return httpx.Response(404)
        return httpx.Response(
            200,
            text="<e2deviceinfo><e2hddlist><e2hdd><e2model>Disk</e2model>"
            "<e2capacity>500 GB</e2capacity><e2free>120 GB</e2free>"
            "</e2hdd></e2hddlist></e2deviceinfo>",
        )

    assert adapter(tmp_path, api).recording_free_space(ROOT) is None
    assert seen == ["/api/deviceinfo", "/web/deviceinfo"]


class StorageReceiver(MovieReceiver):
    def __init__(self):
        super().__init__()
        self.storage = {
            "hdd": [
                {"mount": "/media/hdd", "free": "120.4 GB"},
                {"mount": "/media/usb", "free": "42 GB"},
            ]
        }
        self.storage_failure = None
        self.paths = [ROOT, "/media/usb/", "/media/net/Archiv/"]
        self.movies.append(
            movie_row(
                filename="/media/usb/Musik.ts",
                serviceref="1:0:0:0:0:0:0:0:0:0:/media/usb/Musik.ts",
                eventname="Musik",
            )
        )

    def __call__(self, request):
        if request.url.path == "/api/deviceinfo":
            self.requests.append((request.method, request.url.path, request.url.host))
            if self.storage_failure == "timeout":
                raise httpx.ReadTimeout("private receiver address", request=request)
            if self.storage_failure == "malformed":
                return httpx.Response(200, text="<html>Bad response</html>")
            if self.storage_failure:
                return httpx.Response(self.storage_failure)
            return httpx.Response(200, json=self.storage)
        return super().__call__(request)


def free_space(page):
    return re.search(r'class="recording-free-space">.*?<strong>(.*?)</strong>', page.text).group(1)


def test_recording_page_updates_space_on_refresh_and_folder_change(setup):
    _, _, app = setup
    box = StorageReceiver()
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200 and free_space(page) == "120.4 GB"
        assert (
            page.text.index('id="recording-directory"')
            < page.text.index('class="recording-free-space"')
            < page.text.index('id="recording-filter"')
        )
        box.storage["hdd"][0]["free"] = "119.8 GB"
        page = client.get(
            "/aufnahmen", params={"live_receiver": "1"}, headers={"X-Live-Refresh": "1"}
        )
        assert free_space(page) == "119.8 GB"
        page = client.get("/aufnahmen", params={"directory": "/media/usb/"})
        assert free_space(page) == "42 GB" and "Musik.ts" in page.text
        page = client.get("/aufnahmen", params={"directory": "/media/net/Archiv/"})
        assert free_space(page) == "unbekannt" and "Keine Aufnahmen" in page.text
    assert not box.writes


@pytest.mark.parametrize("failure", [503, 401, "timeout", "malformed"])
def test_storage_failure_keeps_recordings_and_actions_available(setup, failure):
    _, _, app = setup
    box = StorageReceiver()
    box.storage_failure = failure
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    with TestClient(app) as client:
        login(client, "admin", "Admin-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200 and free_space(page) == "unbekannt"
        assert "Tagesschau" in page.text and "Herunterladen" in page.text
        assert 'action="/aufnahmen/delete"' in page.text
        assert "Aufnahmeliste nicht erreichbar" not in page.text
        assert "private receiver address" not in page.text
    assert not box.writes
