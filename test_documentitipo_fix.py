#!/usr/bin/env python
"""
Script di test per verificare la fix del bug di creazione DocumentiTipo.
Testa che sia possibile creare un nuovo DocumentiTipo senza errori.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.contrib.auth import get_user_model
from documenti.models import DocumentiTipo
from documenti.help_forms import HelpDataAdminForm

User = get_user_model()

def test_create_documentitipo():
    """Test creazione nuovo DocumentiTipo con help_data."""
    
    print("🧪 Test: Creazione DocumentiTipo con help_data...")
    
    # Dati di test
    form_data = {
        'codice': 'TEST_FIX',
        'nome': 'Test Fix DocumentiTipo',
        'attivo': True,
        'pattern_codice': '{CLI}_{TIPO}_{DATA}_{SEQ:03d}',
        'nome_file_pattern': '',
        'estensioni_permesse': 'pdf,docx',
        'help_descrizione_breve': 'Tipo documento di test per verificare la fix del bug.',
        'help_quando_usare_casi': 'Test caso 1\nTest caso 2',
        'help_ordine': 0,
        'duplicate_detection_config': {},
    }
    
    try:
        # Crea form
        form = HelpDataAdminForm(data=form_data)
        
        if not form.is_valid():
            print(f"❌ Form non valido: {form.errors}")
            return False
        
        # Salva (qui dovrebbe verificarsi il problema PRIMA della fix)
        print("   Saving form...")
        instance = form.save(commit=True)
        
        print(f"✅ DocumentiTipo creato con successo!")
        print(f"   ID: {instance.pk}")
        print(f"   Codice: {instance.codice}")
        print(f"   Nome: {instance.nome}")
        print(f"   help_data keys: {list(instance.help_data.keys())}")
        
        # Verifica che help_data sia popolato
        assert instance.help_data, "help_data non dovrebbe essere vuoto"
        assert 'descrizione_breve' in instance.help_data, "Manca descrizione_breve"
        
        # Verifica sezioni tecniche generate
        technical_sections = ['attributi_dinamici', 'pattern_codice', 'archiviazione', 'campi_obbligatori']
        for section in technical_sections:
            if section in instance.help_data:
                print(f"   ✓ Sezione tecnica '{section}' generata")
            else:
                print(f"   ⚠️  Sezione tecnica '{section}' mancante (OK se non ci sono attributi)")
        
        # Cleanup
        print(f"   Cleanup: eliminando tipo di test...")
        instance.delete()
        print(f"   ✓ Tipo di test eliminato")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_update_existing():
    """Test aggiornamento DocumentiTipo esistente."""
    
    print("\n🧪 Test: Aggiornamento DocumentiTipo esistente...")
    
    # Crea tipo di test
    tipo_test = DocumentiTipo.objects.create(
        codice='TEST_UPDATE',
        nome='Test Update',
        attivo=True,
    )
    
    try:
        # Aggiorna con form
        form_data = {
            'codice': 'TEST_UPDATE',
            'nome': 'Test Update - Modificato',
            'attivo': True,
            'pattern_codice': '{CLI}_{TIPO}_{DATA}_{SEQ:03d}',
            'nome_file_pattern': '',
            'estensioni_permesse': 'pdf',
            'help_descrizione_breve': 'Descrizione aggiornata.',
            'help_ordine': 0,
            'duplicate_detection_config': {},
        }
        
        form = HelpDataAdminForm(data=form_data, instance=tipo_test)
        
        if not form.is_valid():
            print(f"❌ Form non valido: {form.errors}")
            return False
        
        print("   Updating form...")
        instance = form.save(commit=True)
        
        print(f"✅ DocumentiTipo aggiornato con successo!")
        print(f"   Nome aggiornato: {instance.nome}")
        print(f"   help_data aggiornato: {'descrizione_breve' in instance.help_data}")
        
        # Cleanup
        print(f"   Cleanup: eliminando tipo di test...")
        instance.delete()
        
        return True
        
    except Exception as e:
        print(f"❌ Errore durante il test: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup anche in caso di errore
        tipo_test.delete()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("TEST FIX: DocumentiTipo Admin Add Bug")
    print("=" * 60)
    
    # Test 1: Creazione
    test1_ok = test_create_documentitipo()
    
    # Test 2: Update
    test2_ok = test_update_existing()
    
    print("\n" + "=" * 60)
    print("RISULTATI:")
    print(f"  Test Creazione: {'✅ PASS' if test1_ok else '❌ FAIL'}")
    print(f"  Test Update:    {'✅ PASS' if test2_ok else '❌ FAIL'}")
    print("=" * 60)
    
    sys.exit(0 if (test1_ok and test2_ok) else 1)
