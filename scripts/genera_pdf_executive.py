#!/usr/bin/env python3
"""
Script per generare PDF dell'Executive Summary Conservazione Digitale
"""

import os
import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from datetime import datetime

def genera_pdf_executive():
    """Genera PDF dall'executive summary conservazione digitale"""
    
    # Path files
    base_dir = Path("/home/sandro/mygest")
    md_file = base_dir / "docs" / "CONSERVAZIONE_EXECUTIVE_SUMMARY.md"
    pdf_file = base_dir / "docs" / f"CONSERVAZIONE_EXECUTIVE_SUMMARY_{datetime.now().strftime('%Y%m%d')}.pdf"
    
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
    
    # Template HTML con styling executive
    html_template = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Conservazione Digitale - Executive Summary</title>
        <style>
            @page {{
                size: A4;
                margin: 2.5cm 2cm;
                @top-right {{
                    content: "Executive Summary";
                    font-size: 8pt;
                    color: #777;
                    font-style: italic;
                }}
                @bottom-center {{
                    content: "MyGest - Decision Support";
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
                font-family: "DejaVu Sans", Arial, sans-serif;
                font-size: 10.5pt;
                line-height: 1.65;
                color: #2c3e50;
                max-width: 100%;
            }}
            
            h1 {{
                color: #27ae60;
                font-size: 28pt;
                margin-top: 30pt;
                margin-bottom: 16pt;
                border-bottom: 4px solid #27ae60;
                padding-bottom: 10pt;
                page-break-before: always;
                font-weight: bold;
            }}
            
            h1:first-of-type {{
                page-break-before: auto;
            }}
            
            h2 {{
                color: #16a085;
                font-size: 19pt;
                margin-top: 22pt;
                margin-bottom: 12pt;
                border-bottom: 2px solid #48c9b0;
                padding-bottom: 5pt;
                font-weight: bold;
            }}
            
            h3 {{
                color: #1f618d;
                font-size: 15pt;
                margin-top: 16pt;
                margin-bottom: 10pt;
                font-weight: bold;
            }}
            
            h4 {{
                color: #34495e;
                font-size: 12pt;
                margin-top: 12pt;
                margin-bottom: 8pt;
                font-weight: bold;
            }}
            
            p {{
                margin: 10pt 0;
                text-align: justify;
            }}
            
            code {{
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 2px 6px;
                font-family: "DejaVu Sans Mono", "Courier New", monospace;
                font-size: 9pt;
                color: #e74c3c;
            }}
            
            pre {{
                background-color: #f8f9fa;
                border: 1px solid #bdc3c7;
                border-left: 4px solid #27ae60;
                border-radius: 3px;
                padding: 12pt;
                overflow-x: auto;
                margin: 12pt 0;
                font-family: "DejaVu Sans Mono", "Courier New", monospace;
                font-size: 8.5pt;
                line-height: 1.5;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background: none;
                border: none;
                padding: 0;
                color: #2c3e50;
            }}
            
            ul, ol {{
                margin: 10pt 0;
                padding-left: 28pt;
            }}
            
            li {{
                margin: 5pt 0;
            }}
            
            li::marker {{
                color: #27ae60;
                font-weight: bold;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 12pt 0;
                page-break-inside: avoid;
                font-size: 9.5pt;
            }}
            
            th {{
                background-color: #27ae60;
                color: white;
                padding: 10pt;
                text-align: left;
                font-weight: bold;
                border: 1px solid #229954;
            }}
            
            td {{
                border: 1px solid #bdc3c7;
                padding: 8pt;
            }}
            
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            
            blockquote {{
                border-left: 5px solid #27ae60;
                margin: 12pt 0;
                padding: 8pt 16pt;
                background-color: #d5f4e6;
                font-style: italic;
            }}
            
            hr {{
                border: none;
                border-top: 3px solid #27ae60;
                margin: 20pt 0;
            }}
            
            .title-page {{
                text-align: center;
                padding-top: 160pt;
                page-break-after: always;
            }}
            
            .title-page h1 {{
                font-size: 40pt;
                color: #27ae60;
                border: none;
                margin-bottom: 20pt;
            }}
            
            .title-page .subtitle {{
                font-size: 20pt;
                color: #16a085;
                margin-bottom: 15pt;
                font-weight: 600;
            }}
            
            .title-page .badge {{
                display: inline-block;
                background-color: #27ae60;
                color: white;
                padding: 8pt 16pt;
                border-radius: 20pt;
                font-size: 12pt;
                font-weight: bold;
                margin: 15pt 0;
            }}
            
            .title-page .info {{
                font-size: 11pt;
                color: #7f8c8d;
                margin-top: 60pt;
            }}
            
            /* Highlight boxes */
            .highlight-green {{
                background-color: #d5f4e6;
                border: 2px solid #27ae60;
                border-radius: 5px;
                padding: 12pt;
                margin: 12pt 0;
            }}
            
            .highlight-blue {{
                background-color: #d6eaf8;
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 12pt;
                margin: 12pt 0;
            }}
            
            .highlight-yellow {{
                background-color: #fcf3cf;
                border: 2px solid #f39c12;
                border-radius: 5px;
                padding: 12pt;
                margin: 12pt 0;
            }}
            
            .highlight-red {{
                background-color: #fadbd8;
                border: 2px solid #e74c3c;
                border-radius: 5px;
                padding: 12pt;
                margin: 12pt 0;
            }}
            
            /* Checkmarks e simboli */
            .checkmark {{
                color: #27ae60;
                font-weight: bold;
                font-size: 12pt;
            }}
            
            .warning {{
                color: #f39c12;
                font-weight: bold;
                font-size: 12pt;
            }}
            
            strong {{
                color: #16a085;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="title-page">
            <h1>MyGest</h1>
            <div class="subtitle">Conservazione Digitale a Norma</div>
            <div class="badge">EXECUTIVE SUMMARY</div>
            <div class="subtitle">Analisi Strategica e Decisionale</div>
            <div class="info">
                <p><strong>Versione</strong>: 1.0</p>
                <p><strong>Data</strong>: 17 Novembre 2025</p>
                <p><strong>Destinatari</strong>: Management e Decision Maker</p>
                <p><strong>Tipo</strong>: Business Case e ROI Analysis</p>
            </div>
        </div>
        
        {html_content}
        
        <hr>
        <div style="text-align: center; color: #7f8c8d; font-size: 9pt; margin-top: 25pt;">
            <p><strong>MyGest - Sistema di Gestione Documentale</strong></p>
            <p>Executive Summary - Conservazione Digitale a Norma</p>
            <p>© 2025 - Confidenziale</p>
        </div>
    </body>
    </html>
    """
    
    print("Generazione PDF Executive Summary...")
    
    # Genera PDF
    HTML(string=html_template).write_pdf(
        pdf_file,
        stylesheets=[CSS(string="""
            @page {
                margin: 2.5cm 2cm;
            }
        """)]
    )
    
    size_kb = pdf_file.stat().st_size / 1024
    
    print(f"\n{'='*60}")
    print(f"✓ PDF Executive Summary generato!")
    print(f"{'='*60}")
    print(f"  📄 File: {pdf_file.name}")
    print(f"  📂 Path: {pdf_file.parent}")
    print(f"  📊 Dimensione: {size_kb:.1f} KB")
    print(f"  📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    return pdf_file

if __name__ == "__main__":
    try:
        pdf_path = genera_pdf_executive()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ ERRORE: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
