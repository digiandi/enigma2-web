from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

import uvicorn
from cryptography.fernet import Fernet
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from e2web.config import config_path, load_config
from e2web.db import User, make_engine, migrate
from e2web.ownership import ensure_owner_tag
from e2web.security import audit, passwords, text_field, username, validate_password


def initialize(path: Path) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as destination:
            destination.write(
                'data_dir = "data"\nhost = "127.0.0.1"\nport = 8081\n'
                "session_hours = 12\ncookie_secure = false\n"
                'receiver_timeout = 8.0\nrecording_timeout = 90.0\ntimezone = "Europe/Berlin"\n'
            )
    config = load_config(path)
    config.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not config.key_path.exists():
        # Never regenerate a key for an existing database with stored credentials.
        if config.database_path.exists():
            raise ValueError(
                "Datenbank vorhanden, aber Schlüssel fehlt. Originalschlüssel "
                "aus der Sicherung wiederherstellen."
            )
        fd = os.open(config.key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as destination:
            destination.write(Fernet.generate_key())
    Fernet(config.key_path.read_bytes().strip())
    migrate(config)
    os.chmod(config.database_path, 0o600)


def main():
    parser = argparse.ArgumentParser(prog="e2web")
    parser.add_argument("--config", type=Path, default=config_path())
    parser.add_argument("command", choices=["init", "migrate", "create-admin", "serve"])
    args = parser.parse_args()
    os.environ["E2WEB_CONFIG"] = str(args.config.resolve())
    try:
        if args.command == "init":
            initialize(args.config.resolve())
            print("Konfiguration, Schlüssel und Datenbank sind vorbereitet.")
            return
        config = load_config(args.config)
        if args.command == "migrate":
            migrate(config)
            print("Datenbank ist aktuell.")
        elif args.command == "create-admin":
            name = username(input("Benutzername: "))
            display = text_field(input("Anzeigename: "), "Anzeigename")
            password = getpass.getpass("Passwort: ")
            validate_password(password, getpass.getpass("Passwort wiederholen: "))
            engine = make_engine(config)
            try:
                with Session(engine) as db:
                    db.execute(text("BEGIN IMMEDIATE"))
                    if db.scalar(select(User.id).where(User.username == name)):
                        raise ValueError("Dieser Benutzername ist bereits vergeben.")
                    user = User(
                        username=name,
                        display_name=display,
                        password_hash=passwords.hash(password),
                        role="admin",
                        active=True,
                        all_receivers=True,
                        must_change_password=False,
                    )
                    db.add(user)
                    db.flush()
                    ensure_owner_tag(db, user)
                    audit(db, user, "user.created", user.id)
                    db.commit()
            finally:
                engine.dispose()
            print("Administrator angelegt.")
        else:
            uvicorn.run(
                "e2web.main:create_app",
                factory=True,
                host=config.host,
                port=config.port,
                proxy_headers=True,
                forwarded_allow_ips="127.0.0.1,::1",
            )
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Fehler: {exc}\n")
