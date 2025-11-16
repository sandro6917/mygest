#!/bin/bash
set -euo pipefail

REPO_DIR="/srv/mygest/app"
VENV_DIR="/srv/mygest/venv"
LOG_FILE="/srv/mygest/logs/deploy.log"
SERVICE_NAME="gunicorn_mygest"

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Errore: $REPO_DIR non è un repository git" >&2
  exit 1
fi

mkdir -p "$(dirname "$LOG_FILE")"
exec >> "$LOG_FILE" 2>&1

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : Deploy avviato ====="

cd "$REPO_DIR"
echo "[1/6] Pull del repository"
git fetch --all
git reset --hard origin/main

echo "[2/6] Aggiornamento dipendenze"
source "$VENV_DIR/bin/activate"
set -a
[ -f .env ] && source .env
set +a
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/6] Migrazioni database"
python manage.py migrate --noinput

echo "[4/6] Collectstatic"
python manage.py collectstatic --noinput

echo "[5/6] Test smoke opzionali"
# python manage.py check --deploy

echo "[6/6] Restart servizio"
sudo systemctl restart "$SERVICE_NAME"

echo "===== $(date '+%Y-%m-%d %H:%M:%S') : Deploy completato ====="
