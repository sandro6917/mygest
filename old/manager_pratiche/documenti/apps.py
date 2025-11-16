from __future__ import annotations
from django.apps import AppConfig

class DocumentiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "documenti"

    def ready(self):
        # integrazione opzionale con 'stampe'
        try:
            from stampe import registry
            from stampe.layouts import layout_documento
        except Exception:
            return
        registry.register("documenti", "documento", layout_documento)