import html
import re
from pathlib import Path
from urllib.parse import urlencode

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from ownership_support import owned_rows
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_foundation import csrf_value, login
from test_foundation import setup as setup
from test_recordings import delete_form, install_movie_mock
from test_timers import REFERENCE, existing_url, form_values, new_url, timer_row

from e2web.db import AuditLog, Grant, Receiver, User, WebSession, migrate
from e2web.security import now, token_hash


def user_form(page, **changes):
    return {
        "id": "2",
        "csrf_token": csrf_value(page),
        "display_name": "Benutzer",
        "role": "user",
        "active": "on",
        "access_mode": "assigned",
        "receiver_access_1": "read",
        "receiver_access_2": "none",
        "default_receiver_id": "1",
        **changes,
    }


def test_assign_permissions_default_and_revoke_old_sessions(setup):
    _, engine, app = setup
    install_movie_mock(app)
    with TestClient(app) as admin, TestClient(app) as user:
        login(admin)
        login(user, "user", "User-123")
        page = admin.get("/admin/users/2/edit")
        response = admin.post(
            "/admin/users/save",
            data=user_form(page, receiver_access_2="write", default_receiver_id="2"),
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert user.get("/timer", follow_redirects=False).headers["location"] == "/login"
        with Session(engine) as db:
            target = db.get(User, 2)
            assert target.default_receiver_id == 2 and not target.all_receivers
            assert not db.get(Grant, (2, 1)).can_write and db.get(Grant, (2, 2)).can_write
        login(user, "user", "User-123")
        page = user.get("/timer")
        assert "<h1>Timer: DM920</h1>" in page.text
        assert (
            user.post(
                "/receiver/select",
                data={"receiver_id": "1", "csrf_token": csrf_value(page)},
                follow_redirects=False,
            ).status_code
            == 303
        )
        page = user.get("/timer")
        assert "<h1>Timer: VU+ Duo 4K</h1>" in page.text and "Timer anlegen" not in page.text
        user.post("/logout", data={"csrf_token": csrf_value(page)})
        login(user, "user", "User-123")
        assert "<h1>Timer: DM920</h1>" in user.get("/timer").text


@pytest.mark.parametrize(
    "changes",
    [
        {"default_receiver_id": "2"},
        {"receiver_access_1": "invalid"},
        {"receiver_access_999": "read"},
        {"default_receiver_id": "999"},
        {"access_mode": "invalid"},
        {"receiver_access_nope": "read"},
    ],
)
def test_invalid_assignment_is_rejected_atomically(setup, changes):
    _, engine, app = setup
    with TestClient(app) as admin:
        login(admin)
        page = admin.get("/admin/users/2/edit")
        result = admin.post("/admin/users/save", data=user_form(page, **changes))
        assert result.status_code == 400 and "Receiver-Zugriff" in result.text
    with Session(engine) as db:
        assert db.get(User, 2).default_receiver_id is None
        assert db.get(Grant, (2, 1)).can_write and not db.get(Grant, (2, 2))


@pytest.mark.parametrize("mode", ["assigned", "all_read"])
def test_read_only_views_download_and_forged_writes(setup, mode):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row()]
    owned_rows(app, box.timers + box.movies)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        timer_page = client.get("/timer")
        movie_page = client.get("/aufnahmen")
        edit = client.get(existing_url("/timer/edit", box.timers[0]))
        with Session(engine) as db:
            user = db.get(User, 2)
            user.all_receivers = mode == "all_read"
            user.all_receivers_write = False
            db.get(Grant, (2, 1)).can_write = False
            db.commit()
        for path in [
            "/timer",
            "/sender",
            "/aufnahmen",
            "/epg?" + urlencode({"reference": REFERENCE}),
        ]:
            page = client.get(path)
            assert page.status_code == 200
            assert "Timer anlegen" not in page.text and "Bearbeiten</a>" not in page.text
            assert "data-action-confirm" not in page.text
        assert "DM920" in page.text if mode == "all_read" else "DM920" not in page.text
        assert client.get(new_url()).status_code == 403
        assert client.get(existing_url("/timer/edit", box.timers[0])).status_code == 403
        assert client.get("/sender?for_timer=1").status_code == 403
        assert client.post("/timer/save", data=form_values(edit)).status_code == 403
        assert client.post("/timer/delete", data=delete_form(timer_page)).status_code == 403
        assert client.post("/aufnahmen/delete", data=delete_form(movie_page)).status_code == 403
        assert not box.writes
        page = client.get("/aufnahmen")
        url = html.unescape(re.search(r'href="([^"]*/aufnahmen/download\?[^"]+)"', page.text)[1])
        download = client.get(url)
        assert download.status_code == 200 and download.content == box.file_content


def test_admin_has_write_rights_and_no_assignment_hides_all_receivers(setup):
    _, engine, app = setup
    box = install_movie_mock(app)
    with Session(engine) as db:
        db.get(User, 1).all_receivers_write = False
        db.delete(db.get(Grant, (2, 1)))
        db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer")
        assert "VU+ Duo 4K" not in page.text and "DM920" not in page.text
        assert "Kein Receiver" in page.text and "data-receiver-select" not in page.text
        assert not box.requests
        assert client.get(new_url()).status_code == 403
    with TestClient(app) as client:
        login(client)
        assert client.get(new_url(receiver_id=2)).status_code == 200


@pytest.mark.parametrize("change", ["disabled", "deleted", "grant"])
def test_unavailable_default_falls_back_to_alphabetical_allowed_receiver(setup, change):
    _, engine, app = setup
    install_movie_mock(app)
    with Session(engine) as db:
        target = db.get(User, 2)
        target.default_receiver_id = 1
        db.add(Grant(user_id=2, receiver_id=2))
        db.flush()
        if change == "disabled":
            db.get(Receiver, 1).enabled = False
        elif change == "deleted":
            db.delete(db.get(Receiver, 1))
        else:
            db.delete(db.get(Grant, (2, 1)))
        db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert "<h1>Timer: DM920</h1>" in client.get("/timer").text


def test_upgrade_preserves_users_permissions_credentials_sessions_and_audit(setup):
    cfg, engine, _ = setup
    with Session(engine) as db:
        db.add(
            WebSession(
                token_hash=token_hash("migration-session"),
                user_id=2,
                receiver_id=1,
                expires_at=now() + 3600,
            )
        )
        db.add(AuditLog(actor_id=1, action="migration.check", target_id=2, created_at=now()))
        db.get(Receiver, 1).encrypted_password = "keep-original-ciphertext"
        db.commit()
    alembic = AlembicConfig()
    alembic.set_main_option(
        "script_location", str(Path(__file__).parents[1] / "src/e2web/migrations")
    )
    with engine.begin() as connection:
        alembic.attributes["connection"] = connection
        command.downgrade(alembic, "0002")
    with engine.connect() as connection:
        snapshots = {
            table: list(connection.execute(text(f"SELECT * FROM {table}")))
            for table in [
                "users",
                "receivers",
                "sessions",
                "user_receiver_permissions",
                "audit_log",
            ]
        }
    migrate(cfg)
    with engine.connect() as connection:
        for table, rows in snapshots.items():
            columns = ", ".join(rows[0]._mapping.keys())
            assert list(connection.execute(text(f"SELECT {columns} FROM {table}"))) == rows
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0005"
        assert not list(connection.execute(text("PRAGMA foreign_key_check")))
    with Session(engine) as db:
        assert db.get(User, 2).all_receivers_write and db.get(Grant, (2, 1)).can_write
        assert db.get(User, 2).default_receiver_id is None
