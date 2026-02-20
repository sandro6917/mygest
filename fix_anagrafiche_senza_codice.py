#!/usr/bin/env python3
"""
Script per generare codici CLI per tutte le anagrafiche che ne sono sprovviste.
Da eseguire una tantum per sistemare anagrafiche create senza codice.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from anagrafiche.models import Anagrafica
from anagrafiche.utils import get_or_generate_cli

print("🔧 Fix anagrafiche senza codice CLI")
print("="*80)

# Trova tutte le anagrafiche senza codice
anagrafiche_senza_codice = Anagrafica.objects.filter(codice__isnull=True) | Anagrafica.objects.filter(codice='')
count = anagrafiche_senza_codice.count()

print(f"📊 Trovate {count} anagrafiche senza codice\n")

if count == 0:
    print("✅ Tutte le anagrafiche hanno già un codice!")
else:
    print("Generazione codici in corso...\n")
    
    success = 0
    errors = 0
    
    for ana in anagrafiche_senza_codice:
        try:
            codice = get_or_generate_cli(ana)
            ana.refresh_from_db()
            
            if ana.tipo == 'PF':
                nome_completo = f"{ana.cognome} {ana.nome}"
            else:
                nome_completo = ana.ragione_sociale or "N/A"
            
            print(f"✅ {nome_completo[:40]:40s} → {codice}")
            success += 1
            
        except Exception as e:
            if ana.tipo == 'PF':
                nome_completo = f"{ana.cognome} {ana.nome}"
            else:
                nome_completo = ana.ragione_sociale or "N/A"
            
            print(f"❌ {nome_completo[:40]:40s} → ERRORE: {e}")
            errors += 1
    
    print("\n" + "="*80)
    print(f"📊 Risultati:")
    print(f"   ✅ Successi: {success}")
    print(f"   ❌ Errori: {errors}")
    print(f"   📈 Totale: {success + errors}")
