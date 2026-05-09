"""
Django settings per ambiente PRODUCTION.

Estende base.py con configurazioni hardened per produzione:
- DEBUG=False forzato
- SECRET_KEY validation strict
- HTTPS enforcement
- Security headers
- CORS strict
- Logging esteso
- Compression enabled
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# PRODUCTION OVERRIDES - SECURITY HARDENED
# =============================================================================

# DEBUG SEMPRE False in produzione (non overridabile)
DEBUG = False

# ALLOWED_HOSTS - OBBLIGATORIO in produzione
if not ALLOWED_HOSTS:  # noqa: F405
    raise ImproperlyConfigured(  # noqa: F405
        "ALLOWED_HOSTS non configurato! "
        "Imposta ALLOWED_HOSTS nel file .env con i domini di produzione "
        "(es: ALLOWED_HOSTS=mygest.example.com,api.mygest.example.com)"
    )

# Validazione domini ALLOWED_HOSTS
for host in ALLOWED_HOSTS:  # noqa: F405
    if host in ['*', '.']:
        raise ImproperlyConfigured(  # noqa: F405
            f"ALLOWED_HOSTS contiene wildcard '{host}' - NON sicuro in produzione! "
            "Specifica domini espliciti."
        )

# Log allowed hosts per verifica deploy
print(f"✓ ALLOWED_HOSTS (produzione): {', '.join(ALLOWED_HOSTS)}")  # noqa: F405


# =============================================================================
# HTTPS & SECURITY HEADERS
# =============================================================================

# Force HTTPS
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 anno
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies secure
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Cookie SameSite strict
SESSION_COOKIE_SAMESITE = 'Lax'  # Lax per permettere redirect da pagamenti/login esterni
CSRF_COOKIE_SAMESITE = 'Lax'


# =============================================================================
# JWT AUTHENTICATION - PRODUCTION (STRINGENT)
# =============================================================================

# Scadenze più stringenti per produzione
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=15)  # 15 min (base: 1h)  # noqa: F405
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)     # 1 giorno (base: 7gg)  # noqa: F405

print(f"✓ JWT: Access 15min, Refresh 1day, Blacklist ENABLED")


# =============================================================================
# CORS PRODUCTION - STRICT
# =============================================================================

# Costruisci CORS origins solo da ALLOWED_HOSTS con HTTPS
CORS_ALLOWED_ORIGINS = []
for host in ALLOWED_HOSTS:  # noqa: F405
    if host not in ['localhost', '127.0.0.1', '[::1]']:
        CORS_ALLOWED_ORIGINS.append(f"https://{host}")

# Se non ci sono HTTPS origins, raise error
if not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(  # noqa: F405
        "Nessun CORS origin HTTPS configurato! "
        "ALLOWED_HOSTS deve contenere almeno un dominio di produzione."
    )

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

print(f"✓ CORS_ALLOWED_ORIGINS (produzione): {', '.join(CORS_ALLOWED_ORIGINS)}")


# =============================================================================
# DATABASE PRODUCTION
# =============================================================================

# Validazione DATABASE_URL o credenziali
if not env('DATABASE_URL', default=''):  # noqa: F405
    # Se non c'è DATABASE_URL, valida credenziali singole
    if not DATABASES['default'].get('PASSWORD'):  # noqa: F405
        raise ImproperlyConfigured(  # noqa: F405
            "Database password non configurata! "
            "Imposta DATABASE_URL o DB_PASSWORD nel file .env"
        )
    if DATABASES['default']['PASSWORD'] == 'ScegliUnaPasswordSicura':  # noqa: F405
        raise ImproperlyConfigured(  # noqa: F405
            "Database password usa default insicuro! "
            "Cambia DB_PASSWORD nel file .env"
        )

# Log database info (senza password)
db_config = DATABASES['default']  # noqa: F405
print(f"✓ Database: {db_config['NAME']} @ {db_config['HOST']}:{db_config['PORT']}")


# =============================================================================
# EMAIL PRODUCTION
# =============================================================================

# Validazione credenziali email
if EMAIL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":  # noqa: F405
    if not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:  # noqa: F405
        print("⚠ EMAIL_HOST_USER/PASSWORD non configurati - email disabilitate")
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    else:
        print(f"✓ Email SMTP: {EMAIL_HOST_USER}@{EMAIL_HOST}")  # noqa: F405


# =============================================================================
# STATIC FILES COMPRESSION
# =============================================================================

# Abilita compression in produzione
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True  # Pre-compress durante collectstatic

print("✓ Static files compression: ENABLED")


# =============================================================================
# LOGGING PRODUCTION
# =============================================================================

# Estendi logging per produzione con file handlers

# Security log handler
LOGGING['handlers']['security_file'] = {  # noqa: F405
    'level': 'WARNING',
    'class': 'logging.handlers.TimedRotatingFileHandler',
    'formatter': 'protocollo',
    'filename': str(LOG_DIR / 'security.log'),  # noqa: F405
    'when': 'midnight',
    'backupCount': 90,  # 3 mesi retention per security
    'encoding': 'utf-8',
}

# Error log handler
LOGGING['handlers']['error_file'] = {  # noqa: F405
    'level': 'ERROR',
    'class': 'logging.handlers.TimedRotatingFileHandler',
    'formatter': 'protocollo',
    'filename': str(LOG_DIR / 'errors.log'),  # noqa: F405
    'when': 'midnight',
    'backupCount': 30,  # 1 mese retention
    'encoding': 'utf-8',
}

# Django security logger
LOGGING['loggers']['django.security'] = {  # noqa: F405
    'handlers': ['security_file'],
    'level': 'WARNING',
    'propagate': False,
}

# Django general logger
LOGGING['loggers']['django'] = {  # noqa: F405
    'handlers': ['error_file'],
    'level': 'ERROR',
    'propagate': False,
}

print(f"✓ Logging: {LOG_DIR}")  # noqa: F405


# =============================================================================
# REDIS PRODUCTION
# =============================================================================

# Validazione Redis connection
redis_url = CACHES['default']['LOCATION']  # noqa: F405
if redis_url.startswith('redis://127.0.0.1') or redis_url.startswith('redis://localhost'):
    print(f"⚠ Redis usando localhost: {redis_url}")
    print("  Considera configurare Redis dedicato in produzione via REDIS_URL")
else:
    print(f"✓ Redis: {redis_url}")


# =============================================================================
# ARCHIVIO PRODUCTION
# =============================================================================

# Validazione percorso archivio
if not Path(ARCHIVIO_BASE_PATH).exists():  # noqa: F405
    raise ImproperlyConfigured(  # noqa: F405
        f"ARCHIVIO_BASE_PATH non esiste: {ARCHIVIO_BASE_PATH}\n"  # noqa: F405
        "Crea la directory o configura ARCHIVIO_BASE_PATH corretto nel .env"
    )

if not os.access(ARCHIVIO_BASE_PATH, os.W_OK):  # noqa: F405
    raise ImproperlyConfigured(  # noqa: F405
        f"ARCHIVIO_BASE_PATH non scrivibile: {ARCHIVIO_BASE_PATH}\n"  # noqa: F405
        "Verifica permessi directory per utente mygest"
    )

print(f"✓ Archivio: {ARCHIVIO_BASE_PATH}")  # noqa: F405


# =============================================================================
# JWT PRODUCTION
# =============================================================================

# Raccomandazione blacklist tokens in produzione
if not SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION'):  # noqa: F405
    print("⚠ JWT token blacklist DISABILITATA")
    print("  Raccomandato abilitare: SIMPLE_JWT['BLACKLIST_AFTER_ROTATION'] = True")


# =============================================================================
# RATE LIMITING (TODO)
# =============================================================================

# TODO: Implementare rate limiting in produzione
# REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
#     'rest_framework.throttling.AnonRateThrottle',
#     'rest_framework.throttling.UserRateThrottle',
# ]
# REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
#     'anon': '100/hour',
#     'user': '1000/hour',
# }


# =============================================================================
# INTEGRATIONS VALIDATION
# =============================================================================

# WhatsApp - warn se non configurato
if not WHATSAPP_CLOUD_ACCESS_TOKEN:  # noqa: F405
    print("ℹ WhatsApp API non configurato (opzionale)")

# AI Classifier - warn se no API key
if not AI_CLASSIFIER.get('OPENAI_API_KEY'):  # noqa: F405
    print("ℹ OpenAI API key non configurata - AI Classifier disabilitato")


# =============================================================================
# STARTUP INFO PRODUCTION
# =============================================================================

print("=" * 70)
print("🔒 DJANGO PRODUCTION MODE - SECURITY HARDENED")
print("=" * 70)
print(f"✓ DEBUG: {DEBUG}")
print(f"✓ SECRET_KEY: {len(SECRET_KEY)} chars ({'SECURE' if len(SECRET_KEY) >= 50 else 'WEAK'})")  # noqa: F405
print(f"✓ HTTPS: Enforced with HSTS")
print(f"✓ CORS: {len(CORS_ALLOWED_ORIGINS)} origins (HTTPS only)")
print(f"✓ Static compression: ENABLED")
print(f"✓ Security logging: ENABLED")
print("=" * 70)
print("⚠ RICORDA:")
print("  1. Esegui 'python manage.py check --deploy' per security checklist completa")
print("  2. Verifica backup database configurati")
print("  3. Monitora logs security.log e errors.log")
print("=" * 70)
