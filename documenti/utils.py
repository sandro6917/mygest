from typing import Any, Dict, Optional
import os
import re
import unicodedata
import datetime  # fix: usi datetime.date/datetime.timedelta in basso
from django.utils.text import slugify
from django.apps import apps  # evita import dei modelli a livello modulo

_token_rx = re.compile(r"\{([^\}]+)\}")

def _parse_iso_date(val: str) -> Optional[datetime.date]:
    # Supporta "YYYY-MM-DD" o ISO datetime
    try:
        if "T" in val:
            return datetime.datetime.fromisoformat(val).date()
        return datetime.date.fromisoformat(val)
    except Exception:
        return None

def _format_value(value: Any, fmt: Optional[str]) -> str:
    if value is None:
        return ""
    if fmt:
        # data/datetime o stringa data ISO
        if isinstance(value, (datetime.date, datetime.datetime)):
            d = value.date() if isinstance(value, datetime.datetime) else value
            return d.strftime(fmt)
        if isinstance(value, str):
            d = _parse_iso_date(value)
            if d:
                return d.strftime(fmt)
        # fallback: ignora il fmt su tipi non data
    return str(value)

def _attrs_map(doc: Any) -> Dict[str, Any]:
    """Mappa codice attributo -> valore (grezzo JSON) per il documento."""
    AttributoDefinizione = apps.get_model("documenti", "AttributoDefinizione")
    AttributoValore = apps.get_model("documenti", "AttributoValore")
    defs = AttributoDefinizione.objects.filter(tipo_documento=doc.tipo).only("id", "codice", "tipo_dato")
    by_id = {d.id: d for d in defs}
    out: Dict[str, Any] = {}
    for av in AttributoValore.objects.filter(documento=doc, definizione_id__in=by_id.keys()).only("definizione_id", "valore"):
        d = by_id.get(av.definizione_id)
        if not d:
            continue
        out[d.codice] = av.valore
    return out

def build_document_filename(doc: Any, original_name: str) -> str:
    """
    Costruisce il nome file finale in base a DocumentiTipo.nome_file_pattern.
    Token supportati:
      - {id}, {tipo.codice}
      - {data_documento:%Y%m%d} (fmt opzionale)
      - {slug:descrizione}
      - {attr:<codice>} e {attr:<codice>:%Y%m%d} (fmt opzionale per date)
      - {uattr:<codice>} e {uattr:<codice>:%Y%m%d} -> inserisce "_<valore>" solo se l'attributo esiste
      - {attrobj:<attr_codice>:<app_label>:<model_name>:<field_name>} -> recupera il valore del campo specificato
        dall'istanza del modello collegata tramite l'id memorizzato nell'attributo.
      - {upper:TEXT} / {lower:TEXT} -> converte TEXT in maiuscolo/minuscolo (non annidato)
    Se il pattern è vuoto o non definito, il nome file sarà "<codice-documento>.<ext>".
    Se il risultato è vuoto, si usa come fallback il codice del documento.
    L'estensione del file viene preservata da original_name; se mancante, si usa ".bin".
    
    """
    base, ext = os.path.splitext(original_name or "")
    ext = ext or ".bin"

    pattern = (getattr(doc.tipo, "nome_file_pattern", "") or "").strip()
    if not pattern:
        # fallback minimale: <codice-documento><ext>
        return f"{(doc.codice or 'DOC')}{ext}"

    attrs = _attrs_map(doc)

    def repl(m: re.Match) -> str:
        token = m.group(1).strip()

        # uattr:code[:fmt] -> "_" + valore se presente
        if token.startswith("uattr:"):
            parts = token.split(":", 2)
            code = parts[1].strip() if len(parts) > 1 else ""
            fmt = parts[2] if len(parts) > 2 else None
            s = _format_value(attrs.get(code), fmt)
            return f"_{s}" if s else ""

        # attr:code[:fmt]
        if token.startswith("attr:"):
            # split massimo 2 per tenere insieme eventuale fmt con i suoi ':'
            parts = token.split(":", 2)
            code = parts[1].strip() if len(parts) > 1 else ""
            fmt = parts[2] if len(parts) > 2 else None
            val = attrs.get(code)
            return _format_value(val, fmt)

        # data_documento[:fmt]
        if token.startswith("data_documento"):
            fmt = None
            parts = token.split(":", 1)
            if len(parts) == 2:
                fmt = parts[1]
            return _format_value(getattr(doc, "data_documento", None), fmt)

        # tipo.codice
        if token == "tipo.codice":
            return getattr(getattr(doc, "tipo", None), "codice", "") or ""

        # id
        if token == "id":
            return str(getattr(doc, "id", "") or "")

        # slug:...
        if token.startswith("slug:"):
            sub = token.split(":", 1)[1].strip()
            # slug:attr:<codice>
            if sub.startswith("attr:"):
                code = sub.split(":", 1)[1].strip()
                val = attrs.get(code)
                s = _format_value(val, None)
                return slugify(s)[:10] if s else ""
            # slug:attrobj:<attr_codice>:<app_label>:<model_name>:display_name
            if sub.startswith("attrobj:"):
                parts = sub.split(":", 4)
                if len(parts) == 5:
                    attr_code, app_label, model_name, field_name = parts[1:]
                    obj_id = attrs.get(attr_code)
                    if obj_id:
                        Model = apps.get_model(app_label, model_name)
                        try:
                            # Se il campo richiesto è un metodo/proprietà, non usare .only()
                            if field_name == "display_name":
                                obj = Model.objects.get(id=obj_id)
                                # display_name può essere metodo o property
                                val = getattr(obj, "display_name")
                                s = val() if callable(val) else val
                            else:
                                obj = Model.objects.only(field_name).get(id=obj_id)
                                s = str(getattr(obj, field_name, "") or "")
                            return slugify(s)[:10] if s else ""
                        except Model.DoesNotExist:
                            return ""
            # slug:<campo_doc> (fallback generico)
            if sub == "descrizione":
                return slugify(getattr(doc, "descrizione", "") or "")[:10]
            return slugify(str(getattr(doc, sub, "") or ""))[:10]

        # upper:TEXT / lower:TEXT (semplice, non annidato)
        if token.startswith("upper:"):
            return (token.split(":", 1)[1] or "").upper()
        if token.startswith("lower:"):
            return (token.split(":", 1)[1] or "").lower()

        # attrobj:<attr_codice>:<app_label>:<model_name>:<field_name>
        if token.startswith("attrobj:"):
            # Esempio: attrobj:cliente:anagrafiche:Anagrafica:codice
            parts = token.split(":", 4)
            if len(parts) == 5:
                attr_code, app_label, model_name, field_name = parts[1:]
                obj_id = attrs.get(attr_code)
                if obj_id:
                    Model = apps.get_model(app_label, model_name)
                    try:
                        obj = Model.objects.only(field_name).get(id=obj_id)
                        return str(getattr(obj, field_name, "") or "")
                    except Model.DoesNotExist:
                        return ""
            return ""

        # sconosciuto -> stringa vuota
        return ""

    name = _token_rx.sub(repl, pattern).strip().strip("_- ")
    # fallback se vuoto
    if not name:
        name = (doc.codice or "DOC")
    return f"{name}{ext}"