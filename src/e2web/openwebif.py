from __future__ import annotations

import html
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx
from cryptography.fernet import InvalidToken
from defusedxml.ElementTree import fromstring

from e2web.recordings import Recording, RecordingList, directory_path
from e2web.security import cipher
from e2web.timers import Timer, TimerList, TimerResult


class ReceiverError(ValueError):
    pass


class TimerOutcomeUnknown(ReceiverError):
    pass


@dataclass
class ReceiverDownload:
    client: httpx.Client
    response: httpx.Response

    def close(self):
        self.response.close()
        self.client.close()

    def chunks(self):
        try:
            yield from self.response.iter_raw(chunk_size=64 * 1024)
        finally:
            self.close()


@dataclass(frozen=True)
class EpgEvent:
    id: int
    begin: int
    duration: int
    title: str
    short_description: str
    description: str
    reference: str
    name: str

    @property
    def end(self) -> int:
        return self.begin + self.duration


def plain_text(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ReceiverError("OpenWebif liefert ein unbekanntes Textformat.")
    value = html.unescape(value).replace("\u0086", "").replace("\u0087", "")
    return re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)


def bouquet_reference(stype: str) -> str:
    kind = "2" if stype == "radio" else "1"
    return f'1:7:{kind}:0:0:0:0:0:0:0:FROM BOUQUET "bouquets.{stype}" ORDER BY bouquet'


class OpenWebifClient:
    """Receiver adapter; URLs and credentials stay on the server."""

    def __init__(self, receiver, config, *, transport=None):
        self.receiver = receiver
        self.config = config
        self.transport = transport

    def services(self, reference: str | None = None) -> list[dict[str, str]]:
        data, xml = self._request("getservices", {"sRef": reference} if reference else {})
        return self._services(data, xml)

    def bouquets(self, stype: str = "tv") -> list[dict[str, str]]:
        return self.services(bouquet_reference(stype) if stype == "radio" else None)

    def providers(self, stype: str = "tv") -> list[dict[str, str]]:
        # The generic service query also works on older XML WebInterface receivers.
        kind = "2" if stype == "radio" else "1"
        types = (2, 10) if stype == "radio" else (1, 17, 22, 25, 31, 32, 134, 195)
        query = " || ".join(f"(type == {value})" for value in types)
        return self.services(f"1:7:{kind}:0:0:0:0:0:0:0:{query} FROM PROVIDERS ORDER BY name")

    def epg(self, reference: str) -> list[EpgEvent]:
        data, xml = self._request("epgservice", {"sRef": reference})
        if xml:
            if data.tag != "e2eventlist":
                raise ReceiverError("Die Antwort enthält keine Enigma2-EPG-Liste.")
            rows = [
                {
                    "id": row.findtext("e2eventid"),
                    "begin_timestamp": row.findtext("e2eventstart"),
                    "duration_sec": row.findtext("e2eventduration"),
                    "title": row.findtext("e2eventtitle"),
                    "shortdesc": row.findtext("e2eventdescription"),
                    "longdesc": row.findtext("e2eventdescriptionextended"),
                    "sref": row.findtext("e2eventservicereference"),
                    "sname": row.findtext("e2eventservicename"),
                }
                for row in data.findall("e2event")
            ]
        else:
            rows = self._rows(data, "events", "EPG-Liste")
        events = []
        for row in rows:
            if not isinstance(row, dict):
                raise ReceiverError("OpenWebif liefert ein unbekanntes EPG-Format.")
            # OpenWebif emits a placeholder when the receiver has no EPG data.
            if row.get("id") in (None, "", "None") and not row.get("begin_timestamp"):
                continue
            if str(row.get("begin_timestamp")) == "0" and str(row.get("duration_sec")) == "0":
                continue
            events.append(
                EpgEvent(
                    id=self._integer(row.get("id"), 0, 65535),
                    begin=self._integer(row.get("begin_timestamp"), 1, 4102444800),
                    duration=self._integer(row.get("duration_sec"), 0, 604800),
                    title=plain_text(row.get("title")) or "Ohne Titel",
                    short_description=plain_text(row.get("shortdesc")),
                    description=plain_text(row.get("longdesc")),
                    reference=plain_text(row.get("sref")) or reference,
                    name=plain_text(row.get("sname")),
                )
            )
        # Receivers do not always return events in chronological order.
        return sorted(events, key=lambda event: (event.begin, event.id))

    def timer_list(self) -> TimerList:
        data, xml = self._request("timerlist", {})
        locations, default = [], ""
        if xml:
            if data.tag != "e2timerlist":
                raise ReceiverError("Die Antwort enthält keine Enigma2-Timerliste.")
            fields = {
                "serviceref": "e2servicereference",
                "servicename": "e2servicename",
                "name": "e2name",
                "description": "e2description",
                "eit": "e2eit",
                "begin": "e2timebegin",
                "end": "e2timeend",
                "disabled": "e2disabled",
                "repeated": "e2repeated",
                "justplay": "e2justplay",
                "afterevent": "e2afterevent",
                "dirname": "e2location",
                "tags": "e2tags",
                "state": "e2state",
                "cancelled": "e2cancled",
                "always_zap": "e2alwayszap",
                "pipzap": "e2pipzap",
                "filename": "e2filename",
                "autoadjust": "e2autoadjust",
                "allow_duplicate": "e2allowduplicate",
                "vpsplugin_enabled": "e2vpspluginenabled",
                "vpsplugin_overwrite": "e2vpspluginoverwrite",
                "vpsplugin_time": "e2vpsplugintime",
                "recordingtype": "e2recordingtype",
            }
            rows = [
                {key: row.findtext(tag) for key, tag in fields.items()}
                for row in data.findall("e2timer")
            ]
        else:
            rows = self._rows(data, "timers", "Timerliste")
            if isinstance(data.get("locations"), list):
                locations = [plain_text(p) for p in data["locations"] if isinstance(p, str)]
            default = plain_text(data.get("default"))
        timers = []
        try:
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError
                reference = plain_text(row.get("serviceref"))
                if not reference or len(reference) > 2048 or any(ord(c) < 32 for c in reference):
                    raise ValueError
                begin = self._integer(row.get("begin"), 1, 4102444800)
                end = self._integer(row.get("end"), begin, 4103059600)
                extras = {}
                for key in ("always_zap", "pipzap", "autoadjust"):
                    value = row.get(key)
                    if value not in (None, "", -1, "-1"):
                        extras[key] = str(self._flag(value))
                for key in ("allow_duplicate", "vpsplugin_enabled", "vpsplugin_overwrite"):
                    if row.get(key) not in (None, ""):
                        extras[key] = str(self._flag(row[key]))
                if row.get("vpsplugin_time") not in (None, "", "None", -1, "-1"):
                    extras["vpsplugin_time"] = str(
                        self._integer(row["vpsplugin_time"], 0, 4102444800)
                    )
                if row.get("recordingtype") in {"normal", "descrambled", "scrambled"}:
                    extras["recordingtype"] = row["recordingtype"]
                tags = row.get("tags")
                if isinstance(tags, list) and all(isinstance(tag, str) for tag in tags):
                    tags = " ".join(tags)
                directory = plain_text(row.get("dirname"))
                if directory == "None":
                    directory = ""
                timers.append(
                    Timer(
                        reference=reference,
                        channel=plain_text(row.get("servicename")),
                        name=plain_text(row.get("name")),
                        description=plain_text(row.get("description")),
                        begin=begin,
                        end=end,
                        disabled=self._flag(row.get("disabled", 0)),
                        repeated=self._integer(row.get("repeated") or 0, 0, 127),
                        justplay=self._flag(row.get("justplay", 0)),
                        afterevent=self._integer(row.get("afterevent") or 0, 0, 3),
                        directory=directory,
                        tags=plain_text(tags),
                        eit=self._integer(row.get("eit") or 0, 0, 65535),
                        state=self._integer(row.get("state") or 0, 0, 10),
                        cancelled=bool(self._flag(row.get("cancelled") or 0)),
                        extras=extras,
                        filename=plain_text(row.get("filename"))
                        if row.get("filename") != "None"
                        else "",
                    )
                )
        except (ValueError, TypeError, AttributeError):
            raise ReceiverError("OpenWebif liefert ein unbekanntes Timerformat.") from None
        return TimerList(timers, locations, default, xml)

    @staticmethod
    def _flag(value):
        if value is None:
            return 0
        if value in (0, "0", False, "False", "false"):
            return 0
        if value in (1, "1", True, "True", "true"):
            return 1
        raise ValueError("Ungültiger Schalterwert.")

    def timer_locations(self):
        data, xml = self._request("getlocations", {})
        if xml:
            if data.tag != "e2locations":
                raise ReceiverError("Die Antwort enthält keine Aufnahmepfade.")
            return [plain_text(row.text) for row in data.findall("e2location") if row.text]
        return [plain_text(p) for p in self._rows(data, "locations", "Aufnahmepfade")]

    def recording_locations(self):
        data, xml = self._request("getlocations", {})
        if xml:
            if data.tag != "e2locations":
                raise ReceiverError("Die Antwort enthält keine Aufnahmepfade.")
            roots = [plain_text(row.text) for row in data.findall("e2location") if row.text]
            default = ""
        else:
            roots = [plain_text(p) for p in self._rows(data, "locations", "Aufnahmepfade")]
            default = plain_text(data.get("default"))
        return roots, default

    def current_recording_location(self):
        data, xml = self._request("getcurrlocation", {})
        if xml:
            if data.tag == "e2location":
                location = plain_text(data.text)
            elif data.tag == "e2locations" and len(data.findall("e2location")) == 1:
                location = plain_text(data.findtext("e2location"))
            else:
                raise ReceiverError("Die Antwort enthält keinen Aufnahmepfad.")
        else:
            if not isinstance(data, dict) or data.get("result") is False:
                raise ReceiverError("Der Receiver liefert keinen Aufnahmepfad.")
            location = plain_text(data.get("location"))
        try:
            return directory_path(location)
        except ValueError:
            raise ReceiverError("Der Receiver liefert einen ungültigen Aufnahmepfad.") from None

    def default_recording_location(self):
        # getcurrlocation describes the movie browser's last folder, not this setting.
        data, xml = self._request("settings", {})
        key = "config.usage.default_path"
        if xml:
            if data.tag != "e2settings":
                raise ReceiverError("Die Antwort enthält keine Receiver-Einstellungen.")
            values = [
                row.findtext("e2settingvalue")
                for row in data.findall("e2setting")
                if row.findtext("e2settingname") == key
            ]
        else:
            values = []
            for row in self._rows(data, "settings", "Receiver-Einstellungen"):
                if isinstance(row, list) and len(row) == 2 and row[0] == key:
                    values.append(row[1])
                elif isinstance(row, dict) and row.get("name") == key:
                    values.append(row.get("value"))
        try:
            paths = {directory_path(plain_text(value)) for value in values}
            if len(paths) != 1:
                raise ValueError
        except (ReceiverError, ValueError):
            raise ReceiverError(
                "Der konfigurierte Standardaufnahmeordner konnte nicht ermittelt werden."
            ) from None
        return paths.pop()

    def open_recording(self, filename, range_header=None):
        if (
            not filename.startswith("/")
            or ".." in filename.split("/")
            or any(ord(c) < 32 for c in filename)
        ):
            raise ReceiverError("Ungültige Aufnahmedatei.")
        # Legacy FileStreamer unquotes the already decoded parameter a second time.
        # Reject ambiguous names so that the exact listed file is always served.
        if re.search(r"%[0-9a-fA-F]{2}", filename):
            raise ReceiverError("Dieser Dateiname kann nicht eindeutig heruntergeladen werden.")
        if range_header and not re.fullmatch(r"bytes=(?:\d+-\d*|-\d+)", range_header):
            raise ReceiverError("Ungültiger Downloadbereich.")
        options = self._client_options()
        options["timeout"] = self._recording_timeout()
        client = httpx.Client(**options)
        response = None
        try:
            headers = {"Accept-Encoding": "identity"}
            if range_header:
                headers["Range"] = range_header
            params = {"file": filename, "action": "download"}
            response = client.send(
                client.build_request("GET", "/file", params=params, headers=headers), stream=True
            )
            # Older FileStreamer deployments redirect this one known route to /file/.
            if response.is_redirect:
                location = urlsplit(response.headers.get("Location", ""))
                origin = urlsplit(self.receiver.base_url)
                if location.path == "/file/" and (
                    not location.netloc
                    or (location.netloc == origin.netloc and location.scheme == origin.scheme)
                ):
                    response.close()
                    response = client.send(
                        client.build_request("GET", "/file/", params=params, headers=headers),
                        stream=True,
                    )
            if response.status_code != 416 or not range_header:
                self._check(response)
            if response.status_code not in {200, 206, 416}:
                raise ReceiverError("Die Aufnahmedatei ist nicht verfügbar.")
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                raise ReceiverError("Der Receiver liefert ein unbekanntes Downloadformat.")
            # OpenWebif reports a missing file with status 200 and a text error.
            if (
                response.status_code == 200
                and not response.headers.get("Content-Disposition")
                and response.headers.get("Content-Type", "").startswith(
                    ("text/", "application/json")
                )
            ):
                raise ReceiverError("Die Aufnahmedatei ist nicht verfügbar.")
            return ReceiverDownload(client, response)
        except Exception as exc:
            if response is not None:
                response.close()
            client.close()
            if isinstance(exc, ReceiverError):
                raise
            raise ReceiverError("Der Download vom Receiver konnte nicht geöffnet werden.") from None

    def _recording_timeout(self):
        return httpx.Timeout(
            self.config.receiver_timeout,
            read=max(self.config.receiver_timeout, self.config.recording_timeout),
        )

    def write_timer(self, method: str, params: dict, *, xml: bool) -> TimerResult:
        if method not in {"timeradd", "timerchange", "timerdelete"}:
            raise ValueError("Unzulässiger Timerauftrag.")
        return self._write(method, params, xml=xml)

    def delete_recording(self, reference: str, *, xml: bool) -> TimerResult:
        # Let Enigma2 remove its service and sidecar files, honoring the receiver's trash setting.
        return self._write("moviedelete", {"sRef": reference}, xml=xml)

    def _write(self, method: str, params: dict, *, xml: bool) -> TimerResult:
        # The read selected the interface. A write has exactly one attempt, with no fallback.
        options = self._client_options()
        try:
            with httpx.Client(**options) as client:
                response = client.post(f"/{'web' if xml else 'api'}/{method}", data=params)
                self._check(response)
                if xml:
                    data = fromstring(response.content)
                    if data.tag != "e2simplexmlresult":
                        raise ValueError
                    result = data.findtext("e2state")
                    if result not in {"True", "False", "true", "false"}:
                        raise ValueError
                    success = result.lower() == "true"
                    message = data.findtext("e2statetext", "")
                    conflicts = []
                else:
                    data = response.json()
                    if not isinstance(data, dict) or type(data.get("result")) is not bool:
                        raise ValueError
                    success, message = data["result"], plain_text(data.get("message"))
                    conflicts = []
                    for item in data.get("conflicts", []) or []:
                        if isinstance(item, dict):
                            conflicts.append(
                                {
                                    "name": plain_text(item.get("name")),
                                    "channel": plain_text(item.get("servicename")),
                                }
                            )
                return TimerResult(
                    success,
                    bool(conflicts) or any(w in message.lower() for w in ("conflict", "konflikt")),
                    conflicts,
                )
        except ReceiverError:
            if response.status_code in {401, 403}:
                raise
            raise TimerOutcomeUnknown("Der Receiver hat den Auftrag nicht bestätigt.") from None
        except Exception:
            raise TimerOutcomeUnknown("Der Receiver hat den Auftrag nicht bestätigt.") from None

    def recording_list(self, directory: str | None = None) -> RecordingList:
        if directory:
            directory = directory_path(directory)
        data, xml = self._request(
            "movielist", {"dirname": directory} if directory else {}, recording=True
        )
        folders = []
        if xml:
            if data.tag != "e2movielist":
                raise ReceiverError("Die Antwort enthält keine Enigma2-Aufnahmeliste.")
            fields = {
                "serviceref": "e2servicereference",
                "filename": "e2filename",
                "eventname": "e2title",
                "servicename": "e2servicename",
                "description": "e2description",
                "descriptionExtended": "e2descriptionextended",
                "recordingtime": "e2time",
                "length": "e2length",
                "filesize": "e2filesize",
                "tags": "e2tags",
            }
            rows = [
                {key: row.findtext(tag) for key, tag in fields.items()}
                for row in data.findall("e2movie")
            ]
            folders = [
                plain_text(node.text)
                for node in data.findall("e2locations/e2location")
                if node.text
            ]
        else:
            rows = self._rows(data, "movies", "Aufnahmeliste")
            if isinstance(data.get("directory"), str) and data["directory"]:
                try:
                    directory = directory_path(data["directory"])
                except ValueError:
                    raise ReceiverError(
                        "OpenWebif liefert einen ungültigen Aufnahmepfad."
                    ) from None
            if isinstance(data.get("bookmarks"), list):
                folders = [plain_text(p) for p in data["bookmarks"] if isinstance(p, str)]
        recordings = []
        try:
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError
                reference = plain_text(row.get("serviceref") or row.get("fullname"))
                filename = plain_text(row.get("filename"))
                if not filename and "/" in reference:
                    filename = "/" + reference.split("/", 1)[1]
                if (
                    not reference
                    or len(reference) > 4096
                    or not filename.startswith("/")
                    or any(ord(c) < 32 for c in reference + filename)
                    or ".." in filename.split("/")
                ):
                    raise ValueError
                # Only receiver-supplied file services become deletable entries.
                parts = reference.split(":", 10)
                if len(parts) != 11 or not parts[10].startswith("/") or parts[10] != filename:
                    raise ValueError
                raw_length = row.get("length")
                duration = None
                if isinstance(raw_length, str) and raw_length and "?" not in raw_length:
                    components = raw_length.split(":")
                    if len(components) in (2, 3) and all(part.isdecimal() for part in components):
                        duration = 0
                        for part in components:
                            duration = duration * 60 + int(part)
                recordings.append(
                    Recording(
                        reference=reference,
                        filename=filename,
                        title=plain_text(row.get("eventname")) or filename.rsplit("/", 1)[-1],
                        channel=plain_text(row.get("servicename")),
                        tags=plain_text(
                            " ".join(row["tags"])
                            if isinstance(row.get("tags"), list)
                            and all(isinstance(t, str) for t in row["tags"])
                            else row.get("tags")
                        ),
                        description=plain_text(row.get("description")),
                        extended_description=plain_text(row.get("descriptionExtended")),
                        begin=self._integer(row["recordingtime"], 0, 4102444800)
                        if row.get("recordingtime") not in (None, "", "None", -1, "-1")
                        else 0,
                        duration=duration,
                        size=self._integer(row["filesize"], 0, 2**63 - 1)
                        if row.get("filesize") not in (None, "", "None", -1, "-1")
                        else None,
                    )
                )
        except (ValueError, TypeError, AttributeError):
            raise ReceiverError("OpenWebif liefert ein unbekanntes Aufnahmeformat.") from None
        if not directory and recordings:
            parents = {recording.parent for recording in recordings}
            if len(parents) == 1:
                directory = parents.pop()
        return RecordingList(recordings, directory or "", folders, xml)

    @staticmethod
    def _integer(value, minimum, maximum):
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ReceiverError("OpenWebif liefert ungültige EPG-Zeitdaten.")
        try:
            value = int(value)
        except ValueError:
            raise ReceiverError("OpenWebif liefert ungültige EPG-Zeitdaten.") from None
        if not minimum <= value <= maximum:
            raise ReceiverError("OpenWebif liefert ungültige EPG-Zeitdaten.")
        return value

    @staticmethod
    def _rows(data, key, label):
        if not isinstance(data, dict) or not isinstance(data.get(key), list):
            raise ReceiverError(f"Die Antwort enthält keine OpenWebif-{label}.")
        if data.get("result") is False:
            raise ReceiverError("OpenWebif hat die Abfrage abgelehnt.")
        return data[key]

    @classmethod
    def _services(cls, data, xml):
        if xml:
            if data.tag != "e2servicelist":
                raise ReceiverError("Die Antwort enthält keine Enigma2-Senderliste.")
            return [
                {
                    "reference": row.findtext("e2servicereference", ""),
                    "name": plain_text(row.findtext("e2servicename", "")),
                }
                for row in data.findall("e2service")
            ]
        rows = cls._rows(data, "services", "Senderliste")
        if not all(
            isinstance(row, dict)
            and isinstance(row.get("servicereference"), str)
            and isinstance(row.get("servicename"), str)
            for row in rows
        ):
            raise ReceiverError("OpenWebif liefert ein unbekanntes Senderformat.")
        return [
            {"reference": row["servicereference"], "name": plain_text(row["servicename"])}
            for row in rows
        ]

    def _client_options(self):
        try:
            password = (
                cipher(self.config).decrypt(self.receiver.encrypted_password.encode()).decode()
                if self.receiver.encrypted_password
                else ""
            )
        except (InvalidToken, OSError):
            raise ReceiverError(
                "Receiver-Zugangsdaten können nicht entschlüsselt werden. "
                "Bitte den gespeicherten Schlüssel prüfen."
            ) from None
        auth = (self.receiver.username, password) if self.receiver.username else None
        return dict(
            base_url=self.receiver.base_url,
            auth=auth,
            timeout=self.config.receiver_timeout,
            verify=self.receiver.verify_tls,
            follow_redirects=False,
            trust_env=False,
            transport=self.transport,
        )

    def _request(self, method, params, *, recording=False):
        options = self._client_options()
        if recording:
            options["timeout"] = self._recording_timeout()
        try:
            with httpx.Client(**options) as client:
                response = client.get(f"/api/{method}", params=params)
                if response.status_code in {404, 405}:
                    response = client.get(f"/web/{method}", params=params)
                    self._check(response)
                    return fromstring(response.content), True
                self._check(response)
                return response.json(), False
        except ReceiverError:
            raise
        except httpx.TimeoutException:
            raise ReceiverError("Der Receiver antwortet nicht innerhalb des Zeitlimits.") from None
        except httpx.HTTPError:
            raise ReceiverError(
                "Verbindung fehlgeschlagen. Adresse, Port und gegebenenfalls "
                "HTTPS-Zertifikat prüfen."
            ) from None
        except Exception:
            # Raw network errors can contain receiver addresses or credentials.
            raise ReceiverError("Die Receiver-Antwort konnte nicht verarbeitet werden.") from None

    @staticmethod
    def _check(response):
        if response.status_code in {401, 403}:
            raise ReceiverError(
                "OpenWebif verweigert den Zugriff. Zugangsdaten und "
                "API-Zugriffseinstellungen prüfen."
            )
        if response.is_redirect:
            raise ReceiverError(
                "OpenWebif leitet die Anfrage weiter. Die direkte Adresse "
                "und HTTP/HTTPS-Einstellung prüfen."
            )
        response.raise_for_status()
