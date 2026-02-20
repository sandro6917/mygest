#!/usr/bin/env python3
"""
Genera PDF Documentazione Soluzione 2 - Path Configurabili

Questo script crea un PDF unico con tutta la documentazione
relativa alla Soluzione 2: Path Configurabili e Portabili.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Aggiungi il path del progetto
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
import django
django.setup()

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Preformatted, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Canvas con numerazione pagine"""
    
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.drawRightString(
            A4[0] - 2*cm,
            1.5*cm,
            f"Pagina {self._pageNumber} di {page_count}"
        )
        self.drawString(
            2*cm,
            1.5*cm,
            "MyGest - Soluzione 2: Path Configurabili"
        )


def parse_markdown_to_elements(md_content, styles):
    """Converte markdown in elementi ReportLab"""
    elements = []
    lines = md_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Titoli
        if line.startswith('# '):
            text = line[2:]
            elements.append(Spacer(1, 0.5*cm))
            elements.append(Paragraph(text, styles['Heading1']))
            elements.append(Spacer(1, 0.3*cm))
        
        elif line.startswith('## '):
            text = line[3:]
            elements.append(Spacer(1, 0.4*cm))
            elements.append(Paragraph(text, styles['Heading2']))
            elements.append(Spacer(1, 0.2*cm))
        
        elif line.startswith('### '):
            text = line[4:]
            elements.append(Spacer(1, 0.3*cm))
            elements.append(Paragraph(text, styles['Heading3']))
            elements.append(Spacer(1, 0.15*cm))
        
        elif line.startswith('#### '):
            text = line[5:]
            elements.append(Spacer(1, 0.2*cm))
            elements.append(Paragraph(text, styles['Heading4']))
            elements.append(Spacer(1, 0.1*cm))
        
        # Separatori
        elif line.startswith('---'):
            elements.append(Spacer(1, 0.3*cm))
        
        # Tabelle markdown (semplice rilevamento)
        elif '|' in line and line.strip().startswith('|'):
            # Raccogli tutte le righe della tabella
            table_lines = []
            while i < len(lines) and '|' in lines[i]:
                if not lines[i].strip().replace('|', '').replace('-', '').strip():
                    # Riga separatore (es: |---|---|)
                    i += 1
                    continue
                table_lines.append(lines[i])
                i += 1
            i -= 1
            
            # Converti in testo semplice invece di tabella
            if table_lines:
                elements.append(Spacer(1, 0.2*cm))
                for tline in table_lines:
                    # Rimuovi pipe e converti in testo
                    cells = [c.strip() for c in tline.split('|') if c.strip()]
                    clean_text = ' - '.join(cells)
                    # Pulisci markdown
                    clean_text = clean_text.replace('**', '').replace('`', '')
                    clean_text = clean_text.replace('<br>', ', ')
                    try:
                        elements.append(Paragraph(clean_text, styles['Normal']))
                    except:
                        # Se fallisce, usa Preformatted
                        elements.append(Preformatted(clean_text, styles['CodeBlock']))
                elements.append(Spacer(1, 0.2*cm))
        
        # Blocchi codice
        elif line.startswith('```'):
            code_lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            
            code_text = '\n'.join(code_lines)
            if code_text.strip():
                elements.append(Spacer(1, 0.2*cm))
                # Limita larghezza per evitare overflow
                pre = Preformatted(
                    code_text,
                    styles['CodeBlock'],
                    maxLineLength=85
                )
                elements.append(pre)
                elements.append(Spacer(1, 0.2*cm))
        
        # Liste non ordinate
        elif line.startswith('- ') or line.startswith('* '):
            bullet_items = []
            while i < len(lines) and (lines[i].startswith('- ') or lines[i].startswith('* ')):
                item_text = lines[i][2:].strip()
                # Gestisci checkbox
                if item_text.startswith('[ ] '):
                    item_text = '[ ] ' + item_text[4:]
                elif item_text.startswith('[x] ') or item_text.startswith('[X] '):
                    item_text = '[X] ' + item_text[4:]
                
                bullet_items.append(item_text)
                i += 1
            i -= 1
            
            for item in bullet_items:
                # Pulisci da markdown
                clean_item = item.replace('**', '').replace('`', '').replace('*', '')
                try:
                    elements.append(Paragraph(f"• {clean_item}", styles['Normal']))
                except:
                    elements.append(Preformatted(f"• {clean_item}", styles['CodeBlock']))
        
        # Liste ordinate
        elif line and line[0].isdigit() and '. ' in line:
            clean_line = line.replace('**', '').replace('`', '')
            try:
                elements.append(Paragraph(clean_line, styles['Normal']))
            except:
                elements.append(Preformatted(clean_line, styles['CodeBlock']))
        
        # Paragrafi normali
        elif line.strip():
            # Rimuovi emoji e caratteri speciali
            clean_line = line.replace('✅', '[OK]').replace('❌', '[NO]')
            clean_line = clean_line.replace('✓', 'V').replace('✗', 'X')
            clean_line = clean_line.replace('⚠', '!').replace('ℹ', 'i')
            clean_line = clean_line.replace('━', '-').replace('🎯', '*')
            clean_line = clean_line.replace('📦', '').replace('🚀', '')
            clean_line = clean_line.replace('📊', '').replace('💻', '')
            clean_line = clean_line.replace('🔐', '').replace('🎉', '')
            clean_line = clean_line.replace('📚', '').replace('💡', '')
            clean_line = clean_line.replace('🔧', '').replace('🙏', '')
            clean_line = clean_line.replace('🎁', '').replace('🔄', '')
            clean_line = clean_line.replace('🎊', '').replace('📋', '')
            clean_line = clean_line.replace('📂', '').replace('🐛', '')
            clean_line = clean_line.replace('⏳', '...').replace('🔗', '')
            
            # Rimuovi markdown
            clean_line = clean_line.replace('**', '').replace('`', '')
            clean_line = clean_line.replace('<br>', ', ').replace('<br/>', ', ')
            
            # Escape caratteri XML problematici
            clean_line = clean_line.replace('&', '&amp;')
            clean_line = clean_line.replace('<', '&lt;').replace('>', '&gt;')
            
            if clean_line.strip():
                try:
                    elements.append(Paragraph(clean_line, styles['Normal']))
                except Exception as e:
                    # Fallback a Preformatted se Paragraph fallisce
                    try:
                        elements.append(Preformatted(clean_line, styles['CodeBlock']))
                    except:
                        # Ultimo fallback: ignora la riga
                        pass
        
        # Linee vuote
        else:
            elements.append(Spacer(1, 0.15*cm))
        
        i += 1
    
    return elements


def create_cover_page(styles):
    """Crea la pagina di copertina"""
    elements = []
    
    elements.append(Spacer(1, 5*cm))
    
    title = Paragraph(
        "MyGest - Documentazione Completa",
        styles['CoverTitle']
    )
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    subtitle = Paragraph(
        "Soluzione 2: Path Configurabili e Portabili",
        styles['Heading1']
    )
    elements.append(subtitle)
    elements.append(Spacer(1, 2*cm))
    
    info = [
        ["Soluzione", "Path configurabili senza .env"],
        ["Status", "COMPLETATO E TESTATO"],
        ["Data", datetime.now().strftime("%d/%m/%Y")],
        ["Versione", "1.0"],
        ["Test", "6/6 PASSATI"],
    ]
    
    table = Table(info, colWidths=[5*cm, 10*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    
    elements.append(Spacer(1, 2*cm))
    
    description = Paragraph(
        """
        Questa documentazione descrive l'implementazione completa della Soluzione 2
        per la gestione dei path configurabili in MyGest, risolvendo il problema
        del deploy in produzione dove .env e settings.py non vengono trasferiti.
        """,
        styles['Normal']
    )
    elements.append(description)
    
    elements.append(PageBreak())
    
    return elements


def create_toc(doc_files, styles):
    """Crea l'indice"""
    elements = []
    
    elements.append(Paragraph("Indice dei Contenuti", styles['Heading1']))
    elements.append(Spacer(1, 0.5*cm))
    
    for i, (title, _) in enumerate(doc_files, 1):
        toc_item = Paragraph(
            f"{i}. {title}",
            styles['TOC']
        )
        elements.append(toc_item)
        elements.append(Spacer(1, 0.2*cm))
    
    elements.append(PageBreak())
    
    return elements


def main():
    """Funzione principale"""
    
    print("=" * 70)
    print("Generazione PDF Documentazione Soluzione 2")
    print("=" * 70)
    print()
    
    # File da includere
    doc_files = [
        ("README - Soluzione 2", BASE_DIR / "docs" / "README_SOLUZIONE_2.md"),
        ("Quick Start", BASE_DIR / "docs" / "QUICK_START_SETTINGS.md"),
        ("Guida Completa Settings Local", BASE_DIR / "docs" / "GUIDA_SETTINGS_LOCAL.md"),
        ("Soluzione 2 - Completamento", BASE_DIR / "docs" / "SOLUZIONE_2_COMPLETATA.md"),
        ("Riepilogo Soluzioni Storage", BASE_DIR / "docs" / "RIEPILOGO_SOLUZIONI_STORAGE.md"),
    ]
    
    # Verifica file esistenti
    print("Verifica file...")
    for title, filepath in doc_files:
        if filepath.exists():
            print(f"  [OK] {title}")
        else:
            print(f"  [MANCA] {title} - {filepath}")
            print(f"  Rimuovo dalla lista...")
            doc_files = [(t, f) for t, f in doc_files if f != filepath]
    
    if not doc_files:
        print("\nERRORE: Nessun file documentazione trovato!")
        return 1
    
    print(f"\nFile da includere: {len(doc_files)}")
    print()
    
    # Output PDF
    output_dir = BASE_DIR / "docs"
    output_file = output_dir / f"Documentazione_Soluzione2_PathConfigurabili_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    print(f"Output: {output_file}")
    print()
    
    # Crea PDF
    doc = SimpleDocTemplate(
        str(output_file),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2.5*cm,
        title="MyGest - Soluzione 2: Path Configurabili",
        author="MyGest Development Team",
    )
    
    # Stili
    styles = getSampleStyleSheet()
    
    # Stile titolo copertina
    if 'CoverTitle' not in styles:
        styles.add(ParagraphStyle(
            name='CoverTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
    
    # Stile TOC
    if 'TOC' not in styles:
        styles.add(ParagraphStyle(
            name='TOC',
            parent=styles['Normal'],
            fontSize=11,
            leftIndent=20,
            spaceAfter=6,
        ))
    
    # Stile codice
    if 'CodeBlock' not in styles:
        styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leftIndent=10,
            rightIndent=10,
            spaceAfter=10,
            spaceBefore=10,
            backColor=colors.HexColor('#f5f5f5'),
            borderColor=colors.HexColor('#cccccc'),
            borderWidth=1,
            borderPadding=5,
        ))
    
    # Personalizza stili esistenti
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    styles['Normal'].alignment = TA_JUSTIFY
    
    styles['Heading1'].fontSize = 18
    styles['Heading1'].textColor = colors.HexColor('#2c3e50')
    styles['Heading1'].spaceAfter = 12
    styles['Heading1'].spaceBefore = 20
    
    styles['Heading2'].fontSize = 14
    styles['Heading2'].textColor = colors.HexColor('#34495e')
    styles['Heading2'].spaceAfter = 10
    styles['Heading2'].spaceBefore = 16
    
    styles['Heading3'].fontSize = 12
    styles['Heading3'].textColor = colors.HexColor('#465a6a')
    styles['Heading3'].spaceAfter = 8
    styles['Heading3'].spaceBefore = 12
    
    styles['Heading4'].fontSize = 11
    styles['Heading4'].textColor = colors.HexColor('#576a7a')
    styles['Heading4'].spaceAfter = 6
    styles['Heading4'].spaceBefore = 10
    
    # Story (contenuto)
    story = []
    
    # Copertina
    print("Generazione copertina...")
    story.extend(create_cover_page(styles))
    
    # Indice
    print("Generazione indice...")
    story.extend(create_toc(doc_files, styles))
    
    # Documenti
    for i, (title, filepath) in enumerate(doc_files, 1):
        print(f"[{i}/{len(doc_files)}] Elaborazione: {title}")
        
        # Titolo sezione
        story.append(Paragraph(f"{i}. {title}", styles['Heading1']))
        story.append(Spacer(1, 0.5*cm))
        
        # Leggi e converti contenuto
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            elements = parse_markdown_to_elements(content, styles)
            story.extend(elements)
            
            # PageBreak tra documenti (tranne l'ultimo)
            if i < len(doc_files):
                story.append(PageBreak())
        
        except Exception as e:
            print(f"  ERRORE: {type(e).__name__}")
            # Aggiungi messaggio di errore semplice
            story.append(Spacer(1, 0.3*cm))
            story.append(Preformatted(
                f"[Errore nel caricamento del documento: {type(e).__name__}]",
                styles['CodeBlock']
            ))
            story.append(Spacer(1, 0.3*cm))
            
            # PageBreak tra documenti (tranne l'ultimo)
            if i < len(doc_files):
                story.append(PageBreak())
    
    # Genera PDF
    print()
    print("Generazione PDF in corso...")
    try:
        doc.build(story, canvasmaker=NumberedCanvas)
        print()
        print("=" * 70)
        print("[OK] PDF generato con successo!")
        print("=" * 70)
        print()
        print(f"File: {output_file}")
        print(f"Dimensione: {output_file.stat().st_size / 1024:.1f} KB")
        print()
        
        return 0
    
    except Exception as e:
        print()
        print("=" * 70)
        print(f"[ERRORE] Generazione PDF fallita: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
