#!/bin/bash
# Script per sincronizzare il database locale con la VPS
# ATTENZIONE: Questo script SOVRASCRIVE completamente il database sulla VPS!

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${YELLOW}║  SYNC DATABASE LOCALE → VPS                            ║${NC}"
echo -e "${YELLOW}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Configurazione VPS
VPS_USER="mygest"
VPS_HOST="72.62.34.249"
VPS_KEY="$HOME/.ssh/github_actions_mygest"
VPS_APP_DIR="/srv/mygest/app"
VPS_DB_NAME="mygest"
VPS_DB_USER="mygest_user"

# Configurazione locale
LOCAL_APP_DIR="/home/sandro/mygest"
BACKUP_DIR="$LOCAL_APP_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP_FILE="db_dump_${TIMESTAMP}.sql"

# Crea directory backup se non esiste
mkdir -p "$BACKUP_DIR"

echo -e "${YELLOW}⚠️  ATTENZIONE ⚠️${NC}"
echo -e "Questo script sostituirà completamente il database sulla VPS con i dati locali."
echo -e "Database VPS: ${RED}${VPS_DB_NAME}${NC}"
echo -e "Host VPS: ${RED}${VPS_HOST}${NC}"
echo ""
read -p "Sei sicuro di voler continuare? (scrivi 'SI' per confermare): " confirm

if [ "$confirm" != "SI" ]; then
    echo -e "${RED}Operazione annullata dall'utente.${NC}"
    exit 0
fi

echo ""
echo ""
echo -e "${GREEN}=== STEP 1: Backup database VPS ===${NC}"
ssh -i "$VPS_KEY" ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
    BACKUP_FILE="/tmp/mygest_backup_before_sync_$(date +%Y%m%d_%H%M%S).sql"
    echo "Creazione backup VPS in: $BACKUP_FILE"
    cd /srv/mygest/app
    PGPASSWORD="$(grep '^DB_PASSWORD=' .env | cut -d= -f2 | tr -d '"' | tr -d "'")" \
    pg_dump -h localhost -p 5432 -U mygest_user \
        --clean --if-exists --no-owner --no-acl \
        mygest > "$BACKUP_FILE"
    echo "✅ Backup VPS creato: $BACKUP_FILE"
ENDSSH

echo ""
echo -e "${GREEN}=== STEP 2: Export database locale ===${NC}"
cd "$LOCAL_APP_DIR"

# Credenziali database locale (da settings.py)
DB_NAME="mygest"
DB_USER="mygest_user"
DB_PASSWORD="ScegliUnaPasswordSicura"
DB_HOST="127.0.0.1"
DB_PORT="5432"

echo "Dump database locale: $DB_NAME"
PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" \
    --clean --if-exists --no-owner --no-acl \
    --exclude-table-data='django_session' \
    --exclude-table-data='django_admin_log' \
    "$DB_NAME" > "$BACKUP_DIR/$DUMP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Export locale completato: $BACKUP_DIR/$DUMP_FILE${NC}"
    echo "Dimensione file: $(du -h "$BACKUP_DIR/$DUMP_FILE" | cut -f1)"
else
    echo -e "${RED}❌ Errore durante l'export locale${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== STEP 3: Upload dati sulla VPS ===${NC}"
echo "Upload del dump sulla VPS..."
scp -i "$VPS_KEY" "$BACKUP_DIR/$DUMP_FILE" ${VPS_USER}@${VPS_HOST}:/tmp/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Upload completato${NC}"
else
    echo -e "${RED}❌ Errore durante l'upload${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=== STEP 4: Restore database sulla VPS ===${NC}"
ssh -i "$VPS_KEY" ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
    cd /srv/mygest/app
    
    echo "Restore database da /tmp/db_dump_20260220_100100.sql..."
    PGPASSWORD="$(grep '^DB_PASSWORD=' .env | cut -d= -f2 | tr -d '"' | tr -d "'")" \
    psql -h localhost -p 5432 -U mygest_user -d mygest < /tmp/db_dump_20260220_100100.sql
    
    if [ $? -eq 0 ]; then
        echo "✅ Restore completato con successo"
        
        # Pulizia file temporaneo
        rm -f /tmp/db_dump_20260220_100100.sql
        echo "🗑️  File temporaneo rimosso"
    else
        echo "❌ Errore durante il restore"
        echo "⚠️  Il file dump è disponibile in /tmp/db_dump_20260220_100100.sql"
        exit 1
    fi
ENDSSH

echo ""
echo -e "${GREEN}=== STEP 5: Restart Gunicorn ===${NC}"
ssh -i "$VPS_KEY" ${VPS_USER}@${VPS_HOST} << 'ENDSSH'
    sudo systemctl restart gunicorn_mygest
    sleep 3
    
    if systemctl is-active --quiet gunicorn_mygest; then
        echo "✅ Gunicorn riavviato con successo"
    else
        echo "❌ Errore nel riavvio di Gunicorn"
        exit 1
    fi
ENDSSH

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ SINCRONIZZAZIONE COMPLETATA                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "📊 Statistiche:"
echo -e "   - Dump locale: $BACKUP_DIR/$DUMP_FILE"
echo -e "   - Database VPS: ${GREEN}Aggiornato${NC}"
echo -e "   - Backup VPS: ${GREEN}Disponibile su VPS in /tmp/${NC}"
echo ""
echo -e "🌐 Applicazione disponibile su: ${GREEN}https://mygest.sandrochimenti.it${NC}"
echo ""
