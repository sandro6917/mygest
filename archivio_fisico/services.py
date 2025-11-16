from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
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


def _get_unita_scarico() -> UnitaFisica:
    unita_id = getattr(settings, "ARCHIVIO_FISICO_UNITA_SCARICO_ID", None)
    if not unita_id:
        raise ValidationError("Configura l'impostazione ARCHIVIO_FISICO_UNITA_SCARICO_ID per le operazioni di scarico.")
    try:
        return UnitaFisica.objects.get(pk=unita_id)
    except UnitaFisica.DoesNotExist as exc:
        raise ValidationError("L'unità di scarico configurata non esiste.") from exc


def _default_stato_scarico(obj) -> str | None:
    from documenti.models import Documento
    from fascicoli.models import Fascicolo

    if isinstance(obj, Documento):
        return Documento.Stato.SCARICATO
    if isinstance(obj, Fascicolo):
        return Fascicolo.Stato.SCARICATO
    return None


def _normalize_stato_value(obj, value: str | None) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    from documenti.models import Documento
    from fascicoli.models import Fascicolo

    if isinstance(obj, Documento):
        choices = {code.lower(): code for code, _ in Documento.Stato.choices}
        labels = {label.lower(): code for code, label in Documento.Stato.choices}
    elif isinstance(obj, Fascicolo):
        choices = {code.lower(): code for code, _ in Fascicolo.Stato.choices}
        labels = {label.lower(): code for code, label in Fascicolo.Stato.choices}
    else:
        choices = {}
        labels = {}

    key = raw.lower()
    if key in choices:
        return choices[key]
    if key in labels:
        return labels[key]
    return raw


@transaction.atomic
def process_operazione_archivio(operazione):
    from documenti.models import Documento
    from fascicoli.models import Fascicolo
    from protocollo.models import MovimentoProtocollo

    righe = list(
        operazione.righe.select_related(
            "documento",
            "documento__fascicolo",
            "documento__fascicolo__ubicazione",
            "fascicolo",
            "movimento_protocollo",
        )
    )
    if not righe:
        return

    unita_scarico = _get_unita_scarico() if operazione.tipo_operazione == "uscita" else None

    for riga in righe:
        obj = riga.documento or riga.fascicolo
        if obj is None:
            raise ValidationError("Ogni riga deve riferirsi a un documento o a un fascicolo.")

        if isinstance(obj, Documento):
            if obj.digitale:
                raise ValidationError(f"Il documento {obj} è digitale e non può essere movimentato fisicamente.")
            if not obj.tracciabile:
                raise ValidationError(f"Il documento {obj} non è tracciabile.")
        if isinstance(obj, Fascicolo) and not obj.ubicazione_id and operazione.tipo_operazione != "uscita":
            raise ValidationError(f"Il fascicolo {obj} deve avere un'ubicazione fisica per essere movimentato.")

        protocollo = riga.movimento_protocollo
        if protocollo is None:
            if isinstance(obj, Documento):
                protocollo = MovimentoProtocollo.objects.filter(documento=obj).order_by("data").first()
            else:
                protocollo = MovimentoProtocollo.objects.filter(fascicolo=obj).order_by("data").first()
            if protocollo:
                riga.movimento_protocollo = protocollo
                riga.save(update_fields=["movimento_protocollo"])
        if protocollo is None:
            raise ValidationError(f"{obj} non risulta protocollato.")

        stato_precedente = getattr(obj, "stato", "") or ""
        riga_updates: set[str] = set()
        if riga.stato_precedente != stato_precedente:
            riga.stato_precedente = stato_precedente
            riga_updates.add("stato_precedente")

        if operazione.tipo_operazione == "entrata":
            destinazione = riga.unita_fisica_destinazione or protocollo.ubicazione
            if destinazione is None:
                raise ValidationError(f"Definisci l'unità di arrivo per {obj} prima di registrare l'entrata.")
            if riga.unita_fisica_destinazione_id != getattr(destinazione, "pk", None):
                riga.unita_fisica_destinazione = destinazione
                riga_updates.add("unita_fisica_destinazione")
            if not riga.stato_successivo:
                raise ValidationError("Imposta lo stato successivo per ogni oggetto in entrata.")
            normalized_state = _normalize_stato_value(obj, riga.stato_successivo)
            if normalized_state is None:
                raise ValidationError("Imposta uno stato valido per l'oggetto in entrata.")
            aggiornamenti_obj: list[str] = []
            if normalized_state != getattr(obj, "stato"):
                obj.stato = normalized_state
                aggiornamenti_obj.append("stato")
            if aggiornamenti_obj:
                obj.save(update_fields=aggiornamenti_obj)
            riga_updates.add("stato_successivo")
        elif operazione.tipo_operazione == "uscita":
            sorgente = riga.unita_fisica_sorgente or protocollo.ubicazione
            if sorgente is None:
                raise ValidationError(f"Definisci l'unità di partenza per {obj} prima di registrare l'uscita.")
            if riga.unita_fisica_sorgente_id != getattr(sorgente, "pk", None):
                riga.unita_fisica_sorgente = sorgente
                riga_updates.add("unita_fisica_sorgente")
            destinazione = riga.unita_fisica_destinazione or unita_scarico
            if destinazione is None:
                raise ValidationError("Configura l'unità di destinazione per le operazioni di scarico.")
            if riga.unita_fisica_destinazione_id != getattr(destinazione, "pk", None):
                riga.unita_fisica_destinazione = destinazione
                riga_updates.add("unita_fisica_destinazione")
            default_state = _default_stato_scarico(obj)
            if not riga.stato_successivo and default_state:
                riga.stato_successivo = default_state
            normalized_state = _normalize_stato_value(obj, riga.stato_successivo)
            aggiornamenti_obj = []
            if normalized_state and normalized_state != getattr(obj, "stato"):
                obj.stato = normalized_state
                aggiornamenti_obj.append("stato")
            if aggiornamenti_obj:
                obj.save(update_fields=aggiornamenti_obj)
            riga_updates.add("stato_successivo")
        else:  # interna
            destinazione = riga.unita_fisica_destinazione
            if destinazione is None:
                raise ValidationError("Seleziona l'unità di destinazione per la movimentazione interna.")
            if riga.unita_fisica_destinazione_id != getattr(destinazione, "pk", None):
                riga.unita_fisica_destinazione = destinazione
                riga_updates.add("unita_fisica_destinazione")
            sorgente = riga.unita_fisica_sorgente or protocollo.ubicazione
            if sorgente is None:
                raise ValidationError(f"{obj} deve avere un'ubicazione di protocollo per la movimentazione interna.")
            if riga.unita_fisica_sorgente_id != getattr(sorgente, "pk", None):
                riga.unita_fisica_sorgente = sorgente
                riga_updates.add("unita_fisica_sorgente")
            aggiornamenti_obj = []
            nuovo_stato = _normalize_stato_value(obj, riga.stato_successivo) or getattr(obj, "stato")
            if nuovo_stato and nuovo_stato != getattr(obj, "stato"):
                obj.stato = nuovo_stato
                aggiornamenti_obj.append("stato")
            if isinstance(obj, Fascicolo) and obj.ubicazione_id != getattr(destinazione, "pk", None):
                obj.ubicazione = destinazione
                aggiornamenti_obj.append("ubicazione")
            if aggiornamenti_obj:
                obj.save(update_fields=aggiornamenti_obj)
            if protocollo.ubicazione_id != getattr(destinazione, "pk", None):
                protocollo.ubicazione = destinazione
                protocollo.save(update_fields=["ubicazione"])
            if not riga.stato_successivo:
                riga.stato_successivo = nuovo_stato
            riga_updates.add("stato_successivo")

        if riga_updates:
            riga.save(update_fields=list(riga_updates))