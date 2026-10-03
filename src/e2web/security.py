from __future__ import annotations

import hashlib
import hmac
import ipaddress
import re
import secrets
import time

from cryptography.fernet import Fernet
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError
from sqlalchemy import delete, func, select

from e2web.db import AuditLog, LoginAttempt, User, WebSession

passwords = PasswordHash.recommended()
dummy_hash = passwords.hash(secrets.token_urlsafe(32))


def now() -> int:
    return int(time.time())


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def csrf(token: str) -> str:
    return hmac.new(token.encode(), b"e2web-csrf-v1", hashlib.sha256).hexdigest()


def matches(a: str | None, b: str | None) -> bool:
    return bool(a and b and hmac.compare_digest(a.encode(), b.encode()))


def verify_password(password: str, encoded: str | None) -> bool:
    try:
        return passwords.verify(password, encoded or dummy_hash)
    except (PwdlibError, ValueError, TypeError):
        return False


def validate_password(password: str, confirmation: str) -> None:
    if password != confirmation:
        raise ValueError("Die beiden Passwörter stimmen nicht überein.")
    if not 1 <= len(password) <= 128:
        raise ValueError("Das Passwort muss 1 bis 128 Zeichen lang sein.")


def username(value: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9._-]{2,31}", value):
        raise ValueError(
            "Benutzername: 3–32 Zeichen, beginnend mit einem Buchstaben; "
            "erlaubt sind a–z, 0–9, Punkt, _ und -."
        )
    return value


def text_field(value: str, label: str, maximum: int = 128) -> str:
    value = value.strip()
    if not 1 <= len(value) <= maximum:
        raise ValueError(f"{label} muss 1 bis {maximum} Zeichen lang sein.")
    return value


def hostname(value: str) -> str:
    value = value.strip().strip("[]")
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        pass
    try:
        value = value.encode("idna").decode("ascii").lower()
    except UnicodeError:
        raise ValueError("Ungültiger Hostname.") from None
    if len(value) > 253 or not all(
        re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", part)
        for part in value.rstrip(".").split(".")
    ):
        raise ValueError("Bitte nur eine IP-Adresse oder einen Hostnamen ohne URL/Pfad eingeben.")
    return value.rstrip(".")


def audit(db, actor: User | None, action: str, target_id: int | None = None) -> None:
    db.add(
        AuditLog(
            actor_id=actor.id if actor else None,
            action=action,
            target_id=target_id,
            created_at=now(),
        )
    )


def login_limited(db, name: str, ip: str) -> bool:
    cutoff = now() - 900
    db.execute(delete(LoginAttempt).where(LoginAttempt.attempted_at < cutoff))
    account_count = db.scalar(
        select(func.count()).select_from(LoginAttempt).where(LoginAttempt.username == name)
    )
    ip_count = db.scalar(
        select(func.count()).select_from(LoginAttempt).where(LoginAttempt.ip_address == ip)
    )
    return account_count >= 10 or ip_count >= 30


def revoke(db, user_id: int) -> None:
    db.execute(delete(WebSession).where(WebSession.user_id == user_id))


def clear_failures(db, name: str, ip: str) -> None:
    db.execute(
        delete(LoginAttempt).where(
            (LoginAttempt.username == name) & (LoginAttempt.ip_address == ip)
        )
    )


def active_admins(db) -> int:
    return db.scalar(
        select(func.count()).select_from(User).where(User.active.is_(True), User.role == "admin")
    )


def cipher(config) -> Fernet:
    return Fernet(config.key_path.read_bytes().strip())
