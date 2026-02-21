#!/usr/bin/env python3
"""
Script per generare HTML e PDF dalla guida Markdown

Usage:
    python docs/generate_guide.py
    
Output:
    - docs/GUIDA_DEPLOYMENT_SYNC.html
    - docs/GUIDA_DEPLOYMENT_SYNC.pdf
"""

import os
import sys
from pathlib import Path
import markdown
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

# Directory base
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR
PROJECT_ROOT = BASE_DIR.parent

# File input/output
MD_FILE = DOCS_DIR / "GUIDA_DEPLOYMENT_SYNC.md"
HTML_FILE = DOCS_DIR / "GUIDA_DEPLOYMENT_SYNC.html"
PDF_FILE = DOCS_DIR / "GUIDA_DEPLOYMENT_SYNC.pdf"


def read_markdown():
    """Legge il file Markdown"""
    print(f"📖 Reading {MD_FILE.name}...")
    with open(MD_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def markdown_to_html(md_content):
    """Converte Markdown in HTML con estensioni"""
    print("🔄 Converting Markdown to HTML...")
    
    # Estensioni Markdown
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.sane_lists',
        'markdown.extensions.nl2br',
    ]
    
    # Converti
    html_body = markdown.markdown(
        md_content,
        extensions=extensions,
        extension_configs={
            'markdown.extensions.codehilite': {
                'linenums': False,
                'guess_lang': True,
            },
            'markdown.extensions.toc': {
                'toc_depth': '2-4',
            }
        }
    )
    
    return html_body


def create_html_template(body_html):
    """Crea HTML completo con CSS"""
    css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Fira+Code:wght@400;500&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.7;
            color: #333;
            background: #f9fafb;
            padding: 0;
            font-size: 16px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.95;
        }
        
        /* Content */
        .content {
            padding: 2rem;
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700;
            color: #1e293b;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }
        
        h2 {
            font-size: 2rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 0.5rem;
            margin-top: 3rem;
        }
        
        h3 {
            font-size: 1.5rem;
            color: #475569;
        }
        
        h4 {
            font-size: 1.25rem;
            color: #64748b;
        }
        
        p {
            margin-bottom: 1rem;
            text-align: justify;
        }
        
        /* Links */
        a {
            color: #667eea;
            text-decoration: none;
            border-bottom: 1px solid transparent;
            transition: border-color 0.2s;
        }
        
        a:hover {
            border-bottom-color: #667eea;
        }
        
        /* Code */
        code {
            font-family: 'Fira Code', 'Courier New', monospace;
            background: #f1f5f9;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-size: 0.9em;
            color: #e11d48;
        }
        
        pre {
            background: #1e293b;
            color: #e2e8f0;
            padding: 1.5rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1.5rem 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        pre code {
            background: transparent;
            color: #e2e8f0;
            padding: 0;
            font-size: 0.9rem;
            line-height: 1.6;
        }
        
        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1.5rem 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        thead {
            background: #667eea;
            color: white;
        }
        
        th {
            padding: 1rem;
            text-align: left;
            font-weight: 600;
        }
        
        td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid #e2e8f0;
        }
        
        tbody tr:hover {
            background: #f8fafc;
        }
        
        /* Lists */
        ul, ol {
            margin-left: 2rem;
            margin-bottom: 1rem;
        }
        
        li {
            margin-bottom: 0.5rem;
        }
        
        /* Blockquotes */
        blockquote {
            border-left: 4px solid #667eea;
            padding-left: 1.5rem;
            margin: 1.5rem 0;
            color: #64748b;
            font-style: italic;
        }
        
        /* Alerts */
        .alert {
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin: 1.5rem 0;
            border-left: 4px solid;
        }
        
        .alert-warning {
            background: #fef3c7;
            border-color: #f59e0b;
            color: #92400e;
        }
        
        .alert-success {
            background: #d1fae5;
            border-color: #10b981;
            color: #065f46;
        }
        
        .alert-danger {
            background: #fee2e2;
            border-color: #ef4444;
            color: #991b1b;
        }
        
        /* Utility classes */
        .text-center {
            text-align: center;
        }
        
        .mt-4 {
            margin-top: 2rem;
        }
        
        .mb-4 {
            margin-bottom: 2rem;
        }
        
        /* Footer */
        .footer {
            background: #1e293b;
            color: #94a3b8;
            padding: 2rem;
            text-align: center;
            margin-top: 4rem;
        }
        
        .footer p {
            margin: 0.5rem 0;
        }
        
        /* Print styles */
        @media print {
            .container {
                box-shadow: none;
            }
            
            .header {
                background: #667eea;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            pre {
                background: #1e293b;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            a {
                color: #667eea;
            }
            
            h2 {
                page-break-before: always;
            }
            
            h2:first-of-type {
                page-break-before: auto;
            }
            
            pre, table {
                page-break-inside: avoid;
            }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8rem;
            }
            
            .content {
                padding: 1rem;
            }
            
            h2 {
                font-size: 1.5rem;
            }
            
            table {
                font-size: 0.9rem;
            }
            
            th, td {
                padding: 0.5rem;
            }
        }
        
        /* Syntax highlighting */
        .codehilite .hll { background-color: #49483e }
        .codehilite .c { color: #75715e } /* Comment */
        .codehilite .k { color: #66d9ef } /* Keyword */
        .codehilite .o { color: #f92672 } /* Operator */
        .codehilite .p { color: #f8f8f2 } /* Punctuation */
        .codehilite .s { color: #e6db74 } /* String */
        .codehilite .n { color: #f8f8f2 } /* Name */
        .codehilite .nf { color: #a6e22e } /* Name Function */
        .codehilite .nb { color: #f8f8f2 } /* Name Builtin */
        .codehilite .nc { color: #a6e22e } /* Name Class */
        .codehilite .m { color: #ae81ff } /* Number */
    </style>
    """
    
    html_template = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Guida operativa MyGest per deployment, sincronizzazione database e gestione archivio NAS">
    <meta name="author" content="MyGest Development Team">
    <title>MyGest - Guida Deployment e Sincronizzazione</title>
    {css}
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MyGest</h1>
            <p>Guida Operativa per Deployment e Sincronizzazione</p>
            <p style="margin-top: 1rem; font-size: 0.9rem;">Versione 1.0 - Febbraio 2026</p>
        </div>
        
        <div class="content">
            {body_html}
        </div>
        
        <div class="footer">
            <p><strong>MyGest Development Team</strong></p>
            <p>© 2026 - Tutti i diritti riservati</p>
            <p style="margin-top: 1rem; font-size: 0.9rem;">
                Per supporto: <a href="https://github.com/sandro6917/mygest/issues" style="color: #60a5fa;">GitHub Issues</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html_template


def save_html(html_content):
    """Salva HTML su file"""
    print(f"💾 Saving HTML to {HTML_FILE.name}...")
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ HTML saved: {HTML_FILE}")


def generate_pdf(html_content):
    """Genera PDF da HTML con WeasyPrint"""
    print(f"📄 Generating PDF...")
    
    try:
        # Font configuration
        font_config = FontConfiguration()
        
        # CSS per PDF (ottimizzazioni stampa)
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
                @top-right {
                    content: "MyGest - Guida Deployment";
                    font-size: 10pt;
                    color: #64748b;
                }
                @bottom-center {
                    content: "Pagina " counter(page) " di " counter(pages);
                    font-size: 10pt;
                    color: #64748b;
                }
            }
            
            h2 {
                page-break-before: always;
            }
            
            h2:first-of-type {
                page-break-before: auto;
            }
            
            pre, table, .alert {
                page-break-inside: avoid;
            }
            
            a {
                text-decoration: none;
            }
            
            a[href^="http"]:after {
                content: " (" attr(href) ")";
                font-size: 0.8em;
                color: #64748b;
            }
        ''', font_config=font_config)
        
        # Genera PDF
        HTML(string=html_content, base_url=str(DOCS_DIR)).write_pdf(
            PDF_FILE,
            stylesheets=[pdf_css],
            font_config=font_config
        )
        
        print(f"✅ PDF saved: {PDF_FILE}")
        
        # Dimensione file
        pdf_size = PDF_FILE.stat().st_size / (1024 * 1024)
        print(f"📊 PDF size: {pdf_size:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        print("ℹ️  Install WeasyPrint: pip install weasyprint")
        sys.exit(1)


def main():
    """Main execution"""
    print("\n" + "="*60)
    print("  MyGest - Guida Deployment Generator")
    print("="*60 + "\n")
    
    # Check file esistenza
    if not MD_FILE.exists():
        print(f"❌ Error: {MD_FILE} not found!")
        sys.exit(1)
    
    # 1. Leggi Markdown
    md_content = read_markdown()
    
    # 2. Converti in HTML
    html_body = markdown_to_html(md_content)
    
    # 3. Crea HTML completo
    html_full = create_html_template(html_body)
    
    # 4. Salva HTML
    save_html(html_full)
    
    # 5. Genera PDF
    generate_pdf(html_full)
    
    print("\n" + "="*60)
    print("✅ Generation completed successfully!")
    print("="*60)
    print(f"\n📁 Output files:")
    print(f"   - HTML: {HTML_FILE}")
    print(f"   - PDF:  {PDF_FILE}")
    print(f"\n🌐 Open HTML: file://{HTML_FILE.absolute()}")
    print()


if __name__ == "__main__":
    main()
