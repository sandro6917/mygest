"""Servizi applicativi per l'app comunicazioni."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from protocollo.services import protocolla as protocolla_documento


def protocolla_comunicazione(
    comunicazione,
    *,
    direzione: str | None = None,
    quando=None,
    operatore=None,
    destinatario: str = "",
    destinatario_anagrafica=None,
    ubicazione=None,
    data_rientro_prevista=None,
    causale: str = "",
    note: str = "",
):
    """Protocolla la comunicazione sfruttando l'app protocollo."""
    if comunicazione.protocollo_movimento_id:
        raise ValidationError("La comunicazione risulta già protocollata.")
    if not comunicazione.documento_protocollo_id:
        raise ValidationError("Imposta prima il documento da protocollare.")

    direzione_eff = (direzione or comunicazione.direzione or "IN").upper()
    if direzione_eff not in ("IN", "OUT"):
        raise ValidationError("Direzione non valida per la protocollazione.")

    causale_eff = causale or comunicazione.oggetto or ""

    with transaction.atomic():
        movimento = protocolla_documento(
            comunicazione.documento_protocollo,
            direzione_eff,
            quando=quando,
            operatore=operatore,
            destinatario=destinatario,
            destinatario_anagrafica=destinatario_anagrafica,
            ubicazione=ubicazione,
            data_rientro_prevista=data_rientro_prevista,
            causale=causale_eff,
            note=note or "",
        )
        comunicazione.protocollo_movimento = movimento
        comunicazione.save(update_fields=["protocollo_movimento"])
        return movimento
