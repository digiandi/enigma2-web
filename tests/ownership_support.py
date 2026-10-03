"""Explicitly seed provenance for legacy regression fixtures that represent own data."""

import secrets

from sqlalchemy.orm import Session

from e2web.db import Ownership, Receiver
from e2web.ownership import device_fingerprint
from e2web.security import now
from e2web.timers import service_key


def owned_rows(app, rows, *, user_id=2, receiver_id=1):
    with Session(app.state.engine) as db:
        receiver = db.get(Receiver, receiver_id)
        for row in rows:
            marker = "e2web-owner-" + secrets.token_hex(24)
            row["tags"] = (row.get("tags", "") + " " + marker).strip()
            db.add(
                Ownership(
                    marker=marker,
                    owner_id=user_id,
                    receiver_id=receiver_id,
                    connection=device_fingerprint(receiver),
                    service=service_key(row["serviceref"]),
                    created_at=now(),
                )
            )
        db.commit()
