from django.apps import AppConfig

class AnagraficheConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "anagrafiche"

    def ready(self):
        from . import signals  # noqa
