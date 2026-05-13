"""
Django base settings per MyGest.

Configurazione comune condivisa tra development e production.
NON importare direttamente questo file - usa development.py o production.py.
"""

import os
import sys
from pathlib import Path
from datetime import timedelta
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ImproperlyConfigured
import environ

# Initialize environment variables
env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Read .env file if it exists
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

# Log directory
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# SECURITY CRITICAL SETTINGS
# =============================================================================

def validate_secret_key(secret_key):
    """
    Valida che SECRET_KEY sia configurata correttamente.
    Solleva ImproperlyConfigured se insicura o mancante.
    """
    if not secret_key:
        raise ImproperlyConfigured(
            "SECRET_KEY non configurata! "
            "Imposta la variabile SECRET_KEY nel file .env"
        )
    
    if secret_key.startswith('django-insecure'):
        raise ImproperlyConfigured(
            "SECRET_KEY usa default insicuro! "
            "Genera una chiave sicura: "
            "python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
        )
    
    if len(secret_key) < 50:
        raise ImproperlyConfigured(
            f"SECRET_KEY troppo corta ({len(secret_key)} caratteri, minimo 50). "
            "Genera una chiave sicura con il comando sopra."
        )
    
    return secret_key


# SECRET_KEY - OBBLIGATORIA, nessun default
SECRET_KEY = validate_secret_key(env('SECRET_KEY', default=''))

# DEBUG - default False per sicurezza
DEBUG = env.bool('DEBUG', default=False)

# ALLOWED_HOSTS - da environment variable, richiesto in produzione
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])


# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',  # Token Authentication per Agent Desktop
    'rest_framework_simplejwt',  # JWT Authentication
    'rest_framework_simplejwt.token_blacklist',  # JWT Token Blacklist
    'corsheaders',  # CORS Headers
    'django_filters',  # Django Filter per API
    'graphene_django',
    'compressor',  # Django Compressor per ottimizzazione statica
    'anagrafiche',
    'archivio_fisico',
    'documenti',
    'fascicoli',
    'pratiche',
    'scadenze',
    'stampe',
    'titolario',
    "django_addanother",
    "protocollo",
    "crispy_forms",
    "crispy_bootstrap5",
    "comunicazioni",
    "whatsapp",
    "ai_classifier",  # AI Classificatore Documenti
    "core",  # Core functionality and management commands
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS - Must be at top
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve file statici compressi
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mygest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "mygest.context_processors.app_name",
                "mygest.context_processors.breadcrumbs",
            ],
        },
    },
]

WSGI_APPLICATION = 'mygest.wsgi.application'


# =============================================================================
# DATABASE
# =============================================================================

# Disabilita connection pooling in CI/CD (più semplice per test)
USE_DB_POOL = not env.bool('DISABLE_DB_POOL', default=False)

# Se DATABASE_URL è presente, usala (ha priorità)
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
    # Sovrascrivi ENGINE con pool se abilitato (solo se non è SQLite)
    if USE_DB_POOL and DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3':
        DATABASES['default']['ENGINE'] = 'dj_db_conn_pool.backends.postgresql'
        DATABASES['default']['POOL_OPTIONS'] = {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 20,
            'RECYCLE': 3600,
            'PRE_PING': True,
        }
else:
    # Configurazione di default (sviluppo locale)
    DATABASES = {
        'default': {
            'ENGINE': 'dj_db_conn_pool.backends.postgresql' if USE_DB_POOL else 'django.db.backends.postgresql',
            'NAME': env('DB_NAME', default='mygest'),
            'USER': env('DB_USER', default='mygest_user'),
            'PASSWORD': env('DB_PASSWORD', default=''),
            'HOST': env('DB_HOST', default='127.0.0.1'),
            'PORT': env('DB_PORT', default='5432'),
        }
    }
    
    # Aggiungi opzioni pool solo se abilitato
    if USE_DB_POOL:
        DATABASES['default']['POOL_OPTIONS'] = {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 20,
            'RECYCLE': 3600,
            'PRE_PING': True,
        }

# SQLite per testing (solo se DATABASE_URL non è configurata, per non sovrascrivere PostgreSQL in CI)
if (
    'DATABASE_URL' not in os.environ
    and any(arg.startswith("test") or os.path.basename(arg).startswith("pytest") for arg in sys.argv)
):
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test.sqlite3',
    }


# =============================================================================
# CACHING (REDIS)
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        },
        'KEY_PREFIX': 'mygest',
        'TIMEOUT': 300,  # 5 minuti default
    },
    # Cache separata per sessioni
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env('REDIS_SESSION_URL', default='redis://127.0.0.1:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'mygest_session',
        'TIMEOUT': 86400,  # 24 ore per sessioni
    },
}

# Usa Redis per le sessioni
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'


# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = env('EMAIL_BACKEND', default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env('EMAIL_HOST', default="smtps.aruba.it")
EMAIL_PORT = env.int('EMAIL_PORT', default=465)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=True)

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured("EMAIL_USE_TLS e EMAIL_USE_SSL non possono essere entrambi attivi.")

EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
EMAIL_TIMEOUT = env.int('EMAIL_TIMEOUT', default=30)
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or "noreply@mygest.local")

# Failover to console in development
EMAIL_FAILOVER_TO_CONSOLE = env.bool('EMAIL_FAILOVER_TO_CONSOLE', default=DEBUG)

# IMAP settings
EMAIL_IMAP_HOST = env('EMAIL_IMAP_HOST', default="imaps.aruba.it")
EMAIL_IMAP_PORT = env.int('EMAIL_IMAP_PORT', default=993)
EMAIL_IMAP_USER = env('EMAIL_IMAP_USER', default=EMAIL_HOST_USER)
EMAIL_IMAP_PASSWORD = env('EMAIL_IMAP_PASSWORD', default=EMAIL_HOST_PASSWORD)
EMAIL_IMAP_SENT_FOLDER = env('EMAIL_IMAP_SENT_FOLDER', default="Inviati")
EMAIL_IMAP_SENT_FOLDERS = env.list('EMAIL_IMAP_SENT_FOLDERS', default=[])
EMAIL_IMAP_TIMEOUT = env.int('EMAIL_IMAP_TIMEOUT', default=EMAIL_TIMEOUT)


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'it-it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True


# =============================================================================
# STATIC FILES
# =============================================================================

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',  # Django Compressor
]

# Whitenoise con compressione Brotli
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Django Compressor (abilitato solo in produzione, configurato nei settings specifici)
COMPRESS_ENABLED = False  # Override nei settings specifici
COMPRESS_OFFLINE = False
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.rCSSMinFilter',
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',
]


# =============================================================================
# ARCHIVIO / STORAGE
# =============================================================================

ARCHIVIO_BASE_PATH = env('ARCHIVIO_BASE_PATH', default=str(BASE_DIR / 'archivio'))

# Media URL per servire i file dell'archivio (sovrascritta da R2 se configurato)
MEDIA_URL = '/archivio/'
MEDIA_ROOT = ARCHIVIO_BASE_PATH

# Storage personalizzato per NAS
NAS_STORAGE = FileSystemStorage(location=ARCHIVIO_BASE_PATH)

# ML Models storage (sempre su disco locale, non su R2)
NAS_ML_MODELS_PATH = os.path.join(ARCHIVIO_BASE_PATH, "ml_models")

# Cloudflare R2 Storage (opzionale - se configurato sostituisce il filesystem locale)
# Crea bucket su: https://dash.cloudflare.com → R2 → Crea bucket
# Genera API token con permessi Object Read/Write sul bucket
CLOUDFLARE_R2 = {
    'ACCOUNT_ID': env('R2_ACCOUNT_ID', default=''),
    'ACCESS_KEY_ID': env('R2_ACCESS_KEY_ID', default=''),
    'SECRET_ACCESS_KEY': env('R2_SECRET_ACCESS_KEY', default=''),
    'BUCKET_NAME': env('R2_BUCKET_NAME', default=''),
    # Durata URL firmati in secondi (default 1 ora).
    # I file restano privati su R2: ogni URL contiene una firma con scadenza.
    'URL_EXPIRY_SECONDS': env.int('R2_URL_EXPIRY_SECONDS', default=3600),
    # Se True: lettura da R2 abilitata, scrittura/cancellazione bloccata.
    # Usare in sviluppo per leggere i file di produzione senza rischio di modificarli.
    'READ_ONLY': env.bool('R2_READ_ONLY', default=False),
}

# Importazioni
IMPORTAZIONI_SOURCE_DIRS = env.list(
    'IMPORTAZIONI_SOURCE_DIRS',
    default=[str(BASE_DIR / 'importazioni')]
)


# =============================================================================
# AUTH & REDIRECTS
# =============================================================================

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/classificazione/"
LOGOUT_REDIRECT_URL = "/accounts/login/"


# =============================================================================
# MYGEST SPECIFIC SETTINGS
# =============================================================================

# Etichette / stampa
DYMO_PRINTER_NAME = env('DYMO_PRINTER_NAME', default="DYMO_LabelWriter_450")
ETICHETTE_SERVER_PRINT = env.bool('ETICHETTE_SERVER_PRINT', default=False)
ETICHETTE_MARGIN_MM = env.float('ETICHETTE_MARGIN_MM', default=10.0)

# Documenti
DOCUMENTI_FILE_PATTERN_DEFAULT = env(
    'DOCUMENTI_FILE_PATTERN_DEFAULT',
    default="{tipo.codice}_{id}_{attr:repertorio_atto|REPNA}_{data_documento:%Y%m%d}_{slug:descrizione}.pdf"
)
DOCUMENTI_RENAME_ONLY_NEW = env.bool('DOCUMENTI_RENAME_ONLY_NEW', default=True)
DOCUMENTI_FILENAME_MAX_LEN = env.int('DOCUMENTI_FILENAME_MAX_LEN', default=140)
DOCUMENTI_PATTERN_ENABLE_UNIQUE = env.bool('DOCUMENTI_PATTERN_ENABLE_UNIQUE', default=True)

# Archivio Fisico
ARCHIVIO_FISICO_UNITA_SCARICO_ID = env.int('ARCHIVIO_FISICO_UNITA_SCARICO_ID', default=28)


# =============================================================================
# REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # JWT First
        "rest_framework.authentication.TokenAuthentication",  # Token per Agent Desktop
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}


# =============================================================================
# JWT AUTHENTICATION
# =============================================================================

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,  # ✅ Blacklist abilitata
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}


# =============================================================================
# CORS CONFIGURATION
# =============================================================================

CORS_ALLOWED_ORIGINS_LIST = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",  # Alternative port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS_LIST
CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

# CSRF Cookie Settings per SPA
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_HTTPONLY = False  # Permette al JavaScript di leggere il cookie
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False
CSRF_COOKIE_SECURE = False  # Override in production

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


# =============================================================================
# GRAPHENE
# =============================================================================

GRAPHENE = {
    "SCHEMA": "mygest.schema.schema",
}


# =============================================================================
# INTEGRATIONS
# =============================================================================

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_FILE = env(
    'GOOGLE_CALENDAR_CREDENTIALS_FILE',
    default=str(BASE_DIR / 'google_credentials.json')
)
GOOGLE_CALENDAR_DEFAULT_ID = env('GOOGLE_CALENDAR_DEFAULT_ID', default='')

# WhatsApp Cloud API
WHATSAPP_CLOUD_API_VERSION = env('WHATSAPP_CLOUD_API_VERSION', default="v20.0")
WHATSAPP_CLOUD_BASE_URL = env('WHATSAPP_CLOUD_BASE_URL', default="https://graph.facebook.com")
WHATSAPP_CLOUD_PHONE_NUMBER_ID = env('WHATSAPP_CLOUD_PHONE_NUMBER_ID', default='')
WHATSAPP_CLOUD_BUSINESS_ACCOUNT_ID = env('WHATSAPP_CLOUD_BUSINESS_ACCOUNT_ID', default='')
WHATSAPP_CLOUD_ACCESS_TOKEN = env('WHATSAPP_CLOUD_ACCESS_TOKEN', default='')
WHATSAPP_CLOUD_VERIFY_TOKEN = env('WHATSAPP_CLOUD_VERIFY_TOKEN', default='')
WHATSAPP_CLOUD_APP_SECRET = env('WHATSAPP_CLOUD_APP_SECRET', default='')
WHATSAPP_CLOUD_TIMEOUT = env.int('WHATSAPP_CLOUD_TIMEOUT', default=10)
WHATSAPP_ALERT_DEFAULT_NUMBERS = env.list('WHATSAPP_ALERT_DEFAULT_NUMBERS', default=['+39335337132'])
WHATSAPP_ALERTS_ENABLED = env.bool('WHATSAPP_ALERTS_ENABLED', default=False)

# Telegram Bot
TELEGRAM_BOT_TOKEN = env('TELEGRAM_BOT_TOKEN', default='8352908018:AAHYs48NQCRoDfNWaQ6B-fiQaTO0h8FibYk')
TELEGRAM_ALERT_DEFAULT_CHAT_IDS = env.list('TELEGRAM_ALERT_DEFAULT_CHAT_IDS', default=['7198357516'])
TELEGRAM_ALERTS_ENABLED = env.bool('TELEGRAM_ALERTS_ENABLED', default=True)

# AI Classifier
AI_CLASSIFIER = {
    'DEFAULT_LLM_PROVIDER': 'openai',
    'OPENAI_MODEL': 'gpt-4o-mini',
    'OPENAI_API_KEY': env('OPENAI_API_KEY', default=''),
    'LLM_TEMPERATURE': 0.1,
    'LLM_MAX_TOKENS': 500,
    'CONFIDENCE_THRESHOLD': 0.7,
    'MAX_FILE_SIZE_MB': 50,
    'ALLOWED_EXTENSIONS': ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.docx'],
}


# =============================================================================
# LOGGING
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "protocollo": {
            "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        },
    },
    "handlers": {
        "protocollazione_file": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "protocollo",
            "filename": str(LOG_DIR / "protocollazione.log"),
            "when": "midnight",
            "backupCount": 14,
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "documenti.protocollo": {
            "handlers": ["protocollazione_file"],
            "level": "INFO",
            "propagate": False,
        },
        "documenti.protocollazione": {
            "handlers": ["protocollazione_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# =============================================================================
# CRISPY FORMS
# =============================================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = ("bootstrap5",)
CRISPY_TEMPLATE_PACK = "bootstrap5"


# =============================================================================
# DEFAULT AUTO FIELD
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =============================================================================
# CELERY
# =============================================================================

from celery.schedules import crontab  # noqa: E402

CELERY_BROKER_URL = env('REDIS_URL', default='redis://127.0.0.1:6379/1')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://127.0.0.1:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Rome'
CELERY_TASK_TRACK_STARTED = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

CELERY_BEAT_SCHEDULE = {
    'invia-alert-scadenze': {
        'task': 'scadenze.tasks.invia_alert_scadenze_task',
        'schedule': crontab(minute='*/5'),
    },
    'sincronizza-mailbox': {
        'task': 'comunicazioni.tasks.sincronizza_mailbox_task',
        'schedule': crontab(minute='*/15'),
    },
    'aggiorna-codici-tributo': {
        'task': 'scadenze.tasks.aggiorna_codici_tributo_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),
    },
}
