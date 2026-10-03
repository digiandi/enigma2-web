# Prüfung von Version 1.0.0

Prüfstand: 03.10.2026, Python 3.12 unter Linux.

- 235 automatisierte Tests erfolgreich (`pytest`).
- Statische Prüfung und Formatprüfung erfolgreich (`ruff`).
- Installer-Syntax erfolgreich (`bash -n scripts/install.sh`).
- Python-Wheel und Quelldistribution gebaut und geprüft: alle Seiten, CSS, JavaScript, Logo,
  Aufnahme-Downloads, Rechteverwaltung, NOTICE und fünf Migrationen enthalten.
- Wheel mit `pip` in ein separates Installationsverzeichnis installiert;
  CLI-Initialisierung, erneute Initialisierung mit erhaltenem Schlüssel,
  Schema `0005`, Aufnahmezeitlimit 90 Sekunden, Login und Health-Version geprüft.
- Quell-ZIP mit Tests und Installationshinweisen erstellt; keine Datenbanken,
  Schlüssel, Zugangsdaten, Testdownloads oder Browser-/Testumgebungen enthalten.
- Chromium-Browserlauf aus dem installierten Wheel mit lokalen HTTP-Receivern
  für JSON und XML erfolgreich; Login, Timerformular, Ersteller-Tag,
  versionierte Assets und HTTPS-Proxy geprüft;
  keine JavaScript-Fehler und keine Dialog-Popups.
- Breiten 390, 768, 1024, 1100, 1280 und 1440 Pixel geprüft; kein horizontaler
  Seitenüberlauf. Timer- und Aufnahmeansichten gerendert und visuell geprüft.
- Die umfassenden Funktionsprüfungen des unveränderten Stands 0.8.0,
  einschließlich langer Receivernamen, Löschbestätigung und Rechteabläufen,
  sind in dessen Abschnitt dokumentiert.

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
