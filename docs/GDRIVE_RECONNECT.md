# Riconnessione Google Drive per Backup

## 🔴 Problema

Il token OAuth2 di rclone per Google Drive è **scaduto** (23 novembre 2025).

**Effetto**: I backup notturni vengono salvati solo localmente su VPS, **NON su Google Drive**.

## ✅ Backup Locali Funzionanti

I backup continuano a funzionare correttamente su VPS:

```
📍 Path: /srv/mygest/backups/
📅 Schedule: Ogni notte alle 2:00 AM
📦 Contenuto: Database (20MB) + Media files (99KB)
🗑️  Retention: 14 giorni
💾 Spazio: 2GB utilizzati
```

## 🔧 Procedura Riconnessione

### Metodo 1: Script Automatico

```bash
cd /home/sandro/mygest
./scripts/reconnect_gdrive.sh
```

Lo script ti guiderà attraverso il processo.

### Metodo 2: Manuale

**Step 1**: Connetti al VPS
```bash
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249
```

**Step 2**: Avvia wizard rclone
```bash
rclone config
```

**Step 3**: Segui il wizard
```
Current remotes:
  gdrive

e/n/d/r/c/s/q> e  # Edit existing remote
Name of existing remote> gdrive

# Premi INVIO su tutti i campi (mantieni config esistente)
# ...

Use auto config?
y) Yes
n) No
y/n> y  # Si aprirà il browser per autenticazione

# Autorizza rclone nel browser
# Torna al terminale quando completato

y/e/d> y  # Yes this is OK
q> q  # Quit config
```

**Step 4**: Testa connessione
```bash
rclone lsd gdrive:mygest-backups
```

Dovresti vedere:
```
2026-02-20 02:00:00    -1 prod-srv1130465
```

**Step 5**: Testa upload manuale
```bash
echo "test" > /tmp/test.txt
rclone copy /tmp/test.txt gdrive:mygest-backups/test/
rclone ls gdrive:mygest-backups/test/
```

**Step 6**: Esegui backup manuale per verificare
```bash
/srv/mygest/scripts/backup.sh
```

Controlla log:
```bash
tail -50 /srv/mygest/logs/backup.log
tail -50 /srv/mygest/logs/rclone.log
```

## 📂 Struttura Google Drive

Dopo la riconnessione, i backup saranno caricati su:

```
Google Drive/
└── mygest-backups/
    └── prod-srv1130465/
        ├── 2026-02-20_0200/
        │   ├── db.sql.gz      (Database backup)
        │   └── media.tar.gz   (Media files)
        ├── 2026-02-21_0200/
        └── ... (backup giornalieri)
```

## 🔍 Verifica Stato Attuale

```bash
# Check locale
ssh mygest@72.62.34.249 "ls -lh /srv/mygest/backups/*/db.sql.gz | tail -5"

# Check Google Drive (dopo riconnessione)
ssh mygest@72.62.34.249 "rclone ls gdrive:mygest-backups/prod-srv1130465 --max-depth 1"

# Check log backup
ssh mygest@72.62.34.249 "tail -30 /srv/mygest/logs/backup.log"

# Check cron
ssh mygest@72.62.34.249 "crontab -l | grep backup"
```

## ⚠️ Note Importanti

1. **Autenticazione richiede browser**: L'autenticazione OAuth2 richiede un browser web per l'autorizzazione Google
2. **Account Google**: Usa l'account Google configurato originalmente per rclone
3. **Permessi richiesti**: rclone necessita permessi "Google Drive API" completi
4. **Token expiry**: I token OAuth2 scadono periodicamente (ogni ~6 mesi), sarà necessario riautenticare

## 🎯 Priorità

**ALTA**: Riconnettere entro qualche giorno per avere backup off-site su cloud.

**Backup locali continuano a funzionare**, ma in caso di failure del VPS non avrai backup off-site recenti.

---

**Creato**: 2026-02-20
**Status**: Token scaduto - richiede riconnessione
