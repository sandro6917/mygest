#!/bin/bash
# =============================================================================
# Script di Rollback Sincronizzazione
# =============================================================================
# Ripristina il backup più recente dopo una sincronizzazione fallita
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURAZIONE
# =============================================================================
VPS_HOST="72.62.34.249"
VPS_USER="mygest"
VPS_SSH_KEY="$HOME/.ssh/github_actions_mygest"
BACKUP_DIR="/srv/mygest/backups/sync"

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# FUNZIONI
# =============================================================================

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ $1${NC}" >&2
}

section() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# =============================================================================
# MAIN
# =============================================================================

log "===== ROLLBACK SYNC - START ====="

warn "ATTENZIONE: Stai per ripristinare il backup più recente su PROD"
read -p "Vuoi procedere con il rollback? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    log "Rollback annullato"
    exit 0
fi

section "Ricerca ultimo backup"

log "Connessione a VPS..."
LAST_BACKUP=$(ssh -i "$VPS_SSH_KEY" "$VPS_USER@$VPS_HOST" << 'ENDSSH'
    set -e
    BACKUP_DIR="/srv/mygest/backups/sync"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "ERROR: Directory backup non trovata"
        exit 1
    fi
    
    LAST_BACKUP=$(ls -t "$BACKUP_DIR"/pre_sync_*.sql 2>/dev/null | head -1)
    
    if [ -z "$LAST_BACKUP" ]; then
        echo "ERROR: Nessun backup trovato"
        exit 1
    fi
    
    echo "$LAST_BACKUP"
ENDSSH
)

if [[ "$LAST_BACKUP" == ERROR:* ]]; then
    error "${LAST_BACKUP#ERROR: }"
    exit 1
fi

BACKUP_SIZE=$(ssh -i "$VPS_SSH_KEY" "$VPS_USER@$VPS_HOST" "du -h '$LAST_BACKUP' | cut -f1")
log "✅ Backup trovato: $LAST_BACKUP ($BACKUP_SIZE)"

section "Conferma finale"

warn "Backup da ripristinare: $(basename $LAST_BACKUP)"
warn "Tutti i dati attuali in PROD saranno sostituiti con questo backup"
read -p "Confermi il ripristino? (yes/no): " final_confirm

if [ "$final_confirm" != "yes" ]; then
    log "Rollback annullato"
    exit 0
fi

section "Ripristino backup"

log "Ripristino in corso..."
ssh -i "$VPS_SSH_KEY" "$VPS_USER@$VPS_HOST" << ENDSSH
    set -e
    
    # Load DB credentials
    if [ -f "/srv/mygest/app/.env" ]; then
        export \$(grep -E '^(DB_NAME|DB_USER|DB_PASSWORD|DB_HOST|DB_PORT)=' /srv/mygest/app/.env | xargs)
    fi
    
    echo "🔄 Ripristino database..."
    PGPASSWORD="\${DB_PASSWORD}" psql \\
        -h "\${DB_HOST:-localhost}" \\
        -p "\${DB_PORT:-5432}" \\
        -U "\${DB_USER:-mygest_user}" \\
        "\${DB_NAME:-mygest}" \\
        < "$LAST_BACKUP"
    
    echo "✅ Database ripristinato"
ENDSSH

log "✅ Rollback completato con successo!"
log "📊 Database PROD ripristinato al backup: $(basename $LAST_BACKUP)"

log ""
log "===== ROLLBACK SYNC - END ====="
