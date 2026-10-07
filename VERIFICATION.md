# Prüfung von Version 1.1.12

Prüfstand: 07.10.2026, Python 3.12 unter Linux.

- 344 automatisierte Tests erfolgreich. Code- und Formatprüfung sowie
  Installer-Syntax erfolgreich.
- Browservergleich der Ordnerauswahl mit der bisherigen flexiblen Breite bei
  320, 390, 720, 768, 1024 und 1440 Pixeln Bildschirmbreite. JSON und XML,
  jeweils eine und zwei Festplatten: 24 Ansichten geprüft.
- Über 720 Pixeln beträgt die Feldbreite 50 Prozent des bisherigen Werts
  innerhalb der Rundung auf Bildschirm-Teilpixel. Bei 1440 Pixeln beispielsweise
  277,23 statt 554,50 Pixel. Bis einschließlich 720 Pixel bleibt die bisherige
  mobile Breite erhalten.
- Festplattenangaben beginnen weiterhin direkt rechts neben dem Dropdown und
  bei mehreren Festplatten am gleichen linken Rand untereinander. Keine
  horizontale Überbreite. Desktop- und Mobilansicht zusätzlich visuell geprüft.
- Ordnerwechsel, automatische Aktualisierung, Filtertext und Fokus, Ladeanzeige,
  teilweise und vollständig unbekannter Speicher sowie Aufruf ohne JavaScript
  im Browser geprüft. Keine JavaScript-Fehler, Dialoge oder Receiver-Schreibaufträge
  für diese Darstellung.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.12 und Release-Datum 07.10.2026. CLI-Initialisierung erhält Schlüssel,
  geänderten Port und Aufnahmezeitlimit von 90 Sekunden; Schema `0005`.
  Login, Assets, Favicon, Seitenrahmen, Standardordner, Ordner-Fallback,
  JSON-/XML-Festplattenanzeige, Download und eigenständige Timerkopie geprüft.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Paketbau aus
  dem finalen Installations-ZIP hat identische Inhalte zum geprüften Paketbau.
  Keine Betriebsdaten oder Zugangsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.12`, dreizehn unveränderte bisherige
  Tags, `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle
  Archivdateien und Git-Objekte weiterhin ohne die entfernten Netzwerkbeispiele.
- Hardwareprüfung, GitHub-Push und GitHub-CI wurden nicht ausgeführt; die
  bestehende Ubuntu-Installation wurde nicht geändert. Receiver-Antworten sind
  in dieser Prüfung simuliert.

## Änderungen 1.1.12

- Ordnerauswahl auf größeren Bildschirmen gegenüber 1.1.11 auf die Hälfte verkleinern.
- Mobile Feldbreite und bündige Festplattenangaben beibehalten.
- Keine neue Migration oder Abhängigkeit; Datenbankschema weiterhin `0005`.

## Prüfung von Version 1.1.11

Prüfstand: 07.10.2026, Python 3.12 unter Linux.

- 344 automatisierte Tests erfolgreich, darunter 34 Speicherplatzprüfungen.
  Code- und Formatprüfung sowie JavaScript- und Installer-Syntax erfolgreich.
- JSON-`deviceinfo` mit `hdd` und XML-`deviceinfo` mit `e2hdds/e2hdd` geprüft.
  Beide Formate liefern alle Festplatten mit Modell und freiem Speicher auch ohne
  Einhängepunkt oder Ordnerzuordnung. Zusätzliche Tuner-Modellnamen werden nicht
  als Festplatten gelesen.
- Werte einschließlich `660.884 GB`, `0 MB`, Dezimalkomma und anderer
  unterstützter Einheiten geprüft; Ausgabe in GB mit höchstens drei
  Nachkommastellen. Fehlende, negative oder unlesbare Werte ergeben pro Festplatte
  **unbekannt**, ohne andere lesbare Festplatten auszublenden. Fehlende Modellnamen
  und fehlende bzw. ungültige Festplattenlisten ebenfalls geprüft.
- HTTP-Fehler, Zeitüberschreitung und ungültige JSON-/XML-Antworten der optionalen
  Speicherabfrage lassen Aufnahmeliste, Download und zulässiges Löschen verfügbar.
  Speicherabfrage mit Aufnahme-Lesezeitlimit von standardmäßig 90 Sekunden.
- Browserprüfung mit JSON und XML bei 320, 390, 768, 1024 und 1440 Pixeln Breite:
  zwanzig Ansichten mit einer bzw. zwei Festplatten. Anzeige direkt rechts neben
  dem Ordner-Dropdown, jede Festplatte in einer eigenen Zeile mit gleicher linker
  Position. Mobil darf der Text innerhalb der Zeile umbrechen; keine horizontale
  Überbreite. Desktop- und Mobilansicht zusätzlich visuell geprüft.
- Ordnerwechsel zwischen HDD, USB und Netzwerkpfad im Browser geprüft. Alle
  Festplatten bleiben unabhängig vom gewählten Ordner sichtbar. Die automatische
  Fünf-Sekunden-Aktualisierung erneuert die Werte; Filtertext und Fokus bleiben
  erhalten. Teilweise und vollständig unbekannte Angaben sowie der direkte
  Aufruf ohne JavaScript geprüft. Keine JavaScript-Fehler oder Dialoge.
- Verzögerte Speicherantworten erhalten den sofortigen Seitenrahmen mit Ladehinweis.
  Für die Speicheranzeige wurde kein Receiver-Schreibauftrag ausgeführt.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.11 und Release-Datum 07.10.2026. CLI-Initialisierung erhält Schlüssel,
  geänderten Port und Zeitlimit; Schema `0005`. Login, Assets, Favicon,
  Seitenrahmen, Standardordner, Ordner-Fallback, JSON-/XML-Festplattenanzeige,
  Download und eigenständige Timerkopie geprüft.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Paketbau aus
  dem finalen Installations-ZIP hat identische Inhalte zum geprüften Paketbau.
  Keine Betriebsdaten oder Zugangsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.11`, zwölf unveränderte bisherige
  Tags, `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle
  Archivdateien und Git-Objekte weiterhin ohne die entfernten Netzwerkbeispiele.
- Die Prüfung verwendet simulierte Receiver. Hardwareprüfung, GitHub-Push und
  GitHub-CI wurden nicht ausgeführt; die bestehende Ubuntu-Installation wurde
  nicht geändert.

## Änderungen 1.1.11

- Freier Speicher und Festplattenname für alle vom Receiver gemeldeten Festplatten.
- Die Ordner- und Mountzuordnung aus 1.1.10 entfällt. JSON und ältere XML-
  Festplattenlisten werden gelesen; mehrere Anzeigen beginnen bündig untereinander.
- Automatische Aktualisierung und mobile Darstellung. Keine neue Migration
  oder Abhängigkeit; Datenbankschema weiterhin `0005`.

Primäre Feldreferenzen:
[OpenWebif-Geräteinformationen](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/models/info.py),
[WebInterface-XML](https://github.com/oe-alliance/enigma2-plugins/blob/master/webinterface/src/web/deviceinfo.xml),
[WebInterface-Festplattenwerte](https://github.com/oe-alliance/enigma2-plugins/blob/master/webinterface/src/WebComponents/Sources/Hdd.py).
Feldnamen und Speicherformat wurden am primären Quellcode geprüft;
kein Quellcode dieser Projekte wird eingebunden.

## Prüfung von Version 1.1.10

Prüfstand: 07.10.2026, Python 3.12 unter Linux.

- 340 automatisierte Tests erfolgreich, darunter 30 neue Speicherplatzprüfungen.
  Code- und Formatprüfung sowie JavaScript- und Installer-Syntax erfolgreich.
- Speicherplatz aus JSON-`deviceinfo` geprüft: mehrere Datenträger, Unterordner,
  ein verschachtelter Einhängepunkt, ähnliche Pfadnamen, fehlende Mountangaben,
  widersprüchliche Werte und nicht bestätigte Symlinkpfade.
- Gültige Werte einschließlich `0 MB` bleiben sichtbar. Fehlende, negative,
  unlesbare oder nicht zuordenbare Werte ergeben **unbekannt**. XML-Antworten
  ohne implementierte Mountzuordnung ebenfalls. Es wird keine Dateigröße zur
  Schätzung verwendet und kein erster Datenträger pauschal angenommen.
- HTTP-Fehler, Zeitüberschreitung und ungültige Antworten der optionalen
  Speicherabfrage lassen Aufnahmeliste, Download und zulässiges Löschen verfügbar.
  Speicherabfrage mit Aufnahme-Lesezeitlimit von standardmäßig 90 Sekunden.
- Browserprüfung bei 320, 390, 720, 768, 1024 und 1440 Pixeln Breite: zwölf
  Ansichten mit bekanntem bzw. unbekanntem Speicher. Anzeige direkt rechts neben
  dem Dropdown und vertikal mittig, auch mobil; keine horizontale Überbreite.
  Desktop zeigt Beschriftung und Wert in einer Zeile, mobil darf der Text umbrechen.
- Ordnerwechsel zwischen HDD, USB und nicht zuordenbarem Netzwerkpfad im Browser
  geprüft. Freier Speicher folgt der Auswahl und der Fünf-Sekunden-Aktualisierung;
  Filtertext und Fokus bleiben erhalten. Keine JavaScript-Fehler oder Dialoge.
- Verzögerte Speicherantworten erhalten den sofortigen Seitenrahmen mit Ladehinweis.
  Erster HTML-Aufruf in der Browserprüfung unter 0,1 Sekunden. Direkter Aufruf
  ohne JavaScript zeigt ebenfalls den Speicherwert.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.10 und Release-Datum 07.10.2026. Initialisierung erhält Schlüssel, geänderten
  Port und Zeitlimit; Schema `0005`. Login, Assets, Favicon, Seitenrahmen,
  Standardordner, Ordner-Fallback, Speicheranzeige und eigenständige Timerkopie geprüft.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Paketbau aus
  dem finalen Installations-ZIP hat identische Inhalte zum geprüften Paketbau.
  Keine Betriebsdaten oder Zugangsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.10`, elf unveränderte bisherige
  Tags, `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle
  Archivdateien und Git-Objekte weiterhin ohne die entfernten Netzwerkbeispiele.
- Die Prüfung verwendet simulierte Receiver; kein Receiver-Schreibauftrag für
  die Speicheranzeige. Hardwareprüfung, GitHub-Push und GitHub-CI wurden nicht
  ausgeführt; die bestehende Ubuntu-Installation wurde nicht geändert.

## Änderungen 1.1.10

- Freier Speicherplatz direkt neben der Ordnerauswahl auf **Aufnahmen**.
- Ordnerbezogene Zuordnung mit JSON-Geräteinformationen; **unbekannt** bei
  fehlender Zuordnung oder nicht verfügbarer Angabe.
- Automatische Aktualisierung und mobile Darstellung. Keine neue Migration
  oder Abhängigkeit; Datenbankschema weiterhin `0005`.

Primäre Feldreferenz:
[OpenWebif-Geräteinformationen](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/models/info.py).
Die Felder `hdd`, `mount` und `free` wurden am primären Quellcode geprüft;
kein OpenWebif-Quellcode wird eingebunden.

## Prüfung von Version 1.1.9

Prüfstand: 07.10.2026, Python 3.12 unter Linux.

- 310 automatisierte Tests erfolgreich. Code- und Formatprüfung sowie
  JavaScript- und Installer-Syntax erfolgreich.
- Echter CLI-Start geprüft mit von `e2web init` erzeugter Konfiguration,
  Konfiguration ohne `host` und Installationsvorlage. Alle drei Fälle binden
  an `0.0.0.0`; der tatsächlich geöffnete TCP-Listener wurde geprüft.
- HTTP-Health- und Login-Abfragen über `127.0.0.1` und die zusätzliche lokale
  IPv4-Adresse `127.0.0.2` erfolgreich. Eine ausdrücklich konfigurierte Bindung
  an `127.0.0.1` lässt sich weiterhin verwenden; der zweite Zugriff bleibt
  dann erwartungsgemäß unerreichbar. Die Prüfumgebung hat keine weitere IPv4-
  Netzwerkschnittstelle; der Zugriff von einem anderen Rechner wurde nicht ausgeführt.
- Erneute Initialisierung erhält ausdrücklich gesetzte Bindung, geänderten Port,
  Konfigurationsdatei und Schlüssel. Port weiterhin standardmäßig 8081,
  Aufnahmezeitlimit 90 Sekunden, Datenbankschema `0005`.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.9 und Release-Datum 07.10.2026; dieselben CLI-Bindungsprüfungen erfolgreich.
  Login, Assets, Favicon, Ladevorlagen, Standardordner, Ordner-Fallback und
  eigenständige Timerkopie mit simuliertem Receiver geprüft.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Paketbau aus
  dem finalen Installations-ZIP hat identische Inhalte zum geprüften Paketbau.
  Keine Betriebsdaten oder Zugangsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.9`, zehn unveränderte bisherige
  Tags, `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle
  Archivdateien und Git-Objekte weiterhin ohne die entfernten Netzwerkbeispiele.
- GitHub-Push und GitHub-CI wurden nicht ausgeführt; die bestehende Installation
  auf dem Ubuntu-Server wurde aus dieser Entwicklungsumgebung nicht geändert.

## Änderungen 1.1.9

- Standardbindung in Programm, Konfigurations-Fallback, `e2web init` und
  Installationsvorlage auf `0.0.0.0` umstellen.
- Direkten Aufruf über die Server-IP und Änderung vorhandener Konfigurationen
  dokumentieren. Keine neue Migration oder Abhängigkeit.

## Prüfung von Version 1.1.8

Prüfstand: 06.10.2026, Python 3.12 unter Linux.

- 310 automatisierte Tests erfolgreich, darunter 24 neue Kopierprüfungen.
  Code- und Formatprüfung sowie JavaScript- und Installer-Syntax erfolgreich.
  Bestehende Rechte-, Eigentümer-, Pfad-, Standardordner- und Faviconprüfungen
  bleiben erfolgreich. Der Ladeanzeige-Test verwendet jetzt dieselbe Timeridentität
  wie der simulierte Receiver, auch bei einer Sekundengrenze während der Anmeldung.
- JSON und XML: TV- und Radio-Sender, Name, mehrzeilige Beschreibung,
  sekundengenaue Zeiten, Wiederholung, deaktivierter Zustand und eigener
  Aufnahmepfad korrekt vorausgefüllt. Timerart und Endaktion anpassbar;
  vom jeweiligen Receiver gelieferte Zusatzoptionen bleiben erhalten.
- Speichern erstellt einen unabhängigen `timeradd`-Auftrag mit genau einem
  aktuellen Ersteller-Tag; gewöhnliche Tags bleiben erhalten, ursprüngliche
  Ersteller-Tags entfallen. Keine Änderungsparameter, keine Mutation der Vorlage
  und kein erneutes Senden durch Wiederverwendung eines Formularauftrags.
- Schreibrechte erlauben das Kopieren sichtbarer fremder Vorlagen. Leserechte,
  widerrufene Freigaben, andere Sitzungen, falsche Receiver und ungültige Sender
  werden serverseitig geprüft. Laufende, erledigte, entfernte oder mehrdeutige
  Vorlagen öffnen keinen Kopierentwurf. Ein bereits geöffneter Entwurf bleibt
  nach Entfernen seiner Vorlage ein eigenständiger Erstellauftrag.
- Duplikat- und Receiverkonfliktmeldungen erhalten den anpassbaren Entwurf.
  Sender außerhalb von Bouquets bleiben über die an den Entwurf gebundene
  ursprüngliche Auswahl verfügbar. Zeitumstellung und Sekunden bleiben erhalten.
- Browserprüfung mit verzögerten JSON-/XML-Antworten bei 390, 1024 und 1440
  Pixeln Breite: sechs Ansichten der Timerliste und des kopierten Formulars.
  Buttonfolge Bearbeiten/Kopieren/Löschen; sofortige Ladeanzeige, korrekt
  vorausgefüllte Felder, Abbrechen ohne Schreibauftrag und keine horizontale
  Überbreite der Seite. Mobile Buttons stehen in derselben Reihenfolge untereinander.
- Im Browser nach Duplikatmeldung Sender/Bouquet, Titel, Beschreibung, Beginn,
  Ende, Wiederholung, Pfad, Deaktivierung, Timerart und Endaktion geändert.
  Je JSON-/XML-Receiver genau ein Erstellauftrag, Vorlage unverändert.
  Keine JavaScript-Fehler oder Dialoge. Kopierformular ohne JavaScript geladen.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.8 und Schema `0005`; Login, Assets, Favicon, Ladevorlagen, Standardordner,
  Ordner-Fallback und Timerkopie geprüft. Erneute Initialisierung erhält Schlüssel,
  geänderten Port und Aufnahmezeitlimit von 90 Sekunden.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Paketbau aus
  dem finalen Installations-ZIP hat identische Inhalte zum geprüften Paketbau.
  Keine Betriebsdaten oder Zugangsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.8`, neun unveränderte bisherige
  Tags, `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle
  Archivdateien und Git-Objekte weiterhin ohne die entfernten Netzwerkbeispiele.
- Die Prüfung verwendet simulierte Receiver. GitHub-Push und GitHub-CI wurden
  nicht ausgeführt; Receiverkonfigurationen und Aufnahmedateien auf der
  eingesetzten Hardware wurden aus dieser Entwicklungsumgebung nicht geändert.

## Änderungen 1.1.8

- Anstehende Timer als vorausgefüllten neuen Entwurf kopieren.
- Eigenständiger Erstellauftrag mit Erstellerzuordnung und unveränderter Vorlage.
- Keine neue Migration oder Abhängigkeit; Schema weiterhin `0005`.

## Prüfung von Version 1.1.7

Prüfstand: 06.10.2026, Python 3.12 unter Linux.

- 286 automatisierte Tests erfolgreich; Code- und Formatprüfung erfolgreich.
  JavaScript- und Installer-Syntax geprüft. Bestehende Rechte-, Eigentümer-,
  Pfad-, Favicon- und Auftragsprüfungen bleiben erfolgreich.
- Fallback mit JSON und XML geprüft: nicht verfügbarer Settings-Endpunkt,
  fehlende Einstellung und ungültiger Standardpfad. Ein oder mehrere angebotene
  Ordner, unsortierte Reihenfolge und doppelte Einträge berücksichtigt.
  Der erste alphabetisch sortierte Ordner ist ausgewählt, seine Dateien sind
  geladen und `movielist` erhält dessen Pfad ausdrücklich.
- Konfigurierter Standard hat weiterhin Vorrang, auch ohne Bookmark. Manuelle
  Ordnerauswahl und automatische Aktualisierung behalten den angezeigten Pfad.
  Ohne angebotene Ordner erscheint eine klare Fehlermeldung; kein impliziter
  Zugriff auf den zuletzt lokal geöffneten Ordner.
- Browserprüfung mit verzögerten JSON-/XML-Antworten bei 390 und 1440 Pixeln
  Breite: vier Fallback-Ansichten erfolgreich. Sofortiger Ladehinweis,
  anschließend ausgewählter erster Ordner und dessen Aufnahmen; keine
  horizontale Überbreite, JavaScript-Fehler, Dialoge oder Schreibaufträge.
- Im Browser zusätzlich Ordnerwechsel, Neuladen, Filter und automatische
  Größenaktualisierung geprüft. Neue Bookmarks ändern die aktive Auswahl erst
  beim frischen Menüaufruf. Ein wieder lesbarer Standard wird dann bevorzugt.
  Fehler bei fehlender Ordnerliste und Fallback ohne JavaScript ebenfalls geprüft.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.7 und Schema `0005`; Login, Ladevorlagen, Assets, Favicon, Standardordner
  und Ordner-Fallback erfolgreich. Erneute Initialisierung erhält Schlüssel,
  geänderten Port und Aufnahmezeitlimit von 90 Sekunden.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Paketbau aus
  dem finalen Installations-ZIP hat identische Inhalte zum geprüften Paketbau.
  Keine Betriebsdaten oder Zugangsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.7`, acht unveränderte bisherige
  Tags, `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle
  Archivdateien und Git-Objekte weiterhin ohne die entfernten Netzwerkbeispiele.
- Die Prüfung verwendet simulierte Receiver. GitHub-Push und GitHub-CI wurden
  nicht ausgeführt; Receiverkonfigurationen und Aufnahmedateien auf der
  eingesetzten Hardware wurden aus dieser Entwicklungsumgebung nicht geändert.

## Änderungen 1.1.7

- Bei unbekanntem Standard automatisch den ersten angebotenen Ordner laden.
- Meldung bei fehlendem Standard an eine ebenfalls fehlende Ordnerliste angepasst.
- Keine Änderung am Datenbankschema, an Abhängigkeiten oder Receiveraufträgen.

## Prüfung von Version 1.1.6

Prüfstand: 06.10.2026, Python 3.12 unter Linux.

- 276 automatisierte Tests erfolgreich; Code- und Formatprüfung erfolgreich.
  Installer- und JavaScript-Syntax geprüft. Die bestehenden Rechte-, Eigentümer-,
  Pfad-, Favicon- und Auftragsprüfungen bleiben erfolgreich.
- Standardaufnahmeordner über `settings` geprüft: offizielles JSON-Format mit
  Schlüssel-/Wertpaaren, kompatible Objekteinträge und das ältere XML-Format.
  Maßgeblich ist ausschließlich `config.usage.default_path`; ein abweichender
  lokaler Ordner und ein abweichendes `default` aus `getlocations` werden ignoriert.
- Erstaufruf mit und ohne Bookmark des konfigurierten Standards geprüft.
  `movielist` erhält diesen Pfad ausdrücklich. Fehlende, ungültige oder
  widersprüchliche Standards ergeben eine verständliche Meldung und eine
  ausdrückliche Ordnerauswahl; kein impliziter oder erratener Startordner.
- Seitenrahmen für Timer, Aufnahmen, Sender, EPG sowie Timer erstellen und
  bearbeiten antworten ohne Receiveranfrage. Nachladen ist an den ausgewählten,
  weiterhin berechtigten Receiver gebunden. Gewechselte Receiver und entzogene
  Berechtigungen verhindern eine unpassende Datenabfrage.
- Browserprüfung dieser sechs Seiten mit absichtlich verzögerten JSON- und
  XML-Antworten bei 390 und 1440 Pixeln Breite: 24 Ansichten erfolgreich.
  Ladehinweis und Navigation sofort sichtbar, Daten nach vollständiger Antwort,
  keine horizontale Überbreite, keine JavaScript-Fehler oder Dialoge.
  Erneut versuchen wird ausschließlich nach einem fehlgeschlagenen Erstladen
  sichtbar. Ohne JavaScript liefert Daten anzeigen die vollständige Seite.
- Nachgeladene Timerformulare, TV-/Radio-Bouquetwechsel, Filter, Ordnerwechsel
  und Downloads im Browser geprüft. Dateigröße erneuert sich automatisch;
  Filtertext und angezeigter Ordner bleiben erhalten, auch wenn sich der
  konfigurierte oder lokal gewählte Receiverordner zwischenzeitlich ändert.
- Speichern und Löschen zeigen den Ladehinweis während verzögerter Antworten.
  Fünf-Sekunden-Rückstellung der Löschbestätigung erhalten. Schreibaufträge
  werden genau einmal gesendet. Nach ausgeführtem POST absichtlich die
  Webserverantwort unterbrochen: verständliche Meldung, gesperrtes Formular,
  Liste prüfen und kein erneuter Schreibauftrag, für JSON und XML geprüft.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.6 und Schema `0005`; CLI-Initialisierung, Login, Ladevorlagen, Assets,
  Favicon und Standardordner-Regressionsfall erfolgreich. Erneute Initialisierung
  erhält Schlüssel, geänderten Port und Aufnahmezeitlimit von 90 Sekunden.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Paketbau aus
  dem finalen Installations-ZIP hat dieselben Inhalte wie der zuvor geprüfte
  Paketbau. Neue Ladevorlage, neues Modul und neue Tests sind enthalten.
  Keine Betriebsdaten oder Zugangsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.6`, sieben unveränderte bisherige
  Tags, `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle
  Archivdateien und Git-Objekte weiterhin ohne die entfernten Netzwerkbeispiele.
- Die Prüfung verwendet simulierte Receiver. GitHub-Push und GitHub-CI wurden
  nicht ausgeführt; Receiverkonfigurationen und Aufnahmedateien auf der
  eingesetzten Hardware wurden aus dieser Entwicklungsumgebung nicht geändert.

## Änderungen 1.1.6

- Startordner der Aufnahmen aus der konfigurierten Receiver-Einstellung lesen.
- Sofortiger Seitenrahmen mit nachgeladener vollständiger Receiverantwort;
  Ladehinweis auch bei bestehenden Receiveraufträgen und Bouquetwechseln.
- Kein neues Datenbankschema und keine neuen Abhängigkeiten.

## Prüfung von Version 1.1.5

Prüfstand: 05.10.2026, Python 3.12 unter Linux.

- 248 automatisierte Tests erfolgreich; Code- und Formatprüfung erfolgreich.
  Installer- und JavaScript-Syntax geprüft. Bestehende Tests der aktiven
  Receiverüberschrift an die neue Darstellung angepasst.
- Browserprüfung von Timer-, Sender-, Aufnahme- und EPG-Seiten sowie Timer
  erstellen und bearbeiten bei 320, 390, 720, 768, 1024, 1280, 1440 und 1920
  Pixeln Breite. Auftragsprüfung zusätzlich bei 390 und 1280 Pixeln geprüft.
- Receivername in allen betroffenen Hauptüberschriften ohne Doppelpunkt und
  nach einem Leerzeichen; berechnete Schriftgröße exakt 50 Prozent des
  unveränderten Haupttitels. Lange Namen und responsive Zeilenumbrüche geprüft.
- Receiverfelder auf breiten Ansichten gegenüber 1.1.4 gemessen: Timer von
  rund 245 auf 368 Pixel, übrige Listen und EPG von rund 266 auf 400 Pixel.
  Auf mobilen Ansichten begrenzt die verfügbare Breite das Feld; keine horizontale
  Überbreite der Seite. Auf mittleren Breiten hat die Timerkopfzeile zwei Zeilen,
  damit die Auswahlfelder nicht durch die Überschrift zusammengedrückt werden.
- Auswahlfelder und Filter weiterhin 46 Pixel hoch. Textbereich durch kleinere
  vertikale Innenabstände von rund 21 auf 28 Pixel erhöht. Schriftmetriken mit
  „Agjpqy“ und Bildschirmbilder geprüft; Unterlängen vollständig sichtbar.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.5 und Schema `0005`; Login, Assets und Receiverüberschriften erfolgreich.
  Erneute Initialisierung erhält Schlüssel, geänderten Port und Aufnahmezeitlimit.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Paketbau aus
  dem finalen Installations-ZIP hat dieselben Inhalte wie der zuvor geprüfte
  Paketbau. Keine Betriebsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.5`, unveränderte bisherige Tags,
  `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle Archivdateien
  und Git-Objekte weiterhin ohne die entfernten privaten Netzwerkbeispiele.
- Die Prüfung verwendet simulierte Receiver. GitHub-Push und GitHub-CI wurden
  nicht ausgeführt; bestehende Firefox-Profile wurden nicht geändert.

## Änderungen 1.1.5

- Gemeinsame CSS-Regeln und sechs betroffene Seitenvorlagen angepasst.
- Keine Änderung am Datenbankschema, an Abhängigkeiten oder an Receiveraufträgen.

## Prüfung von Version 1.1.4

Prüfstand: 04.10.2026, Python 3.12 unter Linux.

- 248 automatisierte Tests erfolgreich; Code- und Formatprüfung erfolgreich.
  Installer- und JavaScript-Syntax geprüft.
- Gemeldeten Fehler vor der Korrektur in drei Varianten reproduziert: JSON ohne
  Verzeichnisangabe, JSON mit abweichendem implizitem Verzeichnis und XML.
  Der Standardpfad war `/media/usb/`, während eine implizite Abfrage keine
  Aufnahmen lieferte. Alle drei Regressionen schlugen mit dem bisherigen Loader fehl.
- Erstaufruf und Live-Aktualisierung laden nach der Korrektur ausdrücklich den
  angezeigten Standardordner. Mit und ohne dessen Eintrag in den Bookmarks
  geprüft; andere Ordner, Rückwechsel und Dateidownload ebenfalls geprüft.
- Bei nicht verfügbarer Standardabfrage mit einem und mehreren bekannten
  Aufnahmepfaden geprüft: eindeutigen Pfad verwenden beziehungsweise die
  implizite Auswahl des Receivers beibehalten. Keinen ersten Bookmark erraten.
- Bestehende Prüfungen für kanonische Symlinkpfade, unzulässige Ordner,
  Downloadrechte, Eigentümerrechte und den Schutz laufender Aufnahmen erfolgreich.
- Browserprüfung mit JSON- und XML-Receiver-Simulation auf mobilen und breiten
  Ansichten: Dateien direkt nach dem Erstaufruf sichtbar, Dateigröße nach der
  automatischen Aktualisierung erneuert, Filtertext erhalten, Ordnerwechsel
  und Download erfolgreich. Keine JavaScript-Fehler oder Schreibaufträge.
- Wheel und Quelldistribution gebaut. Installiertes Wheel startet mit Version
  1.1.4 und Schema `0005`; CLI-Initialisierung, Login, Assets, Favicon und
  Standardordner-Regressionsfall erfolgreich. Schlüssel, geänderter Port und
  Aufnahmezeitlimit bei erneuter Initialisierung erhalten.
- Installations- und Git-ZIP entpackt und dateiweise verglichen. Aus dem finalen
  Installations-ZIP gebautes Wheel enthält dieselben Dateien wie das geprüfte
  Wheel. Keine Betriebsdaten enthalten.
- Sauberer Branch `main`, annotierter Tag `v1.1.4`, unveränderte bisherige Tags,
  `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft. Alle Archivdateien
  und Git-Objekte weiterhin ohne die entfernten privaten Netzwerkbeispiele.
- Die Prüfung verwendet simulierte Receiver. Prüfung am eingesetzten Receiver
  nach Installation erforderlich; GitHub-Push und GitHub-CI wurden nicht ausgeführt.

## Änderungen 1.1.4

- Ermittlung des Standardaufnahmeordners vor die Abfrage der Dateien verschoben.
- Keine Änderung am Datenbankschema, an Abhängigkeiten oder an gespeicherten
  Receiververbindungen. Alle Anfragen zur Pfadauflösung sind Lesezugriffe.

## Prüfung von Version 1.1.3

Prüfstand: 04.10.2026, Python 3.12 unter Linux.

- 238 automatisierte Tests erfolgreich; Code- und Formatprüfung erfolgreich.
  Installer- und JavaScript-Syntax geprüft.
- Regression für Firefox-Lesezeichen: Favicon-GET und HEAD ohne Anmeldung,
  mit angemeldetem Administrator und bei erzwungenem Passwortwechsel geprüft.
  Öffentlicher Standardpfad und beide statischen Favicon-Dateien liefern Bilder
  mit `public, max-age=86400`; GET hat Bilddaten, HEAD keinen Body.
- PNG-Signatur und echte ICO-Struktur mit drei Bildern in 16, 32 und 48 Pixeln
  geprüft. Das PNG-Logo ist gegenüber 1.1.2 bytegleich.
- Bedingte statische Favicon-Abfrage liefert HTTP 304 mit speicherbarem Header.
  Anmeldung, Health, persönliche Seiten, CSS/JavaScript, fehlende Dateien und
  unzulässige Methoden behalten `no-store`. Keine Sitzungs-Cookies auf Icon-Antworten.
- Alle Seiten verwenden `/favicon.ico?v=1.1.3`; PNG und ICO enthalten keine
  zusätzlichen Netzwerkadressen oder persönlichen Metadaten.
- Wheel und Quelldistribution vollständig gebaut und geprüft. Start des installierten
  Wheels mit Schema `0005`, Version 1.1.3, Login, Assets und allen Favicon-Pfaden
  erfolgreich. Erneute Initialisierung erhält Schlüssel, Port und Aufnahmezeitlimit.
- Beide ZIPs entpackt und dateiweise verglichen; aus dem Installations-ZIP gebautes
  Wheel hat identische Inhalte wie das geprüfte Wheel. Keine Betriebsdaten enthalten.
- Git-Release 1.1.3 setzt den bestätigten bereinigten Stand 1.1.2 fort.
  Alle bisherigen Commit- und Tag-Kennungen bleiben erhalten. Sauberer Branch
  `main`, annotierter neuer Tag, `git fsck`, Klonen und gewöhnlicher lokaler Push geprüft.
- Alle Git-Objekte und Archivdateien weiterhin ohne die entfernten privaten
  Netzwerkbeispiele. Keine erneute Historienbereinigung erforderlich.
- Der tatsächliche Eintrag in einem bestehenden Firefox-Profil wird nach dem
  Installationsupdate durch Öffnen und Neuladen des Lesezeichens geprüft.
  Die lokale Prüfung ersetzt keinen ausgeführten GitHub-Push oder CI-Lauf.

## Änderungen 1.1.3

- Favicon-Cache-Header gezielt freigegeben; übrige Auslieferung unverändert.
- Öffentliche ICO-Route und korrekte Einbindung in der gemeinsamen Seitenvorlage.
- ICO-Datei aus dem vorhandenen PNG-Logo erzeugt; keine neue Laufzeitabhängigkeit.

## Prüfung von Version 1.1.2

Prüfstand: 04.10.2026, Python 3.12 unter Linux.

- 235 automatisierte Tests erfolgreich; Code- und Formatprüfung erfolgreich.
- Installer-Syntax und JavaScript-Syntax geprüft.
- Wheel und Quelldistribution gebaut und auf vollständige Inhalte geprüft.
  Das installierte Wheel startet mit Version 1.1.2; CLI-Initialisierung,
  Schema `0005`, Login, Assets und neutraler Receiver-Platzhalter geprüft.
  Erneute Initialisierung erhält Schlüssel, Aufnahmezeitlimit 90 Sekunden
  und einen bereits geänderten Port.
- Installations- und Git-ZIP entpackt und dateiweise abgeglichen; keine
  Betriebsdaten, Schlüssel, Zugangsdaten oder Testumgebungen enthalten.
- Jede Datei aller drei früheren Git-Release-Stände mit dem Original verglichen:
  ausschließlich die neutralen Netzwerkbeispiele und zugehörigen Testprüfungen
  geändert. Versionsnummern, Commit-Nachrichten, Autoren und Zeitpunkte erhalten.
- Alle Git-Objekte des neuen Pakets, einschließlich nicht erreichbarer Objekte,
  sowie alle Release-Stände und Archivdateien auf verbliebene private
  Netzwerkbeispiele geprüft. Keine Treffer. Keine alten Sicherungsreferenzen.
- Vier annotierte Tags, lineare Historie, sauberer Branch `main`, `git fsck`
  und Klonen geprüft. Git-Paket enthält keine Remote-Konfiguration.
- Geschützten atomaren Push gegen lokale Repositories geprüft; alle fünf
  Referenzen aktualisiert. Abbruch bei geänderter Branch- oder Tag-Kennung
  ohne Teilaktualisierung und Erkennung zusätzlicher Referenzen geprüft.
- Die bisherigen Browserprüfungen der unveränderten Oberfläche stehen unten.
  Die lokale Prüfung ersetzt keinen ausgeführten Push oder CI-Lauf auf GitHub.

## Änderungen 1.1.2

- Private Netzwerkadressen in Receiverformular und Testfällen ersetzt durch
  reservierte Dokumentationsadressen und `example.test`.
- Vollständige neue Git-Objektdatenbank mit bereinigten Ständen für `v1.0.0`,
  `v1.1.0` und `v1.1.1` erstellt. Deren Commit- und Tag-Kennungen ändern sich;
  diese Bereinigung ersetzt die in früheren Prüfberichten beschriebene
  Beibehaltung der ursprünglichen Kennungen.
- Release 1.1.2 ergänzt; keine Schemaänderung und keine Änderung gespeicherter
  Verbindungen. GitHub-Anleitung und PowerShell-Skript für die einmalige Umstellung.

## Änderungen 1.1.1

- Timer-Kopfzeile auf Desktop in der Reihenfolge Receiverauswahl, „Liste filtern“,
  „Timer erstellen“, mittig auf gleicher Höhe mit der Überschrift.
  Auf mobilen Geräten zuerst die Receiverauswahl, darunter Filter und Button.
- Filter und Receiver-Dropdown haben bei Timern, Sendern und Aufnahmen dieselbe
  gemessene Höhe von 46 CSS-Pixeln; beide Senderansichten (Listen und Sender)
  sowie JSON- und XML-Receiver bei sieben Bildschirmbreiten geprüft.
- Filterfunktion, Dateizeilen und Fünf-Sekunden-Aktualisierung einschließlich
  Suchtext, Fokus und Cursorposition bleiben erhalten.
- Versionsstand und Asset-URLs 1.1.1, Release-Datum 04.10.2026; keine Migration.
- Beide ZIPs entpackt und dateiweise abgeglichen. Git-Historie fortgeführt;
  `v1.0.0` und `v1.1.0` unverändert, annotierter Tag `v1.1.1` auf dem neuen
  Release-Commit. `git fsck`, Klonen und lokaler fortführender Push erfolgreich.

## Änderungen 1.1.0

- Timerfilter links neben der Receiverauswahl in derselben Kopfzeile wie die
  Überschrift und der Button „Timer erstellen“. Aufnahmefilter rechtsbündig
  in der Zeile der Ordnerauswahl. Positionen auf Desktop im Browser geprüft.
- Timer durchsuchen ausschließlich Sender und Titel; Aufnahmen zusätzlich
  den Dateinamen ohne Verzeichnispfad. Beschreibungen, Ersteller, Bouquets,
  Receiver, Zeitangaben, Status und Größen ergeben keine zusätzlichen Treffer.
- Teiltextsuche ohne Groß-/Kleinschreibung und ohne äußere Leerzeichen;
  Umlaute, Anführungszeichen, HTML-Sonderzeichen und eckige Klammern geprüft.
- Die Dateizeile folgt der Sichtbarkeit ihres Haupteintrags, auch bei mobiler
  Tabellendarstellung. Leere Suche zeigt wieder alle Einträge; kein Treffer
  zeigt „Keine passenden Einträge“. Auch erledigte Timer sind durchsuchbar.
  Bereichszahlen zeigen die Anzahl der passenden Einträge des jeweiligen Bereichs.
- Echte Fünf-Sekunden-Abfragen im Browser mit fokussiertem Filter geprüft:
  Suchtext, Fokus, Cursorposition und offener Verlauf bleiben erhalten;
  veränderte Größe/Dauer sowie neu hinzugekommene Einträge werden gefiltert.
  Die Filter funktionieren nach der Aktualisierung weiter.
- Senderfilter ohne sichtbare Außenbeschriftung mit „Listen filtern“ bzw.
  „Sender filtern“ im Feld; zugängliche Bezeichnungen per `aria-label`.
- „Timer erstellen“ in Timerübersicht, Senderliste, EPG, Formularüberschrift
  und Berechtigungshinweisen. Vorhandene Tests auf neue Beschriftung angepasst.
- Versionsstand und Asset-URLs 1.1.0, Release-Datum 04.10.2026; keine Migration.
  Das Git-Paket ergänzt die bestehende Historie und behält `v1.0.0` unverändert.
- Filter- und Browserprüfungen verwenden nur lokale simulierte Receiver;
  Filteraktionen erzeugen keine Schreibaufträge.
- Filter und fokussierte Fünf-Sekunden-Aktualisierung auch mit XML geprüft;
  Aufnahmegröße und Dauer aktualisiert, Dateizeilen korrekt gefiltert.

## Änderungen 1.0.0

- Versionsstand 1.0.0 in Paketmetadaten, Health-Antwort, Fußzeile und Asset-URLs.
- Funktionsstand von 0.8.0; Datenbankschema weiterhin Revision `0005`.
- Getrennte Installations- und Git-Pakete mit identischem Quellstand.
- GitHub-Repository mit Release-Commit, Branch `main`, annotiertem Tag `v1.0.0`
  und CI für Code-/Formatprüfung, Tests, Installer-Syntax und Paketbau.
- Installationsanleitung, Versionsverlauf, Release-Hinweise und GitHub-Anleitung.
- Git-Dateiregeln für LF-Zeilenenden der Linux-Skripte und Ausschluss lokaler Daten.
- Installations- und Git-ZIP entpackt und dateiweise abgeglichen; derselbe
  Quellstand einschließlich aller Unterlagen und des CI-Workflows.
- Lokales Git-Repository ohne Remote geprüft: sauberes Arbeitsverzeichnis,
  `git fsck`, annotierter Tag auf dem Release-Commit und Klonen aus dem
  entpackten Git-Paket erfolgreich.

## Änderungen 0.8.0

- Neue Timer erhalten exakt einen sprechenden Ersteller-Tag, beispielsweise
  `e2web-owner-digiandi` oder `e2web-owner-thomas.meyer`. Derselbe Tag gilt für alle
  Sender und Receiver des Kontos. Es werden keine weiteren Tags erzeugt.
- Registrierung vorhandener Konten durch Migration `0005`, neuer Konten sowohl
  über die Benutzerverwaltung als auch über `create-admin`. Keine vorausgehende
  Timeranlage notwendig, um einen Tag manuell am Receiver verwenden zu können.
- Manuell gesetzte Tags werden bei Timern und Aufnahmen über JSON und XML erkannt.
  Senderwechsel und Verwendung auf einem weiteren freigegebenen Receiver geprüft.
  Receiverfreigaben, Schreibrechte und Prüfung eigener Inhalte bleiben erforderlich.
- Unbekannte, fremde und mehrdeutige Tags berechtigen normale Benutzer nicht zu
  Änderungen. Eingeschleuste Tags und Benutzer-IDs in Timerformularen werden ignoriert;
  neu angelegte Timer erhalten ausschließlich den Tag des angemeldeten Kontos.
  Alte Formulare und geänderte Registrierungen werden vor Schreibaufträgen geprüft.
- Gültige zufällige Kennungen bleiben lesbar. Beim Bearbeiten eines alten Timers
  wird nur dessen Erstellerkennung auf den sprechenden Tag desselben Erstellers
  umgestellt; andere Tags und alte Aufnahmezuordnungen bleiben erhalten. Auch bei
  Bearbeitung durch einen Administrator wird nicht auf diesen umgeordnet.
  Unbekannte Timer werden durch bloßes Bearbeiten nicht einem Benutzer zugewiesen.
- Gelöschte Konten verlieren die Zuordnung. Wiederverwendete Namen und SQLite-IDs
  übernehmen keine alten Rechte; nötigenfalls erhält das neue Konto einen
  sprechenden Zusatz wie `-konto-2`. Der genaue Tag erscheint schreibgeschützt
  im Administratorformular **Benutzer bearbeiten**.
- Upgrade von `0004` zweimal erfolgreich geprüft; Konten, Passwort-Hashes,
  Receiverdaten, alte Eigentümerkennungen, Freigaben, Sitzungen und Schlüssel
  bleiben unverändert. Das Update sendet keine Schreibaufträge an Receiver.
- Chromium-Prüfung von Ersteller-Tag und Benutzerformular bei Desktop- und
  Mobilbreite sowie manueller Zuordnung über JSON und XML erfolgreich.
  Timeranlage mit genau einem sprechenden Tag, Bearbeitung alter Timer,
  Fünf-Sekunden-Aktualisierung, Rechte, Downloads, Löschbestätigungen und HTTPS
  geprüft; keine JavaScript-Fehler oder Dialoge.

## Änderungen 0.7.3

- Benutzerübersicht mit AWAS-Spalte „Letzte Anmeldung“ im Format
  `DD.MM.YYYY HH:MM`, in der konfigurierten Anzeigezeitzone, ohne erfolgreiche
  Anmeldung „Noch nie“. Bereits vorhandene erfolgreiche Login-Ereignisse werden
  berücksichtigt; jeweils der neueste Zeitpunkt pro Benutzer wird ausgewertet.
  Fehlversuche, Passwortänderungen, Seitenaufrufe und Logout ersetzen ihn nicht.
  Anzeige ausschließlich für Administratoren; keine neue Migration nötig.
- Aufnahmepfade und Unterordner des aktuellen Verzeichnisses in einer gemeinsamen
  Dropdown-Auswahl. Separate Unterordnerbuttons entfernt; direkter Ordnerwechsel,
  aktuelle Auswahl und erlaubte übergeordnete Ordner erhalten.
- Mehrere Ebenen, Umlaute/Leerzeichen („Udo Jürgens“), doppelte Pfadmeldungen und
  durch das Fünf-Sekunden-Polling neu hinzukommende Ordner geprüft, über JSON und XML.
  Kein rekursives Abfragen des kompletten Aufnahmebaums. Nicht freigegebene Pfade
  und Traversierung bleiben abgewiesen und werden nicht als Wunschpfad abgefragt.
- Benutzerübersicht und Ordnerwechsel im Chromium-Browser auf Desktop und mobil
  geprüft; vorhandene Abläufe mit Timern, Rechten, Downloads, Zwei-Klick-Löschung,
  automatischer Aktualisierung und HTTPS-Proxy weiterhin erfolgreich.

## Änderungen 0.7.2

- Timer-Dateizeilen mit Dateinamen und Größe ausschließlich bei laufenden Timern.
  Geplante, vorbereitete, deaktivierte und erledigte Timer zeigen keine Dateizeile;
  für sie werden keine Aufnahmelisten für die Dateianzeige gelesen. Auch ein
  wiederkehrender Timer mit dem Dateinamen seiner früheren Aufnahme bleibt ohne
  Dateizeile, solange er ansteht. Statuswechsel beim Polling über JSON und XML geprüft.
- Hinweis „Zum Beenden den laufenden Timer öffnen.“ bei Aufnahmen entfernt.
  Laufende Aufnahmen bleiben einschließlich veralteter Löschaufträge gesperrt;
  es erscheint kein ersatzweiser Löschhinweis bei laufenden Aufnahmen.
- Kleine graue Erstellerzeile „von Anzeigename“ bei jedem Timer und jeder Aufnahme,
  unter Titel bzw. Wiederholung wie bei AWAS. Anzeige auch mit Leserechten sowie
  bei fremden Einträgen; direkte Erstellerzuordnung statt Titel-/Zeitvergleich.
- Unbekannte, gefälschte, mehrdeutige oder anderen Geräten zugeordnete Kennungen
  zeigen „von unbekannt“. Ein gelöschtes und mit derselben ID neu angelegtes Konto
  erhält weder die alte Erstelleranzeige noch dessen Rechte. Credential-Wechsel
  erhält die Anzeige, eine geänderte Geräteadresse nicht. Ersteller bleibt in
  Aufnahme-Tags nach Timerlöschung erhalten; JSON und XML geprüft.
- Sonderzeichen in Anzeigenamen werden HTML-escaped; geänderte Anzeigenamen
  werden bei der nächsten Aktualisierung übernommen. Die Benutzerzeile beeinflusst
  keinerlei Schreibberechtigungen. Keine neue Datenbankmigration notwendig.
- Browserdarstellung, Dateizeilen bei Statuswechseln, durchgehendes Orange sowie
  Erstellerzeilen bei Desktop- und mobilen Breiten geprüft.

## Änderungen 0.7.1

- Fehler aus dem Screenshot mit regulärem XML-Container `e2locations`
  reproduziert: 0.7.0 lieferte beim Laden des Timerformulars Fehler 502.
  Einzelnes `e2location` sowie Container mit genau einem `e2location` werden
  jetzt erkannt; JSON bleibt unterstützt. Erstellung und Speichern über JSON
  und XML einschließlich gemischter Endpunkte geprüft.
- Standardpfad aus der separaten Pfadabfrage berücksichtigt, wenn er in der
  Timerliste fehlt. Keine Annahme, dass der erste Bookmark der Standard sei.
- Bei unbekanntem Standard bleibt die angebotene Pfadauswahl im Formular
  verfügbar. Ein leerer Pfad ist im Browser und auf dem Server gesperrt;
  Auswahl und anschließendes Speichern geprüft. Ohne angebotenen Pfad bleibt
  ein verständlicher Fehler, ohne Schreibauftrag an den Receiver.
- Leere, mehrdeutige und ungültige XML-Pfadantworten werden zurückgewiesen.
- „Zur Übersicht“ in die Sender-Auswahlzeile verschoben; Ausrichtung,
  Rückkehrziel und mobile Darstellung im Browser geprüft.
- „Neu laden“ bei Aufnahmen entfernt. Fünf-Sekunden-Aktualisierung von Größe
  und Dauer weiterhin erfolgreich geprüft.

Primäre Referenzen für die Pfadantworten:
[älteres WebInterface-XML-Template](https://github.com/oe-alliance/enigma2-plugins/blob/master/webinterface/src/web/getcurrlocation.xml)
und [OpenWebif-Pfadmodell](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/models/locations.py).
Die Quellen wurden für diese Korrektur gelesen; kein fremder Quellcode wird eingebunden.

## Änderungen 0.7.0

- „Timer anlegen“ neben der Receiverauswahl in der Kopfzeile;
  Beginn und Ende auf derselben Höhe, Hinweis in einer gemeinsamen Zeile.
- Neuer Seitenname „Enigma2 Timer“, Untertitel „Aufnahmen-Verwaltung“;
  Login ohne Erklärungssatz unter „Anmelden“.
- TV/Radio oberhalb und Bouquetnamen unterhalb des Senders, klein und grau,
  bei Timern und Aufnahmen; TV/Radio, mehrere Bouquets, doppelte Sendernamen,
  nicht mehr gelistete Sender, IPTV-Referenzen und JSON/XML geprüft.
- Bouquetdaten werden im Hintergrund geladen und fünf Minuten geteilt
  zwischengespeichert. Langsame/fehlgeschlagene Abfragen sperren keine Liste;
  Fünf-Sekunden-Polling startet keine wiederholten vollständigen Katalogabfragen.
  Geänderte Receiver-Verbindungen übernehmen keine alten Bouquetnamen.

- Direkte Timeranlage ohne vorherigen Besuch der Senderseite; TV- und
  Radio-Bouquets in einer gemeinsamen Auswahl, zuerst TV, danach Radio;
  Bouquetreihenfolge des Receivers und erste Vorauswahl geprüft.
- Senderliste des ausgewählten Bouquets, erster aufnehmbarer Sender,
  Ausschluss von Markern und Untergruppen; JSON und XML geprüft.
- Bouquetwechsel lädt nur Daten, sendet keinen Receiver-Schreibauftrag;
  eigene Titel, Beschreibung und Zeiten bleiben erhalten. Leere Bouquets
  verhindern Speichern bis zur nächsten verfügbaren Auswahl.
- Sender-/Bouquetzuordnung nach Receiveränderungen, gefälschte Auswahlwerte,
  veraltete Senderlisten und Leserechte serverseitig vor einem Schreibauftrag geprüft.
- Konflikte und Formularfehler erhalten Bouquet, Sender und eingegebene Daten.
- Tatsächlicher Standardaufnahmepfad direkt ausgewählt, kein generischer
  Platzhalter und kein leerer Pfadeintrag; XML-Default über Pfadabfrage.
  Fehlende Default-Angabe wird gemeldet, ohne den ersten Bookmark anzunehmen.
- Timerbereiche „Laufend (x)“ und „Anstehend (x)“ mit korrekten Anzahlen,
  einschließlich leerer Bereiche; erledigter Verlauf bleibt erhalten.
- Dateinamen und native Größen pro Timer, separate Monospace-Dateizeile,
  durchgehendes Orange für laufende Aufnahmen; Größen- und Statuswechsel
  werden beim nächsten Aktualisieren übernommen.
- Dateigröße ohne Schätzung, eindeutige Dateizuordnung, eine Listenabfrage je
  Ordner; XML-Fallback und bestätigte abweichende Receiverpfade geprüft.
  Metadatenfehler, fehlende Dateien und Umschalt-Timer erhalten passende Hinweise
  und lassen die Timerliste sowie ihre zulässigen Aktionen verfügbar.
- Oberfläche ohne Du-Ansprache; Erklärungssatz in der Senderübersicht entfernt.
- Browserprüfung der direkten TV-/Radio-Auswahl und neuer Formular-/Dateizeilen,
  mit den bisherigen Abläufen, mobiler Darstellung und HTTPS-Proxy.

## Fehlerkorrektur 0.6.1

- Fehler nach erfolgreicher Aufnahme-Löschung mit konfiguriertem Pfad
  `/hdd/movie/` und zurückgegebenem Pfad `/media/hdd/movie/` reproduziert.
- Erfolgreiches Löschen mit anschließendem Laden der Liste sowie abgelehntes
  Löschen mit inline angezeigtem Fehler geprüft; keine falsche Meldung 403 mehr.
- Download, Fünf-Sekunden-Aktualisierung und Unterordner mit abweichendem
  tatsächlichen Receiverpfad funktionieren.
- Nicht freigegebene Pfade und Pfadtraversierung bleiben abgewiesen; der
  gewünschte fremde Pfad wird bei der Freigabeprüfung nie abgefragt.
- Ohne Bestätigung des Receivers wird keine `/hdd`-Aliasbeziehung angenommen.
- Vollständiger Browserlauf mit realen lokalen HTTP-Abfragen und der
  abweichenden Pfadangabe erneut durchgeführt; JSON und XML geprüft.

## Oberfläche und Bedienung

Im Browser geprüft:

- Überschrift links, Receiverwahl rechts auf gleicher Höhe; direkte Umschaltung;
- Timer im AWAS-Aufbau mit Aufnahme, Sender, Receiver, Start, Ende, Dauer, Status;
  Beschreibung direkt sichtbar, bei leerer Beschreibung keine zusätzliche Zeile;
- Aufnahmen im AWAS-Aufbau mit Aufnahme, Sender, Receiver, Beginn, Dauer, Status;
  eigene Dateinamenzeile, Monospace-Schrift und Dateigröße rechts;
- durchgehendes AWAS-Orange `#fde7dc` für laufende Timeraufnahmen und für beide
  Zeilen eines laufenden Aufnahmeblocks, auch mobil;
- Datum/Uhrzeit `DD.MM.YYYY HH:MM`, Dauer `HH:MM:SS`, keine Aufnahme-Sendungsdetails;
- direkt ausgewählter echter Standardpfad, Unterordner und Ordnerwechsel;
  kein Button „Übergeordneter Ordner“ und kein generischer Standardpfad-Eintrag;
- Downloads über den Browser mit korrekten Bytes und Dateinamen;
- zentrale dezente Fußzeile mit Zeitzone, Versionsnummer und Release-Datum;
- mittiges Login ohne Slogan;
- Löschen von Timern, Aufnahmen, Receivern und Benutzern mit exakt zwei Klicks;
  erster Klick sendet keinen POST, nach fünf Sekunden automatische Rückstellung;
  anschließender erster Klick bestätigt wieder, zweiter Klick sendet einen POST;
- AWAS-Originalcode für die Bestätigung und seine Bestätigungsstile;
  bei reduzierter Bewegung bleibt der bestätigende Button durchgehend rot;
- Löschfehler unmittelbar in der weiterhin sichtbaren jeweiligen Liste;
- Anlegen aus EPG mit Vor-/Nachlauf und Wochentagen, Bearbeiten laufender Timer
  über JSON und XML ohne doppelte Timer;
- TV/Bouquets als Standard, Anbieter nach Bouquets, EPG über Sender;
- Menüfolge, Administration, mobile Navigation und alle Seiten aus 0.4.0 erhalten.

## Eigentümer und automatische Aktualisierung

- Neu angelegte Timer erhalten einen registrierten sprechenden Ersteller-Tag;
  JSON und XML geprüft; Aufnahmen übernehmen ihre Kennung in `tags`/`e2tags`.
- Wiederholung mit fortgeschriebenen Zeiten und Bearbeitung erhalten den Ersteller.
  Aufnahmen bleiben auch nach Entfernen des Timers ihrem Ersteller zugeordnet.
- Eigene Einträge mit Schreibrechten sind veränderbar; fremde, unbekannte und
  mehrdeutige Kennungen nicht. Alte Zufallskennungen benötigen weiterhin ihren
  ursprünglichen Receiver-/Gerätebezug; sprechende Tags sind bewusst wiederverwendbar.
- Anzeige und Download bleiben für alle freigegebenen Inhalte verfügbar.
- Direkte Edit-Aufrufe und veraltete Schreibformulare greifen nicht auf fremde
  Einträge zu; Eigentümerprüfung auch nach langsamen Receiver-Vorabfragen.
- Gelöschte Benutzer verlieren ihre Zuordnung; erneut vergebene Namen und SQLite-IDs
  übernehmen keine alten Eigentümerrechte. Zugangsdatenwechsel erhält die Zuordnung;
  eine geänderte Geräteadresse verwirft nur alte Zufallskennungen.
- Administratoren ändern unbekannte Timer, löschen beendete unbekannte Aufnahmen
  und sehen keine Receiver-Berechtigungsauswahl; Standardreceiver bleibt auswählbar.
- Laufende Aufnahmen bleiben auch für Administratoren gesperrt. Nach Stoppen durch
  Timerlöschung bleibt die Datei erhalten und wird löschbar; spätere Statusänderung
  blockiert einen zuvor ausgestellten Löschauftrag.
- Browserabfragen im Fünf-Sekunden-Abstand, sichtbare Änderungen der Laufzeit und
  Aufnahmegröße, offener Timerverlauf und Löschbestätigung bleiben erhalten.
- Keine parallelen Aktualisierungsabfragen; versteckte Tabs und Auswahlfelder
  pausieren. Receiverbindung geprüft. Gleichbleibende Löschaufträge erzeugen
  beim Polling keine neuen Datenbankzeilen; gespeicherte Tokens sind verschlüsselt.
- Vollständiger Browserlauf mit JSON/XML, mobilen Breiten, allen Bestätigungen
  und HTTPS-Proxy erneut erfolgreich, keine JavaScript-Fehler oder Dialoge.

## Rechte und Standardreceiver

Automatisiert und über die Oberfläche geprüft:

- Einzelzuweisung von Receiver-Lese- und Schreibrechten durch Administratoren;
- Lesen erlaubt alle Ansichten und Aufnahme-Downloads, bietet keine Schreibaktionen;
- gefälschte direkte Aufrufe und alte Formulare können mit Leserechten keine Timer
  anlegen, bearbeiten oder löschen und keine Aufnahmen löschen;
- nicht freigegebene Receiver werden ausgeblendet und sind nicht auswählbar;
- alternative Freigabe aller Receiver mit gemeinsamen Lese- oder Schreibrechten;
- Administratoren behalten immer Schreibrechte;
- Standardreceiver nach jedem Login ausgewählt, manueller Wechsel bis zum Logout;
- deaktivierter, gelöschter oder entzogener Standardreceiver fällt auf den ersten
  alphabetisch sortierten freigegebenen Receiver zurück;
- ungültige Standardreceiver und Berechtigungen werden ohne teilweise Änderungen
  abgewiesen; Änderungen an Benutzerkonten widerrufen bestehende Sitzungen;
- erneute Prüfung von Konto, Sitzung, Receiverzuordnung, Schreibrechten und
  Verbindung nach längeren Vorabfragen vor Receiver-Schreibaufträgen;
- erneute Download-Prüfung nach der Dateiliste und nach Öffnen der Datei,
  bevor Antwortdaten an den Browser gelangen; entzogene Rechte, abgemeldete
  Sitzungen, deaktivierte Benutzer und geänderte Verbindungen verhindern den Download.

## Downloads, Zeitlimits und HTTPS

- Download über den festen Dateiendpunkt des ausgewählten Receivers, nur für
  genau eine zuvor in dessen erlaubtem Aufnahmeordner gelistete Dateireferenz;
- korrekte Binärdaten und UTF-8-Dateinamen, auch mit Leerzeichen, Plus und Ampersand;
- einzelne Byte-Bereiche, offene und Suffix-Bereiche mit HTTP 206 sowie HTTP 416
  für Bereiche außerhalb der Datei; Mehrfachbereiche werden abgewiesen;
- keine beliebigen Umleitungen: nur `/file/` auf demselben Receiver zulässig;
- keine Weitergabe von Receiverzugangsdaten oder ungeprüften Antwortheadern;
- fehlende Dateien und mehrdeutige wörtliche Prozent-Escapes werden abgewiesen;
- Stream und Receiver-Verbindung werden nach Abschluss geschlossen;
- 90 Sekunden Lesezeitlimit für `movielist` und Dateidownloads, auch beim Laden
  einer alten Konfiguration; andere Receiveranfragen behalten ihr kurzes Zeitlimit;
- Standardpfad-Abfrage mit JSON sowie leerer XML-Aufnahmeliste geprüft;
- nginx-Vorlage enthält `proxy_read_timeout 300s;`, Anleitung beschreibt die
  notwendige Änderung in bestehenden nginx-Sites;
- tatsächlicher HTTPS-Proxy vor einem HTTP-Backend mit absichtlich fehlendem
  Proto-Header: CSS, JavaScript und Logo ausschließlich per HTTPS geladen;
  Anmeldung, Gestaltung und direkte Receiverumschaltung funktionieren.

## Migration und vorhandene Funktionen

Revision `0005` ergänzt registrierte sprechende Ersteller-Tags für alle Konten.
Revision `0004` ergänzt alte Eigentümerkennungen und verschlüsselte Auftragstokens.
Die davorliegende Revision `0003` fügt Standardreceiver und Schreibrechte ohne Neuaufbau der
Benutzertabelle hinzu. Das Upgrade erhält unverändert Konten, Passwort-Hashes,
Receiver, verschlüsselte Zugangsdaten, bestehende Zuordnungen, Sitzungen,
Audit-Ereignisse und den Schlüssel. Bestehende Zugriffe erhalten Schreibrechte.
Die neue Fremdschlüsselbeziehung setzt einen gelöschten Standardreceiver auf
NULL. Auch das bestehende Upgrade von `0001` bleibt geprüft.

Die Tests aus 0.4.0 bestehen weiterhin: CSRF, Login-Begrenzung, HTTPS-Cookies,
Administrator-/Kontoschutz, Passwortverschlüsselung, Sender/EPG, Timeroptionen,
XML-Bearbeitung mit `deleteOldOnSave=1`, Einmalaufträge, gemeinsame Schreibsperre,
Schutz laufender und unklar zuordenbarer Dateien, Konflikte, unbekannte Ergebnisse
und Zeitumstellungen. Es gibt weiterhin keinen automatischen Schreib-Fallback
und keine Wiederholung bei unklaren Ergebnissen.

Die Protokollparameter wurden anhand primärer Quellen geprüft:

- [OpenWebif-HTTP-Endpunkte](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/web.py)
- [OpenWebif-Dateiendpunkt](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/file.py)
- [OpenWebif-XML-Aufnahmetags](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/views/web/movielist.tmpl)
- [OpenWebif-Aufnahme-Modell](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/models/movies.py)
- [OpenWebif-Pfade](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/models/locations.py)
- [Älterer FileStreamer](https://github.com/oe-alliance/enigma2-plugins/blob/master/webinterface/src/WebChilds/FileStreamer.py)
- [Ältere XML-Timerbearbeitung](https://github.com/oe-alliance/enigma2-plugins/blob/master/webinterface/src/WebComponents/Sources/Timer.py)
- [HTTPX-Streaming](https://www.python-httpx.org/quickstart/#streaming-responses)

Die Anwendung verwendet die HTTP-Schnittstellen; OpenWebif- oder
WebInterface-Quellcode wird nicht eingebunden. Der Nutzer hat Installation,
nginx, Receiver-Verbindungen und Sender/Bouquets auf Ubuntu bestätigt. Die
neuen Funktionen wurden hier mit simulierten Receivern geprüft, ohne echte
Receiver zu verändern. Die öffentliche HTTPS-Installation ließ sich aus dieser
Umgebung nicht direkt prüfen; der Proxytest prüft die korrigierte Asset-Einbindung.
Die Installation und Hardwareprüfung auf dem Zielserver stehen noch aus.
