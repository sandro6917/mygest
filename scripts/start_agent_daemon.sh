#!/bin/bash
# Script wrapper per avvio agent in background da PowerShell

cd /home/sandro/mygest
source venv/bin/activate 2>/dev/null

# Avvia agent in background con doppio fork per detach da terminale
(
    # Chiudi stdin, stdout, stderr
    exec 0</dev/null
    exec 1>logs/agent_autodetect.log
    exec 2>&1
    
    # Setsid per creare nuova sessione
    setsid python scripts/mygest_agent_autodetect.py &
    
    # Disown per staccare completamente
    disown
) &

# Attendi che il processo parta
sleep 2

# Restituisci PID
pgrep -f mygest_agent_autodetect.py || exit 1
