from __future__ import annotations
from django.apps import AppConfig

class FascicoliConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fascicoli"

    def ready(self):
        # integrazione opzionale con 'stampe'
        try:
            from stampe import registry
            from stampe.layouts import layout_fascicolo
        except Exception:
            return
        registry.register("fascicoli", "fascicolo", layout_fascicolo)