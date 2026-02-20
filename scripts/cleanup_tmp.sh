#!/bin/bash
# Script per pulizia automatica file temporanei upload
# Usato da cron job

# Directory progetto
PROJECT_DIR="/home/sandro/mygest"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
MANAGE_PY="$PROJECT_DIR/manage.py"
LOG_FILE="$PROJECT_DIR/logs/cleanup_tmp.log"

# Giorni di retention (default: 7)
DAYS="${1:-7}"

# Crea directory log se non esiste
mkdir -p "$(dirname "$LOG_FILE")"

# Timestamp
echo "========================================" >> "$LOG_FILE"
echo "Cleanup tmp - $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Esegui comando
cd "$PROJECT_DIR" || exit 1

"$VENV_PYTHON" "$MANAGE_PY" cleanup_tmp --days="$DAYS" >> "$LOG_FILE" 2>&1

# Status
if [ $? -eq 0 ]; then
    echo "✓ Completato con successo" >> "$LOG_FILE"
else
    echo "✗ Errore durante esecuzione" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
