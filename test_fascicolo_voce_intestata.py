#!/usr/bin/env python
"""Test creazione fascicolo con voce intestata ad anagrafica"""
from django.contrib.auth import get_user_model
from anagrafiche.models import Cliente, Anagrafica
from titolario.models import TitolarioVoce
from fascicoli.models import Fascicolo

User = get_user_model()
user = User.objects.first()

print('='*60)
print('TEST CREAZIONE FASCICOLO CON VOCE INTESTATA')
print('='*60)

# 1. Verifica voce intestata esistente
voce_sylla = TitolarioVoce.objects.filter(anagrafica__isnull=False).first()
if not voce_sylla:
    print('\n❌ Nessuna voce intestata trovata nel database')
    exit(1)

print(f'\n✓ Voce intestata trovata:')
print(f'  Codice: {voce_sylla.codice}')
print(f'  Titolo: {voce_sylla.titolo}')
print(f'  Anagrafica: {voce_sylla.anagrafica.nome if voce_sylla.anagrafica else "N/A"}')
print(f'  Pattern: {voce_sylla.pattern_codice}')

# 2. Verifica che il pattern contenga {ANA}
if '{ANA}' not in voce_sylla.pattern_codice:
    print(f'\n⚠️  Il pattern non contiene {{ANA}}: {voce_sylla.pattern_codice}')
    print('  Aggiorno il pattern per il test...')
    voce_sylla.pattern_codice = '{CLI}-{TIT}-{ANA}-{ANNO}-{SEQ:03d}'
    voce_sylla.save()
    print(f'  Nuovo pattern: {voce_sylla.pattern_codice}')

# 3. Trova un cliente
cliente = Cliente.objects.first()
if not cliente:
    print('\n❌ Nessun cliente trovato nel database')
    exit(1)

print(f'\n✓ Cliente selezionato:')
print(f'  ID: {cliente.id}')
print(f'  Nome: {cliente.anagrafica.display_name()}')

# 4. Crea un fascicolo con la voce intestata
try:
    fascicolo = Fascicolo.objects.create(
        titolo='Test Fascicolo Voce Intestata',
        anno=2026,
        stato='corrente',
        cliente=cliente,
        titolario_voce=voce_sylla,
        retention_anni=10
    )
    
    print(f'\n✅ Fascicolo creato con successo!')
    print(f'  ID: {fascicolo.id}')
    print(f'  Codice: {fascicolo.codice}')
    print(f'  Titolo: {fascicolo.titolo}')
    print(f'  Voce titolario: {fascicolo.titolario_voce.codice}')
    print(f'  Progressivo: {fascicolo.progressivo}')
    
    # Verifica che il codice contenga il codice anagrafica
    if voce_sylla.anagrafica:
        ana_code = voce_sylla.anagrafica.codice
        if ana_code in fascicolo.codice:
            print(f'\n✅ Il codice contiene il codice anagrafica "{ana_code}"')
        else:
            print(f'\n⚠️  Il codice NON contiene il codice anagrafica "{ana_code}"')
            print(f'  Codice generato: {fascicolo.codice}')
    
    # Pulizia: elimina il fascicolo di test
    fascicolo.delete()
    print(f'\n✓ Fascicolo di test eliminato')
    
except Exception as e:
    print(f'\n❌ Errore durante la creazione del fascicolo:')
    print(f'  {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

print(f'\n' + '='*60)
print('TEST COMPLETATO CON SUCCESSO! ✓')
print('='*60)
