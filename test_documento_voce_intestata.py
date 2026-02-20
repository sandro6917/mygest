#!/usr/bin/env python
"""Test creazione documento con voce intestata ad anagrafica"""
from datetime import date
from django.contrib.auth import get_user_model
from anagrafiche.models import Cliente
from titolario.models import TitolarioVoce
from documenti.models import Documento, DocumentiTipo

User = get_user_model()
user = User.objects.first()

print('='*60)
print('TEST CREAZIONE DOCUMENTO CON VOCE INTESTATA')
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

# 2. Trova un cliente
cliente = Cliente.objects.first()
if not cliente:
    print('\n❌ Nessun cliente trovato nel database')
    exit(1)

print(f'\n✓ Cliente selezionato:')
print(f'  ID: {cliente.id}')
print(f'  Nome: {cliente.anagrafica.display_name()}')

# 3. Trova un tipo documento
tipo_doc = DocumentiTipo.objects.first()
if not tipo_doc:
    print('\n⚠️  Nessun tipo documento trovato, creo uno di test...')
    tipo_doc = DocumentiTipo.objects.create(
        codice='TEST',
        nome='Documento Test',
        attivo=True
    )

print(f'\n✓ Tipo documento selezionato:')
print(f'  Codice: {tipo_doc.codice}')
print(f'  Nome: {tipo_doc.nome}')

# 4. Crea un documento con la voce intestata
try:
    documento = Documento.objects.create(
        descrizione='Test Documento Voce Intestata',
        data_documento=date.today(),
        cliente=cliente,
        tipo=tipo_doc,
        titolario_voce=voce_sylla,
        digitale=True,
        tracciabile=True
    )
    
    print(f'\n✅ Documento creato con successo!')
    print(f'  ID: {documento.id}')
    print(f'  Codice: {documento.codice}')
    print(f'  Descrizione: {documento.descrizione}')
    print(f'  Voce titolario: {documento.titolario_voce.codice if documento.titolario_voce else "N/A"}')
    
    # Verifica che il codice contenga il codice anagrafica
    if voce_sylla.anagrafica:
        ana_code = voce_sylla.anagrafica.codice
        if ana_code in documento.codice:
            print(f'\n✅ Il codice contiene il codice anagrafica "{ana_code}"')
        else:
            print(f'\n⚠️  Il codice NON contiene il codice anagrafica "{ana_code}"')
            print(f'  Codice generato: {documento.codice}')
    
    # Pulizia: elimina il documento di test
    documento.delete()
    print(f'\n✓ Documento di test eliminato')
    
except Exception as e:
    print(f'\n❌ Errore durante la creazione del documento:')
    print(f'  {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    exit(1)

print(f'\n' + '='*60)
print('TEST COMPLETATO CON SUCCESSO! ✓')
print('='*60)
