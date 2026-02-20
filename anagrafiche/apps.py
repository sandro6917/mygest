from django.apps import AppConfig


class AnagraficheConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "anagrafiche"

    def ready(self):
        # Importa i signal per registrarli
        import anagrafiche.signals
