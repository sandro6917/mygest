#!/bin/bash
#
# Script per lanciare il training iniziale in background
# Usage: ./run_initial_training.sh [OPTIONS]
#

set -e

# Directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Attiva virtual environment
source venv/bin/activate

# Timestamp per log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/training_${TIMESTAMP}.log"

# Crea directory logs se non esiste
mkdir -p logs

echo "================================================================"
echo "🚀 AVVIO INITIAL TRAINING IN BACKGROUND"
echo "================================================================"
echo ""
echo "📝 Log file: $LOG_FILE"
echo ""
echo "ℹ️  Per monitorare il progresso:"
echo "   tail -f $LOG_FILE"
echo ""
echo "ℹ️  Per verificare il processo:"
echo "   ps aux | grep initial_training"
echo ""
echo "================================================================"
echo ""

# Lancia training in background con auto-conferma
nohup python initial_training.py --yes "$@" > "$LOG_FILE" 2>&1 &

# Salva PID
TRAINING_PID=$!
echo $TRAINING_PID > logs/training.pid

echo "✅ Training avviato con PID: $TRAINING_PID"
echo ""
echo "📊 Per vedere i progressi in tempo reale:"
echo "   tail -f $LOG_FILE"
echo ""

# Attendi 2 secondi e verifica che il processo sia ancora attivo
sleep 2

if ps -p $TRAINING_PID > /dev/null 2>&1; then
    echo "✅ Processo in esecuzione"
    echo ""
    echo "📈 Inizio log:"
    echo "----------------------------------------------------------------"
    head -20 "$LOG_FILE"
    echo "----------------------------------------------------------------"
    echo ""
    echo "🔍 Continua a monitorare con: tail -f $LOG_FILE"
else
    echo "❌ Processo terminato inaspettatamente. Controlla il log:"
    echo ""
    cat "$LOG_FILE"
    exit 1
fi
