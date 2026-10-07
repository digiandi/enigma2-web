from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class Config:
    data_dir: Path
    host: str = "0.0.0.0"
    port: int = 8081
    session_hours: int = 12
    cookie_secure: bool = False
    receiver_timeout: float = 8.0
    recording_timeout: float = 90.0
    timezone: str = "Europe/Berlin"

    @property
    def database_path(self) -> Path:
        return self.data_dir / "e2web.db"

    @property
    def key_path(self) -> Path:
        return self.data_dir / "receiver.key"


def config_path() -> Path:
    return Path(os.environ.get("E2WEB_CONFIG", "e2web.toml")).resolve()


def load_config(path: Path | None = None) -> Config:
    path = (path or config_path()).resolve()
    with path.open("rb") as source:
        values = tomllib.load(source)
    data_dir = Path(values.get("data_dir", "data"))
    if not data_dir.is_absolute():
        data_dir = path.parent / data_dir
    config = Config(
        data_dir=data_dir.resolve(),
        host=str(values.get("host", "0.0.0.0")),
        port=int(values.get("port", 8081)),
        session_hours=int(values.get("session_hours", 12)),
        cookie_secure=bool(values.get("cookie_secure", False)),
        receiver_timeout=float(values.get("receiver_timeout", 8.0)),
        recording_timeout=float(values.get("recording_timeout", 90.0)),
        timezone=str(values.get("timezone", "Europe/Berlin")),
    )
    if not 1 <= config.port <= 65535 or not 1 <= config.session_hours <= 168:
        raise ValueError("Ungültiger Port oder ungültige Sitzungsdauer.")
    if not 1 <= config.receiver_timeout <= 60:
        raise ValueError("Receiver-Timeout muss zwischen 1 und 60 Sekunden liegen.")
    if not 1 <= config.recording_timeout <= 300:
        raise ValueError("Aufnahme-Timeout muss zwischen 1 und 300 Sekunden liegen.")
    try:
        ZoneInfo(config.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("Ungültige EPG-Zeitzone.") from None
    return config
