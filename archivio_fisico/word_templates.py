from __future__ import annotations

import io
import re
from typing import Any, Dict, List, Optional

from django.utils import timezone

_DOCXTPL_IMPORT_ERROR = None
try:  # pragma: no cover - import guard for optional dependency
    from docxtpl import DocxTemplate  # type: ignore
except ImportError as exc:  # pragma: no cover - handled at runtime
    DocxTemplate = None  # type: ignore[assignment]
    _DOCXTPL_IMPORT_ERROR = exc

from anagrafiche.models import Anagrafica, Cliente
from documenti.models import Documento
from fascicoli.models import Fascicolo
from protocollo.models import MovimentoProtocollo

from .models import OperazioneArchivio, UnitaFisica, VerbaleConsegnaTemplate

DATE_FMT_IT = "%d/%m/%Y"
TIME_FMT_IT = "%H:%M"
DEFAULT_FILENAME_PATTERN = "verbale_{operazione_id}_{timestamp:%Y%m%d_%H%M}.docx"


def _serialize_datetime(dt) -> Optional[Dict[str, Any]]:
    if not dt:
        return None
    local_dt = timezone.localtime(dt)
    return {
        "value": dt,
        "local": local_dt,
        "date": local_dt.date(),
        "time": local_dt.time(),
        "iso": local_dt.isoformat(),
        "date_it": local_dt.strftime(DATE_FMT_IT),
        "time_it": local_dt.strftime(TIME_FMT_IT),
        "weekday": local_dt.strftime("%A"),
    }


def _serialize_date(value) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    try:
        return {
            "value": value,
            "iso": value.isoformat(),
            "date_it": value.strftime(DATE_FMT_IT),
        }
    except Exception:
        return {"value": value, "iso": str(value), "date_it": str(value)}


def _serialize_user(user) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    full_name = user.get_full_name() or user.get_username()
    return {
        "id": user.pk,
        "username": user.get_username(),
        "full_name": full_name,
        "email": getattr(user, "email", "") or "",
    }


def _serialize_anagrafica(anagrafica: Optional[Any]) -> Optional[Dict[str, Any]]:
    if not anagrafica:
        return None
    if isinstance(anagrafica, Cliente):
        anagrafica = getattr(anagrafica, "anagrafica", None)
    if not isinstance(anagrafica, Anagrafica):
        return None
    return {
        "id": anagrafica.pk,
        "display": anagrafica.display_name(),
        "codice_fiscale": anagrafica.codice_fiscale,
        "partita_iva": getattr(anagrafica, "partita_iva", ""),
        "email": getattr(anagrafica, "email", ""),
        "telefono": getattr(anagrafica, "telefono", ""),
        "indirizzo": getattr(anagrafica, "indirizzo", ""),
        "tipo": getattr(anagrafica, "tipo", ""),
    }


def _serialize_cliente(cliente: Optional[Cliente]) -> Optional[Dict[str, Any]]:
    if not cliente:
        return None
    return {
        "id": cliente.pk,
        "note": getattr(cliente, "note", ""),
        "cliente_dal": _serialize_date(getattr(cliente, "cliente_dal", None)),
        "cliente_al": _serialize_date(getattr(cliente, "cliente_al", None)),
        "tipo_cliente": getattr(getattr(cliente, "tipo_cliente", None), "descrizione", ""),
        "anagrafica": _serialize_anagrafica(getattr(cliente, "anagrafica", None)),
    }


def _serialize_unita(unita: Optional[UnitaFisica]) -> Optional[Dict[str, Any]]:
    if not unita:
        return None
    return {
        "id": unita.pk,
        "codice": unita.codice,
        "nome": unita.nome,
        "tipo": unita.tipo,
        "tipo_label": unita.get_tipo_display(),
        "full_path": unita.full_path,
        "progressivo": unita.progressivo,
        "note": unita.note,
        "archivio_fisso": unita.archivio_fisso,
        "parent": {
            "id": unita.parent.pk,
            "codice": unita.parent.codice,
            "nome": unita.parent.nome,
            "tipo": unita.parent.get_tipo_display(),
        }
        if unita.parent else None,
    }


def _serialize_titolario(voce) -> Optional[Dict[str, Any]]:
    if not voce:
        return None
    codice_gerarchico = voce.codice_gerarchico() if hasattr(voce, "codice_gerarchico") else voce.codice
    return {
        "id": voce.pk,
        "codice": voce.codice,
        "titolo": voce.titolo,
        "codice_gerarchico": codice_gerarchico,
        "pattern_codice": getattr(voce, "pattern_codice", ""),
    }


def _serialize_movimento(mov: MovimentoProtocollo) -> Dict[str, Any]:
    return {
        "id": mov.pk,
        "direzione": mov.direzione,
        "direzione_label": mov.get_direzione_display(),
        "anno": mov.anno,
        "numero": mov.numero,
        "protocollo": f"{mov.anno}/{mov.numero:06d}",
        "data": _serialize_datetime(mov.data),
        "operatore": _serialize_user(getattr(mov, "operatore", None)),
        "destinatario": mov.destinatario,
        "ubicazione": _serialize_unita(getattr(mov, "ubicazione", None)),
        "chiuso": mov.chiuso,
        "data_rientro_prevista": _serialize_date(mov.data_rientro_prevista),
        "causale": mov.causale,
        "note": mov.note,
        "documento_id": mov.documento_id,
        "fascicolo_id": mov.fascicolo_id,
    }


def _serialize_fascicolo(fascicolo: Optional[Fascicolo], *, include_movimenti: bool = True) -> Optional[Dict[str, Any]]:
    if not fascicolo:
        return None
    data: Dict[str, Any] = {
        "id": fascicolo.pk,
        "codice": fascicolo.codice,
        "titolo": fascicolo.titolo,
        "anno": fascicolo.anno,
        "stato": fascicolo.stato,
        "stato_label": fascicolo.get_stato_display(),
        "note": fascicolo.note,
        "cliente": _serialize_cliente(getattr(fascicolo, "cliente", None)),
        "titolario": _serialize_titolario(getattr(fascicolo, "titolario_voce", None)),
        "ubicazione": _serialize_unita(getattr(fascicolo, "ubicazione", None)),
        "created_at": _serialize_datetime(getattr(fascicolo, "created_at", None)),
        "updated_at": _serialize_datetime(getattr(fascicolo, "updated_at", None)),
    }
    if include_movimenti:
        if hasattr(fascicolo, "prefetched_movimenti"):
            iterable = getattr(fascicolo, "prefetched_movimenti") or []
        else:
            manager = getattr(fascicolo, "movimenti_protocollo", None)
            iterable = manager.all() if manager is not None else []
        data["movimenti_protocollo"] = [_serialize_movimento(m) for m in iterable]
    return data


def _serialize_documento(documento: Optional[Documento], *, include_movimenti: bool = True) -> Optional[Dict[str, Any]]:
    if not documento:
        return None
    data: Dict[str, Any] = {
        "id": documento.pk,
        "codice": documento.codice,
        "descrizione": documento.descrizione,
        "data_documento": _serialize_date(getattr(documento, "data_documento", None)),
        "stato": documento.stato,
        "stato_label": documento.get_stato_display(),
        "tipo_codice": getattr(getattr(documento, "tipo", None), "codice", ""),
        "tipo_nome": getattr(getattr(documento, "tipo", None), "nome", ""),
        "cliente": _serialize_anagrafica(getattr(documento, "cliente", None)),
        "fascicolo": _serialize_fascicolo(getattr(documento, "fascicolo", None), include_movimenti=False),
        "titolario": _serialize_titolario(getattr(documento, "titolario_voce", None)),
        "note": documento.note,
        "tags": documento.tags,
    }
    if include_movimenti:
        if hasattr(documento, "prefetched_movimenti"):
            iterable = getattr(documento, "prefetched_movimenti") or []
        else:
            manager = getattr(documento, "movimenti", None)
            iterable = manager.all() if manager is not None else []
        data["movimenti_protocollo"] = [_serialize_movimento(m) for m in iterable]
    return data


def _sanitize_filename(name: str) -> str:
    sanitized = re.sub(r"[\\/:*?\"<>|]+", "-", name)
    sanitized = sanitized.strip().strip(".-") or "verbale"
    return sanitized


def _build_filename(template: VerbaleConsegnaTemplate, operazione: OperazioneArchivio, *, context: Dict[str, Any]) -> str:
    timestamp = timezone.localtime()
    pattern = template.filename_pattern or DEFAULT_FILENAME_PATTERN
    payload = {
        "operazione_id": operazione.pk,
        "operazione_tipo": operazione.tipo_operazione,
        "operazione_tipo_display": operazione.get_tipo_operazione_display(),
        "timestamp": timestamp,
        "template_slug": template.slug,
    }
    payload.update(context.get("extra", {}))
    try:
        name = pattern.format(**payload)
    except Exception:
        name = DEFAULT_FILENAME_PATTERN.format(operazione_id=operazione.pk, timestamp=timestamp)
    if not name.lower().endswith(".docx"):
        name += ".docx"
    base, ext = name[:-5], ".docx"
    base = _sanitize_filename(base)
    return f"{base}{ext}"


def build_verbale_context(operazione: OperazioneArchivio) -> Dict[str, Any]:
    righe: List[Dict[str, Any]] = []
    sorgenti_map: Dict[int, Dict[str, Any]] = {}
    destinazioni_map: Dict[int, Dict[str, Any]] = {}
    for riga in operazione.righe.all():
        documento = _serialize_documento(getattr(riga, "documento", None))
        fascicolo = _serialize_fascicolo(getattr(riga, "fascicolo", None))
        movimento_serializzato = (
            _serialize_movimento(riga.movimento_protocollo)
            if getattr(riga, "movimento_protocollo_id", None)
            else None
        )
        protocollo = None
        if movimento_serializzato:
            protocollo = movimento_serializzato
        else:
            if documento and documento.get("movimenti_protocollo"):
                protocollo = documento["movimenti_protocollo"][-1]
            elif fascicolo and fascicolo.get("movimenti_protocollo"):
                protocollo = fascicolo["movimenti_protocollo"][-1]
        unita_sorgente = _serialize_unita(getattr(riga, "unita_fisica_sorgente", None))
        unita_destinazione = _serialize_unita(getattr(riga, "unita_fisica_destinazione", None))
        if unita_sorgente and unita_sorgente.get("id") is not None:
            sorgenti_map[unita_sorgente["id"]] = unita_sorgente
        if unita_destinazione and unita_destinazione.get("id") is not None:
            destinazioni_map[unita_destinazione["id"]] = unita_destinazione
        righe.append(
            {
                "id": riga.pk,
                "stato_precedente": riga.stato_precedente,
                "stato_successivo": riga.stato_successivo,
                "note": riga.note,
                "documento": documento,
                "fascicolo": fascicolo,
                "movimento_protocollo": movimento_serializzato,
                "protocollo": protocollo,
                "unita_sorgente": unita_sorgente,
                "unita_destinazione": unita_destinazione,
            }
        )

    movimenti_riga = [row["movimento_protocollo"] for row in righe if row.get("movimento_protocollo")]
    movimento = None
    if movimenti_riga:
        ids = {m.get("id") for m in movimenti_riga if m.get("id") is not None}
        if len(ids) == 1:
            movimento = movimenti_riga[0]
    context = {
        "timestamp": _serialize_datetime(timezone.now()),
        "operazione": {
            "id": operazione.pk,
            "tipo": operazione.tipo_operazione,
            "tipo_label": operazione.get_tipo_operazione_display(),
            "data_ora": _serialize_datetime(operazione.data_ora),
            "note": operazione.note,
            "referente_interno": _serialize_user(getattr(operazione, "referente_interno", None)),
            "referente_esterno": _serialize_anagrafica(getattr(operazione, "referente_esterno", None)),
        },
        "unita": {
            "sorgente": next(iter(sorgenti_map.values()), None),
            "destinazione": next(iter(destinazioni_map.values()), None),
            "sorgenti": list(sorgenti_map.values()),
            "destinazioni": list(destinazioni_map.values()),
        },
        "movimento_protocollo": movimento,
        "righe": righe,
    }
    return context


def render_verbale_consegna(
    template: VerbaleConsegnaTemplate,
    operazione: OperazioneArchivio,
    *,
    extra_context: Optional[Dict[str, Any]] = None,
) -> tuple[bytes, str]:
    if DocxTemplate is None:  # pragma: no cover - defensive
        raise RuntimeError("La libreria docxtpl non è installata") from _DOCXTPL_IMPORT_ERROR
    doc = DocxTemplate(template.file_template.path)
    context = build_verbale_context(operazione)
    if extra_context:
        context.setdefault("extra", {}).update(extra_context)
        context.update(extra_context)
    doc.render(context)
    buffer = io.BytesIO()
    doc.save(buffer)
    filename = _build_filename(template, operazione, context=context)
    return buffer.getvalue(), filename
