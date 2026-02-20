#!/bin/bash
# Script per verificare lo status del sistema di pulizia automatica

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Status Sistema Pulizia File Temporanei                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 1. Script eseguibile
echo "📄 Script di pulizia:"
if [ -x "/home/sandro/mygest/scripts/cleanup_tmp.sh" ]; then
    echo "   ✓ Script presente e eseguibile"
    ls -lh /home/sandro/mygest/scripts/cleanup_tmp.sh
else
    echo "   ✗ Script non trovato o non eseguibile"
fi
echo ""

# 2. Cron job
echo "⏰ Cron job:"
if crontab -l 2>/dev/null | grep -q "cleanup_tmp.sh"; then
    echo "   ✓ Cron job configurato"
    crontab -l | grep cleanup_tmp.sh
else
    echo "   ✗ Nessun cron job trovato"
fi
echo ""

# 3. Servizio cron
echo "🔧 Servizio cron:"
if systemctl is-active --quiet cron 2>/dev/null; then
    echo "   ✓ Servizio cron attivo"
elif pgrep -x "cron" > /dev/null; then
    echo "   ✓ Processo cron in esecuzione"
else
    echo "   ⚠ Servizio cron non attivo (potrebbe essere normale in WSL)"
fi
echo ""

# 4. Directory tmp
echo "📁 Directory temporanea:"
if [ -d "/mnt/archivio/tmp" ]; then
    SIZE=$(du -sh /mnt/archivio/tmp 2>/dev/null | cut -f1)
    COUNT=$(find /mnt/archivio/tmp -type f 2>/dev/null | wc -l)
    echo "   ✓ /mnt/archivio/tmp"
    echo "     Dimensione: $SIZE"
    echo "     File: $COUNT"
else
    echo "   ⚠ Directory /mnt/archivio/tmp non trovata"
fi

if [ -d "/home/sandro/mygest/media/tmp" ]; then
    SIZE=$(du -sh /home/sandro/mygest/media/tmp 2>/dev/null | cut -f1)
    COUNT=$(find /home/sandro/mygest/media/tmp -type f 2>/dev/null | wc -l)
    echo "   ✓ media/tmp"
    echo "     Dimensione: $SIZE"
    echo "     File: $COUNT"
fi
echo ""

# 5. Log
echo "📋 Log esecuzioni:"
if [ -f "/home/sandro/mygest/logs/cleanup_tmp.log" ]; then
    echo "   ✓ Log presente"
    SIZE=$(ls -lh /home/sandro/mygest/logs/cleanup_tmp.log | awk '{print $5}')
    LINES=$(wc -l < /home/sandro/mygest/logs/cleanup_tmp.log)
    echo "     Dimensione: $SIZE"
    echo "     Righe: $LINES"
    echo ""
    echo "   Ultime 5 esecuzioni:"
    grep -A 3 "Cleanup tmp -" /home/sandro/mygest/logs/cleanup_tmp.log | tail -20 | sed 's/^/     /'
else
    echo "   ⚠ Nessun log trovato (nessuna esecuzione ancora)"
fi
echo ""

# 6. Comando Django
echo "🐍 Comando Django cleanup_tmp:"
if [ -f "/home/sandro/mygest/documenti/management/commands/cleanup_tmp.py" ]; then
    echo "   ✓ Comando presente"
    # Test dry-run rapido
    cd /home/sandro/mygest
    if [ -f "venv/bin/python" ]; then
        echo "   Testing..."
        OUTPUT=$(venv/bin/python manage.py cleanup_tmp --dry-run 2>&1 | head -5)
        if echo "$OUTPUT" | grep -q "Pulizia file temporanei"; then
            echo "   ✓ Comando funzionante"
        else
            echo "   ⚠ Errore test comando"
        fi
    fi
else
    echo "   ✗ Comando non trovato"
fi
echo ""

# 7. Riepilogo
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                         Riepilogo                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"

if [ -x "/home/sandro/mygest/scripts/cleanup_tmp.sh" ] && \
   crontab -l 2>/dev/null | grep -q "cleanup_tmp.sh" && \
   [ -f "/home/sandro/mygest/documenti/management/commands/cleanup_tmp.py" ]; then
    echo "✓ Sistema di pulizia automatica ATTIVO e CONFIGURATO"
    echo ""
    echo "Prossima esecuzione: Ogni giorno alle 2:00 AM"
    echo "Retention: 7 giorni"
    echo "Log: /home/sandro/mygest/logs/cleanup_tmp.log"
else
    echo "⚠ Sistema parzialmente configurato - verificare elementi sopra"
fi
echo ""
