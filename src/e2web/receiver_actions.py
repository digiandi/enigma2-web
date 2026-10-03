from __future__ import annotations

import hashlib
import json
import secrets

from fastapi import HTTPException
from sqlalchemy import delete, select, text, update

from e2web.db import TimerAction, User, WebSession
from e2web.security import audit, cipher, now, token_hash


class ReceiverActions:
    """Single-use forms and one shared write lease per receiver, across both feature areas."""

    def __init__(self, config, selected_receiver):
        self.config = config
        self.selected_receiver = selected_receiver

    @staticmethod
    def connection_fingerprint(receiver):
        values = (
            receiver.hostname,
            receiver.port,
            receiver.https,
            receiver.verify_tls,
            receiver.username,
            receiver.encrypted_password,
        )
        return hashlib.sha256(repr(values).encode()).hexdigest()

    def issue_many(self, request, receiver, domain, entries):
        db = request.state.db
        db.execute(
            delete(TimerAction).where(
                TimerAction.created_at < now() - 86400,
                (TimerAction.lock_until.is_(None)) | (TimerAction.lock_until < now()),
            )
        )
        tokens = []
        crypt = cipher(self.config)
        for kind, payload in entries:
            encoded = json.dumps(
                {**payload, "domain": domain, "connection": self.connection_fingerprint(receiver)},
                sort_keys=True,
            )
            if kind == "delete":
                previous = db.scalar(
                    select(TimerAction)
                    .where(
                        TimerAction.session_hash == request.state.web_session.token_hash,
                        TimerAction.receiver_id == receiver.id,
                        TimerAction.kind == kind,
                        TimerAction.payload == encoded,
                        TimerAction.used_at.is_(None),
                        TimerAction.created_at > now() - 900,
                        TimerAction.encrypted_token.is_not(None),
                    )
                    .order_by(TimerAction.created_at.desc())
                    .limit(1)
                )
                if previous:
                    tokens.append(crypt.decrypt(previous.encrypted_token.encode()).decode())
                    continue
            raw = secrets.token_urlsafe(32)
            db.add(
                TimerAction(
                    token_hash=token_hash(raw),
                    encrypted_token=crypt.encrypt(raw.encode()).decode(),
                    session_hash=request.state.web_session.token_hash,
                    receiver_id=receiver.id,
                    kind=kind,
                    created_at=now(),
                    payload=encoded,
                )
            )
            tokens.append(raw)
        db.commit()
        return tokens

    def issue(self, request, receiver, domain, kind, payload):
        return self.issue_many(request, receiver, domain, [(kind, payload)])[0]

    def get(self, request, raw, domain, kinds):
        action = request.state.db.get(TimerAction, token_hash(raw))
        if not action or action.session_hash != token_hash(request.state.raw_token):
            raise HTTPException(403, "Dieser Auftrag gehört nicht zu dieser Sitzung.")
        if (
            action.kind not in kinds
            or action.created_at < now() - 7200
            or action.used_at
            or json.loads(action.payload).get("domain") != domain
        ):
            raise HTTPException(
                409, "Dieser Auftrag ist veraltet oder bereits verwendet. Liste neu laden."
            )
        return action

    def claim(self, request, raw, domain, kinds):
        db = request.state.db
        db.commit()
        db.execute(text("BEGIN IMMEDIATE"))
        db.expire_all()
        session = db.get(WebSession, token_hash(request.state.raw_token))
        user = db.get(User, session.user_id) if session else None
        if not session or session.expires_at <= now() or not user or not user.active:
            request.state.user, request.state.web_session = None, None
            raise HTTPException(403, "Die Sitzung ist nicht mehr gültig. Bitte erneut anmelden.")
        if user.must_change_password:
            raise HTTPException(403, "Bitte zuerst das Passwort ändern.")
        request.state.web_session, request.state.user = session, user
        request.state.action_actor_id = user.id
        action = self.get(request, raw, domain, kinds)
        receiver = self.selected_receiver(request)
        payload = json.loads(action.payload)
        if not receiver or receiver.id != action.receiver_id:
            raise HTTPException(
                409, "Der Receiver oder die Berechtigung wurde geändert. Liste neu laden."
            )
        if not request.app.state.can_write_receiver(request, receiver):
            raise HTTPException(403, "Für diesen Receiver sind nur Leserechte vergeben.")
        if payload["connection"] != self.connection_fingerprint(receiver):
            raise HTTPException(409, "Die Receiver-Konfiguration wurde geändert. Liste neu laden.")
        db.execute(
            update(TimerAction)
            .where(TimerAction.lock_until < now())
            .values(
                locked_receiver_id=None,
                lock_until=None,
            )
        )
        if db.scalar(
            select(TimerAction.token_hash).where(TimerAction.locked_receiver_id == receiver.id)
        ):
            raise HTTPException(
                409, "Ein Auftrag für diesen Receiver läuft bereits. Bitte kurz warten."
            )
        action.used_at = now()
        action.locked_receiver_id = receiver.id
        budget = self.config.receiver_timeout * 7
        if domain == "recording":
            budget = max(
                budget, self.config.recording_timeout * 2 + self.config.receiver_timeout * 5
            )
        action.lock_until = now() + int(budget) + 30
        db.commit()
        return action, receiver, payload

    def verify_authority(self, request, action, receiver):
        # Preflight reads can wake a sleeping HDD. Account edits during that wait
        # must take effect before a write is sent to the receiver.
        receiver_id = receiver.id
        fingerprint = self.connection_fingerprint(receiver)
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
        current = self.selected_receiver(request)
        if (
            not current
            or current.id != receiver_id
            or self.connection_fingerprint(current) != fingerprint
        ):
            raise HTTPException(409, "Receiver oder Berechtigung geändert. Liste neu laden.")
        if not request.app.state.can_write_receiver(request, current):
            raise HTTPException(403, "Für diesen Receiver sind nur Leserechte vergeben.")
        if (
            action.locked_receiver_id != receiver_id
            or not action.lock_until
            or action.lock_until <= now()
        ):
            raise HTTPException(409, "Der Auftrag ist abgelaufen. Liste neu laden.")
        db.commit()

    @staticmethod
    def finish(request, action, receiver, domain, outcome):
        db = request.state.db
        db.execute(
            update(TimerAction)
            .where(TimerAction.token_hash == action.token_hash)
            .values(
                locked_receiver_id=None,
                lock_until=None,
            )
        )
        actor = db.get(User, request.state.action_actor_id)
        audit(db, actor, f"{domain}.{action.kind}.{outcome}", receiver.id)
        db.commit()
