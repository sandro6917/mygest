#!/usr/bin/env python
"""Test creazione fascicolo via API con voce intestata"""
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from anagrafiche.models import Cliente
from titolario.models import TitolarioVoce

User = get_user_model()
user = User.objects.first()

client = APIClient()
client.force_authenticate(user=user)

print('='*60)
print('TEST API: CREAZIONE FASCICOLO CON VOCE INTESTATA')
print('='*60)

# 1. Trova voce intestata
voce_sylla = TitolarioVoce.objects.filter(anagrafica__isnull=False).first()
if not voce_sylla:
    print('\n❌ Nessuna voce intestata trovata')
    exit(1)

print(f'\n✓ Voce intestata: {voce_sylla.codice} - {voce_sylla.titolo}')
print(f'  Anagrafica: {voce_sylla.anagrafica.nome if voce_sylla.anagrafica else "N/A"}')
print(f'  Pattern: {voce_sylla.pattern_codice}')

# 2. Trova cliente
cliente = Cliente.objects.first()
print(f'\n✓ Cliente: {cliente.anagrafica.display_name()}')

# 3. Crea fascicolo via API
data = {
    'titolo': 'Test API Fascicolo Voce Intestata',
    'anno': 2026,
    'stato': 'corrente',
    'cliente': cliente.id,
    'titolario_voce': voce_sylla.id,
    'retention_anni': 10
}

print(f'\n→ POST /api/v1/fascicoli/fascicoli/')
print(f'  Data: {data}')

response = client.post('/api/v1/fascicoli/fascicoli/', data, format='json')

if response.status_code == 201:
    print(f'\n✅ Fascicolo creato con successo!')
    print(f'  Status: {response.status_code}')
    print(f'  ID: {response.data["id"]}')
    print(f'  Codice: {response.data["codice"]}')
    print(f'  Titolo: {response.data["titolo"]}')
    
    # Verifica che il codice contenga l'anagrafica
    if voce_sylla.anagrafica:
        ana_code = voce_sylla.anagrafica.codice
        if ana_code in response.data['codice']:
            print(f'\n✅ Il codice contiene "{ana_code}"')
        else:
            print(f'\n⚠️  Il codice NON contiene "{ana_code}"')
    
    # Elimina il fascicolo di test
    fascicolo_id = response.data['id']
    delete_response = client.delete(f'/api/v1/fascicoli/fascicoli/{fascicolo_id}/')
    if delete_response.status_code == 204:
        print(f'\n✓ Fascicolo di test eliminato')
    
else:
    print(f'\n❌ Errore nella creazione del fascicolo')
    print(f'  Status: {response.status_code}')
    print(f'  Response: {response.data}')
    exit(1)

print(f'\n' + '='*60)
print('TEST API COMPLETATO CON SUCCESSO! ✓')
print('='*60)
