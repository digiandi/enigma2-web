# Versionsverlauf

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
