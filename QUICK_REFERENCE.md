# ⚡ MyGest Deploy - Quick Reference

Comandi rapidi per operazioni comuni.

---

## 🚀 Deploy

### Deploy Automatico (CI/CD)
```bash
# Push su main → deploy automatico
git push origin main
```

### Deploy Manuale (VPS)
```bash
ssh mygest@72.62.34.249
cd /srv/mygest/app
./scripts/deploy.sh
```

### Deploy Senza Backup
```bash
./scripts/deploy.sh --skip-backup
```

### Deploy Forzato
```bash
./scripts/deploy.sh --force
```

---

## 🧪 Testing

### Pre-Deploy Check
```bash
./scripts/pre_deploy_check.sh
```

### Backend Tests
```bash
source venv/bin/activate
pytest --maxfail=5 -v
```

### Frontend Build
```bash
cd frontend
npm run build
```

### Django Check
```bash
python manage.py check --deploy
```

---

## 🏥 Health & Monitoring

### Health Check
```bash
curl http://localhost:8000/api/v1/health/ | jq
```

### Service Status
```bash
sudo systemctl status gunicorn_mygest
```

### View Logs
```bash
# Deploy log
tail -f /srv/mygest/logs/deploy.log

# Service log
sudo journalctl -u gunicorn_mygest -f

# Last 100 lines
sudo journalctl -u gunicorn_mygest -n 100
```

---

## 🔄 Git Operations

### Feature Branch Workflow
```bash
# Create feature
git checkout -b feature/nome-feature

# Develop...
git add .
git commit -m "feat: descrizione"
git push origin feature/nome-feature

# Open PR on GitHub
```

### Release Tag
```bash
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

---

## 🔙 Rollback

### Auto Rollback
```bash
# Il deploy script fa rollback automatico su errore
```

### Manual Rollback
```bash
cd /srv/mygest/app
git log --oneline -5
git reset --hard <commit-hash>
./scripts/deploy.sh
```

---

## 🔐 Environment

### Check Environment Variables
```bash
cat /srv/mygest/app/.env | grep -E "DEBUG|SECRET_KEY|ALLOWED_HOSTS"
```

### Generate SECRET_KEY
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 💾 Database

### Backup Database
```bash
pg_dump mygest > /srv/mygest/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database
```bash
psql mygest < /srv/mygest/backups/db_20260219_143022.sql
```

### Check Migrations
```bash
python manage.py showmigrations
```

### Apply Migrations
```bash
python manage.py migrate
```

---

## 🛠️ Maintenance

### Restart Service
```bash
# Graceful reload (zero downtime)
sudo systemctl reload gunicorn_mygest

# Full restart
sudo systemctl restart gunicorn_mygest
```

### Restart Nginx
```bash
sudo systemctl restart nginx
```

### Check Disk Space
```bash
df -h
du -sh /srv/mygest/archivio
```

### Clean Old Backups (keep last 30 days)
```bash
find /srv/mygest/backups -name "db_*.sql" -mtime +30 -delete
```

---

## 📊 GitHub Actions

### View Workflow Runs
```
https://github.com/sandro6917/mygest/actions
```

### Manual Trigger Deploy
```
GitHub → Actions → Deploy to Production → Run workflow
```

### Check Secrets
```
GitHub → Settings → Secrets and variables → Actions
```

---

## 🔍 Debugging

### Check Service Running
```bash
ps aux | grep gunicorn
```

### Check Port in Use
```bash
sudo lsof -i :8000
```

### Test Gunicorn Manually
```bash
cd /srv/mygest/app
source /srv/mygest/venv/bin/activate
gunicorn mygest.wsgi:application --bind 0.0.0.0:8000
```

### Check Nginx Config
```bash
sudo nginx -t
```

---

## 📁 File Locations

```
/srv/mygest/
├── app/                     # Repository
│   ├── .env                # Environment variables
│   ├── manage.py           # Django management
│   └── scripts/
│       ├── deploy.sh       # Deploy script
│       └── pre_deploy_check.sh
├── venv/                   # Python virtual environment
├── archivio/               # NAS storage
├── backups/                # Database backups
│   └── db_*.sql
└── logs/                   # Logs
    ├── deploy.log          # Deploy logs
    └── *.log
```

---

## 🆘 Emergency Procedures

### Service Down
```bash
# 1. Check status
sudo systemctl status gunicorn_mygest

# 2. Check logs
sudo journalctl -u gunicorn_mygest -n 50

# 3. Restart
sudo systemctl restart gunicorn_mygest

# 4. If still down, check database
sudo systemctl status postgresql
sudo systemctl status redis
```

### Deploy Failed
```bash
# 1. Check deploy log
tail -n 100 /srv/mygest/logs/deploy.log

# 2. Rollback to last working commit
cd /srv/mygest/app
git log --oneline -10
git reset --hard <last-working-commit>
./scripts/deploy.sh

# 3. Verify
curl http://localhost:8000/api/v1/health/
```

### Database Connection Error
```bash
# 1. Check PostgreSQL
sudo systemctl status postgresql

# 2. Check credentials in .env
cat /srv/mygest/app/.env | grep DATABASE

# 3. Test connection
psql -U mygest_user -d mygest -h 127.0.0.1

# 4. Restart PostgreSQL if needed
sudo systemctl restart postgresql
```

---

## 📞 Help

- 📘 **Full Deploy Guide**: [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md)
- 🤖 **CI/CD Setup**: [CICD_SETUP_GUIDE.md](CICD_SETUP_GUIDE.md)
- 📝 **Implementation Summary**: [DEPLOY_IMPLEMENTATION_SUMMARY.md](DEPLOY_IMPLEMENTATION_SUMMARY.md)

---

**Last Updated**: 2026-02-19
