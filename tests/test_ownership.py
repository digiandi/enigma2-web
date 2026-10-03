import pytest
from fastapi.testclient import TestClient
from ownership_support import owned_rows
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from test_foundation import csrf_value, login
from test_foundation import setup as setup
from test_recordings import delete_form, install_movie_mock, movie_row
from test_timers import existing_url, form_values, input_value, new_url, timer_row

from e2web.db import Grant, Ownership, OwnerTag, Receiver, TimerAction, User
from e2web.security import now, token_hash


@pytest.mark.parametrize("xml", [False, True])
def test_created_timer_owner_survives_repeat_edit_and_recording_after_timer_removed(setup, xml):
    _, engine, app = setup
    box = install_movie_mock(app, xml=xml)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        form = form_values(client.get(new_url()), weekdays=["0", "1"])
        assert client.post("/timer/save", data=form, follow_redirects=False).status_code == 303
        row = box.timers[0]
        marker = row["tags"]
        assert marker == "e2web-owner-user"
        assert 'class="recording-owner">von Benutzer</small>' in client.get("/timer").text
        with Session(engine) as db:
            owner = db.get(OwnerTag, marker)
            assert owner.owner_id == 2
            assert not list(db.scalars(select(Ownership)))
        row["begin"] += 86400  # Enigma advances a repeating timer's schedule.
        row["end"] += 86400
        edit = client.get(existing_url("/timer/edit", row))
        assert edit.status_code == 200
        assert (
            client.post("/timer/save", data=form_values(edit), follow_redirects=False).status_code
            == 303
        )
        assert box.timers[0]["tags"] == marker
        box.movies[0]["tags"] = marker
        box.timers = []
        movie = client.get("/aufnahmen")
        assert 'class="recording-owner">von Benutzer</small>' in movie.text
        assert 'action="/aufnahmen/delete"' in movie.text
        assert (
            client.post(
                "/aufnahmen/delete", data=delete_form(movie), follow_redirects=False
            ).status_code
            == 303
        )


@pytest.mark.parametrize(
    "provenance", ["unknown", "foreign", "fake", "ambiguous", "receiver", "connection"]
)
def test_foreign_and_unverifiable_entries_visible_downloadable_but_not_mutable(setup, provenance):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row()]
    if provenance not in {"unknown", "fake"}:
        owned_rows(app, box.timers + box.movies, user_id=1 if provenance == "foreign" else 2)
    if provenance == "fake":
        for row in box.timers + box.movies:
            row["tags"] = "e2web-owner-forged"
    elif provenance == "ambiguous":
        for row in box.timers + box.movies:
            row["tags"] += " e2web-owner-other"
    elif provenance in {"receiver", "connection"}:
        with Session(engine) as db:
            for owner in db.scalars(select(Ownership)):
                if provenance == "receiver":
                    owner.receiver_id = 2
                else:
                    owner.connection = "changed"
            db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        timers, movies = client.get("/timer"), client.get("/aufnahmen")
        assert "Tagesschau" in timers.text and "Tagesschau" in movies.text
        creator = "Andreas" if provenance == "foreign" else "unbekannt"
        for page in (timers, movies):
            assert f'class="recording-owner">von {creator}</small>' in page.text
        assert "Bearbeiten</a>" not in timers.text
        assert 'action="/timer/delete"' not in timers.text
        assert 'action="/aufnahmen/delete"' not in movies.text
        assert "Herunterladen" in movies.text
        assert client.get(existing_url("/timer/edit", box.timers[0])).status_code == 403
        assert not box.writes


@pytest.mark.parametrize("operation", ["timer_edit", "timer_delete", "movie_delete"])
def test_stale_ticket_rechecks_owner_before_receiver_write(setup, operation):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row()]
    owned_rows(app, box.timers + box.movies)
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
            for owner in db.scalars(select(Ownership)):
                owner.owner_id = 1
            db.commit()
        assert client.post(path, data=form, follow_redirects=False).status_code == 403
        assert not box.writes


def test_deleted_user_id_reuse_does_not_inherit_ownership(setup):
    _, engine, app = setup
    box = install_movie_mock(app)
    owned_rows(app, box.movies)
    with Session(engine) as db:
        db.execute(delete(User).where(User.id == 2))
        db.flush()
        assert db.scalar(select(Ownership.owner_id)) is None
        admin = db.get(User, 1)
        db.add(
            User(
                id=2,
                username="replacement",
                display_name="Neu",
                password_hash=admin.password_hash,
                active=True,
                must_change_password=False,
                all_receivers=True,
            )
        )
        db.commit()
    with TestClient(app) as client:
        login(client, "replacement", "Admin-123")
        page = client.get("/aufnahmen")
        assert 'action="/aufnahmen/delete"' not in page.text
        assert 'class="recording-owner">von unbekannt</small>' in page.text
        assert 'class="recording-owner">von Neu</small>' not in page.text


@pytest.mark.parametrize("xml", [False, True])
def test_admin_unknown_entries_and_running_recording_block(setup, xml):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    box.timers = [timer_row(state=0)]
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        assert "Bearbeiten</a>" in page.text
        assert (
            client.get(existing_url("/timer/edit", box.timers[0], receiver_id=2)).status_code == 200
        )
        stale = delete_form(client.get("/aufnahmen"))
        box.timers[0].update(state=2, filename=box.movies[0]["filename"].removesuffix(".ts"))
        page = client.get("/aufnahmen")
        assert 'action="/aufnahmen/delete"' not in page.text
        assert "Zum Beenden den laufenden Timer öffnen." not in page.text
        assert "Löschen derzeit nicht verfügbar" not in page.text
        assert client.post("/aufnahmen/delete", data=stale).status_code == 409
        assert not box.writes
        assert (
            client.post(
                "/timer/delete", data=delete_form(client.get("/timer")), follow_redirects=False
            ).status_code
            == 303
        )
        assert box.movies  # Stopping the timer retains its file.
        assert (
            client.post(
                "/aufnahmen/delete",
                data=delete_form(client.get("/aufnahmen")),
                follow_redirects=False,
            ).status_code
            == 303
        )


def test_refresh_reuses_tickets_and_returns_changed_fields_bound_to_receiver(setup):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row(state=2, begin=now() - 100, end=now() + 100)]
    owned_rows(app, box.timers + box.movies)
    with TestClient(app) as client:
        login(client, "user", "User-123")
        first = client.get("/timer")
        ticket = input_value(first, "action_token")
        for _ in range(8):
            page = client.get("/timer?live_receiver=1")
            assert input_value(page, "action_token") == ticket
        with Session(engine) as db:
            assert len(list(db.scalars(select(TimerAction)))) == 1
            assert db.get(TimerAction, token_hash(ticket)).encrypted_token != ticket
        box.timers[0]["state"] = 3
        page = client.get("/timer?live_receiver=1")
        assert "Erledigte Timer" in page.text and input_value(page, "action_token") != ticket
        box.movies[0]["filesize"] *= 2
        box.movies[0]["length"] = "30:00"
        movies = client.get("/aufnahmen?live_receiver=1")
        assert "2.0 GiB" in movies.text and "00:30:00" in movies.text
        assert client.get("/timer?live_receiver=2").status_code == 409
        assert not box.writes


def test_admin_form_hides_permissions_and_server_ignores_irrelevant_inputs(setup):
    _, engine, app = setup
    install_movie_mock(app)
    with TestClient(app) as client:
        login(client)
        page = client.get("/admin/users/1/edit")
        assert "data-receiver-permissions hidden disabled" in page.text
        form = {
            "csrf_token": csrf_value(page),
            "id": "1",
            "display_name": "Andreas",
            "role": "admin",
            "active": "on",
            "default_receiver_id": "1",
            "access_mode": "invalid",
            "receiver_access_9999": "invalid",
        }
        assert (
            client.post("/admin/users/save", data=form, follow_redirects=False).status_code == 303
        )
    with Session(engine) as db:
        admin = db.get(User, 1)
        assert admin.all_receivers and admin.all_receivers_write and admin.default_receiver_id == 1


def test_credential_rotation_preserves_creator_but_device_change_does_not(setup):
    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row()]
    owned_rows(app, box.timers + box.movies)
    with Session(engine) as db:
        db.get(Receiver, 1).username = "new-login"
        db.get(Receiver, 1).verify_tls = False
        db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        assert "Bearbeiten</a>" in client.get("/timer").text
        page = client.get("/aufnahmen")
        assert 'action="/aufnahmen/delete"' in page.text
        assert 'class="recording-owner">von Benutzer</small>' in page.text
        with Session(engine) as db:
            db.get(Receiver, 1).hostname = "192.0.2.99"
            db.commit()
        assert "Bearbeiten</a>" not in client.get("/timer").text
        page = client.get("/aufnahmen")
        assert 'action="/aufnahmen/delete"' not in page.text
        assert 'class="recording-owner">von unbekannt</small>' in page.text


@pytest.mark.parametrize("xml", [False, True])
def test_creator_names_visible_with_read_only_access_and_refresh_escaped_display_name(setup, xml):
    _, engine, app = setup
    box = install_movie_mock(app, xml=xml)
    box.timers = [
        timer_row(),
        timer_row(name="Fremder Timer", begin=now() + 10000, end=now() + 11000),
    ]
    box.movies.append(
        movie_row(
            filename="/media/hdd/movie/foreign.ts",
            serviceref="1:0:0:0:0:0:0:0:0:0:/media/hdd/movie/foreign.ts",
            eventname="Fremde Aufnahme",
        )
    )
    owned_rows(app, [box.timers[0], box.movies[0]])
    owned_rows(app, [box.timers[1], box.movies[1]], user_id=1)
    with Session(engine) as db:
        db.get(Grant, (2, 1)).can_write = False
        db.commit()
    with TestClient(app) as client:
        login(client, "user", "User-123")
        for path in ("/timer", "/aufnahmen"):
            page = client.get(path)
            assert page.status_code == 200
            assert 'class="recording-owner">von Benutzer</small>' in page.text
            assert 'class="recording-owner">von Andreas</small>' in page.text
            assert 'action="/timer/delete"' not in page.text
            assert 'action="/aufnahmen/delete"' not in page.text
        with Session(engine) as db:
            db.get(User, 1).display_name = 'Andreas <script> & "Name"'
            db.commit()
        for path in ("/timer?live_receiver=1", "/aufnahmen?live_receiver=1"):
            page = client.get(path, headers={"X-Live-Refresh": "1"})
            assert "von Andreas &lt;script&gt; &amp; &#34;Name&#34;" in page.text
            assert "von Andreas <script>" not in page.text
        assert not box.writes


@pytest.mark.parametrize("operation", ["timer_edit", "timer_delete", "movie_delete"])
def test_owner_rechecked_after_slow_receiver_preflight(setup, operation):
    from functools import partial

    import httpx

    from e2web.openwebif import OpenWebifClient

    _, engine, app = setup
    box = install_movie_mock(app)
    box.timers = [timer_row()]
    owned_rows(app, box.timers + box.movies)
    armed = False

    def transport(request):
        nonlocal armed
        response = box(request)
        if armed and request.url.path.endswith("timerlist"):
            armed = False
            with Session(engine) as db:
                for owner in db.scalars(select(Ownership)):
                    owner.owner_id = 1
                db.commit()
        return response

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(transport))
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
        armed = True
        assert client.post(path, data=form, follow_redirects=False).status_code == 403
        assert not box.writes
