# Configurazione Django Modulare - Guida

## 📋 Panoramica

MyGest usa una **struttura settings modulare** per separare le configurazioni di **development** e **production**, garantendo:

- ✅ **Security hardening** in produzione (SECRET_KEY validation, HTTPS enforcement, CORS strict)
- ✅ **Developer experience** ottimizzata in sviluppo (Debug Toolbar, console email, CORS permissivo)
- ✅ **Environment-driven** configuration via `.env` file
- ✅ **Fail-safe defaults** - errore immediato se configurazione critica mancante

---

## 📂 Struttura Files

```
mygest/
├── settings/
│   ├── __init__.py       # Settings loader (auto-detect environment)
│   ├── base.py           # Settings comuni (database, cache, apps, etc.)
│   ├── development.py    # Development overrides (DEBUG=True, permissivo)
│   └── production.py     # Production overrides (hardened security)
└── settings.py           # ⚠️ DEPRECATED - mantenuto per compatibilità
```

### File Breakdown

| File | Scopo | Importabile | Ambiente |
|------|-------|-------------|----------|
| `base.py` | Settings comuni + validation | ❌ NO (solo via extends) | Tutti |
| `development.py` | Dev overrides + Debug Toolbar | ✅ SI via DJANGO_ENV | Development |
| `production.py` | Security hardened + HTTPS | ✅ SI via DJANGO_ENV | Production |
| `__init__.py` | Auto-loader basato su env | ✅ SI (default) | Auto-detect |

---

## 🚀 Utilizzo

### Development (locale)

```bash
# 1. Crea .env file
cp .env.example .env

# 2. Genera SECRET_KEY sicura
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 3. Modifica .env
nano .env

# Imposta:
DJANGO_ENV=development
DEBUG=True
SECRET_KEY=<chiave_generata>
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://mygest_user:password@localhost:5432/mygest

# 4. Avvia server
python manage.py runserver

# Output atteso:
# ✓ Django settings: DEVELOPMENT mode
# 🔧 DJANGO DEVELOPMENT MODE
# DEBUG: True
# ALLOWED_HOSTS: ['localhost', '127.0.0.1', ...]
```

### Production (VPS)

```bash
# 1. Crea .env produzione
nano /srv/mygest/app/.env

# Imposta:
DJANGO_ENV=production
DEBUG=False  # Ignorato, sempre False in production
SECRET_KEY=<chiave_sicura_50+_caratteri>
ALLOWED_HOSTS=mygest.example.com,api.mygest.example.com
DATABASE_URL=postgresql://user:strong_password@localhost:5432/mygest_db
ARCHIVIO_BASE_PATH=/srv/mygest/archivio
REDIS_URL=redis://localhost:6379/1
EMAIL_HOST_USER=notify@mygest.example.com
EMAIL_HOST_PASSWORD=<secure_password>

# 2. Testa configurazione
python manage.py check --deploy

# Output atteso:
# ✓ Django settings: PRODUCTION mode
# 🔒 DJANGO PRODUCTION MODE - SECURITY HARDENED
# ✓ DEBUG: False
# ✓ SECRET_KEY: 64 chars (SECURE)
# ✓ HTTPS: Enforced with HSTS
# ✓ CORS: 2 origins (HTTPS only)

# 3. Collectstatic con compression
python manage.py collectstatic --noinput

# 4. Restart server
sudo systemctl restart mygest
```

---

## 🔐 Security Validations

### SECRET_KEY Validation

La chiave segreta viene validata **all'avvio** in `base.py`:

```python
def validate_secret_key(secret_key):
    """Valida SECRET_KEY - solleva ImproperlyConfigured se insicura"""
    
    # ❌ Errore se mancante
    if not secret_key:
        raise ImproperlyConfigured("SECRET_KEY non configurata!")
    
    # ❌ Errore se usa default django-insecure
    if secret_key.startswith('django-insecure'):
        raise ImproperlyConfigured("SECRET_KEY usa default insicuro!")
    
    # ❌ Errore se < 50 caratteri
    if len(secret_key) < 50:
        raise ImproperlyConfigured("SECRET_KEY troppo corta!")
    
    # ✅ OK
    return secret_key
```

**Come generare**:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Production-Only Validations

In **production settings** (`production.py`):

| Check | Validation | Error se... |
|-------|------------|-------------|
| **ALLOWED_HOSTS** | Must be explicit | Vuoto o contiene `*` wildcard |
| **DATABASE_URL** | Password required | Password vuota o default insicuro |
| **HTTPS** | Enforced | Non configurabile (sempre on) |
| **DEBUG** | Always False | Non configurabile (ignorato .env) |
| **ARCHIVIO_BASE_PATH** | Must exist and writable | Directory non esiste o no permessi |
| **CORS** | Only HTTPS origins | Builds automaticamente da ALLOWED_HOSTS |

---

## 🔄 Migrazione da settings.py Monolitico

### Prima (deprecated):

```python
# mygest/settings.py
SECRET_KEY = env('SECRET_KEY', default='django-insecure-...')  # ❌ Default non sicuro
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# Mixing dev e prod configurations
if DEBUG:
    # dev stuff
else:
    # prod stuff
```

### Dopo (modulare):

```python
# mygest/settings/base.py
SECRET_KEY = validate_secret_key(env('SECRET_KEY', default=''))  # ✅ Validation

# mygest/settings/development.py
DEBUG = True  # ✅ Esplicito per dev

# mygest/settings/production.py
DEBUG = False  # ✅ Sempre False, non overridabile
```

### Compatibilità Retroattiva

Il vecchio `mygest/settings.py` è **ancora presente** ma **deprecated**. Per usarlo esplicitamente:

```bash
# Force old settings (NOT RECOMMENDED)
export DJANGO_SETTINGS_MODULE=mygest.settings
python manage.py runserver
```

**⚠️ DEPRECATION NOTICE**: Il file `settings.py` monolitico sarà rimosso in versione 2.0.

---

## 🌍 Environment Variables

### Variabili Obbligatorie

| Variabile | Development | Production | Default | Note |
|-----------|-------------|------------|---------|------|
| `DJANGO_ENV` | `development` | `production` | `development` | Determina quale settings caricare |
| `SECRET_KEY` | ✅ Obbligatorio | ✅ Obbligatorio | ❌ NESSUNO | Min 50 char, no 'django-insecure' |
| `ALLOWED_HOSTS` | Auto: `localhost,127.0.0.1` | ✅ Obbligatorio | ❌ NESSUNO | No wildcard `*` in prod |
| `DATABASE_URL` | Opzionale | ✅ Raccomandato | Fallback a `DB_*` vars | Format: `postgresql://user:pass@host/db` |

### Variabili Raccomandate

| Variabile | Scopo | Default Development | Default Production |
|-----------|-------|---------------------|--------------------|
| `ARCHIVIO_BASE_PATH` | Storage documenti | `./archivio` | `/srv/mygest/archivio` |
| `REDIS_URL` | Cache + sessions | `redis://localhost:6379/1` | Same |
| `EMAIL_HOST_USER` | SMTP email | Console backend | ❌ Required per SMTP |
| `OPENAI_API_KEY` | AI Classifier | Empty (disabled) | Empty (disabled) |

### Variabili Opzionali

Vedi [.env.example](.env.example) per lista completa con documentazione inline.

---

## 📊 Differenze Development vs Production

| Feature | Development | Production |
|---------|-------------|------------|
| **DEBUG** | ✅ `True` | ❌ `False` (always) |
| **ALLOWED_HOSTS** | `['localhost', '127.0.0.1', ...]` | From `.env` (required) |
| **CORS_ALLOWED_ORIGINS** | HTTP localhost:5173/3000 | HTTPS only from ALLOWED_HOSTS |
| **Django Debug Toolbar** | ✅ Installed | ❌ Not installed |
| **Email Backend** | Console (or SMTP if configured) | SMTP (required) |
| **Static Compression** | ❌ Disabled (faster) | ✅ Enabled (optimized) |
| **HTTPS Enforcement** | ❌ Disabled | ✅ Enforced (HSTS 1 year) |
| **SESSION_COOKIE_SECURE** | ❌ `False` | ✅ `True` |
| **CSRF_COOKIE_SECURE** | ❌ `False` | ✅ `True` |
| **Security Headers** | Relaxed | Strict (CSP, X-Frame, HSTS) |
| **Logging** | Console + files (14 days) | Files only (90 days security) |
| **SECRET_KEY validation** | ✅ Same validation | ✅ Same validation |
| **Database password** | Fallback to default | ❌ Required, no default |
| **ARCHIVIO_BASE_PATH check** | Creates if missing | ❌ Must exist + writable |

---

## 🧪 Testing

### Local Testing

```bash
# Test development settings
DJANGO_ENV=development python manage.py check
DJANGO_ENV=development python manage.py runserver

# Test production settings (simulato)
DJANGO_ENV=production python manage.py check --deploy

# ⚠️ Questo mostrerà errori se .env non ha tutte le var di produzione
```

### Pre-Deploy Checklist

```bash
# 1. Verifica .env produzione
cat /srv/mygest/app/.env | grep -E "SECRET_KEY|ALLOWED_HOSTS|DATABASE_URL"

# 2. Test settings load
cd /srv/mygest/app
source venv/bin/activate
DJANGO_ENV=production python manage.py check --deploy

# 3. Collectstatic
DJANGO_ENV=production python manage.py collectstatic --noinput

# 4. Migrate
DJANGO_ENV=production python manage.py migrate

# 5. Restart
sudo systemctl restart mygest
sudo systemctl status mygest
```

### Common Errors

| Error | Causa | Soluzione |
|-------|-------|-----------|
| `ImproperlyConfigured: SECRET_KEY non configurata!` | Manca `SECRET_KEY` in `.env` | Genera chiave e aggiungi a `.env` |
| `ImproperlyConfigured: SECRET_KEY usa default insicuro!` | SECRET_KEY inizia con `django-insecure` | Sostituisci con chiave nuova |
| `ImproperlyConfigured: ALLOWED_HOSTS non configurato!` | `.env` produzione senza `ALLOWED_HOSTS` | Aggiungi domini: `ALLOWED_HOSTS=mygest.example.com` |
| `ImproperlyConfigured: ALLOWED_HOSTS contiene wildcard '*'` | `ALLOWED_HOSTS=*` in produzione | Specifica domini espliciti |
| `ImproperlyConfigured: ARCHIVIO_BASE_PATH non esiste` | Directory non creata | `mkdir -p /srv/mygest/archivio && chown mygest:mygest /srv/mygest/archivio` |

---

## 📝 Best Practices

### ✅ DO

1. **Usa DJANGO_ENV** per switchare ambienti
2. **Genera SECRET_KEY forte** (min 50 char) per ogni ambiente
3. **Committare .env.example**, mai `.env`
4. **Specifica ALLOWED_HOSTS espliciti** in produzione (no `*`)
5. **Usa DATABASE_URL** per database config (più semplice)
6. **Testa production settings localmente** prima del deploy
7. **Esegui `check --deploy`** prima di ogni deploy produzione
8. **Monitora logs** `security.log` e `errors.log` in produzione

### ❌ DON'T

1. **Non hardcodare segreti** in `settings/*.py` (solo `.env`)
2. **Non usare default insicuri** (`django-insecure`, password vuote)
3. **Non disabilitare HTTPS** in produzione (non configurabile)
4. **Non usare `ALLOWED_HOSTS=['*']`** in produzione (security risk)
5. **Non committare `.env`** su git (gitignored)
6. **Non usare `DEBUG=True`** in produzione (ignorato comunque)
7. **Non modificare SECRET_KEY** dopo deploy (invalida sessioni)
8. **Non usare sqlite** in produzione (PostgreSQL only)

---

## 🔗 Files Correlati

- [.env.example](.env.example) - Template variabili ambiente con documentazione
- [SECURITY_CHECKLIST.md](docs/SECURITY_CHECKLIST.md) - Security review completa
- [GAP_ANALYSIS.md](docs/GAP_ANALYSIS.md) - Gap security identificati
- [DEPLOY_GUIDE.md](DEPLOY_GUIDE.md) - Guida deploy completa

---

## 🆘 Troubleshooting

### Server non si avvia dopo migrazione

```bash
# 1. Verifica quale settings viene caricato
python manage.py diffsettings | grep DJANGO_ENV

# 2. Verifica .env
cat .env | grep -E "DJANGO_ENV|SECRET_KEY"

# 3. Test manuale import
python
>>> from mygest.settings import DEBUG, SECRET_KEY, ALLOWED_HOSTS
>>> print(f"DEBUG={DEBUG}, SECRET_KEY length={len(SECRET_KEY)}, HOSTS={ALLOWED_HOSTS}")
```

### Errore "SECRET_KEY troppo corta"

```bash
# Genera nuova chiave (output = 64 caratteri)
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Copia in .env
echo "SECRET_KEY=<output_generato>" >> .env
```

### CORS errors dopo deploy

```bash
# Verifica CORS_ALLOWED_ORIGINS in produzione
DJANGO_ENV=production python manage.py shell
>>> from django.conf import settings
>>> print(settings.CORS_ALLOWED_ORIGINS)
# Output atteso: ['https://mygest.example.com']

# Se vuoto, verifica ALLOWED_HOSTS
>>> print(settings.ALLOWED_HOSTS)
```

---

**Versione**: 1.0  
**Data**: 3 Marzo 2026  
**Maintainer**: Sandro Chimenti
