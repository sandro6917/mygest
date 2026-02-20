# Guida: Path Configurabili e Portabili (Soluzione 2)

## ⚠️ PROBLEMA RISOLTO

**Vincolo produzione**: I file `.env` e `settings.py` NON vengono trasferiti durante il deploy.

**Soluzione implementata**: Pattern `settings_local.py` con script di setup automatico.

---

## 📋 COME FUNZIONA

### 1. **Struttura File**

```
mygest/
├── settings.py              # Configurazione base (su git, viene deployata)
├── settings_local.py        # Config ambiente-specifico (NON su git)
└── settings_local.py.example  # Template (su git, viene deployata)
```

### 2. **Flusso di Caricamento**

```python
# settings.py (alla fine)
try:
    from .settings_local import *
    print("✓ Settings locali caricati")
except ImportError:
    print("⚠ settings_local.py non trovato - usando default")
    pass
```

**Se settings_local.py ESISTE**: i valori al suo interno sovrascrivono quelli in settings.py
**Se NON esiste**: usa i valori di default in settings.py (sviluppo locale)

---

## 🚀 SETUP AMBIENTE

### **A) Sviluppo Locale (WSL/Linux)**

```bash
# 1. Copia il template
cp mygest/settings_local.py.example mygest/settings_local.py

# 2. Modifica con i tuoi valori locali
nano mygest/settings_local.py

# Esempio sviluppo:
ENVIRONMENT = 'development'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ARCHIVIO_BASE_PATH = "/mnt/archivio"
IMPORTAZIONI_SOURCE_DIRS = [
    "/home/sandro/documenti",
    "/mnt/archivio/importazioni",
]
```

### **B) Produzione (VPS)**

**DOPO IL DEPLOY**, eseguire sul server:

```bash
# 1. Vai nella directory del progetto
cd /srv/mygest  # o dove hai deployato

# 2. Esegui lo script automatico
./scripts/setup_production.sh
```

Lo script chiederà **interattivamente**:
- Domini consentiti (ALLOWED_HOSTS)
- Secret key (può generarla automaticamente)
- Credenziali database
- Path archivio e importazioni
- Configurazione antivirus

E genererà automaticamente `mygest/settings_local.py` con:
- DEBUG = False
- HTTPS security headers
- Password database sicura
- Path corretti per produzione

---

## 📂 VALORI CONFIGURABILI

### **Sicurezza**
- `DEBUG`: True/False
- `ALLOWED_HOSTS`: lista domini
- `SECRET_KEY`: chiave segreta Django

### **Database**
- `DATABASES`: credenziali PostgreSQL complete

### **File Storage**
```python
ARCHIVIO_BASE_PATH = "/srv/mygest/archivio"  # Path base archivio
UPLOAD_TEMP_DIR = "tmp"                       # Directory temp upload
IMPORTAZIONI_SOURCE_DIRS = [...]              # Path sorgenti importazione
MEDIA_ROOT = ARCHIVIO_BASE_PATH
MEDIA_URL = '/archivio/'
```

### **Limiti Upload**
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800      # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600     # 100 MB
ALLOWED_FILE_EXTENSIONS = ['pdf', 'docx', ...]
FORBIDDEN_FILE_EXTENSIONS = ['exe', 'bat', ...]
```

### **Antivirus**
```python
ANTIVIRUS_ENABLED = True/False
ANTIVIRUS_REQUIRED = True/False  # Blocca se non disponibile
CLAMAV_SOCKET = '/var/run/clamav/clamd.ctl'
```

---

## 🔐 SICUREZZA

### File NON su Git
```gitignore
# .gitignore
mygest/settings_local.py    # ✓ Aggiunto
.env
.env.local
.env.production
secrets/
```

### Permessi File (Produzione)
```bash
chmod 600 mygest/settings_local.py  # Solo proprietario legge/scrive
```

### Headers Sicurezza (Automatici in Produzione)
Lo script imposta automaticamente se `DEBUG=False`:
- HTTPS redirect
- Secure cookies
- HSTS headers
- XSS protection
- Content type nosniff

---

## 🎯 VANTAGGI vs .env

| Aspetto | .env | settings_local.py |
|---------|------|-------------------|
| Deploy in produzione | ❌ NON trasferito | ✅ Creato sul server |
| Configurazione complessa | ❌ Solo string | ✅ Codice Python |
| Valori di default | ❌ Servono tutti | ✅ Fallback in settings.py |
| Tipizzazione | ❌ Tutto stringa | ✅ Tipi nativi Python |
| Setup automatico | ❌ Manuale | ✅ Script interattivo |
| Sicurezza | ⚠️ Esposta se deployata | ✅ Creata localmente |

---

## 📝 WORKFLOW DEPLOY

### 1. **Commit & Push** (sviluppo)
```bash
git add .
git commit -m "Update codice"
git push origin main
```

**Attenzione**: `settings_local.py` NON viene pushata (è in .gitignore)

### 2. **Pull su Produzione**
```bash
# Sul server
cd /srv/mygest
git pull origin main
```

**Risultato**: `settings_local.py` del server NON viene toccata (non era su git)

### 3. **Prima Volta in Produzione**
```bash
# Solo la prima volta o se cambi configurazione
./scripts/setup_production.sh
```

### 4. **Verifica e Restart**
```bash
python manage.py check --deploy
sudo systemctl restart gunicorn
```

---

## 🧪 TEST

### Verifica Caricamento Settings
```bash
python manage.py shell
```

```python
from django.conf import settings

# Verifica ambiente
print(settings.ENVIRONMENT)  # 'development' o 'production'

# Verifica path
print(settings.ARCHIVIO_BASE_PATH)  # Dovrebbe essere quello corretto

# Verifica debug
print(settings.DEBUG)  # False in produzione!

# Verifica hosts
print(settings.ALLOWED_HOSTS)
```

### Test Antivirus (se abilitato)
```bash
python manage.py shell
```

```python
from documenti.validators import validate_antivirus

# Test file sicuro
with open('/tmp/test.txt', 'w') as f:
    f.write('test')

from django.core.files import File
with open('/tmp/test.txt', 'rb') as f:
    validate_antivirus(File(f, name='test.txt'))

print("✓ Antivirus funzionante")
```

---

## 🛠️ TROUBLESHOOTING

### ❌ "settings_local.py non trovato"
```bash
# Verifica che esista
ls -la mygest/settings_local.py

# Se non esiste:
cp mygest/settings_local.py.example mygest/settings_local.py
nano mygest/settings_local.py
```

### ❌ "Permission denied" su archivio
```bash
# Verifica proprietario directory
ls -ld /srv/mygest/archivio

# Correggi (sostituisci www-data con tuo utente web)
sudo chown -R www-data:www-data /srv/mygest/archivio
sudo chmod 755 /srv/mygest/archivio
```

### ❌ Errori Import dopo Aggiornamento
```python
# Potrebbe servire ricompilare bytecode
python manage.py shell
import py_compile
py_compile.compile('mygest/settings_local.py')
```

### ❌ Debug in Produzione
```bash
# TEMPORANEAMENTE, per vedere errori:
nano mygest/settings_local.py
# Cambia: DEBUG = True

# Riavvia
sudo systemctl restart gunicorn

# RICORDA DI RIMETTERE DEBUG = False APPENA FINITO!
```

---

## 📋 CHECKLIST POST-DEPLOY

**Produzione:**
- [ ] `settings_local.py` creato con script
- [ ] DEBUG = False
- [ ] ALLOWED_HOSTS configurato correttamente
- [ ] SECRET_KEY unica e sicura (≠ da sviluppo)
- [ ] Database password sicura
- [ ] Path archivio esistente e scrivibile
- [ ] Permessi file 600 su settings_local.py
- [ ] HTTPS headers abilitati
- [ ] Antivirus configurato (se richiesto)
- [ ] Cron cleanup tmp configurato
- [ ] Logs directory esistente e scrivibile

**Test funzionali:**
- [ ] `python manage.py check --deploy` senza errori
- [ ] Upload file funzionante
- [ ] Import documenti funzionante
- [ ] Cleanup tmp schedulato e funzionante

---

## 📚 FILE CREATI

```
mygest/settings_local.py.example    # Template configurazione
scripts/setup_production.sh          # Script setup automatico
docs/GUIDA_SETTINGS_LOCAL.md        # Questa guida
```

**Modificati:**
```
mygest/settings.py                   # +import settings_local alla fine
.gitignore                           # +mygest/settings_local.py
```

---

## 🔗 RIFERIMENTI

- **Django Settings**: https://docs.djangoproject.com/en/4.2/topics/settings/
- **Security**: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
- **File Uploads**: https://docs.djangoproject.com/en/4.2/topics/http/file-uploads/

---

**Autore**: Script generato per risolvere problema deploy produzione  
**Data**: 2025  
**Versione**: 1.0
