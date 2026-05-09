"""
Core App Configuration
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core - Utenti e Permessi'
    
    def ready(self):
        # Import signals se necessari
        pass
