#!/bin/bash
# Script di setup per Google Calendar in MyGest
# Uso: ./setup_google_calendar.sh

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Setup Google Calendar - MyGest${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Verifica virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment non attivo${NC}"
    echo -e "Attivo il virtual environment..."
    source venv/bin/activate || {
        echo -e "${RED}✗ Errore: impossibile attivare venv${NC}"
        exit 1
    }
fi

# 1. Verifica file credenziali
echo -e "${BLUE}[1/7] Verifica file credenziali...${NC}"
CREDS_FILE="/home/sandro/mygest/secrets/google-calendar.json"

if [ ! -f "$CREDS_FILE" ]; then
    echo -e "${RED}✗ File credenziali non trovato: $CREDS_FILE${NC}"
    echo ""
    echo "Passaggi per ottenere il file:"
    echo "1. Vai su https://console.cloud.google.com/"
    echo "2. Seleziona progetto 'mygest-478007'"
    echo "3. APIs & Services > Credentials"
    echo "4. Create Credentials > Service Account"
    echo "5. Crea e scarica la chiave JSON"
    echo "6. Copia il file in: $CREDS_FILE"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ File credenziali trovato${NC}"

# Verifica che sia un Service Account
if grep -q '"type": "service_account"' "$CREDS_FILE"; then
    echo -e "${GREEN}✓ Tipo corretto: Service Account${NC}"
    SERVICE_EMAIL=$(python3 -c "import json; print(json.load(open('$CREDS_FILE'))['client_email'])" 2>/dev/null || echo "N/A")
    echo -e "  Email: ${YELLOW}$SERVICE_EMAIL${NC}"
else
    echo -e "${RED}✗ ERRORE: Il file non è un Service Account${NC}"
    echo -e "${YELLOW}  Tipo attuale: $(grep '"type"' "$CREDS_FILE" || echo 'Non riconosciuto')${NC}"
    echo ""
    echo "Il file deve essere un Service Account JSON, non OAuth2 Client ID"
    echo "Ricrea il Service Account seguendo: docs/GOOGLE_CALENDAR_SETUP.md"
    exit 1
fi

# 2. Verifica librerie Google
echo ""
echo -e "${BLUE}[2/7] Verifica librerie Google...${NC}"

if python3 -c "import google.auth" 2>/dev/null; then
    echo -e "${GREEN}✓ google-auth installato${NC}"
else
    echo -e "${YELLOW}⚠️  google-auth mancante, installo...${NC}"
    pip install -q google-auth
fi

if python3 -c "import googleapiclient" 2>/dev/null; then
    echo -e "${GREEN}✓ google-api-python-client installato${NC}"
else
    echo -e "${YELLOW}⚠️  google-api-python-client mancante, installo...${NC}"
    pip install -q google-api-python-client
fi

if python3 -c "import google_auth_httplib2" 2>/dev/null; then
    echo -e "${GREEN}✓ google-auth-httplib2 installato${NC}"
else
    echo -e "${YELLOW}⚠️  google-auth-httplib2 mancante, installo...${NC}"
    pip install -q google-auth-httplib2
fi

# 3. Verifica configurazione Django
echo ""
echo -e "${BLUE}[3/7] Verifica configurazione Django...${NC}"
python3 check_google_calendar_config.py
CONFIG_CHECK=$?

if [ $CONFIG_CHECK -ne 0 ]; then
    echo -e "${RED}✗ Configurazione non valida${NC}"
    echo "Controlla l'output sopra per i dettagli"
    exit 1
fi

# 4. Verifica Google Calendar API abilitata
echo ""
echo -e "${BLUE}[4/7] Verifica Google Calendar API...${NC}"
echo -e "${YELLOW}⚠️  Verifica manuale richiesta:${NC}"
echo "1. Vai su https://console.cloud.google.com/apis/library"
echo "2. Cerca 'Google Calendar API'"
echo "3. Assicurati che sia ENABLED per il progetto mygest-478007"
echo ""
read -p "È abilitata? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}✗ Google Calendar API non abilitata${NC}"
    echo "Abilitala prima di continuare"
    exit 1
fi
echo -e "${GREEN}✓ Google Calendar API abilitata${NC}"

# 5. Verifica calendario condiviso
echo ""
echo -e "${BLUE}[5/7] Verifica condivisione calendario...${NC}"
echo -e "${YELLOW}⚠️  Verifica manuale richiesta:${NC}"
echo "1. Apri https://calendar.google.com/"
echo "2. Settings > Share with specific people"
echo "3. Aggiungi: ${YELLOW}$SERVICE_EMAIL${NC}"
echo "4. Permessi: 'Make changes to events'"
echo ""
read -p "Calendario condiviso? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}✗ Calendario non condiviso${NC}"
    echo "Condividilo prima di continuare"
    exit 1
fi
echo -e "${GREEN}✓ Calendario condiviso${NC}"

# 6. Abilita signal (opzionale)
echo ""
echo -e "${BLUE}[6/7] Abilita sincronizzazione automatica...${NC}"
echo -e "${YELLOW}Vuoi abilitare la sincronizzazione automatica?${NC}"
echo "Se abiliti, ogni modifica a ScadenzaOccorrenza verrà sincronizzata con Google Calendar"
echo ""
read -p "Abilitare signal automatici? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Decommenta i signal in models.py
    MODELS_FILE="scadenze/models.py"
    
    if grep -q "# post_save.connect(_sync_calendar_after_save" "$MODELS_FILE"; then
        echo "Abilito signal in $MODELS_FILE..."
        
        # Crea backup
        cp "$MODELS_FILE" "$MODELS_FILE.backup"
        
        # Decommenta le righe
        sed -i 's/# post_save\.connect(_sync_calendar_after_save/post_save.connect(_sync_calendar_after_save/g' "$MODELS_FILE"
        sed -i 's/# post_delete\.connect(_delete_calendar_event/post_delete.connect(_delete_calendar_event/g' "$MODELS_FILE"
        
        echo -e "${GREEN}✓ Signal abilitati${NC}"
        echo -e "${YELLOW}⚠️  Riavvia il server Django per applicare le modifiche${NC}"
    else
        echo -e "${GREEN}✓ Signal già abilitati${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Signal NON abilitati (sincronizzazione manuale)${NC}"
    echo "Potrai sincronizzare manualmente con:"
    echo "  python manage.py sync_google_calendar"
fi

# 7. Test di connessione
echo ""
echo -e "${BLUE}[7/7] Test connessione Google Calendar...${NC}"
read -p "Vuoi testare la connessione? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Eseguo dry-run di sincronizzazione..."
    python3 manage.py sync_google_calendar --dry-run || {
        echo -e "${RED}✗ Test fallito${NC}"
        echo "Controlla i log sopra per i dettagli"
        exit 1
    }
    echo -e "${GREEN}✓ Test connessione riuscito${NC}"
fi

# Riepilogo finale
echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}✅ Setup completato con successo!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "Prossimi passi:"
echo ""
echo "1. Riavvia il server Django:"
echo -e "   ${YELLOW}python manage.py runserver${NC}"
echo ""
echo "2. Sincronizza le occorrenze esistenti:"
echo -e "   ${YELLOW}python manage.py sync_google_calendar --all${NC}"
echo ""
echo "3. Verifica gli eventi su Google Calendar:"
echo -e "   ${YELLOW}https://calendar.google.com/${NC}"
echo ""
echo "Documentazione completa: docs/GOOGLE_CALENDAR_SETUP.md"
echo ""
