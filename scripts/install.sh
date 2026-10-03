#!/usr/bin/env bash
set -euo pipefail
if [[ "${EUID}" -ne 0 ]]; then
  echo "Bitte mit sudo ausführen." >&2
  exit 1
fi
for program in python3 rsync systemctl; do
  command -v "$program" >/dev/null || { echo "$program fehlt." >&2; exit 1; }
done
python3 -c 'import sys; assert sys.version_info >= (3, 12), "Python 3.12+ erforderlich"'
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
id e2web-service >/dev/null 2>&1 || useradd --system --home-dir /var/lib/e2web \
  --shell /usr/sbin/nologin e2web-service
install -d -o root -g root -m 0755 /opt/e2web /opt/e2web/app
install -d -o root -g e2web-service -m 0750 /etc/e2web
install -d -o e2web-service -g e2web-service -m 0700 /var/lib/e2web
was_running=false
if systemctl is-active --quiet e2web; then
  was_running=true
  systemctl stop e2web
fi
if [[ "$project_dir" != /opt/e2web/app ]]; then
  rsync -a --delete --exclude=.venv --exclude=data --exclude=e2web.toml \
    --exclude=__pycache__ --exclude=.pytest_cache --exclude=.ruff_cache \
    --exclude=.git --exclude=dist "$project_dir/" /opt/e2web/app/
fi
python3 -m venv /opt/e2web/.venv
/opt/e2web/.venv/bin/pip install /opt/e2web/app
if [[ ! -f /etc/e2web/e2web.toml ]]; then
  install -o root -g e2web-service -m 0640 \
    /opt/e2web/app/deploy/e2web.example.toml /etc/e2web/e2web.toml
fi
runuser -u e2web-service -- /opt/e2web/.venv/bin/e2web \
  --config /etc/e2web/e2web.toml init
install -o root -g root -m 0644 /opt/e2web/app/deploy/e2web.service \
  /etc/systemd/system/e2web.service
systemctl daemon-reload
if [[ "$was_running" == true ]]; then
  systemctl start e2web
fi
echo "Installation abgeschlossen. Weitere Schritte stehen in README.md."
