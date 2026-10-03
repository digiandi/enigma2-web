from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import PurePosixPath


def duration_label(seconds: int | None) -> str:
    if seconds is None or seconds < 0:
        return "Unbekannt"
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def directory_path(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value.startswith("/")
        or len(value) > 2048
        or any(ord(c) < 32 for c in value)
        or ".." in value.split("/")
    ):
        raise ValueError("Ungültiger Aufnahmepfad.")
    return str(PurePosixPath(value)).rstrip("/") + "/"


@dataclass(frozen=True)
class Recording:
    reference: str
    filename: str
    title: str
    channel: str
    description: str
    extended_description: str
    begin: int
    duration: int | None
    size: int | None
    tags: str = ""

    @property
    def fingerprint(self):
        # Changes to file size or timestamp invalidate a deletion from an old page.
        values = (self.reference, self.filename, self.title, self.begin, self.size)
        return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()

    @property
    def parent(self):
        return directory_path(str(PurePosixPath(self.filename).parent))

    @property
    def size_label(self):
        if self.size is None:
            return "Unbekannt"
        size = float(max(0, self.size))
        for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
            if size < 1024 or unit == "TiB":
                return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TiB"


@dataclass(frozen=True)
class RecordingList:
    recordings: list[Recording]
    directory: str
    folders: list[str]
    xml: bool


def recording_running(recording, timers, *, protect_unknown=True):
    for timer in timers:
        if timer.state != 2 or timer.justplay:
            continue
        if not timer.filename:
            if protect_unknown:
                return True  # An unidentified running file must not be removed.
            continue
        if (
            recording.filename == timer.filename
            or recording.filename.removesuffix(".ts") == timer.filename
        ):
            return True
    return False
