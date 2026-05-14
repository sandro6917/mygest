#!/bin/bash
# Setup dei servizi systemd per Celery Worker e Beat
# Eseguire come root: sudo bash setup_celery_services.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$EUID" -ne 0 ]; then
    echo "ERRORE: Eseguire come root: sudo bash $0"
    exit 1
fi

echo "=== Setup servizi Celery per MyGest ==="

# Crea directory log se non esiste
mkdir -p /srv/mygest/logs
chown www-data:www-data /srv/mygest/logs

# Installa i file service
cp "$SCRIPT_DIR/celery-worker.service" /etc/systemd/system/
cp "$SCRIPT_DIR/celery-beat.service" /etc/systemd/system/

systemctl daemon-reload

systemctl enable celery-worker celery-beat
systemctl start celery-worker celery-beat

echo ""
echo "=== Stato servizi ==="
systemctl status celery-worker --no-pager || true
systemctl status celery-beat --no-pager || true

echo ""
echo "=== Setup completato! ==="
echo "Log worker: tail -f /srv/mygest/logs/celery-worker.log"
echo "Log beat:   tail -f /srv/mygest/logs/celery-beat.log"
