"""
Generazione PDF Copertina per Unità Fisiche
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from io import BytesIO
from django.utils import timezone
from datetime import datetime


def render_copertina_unita_pdf(unita) -> bytes:
    """
    Genera un PDF copertina A4 per un'unità fisica.
    
    Il layout mostra:
    - Path completo in alto
    - Codice e Nome al centro (1/3 dall'alto) in grande
    - Informazioni aggiuntive in basso
    
    Args:
        unita: Istanza di UnitaFisica
    
    Returns:
        bytes: PDF generato
    """
    buffer = BytesIO()
    
    # Dimensioni A4 Portrait: 210mm x 297mm
    width, height = A4
    
    # Crea il canvas
    c = canvas.Canvas(buffer, pagesize=A4)
    
    # --- INTESTAZIONE (in alto) ---
    c.setFont("Helvetica", 10)
    c.drawString(10 * mm, (297 - 10) * mm, f"Path: {unita.full_path or 'N/A'}")
    
    # --- CONTENUTO CENTRALE ---
    # Posizione: centro orizzontale, 1/3 dall'alto (2/3 dal basso)
    center_x = width / 2
    center_y = height * (2/3)  # 1/3 dall'alto = 2/3 dal basso
    
    # CODICE (grande, bold)
    c.setFont("Helvetica-Bold", 48)
    codice_text = unita.codice or "N/A"
    codice_width = c.stringWidth(codice_text, "Helvetica-Bold", 48)
    c.drawString(center_x - codice_width/2, center_y + 20*mm, codice_text)
    
    # NOME (grande, normale)
    c.setFont("Helvetica", 36)
    nome_text = unita.nome or ""
    nome_width = c.stringWidth(nome_text, "Helvetica", 36)
    c.drawString(center_x - nome_width/2, center_y - 10*mm, nome_text)
    
    # Linea separatrice sotto il nome
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(0.5)
    line_start_x = center_x - 80*mm
    line_end_x = center_x + 80*mm
    c.line(line_start_x, center_y - 20*mm, line_end_x, center_y - 20*mm)
    
    # --- INFORMAZIONI AGGIUNTIVE (sotto la linea) ---
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    
    y_pos = center_y - 35*mm
    
    # Tipo
    tipo_display = unita.get_tipo_display() if hasattr(unita, 'get_tipo_display') else unita.tipo
    tipo_text = f"Tipo: {tipo_display}"
    tipo_width = c.stringWidth(tipo_text, "Helvetica", 12)
    c.drawString(center_x - tipo_width/2, y_pos, tipo_text)
    
    # Descrizione (se presente)
    if unita.descrizione:
        y_pos -= 7*mm
        c.setFont("Helvetica", 10)
        desc_text = unita.descrizione[:80]  # Limita a 80 caratteri
        desc_width = c.stringWidth(desc_text, "Helvetica", 10)
        c.drawString(center_x - desc_width/2, y_pos, desc_text)
    
    # Note (se presenti)
    if unita.note:
        y_pos -= 6*mm
        c.setFont("Helvetica-Oblique", 9)
        note_text = unita.note[:100]  # Limita a 100 caratteri
        note_width = c.stringWidth(note_text, "Helvetica-Oblique", 9)
        c.drawString(center_x - note_width/2, y_pos, note_text)
    
    # --- PIÈ DI PAGINA ---
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    
    # Riga 1: Ubicazione padre (se presente)
    if unita.parent:
        footer_text = f"Contenuta in: {unita.parent.codice} - {unita.parent.nome}"
        c.drawString(10 * mm, 25 * mm, footer_text)
    
    # Riga 2: Archivio fisso
    archivio_text = "ARCHIVIO FISSO" if unita.archivio_fisso else "Archivio Corrente"
    c.drawString(10 * mm, 20 * mm, archivio_text)
    
    # Riga 3: Data creazione
    if unita.created_at:
        created_text = f"Creato il: {unita.created_at.strftime('%d/%m/%Y %H:%M')}"
    else:
        created_text = "Data creazione: N/A"
    c.drawString(10 * mm, 15 * mm, created_text)
    
    # Data stampa (in basso a destra)
    now = timezone.now()
    stampa_text = f"Stampato il: {now.strftime('%d/%m/%Y %H:%M')}"
    stampa_width = c.stringWidth(stampa_text, "Helvetica", 8)
    c.drawString((210 - 10) * mm - stampa_width, 10 * mm, stampa_text)
    
    # --- BORDO DECORATIVO (opzionale) ---
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(1)
    margin = 8 * mm
    c.rect(margin, margin, width - 2*margin, height - 2*margin)
    
    # Finalizza il PDF
    c.showPage()
    c.save()
    
    # Ritorna i bytes
    buffer.seek(0)
    return buffer.getvalue()
