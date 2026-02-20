# RIEPILOGO: Miglioramenti File Storage e Sicurezza
**Data**: 17 Novembre 2025

---

## 📁 File Creati/Modificati

### ✅ File Nuovi Creati

1. **`documenti/validators.py`** (242 righe)
   - Validatori per dimensione file
   - Validatori estensioni (whitelist/blacklist)
   - Validatore MIME type (python-magic)
   - Validatore antivirus (ClamAV)
   - Validatore combinato `validate_file_content()`

2. **`documenti/management/commands/cleanup_tmp.py`** (157 righe)
   - Comando Django per pulizia file temporanei
   - Supporto dry-run e verbose
   - Rimozione automatica directory vuote
   - Statistiche dettagliate

3. **`.env.production.example`**
   - Template configurazione produzione
   - Valori sicuri di default
   - Documentazione inline

4. **`requirements-security.txt`**
   - Nuove dipendenze: python-magic, clamd
   - Opzionali: celery, redis

5. **`docs/MIGLIORAMENTI_FILE_STORAGE.md`** (690 righe)
   - Analisi completa problemi
   - Soluzioni dettagliate con codice
   - Test e validazione
   - Conformità GDPR

6. **`docs/INSTALLAZIONE_MIGLIORAMENTI_STORAGE.md`** (510 righe)
   - Guida passo-passo installazione
   - Troubleshooting
   - Test di validazione
   - Monitoraggio

7. **`docs/SETTINGS_MODIFICATIONS.txt`**
   - Modifiche specifiche da applicare
   - Codice pronto da copiare

---

## 🔧 Modifiche da Applicare

### File da Modificare Manualmente

#### 1. `mygest/settings.py`
**Azioni**:
- ✅ Rimuovere path hardcoded (linea ~190-202)
- ✅ Aggiungere nuove configurazioni storage (vedere `docs/SETTINGS_MODIFICATIONS.txt`)
- ✅ Aggiungere configurazioni upload limits
- ✅ Aggiungere configurazioni antivirus

**Linee da sostituire**:
```python
# VECCHIO (RIMUOVERE)
ARCHIVIO_BASE_PATH = os.getenv("ARCHIVIO_BASE_PATH", "/mnt/archivio")
IMPORTAZIONI_SOURCE_DIRS = [
    "/home/sandro/documenti",
    "/mnt/archivio/importazioni",
]
```

#### 2. `documenti/models.py`
**Azioni**:
- ✅ Aggiungere import: `from .validators import validate_file_content`
- ✅ Modificare campo `file` aggiungendo validator (linea ~190)
- ✅ Aggiornare funzione `documento_upload_to()` per usare `UPLOAD_TEMP_DIR` (linea ~61)

**Codice da aggiungere**:
```python
# Linea ~4 (import)
from .validators import validate_file_content

# Linea ~190 (campo file)
file = models.FileField(
    storage=nas_storage, 
    upload_to=documento_upload_to, 
    blank=True, 
    null=True, 
    max_length=500,
    validators=[validate_file_content],  # <-- NUOVO
)

# Linea ~85 (dentro documento_upload_to)
temp_dir = getattr(settings, "UPLOAD_TEMP_DIR", "tmp")  # <-- NUOVO
return f"{temp_dir}/{year}/{cli_code}/{filename}"
```

#### 3. `archivio_fisico/models.py`
**Azioni**:
- ✅ Aggiungere import: `from documenti.validators import validate_file_content`
- ✅ Modificare campo `verbale_scan` aggiungendo validator (linea ~40)

**Codice da aggiungere**:
```python
# Linea ~11 (import)
from documenti.validators import validate_file_content

# Linea ~43 (campo verbale_scan)
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

#### 4. `.env` (creare se non esiste)
**Azioni**:
- ✅ Creare file `.env` dalla copia di `.env.example`
- ✅ Configurare valori personalizzati

---

## 📦 Installazione Dipendenze

### Sistema (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install -y clamav clamav-daemon libmagic1 python3-magic
sudo systemctl enable clamav-daemon
sudo systemctl start clamav-daemon
sudo freshclam
```

### Python
```bash
source venv/bin/activate
pip install -r requirements-security.txt
```

---

## ✅ Checklist Implementazione

### Fase 1: Setup Iniziale
- [ ] Backup database
- [ ] Backup codice
- [ ] Installare ClamAV
- [ ] Installare dipendenze Python
- [ ] Creare file `.env`

### Fase 2: Modifiche Codice
- [ ] Aggiornare `settings.py`
- [ ] Aggiornare `documenti/models.py`
- [ ] Aggiornare `archivio_fisico/models.py`
- [ ] Verificare imports senza errori

### Fase 3: Test
- [ ] Test dimensione file (rifiuto file troppo grandi)
- [ ] Test estensioni proibite (rifiuto .exe, .bat, etc.)
- [ ] Test antivirus con EICAR
- [ ] Test upload normale funzionante
- [ ] Test comando cleanup_tmp

### Fase 4: Configurazione Produzione
- [ ] Configurare cron job per cleanup
- [ ] Configurare monitoraggio spazio disco
- [ ] Configurare alert virus rilevati
- [ ] Verificare log funzionanti

---

## 🎯 Problemi Risolti

### ✅ 1. Directory tmp/ non pulita automaticamente
**Soluzione**: Comando `cleanup_tmp` + cron job
```bash
# Cron: pulizia notturna
0 2 * * * cd /path/to/mygest && /path/to/venv/bin/python manage.py cleanup_tmp --days=7
```

### ✅ 2. Path hardcoded non portabili
**Soluzione**: Variabili ambiente in `.env`
```bash
ARCHIVIO_BASE_PATH=/mnt/archivio
IMPORTAZIONI_SOURCE_DIRS=/home/user/docs:/mnt/archivio/importazioni
```

### ✅ 3. Nessuna validazione dimensione file
**Soluzione**: Settings Django + validators
```python
FILE_UPLOAD_MAX_MEMORY_SIZE=52428800  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE=104857600  # 100 MB
validators=[validate_file_content]
```

### ✅ 4. Nessun controllo antivirus
**Soluzione**: Integrazione ClamAV
```python
ANTIVIRUS_ENABLED=true
# Scansione automatica con validate_antivirus()
```

---

## 📊 Test di Validazione

### Test Dimensione (dovrebbe FALLIRE)
```bash
dd if=/dev/urandom of=/tmp/test_60mb.pdf bs=1M count=60
# Upload → Errore: "file troppo grande"
```

### Test Estensione Proibita (dovrebbe FALLIRE)
```bash
echo "test" > /tmp/malware.exe
# Upload → Errore: "estensione non consentita"
```

### Test Antivirus (dovrebbe FALLIRE)
```bash
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > /tmp/eicar.txt
# Upload → Errore: "virus rilevato"
```

### Test Upload Normale (dovrebbe PASSARE)
```bash
# Upload PDF legittimo < 50MB
# → Successo, file salvato in archivio
```

### Test Pulizia tmp/
```bash
# Crea file vecchio
touch -d "10 days ago" media/tmp/2024/TEST/old.pdf

# Esegui pulizia
python manage.py cleanup_tmp --days=7

# Verifica eliminazione
ls media/tmp/2024/TEST/  # → vuoto
```

---

## 🚀 Quick Start

### Per iniziare subito (minimo indispensabile):

```bash
# 1. Installazione
sudo apt-get install clamav clamav-daemon libmagic1
pip install python-magic clamd

# 2. Configurazione
cp .env.example .env
nano .env  # Configura ARCHIVIO_BASE_PATH

# 3. Avvia ClamAV
sudo systemctl start clamav-daemon

# 4. Test
python manage.py shell
>>> from documenti.validators import get_clamd_client
>>> cd = get_clamd_client()
>>> print(cd.ping())  # Deve stampare 'PONG'
>>> exit()

# 5. Applica modifiche codice
# Seguire docs/SETTINGS_MODIFICATIONS.txt

# 6. Test upload
python manage.py runserver
# Prova upload dalla UI

# 7. Configura pulizia automatica
crontab -e
# Aggiungi: 0 2 * * * cd /path/to/mygest && /path/to/venv/bin/python manage.py cleanup_tmp --days=7
```

---

## 📈 Benefici Implementazione

### Sicurezza
- ✅ Protezione da malware (antivirus)
- ✅ Protezione da DoS (limiti dimensione)
- ✅ Prevenzione upload file pericolosi (blacklist estensioni)
- ✅ Validazione MIME reale (anti-spoofing)

### Manutenibilità
- ✅ Path configurabili via .env (portabilità)
- ✅ Pulizia automatica tmp/ (gestione spazio)
- ✅ Log dettagliati (debugging)
- ✅ Monitoring integrato

### Conformità
- ✅ GDPR Art. 32 - Sicurezza trattamento
- ✅ GDPR Art. 25 - Privacy by design
- ✅ GDPR Art. 5 - Limitazione conservazione

---

## 📞 Supporto

**Documentazione completa**:
- `docs/MIGLIORAMENTI_FILE_STORAGE.md` - Analisi dettagliata
- `docs/INSTALLAZIONE_MIGLIORAMENTI_STORAGE.md` - Guida installazione
- `docs/SETTINGS_MODIFICATIONS.txt` - Modifiche codice

**Test**:
```bash
# Test validatori
python manage.py shell -c "from documenti.validators import validate_file_content; print('OK')"

# Test ClamAV
python manage.py shell -c "from documenti.validators import get_clamd_client; print(get_clamd_client().ping())"

# Test cleanup
python manage.py cleanup_tmp --dry-run --verbose
```

**Log**:
```bash
# Log upload e validazioni
tail -f logs/protocollazione.log

# Log ClamAV
sudo tail -f /var/log/clamav/clamav.log
```

---

## ⏱️ Timeline Implementazione

- **Setup iniziale**: 30 minuti
- **Modifiche codice**: 1 ora
- **Test**: 1 ora
- **Configurazione produzione**: 30 minuti
- **TOTALE**: ~3 ore

---

## 🎉 Stato Attuale

✅ **Analisi completata**
✅ **Soluzioni progettate**
✅ **Codice implementato**
✅ **Documentazione completa**
✅ **Guide installazione pronte**

**Pronto per implementazione!**

---

**Versione**: 1.0
**Data**: 17 Novembre 2025
**Autore**: GitHub Copilot
