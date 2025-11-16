# Guida rapida alla messa in produzione di MyGest

Questa guida accompagna un/una principiante nei passaggi fondamentali per pubblicare l'applicazione **MyGest** in un ambiente Linux (es. Ubuntu 22.04 LTS). Se ti senti in difficoltà con un passaggio, procedi lentamente e verifica ogni comando prima di lanciarlo.

---

## 1. Prerequisiti e concetti chiave
- **Accesso al server**: un server Linux raggiungibile via SSH, con almeno 2 vCPU, 4 GB di RAM e 20 GB di spazio libero.
- **Utente amministratore**: un account con permessi `sudo`.
- **Dominio o indirizzo IP**: facoltativo ma consigliato per configurare HTTPS.
- **Componenti principali**: Python 3.11+, PostgreSQL 14+, Git, Nginx, Gunicorn.

> 💡 Se il server è nuovo, aggiorna subito i pacchetti con `sudo apt update && sudo apt upgrade -y`.

---

## 2. Installazione dei pacchetti di sistema
Esegui i seguenti comandi (copiali una riga alla volta):

```bash
sudo apt install -y python3 python3-venv python3-pip git postgresql postgresql-contrib nginx
```

Verifica le versioni installate:

```bash
python3 --version
psql --version
nginx -v
```

---

## 3. Preparazione del database PostgreSQL
1. Entra nella shell di PostgreSQL:
   ```bash
   sudo -u postgres psql
   ```
2. Crea database e utente (sostituisci le password con valori sicuri!):
   ```sql
   CREATE DATABASE mygest;
   CREATE USER mygest_user WITH PASSWORD 'metti_una_password_sicura';
   ALTER ROLE mygest_user SET client_encoding TO 'UTF8';
   ALTER ROLE mygest_user SET default_transaction_isolation TO 'read committed';
   ALTER ROLE mygest_user SET timezone TO 'Europe/Rome';
   GRANT ALL PRIVILEGES ON DATABASE mygest TO mygest_user;
   \q
   ```

> 🔐 Registra la password in un luogo sicuro: servirà nel file di configurazione.

---

## 4. Clonazione del progetto e creazione ambiente virtuale
1. Scegli una cartella di lavoro, es. `/opt/mygest`:
   ```bash
   sudo mkdir -p /opt/mygest
   sudo chown $USER:$USER /opt/mygest
   cd /opt/mygest
   ```
2. Clona il repository (adatta l'URL al tuo caso):
   ```bash
   git clone https://github.com/tuo-account/mygest.git
   cd mygest
   ```
3. Crea e attiva un ambiente virtuale Python:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
4. Installa le dipendenze:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

Quando vuoi uscire dall'ambiente virtuale usa `deactivate`.

---

## 5. Configurazione delle variabili sensibili
Il file `mygest/settings.py` contiene valori di esempio **non adeguati alla produzione** (secret key, credenziali email, `DEBUG=True`). Prima di andare online devi spostarli in variabili d'ambiente.

1. Crea un file `.env` nella radice del progetto:
   ```bash
   cp .env.example .env  # se esiste
   nano .env             # altrimenti crealo da zero
   ```
2. Inserisci valori personalizzati, ad esempio:
   ```bash
   DJANGO_SECRET_KEY=generane_una_con_django
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=tuodominio.it,localhost
   DATABASE_URL=postgres://mygest_user:metti_una_password_sicura@127.0.0.1:5432/mygest
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST=smtp.tuodominio.it
   EMAIL_PORT=587
   EMAIL_HOST_USER=no-reply@tuodominio.it
   EMAIL_HOST_PASSWORD=PasswordEmailSicura
   DEFAULT_FROM_EMAIL=no-reply@tuodominio.it
   ARCHIVIO_BASE_PATH=/mnt/archivio
   ```
3. Adatta `mygest/settings.py` per leggere queste variabili (usa `django-environ`, già elencato nei requisiti). Esempio minimale da inserire in testa al file:
   ```python
   import environ

   env = environ.Env(
       DJANGO_DEBUG=(bool, False),
   )
   environ.Env.read_env(env_file=BASE_DIR / '.env')

   SECRET_KEY = env('DJANGO_SECRET_KEY')
   DEBUG = env('DJANGO_DEBUG')
   ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['localhost'])
   DATABASES = {
       'default': env.db(),
   }
   ```
   Assicurati di rimuovere o commentare le impostazioni hard-coded esistenti.

> ❗ Non pubblicare mai il file `.env` su Git: aggiungilo a `.gitignore`.

---

## 6. Applicazione delle migrazioni e dati iniziali
1. Attiva l'ambiente virtuale (`source venv/bin/activate`).
2. Esegui le migrazioni:
   ```bash
   python manage.py migrate
   ```
3. Crea un utente amministratore per l'area `/admin`:
   ```bash
   python manage.py createsuperuser
   ```
4. Carica eventuali dati iniziali (se previsti dalla tua organizzazione).

---

## 7. Gestione dei file statici e media
1. Raccogli i file statici in `staticfiles/` (verrà creata automaticamente):
   ```bash
   python manage.py collectstatic
   ```
2. Verifica i permessi su `media/` (per file caricati dagli utenti):
   ```bash
   sudo chown -R www-data:www-data media
   sudo chmod -R 750 media
   ```
   Adatta utente/gruppo se usi un altro servizio web.

---

## 8. Test locale prima della messa in servizio
Avvia il server Django in modalità produzione (con `DEBUG=False`) per verificare che tutto funzioni:

```bash
python manage.py runserver 0.0.0.0:8000
```

Apri l'indirizzo `http://<IP-server>:8000` dal tuo browser. Se tutto è ok, interrompi il server con `Ctrl+C`.

---

## 9. Configurazione di Gunicorn (WSGI)
1. Installa Gunicorn (già presente in `requirements.txt`, ma assicurati sia nell'ambiente virtuale):
   ```bash
   pip install gunicorn
   ```
2. Test manuale:
   ```bash
   gunicorn mygest.wsgi:application --bind 0.0.0.0:8001
   ```
   Visita `http://<IP-server>:8001`. Esci con `Ctrl+C`.
3. Crea un servizio `systemd` per avviare Gunicorn automaticamente:
   ```bash
   sudo nano /etc/systemd/system/mygest.service
   ```
   Inserisci:
   ```ini
   [Unit]
   Description=Gunicorn MyGest
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/mygest/mygest
   Environment="PATH=/opt/mygest/mygest/venv/bin"
   EnvironmentFile=/opt/mygest/mygest/.env
   ExecStart=/opt/mygest/mygest/venv/bin/gunicorn mygest.wsgi:application \
     --bind unix:/run/mygest.sock

   [Install]
   WantedBy=multi-user.target
   ```
4. Ricarica e avvia il servizio:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable mygest
   sudo systemctl start mygest
   sudo systemctl status mygest
   ```
   Assicurati che lo stato sia `active (running)`.

---

## 10. Configurazione di Nginx (reverse proxy)
1. Crea un blocco server:
   ```bash
   sudo nano /etc/nginx/sites-available/mygest
   ```
2. Inserisci (sostituisci `tuodominio.it` e i percorsi secondo necessità):
   ```nginx
   server {
       listen 80;
       server_name tuodominio.it;

       client_max_body_size 20M;

       location = /favicon.ico { access_log off; log_not_found off; }

       location /static/ {
           alias /opt/mygest/mygest/staticfiles/;
       }

       location /media/ {
           alias /opt/mygest/mygest/media/;
       }

       location / {
           include proxy_params;
           proxy_pass http://unix:/run/mygest.sock;
       }
   }
   ```
3. Abilita il sito ed esegui il test di configurazione:
   ```bash
   sudo ln -s /etc/nginx/sites-available/mygest /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```
4. (Consigliato) Aggiungi HTTPS con Let's Encrypt:
   ```bash
   sudo apt install -y certbot python3-certbot-nginx
   sudo certbot --nginx -d tuodominio.it
   ```

---

## 11. Configurazione di sicurezza aggiuntiva
- Imposta `CSRF_COOKIE_SECURE=True`, `SESSION_COOKIE_SECURE=True` e `SECURE_HSTS_SECONDS=31536000` in produzione.
- Rimuovi credenziali sensibili dal codice sorgente.
- Limita l'accesso SSH (chiavi SSH, disabilitare login password).
- Esegui backup regolari del database (`pg_dump`) e della cartella `media/`.

---

## 12. Verifiche post-deploy
- Visita `/admin` e accedi con il superuser creato.
- Controlla il funzionamento di caricamento documenti e stampa etichette.
- Invia una email di prova (es. reset password).
- Monitora i log in `/opt/mygest/mygest/logs` e in `/var/log/nginx/`.

---

## 13. Aggiornamenti e manutenzione
Quando esce una nuova versione o devi applicare modifiche:

```bash
cd /opt/mygest/mygest
source venv/bin/activate
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart mygest
sudo systemctl restart nginx
```

Esegui i test automatici (se presenti):

```bash
pytest
```

---

## 14. Risoluzione dei problemi più comuni
- **Errore 502 Bad Gateway**: controlla lo stato di Gunicorn (`sudo systemctl status mygest`).
- **500 Internal Server Error**: guarda i log Django in `logs/` e quelli di Nginx.
- **File statici non visibili**: assicurati che `collectstatic` sia stato eseguito e che i percorsi `alias` in Nginx siano corretti.
- **Email non inviate**: verifica credenziali SMTP e porte (`EMAIL_PORT`, `EMAIL_USE_TLS/SSL`).
- **Permessi su media**: controlla proprietario e permessi delle cartelle.

---

## 15. Checklist finale
- [ ] Credenziali sensibili spostate in `.env` e secret key rigenerata.
- [ ] `DEBUG=False`, `ALLOWED_HOSTS` include dominio/IP.
- [ ] Database PostgreSQL funzionante con utente dedicato.
- [ ] Migrazioni e superuser creati.
- [ ] File statici raccolti e serviti da Nginx.
- [ ] Servizio Gunicorn attivo e abilitato, Nginx configurato.
- [ ] HTTPS configurato (Let's Encrypt o certificato aziendale).
- [ ] Backup pianificati (database + media).

Se la checklist è completa, MyGest è pronto per essere usato in produzione! Buon lavoro 🎉
