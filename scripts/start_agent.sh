#!/bin/bash
# Script avvio MyGest Agent con Auto-Detection

MYGEST_DIR="/home/sandro/mygest"
VENV_PATH="$MYGEST_DIR/venv"
AGENT_SCRIPT="$MYGEST_DIR/scripts/mygest_agent_autodetect.py"
CONFIG_FILE="$HOME/.mygest-agent.conf"

# Colori
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== MyGest Agent Auto-Detection ===${NC}"
echo

# Verifica venv
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}✗ Virtual environment non trovato: $VENV_PATH${NC}"
    exit 1
fi

# Verifica configurazione
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠ File configurazione non trovato: $CONFIG_FILE${NC}"
    echo -e "${YELLOW}  Copia il template: cp config/mygest-agent.conf.example ~/.mygest-agent.conf${NC}"
    exit 1
fi

# Attiva venv
source "$VENV_PATH/bin/activate"

# Verifica watchdog installato
if ! python -c "import watchdog" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Watchdog non installato. Installazione in corso...${NC}"
    pip install -q watchdog
    echo -e "${GREEN}✓ Watchdog installato${NC}"
fi

# Avvia agent
echo -e "${GREEN}✓ Avvio agent...${NC}"
echo
cd "$MYGEST_DIR"
python "$AGENT_SCRIPT"
