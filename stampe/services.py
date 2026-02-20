from __future__ import annotations
import io
from typing import Any, Iterable, Tuple, Optional, List, Dict, Union
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.db.models import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from .models import StampaFormato, StampaModulo, StampaCampo, StampaLista, StampaColonna
from reportlab.graphics.barcode import code128, code39, eanbc, qr as rl_qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from types import SimpleNamespace
from django.shortcuts import get_object_or_404
from reportlab.lib import colors

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
    cur = instance
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            try:
                cur = getattr(cur, part)
            except ObjectDoesNotExist:
                return None
            except AttributeError:
                return None
        if callable(cur):
            try:
                cur = cur()
            except TypeError:
                # callable that requires params (es. RelatedManager): lascia il riferimento per step successivi
                pass
            except ObjectDoesNotExist:
                return None
    return cur

def _to_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val)

def _wrap_lines(c: canvas.Canvas, text: str, max_width: float, font: Tuple[str, float]) -> list[str]:
    if not text or not max_width:
        return [text or ""]
    name, size = font
    words = str(text).split()
    lines: list[str] = []
    line = ""
    for w in words:
        candidate = (line + " " + w).strip()
        if not line:
            # se una singola parola è più larga della larghezza disponibile, la forziamo nella linea corrente
            if c.stringWidth(candidate, name, size) <= max_width or c.stringWidth(w, name, size) > max_width:
                line = w if not line else candidate
            else:
                line = w
        elif c.stringWidth(candidate, name, size) <= max_width:
            line = candidate
        else:
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
            from django.utils import timezone
            now = timezone.now()
            ctx = {
                "obj": instance,
                "attr": _attrs_namespace(instance),
                "now": now.strftime('%d/%m/%Y %H:%M:%S'),
                "date": now.strftime('%d/%m/%Y'),
                "time": now.strftime('%H:%M:%S'),
            }
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

        if campo.tipo == StampaCampo.Tipo.SHAPE:
            _draw_shape(c, campo, x_pt, top_y_pt)
            continue

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
    ct = ContentType.objects.get_for_model(instance.__class__)
    qs = StampaModulo.objects.filter(app_label=ct.app_label, model_name=ct.model)
    doc_tipo = getattr(instance, "documento_tipo_id", None)
    if isinstance(doc_tipo, int):
        qs = qs.filter(documento_tipo=doc_tipo)
    if slug:
        qs = qs.filter(slug=slug)
    m = qs.order_by("-is_default", "id").first()
    if not m:
        from django.http import Http404
        raise Http404("Nessun modulo di stampa disponibile per questa etichetta.")
    return m

def get_lista_for(ct: ContentType, lista_slug: str = None) -> StampaLista:
    qs = StampaLista.objects.filter(
        app_label=ct.app_label,
        model_name=ct.model,
        attivo=True,
    )
    if lista_slug:
        qs = qs.filter(slug=lista_slug)
    else:
        qs = qs.filter(is_default=True)
    lista = qs.first()
    if not lista:
        raise Http404("Nessuna lista di stampa disponibile")
    return lista

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


def _normalize_tree_root_values(raw: Any) -> List[int]:
    if raw is None:
        return []
    if hasattr(raw, "values_list") and callable(getattr(raw, "values_list")):
        try:
            return list(raw.values_list("pk", flat=True))
        except Exception:
            return []
    if isinstance(raw, str):
        cleaned = raw.strip()
        if not cleaned:
            return []
        cleaned = cleaned.strip("[](){}")
        cleaned = cleaned.replace(";", ",")
        values: List[int] = []
        for part in cleaned.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                values.append(int(part))
            except ValueError:
                continue
        return values
    if isinstance(raw, (list, tuple, set)):
        values: List[int] = []
        for item in raw:
            values.extend(_normalize_tree_root_values(item))
        return values
    try:
        return [int(raw)]
    except (TypeError, ValueError):
        return []


def _tree_node_cache_key(node: Any) -> tuple[Any, Any]:
    pk = getattr(node, "pk", None)
    if pk is not None:
        return (node.__class__, pk)
    return (node.__class__, id(node))


def _resolve_children_for_tree(
    node: Any,
    lista: StampaLista,
    filters: Dict[str, Any],
    order_fields: Optional[List[str]],
) -> List[Any]:
    attr_path = (lista.tree_children_attr or "").strip()
    children: Any = None
    if attr_path:
        children = _resolve_attr(node, attr_path)
    else:
        parent_field = (lista.tree_parent_field or "parent").strip()
        if parent_field:
            related_name = f"{parent_field}_set"
            children = getattr(node, related_name, None)
    if children is None:
        return []

    qs: Optional[QuerySet] = None
    if isinstance(children, QuerySet):
        qs = children
    elif hasattr(children, "all") and callable(getattr(children, "all")):
        try:
            qs = children.all()
        except Exception:
            qs = None

    if qs is not None:
        if filters:
            try:
                qs = qs.filter(**filters)
            except Exception:
                pass
        if order_fields:
            try:
                qs = qs.order_by(*order_fields)
            except Exception:
                pass
        try:
            return list(qs)
        except Exception:
            # fallback to iterator
            try:
                return list(iter(qs))
            except Exception:
                return []

    # fallback: prova a iterare sull'oggetto
    try:
        iterable = list(children)
    except TypeError:
        return []
    return iterable


def _traverse_tree(
    node: Any,
    level: int,
    lista: StampaLista,
    filters: Dict[str, Any],
    order_fields: Optional[List[str]],
    max_depth: Optional[int],
    visited: set[tuple[Any, Any]],
) -> List[Any]:
    key = _tree_node_cache_key(node)
    if key in visited:
        return []
    visited.add(key)

    setattr(node, "_stampa_tree_level", level)
    rows: List[Any] = [node]

    if max_depth is not None and level >= max_depth:
        return rows

    for child in _resolve_children_for_tree(node, lista, filters, order_fields):
        rows.extend(_traverse_tree(child, level + 1, lista, filters, order_fields, max_depth, visited))
    return rows


def _collect_tree_rows(ct: ContentType, lista: StampaLista, params: Dict[str, str]) -> List[Any]:
    Model = ct.model_class()
    if Model is None:
        raise Http404("Modello non trovato")

    filters = build_q_and_kwargs(lista.filter_def or {}, params)
    base_qs = Model._default_manager.all()
    if filters:
        base_qs = base_qs.filter(**filters)

    root_ids: List[int] = []
    for raw in lista.tree_roots or []:
        resolved = _resolve_param(raw, params)
        root_ids.extend(_normalize_tree_root_values(resolved))

    if root_ids:
        roots_qs = base_qs.filter(pk__in=root_ids)
    else:
        root_filters = build_q_and_kwargs(lista.tree_root_filter or {}, params)
        if root_filters:
            roots_qs = base_qs.filter(**root_filters)
        else:
            parent_field = (lista.tree_parent_field or "parent").strip()
            if parent_field:
                try:
                    roots_qs = base_qs.filter(**{f"{parent_field}__isnull": True})
                except FieldError:
                    roots_qs = base_qs
            else:
                roots_qs = base_qs

    order_fields = lista.tree_order_by or lista.order_by
    if order_fields:
        try:
            roots_qs = roots_qs.order_by(*order_fields)
        except Exception:
            pass

    roots = list(roots_qs)

    max_depth = lista.tree_max_depth
    visited: set[tuple[Any, Any]] = set()
    rows: List[Any] = []
    for root in roots:
        rows.extend(_traverse_tree(root, 0, lista, filters, order_fields, max_depth, visited))
    return rows

# ---- Rendering lista ----
def _draw_table_header(c: canvas.Canvas, lista: StampaLista, colonne: List[StampaColonna], x0: float, y: float) -> float:
    font_name = lista.header_font_name or "Helvetica-Bold"
    font_size = float(lista.header_font_size or 9.0)
    c.setFont(font_name, font_size)
    max_height = 0
    x = x0
    for col in colonne:
        w = col.larghezza_mm * mm
        if col.align == StampaColonna.Align.CENTER:
            c.drawCentredString(x + w / 2, y, col.label)
        elif col.align == StampaColonna.Align.RIGHT:
            c.drawRightString(x + w, y, col.label)
        else:
            c.drawString(x, y, col.label)
        x += w
        max_height = max(max_height, font_size)
    # Spazio dopo header (puoi aumentare il padding se vuoi più spazio)
    return y - max_height * 1.3

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

def _draw_row(
    c: canvas.Canvas,
    lista: StampaLista,
    colonne: List[StampaColonna],
    obj: Any,
    x_left: float,
    top_y: float,
    page_w: float,
    tree_level: int = 0,
) -> float:
    # calcolo altezza riga approssimato: in base a max_lines e font per colonna
    row_bottom_y = top_y
    x = x_left
    is_tree_layout = getattr(lista, "layout", None) == StampaLista.Layout.TREE
    indent_per_level = 0.0
    indent_flags: List[bool] = []
    if is_tree_layout:
        indent_per_level = max(0.0, float(lista.tree_indent_mm or 0.0)) * mm
        indent_flags = [bool(getattr(col, "indent_tree", False)) for col in colonne]
        if colonne and not any(indent_flags):
            indent_flags[0] = True
    for idx, col in enumerate(colonne):
        w = col.larghezza_mm * mm
        font = (col.font_nome or lista.row_font_name or "Helvetica", float(col.font_size or lista.row_font_size or 9.0))
        max_lines = int(col.max_lines or lista.row_max_lines or 1)
        draw_x = x
        available_w = w
        apply_indent = is_tree_layout and (indent_flags[idx] if idx < len(indent_flags) else False)
        if apply_indent:
            indent_pt = indent_per_level * max(tree_level, 0)
            draw_x = x + indent_pt
            available_w = max(0.0, w - indent_pt)
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
                        widget.drawOn(c, draw_x, y_draw)
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
                    renderPDF.draw(d, c, draw_x, top_y - size_pt)
                    row_bottom_y = min(row_bottom_y, top_y - size_pt)
                except Exception:
                    pass
        else:
            txt = _value_from_col(obj, col)
            y_after = _draw_cell_text(
                c, txt, draw_x, top_y,
                available_w or w, col.align, font, max_lines,
                spacing=float(lista.row_spacing or 1.2),
            )
            row_bottom_y = min(row_bottom_y, y_after)
        x += w
    # se è definita un'altezza forzata, rispettala
    forced = lista.row_height_mm * mm if lista.row_height_mm else None
    if forced:
        return top_y - forced
    return row_bottom_y - (2)  # piccolo padding
        

def render_lista_pdf(ct: ContentType, lista: StampaLista, params: dict, extra_context: dict = None) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    from io import BytesIO
    from django.utils import timezone

    buf = BytesIO()
    fmt = lista.formato
    page_w = fmt.larghezza_mm * mm
    page_h = fmt.altezza_mm * mm
    ml = fmt.margine_left_mm * mm
    mr = fmt.margine_right_mm * mm
    mt = fmt.margine_top_mm * mm
    mb = fmt.margine_bottom_mm * mm

    c = canvas.Canvas(buf, pagesize=(page_w, page_h))
    y = page_h - mt

    colonne = list(lista.colonne.filter(visibile=True).order_by("ordine", "id"))

    data_iterable: Iterable[Any]
    primo_obj: Optional[Any] = None
    if getattr(lista, "layout", None) == StampaLista.Layout.TREE:
        rows = _collect_tree_rows(ct, lista, params)
        primo_obj = rows[0] if rows else None
        data_iterable = rows
    else:
        qs = build_queryset_for_list(ct, lista, params)
        primo_obj = qs.first()
        data_iterable = qs

    extra_context = extra_context or {}
    
    # Aggiungi datetime corrente al context
    now = timezone.now()
    extra_context['now'] = now.strftime('%d/%m/%Y %H:%M:%S')
    extra_context['date'] = now.strftime('%d/%m/%Y')
    extra_context['time'] = now.strftime('%H:%M:%S')

    def _get_attrs_namespace(obj):
        try:
            vals = getattr(obj, "attributi_valori", None)
            if vals:
                return {v.definizione.codice: v.valore for v in vals.select_related("definizione").all()}
        except Exception:
            pass
        return {}

    def _render_titolo(obj):
        ctx = {
            "obj": obj,
            "attr": type("Attr", (), _get_attrs_namespace(obj))(),
        }
        ctx.update(extra_context)
        if lista.titolo_template:
            try:
                return lista.titolo_template.format(**ctx)
            except Exception:
                return lista.titolo or ""
        return lista.titolo or ""

    # --- Titolo (se presente) ---
    titolo = _render_titolo(primo_obj) if primo_obj else (lista.titolo or "")
    if titolo:
        font_name = "Helvetica"
        if lista.titolo_bold and lista.titolo_italic:
            font_name = "Helvetica-BoldOblique"
        elif lista.titolo_bold:
            font_name = "Helvetica-Bold"
        elif lista.titolo_italic:
            font_name = "Helvetica-Oblique"
        font_size = lista.titolo_font_size or 14
        c.setFont(font_name, font_size)
        x = ml + (lista.titolo_x_mm or 0) * mm
        y = page_h - mt - (lista.titolo_y_mm or 0) * mm
        max_width = (lista.titolo_larghezza_mm or 0) * mm or (page_w - ml - mr)
        # Wrapping se necessario
        lines = _wrap_lines(c, titolo, max_width, (font_name, font_size))
        for ln in lines:
            c.drawString(x, y, ln)
            y -= font_size * 1.2
        y -= 2 * mm

    # --- Intestazione (se presente) ---
    if getattr(lista, "intestazione", None):
        c.setFont("Helvetica", lista.intestazione_font_size or 10)
        x = ml + (lista.intestazione_x_mm or 0) * mm
        y_int = y - (lista.intestazione_y_mm or 0) * mm
        for line in lista.intestazione.splitlines():
            c.drawString(x, y_int, line)
            y_int -= (lista.intestazione_font_size or 10) * 1.1
        y = y_int - 2 * mm

    # --- Tabella ---
    y = _draw_table_header(c, lista, colonne, ml, y)
    for obj in data_iterable:
        level = getattr(obj, "_stampa_tree_level", 0)
        y = _draw_row(c, lista, colonne, obj, ml, y, page_w, tree_level=level)
        if y < mb + 20 * mm:
            c.showPage()
            y = page_h - mt
            y = _draw_table_header(c, lista, colonne, ml, y)

    # --- Piè di pagina (se presente) ---
    if getattr(lista, "piedipagina", None):
        # Renderizza il template del piè di pagina
        ctx = extra_context.copy()
        if primo_obj:
            ctx['obj'] = primo_obj
            ctx['attr'] = type("Attr", (), _get_attrs_namespace(primo_obj))()
        
        piedipagina_text = lista.piedipagina
        try:
            # Prova a formattare come template
            piedipagina_text = piedipagina_text.format(**ctx)
        except (KeyError, ValueError, AttributeError):
            # Se fallisce, usa il testo statico
            pass
        
        c.setFont("Helvetica-Oblique", lista.piedipagina_font_size or 9)
        x = ml + (lista.piedipagina_x_mm or 0) * mm
        y_footer = mb + (lista.piedipagina_y_mm or 0) * mm
        for line in piedipagina_text.splitlines():
            c.drawString(x, y_footer, line)
            y_footer += (lista.piedipagina_font_size or 9) * 1.1

    c.save()
    return buf.getvalue()

def _parse_color(value: Optional[str]):
    if not value:
        return None
    try:
        return colors.toColor(value)
    except Exception:
        try:
            if value.startswith("#") and len(value) == 7:
                return colors.HexColor(value)
        except Exception:
            pass
    return None

def _draw_shape(c: canvas.Canvas, campo: StampaCampo, x_pt: float, top_y_pt: float):
    width_pt = max(0.0, float(campo.shape_width_mm or 0.0) * mm)
    height_pt = max(0.0, float(campo.shape_height_mm or 0.0) * mm)
    stroke_width = max(0.0, float(campo.border_width_pt or 0.0))
    radius_pt = max(0.0, float(campo.corner_radius_mm or 0.0) * mm)
    stroke_color = _parse_color(campo.border_color)
    fill_color = _parse_color(campo.fill_color)
    kind = (campo.shape_kind or "rect").lower()
    x = x_pt
    y = top_y_pt - height_pt if kind != "line" else top_y_pt

    c.saveState()
    if stroke_color:
        c.setStrokeColor(stroke_color)
    if fill_color:
        c.setFillColor(fill_color)
    c.setLineWidth(stroke_width)

    if kind == "line":
        c.line(x, y, x + width_pt, y + height_pt)
    elif kind == "rounded_rect" and radius_pt > 0:
        c.roundRect(x, y, width_pt, height_pt, radius_pt, stroke=int(stroke_width > 0), fill=int(bool(fill_color)))
    else:
        c.rect(x, y, width_pt, height_pt, stroke=int(stroke_width > 0), fill=int(bool(fill_color)))
    c.restoreState()

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

        if campo.tipo == StampaCampo.Tipo.SHAPE:
            _draw_shape(c, campo, x_pt, top_y_pt)
            continue

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
    ct = ContentType.objects.get_for_model(instance.__class__)
    qs = StampaModulo.objects.filter(app_label=ct.app_label, model_name=ct.model)
    doc_tipo = getattr(instance, "documento_tipo_id", None)
    if isinstance(doc_tipo, int):
        qs = qs.filter(documento_tipo=doc_tipo)
    if slug:
        qs = qs.filter(slug=slug)
    m = qs.order_by("-is_default", "id").first()
    if not m:
        from django.http import Http404
        raise Http404("Nessun modulo di stampa disponibile per questa etichetta.")
    return m

def get_lista_for(ct: ContentType, lista_slug: str = None) -> StampaLista:
    qs = StampaLista.objects.filter(
        app_label=ct.app_label,
        model_name=ct.model,
        attivo=True,
    )
    if lista_slug:
        qs = qs.filter(slug=lista_slug)
    else:
        qs = qs.filter(is_default=True)
    lista = qs.first()
    if not lista:
        raise Http404("Nessuna lista di stampa disponibile")
    return lista

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
