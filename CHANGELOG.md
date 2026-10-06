# Versionsverlauf

## 1.1.7 – 06.10.2026

- Bei unbekanntem Standardaufnahmeordner automatisch den ersten Eintrag der
  alphabetisch sortierten Ordnerliste auswählen und dessen Aufnahmen laden.
- Lesbaren Standard und manuelle Auswahl weiterhin bevorzugen; angezeigten
  Ordner bei der automatischen Aktualisierung beibehalten.
- Fehlermeldung bei unbekanntem Standard nur, wenn keine auswählbaren
  Aufnahmepfade vorhanden sind. JSON und XML unterstützt.
- Keine neue Migration, keine neuen Abhängigkeiten oder Receiveränderungen.

## 1.1.6 – 06.10.2026

- Aufnahmen starten mit `config.usage.default_path` aus der Receiver-Konfiguration
  über JSON-/XML-`settings`; der zuletzt lokal geöffnete Ordner ist kein Standard.
- Standardpfad ausdrücklich vor `movielist` festlegen, auch ohne Bookmark;
  unlesbaren Standard melden und eine ausdrückliche Ordnerauswahl ermöglichen.
- Sichtbaren Aufnahmeordner bei der Fünf-Sekunden-Aktualisierung festhalten.
- Seitenrahmen für Timer, Aufnahmen, Sender, EPG und Timerformulare sofort laden;
  bis zur vollständigen Antwort „Lade Daten von Receiver...“ anzeigen.
- Receiverbindung, Fehlermeldungen, erneuter Leseversuch und JavaScript-Fallback;
  nachgeladenen Formularen und Filtern ihre Bedienfunktionen zuweisen.
- Ladehinweis auch bei Bouquetwechsel und während bestehender Receiveraufträge.
- Keine neue Migration, keine Änderung von Abhängigkeiten oder Receiverdaten.

## 1.1.5 – 05.10.2026

- Receiverauswahl auf Timer-, Sender-, Aufnahme- und EPG-Seiten um etwa
  50 Prozent verbreitert; auf schmalen Bildschirmen an den verfügbaren Platz angepasst.
- Vertikale Innenabstände in den Auswahl- und Filterfeldern reduziert, damit
  Unterlängen wie bei „g“ vollständig sichtbar sind. Einheitliche Feldhöhe erhalten.
- Haupttitel unverändert, aktiven Receiver ohne Doppelpunkt und nach einem
  Leerzeichen mit halber Schriftgröße daneben anzeigen. Auch Timer erstellen,
  bearbeiten und Auftragsprüfung sowie Sender-EPG berücksichtigen.
- Keine Änderung am Datenbankschema oder an Receiveraufträgen.

## 1.1.4 – 04.10.2026

- Standardaufnahmeordner vor dem ersten Laden der Dateien ermitteln und an
  `movielist` übergeben. Ordnerauswahl und Aufnahmeliste stimmen dadurch auch
  bei `/media/usb/` und fehlender Standardangabe in `getlocations` überein.
- Gleiche Pfadauflösung bei automatischer Aktualisierung, Ordnerwechseln und
  Downloads; JSON- und XML-Antworten berücksichtigt.
- Vorhandene Pfadprüfung einschließlich vom Receiver bestätigter Symlinkpfade
  erhalten; keine neue Migration und keine Änderungen auf dem Receiver.

## 1.1.3 – 04.10.2026

- Favicon-Dateien erhalten einen speicherbaren Cache-Header, damit Firefox sie
  für Lesezeichen übernehmen kann. Andere Antworten behalten `no-store`.
- Öffentlicher Standardpfad `/favicon.ico` für GET und HEAD, auch vor Anmeldung
  oder während eines erzwungenen Passwortwechsels.
- Echte ICO-Datei mit dem vorhandenen Logo in 16, 32 und 48 Pixeln;
  versionierter Verweis in allen Seiten.
- Bereinigte Git-Historie und alle bisherigen Tags fortgeführt; keine Migration.

## 1.1.2 – 04.10.2026

- Private Netzwerkadressen im Receiverformular und in Tests durch neutrale Beispiele ersetzt.
- Alle drei bisherigen Git-Release-Stände bereinigt, einschließlich annotierter Tags.
- PowerShell-Skript für die einmalige GitHub-Umstellung mit Prüfung des bekannten
  Remote-Stands, expliziten Leases und atomarer Aktualisierung.
- Keine neue Migration; gespeicherte Verbindungen und alle Funktionen bleiben erhalten.

## 1.1.1 – 04.10.2026

- Timer-Kopfzeile in der Reihenfolge Receiverauswahl, „Liste filtern“, „Timer erstellen“.
- Filterfelder bei Timern, Sendern und Aufnahmen exakt so hoch wie die Receiverauswahl,
  auch in der mobilen Ansicht.

## 1.1.0 – 04.10.2026

- Timerfilter links neben der Receiverauswahl nach Sender und Timer-Titel.
- Aufnahmefilter rechts neben der Ordnerauswahl nach Sender, Dateiname und Titel.
- Filterzustand, Eingabefokus und Cursorposition bleiben beim automatischen
  Aktualisieren erhalten; Dateizeilen folgen ihrem zugehörigen Eintrag.
- Timer-Zähler nennen die Anzahl der passenden Einträge des jeweiligen Bereichs.
- Filterbeschriftungen stehen direkt in den Eingabefeldern.
- Einheitliche Beschriftung „Timer erstellen“ in Timerbereich, Sendern und EPG.
- Datenbankschema weiterhin Revision `0005`; Update von 1.0.0 ohne Schemaänderung.

## 1.0.0 – 03.10.2026

- Erste Version der 1.0-Reihe auf dem Funktionsstand von 0.8.0.
- Installationspaket für Ubuntu/Debian und vorbereitetes Git-Repository für GitHub.
- Eigene Installationsanleitung, Release-Hinweise und GitHub-Anleitung.
- GitHub Actions für Codeprüfung, Tests und Paketbau mit Python 3.12.
- Git-Dateiregeln für Linux-Skripte auch bei einem Checkout unter Windows.
- Getrennte Verwaltung von Quellcode und lokalen Konfigurations-/Betriebsdaten.
- Datenbankschema weiterhin Revision `0005`; kompatibles Update von 0.8.0.

## 0.8.0 – 03.10.2026

- Sprechende Ersteller-Tags wie `e2web-owner-digiandi` und
  `e2web-owner-thomas.meyer`, manuell am Receiver verwendbar.
- Taganzeige in der Benutzerverwaltung; Registrierung aller bestehenden Konten
  durch Migration `0005` und neuer Konten beim Anlegen.
- Unterstützung alter zufälliger Kennungen und Umstellung beim Bearbeiten.
- Schutz gegen Übernahme alter Rechte bei wiederverwendeten Kontonamen.

## 0.7.3 – 03.10.2026

- Letzte erfolgreiche Anmeldung in der Benutzerübersicht.
- Aufnahmepfade und Unterordner in einer gemeinsamen Ordnerauswahl.

## 0.7.2 – 03.10.2026

- Dateinamen und Größen im Timerbereich ausschließlich bei laufenden Timern.
- Erstelleranzeige „von …“ bei Timern und Aufnahmen.
- Hinweis zum Beenden laufender Aufnahmen entfernt.

## 0.7.1 – 03.10.2026

- Korrektur der Standardpfad-Abfrage über das ältere XML-WebInterface.
- Gemeinsame Auswahlzeile bei Sendern; Aufnahmen ohne manuellen Neu-laden-Button.

## 0.7.0 – 03.10.2026

- Direkte Timeranlage mit gemeinsamer TV-/Radio-Bouquetauswahl.
- Timerbereiche Laufend/Anstehend, Dateizeilen und Sender-/Bouquetangaben.
- Seitenname Enigma2 Timer, angepasste Kopfzeile und bündige Zeitfelder.

## 0.6.1 – 03.10.2026

- Korrektur bestätigter abweichender Aufnahmepfade nach dem Löschen.

## 0.6.0 – 03.10.2026

- Eigentümerrechte, Schutz laufender Aufnahmen und automatische Aktualisierung.
- Administratoren mit Schreibrechten auf alle aktivierten Receiver.

Frühere Funktionen und die zugehörigen Prüfungen sind in
[VERIFICATION.md](VERIFICATION.md) und [README.md](README.md) dokumentiert.
