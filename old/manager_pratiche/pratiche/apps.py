from __future__ import annotations
from django.apps import AppConfig

class PraticheConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pratiche"

    def ready(self):
        from stampe import registry
        from stampe.layouts import layout_pratica
        registry.register("pratiche", "pratica", layout_pratica)