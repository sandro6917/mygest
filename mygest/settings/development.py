"""
Django settings per ambiente DEVELOPMENT.

Estende base.py con configurazioni specifiche per sviluppo locale:
- DEBUG=True
- Django Debug Toolbar
- Email console backend
- Logging verboso
- CORS permissivo
"""

from .base import *  # noqa: F401, F403

# =============================================================================
# DEVELOPMENT OVERRIDES
# =============================================================================

# Debug mode SEMPRE attivo in development (override possibile via .env)
DEBUG = env.bool('DEBUG', default=True)

# ALLOWED_HOSTS permissivo per sviluppo locale
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', '100.99.234.12']

# Internal IPs per Debug Toolbar
INTERNAL_IPS = ['127.0.0.1', 'localhost', '100.99.234.12']


# =============================================================================
# DJANGO DEBUG TOOLBAR
# =============================================================================

if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']  # noqa: F405
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')  # noqa: F405


# =============================================================================
# EMAIL DEVELOPMENT
# =============================================================================

# Default email console backend in sviluppo
if not env('EMAIL_HOST_USER', default=''):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    print("✓ Email backend: CONSOLE (sviluppo)")


# =============================================================================
# CORS PERMISSIVO
# =============================================================================

# In development, permetti Vite dev server con hot reload
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://100.99.234.12:5173",
    "http://100.99.234.12:3000",
]

CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()


# =============================================================================
# STATIC/COMPRESSION
# =============================================================================

# NO compression in development (faster rebuild)
COMPRESS_ENABLED = False
COMPRESS_OFFLINE = False


# =============================================================================
# LOGGING DEVELOPMENT
# =============================================================================

# Console handler sempre attivo in development
LOGGING['handlers']['console'] = {  # noqa: F405
    'level': 'DEBUG',
    'class': 'logging.StreamHandler',
    'formatter': 'protocollo',
}

# Log SQL queries in console (verbose)
if DEBUG and env.bool('LOG_SQL', default=False):
    LOGGING['loggers']['django.db.backends'] = {  # noqa: F405
        'level': 'DEBUG',
        'handlers': ['console'],
    }

# Log importers + AI classifier in console
LOGGING['loggers']['documenti.importers'] = {  # noqa: F405
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

LOGGING['loggers']['api.v1.ai_classifier'] = {  # noqa: F405
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}


# =============================================================================
# DATABASE DEVELOPMENT
# =============================================================================

# Fallback a password vuota se non specificata
if not DATABASES['default'].get('PASSWORD'):  # noqa: F405
    DATABASES['default']['PASSWORD'] = env('DB_PASSWORD', default='ScegliUnaPasswordSicura')  # noqa: F405
    print("⚠ DB_PASSWORD non configurata, usando default sviluppo")


# =============================================================================
# ARCHIVIO DEVELOPMENT
# =============================================================================

# Default archivio in development locale
if ARCHIVIO_BASE_PATH == str(BASE_DIR / 'archivio'):  # noqa: F405
    print(f"✓ ARCHIVIO_BASE_PATH: {ARCHIVIO_BASE_PATH} (sviluppo locale)")  # noqa: F405
    # Crea directory se non esiste
    Path(ARCHIVIO_BASE_PATH).mkdir(parents=True, exist_ok=True)  # noqa: F405


# =============================================================================
# SECURITY RELAXED FOR DEV
# =============================================================================

# NO HTTPS enforcement in development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0  # No HSTS in development
SECURE_CONTENT_TYPE_NOSNIFF = False  # Permissivo per debugging
SECURE_BROWSER_XSS_FILTER = False

# CSRF più permissivo in dev
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'

# Session più permissive
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True  # Manteniamo HttpOnly anche in dev per best practice


# =============================================================================
# JWT AUTHENTICATION - DEVELOPMENT (EXTENDED)
# =============================================================================

# Scadenze più lunghe per comodità in sviluppo
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=24)   # 24 ore (prod: 15min)  # noqa: F405
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=30)   # 30 giorni (prod: 1gg)  # noqa: F405

print(f"✓ JWT: Access 24h, Refresh 30d, Blacklist ENABLED (dev mode)")


# =============================================================================
# STARTUP INFO
# =============================================================================

print("=" * 70)
print("🔧 DJANGO DEVELOPMENT MODE")
print("=" * 70)
print(f"DEBUG: {DEBUG}")
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")  # noqa: F405
print(f"DATABASE: {DATABASES['default']['NAME']} @ {DATABASES['default']['HOST']}")  # noqa: F405
print(f"ARCHIVIO: {ARCHIVIO_BASE_PATH}")  # noqa: F405
print(f"REDIS: {CACHES['default']['LOCATION']}")  # noqa: F405
print(f"EMAIL: {EMAIL_BACKEND}")  # noqa: F405
print("=" * 70)
