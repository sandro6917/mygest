"""
Django settings loader per MyGest.

Carica automaticamente il settings module corretto basato su DJANGO_SETTINGS_MODULE
o DJANGO_ENV environment variable.

Usage:
    # Development (default se non specificato)
    export DJANGO_ENV=development
    
    # Production
    export DJANGO_ENV=production
    
    # Oppure esplicitamente con DJANGO_SETTINGS_MODULE:
    export DJANGO_SETTINGS_MODULE=mygest.settings.production
"""
import os
import sys

# Determina quale settings module caricare
django_env = os.getenv('DJANGO_ENV', 'development').lower()

if django_env == 'production':
    from .production import *  # noqa: F401, F403
    print("✓ Django settings: PRODUCTION mode")
elif django_env == 'development':
    from .development import *  # noqa: F401, F403
    print("✓ Django settings: DEVELOPMENT mode")
else:
    # Fallback a development per ambienti sconosciuti
    print(f"⚠ DJANGO_ENV='{django_env}' non riconosciuto, fallback a DEVELOPMENT")
    from .development import *  # noqa: F401, F403

# Export DEBUG per controlli esterni
__all__ = ['DEBUG']
