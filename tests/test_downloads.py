import html
import re
from functools import partial
from urllib.parse import parse_qs, quote, urlencode, urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient
from ownership_support import owned_rows
from sqlalchemy import delete
from sqlalchemy.orm import Session
from test_foundation import login
from test_foundation import setup as setup
from test_recordings import (
    FILENAME,
    ROOT,
    MovieReceiver,
    delete_form,
    install_movie_mock,
    movie_row,
)
from test_timers import timer_row

from e2web.config import load_config
from e2web.db import Grant, Receiver, User, WebSession
from e2web.openwebif import OpenWebifClient, ReceiverError


def download_url(page):
    return html.unescape(re.search(r'href="([^"]*/aufnahmen/download\?[^"]+)"', page.text)[1])


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize(
    "byte_range, expected",
    [
        (None, None),
        ("bytes=2-7", slice(2, 8)),
        ("bytes=3-", slice(3, None)),
        ("bytes=-5", slice(-5, None)),
        ("bytes=999-", "outside"),
    ],
)
def test_recording_download_exact_bytes_ranges_and_utf8_filename(setup, xml, byte_range, expected):
    _, engine, app = setup
    box = install_movie_mock(app, xml=xml)
    filename = ROOT + "Grüße + A & B.ts"
    box.movies = [movie_row(filename=filename, serviceref="1:0:0:0:0:0:0:0:0:0:" + filename)]
    with Session(engine) as db:
        db.get(Grant, (2, 1)).can_write = False
        db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        url = download_url(client.get("/aufnahmen"))
        result = client.get(url, headers={"Range": byte_range} if byte_range else {})
        if expected == "outside":
            assert result.status_code == 416 and result.content == b""
            assert result.headers["content-range"] == f"bytes */{len(box.file_content)}"
        else:
            assert result.status_code == (206 if byte_range else 200)
            assert result.content == (box.file_content[expected] if expected else box.file_content)
            assert result.headers["content-type"] == "application/octet-stream"
            assert (
                f"filename*=UTF-8''{quote(filename.rsplit('/', 1)[-1], safe='')}"
                in result.headers["content-disposition"]
            )
            assert result.headers["x-accel-buffering"] == "no"
            assert result.headers["accept-ranges"] == "bytes"
        assert len(box.file_requests) == 1
        request = box.file_requests[0]
        assert (
            request.url.params["file"] == filename
            and request.headers["accept-encoding"] == "identity"
        )
        assert request.headers.get("Range") == byte_range
        assert not box.writes


@pytest.mark.parametrize(
    "kind", ["receiver", "reference", "directory", "grant", "missing", "range"]
)
def test_forged_or_stale_download_rejected_before_file_request(setup, kind):
    _, engine, app = setup
    box = install_movie_mock(app)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        url = download_url(client.get("/aufnahmen"))
        headers = {}
        if kind == "receiver":
            url = url.replace("receiver_id=1", "receiver_id=2")
        elif kind == "reference":
            parsed = urlsplit(url)
            params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
            params["reference"] = "1:0:0:0:0:0:0:0:0:0:/etc/passwd"
            url = parsed.path + "?" + urlencode(params)
        elif kind == "directory":
            url = url.replace("directory=" + quote(ROOT, safe=""), "directory=%2Fetc%2F")
        elif kind == "grant":
            with Session(engine) as db:
                db.delete(db.get(Grant, (2, 1)))
                db.commit()
        elif kind == "missing":
            box.movies = []
        else:
            headers["Range"] = "bytes=0-2,4-6"
        result = client.get(url, headers=headers)
        assert result.status_code in {403, 404, 409, 416}
        assert not box.file_requests


@pytest.mark.parametrize("change", ["grant", "session", "connection", "inactive"])
@pytest.mark.parametrize("operation", ["download", "delete", "download_file"])
def test_authority_rechecked_after_hdd_wait(setup, change, operation):
    _, engine, app = setup
    box = MovieReceiver()
    owned_rows(app, box.movies)
    armed = False

    def transport(request):
        nonlocal armed
        result = box(request)
        delayed_path = "/file" if operation == "download_file" else "movielist"
        if armed and request.url.path.endswith(delayed_path):
            armed = False
            with Session(engine) as db:
                if change == "grant":
                    if operation == "delete":
                        db.get(Grant, (2, 1)).can_write = False
                    else:
                        db.delete(db.get(Grant, (2, 1)))
                elif change == "session":
                    db.execute(delete(WebSession).where(WebSession.user_id == 2))
                elif change == "connection":
                    db.get(Receiver, 1).hostname = "192.0.2.99"
                else:
                    db.get(User, 2).active = False
                db.commit()
        return result

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(transport))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        armed = True
        result = (
            client.get(download_url(page))
            if operation.startswith("download")
            else client.post("/aufnahmen/delete", data=delete_form(page), follow_redirects=False)
        )
        assert result.status_code in {303, 403, 409}
        assert not box.writes
        assert len(box.file_requests) == (1 if operation == "download_file" else 0)
        assert result.content != box.file_content


@pytest.mark.parametrize("xml", [False, True])
def test_selected_real_default_path_and_empty_xml_directory(setup, xml):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    box.default_path = ROOT + "Archiv/"
    box.paths = [ROOT, box.default_path]
    box.movies = []
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200 and "Keine Aufnahmen" in page.text
        assert f'<option value="{box.default_path}" selected>' in page.text
        assert "Standardpfad des Receivers" not in page.text
        assert "Übergeordneter Ordner" not in page.text


def test_hdd_timeout_default_on_old_config_and_other_calls_stay_short(setup, tmp_path):
    cfg, engine, _ = setup
    path = tmp_path / "old.toml"
    path.write_text('data_dir="data"\nreceiver_timeout=8.0\n')
    assert load_config(path).recording_timeout == 90
    box = MovieReceiver()
    with Session(engine) as db:
        client = OpenWebifClient(db.get(Receiver, 1), cfg, transport=httpx.MockTransport(box))
        client.recording_list()
        client.timer_list()
        stream = client.open_recording(FILENAME)
        assert b"".join(stream.chunks()) == box.file_content
        assert stream.response.is_closed and stream.client.is_closed
    budgets = {path: values["read"] for path, values in box.timeouts}
    assert budgets["/api/movielist"] == 90 and budgets["/file"] == 90
    assert budgets["/api/timerlist"] == cfg.receiver_timeout
    for value in (0, 301, float("nan"), float("inf")):
        path.write_text(f'data_dir="data"\nrecording_timeout={value}\n')
        with pytest.raises(ValueError):
            load_config(path)


@pytest.mark.parametrize(
    "redirect, allowed",
    [
        ("/file/", True),
        ("http://192.0.2.50:80/file/", True),
        ("http://foreign.test/file/", False),
        ("/etc/passwd", False),
        ("//foreign.test/file/", False),
    ],
)
def test_download_redirect_limited_to_same_receiver_file_route(setup, redirect, allowed):
    cfg, engine, _ = setup
    box = MovieReceiver()
    box.file_redirect = redirect
    with Session(engine) as db:
        client = OpenWebifClient(db.get(Receiver, 1), cfg, transport=httpx.MockTransport(box))
        if allowed:
            stream = client.open_recording(FILENAME)
            assert b"".join(stream.chunks()) == box.file_content
            assert len(box.file_requests) == 2
        else:
            with pytest.raises(ReceiverError):
                client.open_recording(FILENAME)
            assert len(box.file_requests) == 1


def test_ambiguous_legacy_filename_and_missing_text_error_are_not_downloaded(setup):
    cfg, engine, _ = setup
    box = MovieReceiver()
    with Session(engine) as db:
        client = OpenWebifClient(db.get(Receiver, 1), cfg, transport=httpx.MockTransport(box))
        with pytest.raises(ReceiverError):
            client.open_recording(ROOT + "%2e%2e%2fpasswd")
        assert not box.file_requests
        with pytest.raises(ReceiverError):
            client.open_recording(ROOT + "missing.ts")


def test_layout_footer_relative_assets_and_active_companion_rows(setup):
    _, _, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row(state=2, filename=FILENAME.removesuffix(".ts"))]
    with TestClient(app, base_url="http://example.test") as client:
        page = client.get("/login")
        assert "Deine Receiver" not in page.text and "auth-panel-single" in page.text
        assert 'href="/static/app.css?v=1.1.11"' in page.text
        assert 'src="/static/app.js?v=1.1.11"' in page.text
        assert "http://example.test" not in page.text
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert "Sendungsdetails" not in page.text
        assert "recording-data-row-with-file recording-active-row" in page.text
        assert 'class="recording-file-row recording-active-row"' in page.text
        assert 'class="recording-file"' in page.text
        assert (
            "<th>Aufnahme</th><th>Sender</th><th>Receiver</th><th>Beginn</th><th>Dauer</th><th>Status</th>"
            in page.text
        )
        page = client.get("/timer")
        assert (
            "<th>Aufnahme</th><th>Sender</th><th>Receiver</th><th>Start</th><th>Ende</th><th>Dauer</th><th>Status</th>"
            in page.text
        )
        assert page.text.count("Zeitzone") == 1
        assert "Version 1.1.11 · Release 07.10.2026 · Zeitzone Europe/Berlin" in page.text
        assert "00:00:00" in page.text  # State is running but mock start lies in the future.
        assert "Dateityp" not in page.text
