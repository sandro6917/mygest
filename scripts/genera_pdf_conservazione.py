#!/usr/bin/env python3
"""
Script per generare PDF dell'analisi Conservazione Digitale a Norma
"""

import os
import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from datetime import datetime

def genera_pdf_conservazione():
    """Genera PDF dall'analisi conservazione digitale"""
    
    # Path files
    base_dir = Path("/home/sandro/mygest")
    md_file = base_dir / "docs" / "CONSERVAZIONE_DIGITALE_ANALISI.md"
    pdf_file = base_dir / "docs" / f"CONSERVAZIONE_DIGITALE_ANALISI_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    print(f"Lettura file: {md_file}")
    
    # Leggi markdown
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # Converti in HTML
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'extra',
            'codehilite',
            'toc',
            'tables',
            'fenced_code',
        ]
    )
    
    # Template HTML completo con styling avanzato
    html_template = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Conservazione Digitale a Norma - MyGest</title>
        <style>
            @page {{
                size: A4;
                margin: 2.5cm 2cm;
                @top-right {{
                    content: "Conservazione Digitale a Norma";
                    font-size: 8pt;
                    color: #777;
                    font-style: italic;
                }}
                @bottom-center {{
                    content: "MyGest - Analisi e Progettazione";
                    font-size: 8pt;
                    color: #777;
                }}
                @bottom-right {{
                    content: "Pag. " counter(page);
                    font-size: 8pt;
                    color: #777;
                }}
            }}
            
            body {{
                font-family: "DejaVu Sans", "Liberation Sans", Arial, sans-serif;
                font-size: 10pt;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
            }}
            
            /* Titoli */
            h1 {{
                color: #1a5490;
                font-size: 26pt;
                margin-top: 35pt;
                margin-bottom: 18pt;
                border-bottom: 4px solid #1a5490;
                padding-bottom: 12pt;
                page-break-before: always;
                font-weight: bold;
            }}
            
            h1:first-of-type {{
                page-break-before: auto;
            }}
            
            h2 {{
                color: #2874a6;
                font-size: 18pt;
                margin-top: 25pt;
                margin-bottom: 14pt;
                border-bottom: 2px solid #5dade2;
                padding-bottom: 6pt;
                font-weight: bold;
            }}
            
            h3 {{
                color: #1f618d;
                font-size: 14pt;
                margin-top: 18pt;
                margin-bottom: 10pt;
                font-weight: bold;
            }}
            
            h4 {{
                color: #34495e;
                font-size: 12pt;
                margin-top: 14pt;
                margin-bottom: 8pt;
                font-weight: bold;
            }}
            
            /* Paragrafi */
            p {{
                margin: 10pt 0;
                text-align: justify;
            }}
            
            /* Codice inline */
            code {{
                background-color: #f4f6f7;
                border: 1px solid #d5dbdb;
                border-radius: 3px;
                padding: 2px 6px;
                font-family: "DejaVu Sans Mono", "Liberation Mono", "Courier New", monospace;
                font-size: 9pt;
                color: #c0392b;
                white-space: nowrap;
            }}
            
            /* Blocchi di codice */
            pre {{
                background-color: #f8f9fa;
                border: 1px solid #d5dbdb;
                border-left: 4px solid #3498db;
                border-radius: 4px;
                padding: 12pt;
                overflow-x: auto;
                margin: 12pt 0;
                font-family: "DejaVu Sans Mono", "Liberation Mono", "Courier New", monospace;
                font-size: 8.5pt;
                line-height: 1.5;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background: none;
                border: none;
                padding: 0;
                color: #2c3e50;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            
            /* Liste */
            ul, ol {{
                margin: 10pt 0;
                padding-left: 28pt;
            }}
            
            li {{
                margin: 5pt 0;
                line-height: 1.5;
            }}
            
            li::marker {{
                color: #3498db;
                font-weight: bold;
            }}
            
            /* Tabelle */
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 14pt 0;
                page-break-inside: avoid;
                font-size: 9.5pt;
            }}
            
            th {{
                background-color: #2874a6;
                color: white;
                padding: 10pt;
                text-align: left;
                font-weight: bold;
                border: 1px solid #1a5490;
            }}
            
            td {{
                border: 1px solid #d5dbdb;
                padding: 8pt;
                vertical-align: top;
            }}
            
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            
            tr:hover {{
                background-color: #ebf5fb;
            }}
            
            /* Blockquote */
            blockquote {{
                border-left: 5px solid #3498db;
                margin: 12pt 0;
                padding: 8pt 16pt;
                background-color: #ebf5fb;
                font-style: italic;
                page-break-inside: avoid;
            }}
            
            /* Linea orizzontale */
            hr {{
                border: none;
                border-top: 3px solid #3498db;
                margin: 25pt 0;
            }}
            
            /* Pagina titolo */
            .title-page {{
                text-align: center;
                padding-top: 180pt;
                page-break-after: always;
            }}
            
            .title-page h1 {{
                font-size: 42pt;
                color: #1a5490;
                border: none;
                margin-bottom: 25pt;
                font-weight: bold;
            }}
            
            .title-page .subtitle {{
                font-size: 20pt;
                color: #5d6d7e;
                margin-bottom: 15pt;
                font-weight: normal;
            }}
            
            .title-page .info {{
                font-size: 11pt;
                color: #7f8c8d;
                margin-top: 80pt;
                line-height: 1.8;
            }}
            
            /* Box colorati */
            .warning-box {{
                background-color: #fcf3cf;
                border-left: 5px solid #f39c12;
                padding: 12pt;
                margin: 14pt 0;
                page-break-inside: avoid;
            }}
            
            .info-box {{
                background-color: #d6eaf8;
                border-left: 5px solid #3498db;
                padding: 12pt;
                margin: 14pt 0;
                page-break-inside: avoid;
            }}
            
            .success-box {{
                background-color: #d5f4e6;
                border-left: 5px solid #27ae60;
                padding: 12pt;
                margin: 14pt 0;
                page-break-inside: avoid;
            }}
            
            .danger-box {{
                background-color: #fadbd8;
                border-left: 5px solid #e74c3c;
                padding: 12pt;
                margin: 14pt 0;
                page-break-inside: avoid;
            }}
            
            /* Evidenziazioni */
            strong {{
                color: #1a5490;
                font-weight: bold;
            }}
            
            em {{
                color: #34495e;
                font-style: italic;
            }}
            
            /* Link (se presenti) */
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            
            /* Evita interruzioni di pagina indesiderate */
            h1, h2, h3, h4 {{
                page-break-after: avoid;
            }}
            
            table, figure {{
                page-break-inside: avoid;
            }}
            
            /* Numerazione checklist */
            .checklist {{
                list-style-type: none;
                padding-left: 0;
            }}
            
            .checklist li {{
                padding-left: 30pt;
                position: relative;
            }}
            
            .checklist li:before {{
                content: "☐";
                position: absolute;
                left: 0;
                color: #3498db;
                font-size: 14pt;
            }}
        </style>
    </head>
    <body>
        <!-- Pagina Titolo -->
        <div class="title-page">
            <h1>MyGest</h1>
            <div class="subtitle">Conservazione Digitale a Norma</div>
            <div class="subtitle">Analisi Completa e Progettazione</div>
            <div class="info">
                <p><strong>Versione</strong>: 1.0</p>
                <p><strong>Data</strong>: 17 Novembre 2025</p>
                <p><strong>Documento</strong>: Analisi Tecnica Completa</p>
                <p><strong>Autore</strong>: Team Sviluppo MyGest</p>
            </div>
        </div>
        
        <!-- Contenuto -->
        {html_content}
        
        <!-- Footer finale -->
        <hr>
        <div style="text-align: center; color: #7f8c8d; font-size: 9pt; margin-top: 30pt;">
            <p><strong>MyGest - Sistema di Gestione Documentale</strong></p>
            <p>Conservazione Digitale a Norma secondo normativa AgID</p>
            <p>© 2025 - Tutti i diritti riservati</p>
        </div>
    </body>
    </html>
    """
    
    print("Generazione PDF in corso...")
    print("(Questo potrebbe richiedere qualche minuto per la complessità del documento)")
    
    # Genera PDF
    HTML(string=html_template).write_pdf(
        pdf_file,
        stylesheets=[CSS(string="""
            @page {
                margin: 2.5cm 2cm;
            }
        """)]
    )
    
    # Statistiche file
    size_kb = pdf_file.stat().st_size / 1024
    
    print(f"\n{'='*60}")
    print(f"✓ PDF generato con successo!")
    print(f"{'='*60}")
    print(f"  📄 File: {pdf_file.name}")
    print(f"  📂 Path: {pdf_file.parent}")
    print(f"  📊 Dimensione: {size_kb:.1f} KB")
    print(f"  📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    return pdf_file

if __name__ == "__main__":
    try:
        pdf_path = genera_pdf_conservazione()
        sys.exit(0)
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"✗ ERRORE nella generazione PDF")
        print(f"{'='*60}")
        print(f"  Errore: {e}")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
