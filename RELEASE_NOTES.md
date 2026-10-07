# Enigma2 Timer 1.1.11

Release: 07.10.2026 · Git-Tag: `v1.1.11` · Datenbankschema: `0005`

Zentrale Timer- und Aufnahmen-Verwaltung für mehrere Enigma2-Receiver über
OpenWebif oder das ältere XML-WebInterface, mit deutscher Oberfläche im AWAS-Stil.

## Neu in 1.1.11

- **Festplattenanzeige korrigiert:** Die strenge Zuordnung zum Aufnahmeordner
  entfällt. Auch ohne gemeldeten Einhängepunkt werden alle Festplatten des
  ausgewählten Receivers angezeigt, über JSON und das ältere XML-WebInterface.
- **Anzeige:** **Freier Speicherplatz: 660.884 GB (WD(My Passport 0748))**.
  Für jede weitere Festplatte eine neue, bündig unter der ersten beginnende Zeile.
- **Unbekannte Angaben:** Fehlende oder unlesbare Speicherwerte bleiben
  **unbekannt**; Modellname und andere lesbare Festplatten bleiben sichtbar.
  Bei nicht verfügbarer Festplattenliste erscheint eine allgemeine unbekannt-Zeile.
- **Aktualisierung:** Alle Festplattenwerte werden zusammen mit der Aufnahmeliste
  alle fünf Sekunden erneuert und bleiben unabhängig vom ausgewählten Ordner.
- **Update:** Keine Konfigurationsänderung, neue Migration oder Abhängigkeit nötig.
  Aufnahme-Lesezeitlimit weiterhin 90 Sekunden, Datenbankschema `0005`.

## Standardbindung seit 1.1.9

- **Standardbindung:** `host = "0.0.0.0"` für alle IPv4-Adressen des Servers.
  Gilt für die Programmvorgabe, Konfigurationen ohne `host`, `e2web init` und
  die Installationsvorlage. Direkter Aufruf unter `http://SERVER-IP:8081`.
- **Vorhandene Installation:** In `/etc/e2web/e2web.toml` den `host`-Eintrag auf
  `"0.0.0.0"` setzen und `systemctl restart e2web` ausführen. Vorhandene
  Konfigurationswerte werden beim Update erhalten. Einzelheiten: [INSTALL.md](INSTALL.md).
- **Update:** Port weiterhin standardmäßig 8081; keine neue Migration oder
  Abhängigkeit. Schema `0005`, Konten, Receiver und Schlüssel bleiben erhalten.

## Timer kopieren seit 1.1.8

- **Timer kopieren:** Bei anstehenden Timern steht **Kopieren** zwischen
  **Bearbeiten** und **Löschen**. Der Button öffnet **Timer erstellen** mit den
  Daten der Vorlage. Alle Formularfelder lassen sich vor dem Speichern ändern.
- **Übernommene Daten:** Sender, Name, Beschreibung, Beginn/Ende, Wiederholung,
  Aufnahmepfad und deaktivierter Zustand. Timerart und Endaktion sind im
  kopierten Entwurf ebenfalls einstellbar; Receiver-Zusatzoptionen bleiben erhalten.
- **Eigenständige Kopie:** Erst **Timer speichern** sendet einen Erstellauftrag.
  Die Vorlage bleibt unverändert. Der neue Timer gehört dem angemeldeten Benutzer;
  gewöhnliche Tags bleiben erhalten, alte Ersteller-Tags werden ersetzt.
- **Berechtigungen und Fehler:** Schreibrechte sind nötig. Laufende und erledigte
  Timer sind ausgeschlossen. Bei Duplikat oder Receiverkonflikt bleibt der Entwurf
  zum Anpassen geöffnet. JSON, XML, Ladeanzeige und JavaScript-Fallback unterstützt.
- **Update:** Keine neue Migration oder Abhängigkeit; Schema weiterhin `0005`.
  Vorhandene Konten, Konfiguration und Schlüssel bleiben erhalten.

## Aufnahmeordner-Fallback seit 1.1.7

- **Aufnahmen:** Kann der konfigurierte Standardaufnahmeordner nicht ermittelt
  werden, wird automatisch der erste Eintrag der alphabetisch sortierten
  Ordnerliste ausgewählt und geladen. Seine Aufnahmen erscheinen direkt.
- **Vorrang:** Ein lesbarer Standardaufnahmeordner und eine bereits manuell
  getroffene Ordnerauswahl bleiben vorrangig. Die automatische Aktualisierung
  behält den angezeigten Ordner bei.
- **Fehleranzeige:** Sind auch keine auswählbaren Aufnahmepfade verfügbar,
  erscheint eine entsprechende Meldung. Der Fallback unterstützt JSON und XML
  und ändert keine Einstellungen des Receivers.
- **Update:** Keine neue Migration oder Abhängigkeit. Datenbankschema weiterhin
  `0005`; Konfiguration, Schlüssel und Konten bleiben erhalten.

## Seiten laden und Standardordner seit 1.1.6

- **Aufnahmen:** Beim Aufruf über das Menü wird der konfigurierte Standard-
  Aufnahmeordner des Receivers geöffnet. Maßgeblich ist `config.usage.default_path`
  aus der Einstellungen-Abfrage, unabhängig vom zuletzt lokal geöffneten Ordner.
  JSON und das ältere XML-WebInterface werden unterstützt.
- **Ordnerwechsel:** Ein manuell gewählter Ordner bleibt beim Neuladen und bei
  der automatischen Aktualisierung erhalten. Auch ein Standardpfad außerhalb
  der Bookmarks ist nutzbar. Seit 1.1.7 übernimmt bei einem unlesbaren Standard
  automatisch der erste angebotene Ordner.
- **Ladeanzeige:** Timer, Aufnahmen, Sender, EPG und Timerformulare erscheinen
  sofort mit Navigation und Überschrift. Bis zur vollständigen Receiver-Antwort
  steht **Lade Daten von Receiver...** in der Seite; danach folgen Daten oder
  eine verständliche Fehlermeldung. Kein leerer Browser während des Wartens.
- **Bedienung:** Nachgeladene Filter, Ordnerauswahl und Timerformulare bleiben
  bedienbar. Derselbe Ladehinweis erscheint bei Bouquetwechseln und während
  bestehender Receiveraufträge. Beim Erstladen kann nach einem Verbindungsfehler
  über **Erneut versuchen** erneut gelesen werden. Schreibaufträge werden nicht
  automatisch wiederholt; bei unklarer Antwort ist **Liste prüfen** verfügbar.
  Ohne JavaScript ist **Daten anzeigen** verfügbar.
- **Update:** Keine neue Migration oder Abhängigkeit. Konten, Receiver,
  Konfiguration und Schlüssel bleiben erhalten; das Aufnahmezeitlimit beträgt
  weiterhin standardmäßig 90 Sekunden.

## Oberfläche seit 1.1.5

- **Receiverauswahl:** Auswahlfeld auf allen Seiten mit Receiverumschaltung
  um etwa 50 Prozent verbreitert. Auf kleinen Bildschirmen wird weiterhin
  die verfügbare Breite genutzt.
- **Schrift in Auswahlfeldern:** Mehr vertikaler Platz bei unveränderter
  Feldhöhe, damit Buchstaben wie „g“, „p“ und „y“ nicht abgeschnitten werden.
  Filterfelder bleiben genauso hoch wie die Receiverauswahl.
- **Überschriften:** Haupttitel unverändert, danach ein Leerzeichen und der
  aktive Receiver in exakt halber Schriftgröße; kein Doppelpunkt.
  Gilt für Timer, Sender, Aufnahmen, EPG und die Timerformulare einschließlich
  der Auftragsprüfung. Lange Namen können auf schmalen Bildschirmen umbrechen.
- **Update:** Keine neue Migration; vorhandene Benutzer, Receiver, Timer,
  Konfiguration und Schlüssel bleiben erhalten.

## Aufnahmeordner seit 1.1.4

- **Aufnahmen beim ersten Aufruf:** Der gewählte Ordner wird vor dem Laden
  ausdrücklich an `movielist` übergeben. Seit Version 1.1.6 wird dafür der
  konfigurierte Standard aus `settings` gelesen, statt den aktuellen lokalen Ordner
  aus `getcurrlocation` als Standard zu behandeln.
- **Ursache:** Enthielt `getlocations` keinen Standardpfad, wurde zuvor die Liste
  ohne Ordner geladen und erst anschließend der angezeigte Pfad ermittelt.
  Einige Receiver lieferten dabei eine leere Liste aus einem anderen Ordner.
- **Kompatibilität:** JSON und das ältere XML-WebInterface sind berücksichtigt.
  Ordnerwechsel, Downloads und automatische Aktualisierung verwenden dieselbe
  Pfadauflösung. Die Freigabe vom Receiver bestätigter Symlinkpfade bleibt erhalten.
- **Update:** Keine neue Migration oder Änderung gespeicherter Receiver, Timer
  oder Aufnahmedateien. Aufnahmezeitlimit weiterhin standardmäßig 90 Sekunden.

## Favicon seit 1.1.3

- **Favicon:** Der bisherige Header `no-store` verhinderte, dass Firefox das
  Icon für Lesezeichen speichert. Favicon-Dateien werden jetzt gezielt mit
  `public, max-age=86400` ausgeliefert. Andere Antworten behalten `no-store`.
- **Standardpfad:** `/favicon.ico` ist ohne Anmeldung mit GET und HEAD erreichbar.
  Das vorhandene Logo ist als echte ICO-Datei in 16, 32 und 48 Pixeln enthalten.
- **Einbindung:** Alle Seiten verwenden eine versionierte Icon-URL, damit der
  Browser das Favicon nach einem Update neu laden kann.
- **Update:** Keine Migration und keine Änderung gespeicherter Receiver oder Timer.
  Nach Installation die Seite über das Lesezeichen öffnen und neu laden.

## Bereinigung seit 1.1.2

- Private Netzwerkadressen aus dem Receiverformular und den Tests entfernt;
  Beispiele verwenden reservierte Dokumentationsadressen und `example.test`.
- Auch die Git-Historie mit `v1.0.0`, `v1.1.0` und `v1.1.1` ist bereinigt.
  Deren Commit- und Tag-Kennungen ändern sich. Die einmalige
  GitHub-Umstellung wurde mit Version 1.1.2 vorbereitet; siehe [GITHUB.md](GITHUB.md).
- Keine Schemaänderung und keine Änderung gespeicherter Receiververbindungen.

## Oberfläche seit 1.1.1

- **Timer:** Kopfzeile in der Reihenfolge Receiverauswahl, „Liste filtern“,
  „Timer erstellen“. Auf schmalen Bildschirmen steht die Receiverauswahl
  über Filter und Button.
- **Timer, Sender und Aufnahmen:** Filterfelder exakt so hoch wie das
  Dropdownmenü der Receiverauswahl, auch in der mobilen Ansicht.

## Listenfilter seit 1.1.0

- **Timer:** Suche ausschließlich in Sendernamen und Timer-Titeln.
- **Aufnahmen:** „Liste filtern“ rechts neben der Ordnerauswahl; Suche in
  Sendernamen, Dateinamen und Aufnahme-/Timer-Titeln.
- **Alle Filter:** Beschriftung im Eingabefeld; keine zusätzliche sichtbare
  Beschriftung. Teiltextsuche ohne Beachtung der Groß-/Kleinschreibung.
- Filter einschließlich Dateizeilen, Suchtext, Fokus und Cursorposition bleiben
  bei der automatischen Aktualisierung wirksam, auch auf mobilen Geräten.
- Einheitliche Beschriftung **Timer erstellen**, auch bei Sendern und im EPG.

## Enthalten

- Senderlisten mit TV-/Radio-Bouquets und Anbietern sowie EPG pro Sender.
- Timer erstellen, bearbeiten, kopieren, deaktivieren und löschen; wiederkehrende Termine
  und Vor-/Nachlauf aus dem EPG.
- Aufnahmen mit Ordnerauswahl, Dateigröße, Status, Ersteller und Downloads.
- Benutzer-/Receiververwaltung mit Standardreceiver und getrennten Lese-/Schreibrechten.
- Benutzer bearbeiten/löschen eigene Einträge; laufende Aufnahmen bleiben geschützt.
- Automatische Aktualisierung alle fünf Sekunden und zweistufiges Löschen mit
  Rückstellung nach fünf Sekunden.
- Sprechende Ersteller-Tags, manuell am Receiver verwendbar; alte Kennungen bleiben gültig.
- systemd-Installer, nginx-Vorlage und HTTPS-Betrieb hinter einem vorhandenen Proxy.
- GitHub-Unterlagen mit CI-Workflow und vorbereiteter Git-Historie samt `v1.1.11`.

## Installation und Update

Das Installationspaket `enigma2-web-v1.1.11.zip` entpacken und im enthaltenen
Projektverzeichnis als root `bash scripts/install.sh` ausführen.
Bei Neuinstallation danach einen Administrator anlegen und `e2web` aktivieren;
bei vorhandener Installation werden Konten, Receiver, Konfiguration, Datenbank
und Schlüssel weiterverwendet. Einzelheiten: [INSTALL.md](INSTALL.md).

Das Update von 0.8.0 bis 1.1.10 auf 1.1.11 benötigt keine neue Schemaänderung
und verändert keine Timer oder Aufnahmedateien auf Receivern. Vorhandene
Konfiguration, einschließlich eines geänderten Ports, wird erhalten.

## Prüfung

344 automatisierte Tests, Code-/Formatprüfung, JavaScript-/Installer-Syntax,
Browserprüfung mit JSON- und XML-Receivern bei fünf Bildschirmbreiten, Paketbau
und Start des installierten Wheels; Prüfergebnisse stehen in
[VERIFICATION.md](VERIFICATION.md).
Die Speicherabfrage wurde mit simulierten Receivern und anhand der primären
JSON-/XML-Felddefinitionen geprüft. Die Prüfung an der jeweiligen Hardware
folgt nach der Installation. Das Installationspaket enthält keine Betriebsdaten
oder Zugangsdaten.

## GitHub

`enigma2-web-git-v1.1.11.zip` enthält das vorbereitete Repository mit Branch `main`
und Tag `v1.1.11`. Alle bisherigen bereinigten Tags einschließlich `v1.1.10`
bleiben auf ihren bisherigen Ständen. Ein gewöhnlicher Push von `main` und
`v1.1.11` genügt; der vorige Tag `v1.1.10` kann dabei mit übertragen werden,
falls er noch nicht auf GitHub vorhanden ist. Quellstand und Installationspaket
sind identisch. Anleitung: [GITHUB.md](GITHUB.md).
Lizenz- und Herkunftsangaben: [NOTICE.md](NOTICE.md).
