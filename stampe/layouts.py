from __future__ import annotations
import datetime
from django.utils.dateparse import parse_date
from reportlab.lib.units import mm
from anagrafiche.models import Anagrafica
from documenti.models import AttributoValore
import re
from typing import Any, Optional

def _fmt_date(d):
    if isinstance(d, datetime.date):
        return d.strftime("%d/%m/%Y")
    if isinstance(d, str):
        x = parse_date(d)
        return x.strftime("%d/%m/%Y") if x else ""
    return ""

def _get_margin(c):
    # legge il margine centralizzato impostato in services.build_pdf, fallback 3mm
    return getattr(c, "_margin_pt", 3 * mm)

def _wrap_text(c, text: str, max_width_pt: float) -> list[str]:
    # wrapping semplice basato sulla larghezza del font corrente
    if not text:
        return [""]
    font_name = getattr(c, "_fontname", "Calibri")
    font_size = getattr(c, "_fontsize", 10)
    words = str(text).split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if c.stringWidth(test, font_name, font_size) <= max_width_pt:
            line = test
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines or [""]

def _draw_wrapped(
    c,
    x: float,
    y: float,
    text: str,
    max_width_pt: float,
    line_spacing_pt: float,
    max_lines: int = 1,
    ellipsis: bool = True,
) -> float:
    """
    Disegna il testo wrappato fino a max_lines.
    Se il testo eccede e ellipsis=True aggiunge '…' all'ultima riga (adattata alla larghezza).
    Ritorna la nuova y dopo l'ultima riga disegnata.
    """
    lines = _wrap_text(c, text, max_width_pt)
    overflow = len(lines) > max_lines
    lines = lines[:max_lines]
    if overflow and ellipsis and lines:
        last = lines[-1].rstrip()
        # Aggiunge ellissi, accorciando finché entra
        while last and c.stringWidth(last + "…", getattr(c, "_fontname", "Helvetica"), getattr(c, "_fontsize", 10)) > max_width_pt:
            last = last[:-1]
        lines[-1] = (last + "…") if last else "…"
    for ln in lines:
        c.drawString(x, y, ln)
        y -= line_spacing_pt
        if y <= 0:  # sicurezza: evita y negativa
            break
    return y

def _normalize_code(code: str) -> str:
    return (code or "").strip().lower()

def _extract_fk_id(raw: Any) -> Optional[int]:
    """
    Prova a ricavare un intero da varie forme:
    - int diretto
    - stringa con cifre (anche se contiene altri caratteri)
    - lista/tupla: prende il primo elemento
    - dict: chiavi comuni ('id','pk','value')
    """
    if raw in (None, ""):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, (list, tuple)) and raw:
        return _extract_fk_id(raw[0])
    if isinstance(raw, dict):
        for k in ("id", "pk", "value"):
            if k in raw:
                return _extract_fk_id(raw[k])
        return None
    if isinstance(raw, str):
        s = raw.strip()
        # estrai prima sequenza di cifre
        m = re.search(r"\d+", s)
        if m:
            try:
                return int(m.group(0))
            except ValueError:
                return None
    return None

# Layout generico (fallback)
def layout_generic(instance, c, width, height):
    margin = 3 * mm
    y = height - margin
    c.setFont("Helvetica-Bold", 12)
    title = getattr(instance, "get_etichetta_title", lambda: type(instance).__name__)()
    c.drawString(margin, y, str(title)[:48])
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    subtitle = getattr(instance, "get_etichetta_subtitle", lambda: f"ID #{instance.pk}")()
    c.drawString(margin, y, str(subtitle)[:60])
    c.setFont("Helvetica-Oblique", 8)
    c.drawRightString(width - margin, 4 * mm, f"ID #{getattr(instance,'pk','?')}")

# Documento: mostra tipo, cliente, parte (attr dinamico), data/rep
def layout_documento(instance, c, width, height):
    margin = _get_margin(c)
    y = height - margin
    max_width = width - 2 * margin

    tipo = getattr(getattr(instance, "tipo", None), "nome", "") or "Documento"
    cliente = getattr(instance, "cliente", None)
    descrizione = getattr(instance, "descrizione", "") or tipo

    def _anag(a):
        if not a:
            return ""
        for f in ("denominazione", "ragione_sociale"):
            v = getattr(a, f, None)
            if v:
                return v
        return f"{getattr(a,'cognome','')} {getattr(a,'nome','')}".strip() or f"Anagrafica #{a.pk}"

    dyn = {
        _normalize_code(av.definizione.codice): av.valore
        for av in AttributoValore.objects.filter(documento=instance).select_related("definizione")
    }

    # alias parte / controparte
    def _pick(d, *aliases):
        for al in aliases:
            if al in d and d[al] not in (None, ""):
                return d[al]
        return None

    raw_parte = _pick(dyn, "parte_atto", "parte")
    parte_id = _extract_fk_id(raw_parte)
    parte = Anagrafica.objects.filter(pk=parte_id).first() if parte_id else None

    raw_controparte = _pick(dyn, "controparte_atto", "controparte")
    controparte_id = _extract_fk_id(raw_controparte)
    controparte = Anagrafica.objects.filter(pk=controparte_id).first() if controparte_id else None

    raw_notaio = _pick(dyn, "notaio_atto", "notaio")
    notaio_id = _extract_fk_id(raw_notaio)
    notaio = Anagrafica.objects.filter(pk=notaio_id).first() if notaio_id else None

    data_atto = _fmt_date(dyn.get("data_atto")) or _fmt_date(getattr(instance, "data_documento", None))
    rep = dyn.get("repertorio_atto") or dyn.get("num_reg_atto") or ""
    rac = dyn.get("raccolta_atto") or dyn.get("num_rac_atto") or ""

    # Descrizione / Titolo (max 2 righe)
    c.setFont("Helvetica-Bold", 10)
    y = _draw_wrapped(c, margin, y, str(descrizione), max_width, line_spacing_pt=4 * mm, max_lines=2)
    # Cliente
    c.setFont("Helvetica", 8)
    if cliente and y > margin:
        y = _draw_wrapped(c, margin, y, f"Cliente: {_anag(cliente)}", max_width, line_spacing_pt=3.5 * mm, max_lines=2)
    # Parte
    #if parte and y > margin:
    #    y = _draw_wrapped(c, margin, y, f"Parte: {_anag(parte)}", max_width, line_spacing_pt=3.5 * mm, max_lines=2)
    # Controparte
    if controparte and y > margin:
        y = _draw_wrapped(c, margin, y, f"Controparte: {_anag(controparte)}", max_width, line_spacing_pt=3.5 * mm, max_lines=2)

    # Notaio (una riga, ellissi se lunga)
    if notaio and y > margin:
        y = _draw_wrapped(c, margin, y, f"Notaio: {_anag(notaio)}", max_width, line_spacing_pt=3.5 * mm, max_lines=1)

    # Data / Repertorio / Raccolta (una riga, ellissi se lunga)
    if y > margin:
        info_line = f"Data: {data_atto}  Rep: {rep}  Rac: {rac}".strip()
        y = _draw_wrapped(c, margin, y, info_line, max_width, line_spacing_pt=3 * mm, max_lines=1)        

    # ID
    c.setFont("Helvetica-Oblique", 8)
    c.drawRightString(width - margin, 4 * mm, f"ID #{instance.pk}")

# Fascicolo (placeholder, adatta ai tuoi campi)
def layout_fascicolo(instance, c, width, height):
    margin = 3 * mm; y = height - margin
    c.setFont("Helvetica-Bold", 12)
    titolo = getattr(instance, "titolo", None) or "Fascicolo"
    c.drawString(margin, y, str(titolo)[:48]); y -= 6*mm
    c.setFont("Helvetica", 9)
    codice = getattr(instance, "codice", "") or f"ID #{instance.pk}"
    c.drawString(margin, y, f"Cod: {codice}"[:60])

# Pratica (placeholder)
def layout_pratica(instance, c, width, height):
    margin = 3 * mm; y = height - margin
    c.setFont("Helvetica-Bold", 12)
    titolo = getattr(instance, "oggetto", None) or "Pratica"
    c.drawString(margin, y, str(titolo)[:48]); y -= 6*mm
    c.setFont("Helvetica", 9)
    numero = getattr(instance, "numero", "") or f"ID #{instance.pk}"
    c.drawString(margin, y, f"N: {numero}"[:60])

# Unità fisica (placeholder)
def layout_unita_fisica(instance: Any, c, width, height):
    margin = _get_margin(c)
    y = height - margin
    max_width = width - 2 * margin

    tipo = getattr(instance, "get_tipo_display", lambda: "Unità")()
    codice = getattr(instance, "codice", "") or ""
    nome = getattr(instance, "nome", "") or ""
    path = getattr(instance, "full_path", "") or ""

    # Titolo: Tipo • Codice
    c.setFont("Helvetica-Bold", 12)
    y = _draw_wrapped(c, margin, y, f"{tipo} • {codice}", max_width, line_spacing_pt=5, max_lines=1)
    # Nome
    c.setFont("Helvetica", 9)
    y = _draw_wrapped(c, margin, y, nome, max_width, line_spacing_pt=4, max_lines=2)
    # Path
    if path:
        c.setFont("Helvetica", 8)
        _draw_wrapped(c, margin, y, path, max_width, line_spacing_pt=3.5, max_lines=2)

    # ID in basso a destra
    c.setFont("Helvetica-Oblique", 8)
    c.drawRightString(width - margin, 3 * mm, f"ID #{getattr(instance,'pk','?')}")