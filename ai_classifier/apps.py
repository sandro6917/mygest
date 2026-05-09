from django.apps import AppConfig


class AiClassifierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_classifier'
    verbose_name = 'AI Classificatore Documenti'
    
    def ready(self):
        """Inizializzazione app - Registra signals"""
        # Import signals per attivare decoratori @receiver
        import ai_classifier.signals  # noqa
