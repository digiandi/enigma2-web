from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from e2web import __release_date__, __version__
from e2web.channel_details import ChannelCatalog
from e2web.config import Config, load_config
from e2web.db import (
    AuditLog,
    Grant,
    LoginAttempt,
    OwnerTag,
    Receiver,
    TimerAction,
    User,
    WebSession,
    make_engine,
)
from e2web.openwebif import OpenWebifClient, ReceiverError
from e2web.ownership import ensure_owner_tag
from e2web.recording_pages import register_recording_pages
from e2web.security import (
    active_admins,
    audit,
    cipher,
    clear_failures,
    csrf,
    hostname,
    login_limited,
    matches,
    now,
    passwords,
    revoke,
    text_field,
    token_hash,
    username,
    validate_password,
    verify_password,
)
from e2web.timer_pages import register_timer_pages


def create_app(config: Config | None = None) -> FastAPI:
    config = config or load_config()
    engine = make_engine(config)
    timezone = ZoneInfo(config.timezone)
    templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

    @asynccontextmanager
    async def lifespan(app):
        cipher(config)  # A missing key must fail startup rather than destroy stored credentials.
        with engine.connect() as connection:
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0005":
                raise RuntimeError("Bitte zuerst e2web migrate ausführen.")
        try:
            yield
        finally:
            app.state.channel_catalog.close()
            engine.dispose()

    app = FastAPI(
        title="Enigma2 Timer",
        version=__version__,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.config = config
    app.state.engine = engine
    app.state.client_factory = OpenWebifClient
    app.state.channel_catalog = ChannelCatalog()
    app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

    def cookies(request):
        secure = request.url.scheme == "https" or config.cookie_secure
        prefix = "__Host-" if secure else ""
        return prefix + "e2web_session", prefix + "e2web_login_csrf", secure

    def render(request, template, *, status=200, **context):
        user = request.state.user
        receivers = allowed_receivers(request) if user else []
        selected = selected_receiver(request) if user else None
        if template == "users.html":
            context["default_receiver_names"] = {
                r.id: r.name for r in receiver_rows(request.state.db)
            }
        return templates.TemplateResponse(
            request=request,
            name=template,
            context={
                "current_user": user,
                "csrf_token": csrf(request.state.raw_token),
                "receivers": receivers,
                "selected_receiver": selected,
                "can_write_receiver": bool(selected and can_write_receiver(request, selected)),
                "version": __version__,
                "release_date": date.fromisoformat(__release_date__).strftime("%d.%m.%Y"),
                "timezone": config.timezone,
                "error": None,
                "notice": None,
                **context,
            },
            status_code=status,
        )

    def allowed_receivers(request):
        db, user = request.state.db, request.state.user
        return receivers_for_user(db, user)

    def receivers_for_user(db, user):
        statement = select(Receiver).where(Receiver.enabled.is_(True))
        if not user.is_admin and not user.all_receivers:
            statement = statement.where(
                Receiver.id.in_(select(Grant.receiver_id).where(Grant.user_id == user.id))
            )
        return receiver_rows(db, statement)

    def preferred_receiver(user, receivers):
        return next((r for r in receivers if r.id == user.default_receiver_id), receivers[0])

    def can_write_receiver(request, receiver):
        user = request.state.user
        if user.is_admin:
            return True
        if user.all_receivers:
            return user.all_receivers_write
        grant = request.state.db.get(Grant, (user.id, receiver.id))
        return bool(grant and grant.can_write)

    app.state.can_write_receiver = can_write_receiver

    def receiver_rows(db, statement=None):
        rows = db.scalars(statement if statement is not None else select(Receiver))
        return sorted(rows, key=lambda receiver: (receiver.name.casefold(), receiver.id))

    def require_admin(request):
        if not request.state.user or not request.state.user.is_admin:
            raise HTTPException(403, "Dieser Bereich ist Administratoren vorbehalten.")

    def lock_admin(request):
        require_admin(request)
        db = request.state.db
        db.commit()
        db.execute(text("BEGIN IMMEDIATE"))
        db.expire_all()
        if not request.state.user.active or not request.state.user.is_admin:
            raise HTTPException(403, "Administratorzugriff nicht mehr verfügbar.")

    def check_csrf(request, form):
        if not matches(csrf(request.state.raw_token), str(form.get("csrf_token", ""))):
            raise HTTPException(403, "Sicherheitsprüfung fehlgeschlagen. Seite neu laden.")

    def redirect(path):
        return RedirectResponse(path, status_code=303)

    def selected_receiver(request):
        receivers = allowed_receivers(request)
        if not receivers:
            return None
        return next(
            (r for r in receivers if r.id == request.state.web_session.receiver_id),
            preferred_receiver(request.state.user, receivers),
        )

    @app.middleware("http")
    async def session_and_headers(request: Request, call_next):
        with Session(engine, expire_on_commit=False) as db:
            request.state.db = db
            request.state.user = None
            request.state.web_session = None
            request.state.raw_token = ""
            cookie, _, _ = cookies(request)
            raw = request.cookies.get(cookie, "")
            if raw and len(raw) <= 128:
                session = db.get(WebSession, token_hash(raw))
                if session:
                    user = db.get(User, session.user_id)
                    if session.expires_at > now() and user and user.active:
                        request.state.user = user
                        request.state.web_session = session
                        request.state.raw_token = raw
                    else:
                        db.delete(session)
                        db.commit()
            path = request.url.path
            if path not in {"/login", "/health"} and not path.startswith("/static/"):
                if not request.state.user:
                    response = redirect("/login")
                elif request.state.user.must_change_password and path not in {
                    "/account/password",
                    "/logout",
                }:
                    response = redirect("/account/password")
                else:
                    response = await call_next(request)
            else:
                response = await call_next(request)
            response.headers["Cache-Control"] = "no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "same-origin"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; "
                "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
            )
            return response

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        if request.url.path.endswith("/delete") and request.state.user:
            from starlette.concurrency import run_in_threadpool

            # Delete failures stay in the same list; no confirmation or notice pages.
            request.state.db.rollback()
            session = request.state.db.get(WebSession, token_hash(request.state.raw_token))
            user = request.state.db.get(User, session.user_id) if session else None
            if not session or session.expires_at <= now() or not user or not user.active:
                request.state.user = None
                return redirect("/login")
            request.state.user, request.state.web_session = user, session
            if request.url.path == "/timer/delete":
                return await run_in_threadpool(
                    app.state.timer_page,
                    request,
                    action_error=str(exc.detail),
                    status=exc.status_code,
                )
            if request.url.path == "/aufnahmen/delete":
                return await run_in_threadpool(
                    app.state.recording_page,
                    request,
                    action_error=str(exc.detail),
                    status=exc.status_code,
                )
            if request.state.user.is_admin and request.url.path.startswith("/admin/receivers/"):
                return render(
                    request,
                    "receivers.html",
                    rows=receiver_rows(request.state.db),
                    status=exc.status_code,
                    error=str(exc.detail),
                )
            if request.state.user.is_admin and request.url.path.startswith("/admin/users/"):
                return render(
                    request,
                    "users.html",
                    rows=list(request.state.db.scalars(select(User).order_by(User.username))),
                    status=exc.status_code,
                    error=str(exc.detail),
                )
        return render(
            request,
            "error.html",
            status=exc.status_code,
            error=str(exc.detail),
            code=exc.status_code,
        )

    @app.get("/health")
    def health():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "version": __version__}

    @app.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        if request.state.user:
            return redirect("/")
        token = secrets.token_urlsafe(32)
        response = render(
            request,
            "login.html",
            login_csrf=token,
            changed=request.query_params.get("changed") == "1",
        )
        _, cookie, secure = cookies(request)
        response.set_cookie(
            cookie, token, max_age=1800, httponly=True, secure=secure, samesite="strict", path="/"
        )
        return response

    @app.post("/login")
    async def login(request: Request):
        form = await request.form()
        cookie, csrf_cookie, secure = cookies(request)
        csrf_value = request.cookies.get(csrf_cookie)
        if not matches(csrf_value, str(form.get("csrf_token", ""))):
            raise HTTPException(403, "Anmeldung bitte erneut öffnen.")
        name = str(form.get("username", "")).strip().lower()[:32]
        password = str(form.get("password", ""))
        ip = request.client.host if request.client else "unknown"
        db = request.state.db
        # Serialize throttling so parallel login requests cannot bypass the attempt limit.
        db.commit()
        db.execute(text("BEGIN IMMEDIATE"))
        if login_limited(db, name, ip):
            db.commit()
            return render(
                request,
                "login.html",
                status=429,
                login_csrf=csrf_value,
                error="Zu viele Anmeldeversuche. Bitte in 15 Minuten erneut versuchen.",
            )
        user = db.scalar(select(User).where(User.username == name))
        valid = verify_password(
            password if len(password) <= 128 else "", user.password_hash if user else None
        )
        if not user or not user.active or not valid:
            db.add(LoginAttempt(username=name, ip_address=ip, attempted_at=now()))
            audit(db, None, "login.failed")
            db.commit()
            return render(
                request,
                "login.html",
                status=400,
                login_csrf=csrf_value,
                error="Benutzername oder Passwort ist falsch.",
            )
        clear_failures(db, name, ip)
        db.execute(delete(WebSession).where(WebSession.expires_at <= now()))
        raw = secrets.token_urlsafe(32)
        receivers = receivers_for_user(db, user)
        db.add(
            WebSession(
                token_hash=token_hash(raw),
                user_id=user.id,
                expires_at=now() + config.session_hours * 3600,
                receiver_id=preferred_receiver(user, receivers).id if receivers else None,
            )
        )
        audit(db, user, "login.succeeded")
        db.commit()
        response = redirect("/account/password" if user.must_change_password else "/")
        response.set_cookie(
            cookie,
            raw,
            max_age=config.session_hours * 3600,
            httponly=True,
            secure=secure,
            samesite="lax",
            path="/",
        )
        response.delete_cookie(csrf_cookie, secure=secure, httponly=True, samesite="strict")
        return response

    @app.post("/logout")
    async def logout(request: Request):
        check_csrf(request, await request.form())
        db = request.state.db
        db.delete(request.state.web_session)
        db.commit()
        response = redirect("/login")
        cookie, _, secure = cookies(request)
        response.delete_cookie(cookie, secure=secure, httponly=True, samesite="lax")
        return response

    @app.get("/account/password")
    def password_page(request: Request):
        return render(request, "password.html")

    @app.post("/account/password")
    async def change_password(request: Request):
        form = await request.form()
        check_csrf(request, form)
        db, user = request.state.db, request.state.user
        try:
            if not verify_password(str(form.get("current_password", "")), user.password_hash):
                raise ValueError("Das aktuelle Passwort ist falsch.")
            new = str(form.get("password", ""))
            validate_password(new, str(form.get("password_confirmation", "")))
        except ValueError as exc:
            return render(request, "password.html", status=400, error=str(exc))
        user.password_hash = passwords.hash(new)
        user.must_change_password = False
        revoke(db, user.id)
        audit(db, user, "user.password_changed", user.id)
        db.commit()
        response = redirect("/login?changed=1")
        cookie, _, secure = cookies(request)
        response.delete_cookie(cookie, secure=secure, httponly=True, samesite="lax")
        return response

    @app.get("/")
    def home(request: Request):
        return redirect("/timer")

    @app.post("/receiver/select")
    async def receiver_select(request: Request):
        form = await request.form()
        check_csrf(request, form)
        try:
            receiver_id = int(str(form.get("receiver_id", "")))
        except ValueError:
            raise HTTPException(400, "Ungültiger Receiver.") from None
        if receiver_id not in {r.id for r in allowed_receivers(request)}:
            raise HTTPException(403, "Kein Zugriff auf diesen Receiver.")
        request.state.web_session.receiver_id = receiver_id
        request.state.db.commit()
        destination = str(form.get("destination", "/timer"))
        return redirect(
            "/sender"
            if destination == "/epg"
            else destination
            if destination in {"/sender", "/timer", "/aufnahmen"}
            else "/timer"
        )

    def catalog_options(request):
        stype = request.query_params.get("stype", "tv")
        source = request.query_params.get("source", "bouquets")
        if source in {"favorites", "satellites"}:
            source = "bouquets"  # Old bookmarks open the current default selection.
        if stype not in {"tv", "radio"} or source not in {"bouquets", "providers"}:
            raise HTTPException(400, "Ungültige Senderauswahl.")
        return {"stype": stype, "source": source}

    def reference_param(request, key):
        value = request.query_params.get(key, "")
        if len(value) > 2048 or any(ord(char) < 32 for char in value):
            raise HTTPException(400, "Ungültige Senderreferenz.")
        return value

    def label_param(request, key):
        return request.query_params.get(key, "")[:256]

    def catalog_url(path, options, **values):
        return path + "?" + urlencode({**options, **{k: v for k, v in values.items() if v}})

    def service_kind(reference):
        try:
            flags = int(reference.split(":")[1])
        except (ValueError, IndexError):
            return "service"
        if flags & 64:
            return "marker"
        if flags & 7 and not flags & 128:
            return "group"
        return "service"

    def catalog_context(request, *, epg=False):
        options = catalog_options(request)
        for_timer = not epg and request.query_params.get("for_timer") == "1"
        if for_timer:
            options["for_timer"] = "1"
        path = "/epg" if epg else "/sender"
        receiver = selected_receiver(request)
        if for_timer and receiver and not can_write_receiver(request, receiver):
            raise HTTPException(403, "Für diesen Receiver sind nur Leserechte vergeben.")
        rows, error = [], None
        group = reference_param(request, "group" if epg else "reference")
        group_name = label_param(request, "group_name")
        source = options["source"]
        is_group_list = not group
        if receiver:
            try:
                client = app.state.client_factory(receiver, config)
                if group:
                    rows = client.services(group)
                elif source == "providers":
                    rows = client.providers(options["stype"])
                else:
                    rows = client.bouquets(options["stype"])
            except ReceiverError as exc:
                error = str(exc)
        entries = []
        for row in rows:
            reference = row["reference"]
            kind = "group" if is_group_list else service_kind(reference)
            values = {}
            if kind == "group":
                values = {
                    "group" if epg else "reference": reference,
                    "group_name": row["name"][:256],
                }
            elif kind == "service":
                values = {
                    "reference": reference,
                    "name": row["name"][:256],
                    "group": group,
                    "group_name": group_name,
                }
            entries.append(
                {
                    **row,
                    "kind": kind,
                    "href": catalog_url(path if kind == "group" else "/epg", options, **values),
                    "timer_url": catalog_url(
                        "/timer/new", options, **values, receiver_id=receiver.id
                    )
                    if kind == "service" and receiver and can_write_receiver(request, receiver)
                    else None,
                }
            )
        return {
            **options,
            "rows": entries,
            "error": error,
            "epg_browse": epg,
            "for_timer": for_timer,
            "title": "Sender für Timer wählen" if for_timer else "EPG" if epg else "Sender",
            "section_title": group_name
            or ("Sender" if group else {"bouquets": "Bouquets", "providers": "Anbieter"}[source]),
            "is_group_list": is_group_list,
            "group_reference": group,
            "root_url": catalog_url(path, options),
            "type_links": [
                {
                    "label": label,
                    "active": options["stype"] == value,
                    "href": catalog_url(path, {**options, "stype": value}),
                }
                for value, label in [("tv", "TV"), ("radio", "Radio")]
            ],
            "source_links": [
                {
                    "label": label,
                    "active": source == value,
                    "href": catalog_url(path, {**options, "source": value}),
                }
                for value, label in [
                    ("bouquets", "Bouquets"),
                    ("providers", "Anbieter"),
                ]
            ],
        }

    @app.get("/sender")
    def sender_page(request: Request):
        return render(request, "sender.html", **catalog_context(request))

    @app.get("/epg")
    def epg_page(request: Request):
        reference = reference_param(request, "reference")
        if not reference:
            return redirect("/sender")
        options = catalog_options(request)
        group = reference_param(request, "group")
        group_name = label_param(request, "group_name")
        name = label_param(request, "name")
        timestamp = now()
        today = datetime.fromtimestamp(timestamp, timezone).date()
        selected_day = request.query_params.get("day", today.isoformat())
        if selected_day != "all":
            try:
                selected_day = date.fromisoformat(selected_day).isoformat()
            except ValueError:
                raise HTTPException(400, "Ungültiges EPG-Datum.") from None
        receiver = selected_receiver(request)
        events, error = [], None
        if receiver:
            try:
                events = app.state.client_factory(receiver, config).epg(reference)
            except ReceiverError as exc:
                error = str(exc)
        days = {today}
        if selected_day != "all":
            days.add(date.fromisoformat(selected_day))
        sections = {}
        for event in events:
            begin = datetime.fromtimestamp(event.begin, timezone)
            end = datetime.fromtimestamp(event.end, timezone)
            event_day = begin.date()
            days.add(event_day)
            running = event.begin <= timestamp < event.end
            # A programme beginning before midnight still belongs in today's view while running.
            if selected_day != "all" and event_day.isoformat() != selected_day:
                if not (running and selected_day == today.isoformat()):
                    continue
            offset_changed = begin.utcoffset() != end.utcoffset()
            begin_label = begin.strftime("%H:%M")
            end_label = end.strftime("%H:%M" if event_day == end.date() else "%d.%m. %H:%M")
            if offset_changed:
                begin_label += begin.strftime(" %Z")
                end_label += end.strftime(" %Z")
            entry = {
                "event": event,
                "begin": begin,
                "end": end,
                "begin_label": begin_label,
                "end_label": end_label,
                "minutes": (event.duration + 59) // 60,
                "running": running,
                "finished": event.end <= timestamp and event.duration > 0,
                "timer_url": catalog_url(
                    "/timer/new",
                    {},
                    reference=reference,
                    event_id=str(event.id),
                    event_begin=event.begin,
                    receiver_id=receiver.id,
                )
                if receiver
                and can_write_receiver(request, receiver)
                and event.duration > 0
                and event.end > timestamp
                else None,
            }
            sections.setdefault(event_day, []).append(entry)
        return render(
            request,
            "epg.html",
            **options,
            reference=reference,
            name=next((event.name for event in events if event.name), name)
            or "Ausgewählter Sender",
            group=group,
            group_name=group_name,
            selected_day=selected_day,
            days=sorted(days),
            sections=sections,
            error=error,
            timezone=config.timezone,
            back_url=catalog_url("/sender", options, reference=group, group_name=group_name),
        )

    register_timer_pages(
        app,
        config,
        render=render,
        selected_receiver=selected_receiver,
        check_csrf=check_csrf,
        redirect=redirect,
    )

    register_recording_pages(
        app,
        config,
        render=render,
        selected_receiver=selected_receiver,
        check_csrf=check_csrf,
        redirect=redirect,
    )

    @app.get("/admin/receivers")
    def receiver_list(request: Request):
        require_admin(request)
        rows = receiver_rows(request.state.db)
        return render(request, "receivers.html", rows=rows)

    def receiver_form(request, receiver=None, **context):
        return render(
            request,
            "receiver_form.html",
            receiver=receiver,
            values=context.pop("values", receiver),
            **context,
        )

    @app.get("/admin/receivers/new")
    def receiver_new(request: Request):
        require_admin(request)
        return receiver_form(request)

    @app.get("/admin/receivers/{receiver_id}/edit")
    def receiver_edit(request: Request, receiver_id: int):
        require_admin(request)
        receiver = request.state.db.get(Receiver, receiver_id)
        if not receiver:
            raise HTTPException(404, "Receiver nicht gefunden.")
        return receiver_form(request, receiver)

    @app.post("/admin/receivers/save")
    async def receiver_save(request: Request):
        require_admin(request)
        form = await request.form()
        check_csrf(request, form)
        lock_admin(request)
        db = request.state.db
        receiver = None
        try:
            receiver_id = int(str(form.get("id", "0")))
            if receiver_id:
                receiver = db.get(Receiver, receiver_id)
                if not receiver:
                    raise HTTPException(404, "Receiver nicht gefunden.")
            port = int(str(form.get("port", "80")))
            if not 1 <= port <= 65535:
                raise ValueError("Port muss zwischen 1 und 65535 liegen.")
            values = dict(
                name=text_field(str(form.get("name", "")), "Name"),
                hostname=hostname(str(form.get("hostname", ""))),
                port=port,
                username=str(form.get("username", "")).strip(),
                https="https" in form,
                verify_tls="verify_tls" in form,
                enabled="enabled" in form,
            )
            if len(values["username"]) > 128:
                raise ValueError("Receiver-Benutzername ist zu lang.")
            password = str(form.get("password", ""))
            if len(password) > 256:
                raise ValueError("Receiver-Passwort ist zu lang.")
            if password:
                values["encrypted_password"] = cipher(config).encrypt(password.encode()).decode()
            elif "clear_password" in form:
                values["encrypted_password"] = ""
        except ValueError as exc:
            db.rollback()
            return receiver_form(
                request,
                receiver,
                status=400,
                error=str(exc),
                values={**dict(form), **{k: k in form for k in ["https", "verify_tls", "enabled"]}},
            )
        if not receiver:
            receiver = Receiver(**values)
            db.add(receiver)
        else:
            for key, value in values.items():
                setattr(receiver, key, value)
        db.flush()
        audit(db, request.state.user, "receiver.saved", receiver.id)
        db.commit()
        return redirect("/admin/receivers")

    @app.post("/admin/receivers/{receiver_id}/test")
    async def receiver_test(request: Request, receiver_id: int):
        require_admin(request)
        check_csrf(request, await request.form())
        receiver = request.state.db.get(Receiver, receiver_id)
        if not receiver:
            raise HTTPException(404, "Receiver nicht gefunden.")
        # Run blocking network requests in a worker so an offline box does not freeze the UI.
        from starlette.concurrency import run_in_threadpool

        try:
            rows = await run_in_threadpool(app.state.client_factory(receiver, config).services)
            notice, error = f"Verbindung erfolgreich: {len(rows)} Listeneinträge empfangen.", None
        except ReceiverError as exc:
            notice, error = None, str(exc)
        receivers = receiver_rows(request.state.db)
        return render(
            request,
            "receivers.html",
            rows=receivers,
            notice=notice,
            error=error,
            tested_id=receiver.id,
        )

    @app.post("/admin/receivers/{receiver_id}/delete")
    async def receiver_delete(request: Request, receiver_id: int):
        form = await request.form()
        check_csrf(request, form)
        if form.get("confirmed") != "true":
            raise HTTPException(400, "Bitte den Löschen-Button zweimal drücken.")
        lock_admin(request)
        db = request.state.db
        receiver = db.get(Receiver, receiver_id)
        if not receiver:
            raise HTTPException(404, "Receiver nicht gefunden.")
        if db.scalar(
            select(TimerAction.token_hash).where(
                TimerAction.locked_receiver_id == receiver.id, TimerAction.lock_until > now()
            )
        ):
            raise HTTPException(
                409, "Ein Auftrag für diesen Receiver läuft noch. Bitte kurz warten."
            )
        audit(db, request.state.user, "receiver.deleted", receiver.id)
        db.delete(receiver)
        db.commit()
        return redirect("/admin/receivers")

    @app.get("/admin/users")
    def user_list(request: Request):
        require_admin(request)
        db = request.state.db
        last_logins = {
            user_id: datetime.fromtimestamp(timestamp, timezone)
            for user_id, timestamp in db.execute(
                select(AuditLog.actor_id, func.max(AuditLog.created_at))
                .where(AuditLog.action == "login.succeeded", AuditLog.actor_id.is_not(None))
                .group_by(AuditLog.actor_id)
            )
        }
        return render(
            request,
            "users.html",
            rows=list(db.scalars(select(User).order_by(User.username))),
            last_logins=last_logins,
        )

    def user_form(request, target=None, **context):
        db = request.state.db
        grants = (
            {
                g.receiver_id: "write" if g.can_write else "read"
                for g in db.scalars(select(Grant).where(Grant.user_id == target.id))
            }
            if target
            else {}
        )
        return render(
            request,
            "user_form.html",
            target=target,
            all_boxes=receiver_rows(db),
            grants=context.pop("grants", grants),
            values=context.pop("values", target),
            owner_tag=(
                db.scalar(select(OwnerTag.marker).where(OwnerTag.owner_id == target.id))
                if target
                else None
            ),
            **context,
        )

    @app.get("/admin/users/new")
    def user_new(request: Request):
        require_admin(request)
        return user_form(request)

    @app.get("/admin/users/{user_id}/edit")
    def user_edit(request: Request, user_id: int):
        require_admin(request)
        target = request.state.db.get(User, user_id)
        if not target:
            raise HTTPException(404, "Benutzer nicht gefunden.")
        return user_form(request, target)

    @app.post("/admin/users/save")
    async def user_save(request: Request):
        form = await request.form()
        check_csrf(request, form)
        lock_admin(request)
        db, actor = request.state.db, request.state.user
        target = None
        try:
            user_id = int(str(form.get("id", "0")))
            target = db.get(User, user_id) if user_id else None
            if user_id and not target:
                raise HTTPException(404, "Benutzer nicht gefunden.")
            name = target.username if target else username(str(form.get("username", "")))
            display_name = text_field(str(form.get("display_name", "")), "Anzeigename")
            role = str(form.get("role", "user"))
            if role not in {"admin", "user"}:
                raise ValueError("Ungültige Benutzerrolle.")
            active = "active" in form
            known = set(db.scalars(select(Receiver.id)))
            mode = str(form.get("access_mode", ""))
            if role == "admin":
                all_boxes, all_write, grants = True, True, {}
            elif mode:
                if mode not in {"assigned", "all_read", "all_write"}:
                    raise ValueError("Ungültige Receiver-Berechtigung.")
                all_boxes, all_write = mode != "assigned", mode == "all_write"
                grants = {}
                for key, level in form.items():
                    if not key.startswith("receiver_access_"):
                        continue
                    receiver_id = int(key.removeprefix("receiver_access_"))
                    if level not in {"none", "read", "write"}:
                        raise ValueError("Ungültige Receiver-Berechtigung.")
                    if level != "none":
                        grants[receiver_id] = level
            else:
                # Accept old admin forms during an upgrade with their original write rights.
                all_boxes, all_write = "all_receivers" in form, True
                grants = {int(str(x)): "write" for x in form.getlist("receiver_ids")}
            if not set(grants).issubset(known):
                raise ValueError("Ein ausgewählter Receiver existiert nicht mehr.")
            default_receiver_id = (
                int(form["default_receiver_id"]) if form.get("default_receiver_id") else None
            )
            if default_receiver_id is not None:
                default_receiver = db.get(Receiver, default_receiver_id)
                if not default_receiver or not default_receiver.enabled:
                    raise ValueError("Bitte einen aktivierten Standardreceiver auswählen.")
                if role != "admin" and not all_boxes and default_receiver_id not in grants:
                    raise ValueError(
                        "Der Standardreceiver muss für diesen Benutzer freigegeben sein."
                    )
            if target and target.id == actor.id and (role != "admin" or not active):
                raise ValueError(
                    "Das eigene Administratorkonto kann nicht deaktiviert "
                    "oder zum Benutzer herabgestuft werden."
                )
            if (
                target
                and target.is_admin
                and target.active
                and (not active or role != "admin")
                and active_admins(db) <= 1
            ):
                raise ValueError("Der letzte aktive Administrator muss erhalten bleiben.")
            password = str(form.get("password", ""))
            if password or not target:
                validate_password(password, str(form.get("password_confirmation", "")))
            if not target and db.scalar(select(User.id).where(User.username == name)):
                raise ValueError("Dieser Benutzername ist bereits vergeben.")
        except ValueError as exc:
            db.rollback()
            return user_form(
                request,
                target,
                status=400,
                error=str(exc),
                values={**dict(form), **{k: k in form for k in ["active", "all_receivers"]}},
                grants={
                    int(key.removeprefix("receiver_access_")): str(value)
                    for key, value in form.items()
                    if key.startswith("receiver_access_")
                    and key.removeprefix("receiver_access_").isdigit()
                },
            )
        if not target:
            target = User(
                username=name,
                display_name=display_name,
                password_hash=passwords.hash(password),
                role=role,
                active=active,
                all_receivers=all_boxes,
                all_receivers_write=all_write,
                must_change_password=True,
                default_receiver_id=default_receiver_id,
            )
            db.add(target)
            db.flush()
            ensure_owner_tag(db, target)
        else:
            target.display_name, target.role = display_name, role
            target.active, target.all_receivers = active, all_boxes
            target.all_receivers_write = all_write
            target.default_receiver_id = default_receiver_id
            if password:
                target.password_hash = passwords.hash(password)
                target.must_change_password = True
            # Every permission or account edit takes effect for all existing sessions.
            revoke(db, target.id)
        db.execute(delete(Grant).where(Grant.user_id == target.id))
        for receiver_id, level in grants.items():
            db.add(Grant(user_id=target.id, receiver_id=receiver_id, can_write=level == "write"))
        audit(db, actor, "user.saved", target.id)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            return user_form(
                request, target, status=400, error="Dieser Benutzername ist bereits vergeben."
            )
        return redirect("/admin/users")

    @app.post("/admin/users/{user_id}/delete")
    async def user_delete(request: Request, user_id: int):
        form = await request.form()
        check_csrf(request, form)
        if form.get("confirmed") != "true":
            raise HTTPException(400, "Bitte den Löschen-Button zweimal drücken.")
        lock_admin(request)
        db, actor = request.state.db, request.state.user
        target = db.get(User, user_id)
        if not target:
            raise HTTPException(404, "Benutzer nicht gefunden.")
        if target.id == actor.id or (target.is_admin and target.active and active_admins(db) <= 1):
            raise HTTPException(
                400,
                "Das eigene Konto und der letzte aktive Administrator "
                "können nicht gelöscht werden.",
            )
        audit(db, actor, "user.deleted", target.id)
        db.delete(target)
        db.commit()
        return redirect("/admin/users")

    return app
