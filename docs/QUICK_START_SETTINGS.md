# Quick Start: Settings Locali - MyGest

## 🎯 TL;DR

**Problema**: `.env` e `settings.py` NON vanno in produzione  
**Soluzione**: Usa `settings_local.py` creato sul server dopo il deploy

---

## 💻 SVILUPPO (WSL/Locale)

```bash
# 1. Prima volta - crea il tuo settings_local.py
cp mygest/settings_local.py.example mygest/settings_local.py

# 2. Personalizza (opzionale)
nano mygest/settings_local.py

# 3. Verifica caricamento
python manage.py check
# Output: ✓ Settings locali caricati da settings_local.py

# 4. Lavora normalmente
python manage.py runserver
```

### Valori Default Sviluppo
```python
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
ARCHIVIO_BASE_PATH = "/mnt/archivio"
IMPORTAZIONI_SOURCE_DIRS = [
    "/home/sandro/documenti",
    "/mnt/archivio/importazioni",
]
```

---

## 🚀 PRODUZIONE (VPS)

### Prima Volta
```bash
# Sul server dopo git pull
cd /srv/mygest
./scripts/setup_production.sh
```

Lo script chiede:
- Domini web (ALLOWED_HOSTS)
- Credenziali database
- Path archivio produzione
- Configurazione antivirus

E crea automaticamente `mygest/settings_local.py` con valori sicuri.

### Aggiornamenti Normali
```bash
# Sul server
cd /srv/mygest
git pull origin main        # settings_local.py NON viene toccato
python manage.py migrate    # Se ci sono migrazioni
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

**settings_local.py resta intatto** perché è in `.gitignore`!

---

## 🔄 WORKFLOW COMPLETO

### Sviluppo → Git → Produzione

```bash
# === SU LOCALE (WSL) ===
nano documenti/models.py          # Modifica codice
python manage.py makemigrations
python manage.py migrate
git add .
git commit -m "Nuova feature"
git push origin main

# === SU PRODUZIONE (VPS) ===
ssh user@server
cd /srv/mygest
git pull origin main              # ← settings_local.py NON cambia!
python manage.py migrate
sudo systemctl restart gunicorn
```

---

## ✅ COSA CAMBIA vs PRIMA

### ❌ Prima (PROBLEMA)
```python
# settings.py (veniva deployato)
ARCHIVIO_BASE_PATH = "/mnt/archivio"  # ← HARDCODED WSL!
# In produzione path errato → crash
```

### ✅ Ora (RISOLTO)
```python
# settings.py (deployato)
ARCHIVIO_BASE_PATH = "/mnt/archivio"  # Default sviluppo

# settings_local.py (locale, NON deployato)
ARCHIVIO_BASE_PATH = "/srv/mygest/archivio"  # ← Produzione
# Sovrascrive il default quando esiste
```

---

## 🎨 PERSONALIZZAZIONI COMUNI

### Cambiare Path Archivio (Sviluppo)
```python
# mygest/settings_local.py
ARCHIVIO_BASE_PATH = "/home/sandro/archivio_test"
```

### Testare con Dati Reali
```python
# mygest/settings_local.py
IMPORTAZIONI_SOURCE_DIRS = [
    "/mnt/dati_clienti/2024",
    "/home/sandro/downloads/fatture",
]
```

### Disabilitare Antivirus (Sviluppo)
```python
# mygest/settings_local.py
ANTIVIRUS_ENABLED = False
ANTIVIRUS_REQUIRED = False
```

### Aumentare Limite Upload (Test)
```python
# mygest/settings_local.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB invece di 50
```

---

## 🐛 TROUBLESHOOTING RAPIDO

### "settings_local.py non trovato"
```bash
cp mygest/settings_local.py.example mygest/settings_local.py
```

### "Permission denied" su archivio
```bash
sudo chown -R $USER:$USER /mnt/archivio
```

### Valori non applicati
```bash
# Verifica caricamento
python manage.py shell
>>> from django.conf import settings
>>> print(settings.ARCHIVIO_BASE_PATH)
```

### Ripristinare Default
```bash
rm mygest/settings_local.py
# Ora usa valori di default in settings.py
```

---

## 📋 CHECKLIST DEPLOYMENT

**Prima volta produzione:**
- [ ] `git pull` completato
- [ ] `./scripts/setup_production.sh` eseguito
- [ ] Verificato `DEBUG=False` in settings_local.py
- [ ] Testato `python manage.py check --deploy`
- [ ] Riavviato gunicorn/uwsgi

**Aggiornamenti successivi:**
- [ ] `git pull`
- [ ] `python manage.py migrate` (se necessario)
- [ ] `python manage.py collectstatic`
- [ ] Restart server
- [ ] ✅ settings_local.py automaticamente preservato!

---

## 📚 Documentazione Completa

- **Guida dettagliata**: `docs/GUIDA_SETTINGS_LOCAL.md`
- **Script setup**: `scripts/setup_production.sh`
- **Template**: `mygest/settings_local.py.example`

---

**Status**: ✅ Soluzione 2 implementata e testata  
**Verificato**: ✓ Settings locali caricati correttamente
