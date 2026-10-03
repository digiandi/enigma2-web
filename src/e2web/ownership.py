from __future__ import annotations

import hashlib

from fastapi import HTTPException
from sqlalchemy import select

from e2web.db import Ownership, OwnerTag, User
from e2web.security import now
from e2web.timers import service_key

PREFIX = "e2web-owner-"


def device_fingerprint(receiver):
    # Credential rotation does not change who created a timer on this device.
    return hashlib.sha256(
        repr((receiver.hostname, receiver.port, receiver.https)).encode()
    ).hexdigest()


def ensure_owner_tag(db, user):
    row = db.scalar(select(OwnerTag).where(OwnerTag.owner_id == user.id))
    if row is not None:
        return row.marker
    base = PREFIX + user.username
    marker = base
    number = 2
    # Keep deleted accounts' labels reserved. A reused username or SQLite ID
    # must not inherit the recordings and rights of its previous account.
    while db.get(OwnerTag, marker) is not None:
        marker = f"{base}-konto-{number}"
        number += 1
    db.add(OwnerTag(marker=marker, owner_id=user.id, created_at=now()))
    db.flush()
    return marker


def create_marker(request):
    # The authenticated account is authoritative; form-supplied tags are ignored.
    marker = ensure_owner_tag(request.state.db, request.state.user)
    request.state.db.commit()
    return marker


def owner_id(request, receiver, item, *, timer=False):
    markers = [tag for tag in item.tags.split() if tag.startswith(PREFIX)]
    if len(markers) != 1:
        return None
    label = request.state.db.get(OwnerTag, markers[0])
    if label is not None:
        return label.owner_id
    # Pre-0.8.0 labels still require their original receiver/device/service proof.
    row = request.state.db.get(Ownership, markers[0])
    if (
        not row
        or row.receiver_id != receiver.id
        or row.connection != device_fingerprint(receiver)
        or (timer and row.service != service_key(item.reference))
    ):
        return None
    return row.owner_id


def readable_tags(request, receiver, timer):
    user_id = owner_id(request, receiver, timer, timer=True)
    user = request.state.db.get(User, user_id) if user_id is not None else None
    if user is None:
        return timer.tags
    marker = ensure_owner_tag(request.state.db, user)
    tags = [tag for tag in timer.tags.split() if not tag.startswith(PREFIX)]
    tags.append(marker)
    # Preserve the mapping if the receiver applies the write but loses its reply.
    request.state.db.commit()
    return " ".join(tags)


def owner_name(request, receiver, item, *, timer=False):
    user_id = owner_id(request, receiver, item, timer=timer)
    user = request.state.db.get(User, user_id) if user_id is not None else None
    return (user.display_name or user.username) if user else "unbekannt"


def can_manage(request, receiver, item, *, timer=False):
    if not request.app.state.can_write_receiver(request, receiver):
        return False
    return (
        request.state.user.is_admin
        or owner_id(request, receiver, item, timer=timer) == request.state.user.id
    )


def require_manage(request, receiver, item, *, timer=False):
    if not can_manage(request, receiver, item, timer=timer):
        raise HTTPException(
            403, "Nur eigene Timer und Aufnahmen können bearbeitet oder gelöscht werden."
        )
