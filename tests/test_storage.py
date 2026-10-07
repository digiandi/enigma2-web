import re
from functools import partial
from xml.etree.ElementTree import Element, SubElement, tostring

import httpx
import pytest
from fastapi.testclient import TestClient
from test_catalog import adapter
from test_foundation import login
from test_foundation import setup as setup
from test_recordings import ROOT, MovieReceiver, movie_row

from e2web.openwebif import OpenWebifClient


@pytest.mark.parametrize("xml", [False, True])
def test_all_receiver_disks_are_read_without_mount_or_folder_information(tmp_path, xml):
    seen = []

    def api(request):
        seen.append(request)
        assert request.method == "GET" and not request.url.query
        if xml and request.url.path.startswith("/api/"):
            return httpx.Response(404)
        if xml:
            return httpx.Response(
                200,
                text="<e2deviceinfo><e2frontends><e2frontend><e2model>Tuner</e2model>"
                "</e2frontend></e2frontends><e2hdds><e2hdd>"
                "<e2model>WD(My Passport 0748)</e2model><e2capacity>2000.365 GB</e2capacity>"
                "<e2free>660.884 GB</e2free></e2hdd><e2hdd>"
                "<e2model>USB-SSD</e2model><e2capacity>500 GB</e2capacity>"
                "<e2free>42 GB</e2free></e2hdd></e2hdds></e2deviceinfo>",
            )
        return httpx.Response(
            200,
            json={
                "hdd": [
                    {
                        "model": "WD(My Passport 0748)",
                        "capacity": "2000.365 GB",
                        "free": "660.884 GB",
                    },
                    {"model": "USB-SSD", "capacity": "500 GB", "free": "42 GB"},
                ]
            },
        )

    disks = adapter(tmp_path, api).storage_disks()
    assert [(disk.model, disk.free_space) for disk in disks] == [
        ("WD(My Passport 0748)", "660.884 GB"),
        ("USB-SSD", "42 GB"),
    ]
    assert [request.url.path for request in seen] == (
        ["/api/deviceinfo", "/web/deviceinfo"] if xml else ["/api/deviceinfo"]
    )
    assert all(request.extensions["timeout"]["read"] == 90 for request in seen)


@pytest.mark.parametrize(
    ("free", "expected"),
    [
        ("660.884 GB", "660.884 GB"),
        ("42,5 GB", "42.5 GB"),
        ("0 MB", "0 GB"),
        ("512 MB", "0.5 GB"),
        ("1 TB", "1024 GB"),
        ("2 GiB", "2 GB"),
        ("1 KB", "<0.001 GB"),
        (None, None),
        ("", None),
        ("-1 MB", None),
        ("unknown", None),
        ("NaN GB", None),
        (123, None),
        (True, None),
        ("<b>12 GB</b>", None),
    ],
)
def test_free_space_in_gb_and_unknown_values(tmp_path, free, expected):
    client = adapter(
        tmp_path,
        lambda request: httpx.Response(200, json={"hdd": [{"model": "Disk", "free": free}]}),
    )
    disks = client.storage_disks()
    assert len(disks) == 1 and disks[0].model == "Disk"
    assert disks[0].free_space == expected


@pytest.mark.parametrize("xml", [False, True])
def test_partial_disk_information_keeps_other_disks_visible(tmp_path, xml):
    def api(request):
        if xml and request.url.path.startswith("/api/"):
            return httpx.Response(404)
        if xml:
            return httpx.Response(
                200,
                text="<e2deviceinfo><e2hdds><e2hdd><e2model>Disk</e2model><e2free>-1 MB</e2free>"
                "</e2hdd><e2hdd><e2model>Disk</e2model><e2free>12 GB</e2free></e2hdd>"
                "<e2hdd><e2free>8 GB</e2free></e2hdd></e2hdds></e2deviceinfo>",
            )
        return httpx.Response(
            200,
            json={
                "hdd": [
                    {"model": "Disk", "free": "-1 MB"},
                    None,
                    {"model": "Disk", "free": "12 GB"},
                    {"free": "8 GB"},
                ]
            },
        )

    assert [(disk.model, disk.free_space) for disk in adapter(tmp_path, api).storage_disks()] == [
        ("Disk", None),
        ("Disk", "12 GB"),
        ("Unbekannte Festplatte", "8 GB"),
    ]


class StorageReceiver(MovieReceiver):
    def __init__(self, *, xml=False):
        super().__init__(xml=xml)
        self.storage = {
            "hdd": [
                {"model": "WD(My Passport 0748)", "free": "660.884 GB"},
                {"model": "USB-SSD", "free": "42 GB"},
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
        if request.url.path in {"/api/deviceinfo", "/web/deviceinfo"}:
            self.requests.append((request.method, request.url.path, request.url.host))
            if self.xml and request.url.path.startswith("/api/"):
                return httpx.Response(404)
            if self.storage_failure == "timeout":
                raise httpx.ReadTimeout("private receiver address", request=request)
            if self.storage_failure == "malformed":
                return httpx.Response(200, text="<html>Bad response</html>")
            if self.storage_failure:
                return httpx.Response(self.storage_failure)
            if self.xml:
                root = Element("e2deviceinfo")
                disks = SubElement(root, "e2hdds")
                for disk in self.storage.get("hdd", []):
                    row = SubElement(disks, "e2hdd")
                    for key in ("model", "free"):
                        if disk.get(key) is not None:
                            SubElement(row, "e2" + key).text = str(disk[key])
                return httpx.Response(200, content=tostring(root))
            return httpx.Response(200, json=self.storage)
        return super().__call__(request)


def free_spaces(page):
    return re.findall(r'class="recording-free-space">.*?<strong>(.*?)</strong>', page.text)


@pytest.mark.parametrize("xml", [False, True])
def test_recording_page_updates_every_disk_independently_of_folder(setup, xml):
    _, _, app = setup
    box = StorageReceiver(xml=xml)
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200 and free_spaces(page) == ["660.884 GB", "42 GB"]
        assert "(WD(My Passport 0748))" in page.text and "(USB-SSD)" in page.text
        assert (
            page.text.index('id="recording-directory"')
            < page.text.index('class="recording-storage"')
            < page.text.index('id="recording-filter"')
        )
        box.storage["hdd"][0]["free"] = "659.123 GB"
        page = client.get(
            "/aufnahmen", params={"live_receiver": "1"}, headers={"X-Live-Refresh": "1"}
        )
        assert free_spaces(page) == ["659.123 GB", "42 GB"]
        for directory in ("/media/usb/", "/media/net/Archiv/"):
            page = client.get("/aufnahmen", params={"directory": directory})
            assert free_spaces(page) == ["659.123 GB", "42 GB"]
        box.storage["hdd"][0]["free"] = "-1 MB"
        page = client.get("/aufnahmen")
        assert free_spaces(page) == ["unbekannt", "42 GB"]
        assert "(WD(My Passport 0748))" in page.text
    assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize("failure", [503, 401, "timeout", "malformed"])
def test_storage_failure_keeps_recordings_and_actions_available(setup, xml, failure):
    _, _, app = setup
    box = StorageReceiver(xml=xml)
    box.storage_failure = failure
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    with TestClient(app) as client:
        login(client, "admin", "Admin-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200 and free_spaces(page) == ["unbekannt"]
        assert "Tagesschau" in page.text and "Herunterladen" in page.text
        assert 'action="/aufnahmen/delete"' in page.text
        assert "Aufnahmeliste nicht erreichbar" not in page.text
        assert "private receiver address" not in page.text
    assert not box.writes


@pytest.mark.parametrize("payload", [{}, {"hdd": None}, {"hdd": {}}, {"hdd": []}, []])
def test_missing_disk_list_is_unknown_in_the_page(setup, payload):
    _, _, app = setup
    box = StorageReceiver()
    box.storage = payload
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200 and free_spaces(page) == ["unbekannt"]
        assert "Tagesschau" in page.text
