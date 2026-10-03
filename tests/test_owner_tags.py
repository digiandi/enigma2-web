from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from fastapi.testclient import TestClient
from ownership_support import owned_rows
from sqlalchemy import delete, inspect, select, text
from sqlalchemy.orm import Session
from test_foundation import csrf_value, login
from test_foundation import setup as setup
from test_recordings import delete_form, install_movie_mock
from test_timers import existing_url, form_values, new_url, timer_row

from e2web.db import Grant, Ownership, OwnerTag, User, WebSession, migrate
from e2web.ownership import ensure_owner_tag
from e2web.security import passwords


@pytest.mark.parametrize("xml", [False, True])
def test_manual_named_tag_recognized_for_any_sender_and_recording(setup, xml):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    box.timers = [
        timer_row(tags="Sport e2web-owner-user"),
        timer_row(
            serviceref="1:0:2:1111:222:3:C00000:0:0:0:",
            servicename="Radiosender",
            tags="e2web-owner-user",
            begin=1800000000,
            end=1800000600,
        ),
    ]
    box.movies[0]["tags"] = "Nachrichten e2web-owner-user"
    with TestClient(app) as client:
        assert login(client, "user", "User-123").status_code == 303
        page = client.get("/timer")
        assert page.text.count('class="recording-owner">von Benutzer</small>') == 2
        for row in box.timers:
            assert client.get(existing_url("/timer/edit", row)).status_code == 200
        page = client.get("/aufnahmen")
        assert 'class="recording-owner">von Benutzer</small>' in page.text
        assert (
            client.post(
                "/aufnahmen/delete", data=delete_form(page), follow_redirects=False
            ).status_code
            == 303
        )
    assert [method for method, _, _ in box.writes] == ["moviedelete"]


@pytest.mark.parametrize("xml", [False, True])
def test_legacy_timer_edit_converts_tag_without_reassigning_old_files(setup, xml):
    _, engine, app = setup
    box = install_movie_mock(app, xml=xml)
    box.timers = [timer_row(tags="Nachrichten HD")]
    owned_rows(app, box.timers)
    old_tag = box.timers[0]["tags"].split()[-1]
    box.movies[0]["tags"] = old_tag
    with TestClient(app) as client:
        login(client, "user", "User-123")
        form = client.get(existing_url("/timer/edit", box.timers[0]))
        assert (
            client.post("/timer/save", data=form_values(form), follow_redirects=False).status_code
            == 303
        )
        assert box.timers[0]["tags"] == "Nachrichten HD e2web-owner-user"
        assert box.movies[0]["tags"] == old_tag
        assert 'class="recording-owner">von Benutzer</small>' in client.get("/aufnahmen").text
    with Session(engine) as db:
        assert db.get(Ownership, old_tag).owner_id == 2


def test_admin_edit_preserves_legacy_creator_and_unknown_timer_stays_unknown(setup):
    _, _, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row()]
    owned_rows(app, box.timers)
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        client.post("/receiver/select", data={"csrf_token": csrf_value(page), "receiver_id": "1"})
        edit = client.get(existing_url("/timer/edit", box.timers[0]))
        assert (
            client.post("/timer/save", data=form_values(edit), follow_redirects=False).status_code
            == 303
        )
        assert box.timers[0]["tags"] == "Nachrichten HD e2web-owner-user"
        box.timers[0]["tags"] = "Sport Kultur"
        edit = client.get(existing_url("/timer/edit", box.timers[0]))
        assert (
            client.post("/timer/save", data=form_values(edit), follow_redirects=False).status_code
            == 303
        )
        assert box.timers[0]["tags"] == "Sport Kultur"
        assert 'class="recording-owner">von unbekannt</small>' in client.get("/timer").text


@pytest.mark.parametrize(
    "tags",
    [
        "e2web-owner-admin",
        "e2web-owner-missing",
        "e2web-owner-user e2web-owner-admin",
        "e2web-owner-user e2web-owner-user",
        "e2web-owner-USER",
    ],
)
def test_foreign_unknown_and_ambiguous_named_tags_do_not_grant_write_access(setup, tags):
    _, _, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row(tags=tags)]
    box.movies[0]["tags"] = tags
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert client.get(existing_url("/timer/edit", box.timers[0])).status_code == 403
        page = client.get("/aufnahmen")
        assert 'action="/aufnahmen/delete"' not in page.text
        assert "Herunterladen" in page.text
    assert not box.writes


def test_named_owner_still_needs_receiver_write_permission(setup):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row(tags="e2web-owner-user")]
    box.movies[0]["tags"] = "e2web-owner-user"
    with Session(engine) as db:
        db.get(Grant, (2, 1)).can_write = False
        db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert client.get(existing_url("/timer/edit", box.timers[0])).status_code == 403
        assert 'class="recording-owner">von Benutzer</small>' in client.get("/timer").text
        assert 'action="/aufnahmen/delete"' not in client.get("/aufnahmen").text
        assert (
            client.post(
                "/receiver/select",
                data={"csrf_token": csrf_value(client.get("/timer")), "receiver_id": "2"},
                follow_redirects=False,
            ).status_code
            == 403
        )
    assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
def test_form_cannot_choose_another_creator(setup, xml):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        form = form_values(client.get(new_url()), tags="e2web-owner-admin", owner_id="1")
        assert client.post("/timer/save", data=form, follow_redirects=False).status_code == 303
        assert box.timers[0]["tags"] == "e2web-owner-user"
        edit = client.get(existing_url("/timer/edit", box.timers[0]))
        form = form_values(edit, tags="e2web-owner-admin")
        assert client.post("/timer/save", data=form, follow_redirects=False).status_code == 303
        assert box.timers[0]["tags"] == "e2web-owner-user"


@pytest.mark.parametrize("username", ["digiandi", "thomas.meyer", "test_name", "test-name"])
def test_account_registration_uses_exact_username_and_edit_form_displays_tag(setup, username):
    _, engine, app = setup
    with TestClient(app) as client:
        login(client)
        page = client.get("/admin/users/new")
        form = {
            "csrf_token": csrf_value(page),
            "username": username,
            "display_name": "Anzeigename",
            "role": "user",
            "active": "on",
            "password": "Passwort",
            "password_confirmation": "Passwort",
            "access_mode": "assigned",
            "receiver_access_1": "write",
        }
        assert (
            client.post("/admin/users/save", data=form, follow_redirects=False).status_code == 303
        )
        with Session(engine) as db:
            user = db.scalar(select(User).where(User.username == username))
            assert db.get(OwnerTag, "e2web-owner-" + username).owner_id == user.id
            user_id = user.id
        page = client.get(f"/admin/users/{user_id}/edit")
        assert f'value="e2web-owner-{username}" readonly' in page.text


def test_deleted_account_name_and_id_reuse_keep_old_tags_unowned(setup):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row(tags="e2web-owner-user")]
    box.movies[0]["tags"] = "e2web-owner-user"
    with Session(engine) as db:
        db.execute(delete(User).where(User.id == 2))
        db.commit()
        assert db.get(OwnerTag, "e2web-owner-user").owner_id is None
        replacement = User(
            id=2,
            username="user",
            display_name="Neues Konto",
            password_hash=passwords.hash("User-123"),
            must_change_password=False,
            all_receivers=True,
            default_receiver_id=1,
        )
        db.add(replacement)
        db.flush()
        assert ensure_owner_tag(db, replacement) == "e2web-owner-user-konto-2"
        db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert client.get(existing_url("/timer/edit", box.timers[0])).status_code == 403
        assert 'class="recording-owner">von unbekannt</small>' in client.get("/timer").text
        assert 'action="/aufnahmen/delete"' not in client.get("/aufnahmen").text
        box.timers[0]["tags"] = "e2web-owner-user-konto-2"
        assert client.get(existing_url("/timer/edit", box.timers[0])).status_code == 200


@pytest.mark.parametrize("operation", ["timer_edit", "timer_delete", "movie_delete"])
def test_named_owner_rechecked_on_stale_form(setup, operation):
    _, _, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row(tags="e2web-owner-user")]
    box.movies[0]["tags"] = "e2web-owner-user"
    with TestClient(app) as client:
        login(client, "user", "User-123")
        if operation == "timer_edit":
            form = form_values(client.get(existing_url("/timer/edit", box.timers[0])))
            path = "/timer/save"
        else:
            form = delete_form(
                client.get("/timer" if operation == "timer_delete" else "/aufnahmen")
            )
            path = "/timer/delete" if operation == "timer_delete" else "/aufnahmen/delete"
        box.timers[0]["tags"] = box.movies[0]["tags"] = "e2web-owner-admin"
        assert client.post(path, data=form, follow_redirects=False).status_code in {403, 409}
    assert not box.writes


def test_named_tag_reusable_on_another_explicitly_granted_receiver(setup):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row(tags="e2web-owner-user")]
    with Session(engine) as db:
        db.add(Grant(user_id=2, receiver_id=2, can_write=True))
        db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/timer")
        assert (
            client.post(
                "/receiver/select",
                data={"csrf_token": csrf_value(page), "receiver_id": "2"},
                follow_redirects=False,
            ).status_code
            == 303
        )
        assert (
            client.get(existing_url("/timer/edit", box.timers[0], receiver_id=2)).status_code == 200
        )
        assert 'class="recording-owner">von Benutzer</small>' in client.get("/timer").text
    assert not box.writes


@pytest.mark.parametrize("operation", ["timer_edit", "timer_delete", "movie_delete"])
def test_named_registration_rechecked_before_write(setup, operation):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row(tags="e2web-owner-user")]
    box.movies[0]["tags"] = "e2web-owner-user"
    with TestClient(app) as client:
        login(client, "user", "User-123")
        if operation == "timer_edit":
            form = form_values(client.get(existing_url("/timer/edit", box.timers[0])))
            path = "/timer/save"
        else:
            form = delete_form(
                client.get("/timer" if operation == "timer_delete" else "/aufnahmen")
            )
            path = "/timer/delete" if operation == "timer_delete" else "/aufnahmen/delete"
        with Session(engine) as db:
            db.get(OwnerTag, "e2web-owner-user").owner_id = None
            db.commit()
        assert client.post(path, data=form, follow_redirects=False).status_code == 403
    assert not box.writes


def test_cli_created_admin_has_registered_named_tag(tmp_path, monkeypatch):
    from e2web.cli import initialize, main
    from e2web.config import load_config
    from e2web.db import make_engine

    path = tmp_path / "e2web.toml"
    initialize(path)
    inputs = iter(["digiandi", "Andreas Knedlik"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(inputs))
    monkeypatch.setattr("e2web.cli.getpass.getpass", lambda prompt: "Testpasswort")
    monkeypatch.setattr("sys.argv", ["e2web", "--config", str(path), "create-admin"])
    main()
    engine = make_engine(load_config(path))
    with Session(engine) as db:
        user = db.scalar(select(User).where(User.username == "digiandi"))
        assert user.is_admin
        assert db.get(OwnerTag, "e2web-owner-digiandi").owner_id == user.id
    engine.dispose()


def test_upgrade_from_0004_preserves_data_and_registers_all_account_labels(setup):
    config, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row()]
    owned_rows(app, box.timers)
    key = config.key_path.read_bytes()
    with Session(engine) as db:
        db.add(WebSession(token_hash="a" * 64, user_id=2, expires_at=1800000000, receiver_id=1))
        db.commit()
    alembic = AlembicConfig()
    alembic.set_main_option(
        "script_location", str(Path(__file__).parents[1] / "src/e2web/migrations")
    )
    with engine.begin() as connection:
        alembic.attributes["connection"] = connection
        command.downgrade(alembic, "0004")
    with engine.connect() as connection:
        assert "owner_tags" not in inspect(connection).get_table_names()
        snapshots = {
            table: list(connection.execute(text(f"SELECT * FROM {table}")))
            for table in [
                "users",
                "receivers",
                "ownership",
                "user_receiver_permissions",
                "sessions",
            ]
        }
    migrate(config)
    migrate(config)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0005"
        for table, rows in snapshots.items():
            assert list(connection.execute(text(f"SELECT * FROM {table}"))) == rows
        assert not list(connection.execute(text("PRAGMA foreign_key_check")))
    with Session(engine) as db:
        assert db.get(OwnerTag, "e2web-owner-admin").owner_id == 1
        assert db.get(OwnerTag, "e2web-owner-user").owner_id == 2
        assert len(list(db.scalars(select(OwnerTag)))) == 2
    assert config.key_path.read_bytes() == key
