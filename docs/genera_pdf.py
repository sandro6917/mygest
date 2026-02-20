#!/usr/bin/env python3
"""
Script per generare PDF dalla guida Markdown usando WeasyPrint
"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path
import sys

def genera_pdf(input_md: str, output_pdf: str):
    """
    Converte un file Markdown in PDF con stile professionale
    
    Args:
        input_md: Path del file Markdown di input
        output_pdf: Path del file PDF di output
    """
    
    # Leggi il file Markdown
    with open(input_md, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Converti Markdown in HTML con estensioni
    md = markdown.Markdown(extensions=[
        'extra',           # Tabelle, note a piè di pagina, etc.
        'codehilite',      # Syntax highlighting
        'toc',             # Table of contents
        'sane_lists',      # Liste migliorate
        'nl2br',           # Newline to break
        'smarty'           # Smart quotes
    ])
    
    html_content = md.convert(md_content)
    
    # CSS professionale per il PDF
    css_style = """
    @page {
        size: A4;
        margin: 2.5cm 2cm;
        
        @top-right {
            content: "MyGest - Guida Anagrafiche";
            font-size: 9pt;
            color: #666;
        }
        
        @bottom-center {
            content: "Pagina " counter(page) " di " counter(pages);
            font-size: 9pt;
            color: #666;
        }
    }
    
    body {
        font-family: 'DejaVu Sans', Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.6;
        color: #333;
    }
    
    h1 {
        color: #2c3e50;
        font-size: 24pt;
        margin-top: 0;
        margin-bottom: 12pt;
        padding-bottom: 8pt;
        border-bottom: 3px solid #3498db;
        page-break-after: avoid;
    }
    
    h2 {
        color: #34495e;
        font-size: 18pt;
        margin-top: 18pt;
        margin-bottom: 10pt;
        padding-bottom: 4pt;
        border-bottom: 2px solid #95a5a6;
        page-break-after: avoid;
    }
    
    h3 {
        color: #555;
        font-size: 14pt;
        margin-top: 14pt;
        margin-bottom: 8pt;
        page-break-after: avoid;
    }
    
    h4 {
        color: #666;
        font-size: 12pt;
        margin-top: 12pt;
        margin-bottom: 6pt;
        page-break-after: avoid;
    }
    
    p {
        margin-bottom: 8pt;
        text-align: justify;
    }
    
    code {
        background-color: #f4f4f4;
        padding: 2pt 4pt;
        border-radius: 3pt;
        font-family: 'DejaVu Sans Mono', 'Courier New', monospace;
        font-size: 9pt;
        color: #c7254e;
    }
    
    pre {
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-left: 4px solid #3498db;
        padding: 10pt;
        margin: 10pt 0;
        border-radius: 4pt;
        overflow-x: auto;
        page-break-inside: avoid;
    }
    
    pre code {
        background-color: transparent;
        padding: 0;
        color: #333;
        font-size: 8.5pt;
    }
    
    ul, ol {
        margin-bottom: 10pt;
        padding-left: 20pt;
    }
    
    li {
        margin-bottom: 4pt;
    }
    
    strong {
        color: #2c3e50;
        font-weight: bold;
    }
    
    em {
        color: #555;
        font-style: italic;
    }
    
    a {
        color: #3498db;
        text-decoration: none;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12pt 0;
        page-break-inside: avoid;
    }
    
    th {
        background-color: #3498db;
        color: white;
        padding: 8pt;
        text-align: left;
        font-weight: bold;
    }
    
    td {
        border: 1px solid #ddd;
        padding: 6pt 8pt;
    }
    
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    
    blockquote {
        border-left: 4px solid #3498db;
        background-color: #f0f7fb;
        padding: 10pt 12pt;
        margin: 10pt 0;
        font-style: italic;
        page-break-inside: avoid;
    }
    
    hr {
        border: none;
        border-top: 2px solid #ddd;
        margin: 20pt 0;
    }
    
    /* Evita interruzioni di pagina indesiderate */
    h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
    }
    
    p, li {
        orphans: 3;
        widows: 3;
    }
    
    /* Stile per badge/etichette */
    .badge {
        display: inline-block;
        padding: 2pt 6pt;
        background-color: #3498db;
        color: white;
        border-radius: 3pt;
        font-size: 8pt;
        font-weight: bold;
    }
    
    /* Prima pagina */
    h1:first-of-type {
        font-size: 32pt;
        text-align: center;
        margin-top: 100pt;
        margin-bottom: 20pt;
        border: none;
    }
    
    /* TOC styling */
    .toc {
        background-color: #f8f9fa;
        padding: 15pt;
        border: 1px solid #ddd;
        border-radius: 4pt;
        margin-bottom: 20pt;
    }
    
    .toc ul {
        list-style-type: none;
        padding-left: 10pt;
    }
    
    .toc a {
        color: #2c3e50;
    }
    """
    
    # Crea HTML completo con meta e stili
    html_full = f"""
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <title>Guida Modulo Anagrafiche - MyGest</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Genera PDF
    print(f"📄 Conversione Markdown → HTML completata")
    print(f"📝 Generazione PDF in corso...")
    
    HTML(string=html_full).write_pdf(
        output_pdf,
        stylesheets=[CSS(string=css_style)]
    )
    
    # Verifica dimensione file
    file_size = Path(output_pdf).stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"✅ PDF generato con successo!")
    print(f"📦 File: {output_pdf}")
    print(f"📊 Dimensione: {file_size_mb:.2f} MB")


if __name__ == "__main__":
    # Path dei file da argomenti o default
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        input_file = "GUIDA_MODULO_ANAGRAFICHE.md"
        output_file = "GUIDA_MODULO_ANAGRAFICHE.pdf"
    
    # Verifica esistenza file input
    if not Path(input_file).exists():
        print(f"❌ Errore: File {input_file} non trovato!")
        sys.exit(1)
    
    # Estrai titolo dal nome file
    doc_title = Path(input_file).stem.replace('_', ' ').title()
    
    print("=" * 60)
    print(f"  GENERAZIONE PDF - {doc_title}")
    print("=" * 60)
    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print("=" * 60)
    print()
    
    try:
        genera_pdf(input_file, output_file)
        print()
        print("=" * 60)
        print("  ✅ OPERAZIONE COMPLETATA CON SUCCESSO")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"  ❌ ERRORE: {str(e)}")
        print("=" * 60)
        sys.exit(1)
