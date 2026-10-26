import re
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from test_foundation import login
from test_foundation import setup as setup
from test_recordings import FILENAME, install_movie_mock, movie_row
from test_timers import timer_row

START = int(datetime(2026, 10, 24, 23, 50, tzinfo=ZoneInfo("Europe/Berlin")).timestamp())
END = START + 55 * 60


def recording_cells(page):
    row = re.search(r'<tr class="recording-data-row\b.*?</tr>', page.text, re.S)[0]
    return dict(re.findall(r'<td[^>]*data-label="([^"]+)"[^>]*>(.*?)</td>', row, re.S))


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize("filename_suffix", ["", ".ts"])
@pytest.mark.parametrize("state", [2, 3])
def test_recording_shows_planned_timer_end_and_refreshes_after_extension(
    setup, xml, filename_suffix, state
):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    box.movies = [movie_row(recordingtime=START, length="05:00")]
    box.timers = [
        timer_row(
            state=state,
            filename=FILENAME.removesuffix(".ts") + filename_suffix,
            begin=START - 60,
            end=END,
        )
    ]
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200
        cells = recording_cells(page)
        assert list(cells) == ["Aufnahme", "Sender", "Receiver", "Start", "Ende", "Dauer", "Status"]
        assert cells["Start"] == "24.10.2026 23:50"
        assert cells["Ende"] == "25.10.2026 00:45"
        assert cells["Dauer"] == "00:05:00"
        assert 'colspan="8"' in page.text
        assert "<th>Beginn</th>" not in page.text
        assert ("Läuft" if state == 2 else "Abgeschlossen") in cells["Status"]
        assert "<th>Start</th><th>Ende</th><th>Dauer</th>" in page.text

        box.timers[0]["end"] += 1800
        refreshed = client.get(
            "/aufnahmen",
            params={"live_receiver": "1"},
            headers={"X-Live-Refresh": "1"},
        )
        assert refreshed.status_code == 200
        assert recording_cells(refreshed)["Ende"] == "25.10.2026 01:15"
        assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize(
    "situation", ["missing", "other_path", "missing_filename", "ambiguous", "justplay", "offline"]
)
def test_recording_without_unique_available_recording_timer_has_unknown_end(setup, xml, situation):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    box.movies = [movie_row(recordingtime=START, length="05:00")]
    row = timer_row(state=2, filename=FILENAME, begin=START, end=END)
    box.timers = [row]
    if situation == "missing":
        box.timers = []
    elif situation == "other_path":
        row["filename"] = FILENAME.replace("/movie/", "/movie/Andere/")
    elif situation == "missing_filename":
        row.pop("filename")
    elif situation == "ambiguous":
        box.timers.append({**row, "end": END + 1800})
    elif situation == "justplay":
        row["justplay"] = 1
    else:
        box.status_unavailable = True
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/aufnahmen")
        assert page.status_code == 200
        cells = recording_cells(page)
        assert cells["Ende"] == "Unbekannt"
        assert cells["Start"] == "24.10.2026 23:50"
        assert cells["Dauer"] == "00:05:00"
        assert "Herunterladen" in page.text
        assert not box.writes
