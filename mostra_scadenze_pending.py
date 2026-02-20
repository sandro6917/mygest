#!/usr/bin/env python
"""Script per mostrare le scadenze in pending."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from scadenze.models import ScadenzaOccorrenza
from django.utils import timezone

print(f"\n{'='*100}")
print(f"TUTTE LE SCADENZE IN PENDING (70 occorrenze)")
print(f"{'='*100}\n")

occorrenze = ScadenzaOccorrenza.objects.filter(
    stato='pending'
).select_related('scadenza').order_by('inizio')

# Mostra prime 20
for i, occ in enumerate(occorrenze[:20], 1):
    print(f"{i}. ID: {occ.id} | Scadenza ID: {occ.scadenza.id}")
    print(f"   Titolo: {occ.scadenza.titolo}")
    print(f"   Data/Ora: {occ.inizio.strftime('%d/%m/%Y %H:%M')}")
    print(f"   Stato: {occ.stato}")
    print(f"   Priorità: {occ.scadenza.get_priorita_display()}")
    print(f"   Categoria: {occ.scadenza.categoria or 'N/A'}")
    if occ.scadenza.descrizione:
        desc = occ.scadenza.descrizione[:150]
        print(f"   Descrizione: {desc}{'...' if len(occ.scadenza.descrizione) > 150 else ''}")
    print()

if occorrenze.count() > 20:
    print(f"\n... e altre {occorrenze.count() - 20} occorrenze in pending\n")

print(f"{'='*100}\n")

# Statistiche per categoria
from django.db.models import Count
categorie = ScadenzaOccorrenza.objects.filter(stato='pending').values(
    'scadenza__categoria'
).annotate(
    count=Count('id')
).order_by('-count')

print("Distribuzione per categoria:")
for c in categorie:
    cat = c['scadenza__categoria'] or '(Nessuna categoria)'
    print(f"  - {cat}: {c['count']}")

print(f"\n{'='*100}\n")
