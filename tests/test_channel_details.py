import re
import threading
import time
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from test_foundation import login
from test_foundation import setup as setup
from test_recordings import FILENAME, movie_row
from test_timer_layout import RADIO, RADIO_GROUP, SECOND, TV_SECOND, install_selector
from test_timers import GROUP, REFERENCE, timer_row

from e2web.channel_details import (
    ChannelCatalog,
    channel_key,
    read_channel_details,
    recording_channel_details,
)
from e2web.db import Receiver
from e2web.openwebif import ReceiverError


class CatalogReceiver:
    def __init__(self):
        self.calls = []
        self.groups = {
            "tv": [
                {"reference": GROUP, "name": "Fernsehen"},
                {"reference": TV_SECOND, "name": "Weitere TV-Sender"},
                {"reference": "1:64:1:0:0:0:0:0:0:0:", "name": "Marker"},
            ],
            "radio": [{"reference": RADIO_GROUP, "name": "Hörfunk"}],
        }
        self.rows = {
            GROUP: [
                {"reference": REFERENCE, "name": "Das Erste HD"},
                {"reference": SECOND, "name": "ZDF HD"},
                {"reference": "1:64:1:0:0:0:0:0:0:0:", "name": "Marker"},
            ],
            TV_SECOND: [{"reference": SECOND.lower(), "name": "ZDF HD"}],
            RADIO_GROUP: [{"reference": RADIO, "name": "Deutschlandfunk"}],
        }

    def bouquets(self, medium):
        self.calls.append(("bouquets", medium))
        return self.groups[medium]

    def services(self, group):
        self.calls.append(("services", group))
        return self.rows[group]


def receiver_identity(**changes):
    return SimpleNamespace(
        id=1,
        hostname="receiver.test",
        port=80,
        https=False,
        verify_tls=True,
        username="",
        encrypted_password="",
        base_url="http://receiver.test",
        **changes,
    )


def wait_for(predicate):
    deadline = time.monotonic() + 3
    while not predicate():
        if time.monotonic() >= deadline:
            pytest.fail("Background bouquet lookup did not finish")
        time.sleep(0.01)


def test_channel_labels_use_tv_radio_membership_and_all_bouquets_in_receiver_order():
    client = CatalogReceiver()
    details, failed = read_channel_details(client)
    assert not failed
    assert details.describe(REFERENCE) == {"medium": "TV", "bouquet": "Fernsehen"}
    assert details.describe(SECOND.lower() + ":ZDF HD") == {
        "medium": "TV",
        "bouquet": "Fernsehen · Weitere TV-Sender",
    }
    assert details.describe(RADIO) == {"medium": "Radio", "bouquet": "Hörfunk"}
    assert details.describe(channel=" deutschlandfunk ") == details.describe(RADIO)
    assert details.describe(channel="Marker")["bouquet"] == "Bouquet unbekannt"
    assert not any(group == "1:64:1:0:0:0:0:0:0:0:" for _, group in client.calls)


def test_ambiguous_recording_names_do_not_claim_a_bouquet_or_medium():
    client = CatalogReceiver()
    client.rows[RADIO_GROUP][0]["name"] = "Das Erste HD"
    details, _ = read_channel_details(client)
    assert details.describe(channel="Das Erste HD") == {
        "medium": "TV/Radio unbekannt",
        "bouquet": "Bouquet unbekannt",
    }
    assert details.describe(REFERENCE, "Das Erste HD")["bouquet"] == "Fernsehen"
    assert details.describe("1:0:19:FFFF:3FB:1:C00000:0:0:0:", "Das Erste HD") == {
        "medium": "TV",
        "bouquet": "Bouquet unbekannt",
    }


def test_iptv_identity_preserves_url_case_and_distinguishes_streams():
    prefix = "4097:0:0:0:0:0:0:0:0:0:"
    assert channel_key(prefix + "http%3a//host/TV") != channel_key(prefix + "http%3a//host/tv")
    client = CatalogReceiver()
    client.rows[RADIO_GROUP] = [{"reference": prefix + "http%3a//host/Radio", "name": "Radio"}]
    details, _ = read_channel_details(client)
    assert details.describe(prefix + "http%3a//host/Radio") == {
        "medium": "Radio",
        "bouquet": "Hörfunk",
    }


def test_missing_catalog_keeps_verified_labels_and_unknown_values_explicit():
    client = CatalogReceiver()
    original = client.bouquets

    def fail_radio(medium):
        if medium == "radio":
            raise ReceiverError("Nicht erreichbar")
        return original(medium)

    client.bouquets = fail_radio
    details, failed = read_channel_details(client)
    assert failed
    assert details.describe(REFERENCE)["bouquet"] == "Fernsehen"
    assert details.describe(RADIO) == {"medium": "Radio", "bouquet": "Bouquet unbekannt"}
    assert details.describe(channel="Nicht mehr in den Bouquets")["medium"] == "TV/Radio unbekannt"


def test_recording_matching_timer_file_resolves_duplicate_channel_names():
    client = CatalogReceiver()
    client.rows[GROUP][0]["name"] = "Deutschlandfunk"
    details, _ = read_channel_details(client)
    recording = SimpleNamespace(filename=FILENAME, channel="Deutschlandfunk")
    timer = SimpleNamespace(filename=FILENAME.removesuffix(".ts"), reference=RADIO)
    assert recording_channel_details(details, recording, [timer])["bouquet"] == "Hörfunk"
    assert recording_channel_details(details, recording, None)["bouquet"] == "Bouquet unbekannt"
    unrelated = SimpleNamespace(filename=FILENAME + ".other", reference=REFERENCE)
    assert (
        recording_channel_details(details, recording, [unrelated])["bouquet"] == "Bouquet unbekannt"
    )


def test_cache_does_not_repeat_catalog_for_five_second_timer_or_recording_refreshes():
    client = CatalogReceiver()
    receiver = receiver_identity()
    clock = [100.0]
    cache = ChannelCatalog(clock=lambda: clock[0])
    try:
        cache.view(receiver, client)
        wait_for(lambda: cache.view(receiver, client).describe(RADIO)["bouquet"] == "Hörfunk")
        calls = len(client.calls)
        for _ in range(10):
            clock[0] += 5
            assert cache.view(receiver, client).describe(REFERENCE)["bouquet"] == "Fernsehen"
        assert len(client.calls) == calls
        client.groups["tv"][0]["name"] = "Neuer Bouquetname"
        clock[0] += 301
        cache.view(receiver, client)
        wait_for(
            lambda: (
                cache.view(receiver, client).describe(REFERENCE)["bouquet"] == "Neuer Bouquetname"
            )
        )
    finally:
        cache.close()


def test_slow_catalog_does_not_block_a_list_or_start_duplicate_background_jobs():
    entered, release = threading.Event(), threading.Event()
    client = CatalogReceiver()
    original = client.bouquets

    def slow(medium):
        entered.set()
        assert release.wait(3)
        return original(medium)

    client.bouquets = slow
    cache = ChannelCatalog()
    receiver = receiver_identity()
    try:
        started = time.monotonic()
        assert cache.view(receiver, client).describe(REFERENCE)["medium"] == "TV"
        assert time.monotonic() - started < 1
        assert entered.wait(1)
        for _ in range(10):
            assert (
                cache.view(receiver, client).describe(REFERENCE)["bouquet"] == "Bouquet unbekannt"
            )
        release.set()
        wait_for(lambda: cache.view(receiver, client).describe(RADIO)["bouquet"] == "Hörfunk")
        assert client.calls.count(("bouquets", "tv")) == 1
    finally:
        release.set()
        cache.close()


def test_receiver_connection_change_does_not_reuse_another_receivers_labels():
    client = CatalogReceiver()
    cache = ChannelCatalog()
    receiver = receiver_identity()
    try:
        cache.view(receiver, client)
        wait_for(lambda: cache.view(receiver, client).describe(RADIO)["bouquet"] == "Hörfunk")
        other = CatalogReceiver()
        other.groups["radio"][0]["name"] = "Andere Box"
        receiver.hostname = "other-receiver.test"
        receiver.base_url = "http://other-receiver.test"
        cache.view(receiver, other)
        wait_for(lambda: cache.view(receiver, other).describe(RADIO)["bouquet"] == "Andere Box")
        assert cache.view(receiver, other).describe(RADIO)["bouquet"] != "Hörfunk"
    finally:
        cache.close()


@pytest.mark.parametrize("xml", [False, True])
def test_timer_and_recording_pages_show_ordered_channel_details_and_new_branding(setup, xml):
    cfg, engine, app = setup
    box = install_selector(app, xml=xml)
    box.timers = [timer_row(), timer_row(serviceref=RADIO, servicename="Deutschlandfunk & Kultur")]
    box.movies.append(
        movie_row(
            serviceref="1:0:0:0:0:0:0:0:0:0:/media/hdd/movie/radio.ts",
            filename="/media/hdd/movie/radio.ts",
            eventname="Radioaufnahme",
            servicename="Deutschlandfunk & Kultur",
        )
    )
    with Session(engine) as db:
        receiver = db.get(Receiver, 1)
        app.state.channel_catalog.view(receiver, app.state.client_factory(receiver, cfg))
        wait_for(
            lambda: (
                app.state.channel_catalog.view(
                    receiver, app.state.client_factory(receiver, cfg)
                ).describe(RADIO)["bouquet"]
                == "Radio"
            )
        )
    with TestClient(app) as client:
        login_page = client.get("/login")
        assert "Enigma2 Timer" in login_page.text and "Aufnahmen-Verwaltung" in login_page.text
        assert "Mit einem Benutzerkonto fortfahren." not in login_page.text
        assert "Enigma2 Web" not in login_page.text
        login(client, "user", "User-123")
        timers = client.get("/timer")
        assert re.search(
            r'class="receiver-heading-actions">.*?/receiver/select.*?Timer erstellen',
            timers.text,
            re.S,
        )
        for path in ("/timer", "/aufnahmen"):
            page = client.get(path)
            assert page.status_code == 200
            assert re.search(
                r'channel-medium">TV</small>.*?Das Erste HD.*?channel-bouquet">Fernsehen',
                page.text,
                re.S,
            )
            assert re.search(
                r'channel-medium">Radio</small>.*?Deutschlandfunk &amp; Kultur.*?'
                r'channel-bouquet">Radio',
                page.text,
                re.S,
            )
        assert not box.writes


def test_optional_catalog_failure_preserves_timer_and_recording_actions(setup):
    _, _, app = setup
    box = install_selector(app)
    box.timers = [timer_row()]
    original = box.__call__

    def failure(request):
        if request.url.path.endswith("getservices"):
            return httpx.Response(503)
        return original(request)

    from functools import partial

    from e2web.openwebif import OpenWebifClient

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(failure))
    with TestClient(app) as client:
        login(client)
        page = client.get("/timer")
        assert page.status_code == 200 and "Bearbeiten" in page.text and "Löschen" in page.text
        page = client.get("/aufnahmen")
        assert page.status_code == 200 and "Herunterladen" in page.text and "Löschen" in page.text
        assert "Bouquet unbekannt" in page.text
        assert not box.writes
