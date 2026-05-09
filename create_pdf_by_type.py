#!/usr/bin/env python
"""
Divide il file TESTI_ESTRATTI_OCR_COMPLETI.md in file separati per tipo documento,
converte ogni file in PDF usando WeasyPrint e crea un archivio ZIP.
"""

import os
import re
import zipfile
from pathlib import Path
from markdown2 import markdown
from weasyprint import HTML, CSS

def split_by_document_type():
    """Legge il file grande e lo divide per tipo documento."""
    
    input_file = Path(__file__).parent / 'TESTI_ESTRATTI_OCR_COMPLETI.md'
    output_dir = Path(__file__).parent / 'testi_per_tipo'
    pdf_dir = Path(__file__).parent / 'testi_pdf'
    
    # Crea directory output
    output_dir.mkdir(exist_ok=True)
    pdf_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*80)
    print("📄 DIVISIONE FILE PER TIPO DOCUMENTO E CONVERSIONE PDF")
    print("="*80)
    
    if not input_file.exists():
        print(f"\n❌ File non trovato: {input_file}")
        return
    
    print(f"\n📖 Lettura file: {input_file}")
    print(f"   Dimensione: {os.path.getsize(input_file) / 1024 / 1024:.2f} MB")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern per trovare i tipi documento: ## 📂 Tipo Documento: XXXX
    tipo_pattern = re.compile(r'^## 📂 Tipo Documento: (.+)$', re.MULTILINE)
    
    # Trova tutti i tipi
    matches = list(tipo_pattern.finditer(content))
    
    print(f"\n✅ Trovati {len(matches)} tipi documento")
    
    files_created = []
    
    for i, match in enumerate(matches):
        tipo_code = match.group(1).strip()
        start_pos = match.start()
        
        # Fine sezione = inizio prossima sezione o fine file
        if i < len(matches) - 1:
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(content)
        
        # Estrai sezione
        section = content[start_pos:end_pos]
        
        # Nome file sicuro (rimuovi caratteri speciali)
        safe_name = re.sub(r'[^\w\-]', '_', tipo_code)
        md_file = output_dir / f"{safe_name}.md"
        
        # Aggiungi header con titolo e metadata
        header = f"# Testi Estratti - Tipo: {tipo_code}\n\n"
        header += f"**Generato**: 26 Febbraio 2026\n\n"
        header += "---\n\n"
        
        full_content = header + section
        
        # Salva Markdown
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        files_created.append((tipo_code, md_file, safe_name))
        
        print(f"   [{i+1}/{len(matches)}] Creato: {md_file.name} ({len(section):,} caratteri)")
    
    print(f"\n{'='*80}")
    print("🔄 CONVERSIONE IN PDF")
    print(f"{'='*80}")
    
    pdf_files = []
    
    for tipo_code, md_file, safe_name in files_created:
        print(f"\n   Conversione: {md_file.name} → PDF...")
        
        try:
            # Leggi Markdown
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Converti Markdown → HTML
            html_content = markdown(md_content, extras=['tables', 'fenced-code-blocks'])
            
            # Aggiungi CSS per styling migliore
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Testi Estratti - {tipo_code}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 2cm;
                        line-height: 1.6;
                    }}
                    h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                    h2 {{ color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 8px; margin-top: 30px; }}
                    h3 {{ color: #7f8c8d; margin-top: 25px; }}
                    h4 {{ color: #95a5a6; margin-top: 20px; }}
                    pre {{
                        background-color: #f4f4f4;
                        padding: 10px;
                        border-radius: 5px;
                        overflow-x: auto;
                        font-size: 10pt;
                    }}
                    code {{
                        background-color: #f4f4f4;
                        padding: 2px 5px;
                        border-radius: 3px;
                        font-family: 'Courier New', monospace;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 15px 0;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #3498db;
                        color: white;
                    }}
                    hr {{
                        border: none;
                        border-top: 1px solid #ddd;
                        margin: 20px 0;
                    }}
                    strong {{ color: #2c3e50; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            # Converti HTML → PDF
            pdf_file = pdf_dir / f"{safe_name}.pdf"
            HTML(string=styled_html).write_pdf(pdf_file)
            
            pdf_size = os.path.getsize(pdf_file) / 1024
            print(f"      ✅ PDF creato: {pdf_file.name} ({pdf_size:.1f} KB)")
            
            pdf_files.append(pdf_file)
            
        except Exception as e:
            print(f"      ❌ Errore conversione: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("📦 CREAZIONE ARCHIVIO ZIP")
    print(f"{'='*80}")
    
    # Crea ZIP con tutti i PDF
    zip_file = Path(__file__).parent / 'TESTI_ESTRATTI_PDF.zip'
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pdf_file in pdf_files:
            arcname = f"testi_pdf/{pdf_file.name}"
            zipf.write(pdf_file, arcname)
            print(f"   ✅ Aggiunto: {pdf_file.name}")
    
    zip_size = os.path.getsize(zip_file) / 1024 / 1024
    print(f"\n{'='*80}")
    print("✅ COMPLETATO!")
    print(f"{'='*80}")
    print(f"File Markdown creati: {len(files_created)}")
    print(f"File PDF creati: {len(pdf_files)}")
    print(f"Archivio ZIP: {zip_file}")
    print(f"Dimensione ZIP: {zip_size:.2f} MB")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    split_by_document_type()
