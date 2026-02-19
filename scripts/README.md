# MyGest Deployment Scripts

Scripts per automatizzare il deploy di MyGest in produzione.

## 📁 Scripts Disponibili

### 🚀 `deploy.sh` - Deploy Automatico
Script principale per il deploy in produzione con backup e rollback automatico.

**Utilizzo**:
```bash
./scripts/deploy.sh              # Deploy normale
./scripts/deploy.sh --skip-backup # Salta backup
./scripts/deploy.sh --force      # Forza deploy anche con health check fallito
```

**Features**:
- ✅ Backup database automatico
- ✅ Health check pre/post deploy
- ✅ Rollback automatico su errore
- ✅ Zero-downtime reload (graceful)
- ✅ Build frontend incluso
- ✅ Log colorato e dettagliato

**Log**: `/srv/mygest/logs/deploy.log`

---

### ✅ `pre_deploy_check.sh` - Validazione Pre-Deploy
Verifica che tutto sia pronto per il deploy PRIMA di pushare su produzione.

**Utilizzo**:
```bash
./scripts/pre_deploy_check.sh
```

**Checks Eseguiti**:
1. Git status (uncommitted changes)
2. Environment variables (.env)
3. Virtual environment
4. Python dependencies
5. Django system check
6. Database migrations
7. Backend tests (opzionale)
8. Frontend build
9. Collectstatic
10. Security checks

**Exit codes**:
- `0` = Tutto OK, ready to deploy
- `0` con warnings = OK ma review warnings
- `1` = Errori bloccanti

---

## 🔄 Workflow Raccomandato

### 1. Sviluppo Locale
```bash
# Sviluppa feature
git checkout -b feature/nuova-feature

# Test modifiche
./scripts/pre_deploy_check.sh

# Commit e push
git add .
git commit -m "feat: nuova feature"
git push origin feature/nuova-feature
```

### 2. Merge su Main
```bash
git checkout main
git merge feature/nuova-feature
git push origin main
```

### 3. Deploy su Produzione
```bash
ssh mygest@72.62.34.249
cd /srv/mygest/app
./scripts/deploy.sh
```

### 4. Verifica
```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Service status
sudo systemctl status gunicorn_mygest

# Logs
tail -f /srv/mygest/logs/deploy.log
```

---

## 🐛 Troubleshooting

### Deploy Fallisce
```bash
# Controlla logs
tail -f /srv/mygest/logs/deploy.log

# Controlla service
sudo journalctl -u gunicorn_mygest -n 50

# Rollback manuale se necessario
git reset --hard <commit-precedente>
./scripts/deploy.sh
```

### Pre-Deploy Check Fallisce
```bash
# Fix errori uno alla volta
# Poi ri-esegui
./scripts/pre_deploy_check.sh
```

### Permessi Negati
```bash
chmod +x scripts/*.sh
```

---

## 📚 Documentazione Completa

Vedi [DEPLOY_GUIDE.md](../DEPLOY_GUIDE.md) per:
- Deploy manuale step-by-step
- Rollback procedure
- Troubleshooting dettagliato
- Monitoring e logs
- Security checklist

---

## 🔧 Configurazione Richiesta

### VPS Produzione
- File `/srv/mygest/app/.env` con variabili produzione
- Service `gunicorn_mygest` configurato in systemd
- Nginx configurato come reverse proxy
- PostgreSQL e Redis attivi

### Variabili Environment (.env)
```bash
DEBUG=False
SECRET_KEY=<random-string>
ALLOWED_HOSTS=72.62.34.249,tuodominio.com
```

---

**Maintainer**: Sandro Chimenti  
**Last Updated**: 2026-02-19
