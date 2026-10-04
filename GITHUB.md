# Version 1.1.1 auf GitHub bereitstellen

Das Git-Paket `enigma2-web-git-v1.1.1.zip` enthält den vollständigen Quellstand
als vorbereitetes Git-Repository. Branch: `main`, annotierter Tag: `v1.1.1`.
Das Repository führt die Git-Historie von 1.1.0 fort: `v1.0.0` und `v1.1.0`
bleiben auf ihren ursprünglichen Commits; darüber liegt der Release-Commit
für `v1.1.1`. Die
lokale Autorenkennung lautet `Enigma2 Timer Release <release@localhost>`.
Das Paket enthält noch kein Remote.

## Neues Repository anlegen

Auf GitHub ein neues leeres Repository anlegen, beispielsweise `enigma2-web`.
Öffentlich oder privat nach gewünschter Sichtbarkeit wählen. Bei dessen Anlage
README, `.gitignore` und Lizenzdatei nicht automatisch ergänzen: Die vorhandenen
Projektdateien bilden bereits den Release-Stand.

Das Git-Paket vollständig entpacken, einschließlich des Verzeichnisses `.git`.
In PowerShell in den entpackten Ordner wechseln. `OWNER` und gegebenenfalls den
Repositorynamen in der folgenden URL durch die tatsächlichen Angaben ersetzen:

```powershell
cd .\enigma2-web-git-v1.1.1
git status --short --branch
git log -1 --oneline
git tag --list
git remote add origin https://github.com/OWNER/enigma2-web.git
git push -u origin main
git push origin v1.0.0 v1.1.0 v1.1.1
```

Falls `origin` bereits eingerichtet wurde, dessen URL mit `git remote -v` prüfen.
Die normale GitHub-Anmeldung erfolgt über die auf dem Rechner eingerichtete
Git-/Credential-Verwaltung; Zugangsdaten gehören nicht in die Remote-URL.

## Bereits vorhandenes Repository

Ist Version 1.0.0 oder 1.1.0 bereits mit diesem vorbereiteten Repository hochgeladen,
führt das neue Paket dessen Historie unverändert fort. Das Paket in einen neuen
Ordner entpacken, die tatsächliche `origin`-URL eintragen und vor dem Push prüfen:

```powershell
git fetch origin
git log --oneline --graph --decorate --all -8
git push -u origin main
git push origin v1.1.0 v1.1.1
```

Eigene zusätzliche Commits auf GitHub müssen vor dem Push zusammengeführt werden.
Kein erzwungener Push ist nötig. Die vorhandenen Tags `v1.0.0` und `v1.1.0`
werden nicht verschoben.

## Release veröffentlichen

Unter **Releases** einen Release für den vorhandenen Tag `v1.1.1` und Titel
**Enigma2 Timer 1.1.1** erstellen. Den Inhalt von `RELEASE_NOTES.md` als Beschreibung
verwenden und `enigma2-web-v1.1.1.zip` als Installationspaket anhängen. Der Git-Tag
bezeichnet denselben Quellstand wie das Installationspaket.

## Prüfungen

Der Workflow `.github/workflows/ci.yml` führt bei Push, Pull Request und manuellem
Start mit Python 3.12 Codeprüfung, Formatprüfung, Tests, Installer-Syntaxprüfung
und Python-Paketbau aus. Ergebnisse erscheinen auf GitHub unter **Actions**.

Lokale Entwicklung und Prüfung unter Ubuntu oder WSL mit Python 3.12 oder neuer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
pytest
```

Die systemd-Installation und deren Bash-Skript sind für Linux vorgesehen.
Die oben beschriebenen Git-Befehle können auch in PowerShell verwendet werden.

## Weitere Versionen

Vor einem späteren Tag Versionsnummer in `pyproject.toml` und
`src/e2web/__init__.py`, Release-Datum sowie Dokumentation aktualisieren.
Änderungen prüfen und als eigenen Commit aufnehmen. Der Tag `v1.1.1` bleibt
unverändert auf dem ursprünglichen Release-Commit.

Konfiguration, Datenbank, Schlüssel und lokale Protokolle werden durch `.gitignore`
ausgeschlossen. Vor jedem Commit die mit `git status` angezeigten Dateien prüfen.
Lizenz- und Herkunftsangaben stehen in [NOTICE.md](NOTICE.md).
