# 🤖 GitHub Actions CI/CD Setup Guide

## 📋 Indice
- [Overview](#overview)
- [Setup Secrets](#setup-secrets)
- [Workflows Disponibili](#workflows-disponibili)
- [Utilizzo](#utilizzo)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

MyGest utilizza GitHub Actions per automazione CI/CD:

- ✅ **Deploy automatico** su push a `main`
- ✅ **Test automatici** su Pull Request
- ✅ **Release deploy** su git tag
- ✅ **Zero configurazione** server-side
- ✅ **Rollback automatico** su errore

### Workflows Attivi

| Workflow | Trigger | Scopo |
|----------|---------|-------|
| `deploy-production.yml` | Push su `main` | Deploy automatico produzione |
| `test-pr.yml` | Pull Request | Test e validazione PR |
| `release-deploy.yml` | Tag `v*.*.*` | Release versionate |

---

## 🔐 Setup Secrets

### 1. Generare SSH Key per Deploy

Sul tuo computer locale:

```bash
# Genera chiave SSH dedicata per GitHub Actions
ssh-keygen -t ed25519 -C "github-actions@mygest" -f ~/.ssh/github_actions_mygest

# Output:
# - Private key: ~/.ssh/github_actions_mygest
# - Public key: ~/.ssh/github_actions_mygest.pub
```

### 2. Configurare SSH sul VPS

```bash
# Connetti al VPS
ssh mygest@72.62.34.249

# Aggiungi public key agli authorized_keys
nano ~/.ssh/authorized_keys

# Incolla il contenuto di github_actions_mygest.pub
# Salva e esci

# Verifica permessi
chmod 600 ~/.ssh/authorized_keys
```

### 3. Aggiungere Secrets su GitHub

1. Vai su GitHub: **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Aggiungi i seguenti secrets:

#### Secrets Richiesti:

| Nome | Valore | Descrizione |
|------|--------|-------------|
| `SSH_HOST` | `72.62.34.249` | IP o hostname del VPS |
| `SSH_USER` | `mygest` | Username SSH |
| `SSH_KEY` | `contenuto di github_actions_mygest` | Private key SSH (tutto il file) |
| `SSH_PORT` | `22` | Porta SSH (opzionale, default 22) |

#### Come copiare la private key:

```bash
# Linux/Mac
cat ~/.ssh/github_actions_mygest | pbcopy

# Oppure stampa a schermo
cat ~/.ssh/github_actions_mygest
```

Copia **TUTTO** il contenuto, incluso:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

### 4. Creare Environment "production"

1. GitHub repo → **Settings** → **Environments**
2. Click **New environment**
3. Nome: `production`
4. (Opzionale) Aggiungi **Protection rules**:
   - Required reviewers: Aggiungi te stesso
   - Wait timer: 0 minuti (o tempo attesa desiderato)

---

## 🔄 Workflows Disponibili

### 1. Deploy Production (`deploy-production.yml`)

**Trigger**: Push su branch `main`

**Jobs**:
1. **Test** - Esegue test backend (Django + pytest)
2. **Build Frontend** - Compila React app
3. **Deploy** - SSH su VPS ed esegue `deploy.sh`
4. **Health Check** - Verifica sistema operativo

**Utilizzo**:
```bash
# 1. Commit modifiche
git add .
git commit -m "feat: nuova feature"

# 2. Push su main
git push origin main

# 3. GitHub Actions esegue deploy automaticamente
# Vedi progresso su: https://github.com/<username>/mygest/actions
```

**Notifiche**:
- ✅ Success: Commit summary con stato deploy
- ❌ Failure: Alert con log errori

---

### 2. Test Pull Request (`test-pr.yml`)

**Trigger**: Apertura/Update di Pull Request su `main` o `develop`

**Jobs**:
1. **Backend Tests** - Django check + pytest + coverage
2. **Frontend Tests** - TypeScript check + lint + build
3. **Security Checks** - Audit dipendenze + secrets scan
4. **Summary** - Report riepilogativo

**Utilizzo**:
```bash
# 1. Crea feature branch
git checkout -b feature/nuova-funzione

# 2. Sviluppa e commit
git add .
git commit -m "feat: implementa funzione X"
git push origin feature/nuova-funzione

# 3. Apri Pull Request su GitHub
# Test automatici partono automaticamente

# 4. Review risultati e merge quando verde
```

**Check Status**:
- ✅ Tutti i test passano → PR mergeable
- ❌ Test falliscono → Fix richiesto
- ⚠️  Security warning → Review manuale

---

### 3. Release Deploy (`release-deploy.yml`)

**Trigger**: Push di git tag formato `v*.*.*`

**Features**:
- Crea GitHub Release automatica
- Genera changelog da commit
- Deploy su produzione
- Asset e documentazione

**Utilizzo**:
```bash
# 1. Assicurati di essere su main aggiornato
git checkout main
git pull origin main

# 2. Crea e push tag
git tag -a v1.0.0 -m "Release 1.0.0 - Prima release stabile"
git push origin v1.0.0

# 3. GitHub Actions:
#    - Crea GitHub Release
#    - Deploy su produzione
#    - Health check

# 4. Verifica release su:
#    https://github.com/<username>/mygest/releases
```

**Tag Naming Convention**:
- `v1.0.0` - Major release (breaking changes)
- `v1.1.0` - Minor release (nuove feature)
- `v1.0.1` - Patch release (bugfix)

---

## 🚀 Workflow Completo: Feature → Production

### Scenario Tipico:

```bash
# 1. Crea feature branch
git checkout -b feature/nuova-dashboard

# 2. Sviluppa localmente
# ... codice ...

# 3. Commit
git add .
git commit -m "feat: aggiungi dashboard analytics"

# 4. Push feature branch
git push origin feature/nuova-dashboard

# 5. Apri Pull Request su GitHub
# ✅ Test automatici partono (test-pr.yml)

# 6. Review e approva PR
# (su GitHub UI)

# 7. Merge PR su main
# ✅ Deploy automatico parte (deploy-production.yml)

# 8. Verifica deployment
curl http://72.62.34.249:8000/api/v1/health/

# 9. (Opzionale) Crea release
git checkout main
git pull origin main
git tag -a v1.1.0 -m "Release 1.1.0 - Dashboard analytics"
git push origin v1.1.0
# ✅ Release deploy parte (release-deploy.yml)
```

---

## 🔍 Monitoring & Logs

### Visualizzare Workflow Runs

1. GitHub repo → **Actions** tab
2. Click su workflow run per dettagli
3. Click su job per vedere logs

### Live Logs Durante Deploy

```bash
# Sul VPS, monitora in real-time
ssh mygest@72.62.34.249
tail -f /srv/mygest/logs/deploy.log
```

### Status Badges (Opzionale)

Aggiungi badge al README:

```markdown
![Deploy](https://github.com/<username>/mygest/actions/workflows/deploy-production.yml/badge.svg)
![Tests](https://github.com/<username>/mygest/actions/workflows/test-pr.yml/badge.svg)
```

---

## 🐛 Troubleshooting

### Deploy Fallisce

#### 1. SSH Connection Failed
```
Error: ssh: connect to host failed
```

**Fix**:
- Verifica `SSH_HOST`, `SSH_USER`, `SSH_KEY` secrets
- Testa connessione SSH manualmente:
  ```bash
  ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249
  ```

#### 2. Permission Denied
```
Error: Permission denied (publickey)
```

**Fix**:
- Verifica public key in `~/.ssh/authorized_keys` sul VPS
- Verifica permessi:
  ```bash
  chmod 700 ~/.ssh
  chmod 600 ~/.ssh/authorized_keys
  ```

#### 3. Health Check Failed
```
Error: Health check failed after deployment
```

**Fix**:
- Check logs sul VPS:
  ```bash
  ssh mygest@72.62.34.249
  sudo journalctl -u gunicorn_mygest -n 50
  ```
- Verifica service attivo:
  ```bash
  sudo systemctl status gunicorn_mygest
  ```

#### 4. Frontend Build Failed
```
Error: npm run build exited with code 1
```

**Fix**:
- Testa build localmente:
  ```bash
  cd frontend
  npm run build
  ```
- Controlla errori TypeScript
- Verifica `node_modules` updated

### Test Falliscono

#### Backend Tests Failed
```bash
# Esegui test localmente per debug
pytest -v --tb=short

# Test specifico
pytest path/to/test_file.py::test_function -v
```

#### Frontend Tests Failed
```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

### Workflow Non Parte

**Check**:
1. File workflow in `.github/workflows/` committati
2. Sintassi YAML corretta (usa validator online)
3. Branch/tag trigger corretto
4. Secrets configurati correttamente

---

## 🔒 Security Best Practices

### Secrets Management

- ✅ **MAI** committare secrets su Git
- ✅ Usa GitHub Secrets per credenziali
- ✅ Rota SSH keys periodicamente
- ✅ Limita accesso SSH (firewall, fail2ban)

### SSH Key Rotation

```bash
# Genera nuova key
ssh-keygen -t ed25519 -C "github-actions@mygest-$(date +%Y%m)" -f ~/.ssh/ga_mygest_new

# Aggiungi al VPS (non rimuovere vecchia ancora)
cat ~/.ssh/ga_mygest_new.pub | ssh mygest@72.62.34.249 'cat >> ~/.ssh/authorized_keys'

# Aggiorna secret GitHub SSH_KEY

# Testa deploy

# Se OK, rimuovi vecchia key da authorized_keys
```

### Environment Protection

GitHub Settings → Environments → production:
- ✅ Required reviewers: 1+
- ✅ Wait timer: 5 minuti (opzionale)
- ✅ Deployment branches: `main` only

---

## 📊 Metriche & Analytics

### Deploy Frequency
Vedi: GitHub → Insights → Code frequency

### Success Rate
Vedi: GitHub → Actions → Workflow runs

### Average Deploy Time
Tipicamente:
- Test: 3-5 minuti
- Build: 2-3 minuti
- Deploy: 2-4 minuti
- **Total**: 7-12 minuti

---

## 🎯 Next Steps

### Opzionale - Miglioramenti Futuri

1. **Slack/Discord Notifications**
   - Integra webhook per notifiche deploy

2. **Staging Environment**
   - Crea workflow per deploy su staging

3. **Auto-Rollback**
   - Rollback automatico se health check fallisce

4. **Performance Monitoring**
   - Integra Sentry, NewRelic, o Datadog

5. **Database Migrations Check**
   - Verifica migrations safe prima deploy

---

## 📞 Support

**Problemi CI/CD?**
1. Check Actions logs su GitHub
2. Check deploy logs: `/srv/mygest/logs/deploy.log`
3. Check service: `sudo journalctl -u gunicorn_mygest`

**Configurazione Secrets**
- GitHub Docs: https://docs.github.com/en/actions/security-guides/encrypted-secrets

---

**Last Updated**: 2026-02-19  
**Version**: 1.0
