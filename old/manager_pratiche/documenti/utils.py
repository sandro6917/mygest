from typing import Any, Dict, TYPE_CHECKING
import os
import re
import unicodedata
from django.conf import settings
from django.utils.text import slugify

if TYPE_CHECKING:
    from .models import Documento  # solo per hint

TOKEN_RE = re.compile(r"\{([^{}]+)\}")


def _slug(v: str) -> str:
    return slugify(v or "", allow_unicode=False)


def _sanitize_segment(seg: str) -> str:
    if not seg:
        return "n-a"
    # rimuove separatori path e normalizza
    seg = seg.replace("/", "-").replace(os.sep, "-")
    seg = unicodedata.normalize("NFKD", seg).encode("ascii", "ignore").decode("ascii")
    seg = re.sub(r"[^A-Za-z0-9._-]+", "-", seg)
    seg = re.sub(r"-{2,}", "-", seg).strip("-._")
    return seg or "n-a"


def _ensure_length(name: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    if len(name) <= max_len:
        return name
    base, dot, ext = name.rpartition(".")
    if dot and len(ext) < max_len - 1:
        # taglio il base preservando l'estensione
        room = max_len - (len(ext) + 1)
        return (base[:room] if room > 0 else "x") + "." + ext
    return name[:max_len]


def _build_dyn_cache(doc) -> Dict[str, Any]:
    if hasattr(doc, "_dyn_cache"):
        return doc._dyn_cache
    # import lazy per evitare circolare
    from .models import AttributoValore  # noqa
    dyn: Dict[str, Any] = {}
    for av in AttributoValore.objects.filter(documento=doc).select_related("definizione"):
        code = av.definizione.codice.lower()
        value = getattr(av, "valore", None)
        dyn[code] = value
    doc._dyn_cache = dyn
    return dyn


def build_document_filename(doc, original_name: str, pattern: str | None = None) -> str:
    """
    Genera il nome file (basename) in base a pattern esteso.
    """
    dyn = _build_dyn_cache(doc)
    tipo = getattr(doc, "tipo", None)
    ext = os.path.splitext(original_name)[1].lower() or ".pdf"

    if not pattern:
        pattern = (
            getattr(tipo, "nome_file_pattern", "") or
            getattr(settings, "DOCUMENTI_FILE_PATTERN_DEFAULT", "documento_{id}.pdf")
        )

    # Se pattern non contiene estensione esplicita, aggiungi quella originale
    if not os.path.splitext(os.path.basename(pattern))[1]:
        pattern += ext

    # Ricorsione limitata (evita loop)
    def resolve_token(raw: str, depth: int = 0) -> str:
        if depth > 5:
            return ""
        token = raw.strip()

        # default: {default:<inner>|FALLBACK}
        if token.startswith("default:"):
            inner_def = token[len("default:"):]
            if "|" in inner_def:
                inner, fallback = inner_def.split("|", 1)
            else:
                inner, fallback = inner_def, ""
            val = resolve_token(inner, depth + 1)
            return val or _sanitize_segment(fallback)

        # upper/lower trasformazioni
        for prefix, fn in (("upper:", str.upper), ("lower:", str.lower)):
            if token.startswith(prefix):
                inner = token[len(prefix):]
                val = resolve_token(inner, depth + 1)
                return fn(val)

        # if / ifnot sintassi: if:attr:codice:TEXT   |  if:field:campo:TEXT
        if token.startswith("if:") or token.startswith("ifnot:"):
            neg = token.startswith("ifnot:")
            body = token[6:] if neg else token[3:]
            parts = body.split(":", 2)
            if len(parts) == 3:
                kind, identifier, text_block = parts
                present = False
                if kind == "attr":
                    val = dyn.get(identifier.lower())
                    present = val not in (None, "")
                elif kind == "field":
                    val = getattr(doc, identifier, None)
                    present = val not in (None, "")
                if neg:
                    present = not present
                return expand(text_block, depth + 1) if present else ""
            return ""

        # attr:<code>[|DEFAULT]
        if token.startswith("attr:"):
            rest = token[5:]
            code, dflt = (rest.split("|", 1) + [""])[:2] if "|" in rest else (rest, "")
            val = dyn.get(code.lower())
            if val in (None, ""):
                return _sanitize_segment(dflt) if dflt else ""
            return _sanitize_segment(str(val))

        # slug:<field>
        if token.startswith("slug:"):
            field = token[5:]
            val = getattr(doc, field, "") or ""
            return _slug(str(val))

        # tipo.sotto
        if token.startswith("tipo.") and tipo:
            sub = token.split(".", 1)[1]
            val = getattr(tipo, sub, "")
            return _sanitize_segment(str(val))

        # unique placeholder (rimane vuoto qui; la fase di salvataggio garantisce unicità)
        if token == "unique":
            return ""

        # field con possibile formato data: field:%Y%m%d
        fmt = None
        if ":" in token:
            fieldname, fmt = token.split(":", 1)
        else:
            fieldname = token

        if hasattr(doc, fieldname):
            v = getattr(doc, fieldname)
            if isinstance(v, (datetime.datetime, datetime.date)):
                if fmt:
                    try:
                        return v.strftime(fmt)
                    except Exception:
                        return v.isoformat()
                return v.isoformat()
            if v is None:
                return ""
            return _sanitize_segment(str(v))

        return ""

    def expand(text: str, depth: int = 0) -> str:
        return TOKEN_RE.sub(lambda m: resolve_token(m.group(1), depth + 1), text)

    result = expand(pattern)
    # pulizia underscore
    result = re.sub(r"_+", "_", result).strip("_")
    # garantisci estensione
    if not result.lower().endswith(ext):
        result += ext
    # limita lunghezza
    max_len = getattr(settings, "DOCUMENTI_FILENAME_MAX_LEN", 140)
    result = _ensure_length(result, max_len)
    return result