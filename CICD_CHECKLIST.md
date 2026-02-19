# ✅ GitHub Actions Setup Checklist

Usa questa checklist per configurare CI/CD su MyGest.

## 🔐 1. SSH Key Setup

- [ ] Genera SSH key per GitHub Actions
  ```bash
  ssh-keygen -t ed25519 -C "github-actions@mygest" -f ~/.ssh/github_actions_mygest
  ```

- [ ] Copia public key sul VPS
  ```bash
  ssh-copy-id -i ~/.ssh/github_actions_mygest.pub mygest@72.62.34.249
  ```

- [ ] Testa connessione SSH
  ```bash
  ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249
  ```

## 🔑 2. GitHub Secrets Configuration

Vai su: **GitHub Repo → Settings → Secrets and variables → Actions**

- [ ] Aggiungi secret `SSH_HOST` = `72.62.34.249`
- [ ] Aggiungi secret `SSH_USER` = `mygest`
- [ ] Aggiungi secret `SSH_KEY` = contenuto di `~/.ssh/github_actions_mygest` (private key)
- [ ] (Opzionale) Aggiungi secret `SSH_PORT` = `22`

## 🌍 3. GitHub Environment Setup

- [ ] Crea environment "production"
  - GitHub Repo → Settings → Environments → New environment
  - Nome: `production`

- [ ] (Opzionale) Configura protection rules
  - Required reviewers: Aggiungi te stesso
  - Deployment branches: Solo `main`

## 📦 4. VPS Preparation

SSH su VPS e verifica:

- [ ] File `.env` esiste in `/srv/mygest/app/.env`
  ```bash
  ssh mygest@72.62.34.249
  cat /srv/mygest/app/.env | grep -E "DEBUG|SECRET_KEY"
  ```

- [ ] Script deploy eseguibile
  ```bash
  ls -la /srv/mygest/app/scripts/deploy.sh
  chmod +x /srv/mygest/app/scripts/deploy.sh
  ```

- [ ] Service gunicorn attivo
  ```bash
  sudo systemctl status gunicorn_mygest
  ```

- [ ] Cartelle esistenti
  ```bash
  ls -la /srv/mygest/backups
  ls -la /srv/mygest/logs
  ```

## 🧪 5. Test Workflows Localmente

- [ ] Pre-deploy check passa
  ```bash
  cd /home/sandro/mygest
  ./scripts/pre_deploy_check.sh
  ```

- [ ] Frontend build funziona
  ```bash
  cd frontend
  npm run build
  ```

- [ ] Backend tests passano
  ```bash
  pytest --maxfail=5
  ```

## 🚀 6. Test Deploy Workflow

- [ ] Commit files workflow
  ```bash
  git add .github/workflows/
  git commit -m "ci: aggiungi GitHub Actions workflows"
  git push origin main
  ```

- [ ] Verifica workflow parte
  - Vai su GitHub → Actions tab
  - Dovresti vedere "Deploy to Production" in esecuzione

- [ ] Monitora logs
  ```bash
  # Sul VPS
  ssh mygest@72.62.34.249
  tail -f /srv/mygest/logs/deploy.log
  ```

- [ ] Verifica health check
  ```bash
  curl http://72.62.34.249:8000/api/v1/health/
  ```

## ✅ 7. Verifica Finale

- [ ] Workflow "Deploy to Production" completato con successo
- [ ] Health check verde
- [ ] Service attivo: `sudo systemctl status gunicorn_mygest`
- [ ] Applicazione accessibile via browser

## 🎯 8. Primo Deploy Completo

- [ ] Crea feature branch
  ```bash
  git checkout -b feature/test-cicd
  ```

- [ ] Modifica qualcosa (es. README)
  ```bash
  echo "# Test CI/CD" >> README.md
  git add README.md
  git commit -m "test: verifica CI/CD"
  git push origin feature/test-cicd
  ```

- [ ] Apri Pull Request su GitHub

- [ ] Verifica workflow "Test Pull Request" passa

- [ ] Merge PR su main

- [ ] Verifica workflow "Deploy to Production" parte automaticamente

- [ ] Verifica deploy completato con successo

## 🏷️ 9. Test Release Deploy (Opzionale)

- [ ] Crea tag release
  ```bash
  git checkout main
  git pull origin main
  git tag -a v1.0.0 -m "Release 1.0.0 - CI/CD Setup"
  git push origin v1.0.0
  ```

- [ ] Verifica workflow "Release Deploy" parte

- [ ] Verifica GitHub Release creata
  - GitHub Repo → Releases

## 📊 10. Post-Setup

- [ ] Aggiungi badge al README (opzionale)
  ```markdown
  ![Deploy](https://github.com/sandro6917/mygest/actions/workflows/deploy-production.yml/badge.svg)
  ```

- [ ] Documenta processo team (se applicabile)

- [ ] Schedule primo backup test
  ```bash
  ssh mygest@72.62.34.249
  ls -lh /srv/mygest/backups/
  ```

- [ ] Setup monitoring (opzionale)
  - Uptime monitoring (UptimeRobot, Pingdom)
  - Log aggregation (Papertrail, Loggly)

---

## 🐛 Troubleshooting

Se qualcosa va storto:

1. **Check secrets**: GitHub Settings → Secrets
2. **Check logs**: GitHub Actions → Workflow run → Job logs
3. **Check VPS**: `ssh mygest@72.62.34.249` e verifica manualmente
4. **Read guide**: [CICD_SETUP_GUIDE.md](./CICD_SETUP_GUIDE.md)

---

## ✅ Setup Complete!

Una volta completata questa checklist:
- ✅ Deploy automatico su ogni push a `main`
- ✅ Test automatici su ogni Pull Request
- ✅ Release automation con git tags
- ✅ Rollback automatico su errori

**Next**: Sviluppa features e goditi il deploy automatico! 🎉

---

**Date Completed**: _______________  
**Notes**: _______________________________________________
