#!/usr/bin/env python
"""
Script per dividere il file TESTI_ESTRATTI_OCR_COMPLETI.md in file separati
per tipo documento, convertirli in PDF e zipparli.
"""

import os
import re
from pathlib import Path
import subprocess
import zipfile
from datetime import datetime


def split_by_document_type(input_file):
    """Divide il file markdown in file separati per tipo documento."""
    
    print("\n" + "="*80)
    print("📄 DIVISIONE FILE PER TIPO DOCUMENTO")
    print("="*80)
    
    # Crea cartella output
    output_dir = Path(__file__).parent / 'testi_estratti_per_tipo'
    output_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Cartella output: {output_dir}")
    
    # Leggi file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern per identificare le sezioni di tipo documento
    # ## 📂 Tipo Documento: UNILAV
    tipo_pattern = re.compile(r'^## 📂 Tipo Documento: (.+)$', re.MULTILINE)
    
    # Trova tutte le sezioni
    matches = list(tipo_pattern.finditer(content))
    
    print(f"\n✅ Trovate {len(matches)} sezioni di tipo documento")
    
    # Header comune per tutti i file
    header_lines = []
    first_match_pos = matches[0].start() if matches else len(content)
    header = content[:first_match_pos]
    
    # File creati
    files_created = []
    
    # Estrai ogni sezione
    for i, match in enumerate(matches):
        tipo_code = match.group(1).strip()
        
        # Determina inizio e fine sezione
        start_pos = match.start()
        
        if i < len(matches) - 1:
            # Fine sezione è l'inizio della prossima
            end_pos = matches[i + 1].start()
        else:
            # Ultima sezione va fino alla fine del file
            end_pos = len(content)
        
        section_content = content[start_pos:end_pos]
        
        # Nome file safe (rimuovi caratteri speciali)
        safe_name = re.sub(r'[^\w\-]', '_', tipo_code)
        output_file = output_dir / f"{safe_name}.md"
        
        # Scrivi file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Aggiungi header personalizzato
            f.write(f"# 📄 Testi Estratti - Tipo Documento: {tipo_code}\n\n")
            f.write(f"**Generato**: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            f.write("---\n\n")
            f.write(section_content)
        
        files_created.append(output_file)
        
        # Conta documenti in questa sezione
        doc_count = len(re.findall(r'^### 📄 Documento', section_content, re.MULTILINE))
        
        print(f"   ✅ {tipo_code:15s} → {output_file.name:30s} ({doc_count} documenti)")
    
    print(f"\n✅ Creati {len(files_created)} file markdown")
    
    return output_dir, files_created


def convert_to_pdf(markdown_files, output_dir):
    """Converte i file markdown in PDF usando Python puro (weasyprint/reportlab)."""
    
    print("\n" + "="*80)
    print("📄 CONVERSIONE MARKDOWN → PDF")
    print("="*80)
    
    pdf_dir = output_dir / 'pdf'
    pdf_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Cartella PDF: {pdf_dir}")
    
    # Prova importi Python per PDF
    weasyprint_available = False
    reportlab_available = False
    markdown2_available = False
    
    try:
        import weasyprint
        weasyprint_available = True
        print("\n✅ WeasyPrint disponibile - uso WeasyPrint")
    except ImportError:
        print("\n⚠️  WeasyPrint non disponibile")
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        reportlab_available = True
        if not weasyprint_available:
            print("✅ ReportLab disponibile - uso ReportLab")
    except ImportError:
        if not weasyprint_available:
            print("⚠️  ReportLab non disponibile")
    
    try:
        import markdown2
        markdown2_available = True
    except ImportError:
        pass
    
    if not weasyprint_available and not reportlab_available:
        print("\n❌ Nessuna libreria PDF disponibile!")
        print("   Installare con: pip install weasyprint")
        print("   oppure: pip install reportlab")
        print("\n   Zippo solo i file Markdown...")
        return []
    
    pdf_files = []
    errors = []
    
    for md_file in markdown_files:
        pdf_file = pdf_dir / f"{md_file.stem}.pdf"
        
        print(f"\n   🔄 Convertendo: {md_file.name} → {pdf_file.name}")
        
        try:
            # Leggi markdown
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            if weasyprint_available:
                # Usa WeasyPrint (migliore qualità)
                import weasyprint
                from weasyprint import HTML, CSS
                
                # Converti MD in HTML semplice
                html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'DejaVu Sans', Arial, sans-serif;
            font-size: 9pt;
            line-height: 1.4;
            margin: 1cm;
        }}
        pre {{
            background: #f4f4f4;
            border-left: 3px solid #4CAF50;
            padding: 10px;
            font-size: 8pt;
            overflow-wrap: break-word;
            white-space: pre-wrap;
        }}
        h1, h2, h3 {{ color: #333; page-break-after: avoid; }}
        h1 {{ font-size: 16pt; }}
        h2 {{ font-size: 14pt; }}
        h3 {{ font-size: 12pt; }}
        table {{ border-collapse: collapse; width: 100%; font-size: 8pt; }}
        th, td {{ border: 1px solid #ddd; padding: 5px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
    </style>
</head>
<body>
<pre>{md_content}</pre>
</body>
</html>
"""
                
                HTML(string=html_content).write_pdf(pdf_file)
                
                size_kb = os.path.getsize(pdf_file) / 1024
                print(f"      ✅ PDF creato: {size_kb:.2f} KB (WeasyPrint)")
                pdf_files.append(pdf_file)
                
            elif reportlab_available:
                # Usa ReportLab (fallback)
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import cm
                from reportlab.lib.enums import TA_LEFT
                
                doc = SimpleDocTemplate(
                    str(pdf_file),
                    pagesize=A4,
                    rightMargin=1.5*cm,
                    leftMargin=1.5*cm,
                    topMargin=1.5*cm,
                    bottomMargin=1.5*cm
                )
                
                styles = getSampleStyleSheet()
                code_style = ParagraphStyle(
                    'Code',
                    parent=styles['Code'],
                    fontSize=7,
                    leading=9,
                    leftIndent=0,
                    rightIndent=0,
                    alignment=TA_LEFT,
                    fontName='Courier',
                    wordWrap='LTR'
                )
                
                story = []
                
                # Aggiungi contenuto come preformatted
                # Dividi in chunk per evitare overflow
                chunk_size = 5000
                for i in range(0, len(md_content), chunk_size):
                    chunk = md_content[i:i+chunk_size]
                    p = Preformatted(chunk, code_style)
                    story.append(p)
                    if i + chunk_size < len(md_content):
                        story.append(Spacer(1, 0.2*cm))
                
                doc.build(story)
                
                size_kb = os.path.getsize(pdf_file) / 1024
                print(f"      ✅ PDF creato: {size_kb:.2f} KB (ReportLab)")
                pdf_files.append(pdf_file)
        
        except Exception as e:
            print(f"      ❌ Errore: {str(e)[:100]}")
            errors.append((md_file.name, str(e)))
    
    print(f"\n{'='*80}")
    print(f"✅ Convertiti {len(pdf_files)}/{len(markdown_files)} file in PDF")
    
    if errors:
        print(f"\n⚠️  Errori durante conversione ({len(errors)}):")
        for filename, error in errors[:5]:
            print(f"   - {filename}: {error[:100]}")
        if len(errors) > 5:
            print(f"   ... e altri {len(errors) - 5} errori")
    
    return pdf_files


def convert_to_html(markdown_files, output_dir):
    """Conversione alternativa in HTML se PDF non disponibile."""
    
    print("\n" + "="*80)
    print("📄 CONVERSIONE MARKDOWN → HTML (alternativa)")
    print("="*80)
    
    html_dir = output_dir / 'html'
    html_dir.mkdir(exist_ok=True)
    
    html_files = []
    
    for md_file in markdown_files:
        html_file = html_dir / f"{md_file.stem}.html"
        
        # Leggi markdown
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # HTML template semplice
        html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{md_file.stem}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background: #f5f5f5;
        }}
        pre {{
            background: #f4f4f4;
            border: 1px solid #ddd;
            border-left: 3px solid #4CAF50;
            padding: 15px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        h1, h2, h3, h4 {{
            color: #333;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
        }}
    </style>
</head>
<body>
<pre>{md_content}</pre>
</body>
</html>
"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        html_files.append(html_file)
        print(f"   ✅ {md_file.name} → {html_file.name}")
    
    print(f"\n✅ Creati {len(html_files)} file HTML")
    
    return html_files


def create_zip_archive(files, output_dir):
    """Crea archivio ZIP con tutti i file."""
    
    print("\n" + "="*80)
    print("📦 CREAZIONE ARCHIVIO ZIP")
    print("="*80)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_file = output_dir.parent / f'testi_estratti_training_{timestamp}.zip'
    
    print(f"\n📁 File ZIP: {zip_file}")
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            # Aggiungi file allo zip con path relativo
            arcname = file.relative_to(output_dir.parent)
            zipf.write(file, arcname=arcname)
            
            size_kb = os.path.getsize(file) / 1024
            print(f"   ✅ Aggiunto: {arcname} ({size_kb:.2f} KB)")
    
    zip_size_mb = os.path.getsize(zip_file) / (1024 * 1024)
    
    print(f"\n{'='*80}")
    print(f"✅ Archivio creato: {zip_file.name}")
    print(f"   Dimensione: {zip_size_mb:.2f} MB")
    print(f"   File inclusi: {len(files)}")
    
    return zip_file


def main():
    """Main function."""
    
    print("\n" + "="*80)
    print("🚀 SPLIT, CONVERT TO PDF & ZIP - Testi Estratti Training")
    print("="*80)
    
    # File input
    input_file = Path(__file__).parent / 'TESTI_ESTRATTI_OCR_COMPLETI.md'
    
    if not input_file.exists():
        print(f"\n❌ ERRORE: File non trovato: {input_file}")
        return
    
    print(f"\n📄 File input: {input_file}")
    print(f"   Dimensione: {os.path.getsize(input_file) / (1024*1024):.2f} MB")
    
    # Step 1: Dividi per tipo documento
    output_dir, markdown_files = split_by_document_type(input_file)
    
    # Step 2: Converti in PDF
    converted_files = convert_to_pdf(markdown_files, output_dir)
    
    # Step 3: Crea ZIP
    # Includi anche i file markdown originali
    all_files = list(markdown_files) + list(converted_files)
    
    zip_file = create_zip_archive(all_files, output_dir)
    
    # Riepilogo finale
    print("\n" + "="*80)
    print("📊 RIEPILOGO FINALE")
    print("="*80)
    print(f"\n✅ File Markdown creati: {len(markdown_files)}")
    print(f"✅ File PDF/HTML creati: {len(converted_files)}")
    print(f"✅ Archivio ZIP: {zip_file}")
    print(f"\nCartelle create:")
    print(f"   📁 {output_dir}")
    print(f"   📁 {output_dir / 'pdf' if (output_dir / 'pdf').exists() else output_dir / 'html'}")
    print("\n" + "="*80)


if __name__ == '__main__':
    main()
