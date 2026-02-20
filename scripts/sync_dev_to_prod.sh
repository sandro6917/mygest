#!/bin/bash
# =============================================================================
# Script di Sincronizzazione Database: DEV → PROD
# =============================================================================
# Sincronizza dati da database locale (dev) a database VPS (prod)
# Supporta merge intelligente (default) o full replace
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURAZIONE
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXPORT_FILE="$PROJECT_ROOT/fixtures/sync/dev_export_$(date +%Y%m%d_%H%M%S).json"
BACKUP_DIR="/srv/mygest/backups/sync"
VPS_HOST="72.62.34.249"
VPS_USER="mygest"
VPS_SSH_KEY="$HOME/.ssh/github_actions_mygest"
VPS_PROJECT_DIR="/srv/mygest/app"

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
# PARSE ARGUMENTS
# =============================================================================
DRY_RUN=false
FULL_REPLACE=false
FORCE=false
NO_BACKUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --full-replace)
            FULL_REPLACE=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Opzioni:"
            echo "  --dry-run        Simula sincronizzazione senza applicare modifiche"
            echo "  --full-replace   Elimina tutti i dati in prod prima di importare (PERICOLOSO)"
            echo "  --force          Non chiede conferma"
            echo "  --no-backup      Salta backup pre-sync"
            echo "  --help           Mostra questo aiuto"
            echo ""
            echo "Esempi:"
            echo "  $0                      # Merge intelligente (default)"
            echo "  $0 --dry-run            # Anteprima modifiche"
            echo "  $0 --full-replace       # Sovrascrittura completa"
            exit 0
            ;;
        *)
            error "Opzione sconosciuta: $1"
            echo "Usa --help per vedere le opzioni disponibili"
            exit 1
            ;;
    esac
done

# =============================================================================
# MAIN
# =============================================================================

log "===== SYNC DEV → PROD - START ====="
log "Dev:  $(hostname) - Database locale"
log "Prod: $VPS_HOST - Database VPS"

if [ "$DRY_RUN" = true ]; then
    warn "Modalità DRY-RUN: nessuna modifica sarà applicata"
fi

if [ "$FULL_REPLACE" = true ]; then
    warn "Modalità FULL-REPLACE: tutti i dati in prod saranno eliminati!"
fi

# Conferma se non --force
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
    echo ""
    read -p "Vuoi procedere con la sincronizzazione? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "Sincronizzazione annullata"
        exit 0
    fi
fi

# =============================================================================
# STEP 1: Export da DEV
# =============================================================================
section "Step 1/4: Export dati da DEV"

cd "$PROJECT_ROOT"

if [ ! -d "venv" ]; then
    error "Virtual environment non trovato in $PROJECT_ROOT/venv"
    exit 1
fi

source venv/bin/activate

log "Export dati locali..."
python manage.py export_data --output="$EXPORT_FILE" || {
    error "Export fallito"
    exit 1
}

EXPORT_SIZE=$(du -h "$EXPORT_FILE" | cut -f1)
log "✅ Export completato: $EXPORT_FILE ($EXPORT_SIZE)"

# =============================================================================
# STEP 2: Backup PROD (se richiesto)
# =============================================================================
if [ "$NO_BACKUP" = false ] && [ "$DRY_RUN" = false ]; then
    section "Step 2/4: Backup database PROD"
    
    log "Creazione backup su VPS..."
    ssh -i "$VPS_SSH_KEY" "$VPS_USER@$VPS_HOST" << 'ENDSSH'
        set -e
        BACKUP_DIR="/srv/mygest/backups/sync"
        mkdir -p "$BACKUP_DIR"
        
        BACKUP_FILE="$BACKUP_DIR/pre_sync_$(date +%Y%m%d_%H%M%S).sql"
        
        # Load DB credentials
        if [ -f "/srv/mygest/app/.env" ]; then
            export $(grep -E '^(DB_NAME|DB_USER|DB_PASSWORD|DB_HOST|DB_PORT)=' /srv/mygest/app/.env | xargs)
        fi
        
        PGPASSWORD="${DB_PASSWORD}" pg_dump \
            -h "${DB_HOST:-localhost}" \
            -p "${DB_PORT:-5432}" \
            -U "${DB_USER:-mygest_user}" \
            "${DB_NAME:-mygest}" \
            > "$BACKUP_FILE"
        
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "✅ Backup creato: $BACKUP_FILE ($BACKUP_SIZE)"
ENDSSH
    
    log "✅ Backup completato"
else
    log "⏩ Skip backup (--no-backup o --dry-run)"
fi

# =============================================================================
# STEP 3: Upload file export su PROD
# =============================================================================
section "Step 3/4: Upload dati su PROD"

REMOTE_EXPORT_FILE="/tmp/sync_import_$(date +%Y%m%d_%H%M%S).json"

log "Upload $EXPORT_FILE → VPS:$REMOTE_EXPORT_FILE"
scp -i "$VPS_SSH_KEY" "$EXPORT_FILE" "$VPS_USER@$VPS_HOST:$REMOTE_EXPORT_FILE" || {
    error "Upload fallito"
    exit 1
}

log "✅ Upload completato"

# =============================================================================
# STEP 4: Import su PROD
# =============================================================================
section "Step 4/4: Import dati su PROD"

IMPORT_ARGS="--input=$REMOTE_EXPORT_FILE"

if [ "$DRY_RUN" = true ]; then
    IMPORT_ARGS="$IMPORT_ARGS --dry-run"
fi

if [ "$FULL_REPLACE" = true ]; then
    IMPORT_ARGS="$IMPORT_ARGS --full-replace"
fi

log "Esecuzione import su VPS..."
ssh -i "$VPS_SSH_KEY" "$VPS_USER@$VPS_HOST" << ENDSSH
    set -e
    cd "$VPS_PROJECT_DIR"
    source /srv/mygest/venv/bin/activate
    
    python manage.py import_data $IMPORT_ARGS
    
    # Cleanup file temporaneo
    rm -f "$REMOTE_EXPORT_FILE"
ENDSSH

log "✅ Import completato"

# =============================================================================
# CLEANUP
# =============================================================================
section "Cleanup"

# Rimuovi export locale se vecchio (mantieni ultimi 5)
log "Pulizia export vecchi..."
cd "$PROJECT_ROOT/fixtures/sync"
ls -t dev_export_*.json 2>/dev/null | tail -n +6 | xargs -r rm -f

log "✅ Cleanup completato"

# =============================================================================
# FINE
# =============================================================================
section "Riepilogo"

if [ "$DRY_RUN" = true ]; then
    log "✅ Anteprima completata (dry-run)"
    log "💡 Per applicare le modifiche, esegui senza --dry-run"
else
    log "✅ Sincronizzazione DEV → PROD completata con successo!"
    log "📊 Database PROD aggiornato con dati da DEV"
fi

log ""
log "===== SYNC DEV → PROD - END ====="
