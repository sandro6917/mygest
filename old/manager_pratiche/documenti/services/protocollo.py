# services/protocollo.py
from django.db import transaction
from django.utils import timezone
from ..models import Documento, ProtocolloCounter

def assegna_protocollo(documento: Documento, direzione: str, quando=None, forza=False) -> Documento:
    """
    Assegna numero di protocollo a un documento.
    - direzione: "IN" / "OUT"
    - quando: datetime (default now)
    - forza: se True riassegna anche se già protocollato (sconsigliato; di solito False)
    """
    assert direzione in ("IN", "OUT")
    if documento.protocollo_numero and not forza:
        return documento  # già protocollato, idempotente

    quando = quando or timezone.now()
    anno = quando.year

    with transaction.atomic():
        # blocca/crea contatore
        counter = (
            ProtocolloCounter.objects
            .select_for_update()
            .filter(cliente=documento.cliente, anno=anno, direzione=direzione)
            .first()
        )
        if not counter:
            counter = ProtocolloCounter.objects.create(
                cliente=documento.cliente, anno=anno, direzione=direzione, last_number=0
            )
        # incrementa
        counter.last_number += 1
        numero = counter.last_number
        counter.save(update_fields=["last_number"])

        # scrive sul documento
        documento.protocollo_anno = anno
        documento.protocollo_direzione = direzione
        documento.protocollo_numero = numero
        documento.protocollo_data = quando
        documento.save(update_fields=[
            "protocollo_anno", "protocollo_direzione", "protocollo_numero", "protocollo_data"
        ])

    return documento
