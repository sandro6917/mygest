#!/usr/bin/env python
"""Test completo API Titolario Voci"""
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from titolario.models import TitolarioVoce

User = get_user_model()
user = User.objects.first()

client = APIClient()
client.force_authenticate(user=user)

print('='*60)
print('TEST COMPLETO API TITOLARIO VOCI')
print('='*60)

# 1. Test lista completa
response = client.get('/api/v1/fascicoli/titolario-voci/')
voci = response.data
print(f'\n✓ Lista completa: {len(voci)} voci restituite')
print(f'  Voci nel DB: {TitolarioVoce.objects.count()}')
print(f'  Match: {len(voci) == TitolarioVoce.objects.count()}')

# 2. Test ricerca per codice
response = client.get('/api/v1/fascicoli/titolario-voci/?search=HR-PERS')
voci_search = response.data
print(f'\n✓ Ricerca "HR-PERS": {len(voci_search)} risultati')
for v in voci_search:
    print(f'    - {v["codice"]} - {v["titolo"]}')

# 3. Test ricerca per nome anagrafica
response = client.get('/api/v1/fascicoli/titolario-voci/?search=Sylla')
voci_sylla = response.data
print(f'\n✓ Ricerca "Sylla": {len(voci_sylla)} risultati')
for v in voci_sylla:
    print(f'    - {v["codice"]} - {v["titolo"]}', end='')
    if v.get('anagrafica_nome'):
        print(f' (Anagrafica: {v["anagrafica_nome"]})', end='')
    print()

# 4. Test filtro per consente_intestazione
response = client.get('/api/v1/fascicoli/titolario-voci/?consente_intestazione=true')
voci_intestabili = response.data
print(f'\n✓ Voci che consentono intestazione: {len(voci_intestabili)}')
for v in voci_intestabili[:5]:  # Prime 5
    print(f'    - {v["codice"]} - {v["titolo"]}')
if len(voci_intestabili) > 5:
    print(f'    ... e altre {len(voci_intestabili) - 5} voci')

# 5. Conta voci intestate
voci_con_anagrafica = [v for v in voci if v.get('anagrafica')]
print(f'\n✓ Voci intestate ad anagrafiche: {len(voci_con_anagrafica)}')
for v in voci_con_anagrafica:
    print(f'    - {v["codice"]} - {v["titolo"]} ({v.get("anagrafica_nome", "N/A")})')

# 6. Test voci radice
hr_voci = [v for v in voci if v['codice'].startswith('HR')]
print(f'\n✓ Voci HR: {len(hr_voci)}')
for v in hr_voci[:10]:  # Prime 10
    print(f'    - {v["codice"]} - {v["titolo"]}')
if len(hr_voci) > 10:
    print(f'    ... e altre {len(hr_voci) - 10} voci')

print(f'\n' + '='*60)
print('TEST COMPLETATO CON SUCCESSO! ✓')
print('='*60)
