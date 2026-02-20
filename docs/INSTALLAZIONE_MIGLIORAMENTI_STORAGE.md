# Guida Installazione Miglioramenti File Storage e Sicurezza

## Data: 17 Novembre 2025

Questa guida illustra i passaggi per implementare i miglioramenti alla gestione file e storage di MyGest.

---

## 📋 Prerequisiti

- Django 4.2+
- Python 3.10+
- PostgreSQL
- Accesso root/sudo al server (per installazione ClamAV)

---

## 🚀 Installazione

### 1. Backup Preventivo

```bash
# Backup database
pg_dump mygest > backup_mygest_$(date +%Y%m%d).sql

# Backup codice
cd /path/to/mygest
tar -czf ../mygest_backup_$(date +%Y%m%d).tar.gz .
```

### 2. Installazione Dipendenze Python

```bash
# Attiva virtual environment
source venv/bin/activate

# Installa nuove dipendenze
pip install -r requirements-security.txt
```

### 3. Installazione ClamAV (Debian/Ubuntu)

```bash
# Installa ClamAV e daemon
sudo apt-get update
sudo apt-get install -y clamav clamav-daemon libmagic1 python3-magic

# Ferma il servizio per aggiornare le definizioni
sudo systemctl stop clamav-daemon

# Aggiorna definizioni virus
sudo freshclam

# Riavvia il servizio
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon

# Verifica che sia in esecuzione
sudo systemctl status clamav-daemon
```

**Verifica socket ClamAV:**
```bash
ls -la /var/run/clamav/clamd.ctl
# Dovrebbe esistere e essere un socket Unix
```

### 4. Configurazione File .env

```bash
# Copia il template
cp .env.example .env

# Modifica .env con i tuoi valori
nano .env
```

**Configurazione minima richiesta:**

```bash
# Path archivio
ARCHIVIO_BASE_PATH=/mnt/archivio
UPLOAD_TEMP_DIR=tmp

# Dimensioni upload
FILE_UPLOAD_MAX_MEMORY_SIZE=52428800  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE=104857600  # 100 MB

# Antivirus
ANTIVIRUS_ENABLED=true
ANTIVIRUS_REQUIRED=false  # false in sviluppo, true in produzione
CLAMAV_SOCKET=/var/run/clamav/clamd.ctl

# Importazioni
IMPORTAZIONI_SOURCE_DIRS=/home/sandro/documenti:/mnt/archivio/importazioni
```

### 5. Modifica settings.py

Aprire `mygest/settings.py` e applicare le modifiche descritte in `docs/SETTINGS_MODIFICATIONS.txt`:

```bash
# Visualizza le modifiche da fare
cat docs/SETTINGS_MODIFICATIONS.txt
```

**Sostituire la sezione:**
```python
# VECCHIO (circa linea 190-202)
ARCHIVIO_BASE_PATH = os.getenv("ARCHIVIO_BASE_PATH", "/mnt/archivio")
IMPORTAZIONI_SOURCE_DIRS = [
    "/home/sandro/documenti",
    "/mnt/archivio/importazioni",
]
```

**Con il NUOVO codice da** `docs/SETTINGS_MODIFICATIONS.txt` **(sezioni complete)**

### 6. Aggiornamento Models

**File `documenti/models.py`:**

1. Aggiungere import validator:
```python
from .validators import validate_file_content
```

2. Modificare campo `file` (circa linea 190):
```python
file = models.FileField(
    storage=nas_storage, 
    upload_to=documento_upload_to, 
    blank=True, 
    null=True, 
    max_length=500,
    validators=[validate_file_content],  # <-- AGGIUNGERE
)
```

3. Aggiornare funzione `documento_upload_to` (circa linea 61):
```python
def documento_upload_to(instance, filename):
    """
    Percorso provvisorio di upload (sotto MEDIA_ROOT/UPLOAD_TEMP_DIR).
    Il file verrà poi spostato nel NAS dentro 'percorso_archivio' in Documento.save().
    Struttura: {UPLOAD_TEMP_DIR}/<anno>/<cliente_code>/<filename>
    """
    from django.conf import settings
    
    # Anno
    d = getattr(instance, "data_documento", None) or timezone.now().date()
    year = d.year

    # Cliente (anche via fascicolo)
    cli = getattr(instance, "cliente", None)
    if cli is None and getattr(instance, "fascicolo_id", None):
        cli = instance.fascicolo.cliente

    # CLI uniforme (6+2). Se manca il cliente, usa fallback "VARIE"
    if cli:
        anag = getattr(cli, "anagrafica", cli)
        cli_code = get_or_generate_cli(anag)
    else:
        cli_code = "VARIE"
    
    # USA SETTING INVECE DI "tmp" HARDCODED
    temp_dir = getattr(settings, "UPLOAD_TEMP_DIR", "tmp")
    return f"{temp_dir}/{year}/{cli_code}/{filename}"
```

**File `archivio_fisico/models.py`:**

1. Aggiungere import validator (circa linea 11):
```python
from documenti.validators import validate_file_content
```

2. Modificare campo `verbale_scan` (circa linea 40):
```python
verbale_scan = models.FileField(
    storage=nas_storage,
    upload_to="archivio_fisico/operazioni",
    null=True,
    blank=True,
    max_length=500,
    validators=[
        FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "tif", "tiff"]),
        validate_file_content,  # <-- AGGIUNGERE
    ],
    help_text="Facoltativo: carica la scansione del verbale firmato.",
)
```

### 7. Test Installazione

```bash
# Test import moduli
python manage.py shell
```

```python
# In shell Django
from documenti.validators import validate_file_content
from documenti.validators import get_clamd_client

# Test connessione ClamAV
cd = get_clamd_client()
print(cd.ping())  # Dovrebbe stampare 'PONG'

# Test validatori
from django.core.files.uploadedfile import SimpleUploadedFile
file = SimpleUploadedFile("test.pdf", b"test content", content_type="application/pdf")
validate_file_content(file)  # Non dovrebbe sollevare errori

exit()
```

### 8. Creazione Directory

```bash
# Crea directory necessarie
mkdir -p media/tmp
mkdir -p /mnt/archivio  # Se non esiste

# Imposta permessi
chmod 755 media/tmp
```

### 9. Test Upload File

1. Avvia il server di sviluppo:
```bash
python manage.py runserver
```

2. Prova a caricare un documento dalla UI

3. Verifica i log:
```bash
tail -f logs/protocollazione.log
```

### 10. Configurazione Pulizia Automatica tmp/

**Metodo A: Cron Job (RACCOMANDATO)**

```bash
# Apri crontab
crontab -e

# Aggiungi riga per pulizia notturna alle 2:00
0 2 * * * cd /path/to/mygest && /path/to/venv/bin/python manage.py cleanup_tmp --days=7
```

**Test manuale:**
```bash
# Dry-run per vedere cosa verrebbe eliminato
python manage.py cleanup_tmp --days=7 --dry-run --verbose

# Esecuzione reale
python manage.py cleanup_tmp --days=7
```

---

## ✅ Checklist Post-Installazione

- [ ] ClamAV installato e in esecuzione
- [ ] File `.env` configurato
- [ ] `settings.py` aggiornato con nuove configurazioni
- [ ] Models aggiornati con validators
- [ ] Dipendenze Python installate
- [ ] Test upload funzionante
- [ ] Cron job configurato per cleanup tmp/
- [ ] Log funzionanti

---

## 🧪 Test di Validazione

### Test 1: Dimensione File

```bash
# Crea file di 60MB (dovrebbe essere rifiutato se limit=50MB)
dd if=/dev/urandom of=/tmp/test_60mb.pdf bs=1M count=60

# Tenta upload - dovrebbe fallire con errore "file troppo grande"
```

### Test 2: Estensione Proibita

```bash
# Crea file .exe
echo "test" > /tmp/malware.exe

# Tenta upload - dovrebbe fallire con errore "estensione non consentita"
```

### Test 3: Antivirus (EICAR Test)

```bash
# Crea file test EICAR (test standard antivirus, NON è un virus reale)
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > /tmp/eicar.txt

# Tenta upload - dovrebbe essere bloccato da ClamAV
```

### Test 4: MIME Spoofing

```bash
# Rinomina un file di testo in .pdf
echo "questo non è un PDF" > /tmp/fake.pdf

# Tenta upload - se ALLOWED_MIME_TYPES configurato, dovrebbe fallire
```

### Test 5: Pulizia tmp/

```bash
# Crea file vecchi in tmp per test
mkdir -p media/tmp/2024/TEST
touch -d "10 days ago" media/tmp/2024/TEST/old_file.pdf

# Esegui cleanup
python manage.py cleanup_tmp --days=7 --verbose

# Verifica eliminazione
ls media/tmp/2024/TEST/  # Dovrebbe essere vuoto o inesistente
```

---

## 🔍 Troubleshooting

### Problema: ClamAV non si connette

**Sintomo**: `Impossibile connettersi a ClamAV`

**Soluzioni**:
```bash
# Verifica che il daemon sia attivo
sudo systemctl status clamav-daemon

# Verifica socket
ls -la /var/run/clamav/clamd.ctl

# Verifica permessi
sudo chmod 666 /var/run/clamav/clamd.ctl  # Temporaneo per test

# Log ClamAV
sudo tail -f /var/log/clamav/clamav.log
```

### Problema: python-magic non trova libmagic

**Sintomo**: `ImportError: failed to find libmagic`

**Soluzione**:
```bash
# Debian/Ubuntu
sudo apt-get install libmagic1 python3-magic

# Reinstalla python-magic
pip uninstall python-magic
pip install python-magic
```

### Problema: Upload fallisce con "validation error"

**Debug**:
```bash
# Abilita log debug
# In settings.py, aggiungi:
LOGGING['loggers']['documenti'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
}

# Guarda i log
tail -f logs/protocollazione.log
```

### Problema: tmp/ non viene pulita

**Verifica cron**:
```bash
# Controlla se cron è attivo
sudo systemctl status cron

# Log cron
grep cleanup_tmp /var/log/syslog

# Test manuale
python manage.py cleanup_tmp --days=1 --verbose
```

---

## 📊 Monitoraggio

### Script monitoraggio spazio tmp/

```bash
#!/bin/bash
# Salvare come: /usr/local/bin/check_tmp_size.sh

TMP_DIR="/path/to/mygest/media/tmp"
MAX_SIZE_MB=1024  # 1 GB

if [ ! -d "$TMP_DIR" ]; then
    exit 0
fi

SIZE_MB=$(du -sm "$TMP_DIR" | cut -f1)

if [ $SIZE_MB -gt $MAX_SIZE_MB ]; then
    echo "WARNING: tmp/ size is ${SIZE_MB}MB (max: ${MAX_SIZE_MB}MB)"
    # Opzionale: invia email admin
    # mail -s "MyGest: tmp/ space warning" admin@example.com <<< "tmp/ size: ${SIZE_MB}MB"
fi
```

**Aggiungi a cron:**
```bash
# Controlla ogni 6 ore
0 */6 * * * /usr/local/bin/check_tmp_size.sh
```

### Metriche da monitorare

1. **Spazio disco tmp/**:
   ```bash
   du -sh media/tmp/
   ```

2. **File upload giornalieri**:
   ```bash
   grep "File.*scansionato" logs/protocollazione.log | grep "$(date +%Y-%m-%d)" | wc -l
   ```

3. **Virus rilevati**:
   ```bash
   grep "Virus rilevato" logs/protocollazione.log
   ```

4. **Upload rifiutati per dimensione**:
   ```bash
   grep "file_too_large" logs/django.log | wc -l
   ```

---

## 🔐 Sicurezza Produzione

### Configurazione .env produzione

```bash
# .env per produzione
DEBUG=false
ANTIVIRUS_ENABLED=true
ANTIVIRUS_REQUIRED=true  # Blocca se ClamAV down

# Limiti più restrittivi
FILE_UPLOAD_MAX_MEMORY_SIZE=20971520  # 20 MB
DATA_UPLOAD_MAX_MEMORY_SIZE=41943040  # 40 MB
```

### Hardening

1. **Limita permessi file**:
```bash
chmod 750 media/tmp/
chown www-data:www-data media/tmp/
```

2. **Firewall**:
```bash
# Se ClamAV su server remoto, permetti solo connessioni locali
sudo ufw allow from 127.0.0.1 to any port 3310
```

3. **SELinux/AppArmor**:
```bash
# Ubuntu AppArmor per ClamAV
sudo aa-enforce /usr/sbin/clamd
```

---

## 📝 Note Aggiuntive

### Prestazioni

- La validazione MIME aggiunge ~50ms per file
- La scansione antivirus aggiunge ~100-500ms per file (dipende dalla dimensione)
- Per file molto grandi, considerare scansione asincrona con Celery

### Compatibilità

- Testato su Django 4.2+
- Testato su Ubuntu 22.04 LTS
- ClamAV 0.103+

### Alternative ClamAV

Se ClamAV non disponibile/pratico:

1. **VirusTotal API**: servizio cloud per scansione
2. **Windows Defender API**: se su Windows Server
3. **Validazione solo MIME/estensioni**: meno sicuro ma senza dipendenze

---

## 📚 Riferimenti

- [Documentazione ClamAV](https://www.clamav.net/documents)
- [Django File Uploads](https://docs.djangoproject.com/en/4.2/topics/http/file-uploads/)
- [python-magic](https://github.com/ahupp/python-magic)
- [clamd Python](https://github.com/graingert/python-clamd)

---

## 🆘 Supporto

In caso di problemi:

1. Controllare i log: `logs/protocollazione.log`
2. Verificare configurazione: `.env` e `settings.py`
3. Test isolati con `python manage.py shell`
4. Consultare `docs/MIGLIORAMENTI_FILE_STORAGE.md` per dettagli

---

**Data ultima revisione**: 17 Novembre 2025
**Versione guida**: 1.0
