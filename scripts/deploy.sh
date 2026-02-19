#!/bin/bash
# =============================================================================
# MyGest Deploy Script - Production Deployment with Rollback
# =============================================================================
# Usage: ./scripts/deploy.sh [--skip-backup] [--force]
# 
# Features:
# - Automatic backup (database + code)
# - Health checks before/after deploy
# - Automatic rollback on failure
# - Zero-downtime reload (graceful)
# - Detailed logging with colors
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION
# =============================================================================
REPO_DIR="/srv/mygest/app"
VENV_DIR="/srv/mygest/venv"
BACKUP_DIR="/srv/mygest/backups"
LOG_DIR="/srv/mygest/logs"
LOG_FILE="$LOG_DIR/deploy.log"
SERVICE_NAME="gunicorn_mygest"
HEALTH_URL="http://localhost:8000/api/v1/health/"
HEALTH_TIMEOUT=10
MAX_RETRIES=3

# Parse arguments
SKIP_BACKUP=false
FORCE_DEPLOY=false
for arg in "$@"; do
    case $arg in
        --skip-backup) SKIP_BACKUP=true ;;
        --force) FORCE_DEPLOY=true ;;
        --help)
            echo "Usage: $0 [--skip-backup] [--force]"
            echo "  --skip-backup  Skip database backup"
            echo "  --force        Deploy even if health check fails"
            exit 0
            ;;
    esac
done

# =============================================================================
# COLORS & LOGGING
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[${timestamp}]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[${timestamp}] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[${timestamp}] ❌ $1${NC}" | tee -a "$LOG_FILE" >&2
}

success() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[${timestamp}] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

section() {
    echo -e "\n${BLUE}=== $1 ===${NC}" | tee -a "$LOG_FILE"
}

# =============================================================================
# VALIDATION
# =============================================================================
if [ ! -d "$REPO_DIR/.git" ]; then
    error "Directory $REPO_DIR non è un repository git"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    error "Virtual environment $VENV_DIR non trovato"
    exit 1
fi

# Create required directories
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

# =============================================================================
# FUNCTIONS
# =============================================================================

# Backup database
backup_database() {
    if [ "$SKIP_BACKUP" = true ]; then
        warn "Backup database saltato (--skip-backup)"
        return 0
    fi
    
    local backup_file="$BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql"
    log "Backup database in corso..."
    
    if pg_dump mygest > "$backup_file" 2>/dev/null; then
        success "Backup database: $backup_file ($(du -h "$backup_file" | cut -f1))"
        echo "$backup_file"
    else
        error "Backup database fallito"
        return 1
    fi
}

# Health check
health_check() {
    local retries=0
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -sf --max-time "$HEALTH_TIMEOUT" "$HEALTH_URL" > /dev/null 2>&1; then
            return 0
        fi
        retries=$((retries + 1))
        [ $retries -lt $MAX_RETRIES ] && sleep 2
    done
    return 1
}

# Rollback
rollback() {
    local commit=$1
    error "Deploy fallito! Rollback in corso..."
    
    cd "$REPO_DIR"
    git reset --hard "$commit"
    
    source "$VENV_DIR/bin/activate"
    pip install -q -r requirements.txt
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput --clear
    
    sudo systemctl reload "$SERVICE_NAME" || sudo systemctl restart "$SERVICE_NAME"
    
    if health_check; then
        success "Rollback completato con successo"
    else
        error "Rollback fallito! Intervento manuale richiesto"
        exit 2
    fi
    exit 1
}

# =============================================================================
# MAIN DEPLOYMENT FLOW
# =============================================================================

log "===== DEPLOY MYGEST - START ====="
log "Repository: $REPO_DIR"
log "Service: $SERVICE_NAME"

# 1. PRE-DEPLOY CHECKS
section "Step 1/9: Pre-Deploy Checks"

cd "$REPO_DIR"
CURRENT_COMMIT=$(git rev-parse HEAD)
log "Current commit: $CURRENT_COMMIT"

# Check if service is running
if ! systemctl is-active --quiet "$SERVICE_NAME"; then
    warn "Service $SERVICE_NAME non attivo"
fi

# Initial health check
if health_check; then
    success "Health check iniziale: OK"
else
    warn "Health check iniziale fallito (servizio potrebbe essere spento)"
    if [ "$FORCE_DEPLOY" = false ]; then
        error "Usa --force per procedere comunque"
        exit 1
    fi
fi

# 2. BACKUP
section "Step 2/9: Backup Database"
BACKUP_FILE=$(backup_database)

# 3. GIT PULL
section "Step 3/9: Update Code"
git fetch --all
NEW_COMMIT=$(git rev-parse origin/main)

if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    warn "Nessun aggiornamento disponibile (già a $NEW_COMMIT)"
    exit 0
fi

log "Update: $CURRENT_COMMIT -> $NEW_COMMIT"
git reset --hard origin/main
success "Code updated"

# 4. FRONTEND BUILD
section "Step 4/9: Build Frontend"
if [ -d "$REPO_DIR/frontend" ]; then
    cd "$REPO_DIR/frontend"
    if npm run build >> "$LOG_FILE" 2>&1; then
        success "Frontend build completato"
    else
        error "Frontend build fallito"
        rollback "$CURRENT_COMMIT"
    fi
else
    warn "Directory frontend non trovata, skip"
fi

# 5. BACKEND DEPENDENCIES
section "Step 5/9: Update Python Dependencies"
cd "$REPO_DIR"
source "$VENV_DIR/bin/activate"

# Load environment variables
set -a
[ -f .env ] && source .env
set +a

pip install -q --upgrade pip
if pip install -q -r requirements.txt; then
    success "Dependencies aggiornate"
else
    error "Installazione dipendenze fallita"
    rollback "$CURRENT_COMMIT"
fi

# 6. DATABASE MIGRATIONS
section "Step 6/9: Database Migrations"
if python manage.py migrate --noinput >> "$LOG_FILE" 2>&1; then
    success "Migrations applicate"
else
    error "Migrations fallite"
    rollback "$CURRENT_COMMIT"
fi

# 7. COLLECT STATIC
section "Step 7/9: Collect Static Files"
if python manage.py collectstatic --noinput --clear >> "$LOG_FILE" 2>&1; then
    success "Static files raccolti"
else
    error "Collectstatic fallito"
    rollback "$CURRENT_COMMIT"
fi

# 8. DJANGO CHECKS
section "Step 8/9: Django System Check"
if python manage.py check --deploy >> "$LOG_FILE" 2>&1; then
    success "Django check: OK"
else
    warn "Django check ha rilevato problemi (controlla $LOG_FILE)"
fi

# 9. SERVICE RESTART
section "Step 9/9: Restart Service"
log "Reloading $SERVICE_NAME (graceful)..."

if sudo systemctl reload "$SERVICE_NAME" 2>/dev/null; then
    success "Service reloaded (zero downtime)"
else
    warn "Reload fallito, provo restart..."
    if sudo systemctl restart "$SERVICE_NAME"; then
        success "Service restarted"
    else
        error "Restart servizio fallito"
        rollback "$CURRENT_COMMIT"
    fi
fi

# 10. POST-DEPLOY HEALTH CHECK
section "Post-Deploy Health Check"
log "Waiting for service to be ready..."
sleep 3

if health_check; then
    success "Health check: OK"
    success "===== DEPLOY COMPLETATO CON SUCCESSO ====="
    log "Commit deployed: $NEW_COMMIT"
    log "Backup database: $BACKUP_FILE"
    exit 0
else
    error "Health check fallito dopo deploy!"
    rollback "$CURRENT_COMMIT"
fi
