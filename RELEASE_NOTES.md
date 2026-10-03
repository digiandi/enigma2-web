# Enigma2 Timer 1.0.0

Release: 03.10.2026 · Git-Tag: `v1.0.0` · Datenbankschema: `0005`

Zentrale Timer- und Aufnahmen-Verwaltung für mehrere Enigma2-Receiver über
OpenWebif oder das ältere XML-WebInterface, mit deutscher Oberfläche im AWAS-Stil.

## Enthalten

- Senderlisten mit TV-/Radio-Bouquets und Anbietern sowie EPG pro Sender.
- Timer anlegen, bearbeiten, deaktivieren und löschen; wiederkehrende Termine
  und Vor-/Nachlauf aus dem EPG.
- Aufnahmen mit Ordnerauswahl, Dateigröße, Status, Ersteller und Downloads.
- Benutzer-/Receiververwaltung mit Standardreceiver und getrennten Lese-/Schreibrechten.
- Benutzer bearbeiten/löschen eigene Einträge; laufende Aufnahmen bleiben geschützt.
- Automatische Aktualisierung alle fünf Sekunden und zweistufiges Löschen mit
  Rückstellung nach fünf Sekunden.
- Sprechende Ersteller-Tags, manuell am Receiver verwendbar; alte Kennungen bleiben gültig.
- systemd-Installer, nginx-Vorlage und HTTPS-Betrieb hinter einem vorhandenen Proxy.
- GitHub-Unterlagen mit CI-Workflow und vorbereiteter Git-Historie samt `v1.0.0`.

## Installation und Update

Das Installationspaket `enigma2-web-v1.0.0.zip` entpacken und im enthaltenen
Projektverzeichnis als root `bash scripts/install.sh` ausführen.
Bei Neuinstallation danach einen Administrator anlegen und `e2web` aktivieren;
bei vorhandener Installation werden Konten, Receiver, Konfiguration, Datenbank
und Schlüssel weiterverwendet. Einzelheiten: [INSTALL.md](INSTALL.md).

Funktionsstand wie 0.8.0. Das Update von 0.8.0 auf 1.0.0 benötigt keine neue
Schemaänderung und verändert keine Timer oder Aufnahmedateien auf Receivern.

## Prüfung

235 automatisierte Tests, Code-/Formatprüfung, Paketbau sowie Start der gebauten
Installation mit Migration und Health-Endpunkt. JSON- und XML-Antworten werden
mit simulierten Receivern geprüft. Einzelheiten: [VERIFICATION.md](VERIFICATION.md).

Das Installationspaket enthält keine Betriebsdaten oder Zugangsdaten. Für die
Prüfung an der eingesetzten Hardware steht nach Installation der Verbindungstest
in der Receiververwaltung zur Verfügung.

## GitHub

`enigma2-web-git-v1.0.0.zip` enthält das vorbereitete Repository mit Branch `main`
und Tag `v1.0.0`. Quellstand und Installationspaket sind identisch.
Anleitung: [GITHUB.md](GITHUB.md). Lizenz- und Herkunftsangaben: [NOTICE.md](NOTICE.md).
