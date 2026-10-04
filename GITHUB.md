# Version 1.1.2 auf GitHub bereitstellen

Das Git-Paket `enigma2-web-git-v1.1.2.zip` enthält ein vorbereitetes Repository
mit Branch `main` und den annotierten Tags `v1.0.0`, `v1.1.0`, `v1.1.1` und
`v1.1.2`. Private Netzwerkadressen wurden auch aus den drei früheren
Release-Ständen entfernt. Dadurch haben deren Commits und Tags neue Kennungen.
Die Reihenfolge, Versionsnummern und übrigen Inhalte der früheren Releases
bleiben erhalten. Die Autorenkennung lautet
`Enigma2 Timer Release <release@localhost>`. Ein Remote ist noch nicht eingerichtet.

## Bestehendes Repository einmalig bereinigen

Das neue Git-Paket in einen eigenen Ordner entpacken, einschließlich `.git`.
Die folgenden Befehle aus diesem neuen Ordner in PowerShell ausführen:

```powershell
git status --short --branch
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\github-bereinigen.ps1
git ls-remote origin refs/heads/main "refs/tags/v1.*"
```

Das Skript verwendet `https://github.com/digiandi/enigma2-web.git` und prüft
den zuvor bestätigten Remote-Stand. Es ersetzt `main` und die drei alten Tags
durch die bereinigten Stände und ergänzt `v1.1.2`. Alle fünf Referenzen werden
gemeinsam mit `--atomic` aktualisiert. Explizite `--force-with-lease`-Angaben
schützen vor dem Überschreiben eines zwischenzeitlich geänderten Stands.
Ein erneuter Aufruf bei bereits vollständig aktualisiertem Repository ist möglich.

Bei weiteren Branches, zusätzlichen Tags oder geänderten Commits bricht das
Skript vor dem Push ab. Diese Stände müssen zunächst ebenfalls bereinigt werden;
den Schutz nicht durch einen unbeschränkten erzwungenen Push umgehen.
Die Prüfausgabe des Skripts für eine erneute Abstimmung aufbewahren.
Die GitHub-Anmeldung erfolgt wie bisher über die Git-/Credential-Verwaltung.
Zugangsdaten gehören nicht in die Remote-URL. Falls GitHub den erzwungenen Push
durch eine Branch- oder Tag-Regel blockiert, die betreffende Regel für diese
einmalige Umstellung anpassen und anschließend wieder aktivieren.

Für ein anderes Repository kann die URL ausdrücklich angegeben werden:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\github-bereinigen.ps1 -RemoteUrl https://github.com/OWNER/enigma2-web.git
```

Der Push bereinigt die aktuellen Branches und Tags. Alte hochgeladene ZIP-Dateien
an GitHub-Releases müssen zusätzlich entfernt oder durch bereinigte Pakete ersetzt
werden. Das neue Installationspaket beim Release `v1.1.2` verwenden. Bereits
heruntergeladene Kopien und Forks werden durch einen Push nicht verändert.
GitHub kann außerdem alte Commit-Ansichten und Pull-Request-Referenzen behalten;
für die Entfernung solcher serverseitigen Reste gelten die Möglichkeiten und
Voraussetzungen in der [GitHub-Anleitung zur Datenentfernung](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
Ein Push allein garantiert keine endgültige Löschung aller gespeicherten Kopien.

Nach der Umstellung nur noch mit dem neuen Paket oder einem frisch geklonten
Repository weiterarbeiten. Die alte lokale Historie nicht wieder hineinmergen.

## Neues leeres Repository anlegen

Auf GitHub ein leeres Repository anlegen. README, `.gitignore` und Lizenzdatei
bei dessen Anlage nicht automatisch ergänzen: Die Projektdateien sind vorhanden.
Das Git-Paket vollständig entpacken und im enthaltenen Projektordner ausführen;
`OWNER` und gegebenenfalls den Repositorynamen ersetzen:

```powershell
git remote add origin https://github.com/OWNER/enigma2-web.git
git push -u origin main
git push origin v1.0.0 v1.1.0 v1.1.1 v1.1.2
```

Für ein leeres Repository ist das Bereinigungsskript nicht erforderlich.

## Release veröffentlichen

Unter **Releases** einen Release für den vorhandenen Tag `v1.1.2` und Titel
**Enigma2 Timer 1.1.2** erstellen. `RELEASE_NOTES.md` als Beschreibung verwenden
und `enigma2-web-v1.1.2.zip` als Installationspaket anhängen. Git-Tag und
Installationspaket enthalten denselben Quellstand.

## Prüfungen und weitere Versionen

Der Workflow `.github/workflows/ci.yml` prüft bei Push, Pull Request und manuellem
Start mit Python 3.12 Code, Format, Tests, Installer-Syntax und Python-Paketbau.
Die Ergebnisse erscheinen auf GitHub unter **Actions**.

Lokale Prüfung unter Ubuntu oder WSL mit Python 3.12 oder neuer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest
```

Spätere Versionen können die neue bereinigte Historie mit gewöhnlichen Commits
und Pushes fortsetzen. Versionsnummer in `pyproject.toml` und
`src/e2web/__init__.py`, Release-Datum und Dokumentation aktualisieren, prüfen
und committen. Bestehende bereinigte Release-Tags danach nicht verschieben.

Konfiguration, Datenbank, Schlüssel und Protokolle sind durch `.gitignore`
ausgeschlossen. Vor Commits die angezeigten Dateien prüfen. Herkunfts- und
Lizenzangaben stehen in [NOTICE.md](NOTICE.md).
