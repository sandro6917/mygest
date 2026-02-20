#!/bin/bash
################################################################################
# Setup Produzione - MyGest
################################################################################
# Script per configurare l'ambiente di produzione dopo il deploy.
# Questo script crea il file settings_local.py con i valori specifici
# per l'ambiente di produzione.
#
# USO:
#   chmod +x scripts/setup_production.sh
#   ./scripts/setup_production.sh
#
# ATTENZIONE: Eseguire SOLO sul server di produzione!
################################################################################

set -e  # Exit on error

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per stampare con colore
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Directory progetto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SETTINGS_DIR="$PROJECT_ROOT/mygest"
SETTINGS_LOCAL="$SETTINGS_DIR/settings_local.py"
SETTINGS_EXAMPLE="$SETTINGS_DIR/settings_local.py.example"

print_header "Setup Produzione - MyGest"

# Controlla se siamo nella directory corretta
if [[ ! -f "$PROJECT_ROOT/manage.py" ]]; then
    print_error "manage.py non trovato in $PROJECT_ROOT"
    print_error "Eseguire questo script dalla directory del progetto!"
    exit 1
fi

# Controlla se il file example esiste
if [[ ! -f "$SETTINGS_EXAMPLE" ]]; then
    print_error "File template non trovato: $SETTINGS_EXAMPLE"
    exit 1
fi

# Controlla se settings_local.py esiste già
if [[ -f "$SETTINGS_LOCAL" ]]; then
    print_warning "Il file settings_local.py esiste già!"
    read -p "Sovrascrivere? (s/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_info "Setup annullato."
        exit 0
    fi
    mv "$SETTINGS_LOCAL" "$SETTINGS_LOCAL.backup.$(date +%Y%m%d_%H%M%S)"
    print_success "Backup creato: $SETTINGS_LOCAL.backup.*"
fi

print_header "Configurazione Ambiente Produzione"

# Chiedi conferma ambiente
print_warning "ATTENZIONE: Stai configurando l'ambiente di PRODUZIONE!"
read -p "Sei sicuro? (s/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    print_info "Setup annullato."
    exit 0
fi

# ====================================
# INPUT PARAMETRI
# ====================================

print_header "Parametri di Configurazione"

# Debug mode
print_info "Debug mode (DEVE essere False in produzione)"
read -p "DEBUG=False? (S/n): " DEBUG_INPUT
if [[ $DEBUG_INPUT =~ ^[Nn]$ ]]; then
    DEBUG_VALUE="True"
    print_warning "DEBUG=True - OK solo per test!"
else
    DEBUG_VALUE="False"
fi

# Allowed hosts
print_info "Domini consentiti (separati da spazi)"
read -p "ALLOWED_HOSTS (es: example.com www.example.com): " ALLOWED_HOSTS_INPUT
if [[ -z "$ALLOWED_HOSTS_INPUT" ]]; then
    print_error "ALLOWED_HOSTS non può essere vuoto in produzione!"
    exit 1
fi

# Secret key
print_info "Secret key Django (generare una nuova per produzione!)"
print_info "Premi INVIO per generarne una automaticamente"
read -p "SECRET_KEY (lascia vuoto per generare): " SECRET_KEY_INPUT
if [[ -z "$SECRET_KEY_INPUT" ]]; then
    SECRET_KEY_VALUE=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    print_success "Secret key generata automaticamente"
else
    SECRET_KEY_VALUE="$SECRET_KEY_INPUT"
fi

# Database
print_header "Configurazione Database"
read -p "Database NAME [mygest]: " DB_NAME
DB_NAME=${DB_NAME:-mygest}

read -p "Database USER [mygest_user]: " DB_USER
DB_USER=${DB_USER:-mygest_user}

read -s -p "Database PASSWORD: " DB_PASSWORD
echo
if [[ -z "$DB_PASSWORD" ]]; then
    print_error "Password database obbligatoria!"
    exit 1
fi

read -p "Database HOST [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}

read -p "Database PORT [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

# File storage
print_header "Configurazione File Storage"
read -p "Path archivio base [/srv/mygest/archivio]: " ARCHIVIO_PATH
ARCHIVIO_PATH=${ARCHIVIO_PATH:-/srv/mygest/archivio}

read -p "Path importazioni [/srv/mygest/importazioni]: " IMPORT_PATH
IMPORT_PATH=${IMPORT_PATH:-/srv/mygest/importazioni}

# Antivirus
print_header "Configurazione Antivirus"
read -p "Abilitare ClamAV? (S/n): " ANTIVIRUS_INPUT
if [[ $ANTIVIRUS_INPUT =~ ^[Nn]$ ]]; then
    ANTIVIRUS_ENABLED="False"
    ANTIVIRUS_REQUIRED="False"
else
    ANTIVIRUS_ENABLED="True"
    read -p "Bloccare upload se ClamAV non disponibile? (S/n): " ANTIVIRUS_REQUIRED_INPUT
    if [[ $ANTIVIRUS_REQUIRED_INPUT =~ ^[Nn]$ ]]; then
        ANTIVIRUS_REQUIRED="False"
    else
        ANTIVIRUS_REQUIRED="True"
    fi
fi

# ====================================
# CREA FILE settings_local.py
# ====================================

print_header "Generazione settings_local.py"

# Converti ALLOWED_HOSTS in formato Python lista
ALLOWED_HOSTS_PYTHON=$(python3 << EOF
hosts = "$ALLOWED_HOSTS_INPUT".split()
print(str([h.strip() for h in hosts]))
EOF
)

cat > "$SETTINGS_LOCAL" << EOF
"""
Settings locali PRODUZIONE - generato automaticamente
Data: $(date '+%Y-%m-%d %H:%M:%S')

ATTENZIONE: Questo file contiene credenziali sensibili!
NON committare su git, NON condividere.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ====================================
# AMBIENTE
# ====================================
ENVIRONMENT = 'production'

# ====================================
# DEBUG E SICUREZZA
# ====================================
DEBUG = $DEBUG_VALUE
ALLOWED_HOSTS = $ALLOWED_HOSTS_PYTHON

SECRET_KEY = '$SECRET_KEY_VALUE'

# ====================================
# DATABASE
# ====================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': '$DB_NAME',
        'USER': '$DB_USER',
        'PASSWORD': '$DB_PASSWORD',
        'HOST': '$DB_HOST',
        'PORT': '$DB_PORT',
    }
}

# ====================================
# FILE STORAGE E ARCHIVIO
# ====================================
ARCHIVIO_BASE_PATH = '$ARCHIVIO_PATH'
UPLOAD_TEMP_DIR = 'tmp'

IMPORTAZIONI_SOURCE_DIRS = [
    '$IMPORT_PATH',
    os.path.join(ARCHIVIO_BASE_PATH, 'importazioni'),
]

MEDIA_URL = '/archivio/'
MEDIA_ROOT = ARCHIVIO_BASE_PATH

# ====================================
# UPLOAD FILE - LIMITI
# ====================================
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB

ALLOWED_FILE_EXTENSIONS = [
    'pdf', 'docx', 'doc', 'xlsx', 'xls', 'odt', 'ods',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tif', 'tiff',
    'txt', 'csv', 'zip', 'rar', '7z',
    'eml', 'msg',
    'p7m', 'p7s',
]

FORBIDDEN_FILE_EXTENSIONS = [
    'exe', 'bat', 'cmd', 'com', 'pif', 'scr',
    'sh', 'bash', 'run',
    'js', 'vbs', 'vbe', 'jar',
    'msi', 'dll', 'sys',
]

# ====================================
# ANTIVIRUS
# ====================================
ANTIVIRUS_ENABLED = $ANTIVIRUS_ENABLED
ANTIVIRUS_REQUIRED = $ANTIVIRUS_REQUIRED
CLAMAV_SOCKET = '/var/run/clamav/clamd.ctl'
CLAMAV_HOST = 'localhost'
CLAMAV_PORT = 3310

# ====================================
# SICUREZZA HTTPS (produzione)
# ====================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
EOF

chmod 600 "$SETTINGS_LOCAL"
print_success "File creato: $SETTINGS_LOCAL"
print_success "Permessi impostati: 600 (solo proprietario)"

# ====================================
# CREA DIRECTORY
# ====================================

print_header "Creazione Directory"

mkdir -p "$ARCHIVIO_PATH/tmp"
mkdir -p "$IMPORT_PATH"
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/staticfiles"

print_success "Directory archivio: $ARCHIVIO_PATH"
print_success "Directory importazioni: $IMPORT_PATH"
print_success "Directory logs: $PROJECT_ROOT/logs"
print_success "Directory static: $PROJECT_ROOT/staticfiles"

# ====================================
# VERIFICA CONFIGURAZIONE
# ====================================

print_header "Verifica Configurazione"

cd "$PROJECT_ROOT"

# Attiva virtual environment se esiste
if [[ -d "venv" ]]; then
    source venv/bin/activate
    print_success "Virtual environment attivato"
fi

# Test import settings
print_info "Test import settings..."
if python manage.py check --deploy 2>&1 | grep -q "settings_local.py"; then
    print_success "settings_local.py caricato correttamente"
else
    print_warning "Verifica manualmente il caricamento di settings_local.py"
fi

# ====================================
# PROSSIMI PASSI
# ====================================

print_header "Setup Completato!"
echo ""
print_success "Configurazione produzione creata con successo"
echo ""
print_info "PROSSIMI PASSI:"
echo ""
echo "  1. Verifica configurazione:"
echo "     python manage.py check --deploy"
echo ""
echo "  2. Esegui migrazioni database:"
echo "     python manage.py migrate"
echo ""
echo "  3. Crea superutente (se necessario):"
echo "     python manage.py createsuperuser"
echo ""
echo "  4. Raccogli file statici:"
echo "     python manage.py collectstatic --noinput"
echo ""
echo "  5. Configura cron per pulizia tmp:"
echo "     crontab -e"
echo "     0 2 * * * $PROJECT_ROOT/scripts/cleanup_tmp.sh 7"
echo ""
echo "  6. Riavvia server applicazione (gunicorn/uwsgi)"
echo ""
print_warning "IMPORTANTE: Verifica permissions su $ARCHIVIO_PATH"
print_warning "            L'utente web server deve avere accesso write!"
echo ""
