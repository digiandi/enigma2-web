import html
import re
import struct
from functools import partial

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from e2web.cli import initialize
from e2web.config import Config, load_config
from e2web.db import Grant, Receiver, User, WebSession, make_engine, migrate
from e2web.main import create_app
from e2web.openwebif import OpenWebifClient, ReceiverError
from e2web.ownership import ensure_owner_tag
from e2web.security import cipher, now, passwords


def csrf_value(response):
    return html.unescape(re.search(r'name="csrf_token" value="([^"]+)"', response.text)[1])


def login(client, name="admin", password="Admin-123"):
    page = client.get("/login")
    return client.post(
        "/login",
        data={"username": name, "password": password, "csrf_token": csrf_value(page)},
        follow_redirects=False,
    )


@pytest.fixture
def setup(tmp_path):
    cfg = Config(data_dir=tmp_path)
    cfg.key_path.write_bytes(Fernet.generate_key())
    migrate(cfg)
    engine = make_engine(cfg)
    with Session(engine) as db:
        db.add_all(
            [
                User(
                    username="admin",
                    display_name="Andreas",
                    password_hash=passwords.hash("Admin-123"),
                    role="admin",
                    active=True,
                    all_receivers=True,
                    must_change_password=False,
                ),
                User(
                    username="user",
                    display_name="Benutzer",
                    password_hash=passwords.hash("User-123"),
                    role="user",
                    active=True,
                    all_receivers=False,
                    must_change_password=False,
                ),
            ]
        )
        db.add_all(
            [
                Receiver(name="VU+ Duo 4K", hostname="192.0.2.50"),
                Receiver(name="DM920", hostname="192.0.2.51"),
            ]
        )
        db.commit()
        for user in db.scalars(select(User)):
            ensure_owner_tag(db, user)
        db.add(Grant(user_id=2, receiver_id=1))
        db.commit()
    app = create_app(cfg)
    yield cfg, engine, app
    engine.dispose()


@pytest.mark.parametrize("session_state", ["anonymous", "admin", "password_change"])
def test_favicons_persist_without_login_and_private_pages_are_not_cached(setup, session_state):
    _, engine, app = setup
    if session_state == "password_change":
        with Session(engine) as db:
            db.get(User, 1).must_change_password = True
            db.commit()
    with TestClient(app, follow_redirects=False) as client:
        if session_state != "anonymous":
            assert login(client).status_code == 303
        for path, media_type in [
            ("/favicon.ico?v=1.1.13", "image/vnd.microsoft.icon"),
            ("/static/favicon.ico", "image/vnd.microsoft.icon"),
            ("/static/favicon.png", "image/png"),
        ]:
            response = client.get(path)
            assert response.status_code == 200
            assert response.headers["content-type"] == media_type
            assert response.headers["cache-control"] == "public, max-age=86400"
            assert "set-cookie" not in response.headers
            assert response.headers["x-content-type-options"] == "nosniff"
            if "ico" in media_type:
                reserved, kind, count = struct.unpack_from("<HHH", response.content)
                assert (reserved, kind, count) == (0, 1, 3)
                sizes = {
                    struct.unpack_from("<BB", response.content, 6 + 16 * index)
                    for index in range(count)
                }
                assert sizes == {(16, 16), (32, 32), (48, 48)}
            else:
                assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
            head = client.head(path)
            assert head.status_code == 200 and head.content == b""
            assert head.headers["cache-control"] == "public, max-age=86400"
        icon = client.get("/static/favicon.png")
        not_modified = client.get(
            "/static/favicon.png", headers={"If-None-Match": icon.headers["etag"]}
        )
        assert not_modified.status_code == 304
        assert not_modified.headers["cache-control"] == "public, max-age=86400"
        for path in ["/login", "/health", "/admin/users", "/static/app.css", "/static/app.js"]:
            assert client.get(path).headers["cache-control"] == "no-store"
        missing = client.get("/static/favicon-missing.png")
        assert missing.status_code == 404 and missing.headers["cache-control"] == "no-store"
        invalid_method = client.post("/favicon.ico")
        assert invalid_method.status_code == 405
        assert invalid_method.headers["cache-control"] == "no-store"
        if session_state == "anonymous":
            page = client.get("/login")
            assert (
                'rel="icon" type="image/vnd.microsoft.icon" sizes="16x16 32x32 48x48" '
                'href="/favicon.ico?v=1.1.13"'
            ) in page.text


def test_login_csrf_cookies_and_logout(setup):
    _, engine, app = setup
    with TestClient(app) as client:
        assert client.get("/admin/users", follow_redirects=False).status_code == 303
        assert (
            client.post("/login", data={"username": "admin", "password": "Admin-123"}).status_code
            == 403
        )
        response = login(client)
        assert response.status_code == 303
        assert "HttpOnly" in response.headers["set-cookie"]
        assert "SameSite=lax" in response.headers["set-cookie"]
        page = client.get("/admin/users")
        assert "Andreas" in page.text
        assert client.post("/logout", data={"csrf_token": "fälschung"}).status_code == 403
        assert (
            client.post(
                "/logout", data={"csrf_token": csrf_value(page)}, follow_redirects=False
            ).status_code
            == 303
        )
        assert client.get("/sender", follow_redirects=False).headers["location"] == "/login"
    with Session(engine) as db:
        assert not list(db.scalars(select(WebSession)))


def test_https_cookies_are_separate_and_secure(setup):
    _, _, app = setup
    with TestClient(app, base_url="https://example.test") as client:
        response = login(client)
        assert "__Host-e2web_session=" in response.headers["set-cookie"]
        assert "Secure" in response.headers["set-cookie"]
        assert client.get("https://example.test/admin/users").status_code == 200
        assert (
            client.get("http://example.test/admin/users", follow_redirects=False).status_code == 303
        )


def test_grants_apply_to_selection_and_sender_query(setup):
    _, _, app = setup
    seen = []

    def api(request):
        seen.append(request.url.host)
        return httpx.Response(200, json={"services": []})

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(api))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/sender")
        assert "VU+ Duo 4K" in page.text and "DM920" not in page.text
        assert "192.0.2.50" not in page.text
        assert seen == ["192.0.2.50"]
        assert client.get("/admin/receivers").status_code == 403
        assert (
            client.post(
                "/receiver/select", data={"receiver_id": 2, "csrf_token": csrf_value(page)}
            ).status_code
            == 403
        )
        assert seen == ["192.0.2.50"]


def test_receiver_encryption_edit_and_read_only_test(setup):
    cfg, engine, app = setup
    seen = []

    def api(request):
        seen.append((request.method, request.url.path))
        assert request.headers["authorization"].startswith("Basic ")
        return httpx.Response(200, json={"result": True, "services": []})

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(api))
    with TestClient(app) as client:
        login(client)
        page = client.get("/admin/receivers/new")
        form = {
            "csrf_token": csrf_value(page),
            "name": "Box 3",
            "hostname": "192.0.2.52",
            "port": 80,
            "sort_order": 0,
            "enabled": "on",
            "verify_tls": "on",
            "username": "root",
            "password": "Secret-Receiver-123",
        }
        assert (
            client.post("/admin/receivers/save", data=form, follow_redirects=False).status_code
            == 303
        )
        with Session(engine) as db:
            box = db.scalar(select(Receiver).where(Receiver.name == "Box 3"))
            box_id, ciphertext = box.id, box.encrypted_password
            assert "Secret-Receiver-123" not in ciphertext
            assert cipher(cfg).decrypt(ciphertext.encode()).decode() == "Secret-Receiver-123"
        page = client.get(f"/admin/receivers/{box_id}/edit")
        assert "Secret-Receiver-123" not in page.text and ciphertext not in page.text
        form.update(id=box_id, password="", name="Umbenannte Box", csrf_token=csrf_value(page))
        client.post("/admin/receivers/save", data=form)
        with Session(engine) as db:
            assert db.get(Receiver, box_id).encrypted_password == ciphertext
        page = client.get("/admin/receivers")
        result = client.post(
            f"/admin/receivers/{box_id}/test", data={"csrf_token": csrf_value(page)}
        )
        assert "Verbindung erfolgreich" in result.text
        assert seen == [("GET", "/api/getservices")]


def test_new_user_forced_password_change_revokes_sessions(setup):
    _, engine, app = setup
    with TestClient(app) as admin:
        login(admin)
        page = admin.get("/admin/users/new")
        response = admin.post(
            "/admin/users/save",
            data={
                "csrf_token": csrf_value(page),
                "username": "newuser",
                "display_name": "Neuer Benutzer",
                "role": "user",
                "active": "on",
                "all_receivers": "on",
                "password": "Start-123",
                "password_confirmation": "Start-123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
    with TestClient(app) as client:
        assert login(client, "newuser", "Start-123").headers["location"] == "/account/password"
        assert (
            client.get("/sender", follow_redirects=False).headers["location"] == "/account/password"
        )
        page = client.get("/account/password")
        response = client.post(
            "/account/password",
            data={
                "csrf_token": csrf_value(page),
                "current_password": "Start-123",
                "password": "Own-123",
                "password_confirmation": "Own-123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert client.get("/admin/users", follow_redirects=False).headers["location"] == "/login"
        assert login(client, "newuser", "Own-123").headers["location"] == "/"
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.username == "newuser"))
        assert not user.must_change_password


def test_last_admin_self_protection_and_session_revocation(setup):
    _, _, app = setup
    with TestClient(app) as admin, TestClient(app) as user:
        login(admin)
        login(user, "user", "User-123")
        page = admin.get("/admin/users/1/edit")
        token = csrf_value(page)
        response = admin.post(
            "/admin/users/save",
            data={
                "id": 1,
                "csrf_token": token,
                "display_name": "Andreas",
                "role": "user",
                "active": "on",
            },
        )
        assert response.status_code == 400
        assert (
            admin.post(
                "/admin/users/1/delete", data={"csrf_token": token, "confirmed": "true"}
            ).status_code
            == 400
        )
        page = admin.get("/admin/users/2/edit")
        response = admin.post(
            "/admin/users/save",
            data={
                "id": 2,
                "csrf_token": csrf_value(page),
                "display_name": "Benutzer",
                "role": "user",
                "all_receivers": "on",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert user.get("/sender", follow_redirects=False).headers["location"] == "/login"
        assert login(user, "user", "User-123").status_code == 400


def test_throttle_and_expired_session(setup):
    _, engine, app = setup
    with TestClient(app) as client:
        for _ in range(10):
            assert login(client, password="wrong").status_code == 400
        assert login(client).status_code == 429
    with Session(engine) as db:
        from e2web.db import LoginAttempt

        for row in db.scalars(select(LoginAttempt)):
            row.attempted_at = now() - 1000
        db.commit()
    with TestClient(app) as client:
        assert login(client).status_code == 303
        with Session(engine) as db:
            for session in db.scalars(select(WebSession)):
                session.expires_at = now() - 1
            db.commit()
        assert client.get("/sender", follow_redirects=False).status_code == 303


def test_xml_fallback_and_failure_no_redirect_leak(setup):
    cfg, engine, _ = setup
    with Session(engine) as db:
        receiver = db.get(Receiver, 1)
        seen = []

        def xml_api(request):
            seen.append(request.url.path)
            if request.url.path.startswith("/api/"):
                return httpx.Response(404)
            return httpx.Response(
                200,
                text="<e2servicelist><e2service>"
                "<e2servicereference>1:7:abc</e2servicereference>"
                "<e2servicename>Favoriten</e2servicename></e2service></e2servicelist>",
            )

        rows = OpenWebifClient(receiver, cfg, transport=httpx.MockTransport(xml_api)).services()
        assert rows == [{"reference": "1:7:abc", "name": "Favoriten"}]
        assert seen == ["/api/getservices", "/web/getservices"]
        for status in [401, 403, 302]:

            def fail(request):
                return httpx.Response(status, headers={"Location": "https://untrusted.invalid/"})

            with pytest.raises(ReceiverError) as exc:
                OpenWebifClient(receiver, cfg, transport=httpx.MockTransport(fail)).services()
            assert "untrusted" not in str(exc.value)


def test_migration_is_repeatable_and_key_is_preserved(tmp_path):
    path = tmp_path / "e2web.toml"
    initialize(path)
    cfg = load_config(path)
    original = cfg.key_path.read_bytes()
    initialize(path)
    assert cfg.key_path.read_bytes() == original
    engine = make_engine(cfg)
    with engine.connect() as connection:
        assert connection.scalar(text("PRAGMA journal_mode")) == "wal"
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
        assert set(inspect(connection).get_table_names()) >= {
            "users",
            "receivers",
            "sessions",
            "user_receiver_permissions",
            "alembic_version",
        }
    engine.dispose()
    cfg.key_path.unlink()
    with pytest.raises(ValueError, match="Schlüssel fehlt"):
        initialize(path)


def test_templates_and_validation_do_not_echo_passwords(setup):
    _, _, app = setup
    with TestClient(app) as client:
        login(client)
        for url in [
            "/admin/users",
            "/admin/users/new",
            "/admin/users/2/edit",
            "/admin/receivers",
            "/admin/receivers/new",
            "/admin/receivers/1/edit",
            "/account/password",
            "/epg",
            "/timer",
            "/aufnahmen",
        ]:
            assert client.get(url).status_code == 200
        page = client.get("/admin/receivers/new")
        response = client.post(
            "/admin/receivers/save",
            data={
                "csrf_token": csrf_value(page),
                "name": '<script>alert("x")</script>',
                "hostname": "http://bad/path",
                "port": 80,
                "sort_order": 0,
                "password": "never-echo-this",
            },
        )
        assert response.status_code == 400
        assert "never-echo-this" not in response.text
        assert '<script>alert("x")</script>' not in response.text


def test_openwebif_escapes_display_names_and_rejects_unknown_formats(setup):
    cfg, engine, _ = setup
    with Session(engine) as db:
        receiver = db.get(Receiver, 1)
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"services": [{"servicereference": "1:0:1:abc", "servicename": "A &amp; B"}]},
            )
        )
        assert OpenWebifClient(receiver, cfg, transport=transport).services()[0]["name"] == "A & B"
        for response in [{"result": False, "services": []}, {"services": ["unexpected"]}]:
            transport = httpx.MockTransport(
                lambda request, payload=response: httpx.Response(200, json=payload)
            )
            with pytest.raises(ReceiverError):
                OpenWebifClient(receiver, cfg, transport=transport).services()
