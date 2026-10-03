from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from copy import copy
from dataclasses import dataclass, field
from threading import Event, Lock
from time import monotonic
from types import SimpleNamespace

from e2web.openwebif import ReceiverError
from e2web.receiver_actions import ReceiverActions
from e2web.timer_selection import recordable_service, service_flags


def channel_key(reference):
    parts = reference.split(":", 10)
    path = parts[10] if len(parts) == 11 else ""
    if path.startswith(":"):
        path = ""  # Optional DVB display names are not part of a channel's identity.
    return ":".join(part.upper() for part in parts[:10]) + ":" + path


def reference_medium(reference):
    try:
        parts = reference.split(":")
        if parts[0] != "1" or not recordable_service(reference):
            return ""
        kind = int(parts[2], 16)
        if kind in (2, 10):
            return "Radio"
        if kind in (1, 4, 5, 17, 22, 25, 27, 31, 32, 33):
            return "TV"
    except (IndexError, ValueError):
        pass
    return ""


@dataclass
class ChannelDetails:
    by_reference: dict = field(default_factory=dict)
    by_name: dict = field(default_factory=dict)

    def describe(self, reference="", channel=""):
        memberships = self.by_reference.get(channel_key(reference), []) if reference else []
        if not reference:
            keys = self.by_name.get(channel.strip().casefold(), set())
            if len(keys) == 1:
                memberships = self.by_reference[next(iter(keys))]
        media = list(dict.fromkeys(medium for medium, _ in memberships))
        bouquets = list(dict.fromkeys(name for _, name in memberships if name))
        return {
            "medium": " / ".join(media) or reference_medium(reference) or "TV/Radio unbekannt",
            "bouquet": " · ".join(bouquets) or "Bouquet unbekannt",
        }


def read_channel_details(client, *, stopped=None):
    details = ChannelDetails()
    failed = False
    for medium, label in (("tv", "TV"), ("radio", "Radio")):
        if stopped and stopped.is_set():
            break
        try:
            groups = client.bouquets(medium)
            for group in groups:
                if stopped and stopped.is_set():
                    return details, failed
                flags = service_flags(group["reference"])
                if flags is None or not flags & 7 or flags & (64 | 128):
                    continue
                for row in client.services(group["reference"]):
                    if not recordable_service(row["reference"]):
                        continue
                    key = channel_key(row["reference"])
                    membership = (label, group["name"])
                    members = details.by_reference.setdefault(key, [])
                    if membership not in members:
                        members.append(membership)
                    if row["name"].strip():
                        details.by_name.setdefault(row["name"].strip().casefold(), set()).add(key)
        except ReceiverError:
            failed = True
            break  # Optional labels must not cause repeated slow failing requests.
    return details, failed


class ChannelCatalog:
    """Read-only display cache. Never used to authorize a receiver action."""

    def __init__(self, *, clock=monotonic):
        self.clock = clock
        self.lock = Lock()
        self.stopped = Event()
        self.entries = OrderedDict()
        self.workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="e2web-bouquets")

    def view(self, receiver, client):
        key = receiver.id, ReceiverActions.connection_fingerprint(receiver)
        with self.lock:
            for old in list(self.entries):
                if old[0] == receiver.id and old != key:
                    del self.entries[old]
            entry = self.entries.setdefault(
                key, {"details": ChannelDetails(), "expires": 0, "loading": False}
            )
            self.entries.move_to_end(key)
            while len(self.entries) > 16:
                self.entries.popitem(last=False)
            if (
                not self.stopped.is_set()
                and not entry["loading"]
                and self.clock() >= entry["expires"]
            ):
                # Freeze loaded connection values before the request's DB session closes.
                worker_client = copy(client)
                if hasattr(client, "receiver"):
                    worker_client.receiver = SimpleNamespace(
                        base_url=receiver.base_url,
                        username=receiver.username,
                        encrypted_password=receiver.encrypted_password,
                        verify_tls=receiver.verify_tls,
                    )
                entry["loading"] = True
                self.workers.submit(self._refresh, entry, worker_client)
            return entry["details"]

    def _refresh(self, entry, client):
        try:
            details, failed = read_channel_details(client, stopped=self.stopped)
        except Exception:
            details, failed = ChannelDetails(), True
        with self.lock:
            if details.by_reference or not failed:
                entry["details"] = details
            entry["expires"] = self.clock() + (30 if failed else 300)
            entry["loading"] = False

    def close(self):
        self.stopped.set()
        self.workers.shutdown(wait=False, cancel_futures=True)


def recording_channel_details(details, recording, timers):
    matching = {
        channel_key(timer.reference): timer.reference
        for timer in timers or []
        if timer.filename
        and (
            recording.filename == timer.filename
            or recording.filename.removesuffix(".ts") == timer.filename
        )
    }
    reference = next(iter(matching.values())) if len(matching) == 1 else ""
    return details.describe(reference, recording.channel)
