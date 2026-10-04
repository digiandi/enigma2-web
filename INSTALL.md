# Enigma2 Timer 1.1.2 installieren

Voraussetzungen: Ubuntu/Debian mit systemd, Python 3.12 oder neuer, `python3-venv`,
`rsync` und `unzip`. Der Server muss die Receiver erreichen können. Der Installer
benötigt beim ersten Einrichten und beim Update Zugang zum Python-Paketindex.

Die folgenden Befehle sind für eine Anmeldung als root geschrieben. Sie verwenden
den Standardport 8081. Ein anderer Port wird in `/etc/e2web/e2web.toml` mit
`port = 8082` eingestellt; danach den Dienst neu starten und sowohl den
nginx-Zielport als auch die Health-Abfragen entsprechend anpassen. Beim Update
bleibt ein bereits geänderter Port erhalten.

## Neuinstallation

Falls noch nicht vorhanden, die benötigten Pakete installieren:

```bash
apt update
apt install python3 python3-venv rsync unzip
python3 --version
```

Die angezeigte Python-Version muss mindestens 3.12 sein. Anschließend das
Installationspaket auf den Server übertragen und entpacken:

```bash
unzip enigma2-web-v1.1.2.zip
cd enigma2-web-v1.1.2
bash scripts/install.sh
runuser -u e2web-service -- /opt/e2web/.venv/bin/e2web \
  --config /etc/e2web/e2web.toml create-admin
systemctl enable --now e2web
curl --retry 10 --retry-delay 1 --retry-connrefused \
  http://127.0.0.1:8081/health
```

Der erste Administrator wird interaktiv angelegt; es gibt kein vorgegebenes
Passwort. Nach `systemctl enable --now e2web` startet die Anwendung auch beim
Systemstart. Der Installer allein richtet den Dienst ein, bevor der erste
Administrator angelegt und der Dienst aktiviert wird.

## Update einer vorhandenen Installation

Konfiguration, Datenbank und Schlüssel müssen erhalten bleiben. Die vorhandene
Installation verwendet `/etc/e2web/e2web.toml`, `/var/lib/e2web/e2web.db` und
`/var/lib/e2web/receiver.key`. Diese zusammen sichern, beispielsweise bei kurz
gestopptem Webdienst oder mit einer konsistenten SQLite-Sicherung.

Das neue Paket in einen neuen Ordner entpacken und als root ausführen:

```bash
unzip enigma2-web-v1.1.2.zip
cd enigma2-web-v1.1.2
bash scripts/install.sh
curl --retry 10 --retry-delay 1 --retry-connrefused \
  http://127.0.0.1:8081/health
```

Ein bereits laufender Webdienst wird während des Updates angehalten und wieder
gestartet. Ein Administrator muss nicht erneut angelegt werden. Die automatische
Migration erhält vorhandene Daten und verwendet Revision `0005`; beim Update von
0.8.0 oder 1.0.0 ist keine neue Schemaänderung erforderlich. Auf den Receivern werden durch
das Update keine Timer oder Aufnahmedateien verändert.

Erwartete Antwort:

```json
{"status":"ok","version":"1.1.2"}
```

Nach dem Update die Browserseite neu laden. Vorher geöffnete Timerformulare neu
öffnen, damit Version und Formularauftrag übereinstimmen.

## Vorhandenes nginx verwenden

Die Anwendung lauscht intern auf `127.0.0.1:8081`. Der Installer verändert keine
nginx-Konfiguration. Einen vorhandenen passenden HTTPS-Serverblock weiterverwenden
oder in einen eigenen Serverblock den Inhalt von `deploy/nginx-location.conf`
übernehmen:

```nginx
location / {
    proxy_pass http://127.0.0.1:8081;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_read_timeout 300s;
    client_max_body_size 1m;
}
```

Domain und vorhandene HTTPS-Zertifikate gehören in den eigenen Serverblock.
Nach einer Änderung an nginx:

```bash
nginx -t && systemctl reload nginx
```

## Betrieb

```bash
systemctl status e2web --no-pager
journalctl -u e2web -n 80 --no-pager
systemctl restart e2web
curl http://127.0.0.1:8081/health
```

Nach dem Anmelden unter **Receiver** die Geräte anlegen und **Verbindung testen**
verwenden. Unter **Benutzer** die Receiver sowie Lese-/Schreibrechte und
Standardreceiver zuweisen. Administratoren haben Schreibrechte auf alle
aktivierten Receiver.

Für Aufnahmelisten und Downloads gilt standardmäßig ein Lesezeitlimit von
90 Sekunden, damit eine Festplatte anlaufen kann. Anzeigezeitzone ist
standardmäßig `Europe/Berlin`. Weitere Konfiguration, Ersteller-Tags,
Bedienhinweise und vollständige Deinstallation stehen in [README.md](README.md).
