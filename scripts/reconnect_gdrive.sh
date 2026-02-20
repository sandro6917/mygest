#!/bin/bash
# =============================================================================
# Script per riconnettere rclone a Google Drive
# =============================================================================
# Questo script guida attraverso il processo di riautenticazione OAuth2
# necessario quando il token di Google Drive è scaduto.
# =============================================================================

set -e

echo "======================================================"
echo "🔄 Riconnessione rclone a Google Drive"
echo "======================================================"
echo ""
echo "Il token OAuth2 è scaduto. Serve riautenticazione."
echo ""
echo "📋 PROCEDURA:"
echo ""
echo "1️⃣  Connettiti al VPS:"
echo "    ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249"
echo ""
echo "2️⃣  Esegui il wizard rclone:"
echo "    rclone config"
echo ""
echo "3️⃣  Seleziona:"
echo "    - Opzione: e) Edit existing remote"
echo "    - Remote: gdrive"
echo "    - No per modifiche (premi INVIO su tutto)"
echo "    - Advanced config: No"
echo "    - Auto config: Yes (se hai accesso a browser locale)"
echo ""
echo "4️⃣  Si aprirà il browser:"
echo "    - Accedi con account Google"
echo "    - Autorizza rclone"
echo "    - Torna al terminale"
echo ""
echo "5️⃣  Testa la connessione:"
echo "    rclone lsd gdrive:mygest-backups"
echo ""
echo "======================================================"
echo ""

read -p "Vuoi che apra la connessione SSH ora? (s/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "📡 Connessione al VPS..."
    ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249
else
    echo "❌ Operazione annullata."
    echo ""
    echo "💡 TIP: Puoi eseguire manualmente:"
    echo "   ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249"
    echo "   rclone config"
fi
