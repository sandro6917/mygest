#!/bin/bash
#
# Tunnel SSH Inverso: Inoltra porta SMB del NAS (192.168.1.4:445) alla VPS
# Questo script crea un tunnel permanente che permette alla VPS di accedere al NAS locale
#

set -e

# Configurazione
VPS_HOST="72.62.34.249"
VPS_USER="mygest"
VPS_KEY="$HOME/.ssh/github_actions_mygest"
NAS_IP="192.168.1.4"
NAS_SMB_PORT="445"
TUNNEL_PORT="10445"  # Porta sulla VPS dove verrà inoltrato SMB

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  SSH Tunnel: NAS → VPS                                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "NAS Local: $NAS_IP:$NAS_SMB_PORT"
echo "VPS Remote: $VPS_HOST (porta $TUNNEL_PORT)"
echo ""

# Verifica chiave SSH
if [ ! -f "$VPS_KEY" ]; then
    echo -e "${RED}❌ Chiave SSH non trovata: $VPS_KEY${NC}"
    exit 1
fi

# Funzione per controllare se il tunnel è già attivo
check_tunnel() {
    ssh -i "$VPS_KEY" ${VPS_USER}@${VPS_HOST} \
        "netstat -tuln | grep -q :$TUNNEL_PORT" 2>/dev/null
    return $?
}

# Pulisci eventuali tunnel esistenti
echo "🔍 Verifico tunnel esistenti..."
if check_tunnel; then
    echo -e "${YELLOW}⚠️  Tunnel già attivo, lo termino per ricrearlo...${NC}"
    ssh -i "$VPS_KEY" ${VPS_USER}@${VPS_HOST} \
        "pkill -f 'ssh.*-R.*$TUNNEL_PORT' || true" 2>/dev/null || true
    sleep 2
fi

# Crea il tunnel SSH inverso
# -R: Reverse tunnel (porta VPS → porta locale)
# -N: Non eseguire comandi remoti
# -T: Disabilita pseudo-terminal
# -o ServerAliveInterval=60: Mantieni connessione attiva
# -o ServerAliveCountMax=3: Riconnetti dopo 3 tentativi falliti
# -o ExitOnForwardFailure=yes: Esci se il tunnel fallisce

echo -e "${GREEN}🚀 Avvio tunnel SSH inverso...${NC}"
echo "   Questo processo rimarrà in esecuzione (usa Ctrl+C per interrompere)"
echo ""

ssh -v -i "$VPS_KEY" \
    -R ${TUNNEL_PORT}:${NAS_IP}:${NAS_SMB_PORT} \
    -N -T \
    -o ServerAliveInterval=60 \
    -o ServerAliveCountMax=3 \
    -o ExitOnForwardFailure=yes \
    ${VPS_USER}@${VPS_HOST} 2>&1 | tee /tmp/ssh_tunnel_debug.log

# Se arriviamo qui, il tunnel è stato interrotto
echo -e "${RED}❌ Tunnel SSH terminato${NC}"
exit 1
