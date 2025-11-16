from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ScadenzeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "scadenze"
    verbose_name = _("Scadenze")

    def ready(self) -> None:
        # Import dei segnali dell'app per registrare eventuali handler
        from . import signals  # noqa: F401

        return super().ready()