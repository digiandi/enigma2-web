from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime

WEEKDAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")


def service_key(reference: str) -> str:
    # Enigma2 identifies timers by the first eleven reference components and both times.
    return ":".join(reference.split(":")[:11])


@dataclass(frozen=True)
class Timer:
    reference: str
    channel: str
    name: str
    description: str
    begin: int
    end: int
    disabled: int
    repeated: int
    justplay: int
    afterevent: int
    directory: str
    tags: str
    eit: int
    state: int
    cancelled: bool
    extras: dict[str, str] = field(default_factory=dict)
    filename: str = ""

    @property
    def identity(self):
        return {"reference": self.reference, "begin": self.begin, "end": self.end}

    @property
    def identity_key(self):
        return service_key(self.reference), self.begin, self.end

    @property
    def settings(self):
        return {
            "sRef": self.reference,
            "name": self.name,
            "description": self.description,
            "begin": str(self.begin),
            "end": str(self.end),
            "disabled": str(self.disabled),
            "repeated": str(self.repeated),
            "justplay": str(self.justplay),
            "afterevent": str(self.afterevent),
            "dirname": self.directory,
            "tags": self.tags,
            "eit": str(self.eit),
            **self.extras,
        }

    @property
    def fingerprint(self):
        data = json.dumps(self.settings, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(data.encode()).hexdigest()

    @property
    def repeat_label(self):
        if self.repeated == 127:
            return "Täglich"
        if self.repeated == 31:
            return "Montag–Freitag"
        return ", ".join(day[:2] for n, day in enumerate(WEEKDAYS) if self.repeated & (1 << n))

    @property
    def status(self):
        if self.disabled:
            return "Deaktiviert"
        if self.cancelled:
            return "Abgebrochen"
        return {0: "Geplant", 1: "Wird vorbereitet", 2: "Läuft", 3: "Erledigt"}.get(
            self.state, "Unbekannt"
        )


@dataclass(frozen=True)
class TimerList:
    timers: list[Timer]
    locations: list[str]
    default_location: str
    xml: bool


@dataclass(frozen=True)
class TimerResult:
    success: bool
    conflict: bool
    conflicts: list[dict]


def local_timestamp(value, timezone, *, fold="", original=None):
    try:
        local = datetime.fromisoformat(str(value))
    except ValueError:
        raise ValueError("Bitte Datum und Uhrzeit vollständig eingeben.") from None
    if local.tzinfo is not None or not 1970 <= local.year <= 2099:
        raise ValueError("Bitte eine lokale Uhrzeit zwischen 1970 und 2099 eingeben.")
    candidates = sorted(
        {
            int(local.replace(tzinfo=timezone, fold=n).timestamp())
            for n in (0, 1)
            if datetime.fromtimestamp(
                local.replace(tzinfo=timezone, fold=n).timestamp(), timezone
            ).replace(tzinfo=None)
            == local
        }
    )
    if not candidates:
        raise ValueError("Diese Uhrzeit existiert wegen der Zeitumstellung nicht.")
    if len(candidates) == 1:
        return candidates[0]
    if original in candidates and fold == "":
        return original
    if fold in {"0", "1"}:
        return candidates[int(fold)]
    raise ValueError(
        "Diese Uhrzeit kommt bei der Zeitumstellung zweimal vor. "
        "Bitte das erste oder zweite Vorkommen wählen."
    )
