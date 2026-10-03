from __future__ import annotations

import json
from datetime import datetime
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool

from e2web.openwebif import ReceiverError, TimerOutcomeUnknown
from e2web.ownership import can_manage, create_marker, owner_name, readable_tags, require_manage
from e2web.receiver_actions import ReceiverActions
from e2web.recordings import duration_label
from e2web.security import now
from e2web.timer_files import timer_files
from e2web.timer_selection import bouquet_services, recordable_service, timer_bouquets, timer_paths
from e2web.timers import WEEKDAYS, local_timestamp, service_key


def register_timer_pages(app, config, *, render, selected_receiver, check_csrf, redirect):
    timezone = ZoneInfo(config.timezone)

    def client_for(receiver):
        return app.state.client_factory(receiver, config)

    def receiver_for(request):
        receiver = selected_receiver(request)
        if not receiver:
            raise HTTPException(403, "Kein Receiver für diesen Benutzer verfügbar.")
        if not app.state.can_write_receiver(request, receiver):
            raise HTTPException(403, "Für diesen Receiver sind nur Leserechte vergeben.")
        bound = request.query_params.get("receiver_id")
        if bound is not None and bound != str(receiver.id):
            raise HTTPException(
                409, "Der Receiver wurde gewechselt. Bitte die Timerliste neu öffnen."
            )
        return receiver

    def action_url(path, receiver, timer):
        return path + "?" + urlencode({"receiver_id": receiver.id, **timer.identity})

    def find_timer(timers, identity):
        matches = [
            t
            for t in timers
            if service_key(t.reference) == service_key(identity["reference"])
            and t.begin == identity["begin"]
            and t.end == identity["end"]
        ]
        if len(matches) != 1:
            raise HTTPException(
                409, "Der Timer wurde geändert oder entfernt. Timerliste neu öffnen."
            )
        return matches[0]

    def query_identity(request):
        try:
            return {
                "reference": request.query_params["reference"][:2048],
                "begin": int(request.query_params["begin"]),
                "end": int(request.query_params["end"]),
            }
        except (KeyError, ValueError):
            raise HTTPException(400, "Ungültige Timerauswahl.") from None

    actions = ReceiverActions(config, selected_receiver)

    def issue(request, receiver, kind, payload):
        return actions.issue(request, receiver, "timer", kind, payload)

    def get_action(request, raw, kinds):
        return actions.get(request, raw, "timer", kinds)

    def claim(request, raw, kinds):
        return actions.claim(request, raw, "timer", kinds)

    def finish(request, action, receiver, outcome):
        return actions.finish(request, action, receiver, "timer", outcome)

    def local_input(timestamp):
        return datetime.fromtimestamp(timestamp, timezone).strftime("%Y-%m-%dT%H:%M:%S")

    def form_page(
        request, receiver, payload, raw, *, values=None, error=None, status=200, conflicts=None
    ):
        settings = payload["settings"]
        selection = payload.get("selection")
        if selection and values:
            selection = {**selection, "group": values["bouquet"]}
            try:
                selection["services"] = bouquet_services(
                    client_for(receiver), selection["bouquets"], values["bouquet"]
                )
            except (ReceiverError, HTTPException):
                selection["services"] = []
        defaults = {
            "name": settings["name"],
            "description": settings["description"],
            "begin": local_input(int(settings["begin"])),
            "end": local_input(int(settings["end"])),
            "begin_fold": "",
            "end_fold": "",
            "directory": settings["dirname"],
            "disabled": settings["disabled"] == "1",
            "weekdays": [str(n) for n in range(7) if int(settings["repeated"]) & (1 << n)],
            "before": "0",
            "after": "0",
            "bouquet": (payload.get("selection") or {}).get("group", ""),
            "reference": settings["sRef"],
        }
        return render(
            request,
            "timer_form.html",
            receiver=receiver,
            action_token=raw,
            editing="identity" in payload,
            channel=payload["channel"],
            selection=selection,
            values=defaults if values is None else values,
            locations=payload["locations"],
            weekdays=WEEKDAYS,
            timezone=config.timezone,
            from_epg=bool(payload.get("event")),
            justplay=settings["justplay"] == "1",
            error=error,
            status=status,
            conflicts=conflicts or [],
        )

    def result_page(request, receiver, message, *, error=None, status=409, conflicts=None):
        return render(
            request,
            "timer_result.html",
            receiver=receiver,
            message=message,
            error=error,
            status=status,
            conflicts=conflicts or [],
        )

    def timer_page(request, *, action_error=None, status=200):
        receiver = selected_receiver(request)
        running, upcoming, finished, error, xml = [], [], [], None, False
        file_error = None
        if receiver:
            try:
                client = client_for(receiver)
                app.state.channel_catalog.view(receiver, client)
                listing = client.timer_list()
                files, files_failed = timer_files(client, listing.timers)
                if files_failed:
                    file_error = "Dateigrößen konnten nicht vollständig geladen werden."
                xml = listing.xml
                channels = app.state.channel_catalog.view(receiver, client)
                for timer in sorted(listing.timers, key=lambda t: (t.begin, t.name.casefold())):
                    item = {
                        "timer": timer,
                        "file": files.get(timer.identity_key),
                        "owner_name": owner_name(request, receiver, timer, timer=True),
                        "channel_details": channels.describe(timer.reference, timer.channel),
                        "can_manage": can_manage(request, receiver, timer, timer=True),
                        "begin": datetime.fromtimestamp(timer.begin, timezone),
                        "end": datetime.fromtimestamp(timer.end, timezone),
                        "edit_url": action_url("/timer/edit", receiver, timer),
                        "duration": duration_label(
                            max(0, min(now(), timer.end) - timer.begin)
                            if timer.state == 2
                            else timer.end - timer.begin
                        ),
                    }
                    section = (
                        finished if timer.state == 3 else running if timer.state == 2 else upcoming
                    )
                    section.append(item)
                items = [item for item in running + upcoming + finished if item["can_manage"]]
                tokens = actions.issue_many(
                    request,
                    receiver,
                    "timer",
                    [
                        (
                            "delete",
                            {
                                "identity": item["timer"].identity,
                                "fingerprint": item["timer"].fingerprint,
                                "running": item["timer"].state == 2,
                            },
                        )
                        for item in items
                    ],
                )
                for item, raw in zip(items, tokens, strict=True):
                    item["delete_token"] = raw
            except ReceiverError as exc:
                error = str(exc)
        notices = {
            "added": "Timer angelegt.",
            "changed": "Timer gespeichert.",
            "deleted": "Timer gelöscht.",
        }
        return render(
            request,
            "timers.html",
            running=running,
            upcoming=upcoming,
            file_error=file_error,
            finished=finished,
            xml=xml,
            error=action_error or error,
            list_failed=bool(error),
            status=status,
            notice=notices.get(request.query_params.get("done")),
            timezone=config.timezone,
        )

    app.state.timer_page = timer_page

    @app.get("/timer")
    def timer_list_page(request: Request):
        bound = request.query_params.get("live_receiver")
        receiver = selected_receiver(request)
        if bound and (not receiver or bound != str(receiver.id)):
            raise HTTPException(409, "Der Receiver wurde gewechselt. Bitte die Seite neu öffnen.")
        return timer_page(request)

    @app.get("/timer/new")
    def timer_new(request: Request):
        receiver = receiver_for(request)
        reference = request.query_params.get("reference", "")
        if len(reference) > 2048 or any(ord(c) < 32 for c in reference):
            raise HTTPException(400, "Ungültiger Sender.")
        try:
            client = client_for(receiver)
            event_info = None
            selection = None
            if "event_id" in request.query_params:
                try:
                    eid = int(request.query_params["event_id"])
                    event_begin = int(request.query_params["event_begin"])
                except (KeyError, ValueError):
                    raise HTTPException(400, "Ungültige EPG-Auswahl.") from None
                event = next(
                    (
                        event
                        for event in client.epg(reference)
                        if event.id == eid and event.begin == event_begin
                    ),
                    None,
                )
                if not event or event.duration <= 0 or event.end <= now():
                    raise HTTPException(
                        409, "Die Sendung ist nicht mehr verfügbar. EPG neu öffnen."
                    )
                reference, channel = event.reference, event.name or "Ausgewählter Sender"
                begin, end, name = event.begin, event.end, event.title[:256]
                description = (event.short_description or event.description)[:4000]
                event_info = {"id": event.id, "begin": event.begin, "reference": reference}
            elif not reference:
                groups = timer_bouquets(client)
                group = request.query_params.get("group") or (
                    groups[0]["reference"] if groups else ""
                )
                services = bouquet_services(client, groups, group) if group else []
                row = services[0] if services else None
                reference = row["reference"] if row else ""
                channel = row["name"] if row else ""
                begin = (now() // 60 + 5) * 60
                end, name, description = begin + 3600, channel[:256], ""
                selection = {"bouquets": groups, "group": group, "services": services}
            else:
                group = request.query_params.get("group", "")
                if group:
                    if len(group) > 2048 or any(ord(c) < 32 for c in group):
                        raise HTTPException(400, "Ungültige Sendergruppe.")
                    services = client.services(group)
                else:
                    raise HTTPException(400, "Bitte einen Sender aus der Senderliste wählen.")
                row = next((s for s in services if s["reference"] == reference), None)
                if not row:
                    raise HTTPException(
                        409, "Der Sender ist nicht mehr verfügbar. Senderliste neu öffnen."
                    )
                try:
                    flags = int(reference.split(":")[1])
                    if flags & 64 or (flags & 7 and not flags & 128):
                        raise ValueError
                except (ValueError, IndexError):
                    raise HTTPException(400, "Bitte einen aufnehmbaren Sender wählen.") from None
                channel = row["name"]
                begin = (now() // 60 + 5) * 60
                end, name, description = begin + 3600, channel[:256], ""
                groups = timer_bouquets(client)
                if group in {entry["reference"] for entry in groups}:
                    selection = {
                        "bouquets": groups,
                        "group": group,
                        "services": [
                            entry for entry in services if recordable_service(entry["reference"])
                        ],
                    }
            listing = client.timer_list()
            locations, default_location = timer_paths(client, listing)
            payload = {
                "channel": channel,
                "event": event_info,
                "selection": selection,
                "locations": locations,
                "settings": {
                    "sRef": reference,
                    "name": name,
                    "description": description,
                    "begin": str(begin),
                    "end": str(end),
                    "repeated": "0",
                    "disabled": "0",
                    "justplay": "0",
                    "afterevent": "0",
                    "tags": "",
                    "dirname": default_location,
                    "eit": str(event_info["id"] if event_info else 0),
                    "always_zap": "0",
                    "pipzap": "0",
                },
            }
            return form_page(request, receiver, payload, issue(request, receiver, "add", payload))
        except ReceiverError as exc:
            return result_page(
                request,
                receiver,
                "Der Timerentwurf konnte nicht geladen werden.",
                error=str(exc),
                status=502,
            )

    @app.get("/timer/channels")
    def timer_channels(request: Request):
        receiver = receiver_for(request)
        group = request.query_params.get("bouquet", "")
        try:
            client = client_for(receiver)
            groups = timer_bouquets(client)
            return {"services": bouquet_services(client, groups, group)}
        except ReceiverError as exc:
            raise HTTPException(502, str(exc)) from None

    @app.get("/timer/edit")
    def timer_edit(request: Request):
        receiver = receiver_for(request)
        try:
            listing = client_for(receiver).timer_list()
            timer = find_timer(listing.timers, query_identity(request))
            require_manage(request, receiver, timer, timer=True)
            locations, directory = timer_paths(
                client_for(receiver), listing, preferred=timer.directory
            )
            payload = {
                "identity": timer.identity,
                "fingerprint": timer.fingerprint,
                "channel": timer.channel,
                "settings": {**timer.settings, "dirname": directory},
                "locations": locations,
            }
            return form_page(request, receiver, payload, issue(request, receiver, "edit", payload))
        except ReceiverError as exc:
            return result_page(
                request,
                receiver,
                "Der Timer konnte nicht geladen werden.",
                error=str(exc),
                status=502,
            )

    @app.get("/timer/delete")
    def old_delete_page(request: Request):
        return redirect("/timer")

    def parse_form(form, payload):
        values = {
            key: str(form.get(key, ""))
            for key in (
                "name",
                "description",
                "begin",
                "end",
                "directory",
                "before",
                "after",
                "begin_fold",
                "end_fold",
                "bouquet",
                "reference",
            )
        }
        if payload.get("selection"):
            values["bouquet"] = str(form.get("bouquet", payload["selection"]["group"]))
            values["reference"] = str(form.get("reference", payload["settings"]["sRef"]))
        values["disabled"] = form.get("disabled") == "on"
        values["weekdays"] = [str(day) for day in form.getlist("weekdays")]
        try:
            name, description = values["name"].strip(), values["description"].strip()
            if not name or len(name) > 256 or any(ord(c) < 32 for c in name):
                raise ValueError("Bitte einen Timernamen mit 1 bis 256 Zeichen eingeben.")
            if len(description) > 4000 or any(
                ord(c) < 32 and c not in "\n\r\t" for c in description
            ):
                raise ValueError("Die Beschreibung darf höchstens 4000 Zeichen enthalten.")
            settings = payload["settings"]
            if payload.get("selection") and not recordable_service(values["reference"]):
                raise ValueError("Bitte einen aufnehmbaren Sender auswählen.")
            begin = local_timestamp(
                values["begin"],
                timezone,
                fold=values["begin_fold"],
                original=int(settings["begin"]),
            )
            end = local_timestamp(
                values["end"], timezone, fold=values["end_fold"], original=int(settings["end"])
            )
            if payload.get("event") and "identity" not in payload:
                before, after = int(values["before"] or 0), int(values["after"] or 0)
                if not 0 <= before <= 120 or not 0 <= after <= 120:
                    raise ValueError("Vor- und Nachlauf müssen zwischen 0 und 120 Minuten liegen.")
                begin, end = begin - before * 60, end + after * 60
            if not 0 < end - begin <= 604800 or begin < 1:
                raise ValueError(
                    "Das Ende muss nach dem Beginn liegen; höchstens sieben Tage Abstand."
                )
            if not set(values["weekdays"]) <= {str(n) for n in range(7)}:
                raise ValueError("Ungültige Wiederholung.")
            repeated = sum(1 << int(day) for day in set(values["weekdays"]))
            if not repeated and end <= now() and "identity" not in payload:
                raise ValueError(
                    "Der neue Timer darf nicht vollständig in der Vergangenheit liegen."
                )
            allowed_paths = {path for path in [settings["dirname"], *payload["locations"]] if path}
            if values["directory"] not in allowed_paths:
                raise ValueError("Bitte einen der angebotenen Aufnahmepfade wählen.")
            return (
                values,
                {
                    **settings,
                    "name": name,
                    "description": description,
                    "begin": str(begin),
                    "end": str(end),
                    "disabled": "1" if values["disabled"] else "0",
                    "repeated": str(repeated),
                    "dirname": values["directory"],
                },
                None,
            )
        except (ValueError, OverflowError) as exc:
            message = str(exc)
            if message.startswith("invalid literal"):
                message = "Bitte gültige Minutenangaben eingeben."
            return values, None, message

    def save(request, form):
        check_csrf(request, form)
        receiver = selected_receiver(request)
        if receiver and not app.state.can_write_receiver(request, receiver):
            raise HTTPException(403, "Für diesen Receiver sind nur Leserechte vergeben.")
        raw = str(form.get("action_token", ""))
        action = get_action(request, raw, {"add", "edit"})
        payload = json.loads(action.payload)
        values, params, error = parse_form(form, payload)
        if error:
            receiver = selected_receiver(request)
            if not receiver or receiver.id != action.receiver_id:
                raise HTTPException(409, "Der Receiver wurde geändert. Timerliste neu öffnen.")
            return form_page(
                request, receiver, payload, raw, values=values, error=error, status=400
            )
        action, receiver, payload = claim(request, raw, {"add", "edit"})
        outcome = "not_sent"
        try:
            client = client_for(receiver)
            listing = client.timer_list()
            if payload.get("selection"):
                groups = timer_bouquets(client)
                services = bouquet_services(client, groups, values["bouquet"])
                selected = next(
                    (row for row in services if row["reference"] == values["reference"]), None
                )
                if selected is None:
                    raise HTTPException(
                        409, "Der Sender ist nicht mehr verfügbar. Timerformular neu öffnen."
                    )
                params["sRef"] = selected["reference"]
            method = "timeradd"
            if action.kind == "edit":
                timer = find_timer(listing.timers, payload["identity"])
                if timer.fingerprint != payload["fingerprint"]:
                    raise HTTPException(409, "Der Timer wurde verändert. Timerliste neu öffnen.")
                method = "timerchange"
                params.update(
                    channelOld=timer.reference,
                    beginOld=str(timer.begin),
                    endOld=str(timer.end),
                    deleteOldOnSave="1",
                )
            else:
                if any(
                    service_key(t.reference) == service_key(params["sRef"])
                    and t.begin == int(params["begin"])
                    and t.end == int(params["end"])
                    for t in listing.timers
                ):
                    raise HTTPException(
                        409, "Ein Timer mit diesem Sender und Zeitraum existiert bereits."
                    )
                if payload.get("event"):
                    event = payload["event"]
                    if not any(
                        e.id == event["id"] and e.begin == event["begin"] and e.end > now()
                        for e in client.epg(event["reference"])
                    ):
                        raise HTTPException(409, "Die EPG-Sendung wurde geändert. EPG neu öffnen.")
            outcome = "unknown"
            actions.verify_authority(request, action, receiver)
            if action.kind == "edit":
                require_manage(request, receiver, timer, timer=True)
                params["tags"] = readable_tags(request, receiver, timer)
            else:
                params["tags"] = create_marker(request)
            result = client.write_timer(method, params, xml=listing.xml)
            outcome = "success" if result.success else "rejected"
            if result.success:
                return redirect("/timer?done=" + ("added" if action.kind == "add" else "changed"))
            message = (
                "Ein Timerkonflikt verhindert das Speichern."
                if result.conflict
                else "Der Receiver hat den Timerauftrag abgelehnt."
            )
            if action.kind == "add":
                return form_page(
                    request,
                    receiver,
                    payload,
                    issue(request, receiver, "add", payload),
                    values=values,
                    error=message,
                    status=409,
                    conflicts=result.conflicts,
                )
            return result_page(
                request,
                receiver,
                "Bitte die Timerliste prüfen und den Timer erneut öffnen. "
                "Auch bei einer Konfliktmeldung kann der Receiver bereits "
                "Timerdaten geändert haben.",
                error=message,
                conflicts=result.conflicts,
            )
        except TimerOutcomeUnknown:
            return result_page(
                request,
                receiver,
                "Der Ausgang ist unklar. Bitte vor erneutem Speichern die Timerliste prüfen. "
                "Der Auftrag wurde nicht automatisch wiederholt.",
                error="Keine eindeutige Bestätigung vom Receiver.",
                status=502,
            )
        except ReceiverError as exc:
            return result_page(
                request, receiver, "Bitte die Timerliste neu öffnen.", error=str(exc), status=502
            )
        finally:
            finish(request, action, receiver, outcome)

    @app.post("/timer/save")
    async def timer_save(request: Request):
        form = await request.form()
        return await run_in_threadpool(save, request, form)

    def remove(request, form):
        check_csrf(request, form)
        if form.get("confirmed") != "true":
            raise HTTPException(400, "Bitte den Löschen-Button zweimal drücken.")
        raw = str(form.get("action_token", ""))
        action, receiver, payload = claim(request, raw, {"delete"})
        outcome = "not_sent"
        try:
            client = client_for(receiver)
            listing = client.timer_list()
            timer = find_timer(listing.timers, payload["identity"])
            if timer.fingerprint != payload["fingerprint"]:
                raise HTTPException(
                    409, "Der Timer wurde inzwischen geändert. Timerliste neu öffnen."
                )
            if timer.state == 2 and not payload["running"]:
                raise HTTPException(
                    409,
                    "Der Timer läuft inzwischen. Bitte das Löschen in der "
                    "aktualisierten Liste erneut bestätigen.",
                )
            outcome = "unknown"
            actions.verify_authority(request, action, receiver)
            require_manage(request, receiver, timer, timer=True)
            result = client.write_timer(
                "timerdelete",
                {
                    "sRef": timer.reference,
                    "begin": str(timer.begin),
                    "end": str(timer.end),
                },
                xml=listing.xml,
            )
            outcome = "success" if result.success else "rejected"
            if result.success:
                return redirect("/timer?done=deleted")
            return timer_page(
                request, action_error="Der Receiver hat das Löschen abgelehnt.", status=409
            )
        except TimerOutcomeUnknown:
            return timer_page(
                request,
                action_error="Der Ausgang des Löschauftrags ist unklar. "
                "Bitte die Timerliste prüfen. Der Auftrag wurde nicht wiederholt.",
                status=502,
            )
        except ReceiverError as exc:
            return timer_page(request, action_error=str(exc), status=502)
        finally:
            finish(request, action, receiver, outcome)

    @app.post("/timer/delete")
    async def timer_remove(request: Request):
        form = await request.form()
        return await run_in_threadpool(remove, request, form)
