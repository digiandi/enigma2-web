# Enigma2 Timer 1.1.2

Release: 04.10.2026 · Git-Tag: `v1.1.2` · Datenbankschema: `0005`

Zentrale Timer- und Aufnahmen-Verwaltung für mehrere Enigma2-Receiver über
OpenWebif oder das ältere XML-WebInterface, mit deutscher Oberfläche im AWAS-Stil.

## Neu in 1.1.2

- Private Netzwerkadressen aus dem Receiverformular und den Tests entfernt;
  Beispiele verwenden reservierte Dokumentationsadressen und `example.test`.
- Auch die Git-Historie mit `v1.0.0`, `v1.1.0` und `v1.1.1` ist bereinigt.
  Deren Commit- und Tag-Kennungen ändern sich. Ein geprüftes PowerShell-Skript
  ersetzt den bisher bestätigten GitHub-Stand; siehe [GITHUB.md](GITHUB.md).
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
- Timer erstellen, bearbeiten, deaktivieren und löschen; wiederkehrende Termine
  und Vor-/Nachlauf aus dem EPG.
- Aufnahmen mit Ordnerauswahl, Dateigröße, Status, Ersteller und Downloads.
- Benutzer-/Receiververwaltung mit Standardreceiver und getrennten Lese-/Schreibrechten.
- Benutzer bearbeiten/löschen eigene Einträge; laufende Aufnahmen bleiben geschützt.
- Automatische Aktualisierung alle fünf Sekunden und zweistufiges Löschen mit
  Rückstellung nach fünf Sekunden.
- Sprechende Ersteller-Tags, manuell am Receiver verwendbar; alte Kennungen bleiben gültig.
- systemd-Installer, nginx-Vorlage und HTTPS-Betrieb hinter einem vorhandenen Proxy.
- GitHub-Unterlagen mit CI-Workflow und vorbereiteter Git-Historie samt `v1.1.2`.

## Installation und Update

Das Installationspaket `enigma2-web-v1.1.2.zip` entpacken und im enthaltenen
Projektverzeichnis als root `bash scripts/install.sh` ausführen.
Bei Neuinstallation danach einen Administrator anlegen und `e2web` aktivieren;
bei vorhandener Installation werden Konten, Receiver, Konfiguration, Datenbank
und Schlüssel weiterverwendet. Einzelheiten: [INSTALL.md](INSTALL.md).

Das Update von 0.8.0 bis 1.1.1 auf 1.1.2 benötigt keine neue Schemaänderung
und verändert keine Timer oder Aufnahmedateien auf Receivern. Vorhandene
Konfiguration, einschließlich eines geänderten Ports, wird erhalten.

## Prüfung

235 automatisierte Tests, Code-/Formatprüfung, Paketbau und Start des gebauten
Wheels mit Migration und Health-Endpunkt. Alle Git-Objekte und früheren
Release-Stände auf verbliebene private Netzwerkadressen geprüft. Die geschützte
Git-Aktualisierung wurde mit lokalen Repositories einschließlich Abbruch bei
geänderten Remote-Ständen geprüft. Die bisherigen Browserprüfungen der Oberfläche
sind in [VERIFICATION.md](VERIFICATION.md) dokumentiert.

Das Installationspaket enthält keine Betriebsdaten oder Zugangsdaten. Für die
Prüfung an der eingesetzten Hardware steht nach Installation der Verbindungstest
in der Receiververwaltung zur Verfügung.

## GitHub

`enigma2-web-git-v1.1.2.zip` enthält das vorbereitete Repository mit Branch `main`
und Tag `v1.1.2`. Die früheren Tags `v1.0.0`, `v1.1.0` und `v1.1.1`
zeigen auf die entsprechenden bereinigten Release-Stände.
Quellstand und Installationspaket sind identisch.
Anleitung: [GITHUB.md](GITHUB.md). Lizenz- und Herkunftsangaben: [NOTICE.md](NOTICE.md).
