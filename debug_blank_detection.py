#!/usr/bin/env python3
"""
Debug script per testare is_blank_page() su immagini reali dalle scansioni
"""

import sys
from pathlib import Path

# Aggiungi path per importare da scanner_service
sys.path.insert(0, str(Path(__file__).parent))

from scripts.scanner_service import is_blank_page

def analyze_scan_directory(scan_dir: str):
    """Analizza tutte le immagini in una directory di scansione"""
    
    scan_path = Path(scan_dir)
    
    if not scan_path.exists():
        print(f"❌ Directory non trovata: {scan_dir}")
        return
    
    # Trova tutte le immagini PNG
    images = sorted(scan_path.glob('*.png'))
    
    if not images:
        print(f"❌ Nessuna immagine trovata in: {scan_dir}")
        return
    
    print(f"🔍 Analisi di {len(images)} immagini in: {scan_dir}\n")
    print("=" * 80)
    
    blank_count = 0
    
    for img_path in images:
        result = is_blank_page(img_path)
        status = "🗑️  BLANK" if result else "✅ KEEP "
        
        if result:
            blank_count += 1
        
        print(f"{status} | {img_path.name}")
    
    print("=" * 80)
    print(f"\n📊 Risultato: {blank_count} pagine bianche, {len(images) - blank_count} pagine con contenuto")
    print(f"   Rimosse: {blank_count}/{len(images)} ({blank_count/len(images)*100:.1f}%)")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Analizza immagini scansionate per pagine bianche')
    parser.add_argument('scan_dir', help='Directory contenente le immagini scansionate')
    
    args = parser.parse_args()
    
    analyze_scan_directory(args.scan_dir)
