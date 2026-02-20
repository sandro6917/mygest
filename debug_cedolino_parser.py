#!/usr/bin/env python3
"""
Script di debug per analizzare l'estrazione dati dal PDF cedolino.
Mostra esattamente cosa viene estratto dal parser riga per riga.
"""

import sys
import os
import django

# Setup Django
sys.path.insert(0, '/home/sandro/mygest')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

import re
import pdfplumber
from documenti.parsers.cedolino_parser import MESI_ITALIANI

def debug_pdf(pdf_path):
    print("="*100)
    print(f"DEBUG PARSER CEDOLINO: {pdf_path}")
    print("="*100)
    
    if not os.path.exists(pdf_path):
        print(f"❌ File non trovato: {pdf_path}")
        return
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"\n📄 Numero pagine: {len(pdf.pages)}")
        
        # Estrai testo da tutte le pagine
        all_text = ""
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()
            if page_text:
                all_text += page_text + "\n"
        
        # Usa solo prima pagina per l'analisi riga per riga
        text = pdf.pages[0].extract_text()
        lines = text.split('\n')
        
        print(f"\n{'='*100}")
        print("CONTENUTO PDF - TUTTE LE RIGHE")
        print('='*100)
        
        for idx, line in enumerate(lines):
            print(f"{idx:3d}: |{line}|")
        
        print(f"\n{'='*100}")
        print("ANALISI ESTRAZIONE PERIODO")
        print('='*100)
        
        periodo = None
        anno = None
        mese = None
        
        # Test tutti i pattern per il periodo
        for idx, line in enumerate(lines):
            # Pattern 1: SPECIAL./PERIODO sulla stessa riga
            periodo_match = re.search(r'(?:SPECIAL\.|PERIODO).*?([A-Z][a-z]+\s+\d{4})', line, re.IGNORECASE)
            if periodo_match:
                print(f"\n✅ Pattern 1 (stessa riga) - Riga {idx}:")
                print(f"   |{line}|")
                print(f"   Periodo estratto: {periodo_match.group(1)}")
            
            # Pattern 3: "PERIODO RETRIBUZIONE"
            if re.search(r'PERIODO.*RETRIBUZIONE', line, re.IGNORECASE):
                print(f"\n✅ Pattern 3 (PERIODO RETRIBUZIONE) - Riga {idx}:")
                print(f"   |{line}|")
                
                for offset in range(1, 6):
                    if idx + offset < len(lines):
                        next_line = lines[idx + offset].strip()
                        mese_anno_match = re.search(r'\b([A-Z][a-z]+)\s+(\d{4})\b', next_line, re.IGNORECASE)
                        if mese_anno_match:
                            mese_nome = mese_anno_match.group(1).lower()
                            if mese_nome in MESI_ITALIANI:
                                periodo = f"{mese_anno_match.group(1).capitalize()} {mese_anno_match.group(2)}"
                                anno = int(mese_anno_match.group(2))
                                mese = MESI_ITALIANI[mese_nome]
                                
                                print(f"   Riga successiva {idx + offset}: |{next_line}|")
                                print(f"   ✅ PERIODO: {periodo}, Anno: {anno}, Mese: {mese}")
                                break
        
        if periodo:
            print(f"\n🎯 PERIODO FINALE: {periodo} (Mese: {mese}, Anno: {anno})")
        else:
            print(f"\n❌ PERIODO NON TROVATO")
        
        print(f"\n{'='*100}")
        print("ANALISI ESTRAZIONE NETTO")
        print('='*100)
        
        # IMPORTANTE: Il netto è sempre nell'ULTIMA pagina
        print(f"\n📄 Cerco il netto nell'ULTIMA pagina (pagina {len(pdf.pages)})")
        ultima_pagina_text = pdf.pages[-1].extract_text()
        ultima_pagina_lines = ultima_pagina_text.split('\n') if ultima_pagina_text else []
        
        netto = None
        
        # Cerca "NETTO DEL MESE" riga per riga nell'ultima pagina
        for idx, line in enumerate(ultima_pagina_lines):
            if re.search(r'NETTO.*DEL.*MESE', line, re.IGNORECASE):
                print(f"\n✅ Trovato 'NETTO DEL MESE' alla riga {idx} dell'ultima pagina:")
                print(f"   |{line}|")
                
                # Cerca nelle successive 5 righe
                for offset in range(1, 6):
                    if idx + offset < len(ultima_pagina_lines):
                        next_line = ultima_pagina_lines[idx + offset].strip()
                        print(f"\n   Riga {idx + offset}: |{next_line}|")
                        
                        # ESCLUDI righe che contengono parole chiave non desiderate
                        if any(keyword in next_line.upper() for keyword in ['R.O.L', 'ROL', 'FERIE', 'EX-FEST']):
                            print(f"   ⏭️  IGNORATA (contiene keyword R.O.L/FERIE/EX-FEST)")
                            continue
                        
                        # Cerca solo righe con € o solo numeri
                        if '€' in next_line or re.match(r'^\s*\d+[.,]\d+\s*$', next_line):
                            # Cerca tutti gli importi con 2 decimali
                            importi_in_riga = re.findall(
                                r'(\d{1,7}(?:[.,]\d{3})*[.,]\d{2})\s*€?',
                                next_line
                            )
                            
                            if importi_in_riga:
                                print(f"   Importi trovati nella riga: {importi_in_riga}")
                                
                                # Prendi l'ULTIMO importo
                                netto_raw = importi_in_riga[-1]
                                print(f"   ✅ ULTIMO importo selezionato: {netto_raw}")
                                
                                # Normalizza
                                if ',' in netto_raw and '.' in netto_raw:
                                    netto = netto_raw.replace('.', '').replace(',', '.')
                                elif ',' in netto_raw:
                                    netto = netto_raw.replace(',', '.')
                                else:
                                    netto = netto_raw
                                
                                print(f"   ✅ Normalizzato: {netto}")
                                print(f"   ✅ Valore: {float(netto):.2f} EUR")
                                break
                        else:
                            print(f"   ⏭️  IGNORATA (non contiene € né è solo numero)")
                
                if netto:
                    break
        
        if netto:
            print(f"\n🎯 NETTO FINALE: {netto} EUR")
        else:
            print(f"\n❌ NETTO NON TROVATO")
        
        print(f"\n{'='*100}")
        print("RICERCA ALTERNATIVA - CERCA TUTTI I NUMERI CON 2 DECIMALI")
        print('='*100)
        
        # Mostra tutti i numeri trovati in tutto il testo
        all_importi = re.findall(r'(\d{1,7}(?:[.,]\d{3})*[.,]\d{2})', all_text)
        print(f"\nTutti gli importi con 2 decimali trovati nel PDF ({len(all_importi)}):")
        for imp in all_importi:
            # Normalizza
            if ',' in imp and '.' in imp:
                imp_norm = imp.replace('.', '').replace(',', '.')
            elif ',' in imp:
                imp_norm = imp.replace(',', '.')
            else:
                imp_norm = imp
            
            try:
                valore = float(imp_norm)
                print(f"   {imp:>15s} → {valore:>10.2f} EUR")
            except:
                print(f"   {imp:>15s} → ERRORE")
        
        print(f"\n{'='*100}")
        print("RIEPILOGO FINALE")
        print('='*100)
        print(f"Periodo: {periodo if periodo else '❌ NON TROVATO'}")
        print(f"Anno: {anno if anno else '❌ NON TROVATO'}")
        print(f"Mese: {mese if mese else '❌ NON TROVATO'}")
        print(f"Netto: {netto if netto else '❌ NON TROVATO'} EUR")
        print('='*100)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python debug_cedolino_parser.py <percorso_pdf>")
        print("\nCerca file PDF recenti...")
        
        import glob
        possible_paths = [
            "/tmp/*.pdf",
            "/home/sandro/Downloads/*.pdf",
            "/home/sandro/mygest/media/uploads/*.pdf",
        ]
        
        pdf_files = []
        for pattern in possible_paths:
            pdf_files.extend(glob.glob(pattern))
        
        if pdf_files:
            # Ordina per data modifica (più recente prima)
            pdf_files.sort(key=os.path.getmtime, reverse=True)
            print(f"\nTrovati {len(pdf_files)} file PDF. Più recente:")
            print(f"  {pdf_files[0]}")
            
            risposta = input("\nAnalizzare questo file? [S/n]: ")
            if risposta.lower() != 'n':
                debug_pdf(pdf_files[0])
        else:
            print("Nessun PDF trovato.")
    else:
        debug_pdf(sys.argv[1])
