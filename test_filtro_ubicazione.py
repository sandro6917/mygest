#!/usr/bin/env python
"""
Test rapido per verificare il filtro ubicazione
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from archivio_fisico.models import UnitaFisica
from documenti.models import Documento
from fascicoli.models import Fascicolo

print("=" * 60)
print("TEST FILTRO UBICAZIONE")
print("=" * 60)

# Conta unità fisiche
unita_count = UnitaFisica.objects.count()
print(f"\n✓ Unità Fisiche totali: {unita_count}")

# Prendi prime 3 unità per il test
unita_sample = UnitaFisica.objects.all()[:3]

for unita in unita_sample:
    print(f"\n{'=' * 60}")
    print(f"Unità: {unita.codice} - {unita.nome} ({unita.tipo_display})")
    print(f"Path: {unita.full_path}")
    
    # Conta documenti
    doc_count = Documento.objects.filter(ubicazione=unita).count()
    print(f"  → Documenti: {doc_count}")
    
    if doc_count > 0:
        docs = Documento.objects.filter(ubicazione=unita)[:3]
        for doc in docs:
            print(f"    - {doc.codice}: {doc.descrizione[:50]}")
    
    # Conta fascicoli
    fasc_count = Fascicolo.objects.filter(ubicazione=unita).count()
    print(f"  → Fascicoli: {fasc_count}")
    
    if fasc_count > 0:
        fascs = Fascicolo.objects.filter(ubicazione=unita)[:3]
        for fasc in fascs:
            print(f"    - {fasc.codice}: {fasc.titolo[:50]}")

print(f"\n{'=' * 60}")
print("Test completato!")
print("=" * 60)
