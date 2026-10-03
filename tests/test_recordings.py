import re
from functools import partial
from urllib.parse import parse_qs
from xml.etree.ElementTree import Element, SubElement, tostring

import httpx
import pytest
from fastapi.testclient import TestClient
from ownership_support import owned_rows
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from test_catalog import adapter
from test_foundation import csrf_value, login
from test_foundation import setup as setup
from test_timers import MockReceiver, input_value, timer_row

from e2web.db import Grant, Receiver, TimerAction
from e2web.openwebif import OpenWebifClient, ReceiverError
from e2web.security import now, token_hash

ROOT = "/media/hdd/movie/"
FILENAME = ROOT + "Nachrichten + A & B.ts"
MOVIE_REFERENCE = "1:0:0:0:0:0:0:0:0:0:" + FILENAME


def movie_row(**changes):
    return {
        "serviceref": MOVIE_REFERENCE,
        "filename": FILENAME,
        "eventname": "Tagesschau",
        "servicename": "Das Erste HD",
        "description": "Nachrichten",
        "descriptionExtended": "Die Nachrichten aus aller Welt.",
        "recordingtime": now() - 86400,
        "length": "15:30",
        "filesize": 1024**3,
        **changes,
    }


class MovieReceiver(MockReceiver):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.movies = [movie_row()]
        self.reject_delete = False
        self.status_unavailable = False
        self.file_requests = []
        self.file_content = b"Enigma2 recording bytes\x00\xff"
        self.file_redirect = None
        self.file_content_type = "video/mpeg"
        self.default_path = ROOT
        self.paths = [ROOT]
        self.timeouts = []

    def movie_xml(self, movies, folders):
        root = Element("e2movielist")
        mapping = {
            "serviceref": "e2servicereference",
            "filename": "e2filename",
            "eventname": "e2title",
            "servicename": "e2servicename",
            "description": "e2description",
            "descriptionExtended": "e2descriptionextended",
            "recordingtime": "e2time",
            "length": "e2length",
            "filesize": "e2filesize",
            "tags": "e2tags",
        }
        for movie in movies:
            row = SubElement(root, "e2movie")
            for key, tag in mapping.items():
                SubElement(row, tag).text = str(movie.get(key, ""))
        paths = SubElement(root, "e2locations")
        for folder in folders:
            SubElement(paths, "e2location").text = folder
        return tostring(root)

    def __call__(self, request):
        self.timeouts.append((request.url.path, request.extensions.get("timeout")))
        method = request.url.path.rsplit("/", 1)[-1]
        if request.url.path.rstrip("/") == "/file":
            self.file_requests.append(request)
            if self.file_redirect and request.url.path == "/file":
                return httpx.Response(302, headers={"Location": self.file_redirect})
            assert request.method == "GET"
            assert request.url.params["action"] == "download"
            if request.url.params["file"] not in {r["filename"] for r in self.movies}:
                return httpx.Response(200, text="File not found")
            data = self.file_content
            headers = {
                "Content-Disposition": "attachment",
                "Accept-Ranges": "bytes",
                "Content-Type": self.file_content_type,
            }
            status = 200
            if byte_range := request.headers.get("Range"):
                spec = byte_range.removeprefix("bytes=")
                first, last = spec.split("-")
                start = int(first) if first else max(0, len(data) - int(last))
                end = min(int(last), len(data) - 1) if first and last else len(data) - 1
                if start >= len(data) or end < start:
                    return httpx.Response(
                        416,
                        headers={"Content-Range": f"bytes */{len(data)}"},
                        stream=httpx.ByteStream(b""),
                    )
                headers["Content-Range"] = f"bytes {start}-{end}/{len(data)}"
                data, status = data[start : end + 1], 206
            headers["Content-Length"] = str(len(data))
            return httpx.Response(status, headers=headers, stream=httpx.ByteStream(data))
        if method in {"getlocations", "getcurrlocation"}:
            self.requests.append((request.method, request.url.path, request.url.host))
            if self.xml and request.url.path.startswith("/api/"):
                return httpx.Response(404)
            if method == "getlocations":
                if self.xml:
                    root = Element("e2locations")
                    for path in self.paths:
                        SubElement(root, "e2location").text = path
                    return httpx.Response(200, content=tostring(root))
                return httpx.Response(
                    200, json={"locations": self.paths, "default": self.default_path}
                )
            if self.xml:
                return httpx.Response(200, text=f"<e2location>{self.default_path}</e2location>")
            return httpx.Response(200, json={"result": True, "location": self.default_path})
        if method not in {"movielist", "moviedelete"}:
            if method == "timerlist" and self.status_unavailable:
                return httpx.Response(503)
            return super().__call__(request)
        self.requests.append((request.method, request.url.path, request.url.host))
        if self.xml and request.url.path.startswith("/api/"):
            return httpx.Response(404)
        if method == "movielist":
            assert request.method == "GET"
            directory = request.url.params.get("dirname", self.default_path)
            movies = [
                row for row in self.movies if row["filename"].rsplit("/", 1)[0] + "/" == directory
            ]
            folders = ["Serien"] if directory == ROOT else []
            if self.xml:
                return httpx.Response(200, content=self.movie_xml(movies, folders))
            return httpx.Response(
                200, json={"movies": movies, "directory": directory, "bookmarks": folders}
            )
        assert request.method == "POST"
        params = {
            k: v[0] for k, v in parse_qs(request.content.decode(), keep_blank_values=True).items()
        }
        assert set(params) == {"sRef"}  # A force parameter bypasses the receiver's trash policy.
        self.writes.append((method, params, request.url.host))
        if not self.reject_delete:
            self.movies = [row for row in self.movies if row["serviceref"] != params["sRef"]]
        if self.lost_reply:
            raise httpx.ReadTimeout("private receiver address", request=request)
        if self.xml:
            state = "False" if self.reject_delete else "True"
            return httpx.Response(
                200,
                text=f"<e2simplexmlresult><e2state>{state}</e2state>"
                "<e2statetext>OK</e2statetext></e2simplexmlresult>",
            )
        return httpx.Response(200, json={"result": not self.reject_delete})


def install_movie_mock(app, **kwargs):
    box = MovieReceiver(**kwargs)
    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(box))
    return box


def delete_form(page, **changes):
    return {
        "csrf_token": csrf_value(page),
        "action_token": input_value(page, "action_token"),
        "confirmed": "true",
        **changes,
    }


@pytest.mark.parametrize("xml", [False, True])
def test_movie_formats_folder_navigation_and_explicit_single_use_delete(setup, xml):
    cfg, engine, app = setup
    box = install_movie_mock(app, xml=xml)
    owned_rows(app, box.movies)
    with Session(engine) as db:
        listing = app.state.client_factory(db.get(Receiver, 1), cfg).recording_list()
        assert listing.xml == xml and listing.directory == ROOT
        movie = listing.recordings[0]
        assert movie.reference == MOVIE_REFERENCE and movie.filename == FILENAME
        assert movie.duration == 930 and movie.size_label == "1.0 GiB"
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert "<h1>Aufnahmen: VU+ Duo 4K</h1>" in page.text
        assert "Nachrichten + A &amp; B.ts" in page.text
        assert f'value="{ROOT}Serien/"' in page.text and "00:15:30" in page.text
        assert "folder-navigation" not in page.text
        assert not box.writes
        form = delete_form(page)
        missing = client.post("/aufnahmen/delete", data={**form, "confirmed": "0"})
        assert missing.status_code == 400 and "recording-table" in missing.text
        assert not box.writes
        bad_csrf = client.post("/aufnahmen/delete", data={**form, "csrf_token": "forged"})
        assert bad_csrf.status_code == 403 and not box.writes
        result = client.post("/aufnahmen/delete", data=form, follow_redirects=False)
        assert result.status_code == 303 and result.headers["location"].startswith("/aufnahmen?")
        assert box.writes == [("moviedelete", {"sRef": MOVIE_REFERENCE}, "192.0.2.50")]
        assert not box.movies
        assert client.post("/aufnahmen/delete", data=form).status_code == 409
        assert len(box.writes) == 1
        empty = client.get(result.headers["location"])
        assert "<h1>Aufnahmen: VU+ Duo 4K</h1>" in empty.text and "Keine Aufnahmen" in empty.text
        child = client.get("/aufnahmen", params={"directory": ROOT + "Serien/"})
        assert child.status_code == 200 and "Übergeordneter Ordner" not in child.text
        before = len(box.requests)
        assert client.get("/aufnahmen", params={"directory": "/etc/"}).status_code == 403
        assert all(method == "GET" for method, _, _ in box.requests[before:])
        assert not box.writes[1:]  # Only configured roots may be probed; no further write.
        assert client.get("/aufnahmen", params={"directory": ROOT + "../"}).status_code == 400
    assert all(
        path.startswith("/web/" if xml else "/api/")
        for method, path, _ in box.requests
        if method == "POST"
    )


@pytest.mark.parametrize("xml", [False, True])
def test_folder_dropdown_supports_unicode_children_ancestors_and_live_refresh(setup, xml):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    child = ROOT + "Udo Jürgens/"
    grandchild = child + "Konzerte/"
    folders = {
        ROOT: ["Udo Jürgens", "Udo Jürgens/", "/etc/", "../", ROOT],
        child: ["Konzerte", "../", ROOT],
        grandchild: [],
    }
    queries = []

    def transport(request):
        if request.url.path.endswith("movielist"):
            path = request.url.params.get("dirname", ROOT)
            queries.append(path)
            if xml and request.url.path.startswith("/api/"):
                return httpx.Response(404)
            if xml:
                return httpx.Response(200, content=box.movie_xml([], folders[path]))
            return httpx.Response(
                200, json={"movies": [], "directory": path, "bookmarks": folders[path]}
            )
        return box(request)

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(transport))

    def options(page):
        select = re.search(r'<select id="recording-directory".*?</select>', page.text, re.S)[0]
        return re.findall(r'<option value="([^"]+)"', select)

    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200
        assert options(page) == [ROOT, child]
        assert "data-auto-submit" in page.text and "folder-navigation" not in page.text
        folders[ROOT].append("Neue Aufnahmen")
        page = client.get("/aufnahmen?live_receiver=1", headers={"X-Live-Refresh": "1"})
        assert ROOT + "Neue Aufnahmen/" in options(page)
        page = client.get("/aufnahmen", params={"directory": child})
        assert options(page) == [ROOT, child, grandchild]
        assert f'value="{child}" selected' in page.text
        page = client.get("/aufnahmen", params={"directory": grandchild})
        assert options(page) == [ROOT, child, grandchild]
        assert f'value="{grandchild}" selected' in page.text
        assert client.get("/aufnahmen", params={"directory": "/etc/"}).status_code == 403
        assert "/etc/" not in queries and not any(".." in path for path in queries)
        assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize("filename", [FILENAME.removesuffix(".ts"), ""])
def test_running_recording_is_protected_on_list_and_rechecked_before_delete(setup, xml, filename):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    owned_rows(app, box.movies)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        stale = client.get("/aufnahmen")
        box.timers = [timer_row(state=2, filename=filename)]
        page = client.get("/aufnahmen")
        assert 'action="/aufnahmen/delete"' not in page.text
        assert "Läuft</span>" in page.text if filename else "Unbekannt</span>" in page.text
        assert "Zum Beenden den laufenden Timer öffnen." not in page.text
        rejected = client.post("/aufnahmen/delete", data=delete_form(stale))
        assert rejected.status_code == 409 and "läuft noch" in rejected.text
        assert "recording-table" in rejected.text and not box.writes


def test_unknown_recording_status_disables_delete_and_stale_files_are_rejected(setup):
    _, _, app = setup
    box = install_movie_mock(app)
    owned_rows(app, box.movies)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        first = client.get("/aufnahmen")
        box.status_unavailable = True
        page = client.get("/aufnahmen")
        assert "Status laufender Aufnahmen" in page.text
        assert 'action="/aufnahmen/delete"' not in page.text
        assert client.post("/aufnahmen/delete", data=delete_form(first)).status_code == 502
        box.status_unavailable = False
        first = client.get("/aufnahmen")
        box.movies[0]["filesize"] += 1
        changed = client.post("/aufnahmen/delete", data=delete_form(first))
        assert changed.status_code == 409 and "geändert oder entfernt" in changed.text
        assert "recording-table" in changed.text and not box.writes


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize("outcome", ["rejected", "unknown"])
def test_movie_delete_errors_stay_in_list_without_automatic_retry(setup, xml, outcome):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    owned_rows(app, box.movies)
    box.reject_delete = outcome == "rejected"
    box.lost_reply = outcome == "unknown"
    with TestClient(app) as client:
        login(client, "user", "User-123")
        form = delete_form(client.get("/aufnahmen"))
        response = client.post("/aufnahmen/delete", data=form)
        assert response.status_code == (409 if outcome == "rejected" else 502)
        assert "<h1>Aufnahmen: VU+ Duo 4K</h1>" in response.text
        assert "abgelehnt" in response.text if outcome == "rejected" else "unklar" in response.text
        assert len(box.writes) == 1
        assert client.post("/aufnahmen/delete", data=form).status_code == 409
        assert len(box.writes) == 1


@pytest.mark.parametrize("change", ["grant", "connection"])
def test_stale_movie_authority_cannot_delete(setup, change):
    _, engine, app = setup
    box = install_movie_mock(app)
    owned_rows(app, box.movies)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        form = delete_form(client.get("/aufnahmen"))
        with Session(engine) as db:
            if change == "grant":
                db.execute(delete(Grant).where(Grant.user_id == 2))
            else:
                db.get(Receiver, 1).hostname = "192.0.2.99"
            db.commit()
        assert client.post("/aufnahmen/delete", data=form).status_code == 409
        assert not box.writes


def test_timer_movie_domains_and_shared_receiver_lease_cannot_be_bypassed(setup):
    _, engine, app = setup
    box = install_movie_mock(app)
    owned_rows(app, box.movies)
    box.timers = [timer_row()]
    owned_rows(app, box.timers)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        timer = client.get("/timer")
        movie = client.get("/aufnahmen")
        assert client.post("/aufnahmen/delete", data=delete_form(timer)).status_code == 409
        assert client.post("/timer/delete", data=delete_form(movie)).status_code == 409
        with Session(engine) as db:
            lease = db.get(TimerAction, token_hash(input_value(timer, "action_token")))
            lease.locked_receiver_id, lease.lock_until = 1, now() + 300
            lease.used_at = now()
            db.commit()
        blocked = client.post("/aufnahmen/delete", data=delete_form(movie))
        assert blocked.status_code == 409 and "läuft bereits" in blocked.text
        assert not box.writes
        with Session(engine) as db:
            lease = db.scalar(select(TimerAction).where(TimerAction.locked_receiver_id == 1))
            lease.lock_until = now() - 1
            db.commit()
        assert (
            client.post(
                "/aufnahmen/delete", data=delete_form(movie), follow_redirects=False
            ).status_code
            == 303
        )
        assert len(box.writes) == 1


def test_receiver_cannot_be_removed_during_a_recording_write(setup):
    _, engine, app = setup
    install_movie_mock(app)
    with TestClient(app) as client:
        login(client)
        page = client.get("/admin/receivers")
        client.get("/aufnahmen")
        with Session(engine) as db:
            action = db.scalar(select(TimerAction))
            action.locked_receiver_id, action.lock_until, action.used_at = 2, now() + 300, now()
            db.commit()
        result = client.post(
            "/admin/receivers/2/delete",
            data={"csrf_token": csrf_value(page), "confirmed": "true"},
        )
        assert result.status_code == 409 and "Receiver" in result.text
        with Session(engine) as db:
            assert db.get(Receiver, 2) is not None


@pytest.mark.parametrize(
    "changes",
    [
        {"serviceref": "1:0:1:channel"},
        {"filename": "/etc/other-file"},
        {"serviceref": "1:0:0:0:0:0:0:0:0:0:/media/../etc/file", "filename": "/media/../etc/file"},
        {"filesize": -2},
        {"recordingtime": True},
    ],
)
def test_malformed_movie_metadata_never_becomes_a_delete_target(tmp_path, changes):
    client = adapter(
        tmp_path, lambda request: httpx.Response(200, json={"movies": [movie_row(**changes)]})
    )
    with pytest.raises(ReceiverError):
        client.recording_list()


def test_legacy_unknown_movie_metadata_is_displayable(tmp_path):
    movie = movie_row(recordingtime=-1, length="?:??", filesize=-1)
    client = adapter(tmp_path, lambda request: httpx.Response(200, json={"movies": [movie]}))
    parsed = client.recording_list().recordings[0]
    assert parsed.begin == 0 and parsed.duration is None and parsed.size is None


@pytest.mark.parametrize("operation", ["delete", "rejected", "download", "poll", "folder"])
def test_canonical_receiver_path_remains_authorized_after_followup(setup, operation):
    cfg, engine, app = setup
    box = MovieReceiver()
    box.default_path = "/hdd/movie/"
    box.paths = ["/hdd/movie/"]
    box.movies.append(
        movie_row(
            filename=ROOT + "Serien/Folge.ts",
            serviceref="1:0:0:0:0:0:0:0:0:0:" + ROOT + "Serien/Folge.ts",
        )
    )
    owned_rows(app, box.movies)
    query_paths = []

    def transport(request):
        if request.url.path.endswith("movielist"):
            path = request.url.params.get("dirname", box.default_path)
            query_paths.append(path)
            if path.startswith("/hdd/"):
                request = httpx.Request(
                    request.method,
                    request.url.copy_set_param("dirname", "/media" + path),
                    content=request.content,
                    headers=request.headers,
                )
        return box(request)

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(transport))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200 and ROOT in page.text
        if operation in {"delete", "rejected"}:
            box.reject_delete = operation == "rejected"
            response = client.post("/aufnahmen/delete", data=delete_form(page))
            assert response.status_code == (409 if box.reject_delete else 200)
            assert "recording-table" in response.text or "Keine Aufnahmen" in response.text
            assert "außerhalb der Aufnahmepfade" not in response.text
            assert len(box.writes) == 1
            assert (
                bool(any(row["serviceref"] == MOVIE_REFERENCE for row in box.movies))
                == box.reject_delete
            )
        elif operation == "download":
            response = client.get(
                "/aufnahmen/download",
                params={"receiver_id": 1, "reference": MOVIE_REFERENCE, "directory": ROOT},
            )
            assert response.status_code == 200 and response.content == box.file_content
        else:
            response = client.get(
                "/aufnahmen",
                params={
                    "directory": ROOT + "Serien/" if operation == "folder" else ROOT,
                    "live_receiver": "1",
                },
            )
            assert response.status_code == 200
            assert (
                "Folge.ts" in response.text
                if operation == "folder"
                else "Tagesschau" in response.text
            )
        assert client.get("/aufnahmen", params={"directory": "/etc/"}).status_code == 403
        assert "/etc/" not in query_paths
        assert client.get("/aufnahmen", params={"directory": ROOT + "../"}).status_code == 400
        assert not any(".." in path for path in query_paths)


def test_canonical_path_resolution_does_not_assume_hdd_alias_is_valid(setup):
    _, _, app = setup
    box = install_movie_mock(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert client.get("/aufnahmen", params={"directory": "/hdd/movie/"}).status_code == 403
        assert not box.writes
