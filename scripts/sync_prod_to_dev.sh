#!/bin/bash
# =============================================================================
# Script di Sincronizzazione Database: PROD → DEV
# =============================================================================
# Sincronizza dati da database VPS (prod) a database locale (dev)
# Utile per testare con dati reali in ambiente di sviluppo
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURAZIONE
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXPORT_FILE="$PROJECT_ROOT/fixtures/sync/prod_export_$(date +%Y%m%d_%H%M%S).json"
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
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Opzioni:"
            echo "  --dry-run        Simula sincronizzazione senza applicare modifiche"
            echo "  --force          Non chiede conferma"
            echo "  --help           Mostra questo aiuto"
            echo ""
            echo "Esempi:"
            echo "  $0                # Sincronizza prod → dev"
            echo "  $0 --dry-run      # Anteprima modifiche"
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

log "===== SYNC PROD → DEV - START ====="
log "Prod: $VPS_HOST - Database VPS"
log "Dev:  $(hostname) - Database locale"

if [ "$DRY_RUN" = true ]; then
    warn "Modalità DRY-RUN: nessuna modifica sarà applicata"
fi

# Conferma
if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
    echo ""
    warn "ATTENZIONE: I dati locali (dev) saranno aggiornati con quelli di produzione"
    read -p "Vuoi procedere? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        log "Sincronizzazione annullata"
        exit 0
    fi
fi

# =============================================================================
# STEP 1: Export da PROD
# =============================================================================
section "Step 1/3: Export dati da PROD"

REMOTE_EXPORT_FILE="/tmp/prod_export_$(date +%Y%m%d_%H%M%S).json"

log "Export dati da VPS..."
ssh -i "$VPS_SSH_KEY" "$VPS_USER@$VPS_HOST" << ENDSSH
    set -e
    cd "$VPS_PROJECT_DIR"
    source /srv/mygest/venv/bin/activate
    
    python manage.py export_data --output="$REMOTE_EXPORT_FILE"
ENDSSH

log "✅ Export completato su VPS"

# =============================================================================
# STEP 2: Download file export
# =============================================================================
section "Step 2/3: Download dati da PROD"

log "Download VPS:$REMOTE_EXPORT_FILE → $EXPORT_FILE"
scp -i "$VPS_SSH_KEY" "$VPS_USER@$VPS_HOST:$REMOTE_EXPORT_FILE" "$EXPORT_FILE" || {
    error "Download fallito"
    exit 1
}

EXPORT_SIZE=$(du -h "$EXPORT_FILE" | cut -f1)
log "✅ Download completato: $EXPORT_FILE ($EXPORT_SIZE)"

# Cleanup su VPS
ssh -i "$VPS_SSH_KEY" "$VPS_USER@$VPS_HOST" "rm -f $REMOTE_EXPORT_FILE"

# =============================================================================
# STEP 3: Import in DEV
# =============================================================================
section "Step 3/3: Import dati in DEV"

cd "$PROJECT_ROOT"
source venv/bin/activate

IMPORT_ARGS="--input=$EXPORT_FILE"

if [ "$DRY_RUN" = true ]; then
    IMPORT_ARGS="$IMPORT_ARGS --dry-run"
fi

log "Esecuzione import in locale..."
python manage.py import_data $IMPORT_ARGS || {
    error "Import fallito"
    exit 1
}

log "✅ Import completato"

# =============================================================================
# CLEANUP
# =============================================================================
section "Cleanup"

log "Pulizia export vecchi..."
cd "$PROJECT_ROOT/fixtures/sync"
ls -t prod_export_*.json 2>/dev/null | tail -n +6 | xargs -r rm -f

log "✅ Cleanup completato"

# =============================================================================
# FINE
# =============================================================================
section "Riepilogo"

if [ "$DRY_RUN" = true ]; then
    log "✅ Anteprima completata (dry-run)"
    log "💡 Per applicare le modifiche, esegui senza --dry-run"
else
    log "✅ Sincronizzazione PROD → DEV completata con successo!"
    log "📊 Database DEV aggiornato con dati da PROD"
fi

log ""
log "===== SYNC PROD → DEV - END ====="
