# Enigma2 Timer 1.1.2

Eigenständige, zentral betriebene Webanwendung im Stil von AWAS 3.0.7.
AWAS und seine Datenbank werden nicht verändert.

Version 1.1.2 ersetzt private Netzwerkadressen in Beispielen und Tests durch
neutrale Werte. Das Git-Paket enthält auch die bereinigten früheren Release-Stände;
beim bestehenden GitHub-Repository ist die einmalige Umstellung nach
[GITHUB.md](GITHUB.md) erforderlich.
Installation und Update: [INSTALL.md](INSTALL.md). GitHub: [GITHUB.md](GITHUB.md).
[Release-Hinweise](RELEASE_NOTES.md), [Versionsverlauf](CHANGELOG.md),
[Prüfbericht](VERIFICATION.md) und [Herkunfts-/Lizenzhinweise](NOTICE.md).

## Stand dieser Version

Implementiert:

- deutsche, responsive Oberfläche mit der tatsächlichen AWAS-Gestaltung:
  violette Kopfleiste, hellvioletter Hintergrund, orangefarbene Aktionen,
  digiandi-Logo, 90 % Seitenbreite und mobile Navigation;
- Anmeldung und Abmeldung, Argon2id-Passwort-Hashes, serverseitige widerrufbare
  Sitzungen, CSRF-Schutz auch bei der Anmeldung, Anmeldebegrenzung;
- getrennte HTTP-/HTTPS-Sitzungscookies, automatische Secure-Cookies bei HTTPS,
  HttpOnly und SameSite;
- Administrator-/Benutzerrollen; Benutzer anlegen, bearbeiten, deaktivieren,
  löschen und Startpasswort zurücksetzen;
- erzwungener Passwortwechsel für neu angelegte Konten bzw. nach Passwort-Reset;
- Schutz des eigenen Administratorkontos und des letzten aktiven Administrators;
- Benutzerübersicht mit „Letzte Anmeldung“ wie bei AWAS, einschließlich vorhandener Login-Zeitpunkte;
- Receiver-Rechte pro Benutzer: kein Zugriff, Lesen oder Lesen und Schreiben;
  zusätzlich Wahl eines Standardreceivers, serverseitig geprüft;
- Receiver anlegen, bearbeiten, deaktivieren, löschen und testen;
- alphabetische Receiver-Reihenfolge ohne manuelles Sortierfeld;
- Eigentümerrechte: Benutzer ändern/löschen nur eigene Timer und Aufnahmen;
- Erstellerangabe „von …“ bei jedem Timer und jeder Aufnahme wie bei AWAS;
- sprechende Ersteller-Tags wie `e2web-owner-digiandi`, auch manuell am Receiver verwendbar;
- automatische Aktualisierung von Timern und Aufnahmen alle fünf Sekunden;
- sofortige Listenfilter: Timer nach Sender/Titel, Aufnahmen nach Sender/Dateiname/Titel;
  Filtertext bleibt bei der automatischen Aktualisierung einschließlich Cursorposition erhalten;
- verschlüsselte Receiver-Passwörter mit persistentem separatem Schlüssel;
- Receiver-Auswahl rechts neben der großen Überschrift, mit direkter Umschaltung;
- Timer-Kopfzeile mit Receiverauswahl, Listenfilter und „Timer erstellen“ in dieser Reihenfolge;
- Filterfelder und Receiverauswahl mit gleicher Höhe auf Desktop und mobil;
- nach jeder Anmeldung automatisch den vom Administrator festgelegten Receiver wählen;
- mittiges Login-Formular ohne Slogan; relative CSS-/JavaScript-URLs für HTTPS hinter nginx;
- Seitenname „Enigma2 Timer“ mit Untertitel „Aufnahmen-Verwaltung“;
- dezente Fußzeile mit Version, Release-Datum und Anzeigezeitzone;
- Timer als Startseite; Menüfolge Timer, Sender, Aufnahmen, Receiver, Benutzer;
- Receiver- und Benutzerverwaltung nur für Administratoren, mit orangefarbener
  Überschrift „Administration“ wie bei AWAS;
- Senderlisten für TV und Radio: Bouquets und Anbieter; Standardauswahl TV/Bouquets;
- Sender in der Reihenfolge des Receivers, Gruppenüberschriften und Namensfilter;
- Sender-EPG mit Datumsauswahl, Beginn/Ende, Dauer, laufender Sendung und
  aufklappbaren Sendungsdetails;
- Timerliste mit Bereichen „Laufend (x)“ und „Anstehend (x)“, Dateinamen und
  Dateigrößen ausschließlich bei laufenden Timern; AWAS-Spalten Aufnahme, Sender, Receiver, Start, Ende, Dauer und
  Status; direkt sichtbarer Beschreibung, Wiederholung und
  aufklappbarem Verlauf; ohne Beschreibung entfällt die entsprechende Zeile;
- gemeinsame große Überschriften wie „Timer: Vu+ Zero“, „Sender: Vu+ Zero“ und
  „Aufnahmen: Vu+ Zero“;
- Timerformular mit gemeinsamer TV-/Radio-Bouquetauswahl und direkt geladener
  Senderliste, erstem Bouquet/Sender vorausgewählt und tatsächlichem Standardpfad;
- bündige Felder für Beginn und Ende, gemeinsamer Hinweis unter beiden Feldern;
- Senderangaben in Timern und Aufnahmen mit kleiner grauer TV-/Radiozeile
  oberhalb und Bouquetnamen unterhalb des Sendernamens;
- neutrale Oberfläche ohne Du-Ansprache; Senderübersicht ohne Erklärungssatz;
- Aufnahme-Timer direkt im Timerbereich sowie aus Senderliste und EPG anlegen, bearbeiten, deaktivieren
  und löschen; Vor-/Nachlauf aus dem EPG und beliebige Wochentagswiederholungen;
- Bearbeiten auch laufender Timer und von Timern über die ältere XML-Schnittstelle;
- Aufnahmelisten mit direkt ausgewähltem Receiver-Standardpfad und Unterordnern
  in einer gemeinsamen Ordnerauswahl ohne separate Unterordnerbuttons;
  AWAS-Spaltenfolge, Datum/Uhrzeit und Laufzeit, separate Dateinamenzeile mit
  Dateigröße; Download, Löschung und Schutz laufender Aufnahmen;
- laufende Aufnahmen in Timern und Aufnahmelisten orange wie bei AWAS (`#fde7dc`);
- 90 Sekunden Lesezeitlimit für Aufnahmelisten und Downloads zum HDD-Anlauf;
- alle Löschbuttons mit zwei Klicks: zunächst „Wirklich löschen?“ auf rotem
  Hintergrund, beim zweiten Klick innerhalb von fünf Sekunden ausführen; danach
  automatisch zurücksetzen, genau wie AWAS; Ergebnis direkt in der jeweiligen Liste;
- Empfang und Anzeige von Timerkonflikten, Erhalt vorhandener Zusatzoptionen,
  Schutz gegen doppelte Formularsendungen und Änderungen aus alten Browser-Tabs;
- OpenWebif-JSON-Abfrage mit XML-Fallback bei fehlendem JSON-Endpunkt;
- SQLite/WAL, Alembic-Migration und sicherheitsrelevante Audit-Ereignisse.

Timer werden nur nach ausdrücklichem Speichern bzw. bestätigtem Löschen
auf dem ausgewählten Receiver geändert. Aufnahmen werden ausschließlich
über den Löschbutton in der Aufnahmeliste entfernt.

Der endgültige Funktionsumfang ist ausschließlich:

1. Senderlisten (Bouquets/Anbieter) anzeigen.
2. Timer erstellen, bearbeiten und löschen.
3. EPG anzeigen und daraus Timer erstellen.
4. Aufnahmen anzeigen, herunterladen und löschen.

Anmeldung, Benutzer- und Receiververwaltung dienen dieser zentralen Anwendung.
Fernbedienung, Screenshots, Umschalten, Live-TV, Systeminformationen und
Receiver-Konfiguration bleiben in den Originaloberflächen.

## Lokal starten

Voraussetzung: Python 3.12 oder neuer. Im entpackten Projektverzeichnis:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
e2web init
e2web create-admin
e2web serve
```

Öffnen: <http://127.0.0.1:8081>. Der erste Administrator wird interaktiv erstellt;
es gibt keine Standardzugangsdaten und keine öffentliche Registrierung.
Unter **Receiver** eine Box hinzufügen und **Verbindung testen** drücken.

`e2web init` legt `e2web.toml`, `data/receiver.key` und `data/e2web.db` an und
führt Migrationen aus. Es überschreibt keine vorhandene Konfiguration oder
Schlüssel. Bei vorhandener Datenbank und fehlendem Schlüssel bricht es ab.

Andere Konfiguration verwenden:

```bash
e2web --config /etc/e2web/e2web.toml migrate
e2web --config /etc/e2web/e2web.toml create-admin
e2web --config /etc/e2web/e2web.toml serve
```

Alternativ `E2WEB_CONFIG` setzen. Relative `data_dir`-Pfade beziehen sich auf
das Verzeichnis der Konfigurationsdatei, nicht auf das aktuelle Arbeitsverzeichnis.

## Auf Debian/Ubuntu installieren

Im Projektverzeichnis ausführen:

```bash
sudo bash scripts/install.sh
sudo -u e2web-service /opt/e2web/.venv/bin/e2web \
  --config /etc/e2web/e2web.toml create-admin
sudo systemctl enable --now e2web
```

Der Installer stellt den Dienst bereit, startet ihn aber nicht vor der Anlage
des Administrators. Er benötigt Python 3.12+, `python3-venv`, `rsync` und
Zugang zum Python-Paketindex. Diese Systempakete bei Bedarf zuvor installieren.
Es werden weder nginx-Konfigurationen aktiviert noch vorhandene AWAS-Dateien
verändert. Der Nutzer hat die Erstinstallation und nginx-Anbindung für Version
0.1.0 auf Ubuntu bestätigt. Die Timer- und Aufnahmefunktionen von 1.1.2 wurden mit
simulierten Receivern geprüft; die Prüfung an der tatsächlichen Hardware steht noch aus.

Pfade:

| Zweck | Pfad |
|---|---|
| Anwendung | `/opt/e2web/app` |
| Python-Umgebung | `/opt/e2web/.venv` |
| Konfiguration | `/etc/e2web/e2web.toml` |
| Datenbank | `/var/lib/e2web/e2web.db` |
| Verschlüsselungsschlüssel | `/var/lib/e2web/receiver.key` |
| Dienst | `e2web.service` |
| Interner Port | `127.0.0.1:8081` |

Für nginx ist `deploy/nginx-location.conf` eine Vorlage für den Inhalt eines
eigenen Serverblocks. Hostname und vorhandene HTTPS-Zertifikate werden im
bestehenden nginx-Setup eingerichtet. Die Anwendung vertraut Proxy-Headern nur
von `127.0.0.1` und `::1`. Bei HTTPS kann zusätzlich `cookie_secure = true`
gesetzt werden; dann funktionieren Anmeldungen nur über HTTPS.

## Receiver-Zugriff

Die Verbindung erfolgt vom Server aus. Receiver-Adressen, Benutzernamen und
Passwörter werden regulären Benutzern nicht ausgegeben. Der Server benötigt
Netzzugriff auf die Boxen. Private LAN-Adressen sind ausdrücklich erlaubt;
nur Administratoren können Verbindungsziele konfigurieren.

Der Verbindungstest liest `/api/getservices`. Bei HTTP 404/405 erfolgt ein
Fallback auf `/web/getservices`. Es werden keine Timer angelegt oder gelöscht
und keine Receiver-Funktionen ausgelöst. Eine gültige leere Senderliste zählt
ebenfalls als erfolgreiche API-Verbindung. Umleitungen werden nicht verfolgt.

HTTPS-Zertifikatsprüfung ist standardmäßig aktiviert; sie kann bei einem
selbstsignierten Receiver-Zertifikat ausdrücklich für diese Box abgeschaltet
werden. Bei HTTP ist die Strecke zwischen zentralem Server und Box unverschlüsselt.
Receiver mit herstellerspezifischer API-Sitzungsprüfung können weitere
Adapteranpassungen erfordern; Zugriffseinstellungen nicht pauschal abschalten.

API-Referenz: <https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/wiki/OpenWebif-API-documentation>.
Die Sender- und EPG-Feldnamen wurden außerdem anhand des primären
[OpenWebif-Adapters](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/models/services.py)
geprüft.
Timer-Felder und Änderungsparameter wurden anhand der primären
[Timer-Implementierung](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/models/timers.py)
und der
[HTTP-Endpunkte](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/web.py)
geprüft.
Die Aufnahmeformate und Löschparameter wurden mit dem
[Aufnahme-Modell](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/models/movies.py)
und den XML-Templates abgeglichen. Downloads wurden anhand des primären
[OpenWebif-Dateiendpunkts](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/plugin/controllers/file.py)
und des älteren
[FileStreamer](https://github.com/oe-alliance/enigma2-plugins/blob/master/webinterface/src/WebChilds/FileStreamer.py)
geprüft. Die ältere Timerbearbeitung wurde außerdem
anhand der primären
[WebInterface-Implementierung](https://github.com/oe-alliance/enigma2-plugins/blob/master/webinterface/src/WebComponents/Sources/Timer.py)
geprüft: `deleteOldOnSave=1` wählt dort die Änderung des vorhandenen Timers.
Es wird kein OpenWebif-Quellcode in die Anwendung eingebunden.


Unter **Benutzer → Bearbeiten** kann ein Administrator Receiver einzeln zuweisen.
**Lesen** erlaubt Sender, EPG, Timer und Aufnahmen anzusehen sowie Aufnahmen
herunterzuladen. **Lesen und Schreiben** erlaubt zusätzlich Timer anzulegen,
eigene Timer zu bearbeiten und zu löschen sowie eigene Aufnahmen zu löschen. Receiver mit
**Kein Zugriff** werden ausgeblendet und sind auch über direkte URLs nicht
zugänglich. Alternativ lassen sich alle aktivierten und künftig hinzugefügten
Receiver mit gemeinsamen Lese- oder Schreibrechten freigeben. Administratoren
haben immer Zugriff mit Schreibrechten auf alle aktivierten Receiver. Deshalb
entfällt die gesamte Berechtigungsauswahl bei der Rolle Administrator; der
Standardreceiver bleibt auswählbar.

### Letzte Anmeldung

Die Benutzerübersicht zeigt Administratoren in der Spalte **Letzte Anmeldung**
die letzte erfolgreiche Anmeldung jedes Kontos, wie bei AWAS im Format
`DD.MM.YYYY HH:MM` und in der konfigurierten Anzeigezeitzone (standardmäßig
`Europe/Berlin`). Ohne erfolgreiche Anmeldung steht **Noch nie**.
Die bereits vorhandenen erfolgreichen Login-Ereignisse werden berücksichtigt;
Fehlversuche, Seitenaufrufe, Abmeldung und Passwortänderungen ersetzen den
Zeitpunkt nicht. Für diese Anzeige ist keine neue Datenbankmigration notwendig.

### Eigene Timer und Aufnahmen

Ab Version 0.8.0 erhält jeder neu über diese Anwendung angelegte Timer einen
sprechenden Ersteller-Tag mit dem Benutzernamen, beispielsweise
`e2web-owner-digiandi` oder `e2web-owner-thomas.meyer`. Derselbe Tag gilt für
alle Sender und Receiver eines Kontos. Die Anwendung erzeugt keine weiteren
Tags. Bei wiederkehrenden Timern bleibt der Tag erhalten; zusätzliche vorhandene
Receiver-Tags bleiben beim Bearbeiten erhalten. OpenWebif übernimmt die Tags in
die Aufnahmemetadaten, sodass eine Aufnahme ihrem Ersteller auch nach dem Entfernen
des Timers zugeordnet bleibt.

Administratoren finden den genauen **Ersteller-Tag** unter **Benutzer → Bearbeiten**.
Alle vorhandenen Benutzerkonten erhalten beim Update einen solchen Tag, auch ohne
bisher einen Timer in der Anwendung erstellt zu haben. Neue Konten werden bei ihrer
Anlage registriert. Die Datenbank bindet den Tag an das konkrete Konto; die Anzeige
verwendet weiterhin dessen Anzeigenamen.

Für eine manuelle Zuordnung in der Originaloberfläche des Receivers:

1. Den gewünschten Timer öffnen und dessen Tags bearbeiten.
2. Vorhandene Tags mit dem Präfix `e2web-owner-` durch den Ersteller-Tag des
   gewünschten Benutzers ersetzen; alle anderen Tags können erhalten bleiben.
3. Speichern. Enigma2 Timer übernimmt die Zuordnung mit der nächsten Aktualisierung.

Genau ein Ersteller-Tag muss vorhanden sein. Unbekannte oder mehrere Ersteller-Tags
ergeben keine Zuordnung. Der Benutzer benötigt zusätzlich Schreibrechte auf dem
jeweiligen Receiver, um seine Timer und Aufnahmen zu ändern oder zu löschen.
Neue Aufnahmen übernehmen den Timer-Tag; bereits angelegte Aufnahmedateien werden
durch das Ändern eines Timers nicht nachträglich umgeschrieben. Liefert die
Originaloberfläche eine Tagbearbeitung für Aufnahmen, wird auch dort der
entsprechende Ersteller-Tag erkannt.

Die zufälligen Kennungen aus 0.6.0 bis 0.7.3 bleiben mit ihren bisherigen
Datenbankzuordnungen gültig. Beim Speichern eines solchen Timers wird seine gültige
Kennung durch den sprechenden Tag seines bisherigen Erstellers ersetzt, auch wenn
ein Administrator ihn bearbeitet. Alte Aufnahmen behalten ihre bisherige gültige
Kennung. Das Update selbst ändert keine Timer oder Dateien auf Receivern.

Nach dem Löschen eines Kontos bleibt dessen Tag reserviert und ohne Ersteller.
Wird derselbe Benutzername erneut angelegt, bekommt das neue Konto einen weiterhin
sprechenden Tag wie `e2web-owner-digiandi-konto-2`. Damit übernimmt es keine alten
Aufnahmen oder Rechte. Maßgeblich ist stets der im Benutzerformular angezeigte Tag.

Bei jedem Timer und jeder Aufnahme steht unter dem Titel bzw. der Wiederholung
klein und grau **von Anzeigename** wie bei AWAS. Die Anzeige verwendet ausschließlich
die Zuordnung des Tags zur lokalen Benutzerdatenbank und bleibt auch für
Leseberechtigte sichtbar. Nach Entfernen eines Timers bleibt der Ersteller seiner
Aufnahmen erkennbar, wenn die Aufnahme-Tags erhalten sind. Ohne gültige Zuordnung
oder nach Löschen des Benutzerkontos steht **von unbekannt**; es wird kein
Ersteller anhand von Sendungsnamen oder Aufnahmezeit geraten.

Normale Benutzer mit Schreibrechten können ausschließlich eigene Timer
bearbeiten/löschen und eigene Aufnahmen löschen. Mit Leserechten entfällt auch
das. Administratoren dürfen alle Timer bearbeiten/löschen und alle beendeten
Aufnahmen löschen. Alle freigegebenen Inhalte bleiben unabhängig vom Ersteller
sichtbar und Aufnahmen herunterladbar. Eigentümer werden vor Schreibaufträgen
serverseitig erneut geprüft; ausgeblendete Buttons allein reichen dafür nicht.

Bestehende oder direkt am Receiver erstellte Einträge ohne gültigen Ersteller-Tag
bleiben ausschließlich durch Administratoren veränderbar. Dasselbe gilt, wenn
ein Receiver die Kennung entfernt oder keine Aufnahme-Tags liefert; die Anwendung
rät keine Eigentümer anhand von Titel oder Zeitpunkt. Alte zufällige Kennungen
bleiben an ihre ursprüngliche Receiveradresse und bei Timern an den Sender gebunden.
Sprechende Tags können bewusst auf anderen Sendern und Receivern verwendet werden;
sie erteilen dabei keine Receiverrechte. Gelöschte Konten verleihen keine Rechte
an spätere Konten. Änderungen der Anmeldedaten desselben Receivers erhalten
die Eigentümerzuordnung. Datenbank und Schlüssel müssen
bei einem Update erhalten bleiben.

### Listen filtern

Auf **Timer** steht das Eingabefeld **Liste filtern** in der Kopfzeile rechts
neben der Receiverauswahl und vor **Timer erstellen**. Es durchsucht ausschließlich Sendernamen und Timer-Titel,
auch im aufklappbaren Verlauf. Auf **Aufnahmen** steht das Feld rechts neben der
Ordnerauswahl und durchsucht Sendernamen, Dateinamen und Aufnahme-/Timer-Titel.
Beschreibungen, Ersteller, Receiver, Bouquets, Verzeichnispfade und Zeitangaben
sind keine Suchfelder. Groß-/Kleinschreibung wird ignoriert; ein Textteil genügt.

Die Filter wirken unmittelbar auf die angezeigte Liste und lösen keine
Schreibaufträge aus. Dateizeilen werden mit dem zugehörigen Eintrag ein- und
ausgeblendet. Bei der Fünf-Sekunden-Aktualisierung bleiben Suchtext, Fokus und
Cursorposition erhalten; neue und geänderte Einträge werden erneut gefiltert.
Beim Leeren des Felds erscheinen wieder alle Einträge. Die Bereichszahlen bei
Timern zeigen die Anzahl der passenden Einträge des jeweiligen Bereichs.

Bei Sendern stehen **Listen filtern** bzw. **Sender filtern** direkt im
Eingabefeld. Alle Filterfelder besitzen eine zugängliche Bezeichnung ohne
zusätzlichen sichtbaren Beschriftungstext. Bei Timern, Sendern und Aufnahmen
sind sie exakt so hoch wie das Dropdownmenü der Receiverauswahl.

### Automatische Aktualisierung

Timer und Aufnahmen werden bei sichtbarer Seite alle fünf Sekunden neu vom
Receiver abgefragt. Neue und entfernte Einträge, Status, Dateigröße und Laufzeit
werden übernommen. Laufende Timer zeigen die bislang verstrichene Dauer.
Aufnahmedauer und Dateigröße stammen aus den Receiverdaten.

Offene Timerverläufe und der Aufnahmeordner bleiben erhalten. Während einer
Löschbestätigung oder einer Ordner-/Receiverauswahl wird die Ersetzung der
Ansicht ausgesetzt. Bei langsamer Festplatte läuft immer nur eine Abfrage;
der nächste Versuch erfolgt nach ihrem Ende. Nicht sichtbare Browser-Tabs
pausieren die Abfragen. Unveränderte Löschaufträge werden für kurze Zeit
wiederverwendet, bleiben aber an Sitzung und Receiver gebunden und einmalig.

Laufende Aufnahmen können auch von Administratoren nicht gelöscht werden.
Zuerst den zugehörigen laufenden Timer beenden: Sein Löschbutton stoppt die
Aufnahme und entfernt den Timer (bei Wiederholungen die gesamte Serie),
behält aber die Aufnahmedatei. Erst danach erscheint deren Löschbutton.
Vor dem Löschen wird der aktuelle Timerstatus nochmals geprüft. Bei
nicht eindeutig prüfbarem Status bleibt das Löschen gesperrt.

Der **Standardreceiver** muss aktiviert und freigegeben sein. Er ist nach jeder
Anmeldung direkt ausgewählt; ein manueller Wechsel bleibt bis zur nächsten
Anmeldung in der Sitzung erhalten. Ist der Standardreceiver deaktiviert,
gelöscht oder nicht mehr freigegeben, wird der erste verfügbare Receiver
alphabetisch ausgewählt. Neue Benutzerformulare starten mit Einzelzuweisung
ohne freigegebene Receiver.

Alle Änderungen an bestehenden Benutzerkonten widerrufen deren Sitzungen.
Bei Änderung des eigenen Kontos ist deshalb eine erneute Anmeldung erforderlich.
Timer und Aufnahmen bleiben Receiver-Daten. Die lokale Datenbank enthält
Verwaltungs-/Authentifizierungsdaten, Audit-Ereignisse und befristete
Receiveraufträge zum Schutz vor mehrfacher Ausführung. Alte Aufträge werden beim
Ausstellen neuer Formularaufträge nach 24 Stunden bereinigt; ungesendete Formulare
laufen nach zwei Stunden ab.

## Senderlisten und EPG

Unter **Sender** zunächst TV/Radio und Bouquets/Anbieter wählen.
Die Übersicht öffnet standardmäßig TV und Bouquets. Beide Listenarten öffnen
ihre Senderliste. Bei einem Sender führt **EPG anzeigen** direkt zu dessen
Sendungen. Das EPG hat keinen eigenen Menüpunkt; der Bereich **Sender** bleibt
während der EPG-Anzeige aktiv. **Zur Übersicht** steht bei geöffneten Senderlisten
in derselben Auswahlzeile wie TV, Radio, Bouquets und Anbieter. Der Namensfilter verändert die Reihenfolge nicht.
Gruppenüberschriften haben keine EPG- oder Timeraktion.

Die Anbieterübersicht nutzt `getservices` mit einer Enigma2-Abfrage
`FROM PROVIDERS ORDER BY name`, einschließlich der TV-/Radio-Servicetypen.
Damit funktioniert die Abfrage auch über die ältere XML-Schnittstelle.
Die bisherigen eigenen Auswahlbuttons Favoriten und Satelliten entfallen.
Persönliche Favoritenbouquets bleiben als normale Bouquets erreichbar.

Das EPG zeigt standardmäßig den heutigen Tag. Die Datumsauswahl bietet die
Tage, für die der Receiver Daten liefert, sowie **Alle verfügbaren Tage**.
Ein laufendes Programm, das vor Mitternacht begonnen hat, erscheint weiterhin
in der heutigen Ansicht. Leere EPG-Daten sind kein Verbindungsfehler.
Die verfügbaren Daten hängen vom EPG-Speicher der Box ab.

Zeiten werden anhand der Unix-Zeitstempel berechnet, standardmäßig in
`Europe/Berlin`, unabhängig von der Zeitzone des Ubuntu-Servers. Sommer- und
Winterzeit werden berücksichtigt. Bei einer Sendung über einen Zeitwechsel
werden die Zeitzonen-Kürzel zur Unterscheidung angezeigt. Optional in
`/etc/e2web/e2web.toml` eine andere IANA-Zeitzone einstellen, anschließend
den Dienst neu starten:

```toml
timezone = "Europe/Berlin"
```

Bei alten Konfigurationsdateien ohne diesen Eintrag gilt automatisch derselbe
Standard. Das EPG nutzt `/api/epgservice` mit XML-Fallback auf
`/web/epgservice` bei HTTP 404/405.

Der Receiverwechsel erfolgt sofort und führt zur Übersicht im aktuellen
Menübereich zurück. Sender-/Bouquetreferenzen der bisherigen Box werden dabei
verworfen. Aus dem EPG führt der Receiverwechsel zur Senderübersicht.
Die Receiverauswahl bleibt alphabetisch und nur auf zugewiesene
Receiver beschränkt.

## Senderangaben bei Timern und Aufnahmen

In der Spalte **Sender** stehen **TV** oder **Radio** über dem Sendernamen und
zugehörige Bouquets darunter, jeweils klein und grau. Ist ein Sender in mehreren
Bouquets, werden alle in der Reihenfolge des Receivers angezeigt. Die Anzeige
beschreibt die aktuelle Bouquetzuordnung, nicht den ursprünglichen Auswahlweg.
Timer werden über ihre Senderreferenz zugeordnet. Bei Aufnahmen wird zunächst
ein noch vorhandener Timer mit derselben Datei verwendet, andernfalls ein
eindeutiger Sendername aus dem Bouquetkatalog. Bei fehlenden oder mehrdeutigen
Daten stehen **Bouquet unbekannt** bzw. **TV/Radio unbekannt**, ohne eine Zuordnung
zu erraten. Namen allein beeinflussen niemals Bearbeitungs- oder Löschrechte.

Die TV-/Radio-Kataloge werden im Hintergrund geladen und fünf Minuten
zwischengespeichert. Neu geladene Angaben erscheinen mit der nächsten
Fünf-Sekunden-Aktualisierung. Fehler verzögern die eigentliche Timer-/Aufnahmeliste
nicht; eine fehlgeschlagene Abfrage wird frühestens nach 30 Sekunden wiederholt.
Ein Wechsel der Receiver-Verbindungsdaten verwirft die bisherige Zuordnung.

## Timer

Die Kopfzeile enthält rechts neben der Überschrift zuerst die Receiverauswahl,
dann **Liste filtern** und danach **Timer erstellen**. Auf schmalen Bildschirmen
steht die Receiverauswahl über Filter und Button.

**Timer** ist die Startseite. Die AWAS-Bereiche **Laufend (x)** und
**Anstehend (x)** zeigen jeweils die Anzahl ihrer Einträge. Auch bei null
Einträgen bleiben beide Bereiche mit einem kurzen Hinweis sichtbar. Vorbereitete
und deaktivierte Timer stehen unter Anstehend; erledigte Timer bleiben in einem
aufklappbaren Verlauf. Innerhalb der Bereiche wird nach Beginn sortiert.
Beschreibungen stehen direkt unter dem Namen; leere Beschreibungen entfallen.

Nur unter laufenden Timern steht eine eigene Dateizeile in derselben Monospace-Schrift
wie unter Aufnahmen: Dateiname links und Dateigröße rechts. Laufende
Aufnahmeblöcke bleiben bis einschließlich Dateizeile durchgehend orange.
Dateigrößen stammen aus der Aufnahmeliste des Receivers und aktualisieren sich
zusammen mit Status und Dauer alle fünf Sekunden. Die Zuordnung verwendet
eindeutige Dateinamen, keine Titelvergleiche. Eine Metadatenabfrage genügt je
Aufnahmeordner; abweichende, vom Receiver bestätigte Ordnernamen werden auch
über XML berücksichtigt. Fehlende Größen erscheinen als „Unbekannt“ und
verhindern keine Timerbearbeitung. Ohne zugeordnete Datei erscheint
„Noch keine Datei vorhanden“; laufende Umschalt-Timer erhalten einen passenden Hinweis.
Geplante, vorbereitete, deaktivierte und erledigte Timer zeigen keine Dateizeile.
Für sie werden auch keine Aufnahmelisten zur Dateigrößenanzeige abgefragt.

**Timer erstellen** öffnet direkt das Timerformular. Seine gemeinsame
Bouquet-Auswahl enthält zunächst die TV-Bouquets, darunter die Radio-Bouquets,
in der Reihenfolge des Receivers. Das erste Bouquet und dessen erster
aufnehmbarer Sender sind vorausgewählt. Unter der Bouquet-Auswahl steht die
Senderliste dieses Bouquets. Ein Wechsel lädt die passende Liste und wählt
wieder deren ersten Sender; Gruppenüberschriften und Untergruppen sind keine
aufnehmbaren Sender. Bei leeren Bouquets bleibt Speichern gesperrt, bis ein
verfügbarer Sender gewählt wurde. Zeiten, Beschreibung und ein selbst
vergebener Name bleiben bei Bouquetwechseln erhalten. Ein automatisch gesetzter
Sendername folgt der neuen Senderauswahl. Wechselnde Anfragen können keine
veraltete Senderliste über eine neuere Auswahl schreiben.

Die Bouquet-/Senderabfragen legen keine Timer an. Erst **Timer speichern**
sendet einen Auftrag. Der ausgewählte Sender wird vor dem Schreiben erneut
im aktuellen Bouquet des ausgewählten Receivers geprüft. Lese-/Schreibrechte,
Sitzungsbindung und die vorhandene Receiversperre gelten unverändert.

Sender- und EPG-Links öffnen weiterhin Entwürfe mit ihrer konkreten Auswahl.
Bei einer Auswahl aus einem Bouquet ist die gemeinsame Bouquetauswahl ebenfalls
verfügbar. EPG-Entwürfe behalten ihre Sendungsdaten und Vor-/Nachlauf. Diese
Minuten werden vom eingegebenen Beginn abgezogen bzw. zum Ende addiert.

Ohne ausgewählte Wochentage ist ein Timer einmalig. Alle sieben Wochentage
bedeuten täglich, Montag bis Freitag werktäglich; jede andere Kombination
wird ebenfalls unterstützt. Die wiederholten Termine richtet der Receiver
nach seiner eigenen Zeitzone ein. Seine Zeitzone und die konfigurierte
Anzeigezeitzone sollten deshalb übereinstimmen.

Aufnahmepfade kommen vom Receiver. Der tatsächliche Standardpfad ist direkt
ausgewählt; der bisherige generische Eintrag „Standardpfad des Receivers“
entfällt. Fehlt die Standardangabe in der Timerliste, wird sie über die
Receiver-Pfadabfrage ermittelt. Ein unbekannter Standard wird nicht durch den
ersten Bookmark ersetzt. Sind Aufnahmepfade verfügbar, bleibt das Formular
geöffnet und verlangt die ausdrückliche Auswahl eines Pfads. Ohne Auswahl ist
Speichern im Browser und auf dem Server gesperrt. Nur wenn der Receiver gar
keinen verwendbaren Pfad liefert, erscheint eine Fehlermeldung. Bei vorhandenen Timern bleibt deren gewählter Pfad
ausgewählt. Neue Timer sind Aufnahme-Timer und lösen
nach ihrem Ende keine Standby-/Ausschaltaktion aus. Bei vorhandenen Timern
bleiben Timerart, Endaktion, zusätzliche Tags, EIT sowie verfügbare VPS-, Aufnahme- und
weitere Zusatzoptionen erhalten. Ein vorhandener Umschalt-Timer wird als
solcher gekennzeichnet. Laufende Timer lassen sich ebenfalls bearbeiten;
beispielsweise kann ihr Ende verlängert werden. Welche Änderung während der
Aufnahme wirksam wird, entscheidet der Receiver.

Beim Löschen ändert der erste Klick den Button zu **Wirklich löschen?** und
färbt ihn rot wie AWAS; erst der zweite Klick innerhalb von fünf Sekunden
sendet den Auftrag. Nach fünf Sekunden ohne Bestätigung steht wieder **Löschen**
auf dem Button. Code, Farben und Blinkverhalten entsprechen AWAS; bei reduzierter
Bewegung bleibt der Button während der Bestätigung durchgehend rot. Es gibt kein Popup
und keine separate Bestätigungs- oder Ergebnisseite. Hinweise stehen direkt
in der Timerliste. Die Bestätigung gilt für den angezeigten Receiver und Timer.
Bei wiederkehrenden Timern wird die gesamte Serie entfernt. Eine laufende
Aufnahme wird dadurch beendet; dieser Hinweis steht direkt beim Löschbutton.
Beginnt ein Timer erst nach dem Laden der Liste zu laufen, muss das Löschen
in der aktualisierten Liste erneut mit zwei Klicks bestätigt werden. Gespeicherte
Aufnahmedateien werden durch die Timerlöschung nicht gelöscht.

Formulare sind an Sitzung und Receiver gebunden. Vor Änderungen werden
Berechtigungen, Receiverkonfiguration und vorhandener Timer erneut geprüft.
Parallele Schreibaufträge derselben Box werden nacheinander zugelassen.
Veraltete Formulare und bereits verwendete Aufträge werden abgewiesen.

Die Timerliste nutzt `/api/timerlist` mit XML-Fallback auf `/web/timerlist`.
Anlegen, Bearbeiten und Löschen funktionieren über beide Schnittstellen.
Beim Bearbeiten werden die alte Senderreferenz und die bisherigen Zeiten sowie
`deleteOldOnSave=1` übertragen, damit auch das ältere WebInterface den
vorhandenen Timer ändert. XML liefert je nach Receiver weniger Zusatzoptionen
als JSON. Die Anwendung erhält die übertragenen Optionen; für nicht gelieferte
Plugin-Optionen kann der Receiver seine Standardwerte einsetzen.
Aufnahmepfade älterer XML-Receiver kommen aus `/web/getlocations`;
ist dieser Endpunkt nicht verfügbar, bleibt der Standardpfad nutzbar.

Änderungen erfolgen per POST an `timeradd`, `timerchange` bzw. `timerdelete`,
mit genau einem Sendeversuch über die zuvor gelesene Schnittstelle. Ein
Schreibauftrag wird bei Fehlern weder über einen anderen Endpunkt noch
automatisch erneut gesendet. Bei unklarer Bestätigung zuerst die Timerliste
prüfen. Bei einer abgelehnten Änderung gilt das ebenfalls: OpenWebif kann
Timerdaten bereits vor seiner Konfliktprüfung verändert haben. Nach einem
Konflikt beim Anlegen bleibt der Entwurf korrigierbar; verfügbare Konflikt-Timer
werden angezeigt.

Die Zeitangaben behalten ihre Sekunden. Nicht existierende Uhrzeiten bei der
Sommerzeitumstellung werden abgewiesen. Für doppelte Uhrzeiten im Herbst ist
unter **Doppelte Uhrzeit bei der Zeitumstellung** das erste oder zweite
Vorkommen wählbar; bestehende unveränderte Termine behalten ihr Vorkommen.

## Aufnahmen

**Aufnahmen** zeigt die Dateien im Standardpfad der Box. Über **Ordner** lassen
sich die angebotenen Aufnahmepfade und die vom Receiver gemeldeten Unterordner
des aktuellen Ordners auswählen. Separate Unterordnerbuttons entfallen.
Auch der aktuelle Ordner und seine freigegebenen übergeordneten Ordner bleiben
im Dropdown erreichbar. Neue Unterordner erscheinen mit der automatischen
Aktualisierung; weitere Ebenen nach Auswahl des betreffenden Ordners.
Es wird kein kompletter Verzeichnisbaum rekursiv vom Receiver geladen. Der tatsächliche
Standardpfad ist direkt ausgewählt; der Button für den übergeordneten Ordner entfällt. Die Liste ist nach Aufnahmezeit absteigend
sortiert. Unbekannte Zeiten, Größen oder Laufzeiten bleiben als solche sichtbar.
Die Liste aktualisiert sich alle fünf Sekunden; deshalb entfällt der Button
**Neu laden**.


Die Tabelle entspricht AWAS: **Aufnahme, Sender, Receiver, Beginn, Dauer, Status**.
Der Dateiname steht in einer eigenen Zeile am unteren Rand in derselben
Monospace-Schrift, rechts daneben die Dateigröße. Laufende Dateien sind über
beide Zeilen durchgehend orange. Datum/Uhrzeit verwenden `DD.MM.YYYY HH:MM`,
Laufzeiten `HH:MM:SS`. Aufklappbare Sendungsdetails entfallen. Die Anzeigezeitzone,
Version und das Release-Datum stehen ausschließlich in der Fußzeile.
Die Erstellerzeile **von …** steht wie bei AWAS klein und grau unter dem Titel.
Der bisherige Hinweis „Zum Beenden den laufenden Timer öffnen.“ entfällt;
laufende Dateien bleiben bis zum Beenden des Timers gegen Löschen geschützt.

**Herunterladen** reicht die vom Receiver gelistete Datei direkt an den Browser
weiter, ohne sie auf dem Webserver vollständig zwischenzuspeichern. Das gilt
auch für laufende Dateien und Benutzer mit Leserechten. Einzelne HTTP-Byte-Bereiche
werden unterstützt. Receiverzugangsdaten bleiben auf dem Server; nach längeren
Leseanfragen wird die Berechtigung vor dem Download erneut geprüft. Der Download
nutzt `/file?action=download&file=…`, mit begrenzter Unterstützung für eine
Umleitung zum selben Receiver unter `/file/`. Dateinamen mit wörtlichen
Prozent-Escapes wie `%2f` werden wegen abweichender Dekodierung älterer
WebInterfaces abgewiesen.

Für Aufnahmelisten und Downloads gilt standardmäßig ein separates Lesezeitlimit
von **90 Sekunden**, auch bei vorhandener Konfiguration ohne neuen Eintrag.
Sender, EPG und Timer behalten das bisherige Receiver-Zeitlimit. Optional:

```toml
recording_timeout = 90.0
```

Nach einer Änderung den Dienst neu starten. Das nginx-Lesezeitlimit muss länger
sein; die Vorlage verwendet **300 Sekunden**, auch für den XML-Fallback.

Der Löschbutton arbeitet mit derselben Bestätigung durch zwei Klicks wie Timer,
Receiver und Benutzer. Die Anwendung liest die Datei vor dem Auftrag erneut
und sendet genau einen POST an `moviedelete`, ausschließlich mit der vom
Receiver gelieferten vollständigen Dateireferenz. Enigma2 behandelt die
Aufnahmedatei und ihre Begleitdateien; OpenWebif berücksichtigt dabei einen
auf dem Receiver aktivierten Papierkorb. Ein erzwungener Löschparameter wird
nicht gesendet. Das ältere WebInterface kann direkt von der Festplatte löschen.

Laufende Aufnahmen lassen sich erst nach dem Beenden ihres Timers löschen.
Der Status wird auch unmittelbar vor dem Löschen erneut geprüft. Liefert die
Box für eine laufende Aufnahme keinen Dateinamen, bleibt die Löschung aller
Aufnahmen bis zu einer eindeutigen Zuordnung gesperrt. Ist die Timerliste nicht
erreichbar, wird die Aufnahmeliste angezeigt, aber die Löschung deaktiviert.

Die Liste verwendet `movielist`, Aufnahmepfade verwenden `getlocations`, jeweils
mit JSON und XML-Fallback bei HTTP 404/405. Fehler beim Löschen werden direkt
in der Aufnahmeliste angezeigt. Auch bei verlorener Antwort wird nicht erneut
gesendet; zuerst die aktuelle Liste und gegebenenfalls den Receiver prüfen.
Timer- und Aufnahmeschreibvorgänge teilen sich dieselbe Receiversperre.

### Korrektur in 0.6.1: Aufnahmepfade nach dem Löschen

Ein Receiver kann einen konfigurierten Pfad wie `/hdd/movie/` in seiner Antwort
als `/media/hdd/movie/` melden. Bis 0.6.0 konnte dadurch nach erfolgreichem
Löschen beim erneuten Laden ein Fehler 403 erscheinen; auch Downloads,
Unterordner und Aktualisierungen konnten betroffen sein. Die Aufnahme war
trotz der Meldung bereits gelöscht.

Die Anwendung prüft jetzt bei abweichenden Pfaden die vom Receiver tatsächlich
zurückgegebenen Ordner seiner freigegebenen Aufnahmepfade. Nur diese bestätigten
Ordner und ihre Unterordner werden akzeptiert. Es wird keine bestimmte
Symlinkbeziehung vorausgesetzt und kein fremder Wunschpfad zur Prüfung geladen.
Nach erfolgreichem Löschen bleibt die aktuelle Aufnahmeliste erreichbar.

## Update von 0.1.x bis 1.1.1 auf 1.1.2

Das neue Paket auf den Ubuntu-Server übertragen, entpacken und aus dem neuen
Projektverzeichnis den Installer erneut ausführen. Als root:

```bash
unzip enigma2-web-v1.1.2.zip
cd enigma2-web-v1.1.2
bash scripts/install.sh
curl --retry 10 --retry-delay 1 --retry-connrefused http://127.0.0.1:8081/health
```

Der Installer hält den laufenden Dienst während des Updates an und startet ihn
anschließend wieder. Der Health-Aufruf wartet bei Bedarf auf den Dienststart.
Die erwartete Antwort enthält `"version":"1.1.2"`.

Die vorhandenen Benutzer, Receiver, Passwörter, Sitzungen, die Konfiguration
und der Verschlüsselungsschlüssel werden weiterverwendet. Ein Administrator
muss nicht erneut angelegt werden. Ein bereits angepasster Port bleibt erhalten;
standardmäßig wird Port 8081 verwendet. Bei einem anderen Port den Health-Aufruf
entsprechend anpassen. In der vorhandenen nginx-Site das Lesezeitlimit auf
300 Sekunden erhöhen (siehe nächsten Abschnitt); der Installer verändert nginx nicht.

Die Datenbank wird automatisch auf Revision `0005` migriert. Von 0.8.0 bis 1.1.1 auf 1.1.2 ist keine neue Schemaänderung nötig. Vorhandene Konten,
Receiverzuordnungen, Sitzungen, Audit-Ereignisse und alte Eigentümerkennungen
bleiben erhalten. Die neue Migration ergänzt sprechende Ersteller-Tags für alle
vorhandenen Konten. Frühere Revisionen ergänzen weiterhin Eigentümerkennungen,
verschlüsselte Einmalaufträge, Standardreceiver und Lese-/Schreibrechte. Bereits geöffnete Formulare
einer älteren Version müssen nach dem Update neu geladen werden.
Vorhandene Timer und Aufnahmen ohne nachweisbaren Ersteller bleiben sichtbar
und herunterladbar, sind für normale Benutzer aber nicht bearbeitbar/löschbar.
Das bisherige interne Sortierfeld bleibt
zur Kompatibilität in der Datenbank, wird aber weder angeboten noch ausgewertet.
Alle Receiverlisten werden unabhängig davon alphabetisch nach Namen sortiert,
ohne Unterscheidung zwischen Groß- und Kleinschreibung.


### nginx-Zeitlimit und HTTPS

Im vorhandenen `location /` des eigenen e2web-Serverblocks
(`/etc/nginx/sites-available/e2web`, sofern unter diesem Namen eingerichtet)
sollten diese Direktiven stehen. Vorhandene gleichnamige Direktiven ändern,
nicht ein zweites Mal hinzufügen:

```nginx
proxy_pass http://127.0.0.1:8081;
proxy_set_header Host $host;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For $remote_addr;
proxy_set_header X-Real-IP $remote_addr;
proxy_read_timeout 300s;
```

Danach als root:

```bash
nginx -t && systemctl reload nginx
```

CSS, JavaScript und Logo verwenden jetzt URLs wie `/static/app.css?v=1.1.2`.
Der Browser lädt sie dadurch unter derselben HTTPS-Adresse wie die Seite.
Das verhindert HTTP-Asset-URLs und Mixed Content bei einer HTTPS-Verbindung
zum Proxy. Der Proxy-Header ist weiterhin für sichere Sitzungscookies wichtig.
Nach dem Update die Seite neu laden; die Asset-Version verhindert alte
CSS-/JavaScript-Dateien im Browsercache.

## Prüfen und sichern

```bash
ruff check .
pytest
e2web --config /etc/e2web/e2web.toml migrate
curl http://127.0.0.1:8081/health
```

Tests verwenden simulierte OpenWebif-Antworten. Echte Receiver wurden aus
dieser Entwicklungsumgebung nicht erreicht oder verändert. Nach Installation
ist der Verbindungstest daher die erste Prüfung an der eingesetzten Hardware.

Konfiguration, Datenbank **und Schlüssel** zusammen sichern. Der Schlüssel ist
für die Entschlüsselung der gespeicherten Receiver-Passwörter erforderlich.
Für eine einfache konsistente Kopie den Dienst stoppen und anschließend wieder
starten; bei laufendem SQLite niemals nur die Hauptdatei ohne WAL berücksichtigen.
Das Quellpaket enthält keine echten Zugangsdaten, Schlüssel oder Datenbanken.

## Vollständig deinstallieren

Die folgenden Befehle als root entfernen den Dienst und seine Installation.
Dabei werden auch alle Benutzerkonten, Receiverzuordnungen und gespeicherten
Receiverzugänge einschließlich des Verschlüsselungsschlüssels gelöscht.

```bash
systemctl disable --now e2web
systemctl reset-failed e2web 2>/dev/null || true
rm -f /etc/nginx/sites-enabled/e2web /etc/nginx/sites-available/e2web
nginx -t && systemctl reload nginx
rm -f /etc/systemd/system/e2web.service
systemctl daemon-reload
rm -rf -- /opt/e2web /etc/e2web /var/lib/e2web
userdel e2web-service
```

Die nginx-Befehle gelten für den zuvor angelegten eigenen Site-Eintrag `e2web`.
Bei einer Einbindung in einen anderen Serverblock dort die zugehörige
Proxy-Konfiguration entfernen, anschließend `nginx -t` prüfen und nginx neu laden.
Heruntergeladene ZIP-Dateien und entpackte Projektordner, beispielsweise
`/root/enigma2-web-v0.1.0`, können danach ebenfalls entfernt werden.

## Weiterentwicklung

Der vorgesehene Kernumfang ist implementiert. Reale Antworten der eingesetzten
Receiver dienen jetzt der weiteren Kompatibilitätsprüfung.
