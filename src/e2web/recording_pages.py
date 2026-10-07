from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import PurePosixPath
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool

from e2web.channel_details import recording_channel_details
from e2web.db import User, WebSession
from e2web.openwebif import ReceiverError, TimerOutcomeUnknown
from e2web.ownership import can_manage, owner_name, require_manage
from e2web.receiver_actions import ReceiverActions
from e2web.recordings import directory_path, duration_label, recording_running
from e2web.security import now, token_hash


def register_recording_pages(app, config, *, render, selected_receiver, check_csrf, redirect):
    timezone = ZoneInfo(config.timezone)
    actions = ReceiverActions(config, selected_receiver)

    def link(path):
        return "/aufnahmen?" + urlencode({"directory": path})

    def load_recordings(client, requested):
        try:
            paths, _ = client.recording_locations()
            roots = [directory_path(path) for path in paths]
        except (ReceiverError, ValueError):
            roots = []
        try:
            requested = directory_path(requested) if requested else ""
        except ValueError:
            raise HTTPException(400, "Ungültiger Aufnahmepfad.") from None
        try:
            default_path = client.default_recording_location()
        except ReceiverError:
            default_path = ""
        if default_path:
            roots.append(default_path)
        elif not requested:
            # Match the first offered folder; always send an explicit movielist path.
            roots = sorted(set(roots), key=str.casefold)
            if not roots:
                return None, "", roots
            default_path = roots[0]
        listing = None
        if requested and not any(requested.startswith(root) for root in roots):
            # OpenWebif resolves symlinks (e.g. /hdd -> /media/hdd) in its
            # response. Resolve only configured roots, never the requested path,
            # before accepting a canonical root returned by the receiver.
            probes = list(dict.fromkeys(path for path in [default_path, *roots] if path))
            for root in probes:
                try:
                    resolved = client.recording_list(root or None)
                except ReceiverError:
                    continue
                if resolved.directory:
                    canonical = directory_path(resolved.directory)
                    roots.append(canonical)
                    if requested.startswith(canonical):
                        if requested == canonical:
                            listing = resolved
                        break
            if not any(requested.startswith(root) for root in roots):
                raise HTTPException(403, "Dieser Ordner liegt außerhalb der Aufnahmepfade.")
        if listing is None:
            listing = client.recording_list(requested or default_path or None)
        directory = listing.directory or requested or default_path
        if not requested and directory:
            roots.append(directory)
        return listing, directory, sorted(set(roots), key=str.casefold)

    def recording_page(request, *, action_error=None, status=200):
        receiver = selected_receiver(request)
        entries, directory_choices, directory, error = [], [], "", None
        status_error = None
        free_space = None
        if receiver:
            client = app.state.client_factory(receiver, config)
            app.state.channel_catalog.view(receiver, client)
            try:
                requested = (
                    getattr(request.state, "recording_return_directory", "")
                    if request.url.path == "/aufnahmen/delete"
                    else request.query_params.get("directory", "")
                )
                listing, directory, roots = load_recordings(client, requested)
                directory_choices = list(roots)
                if listing is None:
                    raise ReceiverError(
                        "Der konfigurierte Standardaufnahmeordner konnte nicht ermittelt werden. "
                        "Es sind keine auswählbaren Aufnahmepfade verfügbar."
                    )
                if directory:
                    directory_choices.append(directory)
                    for parent in PurePosixPath(directory).parents:
                        path = directory_path(str(parent))
                        if any(path.startswith(root) for root in roots):
                            directory_choices.append(path)
                    for folder in listing.folders:
                        try:
                            child = directory_path(
                                folder if folder.startswith("/") else directory + folder
                            )
                        except ValueError:
                            continue
                        if child != directory and child.startswith(directory):
                            directory_choices.append(child)
                directory_choices = sorted(set(directory_choices), key=str.casefold)
                try:
                    timers = client.timer_list().timers
                except ReceiverError:
                    timers = None
                    status_error = (
                        "Der Status laufender Aufnahmen konnte nicht geprüft werden. "
                        "Löschen ist vorübergehend nicht verfügbar."
                    )
                channels = app.state.channel_catalog.view(receiver, client)
                for recording in sorted(
                    listing.recordings, key=lambda r: (-r.begin, r.title.casefold(), r.reference)
                ):
                    running = timers is not None and recording_running(
                        recording, timers, protect_unknown=False
                    )
                    status_known = timers is not None and (
                        running
                        or not any(
                            t.state == 2 and not t.justplay and not t.filename for t in timers
                        )
                    )
                    entries.append(
                        {
                            "recording": recording,
                            "owner_name": owner_name(request, receiver, recording),
                            "channel_details": recording_channel_details(
                                channels, recording, timers
                            ),
                            "can_manage": can_manage(request, receiver, recording),
                            "running": running,
                            "status_known": status_known,
                            "begin": datetime.fromtimestamp(recording.begin, timezone)
                            if recording.begin
                            else None,
                            "duration": duration_label(recording.duration),
                            "delete_token": None,
                            "download_url": "/aufnahmen/download?"
                            + urlencode(
                                {
                                    "receiver_id": receiver.id,
                                    "reference": recording.reference,
                                    "directory": directory,
                                }
                            ),
                        }
                    )
                deletable = (
                    [
                        item
                        for item in entries
                        if item["can_manage"]
                        and timers is not None
                        and not recording_running(item["recording"], timers)
                    ]
                    if app.state.can_write_receiver(request, receiver)
                    else []
                )
                tokens = actions.issue_many(
                    request,
                    receiver,
                    "recording",
                    [
                        (
                            "delete",
                            {
                                "reference": item["recording"].reference,
                                "fingerprint": item["recording"].fingerprint,
                                "directory": directory,
                            },
                        )
                        for item in deletable
                    ],
                )
                for item, raw in zip(deletable, tokens, strict=True):
                    item["delete_token"] = raw
                try:
                    free_space = client.recording_free_space(directory)
                except ReceiverError:
                    pass  # Optional storage information must not hide the recordings.
            except ReceiverError as exc:
                error = str(exc)
        return render(
            request,
            "recordings.html",
            entries=entries,
            directory=directory,
            directory_choices=directory_choices,
            free_space=free_space,
            timezone=config.timezone,
            error=action_error or error or status_error,
            list_failed=bool(error),
            status=status,
            notice="Aufnahme entfernt." if request.query_params.get("done") == "deleted" else None,
        )

    app.state.recording_page = recording_page

    @app.get("/aufnahmen")
    def recording_list_page(request: Request):
        bound = request.query_params.get("live_receiver")
        receiver = selected_receiver(request)
        if bound and (not receiver or bound != str(receiver.id)):
            raise HTTPException(409, "Der Receiver wurde gewechselt. Bitte die Seite neu öffnen.")
        return recording_page(request)

    def verify_download_access(request, receiver_id, fingerprint):
        db = request.state.db
        db.commit()
        db.expire_all()
        session = db.get(WebSession, token_hash(request.state.raw_token))
        user = db.get(User, session.user_id) if session else None
        if (
            not session
            or session.expires_at <= now()
            or not user
            or not user.active
            or user.must_change_password
        ):
            request.state.user, request.state.web_session = None, None
            raise HTTPException(403, "Die Sitzung ist nicht mehr gültig. Bitte erneut anmelden.")
        request.state.user, request.state.web_session = user, session
        current = selected_receiver(request)
        if (
            not current
            or current.id != receiver_id
            or actions.connection_fingerprint(current) != fingerprint
        ):
            raise HTTPException(
                409, "Receiver oder Berechtigung geändert. Aufnahmeliste neu öffnen."
            )
        db.commit()

    @app.get("/aufnahmen/download")
    def recording_download(request: Request):
        receiver = selected_receiver(request)
        if not receiver or request.query_params.get("receiver_id") != str(receiver.id):
            raise HTTPException(409, "Der Receiver wurde geändert. Aufnahmeliste neu öffnen.")
        reference = request.query_params.get("reference", "")
        if not reference or len(reference) > 4096 or any(ord(c) < 32 for c in reference):
            raise HTTPException(400, "Ungültige Aufnahmereferenz.")
        range_header = request.headers.get("Range")
        if range_header and (
            len(range_header) > 128 or not re.fullmatch(r"bytes=(?:\d+-\d*|-\d+)", range_header)
        ):
            raise HTTPException(416, "Bitte nur einen gültigen Downloadbereich anfordern.")
        receiver_id = receiver.id
        fingerprint = actions.connection_fingerprint(receiver)
        request.state.db.commit()
        try:
            client = app.state.client_factory(receiver, config)
            listing, _, _ = load_recordings(client, request.query_params.get("directory", ""))
            matches = [r for r in listing.recordings if r.reference == reference]
            if len(matches) != 1:
                raise HTTPException(404, "Die Aufnahme wurde geändert oder entfernt.")
            verify_download_access(request, receiver_id, fingerprint)
            stream = client.open_recording(matches[0].filename, range_header)
        except ReceiverError as exc:
            raise HTTPException(502, str(exc)) from None
        try:
            # Opening the file can also wait for the HDD; check before any response bytes.
            verify_download_access(request, receiver_id, fingerprint)
            response = stream.response
            filename = PurePosixPath(matches[0].filename).name
            ascii_name = (
                re.sub(
                    r"[^a-zA-Z0-9 _().-]",
                    "_",
                    unicodedata.normalize("NFKD", filename).encode("ascii", "ignore").decode(),
                )
                or "aufnahme.ts"
            )
            headers = {
                "Content-Disposition": (
                    f'attachment; filename="{ascii_name}"; '
                    f"filename*=UTF-8''{quote(filename, safe='')}"
                ),
                "X-Accel-Buffering": "no",
            }
            length = response.headers.get("Content-Length", "")
            if length.isdecimal() and len(length) < 20:
                headers["Content-Length"] = length
            content_range = response.headers.get("Content-Range", "")
            if response.status_code in {206, 416}:
                if not re.fullmatch(r"bytes (?:\d+-\d+|\*)/\d+", content_range):
                    raise HTTPException(
                        502, "Der Receiver liefert einen ungültigen Downloadbereich."
                    )
                headers["Content-Range"] = content_range
            if response.headers.get("Accept-Ranges") == "bytes":
                headers["Accept-Ranges"] = "bytes"
            if response.status_code == 416:
                stream.close()
                headers["Content-Length"] = "0"
                return Response(status_code=416, headers=headers)
            return StreamingResponse(
                stream.chunks(),
                status_code=response.status_code,
                media_type="application/octet-stream",
                headers=headers,
                background=BackgroundTask(stream.close),
            )
        except BaseException:
            stream.close()
            raise

    def remove(request, form):
        check_csrf(request, form)
        if form.get("confirmed") != "true":
            raise HTTPException(400, "Bitte den Löschen-Button zweimal drücken.")
        action, receiver, payload = actions.claim(
            request, str(form.get("action_token", "")), "recording", {"delete"}
        )
        request.state.recording_return_directory = payload["directory"]
        outcome = "not_sent"
        try:
            client = app.state.client_factory(receiver, config)
            listing = client.recording_list(payload["directory"] or None)
            matches = [r for r in listing.recordings if r.reference == payload["reference"]]
            if len(matches) != 1 or matches[0].fingerprint != payload["fingerprint"]:
                raise HTTPException(
                    409,
                    "Die Aufnahme wurde geändert oder entfernt. Bitte die aktuelle Liste prüfen.",
                )
            if recording_running(matches[0], client.timer_list().timers):
                raise HTTPException(
                    409, "Diese Aufnahme läuft noch. Bitte zuerst ihren Timer beenden."
                )
            outcome = "unknown"
            actions.verify_authority(request, action, receiver)
            require_manage(request, receiver, matches[0])
            result = client.delete_recording(matches[0].reference, xml=listing.xml)
            outcome = "success" if result.success else "rejected"
            if result.success:
                return redirect(
                    "/aufnahmen?"
                    + urlencode({"directory": payload["directory"], "done": "deleted"})
                )
            return recording_page(
                request,
                action_error="Der Receiver hat das Löschen der Aufnahme abgelehnt.",
                status=409,
            )
        except TimerOutcomeUnknown:
            return recording_page(
                request,
                action_error="Der Ausgang des Löschauftrags ist unklar. "
                "Bitte die Aufnahmeliste prüfen. Der Auftrag wurde nicht wiederholt.",
                status=502,
            )
        except ReceiverError as exc:
            return recording_page(request, action_error=str(exc), status=502)
        finally:
            actions.finish(request, action, receiver, "recording", outcome)

    @app.post("/aufnahmen/delete")
    async def recording_delete(request: Request):
        form = await request.form()
        return await run_in_threadpool(remove, request, form)
