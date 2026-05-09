#!/bin/bash
#
# Cron Job Script per Re-training Automatico ML
#
# Installazione:
#   1. Rendi eseguibile: chmod +x /srv/mygest/app/scripts/cron_retrain_ml.sh
#   2. Aggiungi a crontab: crontab -e
#      0 2 * * * /srv/mygest/app/scripts/cron_retrain_ml.sh >> /srv/mygest/logs/cron_retrain.log 2>&1
#
# Schedule: Ogni notte alle 02:00
#

# Configurazione
PROJECT_DIR="/srv/mygest/app"
VENV_DIR="$PROJECT_DIR/venv"
LOG_FILE="/srv/mygest/logs/cron_retrain.log"

# Se in sviluppo locale
if [ ! -d "$PROJECT_DIR" ]; then
    PROJECT_DIR="/home/sandro/mygest"
    VENV_DIR="$PROJECT_DIR/venv"
    LOG_FILE="$PROJECT_DIR/logs/cron_retrain.log"
fi

# Crea directory logs se non esiste
mkdir -p "$(dirname "$LOG_FILE")"

# Timestamp
echo "======================================" | tee -a "$LOG_FILE"
echo "🕐 $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"

# Vai nella directory del progetto
cd "$PROJECT_DIR" || exit 1

# Attiva virtualenv
source "$VENV_DIR/bin/activate" || exit 1

# Esegui re-training
echo "🤖 Avvio re-training automatico..." | tee -a "$LOG_FILE"

python manage.py retrain_ml_model \
    --min-samples 20 \
    --auto-activate \
    --improvement-threshold 0.02 \
    2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Re-training completato con successo" | tee -a "$LOG_FILE"
else
    echo "❌ Re-training fallito con exit code: $EXIT_CODE" | tee -a "$LOG_FILE"
fi

echo "" | tee -a "$LOG_FILE"

exit $EXIT_CODE
