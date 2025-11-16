from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Anagrafica, AnagraficaDeletion

@receiver(post_delete, sender=Anagrafica)
def log_anagrafica_deletion(sender, instance: Anagrafica, **kwargs):
    try:
        display = instance.display_name()
    except Exception:
        display = getattr(instance, "ragione_sociale", "") or f"{getattr(instance,'cognome','')} {getattr(instance,'nome','')}".strip()
    AnagraficaDeletion.objects.create(
        original_id=instance.pk or 0,
        codice_fiscale=instance.codice_fiscale or "",
        display_name=display or "",
    )