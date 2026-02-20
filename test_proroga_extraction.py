#!/usr/bin/env python
"""
Script di test per verificare l'estrazione della data_proroga dai PDF UNILAV.
Uso: python test_proroga_extraction.py <percorso_pdf>
"""

import sys
import pdfplumber
import re
from datetime import datetime

def test_extraction(pdf_path):
    """Testa l'estrazione della data proroga da un PDF"""
    
    print(f"📄 Analisi PDF: {pdf_path}")
    print("=" * 80)
    
    with pdfplumber.open(pdf_path) as pdf:
        # Estrae tutto il testo
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n\n"
        
        # Mostra righe con 'proroga'
        print("\n🔍 Righe contenenti 'proroga':")
        print("-" * 80)
        proroga_lines = [line for line in full_text.split('\n') if 'proroga' in line.lower()]
        for i, line in enumerate(proroga_lines, 1):
            print(f"{i}. {repr(line)}")
        
        # Test Pattern 1
        print("\n" + "=" * 80)
        print("🧪 Test Pattern 1: data fine proroga con/senza ':'")
        print("-" * 80)
        pattern1 = r'data\s+fine\s+proroga\s*:?\s*(\d{2}/\d{2}/\d{4})'
        match1 = re.search(pattern1, full_text, re.IGNORECASE | re.DOTALL)
        
        if match1:
            print(f"✅ MATCH TROVATO!")
            print(f"   Testo completo: {repr(match1.group(0))}")
            print(f"   Data estratta: {match1.group(1)}")
            
            try:
                dt = datetime.strptime(match1.group(1), "%d/%m/%Y")
                converted = dt.strftime("%Y-%m-%d")
                print(f"   Data convertita: {converted}")
            except ValueError as e:
                print(f"   ❌ Errore conversione: {e}")
        else:
            print("❌ Nessun match")
        
        # Test Pattern 2
        print("\n" + "=" * 80)
        print("🧪 Test Pattern 2: proroga + data entro 50 caratteri")
        print("-" * 80)
        pattern2 = r'(?:proroga|nuova\s+scadenza)[^\n]{0,50}?(\d{2}/\d{2}/\d{4})'
        match2 = re.search(pattern2, full_text, re.IGNORECASE | re.DOTALL)
        
        if match2:
            print(f"✅ MATCH TROVATO!")
            print(f"   Testo completo: {repr(match2.group(0))}")
            print(f"   Data estratta: {match2.group(1)}")
            
            try:
                dt = datetime.strptime(match2.group(1), "%d/%m/%Y")
                converted = dt.strftime("%Y-%m-%d")
                print(f"   Data convertita: {converted}")
            except ValueError as e:
                print(f"   ❌ Errore conversione: {e}")
        else:
            print("❌ Nessun match")
        
        # Test extraction come nel parser
        print("\n" + "=" * 80)
        print("🎯 Risultato finale (logica parser):")
        print("-" * 80)
        
        data_proroga = None
        data_proroga_match = re.search(pattern1, full_text, re.IGNORECASE | re.DOTALL)
        
        if not data_proroga_match:
            data_proroga_match = re.search(pattern2, full_text, re.IGNORECASE | re.DOTALL)
        
        if data_proroga_match:
            data_proroga_raw = data_proroga_match.group(1)
            try:
                dt = datetime.strptime(data_proroga_raw, "%d/%m/%Y")
                data_proroga = dt.strftime("%Y-%m-%d")
                print(f"✅ data_proroga estratta: {data_proroga}")
            except ValueError:
                print(f"❌ Errore conversione data: {data_proroga_raw}")
        else:
            print("❌ data_proroga: None")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_proroga_extraction.py <percorso_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    try:
        test_extraction(pdf_path)
    except FileNotFoundError:
        print(f"❌ File non trovato: {pdf_path}")
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
