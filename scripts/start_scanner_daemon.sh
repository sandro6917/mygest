#!/bin/bash
# Script wrapper per avvio scanner service in background da PowerShell

cd /home/sandro/mygest
source venv/bin/activate 2>/dev/null

# Crea directory log se non esiste
mkdir -p logs

# Avvia scanner service in background con doppio fork per detach da terminale
(
    # Chiudi stdin, stdout, stderr
    exec 0</dev/null
    exec 1>logs/scanner_service.log
    exec 2>&1
    
    # Setsid per creare nuova sessione
    setsid python scripts/scanner_service.py &
    
    # Disown per staccare completamente
    disown
) &

# Attendi che il processo parta
sleep 2

# Restituisci PID
pgrep -f scanner_service.py || exit 1
