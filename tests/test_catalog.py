from datetime import datetime, timezone
from functools import partial

import httpx
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from test_foundation import csrf_value, login
from test_foundation import setup as setup

from e2web.config import Config, load_config
from e2web.db import Receiver
from e2web.openwebif import OpenWebifClient, ReceiverError
from e2web.security import cipher

TV_FAVORITES = '1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.favourites.tv" ORDER BY bouquet'
CHANNEL = "1:0:19:283D:3FB:1:C00000:0:0:0:"


def adapter(tmp_path, api):
    config = Config(data_dir=tmp_path)
    config.key_path.write_bytes(Fernet.generate_key())
    receiver = Receiver(
        name="Box",
        hostname="192.0.2.50",
        port=80,
        https=False,
        verify_tls=True,
        username="root",
        encrypted_password=cipher(config).encrypt(b"Receiver-Secret").decode(),
    )
    return OpenWebifClient(receiver, config, transport=httpx.MockTransport(api))


def event(begin=1790956800, **values):
    return {
        "id": 42,
        "begin_timestamp": begin,
        "duration_sec": 3600,
        "title": "Sendung",
        "shortdesc": "Kurzbeschreibung",
        "longdesc": "Beschreibung",
        "sref": CHANNEL,
        "sname": "Das Erste HD",
        **values,
    }


def test_epg_json_normalization_and_query_encoding(tmp_path):
    reference = CHANNEL + "A+B & C"
    seen = []

    def api(request):
        seen.append(request)
        assert request.method == "GET" and request.url.path == "/api/epgservice"
        assert request.url.params["sRef"] == reference
        assert request.headers["Authorization"].startswith("Basic ")
        return httpx.Response(
            200,
            json={
                "result": True,
                "events": [
                    event(2000, id="65535", duration_sec="1200"),
                    {"id": None, "sref": reference},
                    event(1000, id=0, title="A &amp; B", longdesc="Zeile 1<br />Zeile 2"),
                ],
            },
        )

    rows = adapter(tmp_path, api).epg(reference)
    assert [row.begin for row in rows] == [1000, 2000]
    assert rows[0].id == 0 and rows[0].end == 4600
    assert rows[0].title == "A & B"
    assert rows[0].description == "Zeile 1\nZeile 2"
    assert rows[1].duration == 1200
    assert len(seen) == 1


def test_epg_xml_fallback_and_empty_placeholders(tmp_path):
    seen = []

    def api(request):
        seen.append(request.url.path)
        assert request.url.params["sRef"] == CHANNEL
        if request.url.path.startswith("/api/"):
            return httpx.Response(404)
        return httpx.Response(
            200,
            text="""<e2eventlist><e2event>
            <e2eventid>23</e2eventid><e2eventstart>1000</e2eventstart>
            <e2eventduration>1800</e2eventduration><e2eventtitle>A &amp; B</e2eventtitle>
            <e2eventdescription>Kurz</e2eventdescription>
            <e2eventdescriptionextended><![CDATA[Zeile 1\nZeile 2]]></e2eventdescriptionextended>
            <e2eventservicename>Radio Eins</e2eventservicename></e2event>
            <e2event><e2eventid>0</e2eventid><e2eventstart>0</e2eventstart>
            <e2eventduration>0</e2eventduration></e2event></e2eventlist>""",
        )

    rows = adapter(tmp_path, api).epg(CHANNEL)
    assert seen == ["/api/epgservice", "/web/epgservice"]
    assert len(rows) == 1 and rows[0].reference == CHANNEL
    assert rows[0].title == "A & B" and rows[0].name == "Radio Eins"
    assert rows[0].description == "Zeile 1\nZeile 2"


@pytest.mark.parametrize(
    "payload",
    [
        {"events": [], "result": False},
        {"events": {}},
        {"events": ["not an event"]},
        {"events": [event(begin_timestamp=True)]},
        {"events": [event(duration_sec=-1)]},
        {"events": [event(id="not a number")]},
        {"events": [event(begin_timestamp=10**100)]},
    ],
)
def test_invalid_epg_is_safe(tmp_path, payload):
    client = adapter(tmp_path, lambda request: httpx.Response(200, json=payload))
    with pytest.raises(ReceiverError) as raised:
        client.epg(CHANNEL)
    assert "192.0.2" not in str(raised.value) and "Receiver-Secret" not in str(raised.value)


@pytest.mark.parametrize("stype", ["tv", "radio"])
@pytest.mark.parametrize("xml", [False, True])
def test_providers_use_generic_service_query_on_json_and_xml(tmp_path, stype, xml):
    seen = []

    def api(request):
        reference = request.url.params["sRef"]
        seen.append(reference)
        assert request.method == "GET" and request.url.path.endswith("/getservices")
        assert reference.endswith(" FROM PROVIDERS ORDER BY name")
        assert reference.startswith("1:7:2:" if stype == "radio" else "1:7:1:")
        assert ("(type == 10)" in reference) == (stype == "radio")
        assert ("(type == 32)" in reference) == (stype == "tv")
        if xml:
            if request.url.path.startswith("/api/"):
                return httpx.Response(404)
            return httpx.Response(
                200,
                text="<e2servicelist><e2service><e2servicereference>1:7:1:provider</e2servicereference>"
                "<e2servicename>A &amp; B</e2servicename></e2service></e2servicelist>",
            )
        return httpx.Response(
            200,
            json={"services": [{"servicereference": "1:7:1:provider", "servicename": "A & B"}]},
        )

    assert adapter(tmp_path, api).providers(stype) == [
        {"reference": "1:7:1:provider", "name": "A & B"}
    ]
    assert len(seen) == (2 if xml else 1)
    assert len(set(seen)) == 1


def test_catalog_routes_links_markers_and_receiver_isolation(setup):
    _, _, app = setup
    seen = []

    def api(request):
        seen.append(request)
        assert request.url.host == "192.0.2.50"
        if request.url.path.endswith("epgservice"):
            return httpx.Response(200, json={"events": [event()]})
        reference = request.url.params.get("sRef")
        services = (
            [{"servicereference": TV_FAVORITES, "servicename": "Favoriten"}]
            if not reference
            else [
                {"servicereference": "1:64:1:0:0:0:0:0:0:0:", "servicename": "Nachrichten"},
                {"servicereference": CHANNEL, "servicename": "ZDF HD"},
                {"servicereference": "1:134:1:1:0:0:0:0:0:0:", "servicename": "Alternativen"},
            ]
        )
        return httpx.Response(200, json={"services": services})

    app.state.client_factory = partial(OpenWebifClient, transport=httpx.MockTransport(api))
    with TestClient(app) as client:
        login(client, "user", "User-123")
        root = client.get("/epg")
        assert "DM920" not in root.text
        listing = client.get("/sender", params={"reference": TV_FAVORITES})
        assert "Gruppenüberschrift" in listing.text
        assert listing.text.count(">EPG anzeigen</a>") == 2
        assert ">Sender anzeigen</a>" not in listing.text  # alternatives are playable services
        epg = client.get("/epg", params={"reference": CHANNEL, "receiver_id": 2, "day": "all"})
        assert "Das Erste HD" in epg.text and "Sendungsdetails" in epg.text
        denied = client.post(
            "/receiver/select", data={"receiver_id": 2, "csrf_token": csrf_value(epg)}
        )
        assert denied.status_code == 403
        reset = client.post(
            "/receiver/select",
            data={"receiver_id": 1, "destination": "/epg", "csrf_token": csrf_value(epg)},
            follow_redirects=False,
        )
        assert reset.headers["location"] == "/sender"
        for parameters in [{"stype": "wrong"}, {"source": "wrong"}]:
            assert client.get("/sender", params=parameters).status_code == 400
        assert client.get("/epg", params={"reference": "x" * 2049}).status_code == 400
        assert client.get("/epg", params={"reference": CHANNEL, "day": "wrong"}).status_code == 400
    assert all(request.method == "GET" for request in seen)


@pytest.mark.parametrize(
    "start, expected_time, expected_offset",
    [
        ("2026-07-01T18:15:00+00:00", "20:15", "+02:00"),
        ("2026-12-01T19:15:00+00:00", "20:15", "+01:00"),
    ],
)
def test_epg_timezone_escaping_and_date_filter(setup, start, expected_time, expected_offset):
    _, _, app = setup
    timestamp = int(datetime.fromisoformat(start).timestamp())
    payload = {
        "events": [
            event(
                timestamp, title='<script>alert("title")</script>', longdesc="<img src=x onerror=x>"
            ),
            event(timestamp + 86400, title="Morgen"),
        ]
    }
    app.state.client_factory = partial(
        OpenWebifClient,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload)),
    )
    with TestClient(app) as client:
        login(client, "user", "User-123")
        day = datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat()
        page = client.get("/epg", params={"reference": CHANNEL, "day": day})
        assert expected_time in page.text and expected_offset in page.text
        assert "&lt;script&gt;" in page.text and "&lt;img" in page.text
        assert '<script>alert("title")' not in page.text and "<img src=x" not in page.text
        assert "Morgen" not in page.text
        page = client.get("/epg", params={"reference": CHANNEL, "day": "all"})
        assert "Morgen" in page.text


def test_running_program_across_midnight(setup, monkeypatch):
    _, _, app = setup
    begin = int(datetime.fromisoformat("2026-10-02T21:30:00+00:00").timestamp())
    current = int(datetime.fromisoformat("2026-10-02T22:10:00+00:00").timestamp())
    monkeypatch.setattr("e2web.main.now", lambda: current)
    app.state.client_factory = partial(
        OpenWebifClient,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"events": [event(begin, title="Nachtprogramm")]}
            )
        ),
    )
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/epg", params={"reference": CHANNEL})
        assert "Nachtprogramm" in page.text and ">Läuft</span>" in page.text
        assert "bis 03.10. 00:30" in page.text
        assert 'value="2026-10-03" selected' in page.text


def test_epg_spanning_clock_change_keeps_real_duration(setup):
    _, _, app = setup
    begin = int(datetime.fromisoformat("2026-10-25T00:30:00+00:00").timestamp())
    app.state.client_factory = partial(
        OpenWebifClient,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"events": [event(begin)]})
        ),
    )
    with TestClient(app) as client:
        login(client, "user", "User-123")
        page = client.get("/epg", params={"reference": CHANNEL, "day": "2026-10-25"})
        assert "02:30 CEST" in page.text and "bis 02:30 CET" in page.text
        assert "60 Min." in page.text


def test_old_configuration_uses_berlin_and_invalid_timezone_fails(tmp_path):
    path = tmp_path / "e2web.toml"
    path.write_text('data_dir = "data"\n')
    assert load_config(path).timezone == "Europe/Berlin"
    path.write_text('timezone = "Unknown/Zone"\n')
    with pytest.raises(ValueError, match="EPG-Zeitzone"):
        load_config(path)
