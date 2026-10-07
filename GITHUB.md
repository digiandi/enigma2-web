# Version 1.1.13 auf GitHub bereitstellen

Das Git-Paket `enigma2-web-git-v1.1.13.zip` enthält den vollständigen Quellstand
als vorbereitetes Repository mit Branch `main` und annotiertem Tag `v1.1.13`.
Es setzt den bereinigten Stand 1.1.12 mit einem neuen Release-Commit fort.
Die vorhandenen Tags bis einschließlich `v1.1.12` bleiben auf
ihren bisherigen bereinigten Ständen. Für dieses Update genügt ein normaler Push.
Die Autorenkennung lautet `Enigma2 Timer Release <release@localhost>`.
Das Paket enthält noch kein Remote.

## Bestehendes bereinigtes Repository aktualisieren

Das Git-Paket vollständig in einen eigenen Ordner entpacken, einschließlich
`.git`. In PowerShell im enthaltenen Projektordner ausführen:

```powershell
git status --short --branch
git log -2 --oneline
git remote add origin https://github.com/digiandi/enigma2-web.git
git push -u origin main
git push origin v1.1.12 v1.1.13
git ls-remote origin refs/heads/main "refs/tags/v1.*"
```

Bei einem anderen GitHub-Konto oder Repository die URL entsprechend anpassen.
Falls `origin` bereits eingerichtet ist, dessen URL mit `git remote -v` prüfen.
Die normale GitHub-Anmeldung erfolgt über die eingerichtete Git-/Credential-Verwaltung;
Zugangsdaten gehören nicht in die Remote-URL.

Eigene zusätzliche Commits auf GitHub müssen vor dem Push berücksichtigt werden.
Ein normaler Push bricht ab, wenn der neue Stand die dortige Historie nicht fortsetzt.
Die vorhandenen Release-Tags werden nicht verschoben. Der Push enthält auch
`v1.1.12`, falls dieser Tag noch nicht hochgeladen wurde. Ist er bereits mit
derselben Kennung vorhanden, bleibt er unverändert.

## Einmalige Bereinigung aus Version 1.1.2

Die Entfernung privater Netzwerkbeispiele aus älteren Releases erfolgte mit
Version 1.1.2. Wer diese Umstellung bereits abgeschlossen hat, verwendet für
1.1.13 ausschließlich die normalen Update-Befehle oben.

Das weiterhin enthaltene `scripts/github-bereinigen.ps1` ist das Hilfsmittel für
die einmalige Umstellung auf 1.1.2. Es prüft genau diesen Release-Stand und
ist kein allgemeines Update-Skript für spätere Versionen. Bei einem noch
unbereinigten Repository zuerst das Git-Paket 1.1.2 samt damaliger Anleitung
verwenden und anschließend mit Version 1.1.13 fortsetzen.

Alte hochgeladene ZIP-Dateien an GitHub-Releases zusätzlich entfernen oder durch
bereinigte Pakete ersetzen. Heruntergeladene Kopien und Forks werden durch
Git-Pushes nicht verändert. Für eventuell verbliebene Commit-Ansichten und
Pull-Request-Referenzen gelten die Möglichkeiten und Voraussetzungen in der
[GitHub-Anleitung zur Datenentfernung](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
Nach der Umstellung mit der bereinigten Historie weiterarbeiten und keine alte
unbereinigte Historie hineinmergen.

## Neues leeres Repository anlegen

Auf GitHub ein leeres Repository anlegen. README, `.gitignore` und Lizenzdatei
bei dessen Anlage nicht automatisch ergänzen: Die Projektdateien sind vorhanden.
Das Git-Paket vollständig entpacken und im Projektordner ausführen;
`OWNER` und gegebenenfalls den Repositorynamen ersetzen:

```powershell
git remote add origin https://github.com/OWNER/enigma2-web.git
git push -u origin main
git push origin v1.0.0 v1.1.0 v1.1.1 v1.1.2 v1.1.3 v1.1.4 v1.1.5 v1.1.6 v1.1.7 v1.1.8 v1.1.9 v1.1.10 v1.1.11 v1.1.12 v1.1.13
```

Für ein leeres Repository ist das Bereinigungsskript nicht erforderlich.

## Release veröffentlichen

Unter **Releases** einen Release für Tag `v1.1.13` mit Titel **Enigma2 Timer 1.1.13**
erstellen. `RELEASE_NOTES.md` als Beschreibung verwenden und
`enigma2-web-v1.1.13.zip` als Installationspaket anhängen. Git-Tag und Installationspaket
enthalten denselben Quellstand.

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

Spätere Versionen setzen die bereinigte Historie mit gewöhnlichen Commits und
Pushes fort. Versionsnummer in `pyproject.toml` und `src/e2web/__init__.py`,
Release-Datum und Dokumentation aktualisieren, prüfen und committen.
Bestehende bereinigte Release-Tags danach nicht verschieben.

Konfiguration, Datenbank, Schlüssel und Protokolle sind durch `.gitignore`
ausgeschlossen. Vor Commits die angezeigten Dateien prüfen. Herkunfts- und
Lizenzangaben stehen in [NOTICE.md](NOTICE.md).
