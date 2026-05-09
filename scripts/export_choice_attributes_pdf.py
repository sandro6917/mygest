#!/usr/bin/env python
"""
Script per generare PDF con attributi choice di tutti i tipi documento.

Usage:
    python scripts/export_choice_attributes_pdf.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from documenti.models import DocumentiTipo, AttributoDefinizione


def create_choice_attributes_pdf():
    """Crea PDF con tutti gli attributi choice."""
    
    # Nome file output
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'attributi_choice_{timestamp}.pdf'
    output_path = os.path.join('/tmp', output_file)
    
    print(f"📄 Generazione PDF: {output_path}")
    
    # Crea documento PDF (landscape per tabelle larghe)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(A4),
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1976d2'),
        spaceAfter=30,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#424242'),
        spaceAfter=12,
        spaceBefore=20,
    )
    
    # Contenuto documento
    story = []
    
    # Titolo
    story.append(Paragraph("Attributi Choice - Tutti i Tipi Documento", title_style))
    story.append(Paragraph(
        f"Generato il: {timezone.now().strftime('%d/%m/%Y %H:%M')}",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # Query: tutti i tipi documento con attributi choice
    tipi_documento = DocumentiTipo.objects.all().order_by('codice')
    
    total_tipi = 0
    total_attributi = 0
    
    for tipo_doc in tipi_documento:
        # Attributi choice di questo tipo documento
        attributi_choice = AttributoDefinizione.objects.filter(
            tipo_documento=tipo_doc,
            tipo_dato='choice'
        ).order_by('ordine', 'nome')
        
        if not attributi_choice.exists():
            continue  # Salta se non ha attributi choice
        
        total_tipi += 1
        total_attributi += attributi_choice.count()
        
        # Heading tipo documento
        story.append(Paragraph(
            f"<b>{tipo_doc.codice}</b> (ID: {tipo_doc.id})",
            heading_style
        ))
        
        # Tabella attributi
        data = [
            ['Codice', 'Nome', 'Scelte Configurate', 'Obbligatorio']
        ]
        
        for attr in attributi_choice:
            # Parsing scelte
            scelte_str = attr.choices or ""
            
            # Formatta scelte per leggibilità
            if scelte_str:
                scelte_list = []
                for part in scelte_str.split(','):
                    part = part.strip()
                    if '|' in part:
                        val, label = part.split('|', 1)
                        scelte_list.append(f"{val.strip()} = {label.strip()}")
                    else:
                        scelte_list.append(part)
                scelte_formatted = '\n'.join(scelte_list)
            else:
                scelte_formatted = "(nessuna scelta configurata)"
            
            data.append([
                attr.codice,
                attr.nome,
                scelte_formatted,
                '✓' if attr.required else ''
            ])
        
        # Crea tabella
        table = Table(data, colWidths=[5*cm, 6*cm, 12*cm, 2*cm])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Body
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('LEFTPADDING', (0, 1), (-1, -1), 8),
            ('RIGHTPADDING', (0, 1), (-1, -1), 8),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.8*cm))
    
    # Riepilogo finale
    if total_tipi > 0:
        story.append(PageBreak())
        story.append(Paragraph("📊 Riepilogo", heading_style))
        
        summary_data = [
            ['Metrica', 'Valore'],
            ['Tipi Documento con Attributi Choice', str(total_tipi)],
            ['Totale Attributi Choice', str(total_attributi)],
            ['Media Attributi per Tipo', f"{total_attributi / total_tipi:.1f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[12*cm, 8*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(summary_table)
    else:
        story.append(Paragraph(
            "⚠️ Nessun tipo documento con attributi choice trovato.",
            styles['Normal']
        ))
    
    # Genera PDF
    doc.build(story)
    
    print(f"✅ PDF generato: {output_path}")
    print(f"📊 Statistiche:")
    print(f"   - Tipi Documento: {total_tipi}")
    print(f"   - Attributi Choice: {total_attributi}")
    
    return output_path


if __name__ == '__main__':
    try:
        pdf_path = create_choice_attributes_pdf()
        print(f"\n🎉 Fatto! Scarica il file da: {pdf_path}")
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
