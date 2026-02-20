# Piano Implementazione Step-by-Step
## Miglioramenti File Storage e Sicurezza

**Data**: 17 Novembre 2025
**Tempo stimato**: 3-4 ore
**Difficoltà**: Media

---

## ✅ PRE-REQUISITI

Prima di iniziare, verifica:

- [ ] Hai accesso root/sudo al server
- [ ] Python 3.10+ installato
- [ ] Virtual environment attivo
- [ ] Git configurato (per version control)
- [ ] Backup database fatto
- [ ] Backup codice fatto

---

## 📅 FASE 1: Backup e Preparazione (15 min)

### Step 1.1: Backup Database
```bash
cd /home/sandro/mygest

# Backup PostgreSQL
pg_dump mygest > backups/mygest_backup_$(date +%Y%m%d_%H%M%S).sql

# Verifica backup
ls -lh backups/
```

### Step 1.2: Backup Codice
```bash
# Commit modifiche pendenti (se presenti)
git add .
git commit -m "Checkpoint prima miglioramenti storage"

# Crea branch per nuove modifiche
git checkout -b feature/storage-security-improvements

# Backup alternativo (tar)
cd ..
tar -czf mygest_backup_$(date +%Y%m%d).tar.gz mygest/
```

### Step 1.3: Verifica Ambiente
```bash
cd mygest
source venv/bin/activate

# Verifica Python
python --version  # Deve essere 3.10+

# Verifica Django
python manage.py --version  # Deve essere 4.2+

# Test server funzionante
python manage.py check
```

**✅ Checkpoint 1**: Backup completati, ambiente verificato

---

## 📦 FASE 2: Installazione Dipendenze (20 min)

### Step 2.1: Installazione ClamAV
```bash
# Update sistema
sudo apt-get update

# Installa ClamAV
sudo apt-get install -y clamav clamav-daemon

# Installa libmagic
sudo apt-get install -y libmagic1 python3-magic

# Verifica installazione
which clamd
which freshclam
```

### Step 2.2: Configurazione ClamAV
```bash
# Ferma daemon per update
sudo systemctl stop clamav-daemon

# Aggiorna definizioni virus (può richiedere diversi minuti)
sudo freshclam

# Avvia daemon
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon

# Verifica stato
sudo systemctl status clamav-daemon
```

### Step 2.3: Test ClamAV
```bash
# Verifica socket
ls -la /var/run/clamav/clamd.ctl

# Test ping
clamdscan --version

# Test EICAR (stringa test sicura)
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > /tmp/eicar.txt
clamdscan /tmp/eicar.txt
# Output deve contenere "FOUND"

# Pulizia test
rm /tmp/eicar.txt
```

### Step 2.4: Dipendenze Python
```bash
# Installa nuove dipendenze
pip install python-magic==0.4.27
pip install clamd==1.0.2

# Verifica installazione
python -c "import magic; print(magic.__version__)"
python -c "import clamd; print('clamd OK')"

# Aggiorna requirements.txt
pip freeze > requirements_current.txt
```

**✅ Checkpoint 2**: Tutte le dipendenze installate e funzionanti

---

## ⚙️ FASE 3: Configurazione (15 min)

### Step 3.1: Creare file .env
```bash
# Crea .env dalla copia di .env.example (già presente nel progetto)
# Se non esiste, copia dal template creato
cp .env.example .env

# Modifica con editor
nano .env
```

**Configurazione minima .env:**
```bash
# Storage
ARCHIVIO_BASE_PATH=/mnt/archivio
UPLOAD_TEMP_DIR=tmp
IMPORTAZIONI_SOURCE_DIRS=/home/sandro/documenti:/mnt/archivio/importazioni

# Upload Limits
FILE_UPLOAD_MAX_MEMORY_SIZE=52428800
DATA_UPLOAD_MAX_MEMORY_SIZE=104857600

# Antivirus
ANTIVIRUS_ENABLED=true
ANTIVIRUS_REQUIRED=false
CLAMAV_SOCKET=/var/run/clamav/clamd.ctl

# Altri settings esistenti...
SECRET_KEY=your-secret-key-here
DEBUG=true
```

### Step 3.2: Creare Directory Necessarie
```bash
# Directory temporanea
mkdir -p media/tmp
chmod 755 media/tmp

# Directory importazioni (se non esiste)
mkdir -p /home/sandro/documenti
mkdir -p importazioni

# Verifica
ls -ld media/tmp
ls -ld /mnt/archivio  # Deve esistere
```

**✅ Checkpoint 3**: Configurazione completa

---

## 💻 FASE 4: Modifiche Codice (45 min)

### Step 4.1: Modificare settings.py
```bash
# Apri settings.py
nano mygest/settings.py
```

**Trova (circa linea 190):**
```python
ARCHIVIO_BASE_PATH = os.getenv("ARCHIVIO_BASE_PATH", "/mnt/archivio")

# Importazioni
IMPORTAZIONI_SOURCE_DIRS = [
    "/home/sandro/documenti",
    "/mnt/archivio/importazioni",
]
```

**Sostituisci con** (vedere `docs/SETTINGS_MODIFICATIONS.txt` per codice completo):
```python
# ====================================
# File Storage e Path Configurazione
# ====================================

ARCHIVIO_BASE_PATH = os.getenv(
    "ARCHIVIO_BASE_PATH", 
    str(BASE_DIR / "media" / "archivio") if DEBUG else "/srv/mygest/archivio"
)

UPLOAD_TEMP_DIR = os.getenv("UPLOAD_TEMP_DIR", "tmp")

IMPORTAZIONI_SOURCE_DIRS_STR = os.getenv(
    "IMPORTAZIONI_SOURCE_DIRS",
    str(BASE_DIR / "importazioni")
)
IMPORTAZIONI_SOURCE_DIRS = [
    p.strip() for p in IMPORTAZIONI_SOURCE_DIRS_STR.split(":")
    if p.strip()
]

# ... continua con resto configurazioni da SETTINGS_MODIFICATIONS.txt
```

**Aggiungi anche** (dopo la sezione storage):
```python
# ====================================
# Upload File - Limiti e Sicurezza
# ====================================

FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv(
    "FILE_UPLOAD_MAX_MEMORY_SIZE", 
    50 * 1024 * 1024
))

DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv(
    "DATA_UPLOAD_MAX_MEMORY_SIZE",
    100 * 1024 * 1024
))

ALLOWED_FILE_EXTENSIONS = [
    'pdf', 'docx', 'doc', 'xlsx', 'xls', 'odt', 'ods',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tif', 'tiff',
    'txt', 'csv', 'zip', 'rar', '7z',
    'eml', 'msg', 'p7m', 'p7s',
]

FORBIDDEN_FILE_EXTENSIONS = [
    'exe', 'bat', 'cmd', 'com', 'pif', 'scr',
    'sh', 'bash', 'run',
    'js', 'vbs', 'vbe', 'jar',
    'msi', 'dll', 'sys',
]

# ====================================
# Antivirus - ClamAV
# ====================================

ANTIVIRUS_ENABLED = os.getenv('ANTIVIRUS_ENABLED', 'true').lower() == 'true'
ANTIVIRUS_REQUIRED = os.getenv('ANTIVIRUS_REQUIRED', 'false').lower() == 'true'
CLAMAV_SOCKET = os.getenv('CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')
CLAMAV_HOST = os.getenv('CLAMAV_HOST', 'localhost')
CLAMAV_PORT = int(os.getenv('CLAMAV_PORT', '3310'))
```

### Step 4.2: Modificare documenti/models.py
```bash
nano documenti/models.py
```

**1. Aggiungi import (circa linea 4):**
```python
from .validators import validate_file_content
```

**2. Modifica campo file (circa linea 190):**
Trova:
```python
file = models.FileField(
    storage=nas_storage, 
    upload_to=documento_upload_to, 
    blank=True, 
    null=True, 
    max_length=500
)
```

Sostituisci con:
```python
file = models.FileField(
    storage=nas_storage, 
    upload_to=documento_upload_to, 
    blank=True, 
    null=True, 
    max_length=500,
    validators=[validate_file_content],  # <-- NUOVO
)
```

**3. Modifica documento_upload_to (circa linea 85):**
Trova l'ultima riga della funzione:
```python
return f"tmp/{year}/{cli_code}/{filename}"
```

Sostituisci con:
```python
temp_dir = getattr(settings, "UPLOAD_TEMP_DIR", "tmp")
return f"{temp_dir}/{year}/{cli_code}/{filename}"
```

### Step 4.3: Modificare archivio_fisico/models.py
```bash
nano archivio_fisico/models.py
```

**1. Aggiungi import (circa linea 11):**
```python
from documenti.validators import validate_file_content
```

**2. Modifica campo verbale_scan (circa linea 43):**
Trova:
```python
verbale_scan = models.FileField(
    storage=nas_storage,
    upload_to="archivio_fisico/operazioni",
    null=True,
    blank=True,
    max_length=500,
    validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "tif", "tiff"])],
    help_text="Facoltativo: carica la scansione del verbale firmato.",
)
```

Sostituisci con:
```python
verbale_scan = models.FileField(
    storage=nas_storage,
    upload_to="archivio_fisico/operazioni",
    null=True,
    blank=True,
    max_length=500,
    validators=[
        FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "tif", "tiff"]),
        validate_file_content,  # <-- NUOVO
    ],
    help_text="Facoltativo: carica la scansione del verbale firmato.",
)
```

**✅ Checkpoint 4**: Modifiche codice completate

---

## 🧪 FASE 5: Testing (30 min)

### Step 5.1: Test Syntax
```bash
# Verifica syntax Python
python -m py_compile mygest/settings.py
python -m py_compile documenti/models.py
python -m py_compile documenti/validators.py
python -m py_compile archivio_fisico/models.py

# Django check
python manage.py check
```

### Step 5.2: Test Import
```bash
python manage.py shell
```

```python
# In shell Django
from documenti.validators import validate_file_content, get_clamd_client

# Test ClamAV
cd = get_clamd_client()
print(cd.ping())  # Deve stampare 'PONG'

# Test validator
from django.core.files.uploadedfile import SimpleUploadedFile
file = SimpleUploadedFile("test.pdf", b"test", content_type="application/pdf")
validate_file_content(file)
print("Validator OK!")

exit()
```

### Step 5.3: Test Upload File
```bash
# Avvia server
python manage.py runserver
```

**In un altro terminale:**
```bash
# Monitora log
tail -f logs/protocollazione.log
```

**Nel browser:**
1. Vai a http://localhost:8000/admin/
2. Login
3. Vai a Documenti → Aggiungi documento
4. Prova a caricare un file PDF valido < 50MB → Deve funzionare
5. Prova a caricare un file .exe → Deve essere bloccato
6. Verifica log per messaggi "File scansionato: pulito"

### Step 5.4: Test Dimensione
```bash
# Crea file di 60MB
dd if=/dev/urandom of=/tmp/test_60mb.pdf bs=1M count=60

# Prova upload da UI → Deve essere rifiutato con errore "file troppo grande"
```

### Step 5.5: Test Antivirus
```bash
# Crea EICAR test file
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > /tmp/eicar.txt

# Prova upload da UI → Deve essere bloccato con messaggio virus
# Verifica log per "Virus rilevato"
```

### Step 5.6: Test Pulizia tmp/
```bash
# Test dry-run
python manage.py cleanup_tmp --days=7 --dry-run --verbose

# Test reale (se non ci sono file vecchi, il comando non farà nulla)
python manage.py cleanup_tmp --days=7 --verbose
```

### Step 5.7: Test Automatici
```bash
# Esegui test suite
python manage.py test documenti.tests.test_validators

# Se fail per ClamAV non disponibile, disabilita temporaneamente
ANTIVIRUS_ENABLED=false python manage.py test documenti.tests.test_validators
```

**✅ Checkpoint 5**: Tutti i test passano

---

## 🚀 FASE 6: Deploy Configurazione Produzione (15 min)

### Step 6.1: Cron Job per Pulizia tmp/
```bash
# Apri crontab
crontab -e

# Aggiungi riga (modifica path)
0 2 * * * cd /home/sandro/mygest && /home/sandro/mygest/venv/bin/python manage.py cleanup_tmp --days=7 >> /home/sandro/mygest/logs/cleanup_tmp.log 2>&1
```

### Step 6.2: Verifica Permessi
```bash
# Verifica permessi directory
ls -ld media/tmp/
ls -ld /mnt/archivio/

# Se necessario, aggiusta
chmod 755 media/tmp/
sudo chown -R www-data:www-data media/tmp/  # Solo se su server produzione con www-data
```

### Step 6.3: Restart Servizi (se in produzione)
```bash
# Se usi gunicorn/systemd
sudo systemctl restart mygest

# Se usi supervisor
sudo supervisorctl restart mygest

# Verifica log avvio
tail -f /var/log/mygest/error.log
```

**✅ Checkpoint 6**: Deploy completato

---

## 📊 FASE 7: Monitoraggio (10 min)

### Step 7.1: Setup Monitoring Spazio
```bash
# Crea script monitoraggio
cat > /usr/local/bin/check_tmp_size.sh << 'EOF'
#!/bin/bash
TMP_DIR="/home/sandro/mygest/media/tmp"
MAX_SIZE_MB=1024
SIZE_MB=$(du -sm "$TMP_DIR" 2>/dev/null | cut -f1)
if [ $SIZE_MB -gt $MAX_SIZE_MB ]; then
    echo "WARNING: tmp/ is ${SIZE_MB}MB (max: ${MAX_SIZE_MB}MB)"
fi
EOF

chmod +x /usr/local/bin/check_tmp_size.sh

# Test
/usr/local/bin/check_tmp_size.sh
```

### Step 7.2: Aggiungi a Cron
```bash
crontab -e

# Aggiungi check ogni 6 ore
0 */6 * * * /usr/local/bin/check_tmp_size.sh
```

### Step 7.3: Verifica Log
```bash
# Log Django
tail -50 logs/protocollazione.log

# Log ClamAV
sudo tail -50 /var/log/clamav/clamav.log

# Log pulizia tmp (dopo primo run cron)
tail -50 logs/cleanup_tmp.log
```

**✅ Checkpoint 7**: Monitoraggio attivo

---

## 📝 FASE 8: Documentazione e Commit (10 min)

### Step 8.1: Commit Modifiche
```bash
# Verifica modifiche
git status
git diff

# Add file nuovi e modificati
git add mygest/settings.py
git add documenti/models.py
git add documenti/validators.py
git add documenti/management/commands/cleanup_tmp.py
git add archivio_fisico/models.py
git add .env.example
git add .env.production.example
git add requirements-security.txt
git add docs/

# Commit
git commit -m "feat: Implementa miglioramenti sicurezza file storage

- Aggiunto validatore dimensione max file (50MB default)
- Aggiunto controllo estensioni (whitelist/blacklist)
- Aggiunto validatore MIME type reale
- Integrato ClamAV per scansione antivirus
- Path configurabili via .env
- Comando cleanup_tmp per pulizia automatica
- Test suite completa

Risolve: #XXX"

# Push (se su Git remoto)
git push origin feature/storage-security-improvements
```

### Step 8.2: Update Documentazione
```bash
# Verifica che tutti i doc siano stati creati
ls -l docs/MIGLIORAMENTI_FILE_STORAGE.md
ls -l docs/INSTALLAZIONE_MIGLIORAMENTI_STORAGE.md
ls -l docs/RIEPILOGO_MIGLIORAMENTI_STORAGE.md
ls -l docs/PIANO_IMPLEMENTAZIONE.md
```

**✅ Checkpoint 8**: Tutto documentato e committato

---

## ✅ CHECKLIST FINALE

Verifica completamento:

- [ ] Backup database fatto
- [ ] Backup codice fatto
- [ ] ClamAV installato e funzionante
- [ ] Dipendenze Python installate
- [ ] File .env configurato
- [ ] settings.py aggiornato
- [ ] documenti/models.py aggiornato
- [ ] archivio_fisico/models.py aggiornato
- [ ] Test upload funzionante
- [ ] Test dimensione funzionante
- [ ] Test estensione funzionante
- [ ] Test antivirus funzionante
- [ ] Comando cleanup_tmp funzionante
- [ ] Cron job configurato
- [ ] Monitoraggio attivo
- [ ] Modifiche committate
- [ ] Documentazione completa

---

## 🎉 COMPLETAMENTO

**CONGRATULAZIONI!** Hai completato con successo l'implementazione dei miglioramenti di sicurezza file storage.

### Prossimi Passi

1. **Monitorare per 1 settimana**:
   - Verificare log giornalmente
   - Controllare spazio disco tmp/
   - Verificare che pulizia automatica funzioni

2. **Ottimizzazioni opzionali**:
   - Implementare scansione asincrona con Celery per file grandi
   - Aggiungere dashboard monitoring
   - Configurare alert email per virus rilevati

3. **Review e Merge**:
   - Fare code review con team
   - Testare in ambiente staging
   - Merge su main branch

### Supporto

In caso di problemi:
- Consultare `docs/INSTALLAZIONE_MIGLIORAMENTI_STORAGE.md` sezione Troubleshooting
- Verificare log: `logs/protocollazione.log`
- Testare validator isolatamente: `python manage.py shell`

---

**Tempo totale stimato**: 3-4 ore
**Tempo effettivo**: _____ ore

**Note implementazione**:
_________________
_________________
_________________

**Data completamento**: _______________
**Implementato da**: _______________
