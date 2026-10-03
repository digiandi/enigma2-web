import re
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_foundation import csrf_value, login
from test_foundation import setup as setup

from e2web.db import AuditLog, User


def login_value(response, username):
    row = next(row for row in response.text.split("</tr>") if f"<small>{username}</small>" in row)
    return re.search(r'data-label="Letzte Anmeldung">([^<]*)', row)[1]


def test_last_login_uses_existing_successful_history_local_time_and_never_signed_in(setup):
    _, engine, app = setup
    with Session(engine) as db:
        db.add_all(
            [
                AuditLog(actor_id=2, action="login.succeeded", created_at=1704096000),
                AuditLog(actor_id=2, action="login.succeeded", created_at=1735808400),
                AuditLog(actor_id=2, action="login.failed", created_at=1735894800),
                AuditLog(actor_id=2, action="user.password_changed", created_at=1735981200),
                User(username="never", display_name="Neu", password_hash="unused"),
            ]
        )
        db.commit()
    with TestClient(app) as client:
        assert login(client).status_code == 303
        page = client.get("/admin/users")
        assert page.status_code == 200
        assert login_value(page, "user") == "02.01.2025 10:00"
        assert login_value(page, "never") == "Noch nie"
        assert login_value(page, "admin") != "Noch nie"


def test_only_successful_login_updates_display_and_users_cannot_read_admin_list(setup, monkeypatch):
    _, _, app = setup
    first = int(datetime(2026, 10, 3, 17, 23, tzinfo=UTC).timestamp())
    clock = [first]
    monkeypatch.setattr("e2web.security.now", lambda: clock[0])
    with TestClient(app) as user, TestClient(app) as admin:
        assert login(user, "user", "User-123").status_code == 303
        assert user.get("/admin/users").status_code == 403
        assert login(admin).status_code == 303
        assert login_value(admin.get("/admin/users"), "user") == "03.10.2026 19:23"
        clock[0] += 3600
        page = user.get("/login")
        assert user.post("/logout", data={"csrf_token": csrf_value(page)}).status_code == 200
        assert login(user, "user", "wrong-password").status_code == 400
        assert login_value(admin.get("/admin/users"), "user") == "03.10.2026 19:23"
        assert login(user, "user", "User-123").status_code == 303
        assert login_value(admin.get("/admin/users"), "user") == "03.10.2026 20:23"
