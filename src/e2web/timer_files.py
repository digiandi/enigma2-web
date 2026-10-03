from __future__ import annotations

from pathlib import PurePosixPath

from e2web.openwebif import ReceiverError
from e2web.recordings import directory_path


def timer_files(client, timers):
    """Read running timers' file sizes, matched by exact filename, never title."""
    folders = {}
    result = {}
    failed = False
    for timer in timers:
        if timer.state != 2 or timer.justplay or not timer.filename:
            result[timer.identity_key] = None
            continue
        filename = timer.filename
        shown_name = PurePosixPath(filename).name
        if not shown_name.endswith(".ts"):
            shown_name += ".ts"
        file = {"name": shown_name, "size": "Unbekannt"}
        result[timer.identity_key] = file
        try:
            if not filename.startswith("/"):
                raise ValueError
            parent = directory_path(str(PurePosixPath(filename).parent))
        except ValueError:
            continue
        if parent not in folders:
            try:
                folders[parent] = client.recording_list(parent)
            except ReceiverError:
                folders[parent] = None
                failed = True
        listing = folders[parent]
        if listing is None:
            continue
        # The receiver may resolve a configured directory symlink in its reply.
        canonical = listing.directory or parent
        candidates = {filename, filename + ".ts", canonical + shown_name}
        parents = {recording.parent for recording in listing.recordings}
        if len(parents) == 1:
            candidates.add(next(iter(parents)) + shown_name)
        matches = [
            recording for recording in listing.recordings if recording.filename in candidates
        ]
        if len(matches) == 1:
            file["name"] = PurePosixPath(matches[0].filename).name
            file["size"] = matches[0].size_label
    return result, failed
