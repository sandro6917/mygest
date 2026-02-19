# 🚀 MyGest Deploy Guide

## 📋 Indice
- [Pre-Requisiti](#pre-requisiti)
- [Deploy Automatico](#deploy-automatico)
- [Deploy Manuale](#deploy-manuale)
- [Rollback](#rollback)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)

---

## 🔧 Pre-Requisiti

### Server VPS
- **OS**: Linux (Ubuntu/Debian)
- **Python**: 3.10+
- **PostgreSQL**: 13+
- **Redis**: 6+
- **Nginx**: 1.18+
- **Node.js**: 20+ (per build frontend)

### Configurazione Produzione

1. **File `.env` sul server**:
```bash
ssh mygest@72.62.34.249
cd /srv/mygest/app
cp .env.example .env
nano .env
```

2. **Variabili critiche**:
```bash
DEBUG=False
SECRET_KEY=<genera-chiave-random>
ALLOWED_HOSTS=72.62.34.249,tuodominio.com
ARCHIVIO_BASE_PATH=/srv/mygest/archivio
```

3. **Generare SECRET_KEY**:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🤖 Deploy Automatico (Raccomandato)

### Script: `scripts/deploy.sh`

#### Features:
- ✅ Backup automatico database
- ✅ Health check pre/post deploy
- ✅ Rollback automatico su errore
- ✅ Zero-downtime reload
- ✅ Log dettagliato

#### Utilizzo:

```bash
# Deploy normale
ssh mygest@72.62.34.249
cd /srv/mygest/app
./scripts/deploy.sh

# Deploy senza backup (use cautiously)
./scripts/deploy.sh --skip-backup

# Deploy forzato (ignora health check iniziale)
./scripts/deploy.sh --force
```

#### Output Esempio:
```
=== Step 1/9: Pre-Deploy Checks ===
✅ Health check iniziale: OK
=== Step 2/9: Backup Database ===
✅ Backup database: /srv/mygest/backups/db_20260219_143022.sql (15MB)
=== Step 3/9: Update Code ===
✅ Code updated
...
✅ ===== DEPLOY COMPLETATO CON SUCCESSO =====
```

---

## 🔨 Deploy Manuale

### 1. Pre-Deploy Check (Locale)

Prima di fare il deploy, esegui lo script di validazione in locale:

```bash
cd /home/sandro/mygest
./scripts/pre_deploy_check.sh
```

Questo verifica:
- Git status
- Environment variables
- Django checks
- Database migrations
- Frontend build
- Tests (opzionale)

### 2. Steps Deploy Manuale

#### Step 1: Backup Database
```bash
ssh mygest@72.62.34.249
cd /srv/mygest/app
pg_dump mygest > /srv/mygest/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

#### Step 2: Pull Codice
```bash
git fetch --all
git status  # Verifica branch
git pull origin main
```

#### Step 3: Build Frontend
```bash
cd frontend
npm ci --production
npm run build
cd ..
```

#### Step 4: Backend Dependencies
```bash
source /srv/mygest/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 5: Database Migrations
```bash
python manage.py migrate --noinput
```

#### Step 6: Collect Static
```bash
python manage.py collectstatic --noinput --clear
```

#### Step 7: Django Check
```bash
python manage.py check --deploy
```

#### Step 8: Restart Service
```bash
# Graceful reload (zero downtime)
sudo systemctl reload gunicorn_mygest

# Oppure restart completo
sudo systemctl restart gunicorn_mygest
```

#### Step 9: Verify
```bash
# Check service status
sudo systemctl status gunicorn_mygest

# Health check
curl http://localhost:8000/api/v1/health/

# Check logs
sudo journalctl -u gunicorn_mygest -f
```

---

## 🔙 Rollback

### Rollback Automatico
Lo script `deploy.sh` effettua rollback automatico se:
- Frontend build fallisce
- Migrations falliscono
- Health check post-deploy fallisce

### Rollback Manuale

#### Metodo 1: Git Reset
```bash
ssh mygest@72.62.34.249
cd /srv/mygest/app

# Trova commit precedente
git log --oneline -5

# Reset a commit specifico
git reset --hard <commit-hash>

# Re-deploy
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn_mygest
```

#### Metodo 2: Database Restore
```bash
# Se le migrations hanno causato problemi

# Stop service
sudo systemctl stop gunicorn_mygest

# Restore database
psql mygest < /srv/mygest/backups/db_20260219_143022.sql

# Reset migrations se necessario
python manage.py migrate <app> <migration_number>

# Restart
sudo systemctl start gunicorn_mygest
```

---

## 🐛 Troubleshooting

### Deploy Fallisce

#### 1. Frontend Build Error
```bash
# Check npm logs
cd frontend
npm run build

# Fix: Pulisci cache
rm -rf node_modules package-lock.json
npm install
npm run build
```

#### 2. Migrations Error
```bash
# Check pending migrations
python manage.py showmigrations

# Apply specific migration
python manage.py migrate <app> <migration_number>

# Fake migration se necessario (use cautiously!)
python manage.py migrate --fake <app> <migration>
```

#### 3. Collectstatic Error
```bash
# Check settings
python manage.py check

# Verify STATIC_ROOT
ls -la /srv/mygest/app/staticfiles

# Force clean
rm -rf staticfiles/*
python manage.py collectstatic --noinput --clear
```

#### 4. Service Won't Start
```bash
# Check logs
sudo journalctl -u gunicorn_mygest -n 50

# Check config
sudo systemctl cat gunicorn_mygest

# Test gunicorn manually
cd /srv/mygest/app
source /srv/mygest/venv/bin/activate
gunicorn mygest.wsgi:application --bind 0.0.0.0:8000
```

#### 5. Health Check Fails
```bash
# Test locally
curl -v http://localhost:8000/api/v1/health/

# Check database
python manage.py dbshell

# Check Redis
redis-cli ping

# Check logs
tail -f /srv/mygest/logs/deploy.log
```

### Common Issues

#### Permission Denied
```bash
# Fix ownership
sudo chown -R mygest:mygest /srv/mygest/app
sudo chmod +x scripts/*.sh
```

#### Out of Memory
```bash
# Check memory
free -h

# Check processes
ps aux | grep gunicorn

# Restart service to free memory
sudo systemctl restart gunicorn_mygest
```

#### Port Already in Use
```bash
# Find process
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

---

## 📊 Monitoring

### Health Endpoints

#### Main Health Check
```bash
curl http://localhost:8000/api/v1/health/
```

Response:
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Database connesso"
    },
    "cache": {
      "status": "healthy",
      "message": "Cache operativa"
    }
  },
  "response_time_ms": 4.58,
  "timestamp": 1771514231.603
}
```

#### Readiness Probe
```bash
curl http://localhost:8000/api/v1/ready/
```

#### Liveness Probe
```bash
curl http://localhost:8000/api/v1/live/
```

### Service Status
```bash
# Service status
sudo systemctl status gunicorn_mygest

# Logs real-time
sudo journalctl -u gunicorn_mygest -f

# Last 100 lines
sudo journalctl -u gunicorn_mygest -n 100

# Logs with timestamp
sudo journalctl -u gunicorn_mygest --since "10 minutes ago"
```

### Deploy Logs
```bash
# View deploy log
tail -f /srv/mygest/logs/deploy.log

# Last deploy
tail -n 100 /srv/mygest/logs/deploy.log

# Search errors
grep -i error /srv/mygest/logs/deploy.log
```

### Nginx Logs
```bash
# Access log
sudo tail -f /var/log/nginx/access.log

# Error log
sudo tail -f /var/log/nginx/error.log
```

### Database Status
```bash
# PostgreSQL status
sudo systemctl status postgresql

# Active connections
psql mygest -c "SELECT count(*) FROM pg_stat_activity;"

# Database size
psql mygest -c "SELECT pg_size_pretty(pg_database_size('mygest'));"
```

### Disk Space
```bash
# Check disk usage
df -h

# Check archivio size
du -sh /srv/mygest/archivio

# Find large files
find /srv/mygest -type f -size +100M
```

---

## 🔐 Security Checklist

### Before Production Deploy

- [ ] `DEBUG=False` in `.env`
- [ ] `SECRET_KEY` unica e random
- [ ] `ALLOWED_HOSTS` configurato correttamente
- [ ] `.env` non committato su Git
- [ ] Password database cambiate da default
- [ ] Firewall configurato (solo porte necessarie)
- [ ] SSL/HTTPS configurato su Nginx
- [ ] Backup automatici configurati
- [ ] Monitoring attivo

---

## 📞 Support

### Log Files
- Deploy: `/srv/mygest/logs/deploy.log`
- Django: `/srv/mygest/logs/`
- Nginx: `/var/log/nginx/`
- System: `journalctl -u gunicorn_mygest`

### Quick Commands Cheat Sheet
```bash
# Deploy
./scripts/deploy.sh

# Pre-deploy check
./scripts/pre_deploy_check.sh

# Service restart
sudo systemctl restart gunicorn_mygest

# Health check
curl http://localhost:8000/api/v1/health/

# View logs
tail -f /srv/mygest/logs/deploy.log

# Rollback
git reset --hard <commit> && ./scripts/deploy.sh
```

---

**Last Updated**: 2026-02-19  
**Version**: 2.0
