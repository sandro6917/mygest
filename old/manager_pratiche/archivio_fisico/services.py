from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import UnitaFisica, CollocazioneFisica

def assegna_collocazione(obj, unita: UnitaFisica, *, note: str = "") -> CollocazioneFisica:
    ct = ContentType.objects.get_for_model(type(obj))
    return CollocazioneFisica.objects.create(
        content_type=ct, object_id=obj.pk, unita=unita, note=note, attiva=True, dal=timezone.now().date()
    )

def assegna_collocazione_documento(documento, unita: UnitaFisica, *, note: str = "") -> CollocazioneFisica:
    return CollocazioneFisica.objects.create(
        documento=documento,
        unita=unita,
        note=note,
        attiva=True,
        dal=timezone.now().date(),
    )