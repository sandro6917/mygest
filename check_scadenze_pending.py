#!/usr/bin/env python
"""Script per verificare le scadenze in pending."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from scadenze.models import ScadenzaOccorrenza
from django.utils import timezone
from datetime import datetime

# Range come dalla richiesta API
inizio = datetime(2026, 1, 23).replace(tzinfo=timezone.get_current_timezone())
fine = datetime(2026, 1, 30).replace(tzinfo=timezone.get_current_timezone())

print(f"\n{'='*80}")
print(f"SCADENZE IN PENDING/SCHEDULED dal {inizio.date()} al {fine.date()}")
print(f"{'='*80}\n")

occorrenze = ScadenzaOccorrenza.objects.filter(
    inizio__gte=inizio,
    inizio__lt=fine,
    stato__in=['pending', 'scheduled']
).select_related('scadenza').order_by('inizio')

count = occorrenze.count()
print(f"Totale occorrenze trovate: {count}\n")

if count > 0:
    for i, occ in enumerate(occorrenze[:10], 1):
        print(f"{i}. ID Occorrenza: {occ.id}")
        print(f"   Scadenza: {occ.scadenza.titolo}")
        print(f"   Data/Ora: {occ.inizio.strftime('%d/%m/%Y %H:%M')}")
        print(f"   Stato: {occ.stato}")
        print(f"   Priorità: {occ.scadenza.get_priorita_display()}")
        print(f"   Categoria: {occ.scadenza.categoria or 'N/A'}")
        if occ.scadenza.descrizione:
            desc = occ.scadenza.descrizione[:200]
            print(f"   Descrizione: {desc}...")
        print()
    
    if count > 10:
        print(f"... e altre {count - 10} occorrenze\n")
else:
    print("Nessuna scadenza in pending trovata nel range specificato.\n")
    
    # Verifica se ci sono scadenze in generale
    tutte = ScadenzaOccorrenza.objects.filter(
        inizio__gte=inizio,
        inizio__lt=fine
    ).count()
    print(f"Scadenze totali nel range (tutti gli stati): {tutte}")
    
    # Verifica stati presenti
    from django.db.models import Count
    stati = ScadenzaOccorrenza.objects.filter(
        inizio__gte=inizio,
        inizio__lt=fine
    ).values('stato').annotate(count=Count('id')).order_by('-count')
    
    if stati:
        print("\nDistribuzione per stato:")
        for s in stati:
            print(f"  - {s['stato']}: {s['count']}")

print(f"\n{'='*80}\n")
