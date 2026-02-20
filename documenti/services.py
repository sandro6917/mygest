from __future__ import annotations
from typing import Optional
from django.utils import timezone
from django.core.exceptions import ValidationError
from archivio_fisico.models import UnitaFisica
from anagrafiche.models import Anagrafica
from protocollo.models import MovimentoProtocollo
from .models import Documento

def protocolla(
    documento: Documento,
    direzione: str,  # 'IN' | 'OUT'
    *,
    quando=None,
    operatore=None,
    destinatario: str = "",
    destinatario_anagrafica: Optional[Anagrafica] = None,
    ubicazione: Optional[UnitaFisica] = None,
    data_rientro_prevista=None,
    causale: str = "",
    note: str = "",
) -> MovimentoProtocollo:
    quando = quando or timezone.now()
    direzione = (direzione or "").upper()
    if direzione not in ("IN", "OUT"):
        raise ValidationError("Direzione non valida (usa 'IN' o 'OUT')")

    if direzione == "IN":
        return MovimentoProtocollo.registra_entrata(
            documento=documento, quando=quando, operatore=operatore,
            da_chi=destinatario, destinatario_anagrafica=destinatario_anagrafica,
            ubicazione=ubicazione,
            causale=causale, note=note
        )
    else:
        return MovimentoProtocollo.registra_uscita(
            documento=documento, quando=quando, operatore=operatore,
            a_chi=destinatario, destinatario_anagrafica=destinatario_anagrafica,
            data_rientro_prevista=data_rientro_prevista,
            causale=causale, note=note, ubicazione=ubicazione
        )