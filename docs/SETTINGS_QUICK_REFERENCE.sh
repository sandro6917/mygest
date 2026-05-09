#!/bin/bash
# =============================================================================
# Django Settings Modulari - Quick Reference Commands
# =============================================================================
# Collezione di comandi utili per gestire settings dev/prod

# -----------------------------------------------------------------------------
# GENERAZIONE SECRET_KEY
# -----------------------------------------------------------------------------

# Genera SECRET_KEY sicura (50+ char)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Output esempio:
# nf*a74i2my&f@o7!x8^kd7@&6t4co-k7qm=*c8=*8%khu-!cw-

# -----------------------------------------------------------------------------
# TEST CONFIGURAZIONE
# -----------------------------------------------------------------------------

# Development mode (default)
python manage.py check
# Output: ✓ Django settings: DEVELOPMENT mode

# Development mode (esplicito)
DJANGO_ENV=development python manage.py check

# Production mode (simulato locale)
DJANGO_ENV=production python manage.py check --deploy

# Production mode (server)
ssh user@vps
cd /srv/mygest/app
source venv/bin/activate
python manage.py check --deploy

# -----------------------------------------------------------------------------
# VERIFICA VARIABILI CARICATE
# -----------------------------------------------------------------------------

# Verifica .env
cat .env | grep -E "DJANGO_ENV|SECRET_KEY|DEBUG|ALLOWED_HOSTS|DATABASE_URL"

# Verifica settings caricati (interactive shell)
python manage.py shell
>>> from django.conf import settings
>>> print(f"DEBUG: {settings.DEBUG}")
>>> print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
>>> print(f"SECRET_KEY length: {len(settings.SECRET_KEY)} chars")
>>> print(f"CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")
>>> print(f"DATABASE: {settings.DATABASES['default']['NAME']}")

# Verifica differenze settings
python manage.py diffsettings

# Verifica quale settings module è caricato
python -c "import os; print(os.environ.get('DJANGO_SETTINGS_MODULE', 'mygest.settings'))"

# -----------------------------------------------------------------------------
# SETUP DEVELOPMENT
# -----------------------------------------------------------------------------

# Quick start (da zero)
cp .env.development.example .env
nano .env  # Modifica SECRET_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

# Output atteso:
# ✓ Django settings: DEVELOPMENT mode
# 🔧 DJANGO DEVELOPMENT MODE

# -----------------------------------------------------------------------------
# SETUP PRODUCTION
# -----------------------------------------------------------------------------

# 1. Crea .env produzione
ssh user@vps
cd /srv/mygest/app
nano .env

# Contenuto minimo .env produzione:
# DJANGO_ENV=production
# SECRET_KEY=<generata_64_caratteri>
# ALLOWED_HOSTS=mygest.example.com
# DATABASE_URL=postgresql://user:pass@localhost/db
# ARCHIVIO_BASE_PATH=/srv/mygest/archivio
# EMAIL_HOST_USER=notify@example.com
# EMAIL_HOST_PASSWORD=<secure_password>

# 2. Test configurazione
source venv/bin/activate
python manage.py check --deploy

# 3. Collectstatic (con compression)
python manage.py collectstatic --noinput

# 4. Migrate
python manage.py migrate

# 5. Restart server
sudo systemctl restart mygest

# 6. Verifica
sudo systemctl status mygest
tail -f /srv/mygest/app/logs/security.log

# -----------------------------------------------------------------------------
# TROUBLESHOOTING
# -----------------------------------------------------------------------------

# Errore: "SECRET_KEY non configurata"
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
echo "SECRET_KEY=<output_sopra>" >> .env

# Errore: "SECRET_KEY usa default insicuro"
grep "^SECRET_KEY=" .env
# Se inizia con "django-insecure", sostituisci con chiave generata

# Errore: "SECRET_KEY troppo corta"
grep "^SECRET_KEY=" .env | awk -F= '{print length($2)}'
# Se < 50, genera nuova chiave

# Errore: "ALLOWED_HOSTS non configurato" (production)
echo "ALLOWED_HOSTS=mygest.example.com" >> .env

# Errore: "ALLOWED_HOSTS contiene wildcard '*'"
grep "^ALLOWED_HOSTS=" .env
# Sostituisci "*" con domini espliciti

# Errore: "Database password non configurata" (production)
echo "DB_PASSWORD=SecurePassword123!" >> .env
# O usa DATABASE_URL invece

# Errore: "ARCHIVIO_BASE_PATH non esiste"
mkdir -p /srv/mygest/archivio
chown mygest:mygest /srv/mygest/archivio

# Server non si avvia
python manage.py check
tail -f /srv/mygest/app/logs/errors.log
journalctl -u mygest -f

# Import error settings module
python -c "from mygest.settings import DEBUG; print(f'DEBUG={DEBUG}')"

# -----------------------------------------------------------------------------
# MIGRAZIONE DA SETTINGS MONOLITICO
# -----------------------------------------------------------------------------

# Backup settings vecchio (già fatto automaticamente)
# mygest/settings.py → mygest/settings_old.py

# Confronta differenze
diff mygest/settings_old.py mygest/settings/base.py

# Ripristina vecchio settings (emergenza)
mv mygest/settings.py mygest/settings_new.py
mv mygest/settings_old.py mygest/settings.py
sudo systemctl restart mygest

# -----------------------------------------------------------------------------
# DEPLOYMENT
# -----------------------------------------------------------------------------

# Pre-deploy checklist
python manage.py check --deploy
python manage.py collectstatic --noinput --dry-run
grep -E "SECRET_KEY|ALLOWED_HOSTS|DATABASE" .env

# Deploy con zero-downtime
sudo systemctl reload mygest  # Graceful reload
# O
sudo systemctl restart mygest  # Hard restart

# Post-deploy verifica
curl -I https://mygest.example.com
# Verifica headers:
# - Strict-Transport-Security
# - X-Content-Type-Options
# - X-Frame-Options

# -----------------------------------------------------------------------------
# SECURITY AUDIT
# -----------------------------------------------------------------------------

# Django deployment checklist
python manage.py check --deploy

# Verifica SECRET_KEY forte
python -c "from django.conf import settings; print(f'SECRET_KEY: {len(settings.SECRET_KEY)} chars')"

# Verifica HTTPS enforcement
python manage.py shell
>>> from django.conf import settings
>>> print(f"SECURE_SSL_REDIRECT: {settings.SECURE_SSL_REDIRECT}")
>>> print(f"SECURE_HSTS_SECONDS: {settings.SECURE_HSTS_SECONDS}")
>>> print(f"SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")

# Verifica CORS strict
python manage.py shell
>>> from django.conf import settings
>>> print(f"CORS_ALLOWED_ORIGINS: {settings.CORS_ALLOWED_ORIGINS}")
# Output atteso produzione: ['https://mygest.example.com']

# Test HTTPS redirect (produzione)
curl -I http://mygest.example.com
# Output atteso: HTTP/1.1 301 Moved Permanently → https://

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------

# Tail security log
tail -f /srv/mygest/app/logs/security.log

# Find failed login attempts
grep "WARN" /srv/mygest/app/logs/security.log

# Error log
tail -f /srv/mygest/app/logs/errors.log

# Protocollazione log
tail -f /srv/mygest/app/logs/protocollazione.log

# Systemd logs
journalctl -u mygest -n 100
journalctl -u mygest -f  # Follow

# -----------------------------------------------------------------------------
# ENVIRONMENT SWITCHING
# -----------------------------------------------------------------------------

# Switch a development (locale)
export DJANGO_ENV=development
python manage.py runserver

# Switch a production (locale test)
export DJANGO_ENV=production
python manage.py check --deploy

# Permanente in systemd (VPS)
sudo nano /etc/systemd/system/mygest.service
# Aggiungi:
# Environment="DJANGO_ENV=production"
sudo systemctl daemon-reload
sudo systemctl restart mygest

# -----------------------------------------------------------------------------
# BACKUP & RESTORE
# -----------------------------------------------------------------------------

# Backup configurazione
cp .env .env.backup.$(date +%Y%m%d)

# Backup database (con encryption)
export $(cat .env | grep -v "^#" | xargs)
pg_dump mygest_production | gpg --encrypt --recipient admin@example.com > backup_$(date +%Y%m%d).sql.gpg

# Restore database
gpg --decrypt backup_20260303.sql.gpg | psql mygest_production

# -----------------------------------------------------------------------------
# MONITORING
# -----------------------------------------------------------------------------

# Check disk space archivio
df -h /srv/mygest/archivio

# Check Redis
redis-cli ping
redis-cli INFO stats

# Check PostgreSQL
sudo -u postgres psql -c "SELECT datname, pg_size_pretty(pg_database_size(datname)) FROM pg_database;"

# Check processes
ps aux | grep gunicorn
ps aux | grep nginx

# -----------------------------------------------------------------------------
# UTILITIES
# -----------------------------------------------------------------------------

# Generate random password (database, email, etc)
openssl rand -base64 32

# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])

# Test database connection
python manage.py dbshell
\dt  # List tables
\q   # Quit

# Clear cache (Redis)
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()

# Create superuser
python manage.py createsuperuser

# Update static files
python manage.py collectstatic --noinput

# -----------------------------------------------------------------------------
# PERFORMANCE
# -----------------------------------------------------------------------------

# Analyze queries slow
python manage.py shell
>>> from django.db import connection
>>> connection.queries[:10]  # Last 10 queries

# Test Redis performance
redis-cli --latency

# Test PostgreSQL performance
sudo -u postgres psql mygest_production -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"

# -----------------------------------------------------------------------------
# DOCUMENTATION
# -----------------------------------------------------------------------------

# Vedi documentazione completa
cat docs/DJANGO_SETTINGS_MODULARI.md
cat docs/DJANGO_SETTINGS_HARDENING_IMPLEMENTATION.md
cat docs/SECURITY_CHECKLIST.md
cat .env.example

# Online
# https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
