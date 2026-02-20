#!/usr/bin/env python3
"""
Script per generare PDF della guida File Storage e Deploy
"""

import os
import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from datetime import datetime

def genera_pdf_guida_storage():
    """Genera PDF dalla guida markdown"""
    
    # Path files
    base_dir = Path("/home/sandro/mygest")
    md_file = base_dir / "docs" / "GUIDA_FILE_STORAGE_E_DEPLOY.md"
    pdf_file = base_dir / "docs" / f"GUIDA_FILE_STORAGE_E_DEPLOY_{datetime.now().strftime('%Y%m%d')}.pdf"
    
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
    
    # Template HTML completo
    html_template = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Guida File Storage e Deploy - MyGest</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                @top-right {{
                    content: "MyGest - Storage & Deploy";
                    font-size: 9pt;
                    color: #666;
                }}
                @bottom-right {{
                    content: "Pagina " counter(page) " di " counter(pages);
                    font-size: 9pt;
                    color: #666;
                }}
            }}
            
            body {{
                font-family: "DejaVu Sans", Arial, sans-serif;
                font-size: 10pt;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
            }}
            
            h1 {{
                color: #2c3e50;
                font-size: 24pt;
                margin-top: 30pt;
                margin-bottom: 15pt;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10pt;
                page-break-before: always;
            }}
            
            h1:first-of-type {{
                page-break-before: auto;
            }}
            
            h2 {{
                color: #34495e;
                font-size: 18pt;
                margin-top: 20pt;
                margin-bottom: 12pt;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5pt;
            }}
            
            h3 {{
                color: #2c3e50;
                font-size: 14pt;
                margin-top: 15pt;
                margin-bottom: 10pt;
            }}
            
            h4 {{
                color: #555;
                font-size: 12pt;
                margin-top: 12pt;
                margin-bottom: 8pt;
            }}
            
            p {{
                margin: 8pt 0;
                text-align: justify;
            }}
            
            code {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 2px 5px;
                font-family: "DejaVu Sans Mono", "Courier New", monospace;
                font-size: 9pt;
                color: #c7254e;
            }}
            
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-left: 3px solid #3498db;
                border-radius: 3px;
                padding: 10pt;
                overflow-x: auto;
                margin: 10pt 0;
                font-family: "DejaVu Sans Mono", "Courier New", monospace;
                font-size: 8pt;
                line-height: 1.4;
                page-break-inside: avoid;
            }}
            
            pre code {{
                background: none;
                border: none;
                padding: 0;
                color: #333;
            }}
            
            ul, ol {{
                margin: 8pt 0;
                padding-left: 25pt;
            }}
            
            li {{
                margin: 4pt 0;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 10pt 0;
                page-break-inside: avoid;
            }}
            
            th {{
                background-color: #3498db;
                color: white;
                padding: 8pt;
                text-align: left;
                font-weight: bold;
            }}
            
            td {{
                border: 1px solid #ddd;
                padding: 8pt;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 10pt 0;
                padding: 5pt 15pt;
                background-color: #f0f7fb;
                font-style: italic;
            }}
            
            hr {{
                border: none;
                border-top: 2px solid #3498db;
                margin: 20pt 0;
            }}
            
            .title-page {{
                text-align: center;
                padding-top: 150pt;
                page-break-after: always;
            }}
            
            .title-page h1 {{
                font-size: 36pt;
                color: #2c3e50;
                border: none;
                margin-bottom: 20pt;
            }}
            
            .title-page .subtitle {{
                font-size: 18pt;
                color: #7f8c8d;
                margin-bottom: 40pt;
            }}
            
            .title-page .info {{
                font-size: 12pt;
                color: #95a5a6;
                margin-top: 60pt;
            }}
            
            .warning {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 10pt;
                margin: 10pt 0;
            }}
            
            .info-box {{
                background-color: #d1ecf1;
                border-left: 4px solid #17a2b8;
                padding: 10pt;
                margin: 10pt 0;
            }}
            
            .success {{
                background-color: #d4edda;
                border-left: 4px solid #28a745;
                padding: 10pt;
                margin: 10pt 0;
            }}
        </style>
    </head>
    <body>
        <div class="title-page">
            <h1>MyGest</h1>
            <div class="subtitle">Guida Completa: File Storage e Deploy</div>
            <div class="subtitle">Architettura, Implementazione e Procedure</div>
            <div class="info">
                <p>Versione: 1.0</p>
                <p>Data: 17 Novembre 2025</p>
                <p>Autore: Sistema MyGest</p>
            </div>
        </div>
        
        {html_content}
    </body>
    </html>
    """
    
    print("Generazione PDF...")
    
    # Genera PDF
    HTML(string=html_template).write_pdf(
        pdf_file,
        stylesheets=[CSS(string="""
            @page {
                margin: 2cm;
            }
        """)]
    )
    
    print(f"\n✓ PDF generato con successo!")
    print(f"  File: {pdf_file}")
    print(f"  Dimensione: {pdf_file.stat().st_size / 1024:.1f} KB")
    
    return pdf_file

if __name__ == "__main__":
    try:
        pdf_path = genera_pdf_guida_storage()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Errore nella generazione PDF: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
