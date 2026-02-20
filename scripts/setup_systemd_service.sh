#!/bin/bash
# Setup script per il servizio systemd di auto cleanup

set -e

echo "=== Setup MyGest Auto Cleanup Service ==="
echo ""

# Verifica permessi
if [ "$EUID" -ne 0 ]; then 
    echo "ERRORE: Questo script deve essere eseguito come root"
    echo "Usa: sudo bash setup_systemd_service.sh"
    exit 1
fi

# Copia il file service
echo "Copiando il file service..."
cp mygest-cleanup.service /etc/systemd/system/

# Ricarica systemd
echo "Ricaricando systemd..."
systemctl daemon-reload

# Abilita il servizio
echo "Abilitando il servizio..."
systemctl enable mygest-cleanup.service

# Avvia il servizio
echo "Avviando il servizio..."
systemctl start mygest-cleanup.service

# Mostra lo stato
echo ""
echo "=== Stato del servizio ==="
systemctl status mygest-cleanup.service

echo ""
echo "=== Setup completato! ==="
echo ""
echo "Comandi utili:"
echo "  - Vedere i log:        sudo journalctl -u mygest-cleanup -f"
echo "  - Fermare il servizio: sudo systemctl stop mygest-cleanup"
echo "  - Riavviare:          sudo systemctl restart mygest-cleanup"
echo "  - Disabilitare:       sudo systemctl disable mygest-cleanup"
echo ""
