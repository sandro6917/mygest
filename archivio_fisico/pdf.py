from io import BytesIO
from typing import Iterable, Optional
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
# nuovo: import opzionale qrcode
try:
    import qrcode  # type: ignore
except Exception:
    qrcode = None

def _gen_qr_image(data: str) -> Optional[ImageReader]:
    if not qrcode:
        return None
    try:
        img = qrcode.make(data)
        return ImageReader(img)
    except Exception:
        return None

def _truncate(text: str, max_chars: int) -> str:
    if text and len(text) > max_chars:
        return text[: max_chars - 1] + "…"
    return text or ""

def render_etichette_unita(unita_list: Iterable, *, include_qr: bool = True, mostra_path: bool = True,
                           cols: int = 3, rows: int = 8, bordi: bool = False,
                           base_url: Optional[str] = None) -> HttpResponse:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    pw, ph = A4

    margin_x = 8 * mm
    margin_y = 12 * mm
    grid_w = pw - 2 * margin_x
    grid_h = ph - 2 * margin_y
    cell_w = grid_w / max(1, cols)
    cell_h = grid_h / max(1, rows)

    title_size = 10
    text_size = 8

    items = list(unita_list)
    idx = 0
    total = len(items)

    while idx < total:
        for r in range(rows):
            for ccol in range(cols):
                if idx >= total:
                    break
                u = items[idx]; idx += 1
                x = margin_x + ccol * cell_w
                y = ph - margin_y - (r + 1) * cell_h
                if bordi:
                    c.rect(x, y, cell_w, cell_h, stroke=1, fill=0)

                qr_side = min(cell_w, cell_h) * 0.35 if include_qr else 0
                text_left = x + (qr_side + 4) if include_qr else x + 2
                cursor_y = y + cell_h - 4

                c.setFont("Helvetica-Bold", title_size)
                titolo = f"{u.get_tipo_display()} • {getattr(u, 'codice', '')}"
                c.drawString(text_left, cursor_y, _truncate(titolo, 40))
                cursor_y -= 12

                c.setFont("Helvetica", text_size)
                c.drawString(text_left, cursor_y, _truncate(getattr(u, "nome", "") or "", 50))
                cursor_y -= 10

                if mostra_path and getattr(u, "full_path", ""):
                    c.setFont("Helvetica", text_size - 1)
                    c.drawString(text_left, cursor_y, _truncate(u.full_path, 60))
                    cursor_y -= 9

                if include_qr:
                    target_url = f"{base_url}/archivio-fisico/{u.pk}/" if base_url else None
                    qr_img = _gen_qr_image(target_url or f"UNITA:{u.pk}:{getattr(u, 'full_path', '') or getattr(u,'codice','')}")
                    if qr_img:
                        qr_x = x + 2
                        qr_y = y + (cell_h - qr_side) / 2
                        c.drawImage(qr_img, qr_x, qr_y, width=qr_side, height=qr_side, preserveAspectRatio=True, mask='auto')
        c.showPage()

    c.save()
    pdf = buf.getvalue()
    buf.close()
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'inline; filename="etichette_archivio.pdf"'
    return resp