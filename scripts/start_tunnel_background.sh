#!/bin/bash
# Wrapper per avviare tunnel SSH in background persistente da PowerShell

# Kill eventuali tunnel esistenti
pkill -f "ssh.*-R.*10445" 2>/dev/null || true
sleep 2

# Avvia tunnel in background
nohup ssh -i ~/.ssh/github_actions_mygest \
    -R 10445:192.168.1.4:445 \
    -N -T \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    mygest@72.62.34.249 \
    > /tmp/ssh_tunnel.log 2>&1 &

# Salva PID
echo $! > /tmp/ssh_tunnel.pid

# Attendi un attimo per verificare che sia partito
sleep 3

# Verifica che il processo sia ancora in esecuzione
if pgrep -f "ssh.*10445" > /dev/null; then
    echo "✅ Tunnel avviato (PID: $(cat /tmp/ssh_tunnel.pid))"
    exit 0
else
    echo "❌ Tunnel fallito"
    cat /tmp/ssh_tunnel.log
    exit 1
fi
