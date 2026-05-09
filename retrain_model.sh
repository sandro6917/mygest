#!/bin/bash

# Re-train modello ML con supporto ZIP
# Include tutti i documenti, anche quelli precedentemente skippati

set -e

echo "=================================="
echo "🔄 RE-TRAINING MODELLO ML"
echo "=================================="
echo ""
echo "Questo script ri-addestra il modello ML includendo:"
echo "  ✅ File PDF, DOCX, XLSX, Immagini"
echo "  ✅ File ZIP (NUOVO!)"
echo "  ✅ File TXT, CSV, LOG"
echo ""

# Attiva virtualenv
source venv/bin/activate

# Timestamp per log
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/retraining_${TIMESTAMP}.log"

mkdir -p logs

echo "📝 Log salvato in: $LOG_FILE"
echo ""

# Conferma
read -p "Vuoi procedere con il re-training? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "❌ Re-training annullato"
    exit 0
fi

echo ""
echo "🚀 Avvio re-training..."
echo ""

# Esegui re-training in background
nohup python initial_training.py \
    --yes \
    --min-docs-per-type 5 \
    > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > logs/retraining.pid

echo "✅ Re-training avviato!"
echo ""
echo "   PID: $PID"
echo "   Log: $LOG_FILE"
echo ""
echo "📊 Monitora progresso con:"
echo "   tail -f $LOG_FILE"
echo ""
echo "✅ Verifica processo:"
echo "   ps aux | grep $PID"
echo ""
