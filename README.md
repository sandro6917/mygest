# MyGest - Sistema di Gestione Pratiche

[![Deploy](https://github.com/sandro6917/mygest/actions/workflows/deploy-production.yml/badge.svg)](https://github.com/sandro6917/mygest/actions/workflows/deploy-production.yml)
[![Tests](https://github.com/sandro6917/mygest/actions/workflows/test-pr.yml/badge.svg)](https://github.com/sandro6917/mygest/actions/workflows/test-pr.yml)

> 🎉 **Nuova Interfaccia Utente Moderna!** - Aggiornato il 17 Novembre 2025
> 🤖 **CI/CD Automatizzato!** - Deploy automatico con GitHub Actions

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/sandro6917/mygest.git
cd mygest

# Setup backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate

# Setup frontend
cd frontend
npm install
npm run dev

# Open browser: http://localhost:5173
```

## 📚 Documentazione

### 🔧 Development
- 📖 [Copilot Instructions](.github/copilot-instructions.md) - Linee guida sviluppo
- 🧪 [Pre-Deploy Check](scripts/README.md) - Validazione pre-deploy

### 🚀 Deployment
- 📘 [Deploy Guide](DEPLOY_GUIDE.md) - Guida completa deploy manuale
- 🤖 [CI/CD Setup](CICD_SETUP_GUIDE.md) - Configurazione GitHub Actions
- ✅ [CI/CD Checklist](CICD_CHECKLIST.md) - Setup step-by-step

### 👥 User Guide
- 📖 [Guida Utente](docs/GUIDA_UTENTE_NUOVA_UI.md) - Manuale utente UI
- 💻 [Guida Sviluppatore](docs/GUIDA_NUOVE_FUNZIONALITA_UI.md) - Nuove funzionalità
- 📑 [Indice Documentazione](docs/INDICE_DOCUMENTAZIONE_UI.md) - Indice completo

---

## � Features

### Interfaccia Moderna
- �🌓 **Dark/Light Mode** - Toggle automatico con persistenza
- 🔔 **Toast Notifications** - Notifiche moderne non invasive  
- ✅ **Form Intelligenti** - Validazione real-time mentre digiti
- 🎨 **Icone SVG** - Navigazione più intuitiva con icone moderne
- ♿ **100% Accessibile** - Conforme WCAG 2.1 Level AA
- 📱 **Mobile-First** - Ottimizzato per smartphone e tablet

### CI/CD Automation
- 🤖 **Deploy Automatico** - Su push a `main`
- 🧪 **Test Automatici** - Su ogni Pull Request
- 📦 **Release Automation** - Deploy con git tags
- 🔙 **Rollback Automatico** - Su errori deploy
- 🏥 **Health Checks** - Monitoring integrato

---

## 📋 Panoramica Progetto

Sistema di gestione pratiche full-stack con Django + React.

## ⚙️ Requisiti

### Locale (Sviluppo)
- **Python**: 3.10+
- **Node.js**: 20+
- **PostgreSQL**: 13+
- **Redis**: 6+
- **Git**: 2.30+

### VPS (Produzione)
- **OS**: Ubuntu 22.04
- **Python**: 3.10+
- **PostgreSQL**: 13+
- **Redis**: 6+
- **Nginx**: 1.18+
- **Gunicorn**: Servizio systemd configurato

## 🔄 Workflow di Sviluppo

### 1. Setup Locale

```bash
# Clone e setup
git clone https://github.com/sandro6917/mygest.git
cd mygest
   ```bash
   source venv/bin/activate
   export DJANGO_SETTINGS_MODULE=mygest.settings
   python manage.py test
   ```
3. Committa e unisci in `main`:
   ```bash
   git add ...
   git commit -m "Descrizione"
   git checkout main
   git merge feature/nome-feature
   git push origin main
   ```
4. Tagga la release (opzionale ma consigliato):
   ```bash
   git tag -a v1.0.1 -m "Breve descrizione"
   git push origin v1.0.1
   ```

## Deploy sulla VPS

1. Collegati alla VPS:
   ```bash
   ssh mygest@72.62.34.249
   cd /srv/mygest/app
   ```
2. Assicurati che il repo sia aggiornato:
   ```bash
   git pull
   ```
3. Esegui lo script di deploy:
   ```bash
   chmod +x scripts/deploy.sh   # solo la prima volta
   ./scripts/deploy.sh
   ```
   Lo script esegue:
   - `git fetch/reset` sul branch `main`
   - Aggiornamento della virtualenv
   - `python manage.py migrate`
   - `python manage.py collectstatic`
   - Restart di `gunicorn_mygest`
   I log sono salvati in `/srv/mygest/logs/deploy.log`.

4. Controlla lo stato:
   ```bash
   sudo journalctl -u gunicorn_mygest -n 50
   sudo systemctl status gunicorn_mygest
   ```
   Effettua uno smoke test via browser (`https://mygest.sandrochimenti.it`).

## Sincronizzare il database (Produzione → Locale)

1. Sulla VPS:
   ```bash
   sudo -u postgres pg_dump -Fc mygest > /tmp/mygest.dump
   ```
2. Scarica il dump in locale:
   ```bash
   scp mygest@72.62.34.249:/tmp/mygest.dump /tmp/
   ```
3. In locale (attenzione: sovrascrive il DB locale):
   ```bash
   dropdb mygest
   createdb mygest
   pg_restore -Fc -d mygest /tmp/mygest.dump
   rm /tmp/mygest.dump
   ```
4. Pulizia sulla VPS:
   ```bash
   ssh mygest@72.62.34.249 'rm /tmp/mygest.dump'
   ```

## Backup e monitoraggio

- Backup giornalieri: `/srv/mygest/scripts/backup.sh` (pg_dump, archivio, upload su Google Drive) con cron alle 02:00.
- Monitoraggio heartbeat: configurato in `backup.sh` tramite Healthchecks.
- Log di deploy: `/srv/mygest/logs/deploy.log`.

## Note

- Non inviare mai credenziali nel repository (`.env` e `secrets/` sono ignorati).
- Aggiorna `ARCHIVIO_BASE_PATH` nel `.env` se sposti l'archivio:
  - **Locale (WSL)**: `/mnt/archivio` (montaggio NAS)
  - **Produzione (VPS)**: `/srv/mygest/archivio`
- **Gestione Storage**: Vedi [docs/guida_storage.md](docs/guida_storage.md) per la configurazione completa dello storage e la migrazione dei file
- Se aggiungi servizi (Celery, WebSocket), crea relative unit systemd e aggiorna lo script di deploy.
- In caso di rollback, puoi usare `git checkout <tag>` sulla VPS e rilanciare `scripts/deploy.sh`.

## 👩‍💻 Sviluppo Locale e Accesso Remoto

### Avvio rapido in locale

```bash
# Terminale 1 – Backend Django
python manage.py runserver

# Terminale 2 – Frontend Vite
cd frontend
npm install        # prima volta
npm run dev
```

### Esporre l'ambiente via Tailscale

Per permettere ad altri device (o a te stesso da remoto) di usare l'interfaccia React tramite la rete Tailscale:

1. **Backend** – avvia Django su tutte le interfacce, così l'IP Tailscale risponde sulla porta 8000:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```
2. **Frontend** – esponi Vite su tutte le interfacce:
   ```bash
   cd frontend
   npm run dev -- --host 0.0.0.0 --port 5173
   ```
3. **Connessione** – da un altro computer in Tailscale apri `http://<IP-tailscale-del-PC>:5173`.

Grazie alla nuova configurazione (`VITE_API_URL=/api/v1` e fallback dinamici in `frontend/src/config.ts`), tutte le richieste API passano dal proxy di Vite, evitando errori di rete durante il login anche quando l'app è raggiunta tramite Tailscale.

