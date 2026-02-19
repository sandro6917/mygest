#!/bin/bash
# =============================================================================
# MyGest Pre-Deploy Validation Script
# =============================================================================
# Usage: ./scripts/pre_deploy_check.sh
#
# Esegue tutti i check necessari prima di un deploy:
# - Frontend build
# - Backend tests
# - Django checks
# - Migrations check
# - Collectstatic
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNINGS=0

log() { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; WARNINGS=$((WARNINGS + 1)); }
error() { echo -e "${RED}✗${NC} $1"; FAILED=$((FAILED + 1)); }
section() { echo -e "\n${BLUE}=== $1 ===${NC}"; }

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         MyGest Pre-Deploy Validation Check               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# =============================================================================
# 1. GIT STATUS CHECK
# =============================================================================
section "1. Git Status"

if [ -d ".git" ]; then
    if git diff-index --quiet HEAD --; then
        log "No uncommitted changes"
        PASSED=$((PASSED + 1))
    else
        warn "Uncommitted changes detected"
        git status --short
    fi
    
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$CURRENT_BRANCH" = "main" ]; then
        log "On main branch"
        PASSED=$((PASSED + 1))
    else
        warn "Not on main branch (current: $CURRENT_BRANCH)"
    fi
else
    error "Not a git repository"
fi

# =============================================================================
# 2. ENVIRONMENT CHECK
# =============================================================================
section "2. Environment Configuration"

if [ -f ".env" ]; then
    log ".env file exists"
    PASSED=$((PASSED + 1))
    
    # Check critical variables
    source .env
    if [ "$DEBUG" = "False" ] || [ "$DEBUG" = "false" ]; then
        warn "DEBUG=False (produzione mode)"
    else
        log "DEBUG=True (development mode)"
        PASSED=$((PASSED + 1))
    fi
else
    error ".env file not found"
fi

if [ -f ".env.example" ]; then
    log ".env.example exists"
    PASSED=$((PASSED + 1))
else
    warn ".env.example not found"
fi

# =============================================================================
# 3. VIRTUAL ENVIRONMENT
# =============================================================================
section "3. Python Virtual Environment"

# Check multiple possible venv locations
VENV_PATH=""
if [ -d "venv" ]; then
    VENV_PATH="venv"
elif [ -d "/srv/mygest/venv" ]; then
    VENV_PATH="/srv/mygest/venv"
elif [ -d ".venv" ]; then
    VENV_PATH=".venv"
fi

if [ -n "$VENV_PATH" ]; then
    log "Virtual environment exists at: $VENV_PATH"
    PASSED=$((PASSED + 1))
    
    source "$VENV_PATH/bin/activate"
    
    PYTHON_VERSION=$(python --version 2>&1)
    log "Python: $PYTHON_VERSION"
    PASSED=$((PASSED + 1))
else
    warn "Virtual environment not found (skipping Python checks)"
    warn "For production deployment, ensure venv exists at /srv/mygest/venv"
    # Don't exit - continue with other checks
fi

# =============================================================================
# 4. BACKEND DEPENDENCIES
# =============================================================================
section "4. Python Dependencies"

if pip check > /dev/null 2>&1; then
    log "All dependencies compatible"
    PASSED=$((PASSED + 1))
else
    warn "Dependency conflicts detected"
    pip check
fi

# =============================================================================
# 5. DJANGO CHECKS
# =============================================================================
section "5. Django System Check"

if python manage.py check --deploy > /dev/null 2>&1; then
    log "Django check: PASSED"
    PASSED=$((PASSED + 1))
else
    error "Django check failed:"
    python manage.py check --deploy
fi

# =============================================================================
# 6. DATABASE MIGRATIONS
# =============================================================================
section "6. Database Migrations"

if python manage.py showmigrations --plan | grep -q "\[ \]"; then
    warn "Unapplied migrations detected:"
    python manage.py showmigrations --plan | grep "\[ \]"
else
    log "All migrations applied"
    PASSED=$((PASSED + 1))
fi

if python manage.py makemigrations --dry-run --check > /dev/null 2>&1; then
    log "No missing migrations"
    PASSED=$((PASSED + 1))
else
    error "Missing migrations detected:"
    python manage.py makemigrations --dry-run
fi

# =============================================================================
# 7. BACKEND TESTS (Optional)
# =============================================================================
section "7. Backend Tests"

if command -v pytest > /dev/null 2>&1; then
    echo "Running tests (this may take a while)..."
    if pytest --maxfail=5 -q > /dev/null 2>&1; then
        log "All tests passed"
        PASSED=$((PASSED + 1))
    else
        warn "Some tests failed (run: pytest -v)"
    fi
else
    warn "pytest not installed, skipping tests"
fi

# =============================================================================
# 8. FRONTEND CHECK
# =============================================================================
section "8. Frontend Build"

if [ -d "frontend" ]; then
    cd frontend
    
    if [ -f "package.json" ]; then
        log "package.json found"
        PASSED=$((PASSED + 1))
        
        if [ -d "node_modules" ]; then
            log "node_modules exists"
            PASSED=$((PASSED + 1))
        else
            warn "node_modules not found (run: npm install)"
        fi
        
        # Try building
        echo "Building frontend (this may take a while)..."
        if npm run build > /dev/null 2>&1; then
            log "Frontend build: SUCCESS"
            PASSED=$((PASSED + 1))
            
            if [ -d "dist" ]; then
                DIST_SIZE=$(du -sh dist | cut -f1)
                log "Build output: dist/ ($DIST_SIZE)"
                PASSED=$((PASSED + 1))
            fi
        else
            error "Frontend build failed"
            echo "Run: cd frontend && npm run build"
        fi
    else
        warn "package.json not found"
    fi
    
    cd ..
else
    warn "frontend directory not found"
fi

# =============================================================================
# 9. COLLECTSTATIC
# =============================================================================
section "9. Static Files Collection"

if python manage.py collectstatic --noinput --dry-run > /dev/null 2>&1; then
    log "collectstatic: OK"
    PASSED=$((PASSED + 1))
else
    error "collectstatic failed"
fi

# =============================================================================
# 10. SECURITY CHECKS
# =============================================================================
section "10. Security Checks"

# Check SECRET_KEY
if grep -q "django-insecure" mygest/settings.py 2>/dev/null; then
    warn "Default SECRET_KEY in settings.py (ensure .env overrides it)"
fi

# Check for sensitive files
if [ -f ".env" ] && grep -q ".env" .gitignore; then
    log ".env is in .gitignore"
    PASSED=$((PASSED + 1))
else
    error ".env not in .gitignore!"
fi

# =============================================================================
# SUMMARY
# =============================================================================
echo -e "\n${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    SUMMARY                                ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Passed:   $PASSED${NC}"
echo -e "${YELLOW}⚠ Warnings: $WARNINGS${NC}"
echo -e "${RED}✗ Failed:   $FAILED${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Pre-deploy check FAILED!${NC}"
    echo "Fix the errors above before deploying."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Pre-deploy check passed with WARNINGS${NC}"
    echo "Review warnings before deploying to production."
    exit 0
else
    echo -e "${GREEN}✅ Pre-deploy check PASSED!${NC}"
    echo "Ready to deploy."
    exit 0
fi
