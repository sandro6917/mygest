#!/bin/bash

# Script per controllare stato re-training

LOG_FILE="logs/retraining_20260225_170800.log"
PID=245254

clear
echo "======================================================================="
echo "🔍 STATO RE-TRAINING ML v1.1.0"
echo "======================================================================="
echo ""

# 1. Verifica processo
echo "1️⃣  PROCESSO:"
if ps aux | grep $PID | grep -v grep > /dev/null; then
    echo "   ✅ ATTIVO"
    ps aux | grep $PID | grep -v grep | awk '{printf "   CPU: %s%%  |  RAM: %s MB  |  Tempo: %s\n", $3, int($6/1024), $10}'
else
    echo "   ✅ COMPLETATO (processo terminato)"
fi
echo ""

# 2. Conta righe log
echo "2️⃣  LOG:"
LINE_COUNT=$(wc -l < $LOG_FILE)
echo "   Righe nel log: $LINE_COUNT"

if [ $LINE_COUNT -lt 10 ]; then
    echo "   Status: 🟡 Fase iniziale"
elif [ $LINE_COUNT -lt 40 ]; then
    echo "   Status: 🟠 In elaborazione..."
else
    echo "   Status: 🟢 Probabilmente completato!"
fi
echo ""

# 3. Cerca completamento
echo "3️⃣  RISULTATI:"
if grep -q "TRAINING COMPLETATO" $LOG_FILE 2>/dev/null; then
    echo "   ✅ TRAINING COMPLETATO CON SUCCESSO!"
    echo ""
    echo "   📊 Metriche:"
    grep -A 5 "RISULTATI:" $LOG_FILE | tail -6
    echo ""
    echo "   💾 Files:"
    grep "Modello:" $LOG_FILE | head -1
    echo ""
    echo "   🎯 PROSSIMO PASSO:"
    echo "      Attiva il modello con:"
    echo "      python manage.py shell -c \"from ai_classifier.models import MLModel; MLModel.objects.latest('trained_at').activate()\""
else
    echo "   ⏳ Training ancora in corso..."
    echo ""
    echo "   📝 Ultimi log:"
    tail -10 $LOG_FILE | sed 's/^/      /'
fi

echo ""
echo "======================================================================="
echo "🔄 Ri-esegui questo script per aggiornare lo stato"
echo "======================================================================="
