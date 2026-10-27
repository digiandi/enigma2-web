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
def test_recording_end_follows_its_duration_while_timer_keeps_its_planned_end(
    setup, xml, filename_suffix, state
):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    box.movies = [movie_row(recordingtime=START, length="15:00")]
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
        assert cells["Ende"] == "25.10.2026 00:05"
        assert cells["Dauer"] == "00:15:00"
        assert 'colspan="8"' in page.text
        assert "<th>Beginn</th>" not in page.text
        assert ("Läuft" if state == 2 else "Abgeschlossen") in cells["Status"]
        assert "<th>Start</th><th>Ende</th><th>Dauer</th>" in page.text
        timer_page = client.get("/timer")
        assert timer_page.status_code == 200
        assert 'data-label="Ende">25.10.2026 00:45</td>' in timer_page.text

        box.timers[0]["end"] += 1800
        refreshed = client.get(
            "/aufnahmen",
            params={"live_receiver": "1"},
            headers={"X-Live-Refresh": "1"},
        )
        assert refreshed.status_code == 200
        assert recording_cells(refreshed)["Ende"] == "25.10.2026 00:05"
        box.movies[0]["length"] = "45:00"
        refreshed = client.get(
            "/aufnahmen",
            params={"live_receiver": "1"},
            headers={"X-Live-Refresh": "1"},
        )
        assert refreshed.status_code == 200
        assert recording_cells(refreshed)["Ende"] == "25.10.2026 00:35"
        assert recording_cells(refreshed)["Dauer"] == "00:45:00"
        timer_page = client.get("/timer")
        assert timer_page.status_code == 200
        assert 'data-label="Ende">25.10.2026 01:15</td>' in timer_page.text
        assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
@pytest.mark.parametrize(
    "situation", ["missing", "other_path", "missing_filename", "ambiguous", "justplay", "offline"]
)
def test_recording_end_is_independent_of_timer_availability_and_matching(setup, xml, situation):
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
        assert cells["Ende"] == "24.10.2026 23:55"
        assert cells["Start"] == "24.10.2026 23:50"
        assert cells["Dauer"] == "00:05:00"
        assert "Herunterladen" in page.text
        assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
def test_recording_end_requires_usable_metadata_even_when_matching_timer_exists(setup, xml):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    box.timers = [timer_row(state=2, filename=FILENAME, begin=START, end=END)]
    cases = [
        ({"length": "?:??"}, "24.10.2026 23:50", "Unbekannt"),
        ({"length": None}, "24.10.2026 23:50", "Unbekannt"),
        ({"length": ""}, "24.10.2026 23:50", "Unbekannt"),
        ({"length": "invalid"}, "24.10.2026 23:50", "Unbekannt"),
        ({"length": "-1:00"}, "24.10.2026 23:50", "Unbekannt"),
        ({"recordingtime": -1}, "Unbekannt", "00:05:00"),
        ({"recordingtime": 0}, "Unbekannt", "00:05:00"),
        ({"recordingtime": ""}, "Unbekannt", "00:05:00"),
        ({"recordingtime": None}, "Unbekannt", "00:05:00"),
        ({"length": "9999999999999999999999:00"}, "24.10.2026 23:50", None),
    ]
    with TestClient(app) as client:
        login(client, "user", "User-123")
        for changes, start, duration in cases:
            box.movies = [movie_row(recordingtime=START, length="05:00") | changes]
            page = client.get("/aufnahmen")
            assert page.status_code == 200, changes
            cells = recording_cells(page)
            assert cells["Ende"] == "Unbekannt", changes
            assert cells["Start"] == start, changes
            if duration is not None:
                assert cells["Dauer"] == duration, changes
            assert "Herunterladen" in page.text
        assert not box.writes


@pytest.mark.parametrize("xml", [False, True])
def test_recording_end_uses_elapsed_seconds_across_clock_changes_and_accepts_zero_duration(
    setup, xml
):
    _, _, app = setup
    box = install_movie_mock(app, xml=xml)
    box.timers = []
    berlin = ZoneInfo("Europe/Berlin")
    cases = [
        (datetime(2026, 10, 24, 23, 50, tzinfo=berlin), "00:00", "24.10.2026 23:50"),
        (datetime(2026, 10, 24, 23, 50, tzinfo=berlin), "01:15:30", "25.10.2026 01:05"),
        (datetime(2026, 3, 29, 1, 50, tzinfo=berlin), "20:00", "29.03.2026 03:10"),
        (datetime(2026, 10, 25, 2, 50, tzinfo=berlin), "20:00", "25.10.2026 02:10"),
        (datetime(2026, 10, 25, 2, 50, fold=1, tzinfo=berlin), "20:00", "25.10.2026 03:10"),
    ]
    with TestClient(app) as client:
        login(client, "user", "User-123")
        for start, duration, end in cases:
            box.movies = [movie_row(recordingtime=int(start.timestamp()), length=duration)]
            page = client.get("/aufnahmen")
            assert page.status_code == 200
            assert recording_cells(page)["Ende"] == end, (start, duration)
        assert not box.writes
