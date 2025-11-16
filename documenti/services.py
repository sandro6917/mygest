from __future__ import annotations
from typing import Optional
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Documento, MovimentoProtocollo, Ubicazione

def protocolla(
    documento: Documento,
    direzione: str,  # 'IN' | 'OUT'
    *,
    quando=None,
    operatore=None,
    destinatario: str = "",
    ubicazione: Optional[Ubicazione] = None,
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
            da_chi=destinatario, ubicazione=ubicazione,
            causale=causale, note=note
        )
    else:
        return MovimentoProtocollo.registra_uscita(
            documento=documento, quando=quando, operatore=operatore,
            a_chi=destinatario, data_rientro_prevista=data_rientro_prevista,
            causale=causale, note=note, ubicazione=ubicazione
        )