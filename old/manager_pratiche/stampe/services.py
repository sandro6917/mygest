from __future__ import annotations
import io
from typing import Any, Iterable, Tuple, Optional, List, Dict, Union
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from .models import StampaFormato, StampaModulo, StampaCampo, StampaLista, StampaColonna
from reportlab.graphics.barcode import code128, code39, eanbc, qr as rl_qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from types import SimpleNamespace
from django.shortcuts import get_object_or_404

# ---- Utilities base (compat vecchia API) ----
SIZES = {
    "dymo_99012": (89.0, 36.0),  # legacy
    "dymo_99010": (89.0, 28.0),
}

def size_to_points(size_key: str) -> Tuple[float, float]:
    w_mm, h_mm = SIZES.get(size_key, SIZES["dymo_99012"])
    return (w_mm * mm, h_mm * mm)

def build_pdf(instance, layout_callable, size_key: str = "dymo_99012", margin_mm: Optional[float] = None) -> bytes:
    width, height = size_to_points(size_key)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    if margin_mm is None:
        margin_mm = 7.0
    c._margin_pt = float(margin_mm) * mm
    c._size_key = size_key
    layout_callable(instance, c, width, height)
    c.showPage()
    c.save()
    return buf.getvalue()

# ---- Nuovo motore DB-driven ----
def _pagesize_points(fmt: StampaFormato) -> Tuple[float, float]:
    w = fmt.larghezza_mm * mm
    h = fmt.altezza_mm * mm
    # l'orientamento è semantico; le dimensioni sono già coerenti con ciò che vuoi stampare
    return (w, h)

def _font_for(obj_font_name: Optional[str], obj_font_size: Optional[float], fmt: StampaFormato, mod: StampaModulo) -> Tuple[str, float]:
    name = obj_font_name or mod.font_nome or fmt.font_nome_default or "Helvetica"
    size = obj_font_size or mod.font_size or fmt.font_size_default or 10.0
    return name, float(size)

def _dynamic_attr_value(instance: Any, code: str):
    # Recupera il valore dell’attributo dinamico (per codice)
    try:
        vals = instance.attributi_valori.select_related("definizione")
        v = vals.filter(definizione__codice=code).first()
        return None if v is None else v.valore
    except Exception:
        # Compat se instance non è Documento o non ha attributi dinamici
        return None

def _attrs_namespace(instance: Any) -> SimpleNamespace:
    try:
        mapping = {
            v.definizione.codice: v.valore
            for v in instance.attributi_valori.select_related("definizione").all()
        }
        return SimpleNamespace(**mapping)
    except Exception:
        return SimpleNamespace()

def _resolve_attr(instance: Any, path: str) -> Any:
    # Estende path con supporto "attr.<codice>"
    parts = (path or "").split(".")
    if not parts or not path:
        return None
    if parts[0] in ("attr", "attrs"):  # attributi dinamici per codice
        return _dynamic_attr_value(instance, parts[1]) if len(parts) > 1 else None
    cur = instance
    for part in parts:
        if not part:
            continue
        cur = cur.get(part) if isinstance(cur, dict) else getattr(cur, part, None)
        if cur is None:
            break
    return cur() if callable(cur) else cur

def _to_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val)

def _wrap_lines(c: canvas.Canvas, text: str, max_width: float, font: Tuple[str, float]) -> list[str]:
    if not text or not max_width:
        return [text or ""]
    name, size = font
    words = str(text).split()
    lines, line = [], ""
    for w in words:
        t = (line + " " + w).strip()
        if c.stringWidth(t, name, size) <= max_width:
            line = t
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines or [""]

def _draw_text(c: canvas.Canvas, x: float, baseline_y: float, text: str, width: Optional[float], align: str, font: Tuple[str, float], max_lines: int):
    name, size = font
    c.setFont(name, size)
    lines = [text]
    if width:
        lines = _wrap_lines(c, text, width, font)
    lines = lines[: max_lines or 1]
    line_height = size * 1.2
    y = baseline_y
    for ln in lines:
        if width:
            if align == StampaCampo.Align.CENTER:
                c.drawCentredString(x + width / 2, y, ln)
            elif align == StampaCampo.Align.RIGHT:
                c.drawRightString(x + width, y, ln)
            else:
                c.drawString(x, y, ln)
        else:
            # singolo punto di ancoraggio
            if align == StampaCampo.Align.RIGHT:
                c.drawRightString(x, y, ln)
            elif align == StampaCampo.Align.CENTER:
                c.drawCentredString(x, y, ln)
            else:
                c.drawString(x, y, ln)
        y -= line_height

def _value_from_campo(instance: Any, campo: StampaCampo) -> str:
    # Priorità: attr_path -> template -> static
    if campo.attr_path:
        v = _resolve_attr(instance, campo.attr_path)
        if v not in (None, ""):
            return _to_str(v)
    if campo.template:
        try:
            ctx = {"obj": instance, "attr": _attrs_namespace(instance)}
            return (campo.template or "").format(**ctx)
        except Exception:
            pass
    return _to_str(campo.static_value)

def _draw_barcode(c: canvas.Canvas, campo: StampaCampo, x_pt: float, top_y_pt: float, value: str):
    if not value:
        return
    bw = max(0.1, float(campo.barcode_bar_width_mm or 0.3)) * mm
    bh = max(5.0, float(campo.barcode_height_mm or 12.0)) * mm
    std = (campo.barcode_standard or "code128").lower()

    try:
        if std == "code39":
            widget = code39.Standard39(value, barWidth=bw, barHeight=bh, checksum=False, stop=True)
        elif std == "ean13":
            # EAN-13 richiede 12 o 13 cifre
            digits = "".join(ch for ch in value if ch.isdigit())
            if len(digits) < 12:
                return
            digits = digits[:13]
            widget = eanbc.Ean13BarcodeWidget(digits, barWidth=bw, barHeight=bh)
        else:  # code128 default
            widget = code128.Code128(value, barWidth=bw, barHeight=bh)
        # drawOn usa coordinate in basso-sinistra
        y_draw = top_y_pt - widget.height
        widget.drawOn(c, x_pt, y_draw)
    except Exception:
        pass

def _draw_qrcode(c: canvas.Canvas, campo: StampaCampo, x_pt: float, top_y_pt: float, value: str):
    if not value:
        return
    size_pt = max(8.0, float(campo.qr_size_mm or 24.0)) * mm
    level = (campo.qr_error or "M")
    try:
        widget = rl_qr.QrCodeWidget(value, barLevel=level)
        minx, miny, maxx, maxy = widget.getBounds()
        w = maxx - minx
        h = maxy - miny
        sx = size_pt / w
        sy = size_pt / h
        d = Drawing(size_pt, size_pt, transform=[sx, 0, 0, sy, 0, 0])
        d.add(widget)
        # renderPDF.draw usa basso-sinistra
        y_draw = top_y_pt - size_pt
        renderPDF.draw(d, c, x_pt, y_draw)
    except Exception:
        pass

def render_modulo_pdf(instance: Any, modulo: StampaModulo) -> bytes:
    fmt = modulo.formato
    page_w, page_h = _pagesize_points(fmt)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))

    mt = fmt.margine_top_mm * mm
    ml = fmt.margine_left_mm * mm
    default_font = _font_for(None, None, fmt, modulo)

    for campo in modulo.campi.filter(visibile=True).order_by("ordine", "id"):
        x_pt = ml + campo.x_mm * mm
        top_y_pt = page_h - mt - campo.y_mm * mm

        if campo.tipo in (StampaCampo.Tipo.BARCODE, StampaCampo.Tipo.QRCODE):
            value = _value_from_campo(instance, campo)
            if campo.tipo == StampaCampo.Tipo.BARCODE:
                _draw_barcode(c, campo, x_pt, top_y_pt, value)
            else:
                _draw_qrcode(c, campo, x_pt, top_y_pt, value)
            continue

        # testo
        font_name = campo.font_nome or default_font[0]
        font_size = float(campo.font_size or default_font[1])
        name = font_name
        if campo.bold and campo.italic:
            name = "Helvetica-Oblique"
        elif campo.bold:
            name = "Helvetica-Bold" if "Helvetica" in font_name else font_name
        elif campo.italic:
            name = "Helvetica-Oblique" if "Helvetica" in font_name else font_name

        val = _value_from_campo(instance, campo)
        width_pt = campo.larghezza_mm * mm if campo.larghezza_mm else None
        _draw_text(c, x_pt, top_y_pt, _to_str(val), width_pt, campo.align, (name, font_size), campo.max_lines or 1)

    c.showPage()
    c.save()
    return buf.getvalue()

def get_modulo_or_404(app_label: str, model: str, slug: Optional[str]) -> StampaModulo:
    from django.shortcuts import get_object_or_404
    if slug:
        return get_object_or_404(StampaModulo, app_label=app_label, model_name=model, slug=slug, attivo=True)
    # default per app/model
    try:
        return StampaModulo.objects.get(app_label=app_label, model_name=model, is_default=True, attivo=True)
    except ObjectDoesNotExist:
        # se manca default, prendi il primo attivo
        return get_object_or_404(StampaModulo, app_label=app_label, model_name=model, attivo=True)

def _doc_tipo_from_instance(instance: Any):
    # Rileva il TipoDocumento dall’istanza se presente (Documento.tipo)
    return getattr(instance, "tipo", None)

def get_modulo_for_instance(instance: Any, slug: Optional[str] = None) -> StampaModulo:
    meta = instance._meta
    app_label = meta.app_label
    model_name = meta.model_name

    qs = StampaModulo.objects.filter(app_label=app_label, model_name=model_name, attivo=True)
    doc_tipo = _doc_tipo_from_instance(instance)

    if slug:
        # match più specifico: slug + tipo
        if doc_tipo is not None:
            m = qs.filter(slug=slug, documento_tipo=doc_tipo).order_by("-is_default", "id").first()
            if m:
                return m
        # fallback: slug senza tipo
        m = qs.filter(slug=slug, documento_tipo__isnull=True).order_by("-is_default", "id").first()
        if m:
            return m
        # se slug specificato ma non trovato, 404 esplicito
        return get_object_or_404(StampaModulo, app_label=app_label, model_name=model_name, slug=slug, attivo=True)

    # senza slug: preferisci moduli del tipo documento
    if doc_tipo is not None:
        m = qs.filter(documento_tipo=doc_tipo).order_by("-is_default", "id").first()
        if m:
            return m
    # poi generici
    m = qs.filter(documento_tipo__isnull=True).order_by("-is_default", "id").first()
    if m:
        return m
    # ultimo: qualunque attivo
    m = qs.order_by("-is_default", "id").first()
    if m:
        return m

    from django.http import Http404
    raise Http404("Nessun modulo di stampa disponibile")

# ---- Liste: resolver e filtri ----
def get_lista_for(app_label: str, model: str, slug: Optional[str] = None) -> StampaLista:
    qs = StampaLista.objects.filter(app_label=app_label, model_name=model, attivo=True)
    if slug:
        return get_object_or_404(qs, slug=slug)
    lst = qs.order_by("-is_default", "id").first()
    if lst:
        return lst
    raise Http404("Nessuna lista di stampa disponibile")

def _resolve_param(value: Any, params: Dict[str, str]) -> Any:
    # Placeholder ":name" -> prendi da params[name]; se mancante, None
    if isinstance(value, str) and value.startswith(":"):
        return params.get(value[1:], None)
    return value

def build_q_and_kwargs(filter_def: Dict[str, Any], params: Dict[str, str]) -> Dict[str, Any]:
    """
    Converte il JSON filter_def in kwargs per filter().
    Supporta placeholder ':param' risolti da querystring.
    Valori None non vengono applicati.
    """
    kwargs: Dict[str, Any] = {}
    if not filter_def:
        return kwargs
    for lookup, raw in filter_def.items():
        val = _resolve_param(raw, params)
        if val in (None, ""):
            continue
        kwargs[lookup] = val
    return kwargs

def build_queryset_for_list(ct: ContentType, lista: StampaLista, params: Dict[str, str]):
    Model = ct.model_class()
    if Model is None:
        raise Http404("Modello non trovato")
    qs = Model._default_manager.all()
    # Consenti override da GET: f__campo_lookup=valore
    extra_filters = {k[3:]: v for k, v in params.items() if k.startswith("f__") and v not in (None, "")}
    kwargs = build_q_and_kwargs(lista.filter_def or {}, params)
    if kwargs:
        qs = qs.filter(**kwargs)
    if extra_filters:
        qs = qs.filter(**extra_filters)
    # Ordinamento: GET ?order=campo,-campo2 override; altrimenti lista.order_by
    order = params.get("order")
    if order:
        qs = qs.order_by(*[p.strip() for p in order.split(",") if p.strip()])
    elif lista.order_by:
        qs = qs.order_by(*lista.order_by)
    return qs

# ---- Rendering lista ----
def _draw_table_header(c: canvas.Canvas, lista: StampaLista, colonne: List[StampaColonna], x0: float, y: float) -> float:
    c.setFont(lista.header_font_name or "Helvetica-Bold", float(lista.header_font_size or 9.0))
    for col in colonne:
        w = col.larghezza_mm * mm
        if col.align == StampaColonna.Align.CENTER:
            c.drawCentredString(x0 + w / 2, y, col.label)
        elif col.align == StampaColonna.Align.RIGHT:
            c.drawRightString(x0 + w, y, col.label)
        else:
            c.drawString(x0, y, col.label)
        x0 += w
    return y

def _value_from_col(obj: Any, col: StampaColonna) -> str:
    if col.tipo == StampaColonna.Tipo.TEMPLATE and col.template:
        try:
            return (col.template or "").format(**{"obj": obj})
        except Exception:
            return ""
    if col.tipo in (StampaColonna.Tipo.BARCODE, StampaColonna.Tipo.QRCODE):
        # usa attr_path se presente, altrimenti template
        v = _resolve_attr(obj, col.attr_path) if col.attr_path else None
        if v in (None, "") and col.template:
            try:
                v = (col.template or "").format(**{"obj": obj})
            except Exception:
                v = ""
        return _to_str(v)
    # TEXT default via attr_path
    return _to_str(_resolve_attr(obj, col.attr_path)) if col.attr_path else ""

def _draw_cell_text(c: canvas.Canvas, txt: str, x: float, top_y: float, w_pt: float, align: str, font: Tuple[str, float], max_lines: int, spacing: float) -> float:
    name, size = font
    c.setFont(name, size)
    lines = _wrap_lines(c, txt, w_pt, font)
    lines = lines[:max_lines]
    line_h = size * spacing
    y = top_y
    for ln in lines:
        if align == "center":
            c.drawCentredString(x + w_pt / 2, y, ln)
        elif align == "right":
            c.drawRightString(x + w_pt, y, ln)
        else:
            c.drawString(x, y, ln)
        y -= line_h
    # ritorna la y più bassa raggiunta
    return top_y - (line_h * max(1, len(lines)))

def _draw_row(c: canvas.Canvas, lista: StampaLista, colonne: List[StampaColonna], obj: Any, x_left: float, top_y: float, page_w: float) -> float:
    # calcolo altezza riga approssimato: in base a max_lines e font per colonna
    row_bottom_y = top_y
    x = x_left
    for col in colonne:
        w = col.larghezza_mm * mm
        font = (col.font_nome or lista.row_font_name or "Helvetica", float(col.font_size or lista.row_font_size or 9.0))
        max_lines = int(col.max_lines or lista.row_max_lines or 1)
        if col.tipo == StampaColonna.Tipo.BARCODE:
            bw = max(0.1, float(col.barcode_bar_width_mm)) * mm
            bh = max(5.0, float(col.barcode_height_mm)) * mm
            std = (col.barcode_standard or "code128").lower()
            val = _value_from_col(obj, col)
            if val:
                try:
                    if std == "code39":
                        widget = code39.Standard39(val, barWidth=bw, barHeight=bh, checksum=False, stop=True)
                    elif std == "ean13":
                        digits = "".join(ch for ch in val if ch.isdigit())
                        if len(digits) >= 12:
                            widget = eanbc.Ean13BarcodeWidget(digits[:13], barWidth=bw, barHeight=bh)
                        else:
                            widget = None
                    else:
                        widget = code128.Code128(val, barWidth=bw, barHeight=bh)
                    if widget:
                        y_draw = top_y - widget.height
                        widget.drawOn(c, x, y_draw)
                        row_bottom_y = min(row_bottom_y, y_draw)
                except Exception:
                    pass
        elif col.tipo == StampaColonna.Tipo.QRCODE:
            size_pt = max(8.0, float(col.qr_size_mm or 12.0)) * mm
            val = _value_from_col(obj, col)
            if val:
                try:
                    widget = rl_qr.QrCodeWidget(val, barLevel=(col.qr_error or "M"))
                    minx, miny, maxx, maxy = widget.getBounds()
                    sx = size_pt / (maxx - minx)
                    sy = size_pt / (maxy - miny)
                    d = Drawing(size_pt, size_pt, transform=[sx, 0, 0, sy, 0, 0])
                    d.add(widget)
                    renderPDF.draw(d, c, x, top_y - size_pt)
                    row_bottom_y = min(row_bottom_y, top_y - size_pt)
                except Exception:
                    pass
        else:
            txt = _value_from_col(obj, col)
            y_after = _draw_cell_text(
                c, txt, x, top_y,
                w, col.align, font, max_lines,
                spacing=float(lista.row_spacing or 1.2),
            )
            row_bottom_y = min(row_bottom_y, y_after)
        x += w
    # se è definita un'altezza forzata, rispettala
    forced = lista.row_height_mm * mm if lista.row_height_mm else None
    if forced:
        return top_y - forced
    return row_bottom_y - (2)  # piccolo padding
        

def render_lista_pdf(ct: ContentType, lista: StampaLista, params: Dict[str, str]) -> bytes:
    Model = ct.model_class()
    if not Model:
        raise Http404("Modello non trovato")

    qs = build_queryset_for_list(ct, lista, params)
    page_w, page_h = _pagesize_points(lista.formato)
    mt, ml, mr, mb = (lista.formato.margine_top_mm * mm, lista.formato.margine_left_mm * mm,
                      lista.formato.margine_right_mm * mm, lista.formato.margine_bottom_mm * mm)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_w, page_h))

    colonne = list(lista.colonne.filter(visibile=True).order_by("ordine", "id"))

    def _new_page():
        c.setFont(lista.header_font_name or "Helvetica-Bold", float(lista.header_font_size or 9.0))
        x = ml
        header_y = page_h - mt
        _draw_table_header(c, lista, colonne, x, header_y)
        return header_y - (lista.header_font_size or 9.0) * 1.8  # spazio dopo intestazione

    y_cursor = _new_page()
    for obj in qs.iterator():
        # nuova pagina se non c'è spazio sufficiente per la riga
        min_row_height = (lista.row_height_mm or (lista.row_font_size * lista.row_spacing * (lista.row_max_lines or 1) / 2.834)) if (lista.row_font_size and lista.row_spacing) else 8
        if y_cursor - (min_row_height * mm) < mb + 10:
            c.showPage()
            y_cursor = _new_page()

        y_next = _draw_row(c, lista, colonne, obj, ml, y_cursor, page_w)
        y_cursor = y_next

    c.showPage()
    c.save()
    return buf.getvalue()
