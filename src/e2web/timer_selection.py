from __future__ import annotations

from fastapi import HTTPException

from e2web.openwebif import ReceiverError
from e2web.recordings import directory_path


def service_flags(reference):
    try:
        if len(reference) > 2048 or any(ord(c) < 32 for c in reference):
            return None
        return int(reference.split(":")[1])
    except (ValueError, IndexError):
        return None


def recordable_service(reference):
    flags = service_flags(reference)
    return flags is not None and not flags & 64 and (not flags & 7 or bool(flags & 128))


def timer_bouquets(client):
    groups = []
    for medium in ("tv", "radio"):
        for row in client.bouquets(medium):
            flags = service_flags(row["reference"])
            if flags is not None and flags & 7 and not flags & (64 | 128):
                groups.append({**row, "medium": medium})
    return groups


def bouquet_services(client, groups, group):
    if group not in {row["reference"] for row in groups}:
        raise HTTPException(409, "Das Bouquet ist nicht mehr verfügbar. Timerformular neu öffnen.")
    return [row for row in client.services(group) if recordable_service(row["reference"])]


def timer_paths(client, listing, *, preferred=""):
    paths = list(listing.locations)
    default = listing.default_location
    if listing.xml or not paths or not default:
        try:
            extra_paths, extra_default = client.recording_locations()
            paths.extend(extra_paths)
            default = default or extra_default
        except ReceiverError:
            pass
    if not default:
        try:
            default = client.current_recording_location()
        except (ReceiverError, ValueError):
            default = ""
    try:
        default = directory_path(default) if default else ""
        preferred = directory_path(preferred) if preferred else ""
        paths = [directory_path(path) for path in [default, preferred, *paths] if path]
    except ValueError:
        raise ReceiverError("Der Receiver liefert einen ungültigen Aufnahmepfad.") from None
    if not paths:
        raise ReceiverError("Der Standardaufnahmepfad konnte nicht ermittelt werden.")
    return list(dict.fromkeys(paths)), preferred or default
