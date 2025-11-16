# MyGest Deploy Workflow

Questa guida descrive come sviluppare in locale e distribuire l'applicazione Django "MyGest" sulla VPS Hostinger.

## Requisiti

- **Locale (WSL/Linux/macOS)**
  - Python 3.11
  - PostgreSQL client tools (`pg_dump`, `pg_restore`)
  - Git
  - Accesso SSH/GitHub configurato
- **VPS**
  - Ubuntu 22.04 con pacchetti installati (python3.11, nginx, postgresql, redis, git)
  - Repository clonato in `/srv/mygest/app`
  - Virtualenv in `/srv/mygest/venv`
  - File `.env` con configurazione production
  - Service systemd `gunicorn_mygest`
  - Script `scripts/deploy.sh`

## Flusso di lavoro di sviluppo

1. Crea un branch feature:
   ```bash
   git checkout -b feature/nome-feature
   ```
2. Sviluppa e testa in locale:
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
- Aggiorna `ARCHIVIO_BASE_PATH` nel `.env` se sposti l'archivio (default: `/srv/mygest/archivio`).
- Se aggiungi servizi (Celery, WebSocket), crea relative unit systemd e aggiorna lo script di deploy.
- In caso di rollback, puoi usare `git checkout <tag>` sulla VPS e rilanciare `scripts/deploy.sh`.
