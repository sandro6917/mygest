#!/usr/bin/env python
"""
Script di test per verificare i filtri API delle scadenze.
"""
import os
import sys

# Assicurati di usare il settings corretto (non quello di test)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")

import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from api.v1.scadenze.views import ScadenzaOccorrenzaViewSet
from api.v1.scadenze.filters import ScadenzaOccorrenzaFilter
from scadenze.models import ScadenzaOccorrenza

User = get_user_model()

print(f"\n{'='*100}")
print("TEST FILTRI API SCADENZE OCCORRENZE")
print(f"{'='*100}\n")

# Test 1: Filtro stato__in
print("1. TEST filtro stato__in=pending,scheduled")
print("-" * 80)
filter_params = {'stato__in': 'pending,scheduled'}
filterset = ScadenzaOccorrenzaFilter(filter_params, queryset=ScadenzaOccorrenza.objects.all())
qs = filterset.qs
print(f"Query params: {filter_params}")
print(f"Risultati: {qs.count()} occorrenze")
print(f"Stati trovati: {set(qs.values_list('stato', flat=True))}")
print()

# Test 2: Filtro per data (range come dalla richiesta API)
print("2. TEST filtro inizio__gte=2026-01-23 & inizio__lt=2026-01-30")
print("-" * 80)
filter_params = {
    'inizio__gte': '2026-01-23',
    'inizio__lt': '2026-01-30'
}
filterset = ScadenzaOccorrenzaFilter(filter_params, queryset=ScadenzaOccorrenza.objects.all())
qs = filterset.qs
print(f"Query params: {filter_params}")
print(f"Risultati: {qs.count()} occorrenze")
if qs.exists():
    print("\nPrime 5 occorrenze trovate:")
    for occ in qs.order_by('inizio')[:5]:
        print(f"  - ID {occ.id}: {occ.scadenza.titolo} - {occ.inizio.strftime('%d/%m/%Y %H:%M')} - {occ.stato}")
print()

# Test 3: Combinazione filtri (come dalla richiesta originale)
print("3. TEST combinazione: inizio__gte + inizio__lt + stato__in")
print("-" * 80)
filter_params = {
    'inizio__gte': '2026-01-23',
    'inizio__lt': '2026-01-30',
    'stato__in': 'pending,scheduled'
}
filterset = ScadenzaOccorrenzaFilter(filter_params, queryset=ScadenzaOccorrenza.objects.all())
qs = filterset.qs
print(f"Query params: {filter_params}")
print(f"Risultati: {qs.count()} occorrenze")
if qs.exists():
    print("\nTutte le occorrenze trovate:")
    for occ in qs.order_by('inizio'):
        print(f"  - ID {occ.id}: {occ.scadenza.titolo} - {occ.inizio.strftime('%d/%m/%Y %H:%M')} - {occ.stato}")
else:
    print("\n⚠️  Nessuna occorrenza trovata nel range specificato con stato pending/scheduled")
    
    # Verifica se esistono occorrenze nel range senza filtro stato
    filterset_no_stato = ScadenzaOccorrenzaFilter(
        {'inizio__gte': '2026-01-23', 'inizio__lt': '2026-01-30'}, 
        queryset=ScadenzaOccorrenza.objects.all()
    )
    count_no_stato = filterset_no_stato.qs.count()
    print(f"   Occorrenze nel range (senza filtro stato): {count_no_stato}")
    
    # Verifica occorrenze pending in generale
    filterset_only_pending = ScadenzaOccorrenzaFilter(
        {'stato__in': 'pending'}, 
        queryset=ScadenzaOccorrenza.objects.all()
    )
    count_pending = filterset_only_pending.qs.count()
    print(f"   Occorrenze pending (senza filtro data): {count_pending}")
    
    if count_pending > 0:
        print("\n   Prime 5 scadenze pending (indipendentemente dalla data):")
        for occ in filterset_only_pending.qs.order_by('inizio')[:5]:
            print(f"     - ID {occ.id}: {occ.inizio.strftime('%d/%m/%Y %H:%M')} - {occ.scadenza.titolo}")

print()

# Test 4: Verifica SQL generato
print("4. SQL QUERY GENERATA")
print("-" * 80)
filter_params = {
    'inizio__gte': '2026-01-23',
    'inizio__lt': '2026-01-30',
    'stato__in': 'pending,scheduled'
}
filterset = ScadenzaOccorrenzaFilter(filter_params, queryset=ScadenzaOccorrenza.objects.all())
sql_query = str(filterset.qs.query)
print(f"{sql_query[:500]}...")
print()

print(f"{'='*100}")
print("✅ TEST COMPLETATO")
print(f"{'='*100}\n")
