"""
Script di debug per verificare il problema con il pattern template dei cedolini.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import DocumentiTipo, AttributoDefinizione, AttributoValore
from documenti.utils import build_document_filename

# Verifica configurazione tipo BPAG
try:
    tipo_bpag = DocumentiTipo.objects.get(codice='BPAG')
    print(f"✓ Tipo documento BPAG trovato")
    print(f"  - Nome: {tipo_bpag.nome}")
    print(f"  - Pattern codice: {tipo_bpag.pattern_codice}")
    print(f"  - Pattern nome file: {tipo_bpag.nome_file_pattern}")
    print()
    
    # Verifica attributi definiti
    print("Attributi definiti per BPAG:")
    attributi = AttributoDefinizione.objects.filter(tipo_documento=tipo_bpag).order_by('ordine')
    for attr in attributi:
        print(f"  - {attr.codice}: {attr.nome} (tipo: {attr.tipo_dato}, widget: {attr.widget}, required: {attr.required})")
    print()
    
    # Test build_document_filename con attributi simulati
    print("Test build_document_filename:")
    print("=" * 80)
    
    # Simula un documento con attributi
    class FakeDoc:
        def __init__(self):
            self.pk = 999
            self.codice = "TEST-BPAG-2026-001"
            self.tipo = tipo_bpag
            
    fake_doc = FakeDoc()
    
    # Test 1: attrs come dict con valori nativi (come passato da _create_attributi)
    attrs_nativi = {
        'tipo': 'Libro Unico',
        'anno_riferimento': 2026,
        'mese_riferimento': 2,
        'mensilita': 1,
        'dipendente': 'Rossi Mario',  # ❌ Dovrebbe essere un ID!
    }
    
    print(f"Test 1: attrs con valori nativi")
    print(f"  attrs_nativi = {attrs_nativi}")
    result1 = build_document_filename(fake_doc, 'cedolino.pdf', attrs=attrs_nativi)
    print(f"  Risultato: {result1}")
    print()
    
    # Test 2: attrs come dict con valori stringhe (come salvato nel DB)
    attrs_stringhe = {
        'tipo': 'Libro Unico',
        'anno_riferimento': '2026',
        'mese_riferimento': '2',
        'mensilita': '1',
        'dipendente': 'Rossi Mario',
    }
    
    print(f"Test 2: attrs con valori stringhe")
    print(f"  attrs_stringhe = {attrs_stringhe}")
    result2 = build_document_filename(fake_doc, 'cedolino.pdf', attrs=attrs_stringhe)
    print(f"  Risultato: {result2}")
    print()
    
    # Test 3: attrs=None (legge dal DB, ma non ci sono attributi salvati per fake_doc)
    print(f"Test 3: attrs=None (legge dal DB)")
    result3 = build_document_filename(fake_doc, 'cedolino.pdf', attrs=None)
    print(f"  Risultato: {result3}")
    print()
    
    # Test 4: attrs con dipendente come ID (corretto)
    # Prima trova o crea un'anagrafica di test
    from anagrafiche.models import Anagrafica
    try:
        anagrafica_test = Anagrafica.objects.filter(tipo='PF').first()
        if anagrafica_test:
            attrs_correct = {
                'tipo': 'Libro Unico',
                'anno_riferimento': 2026,
                'mese_riferimento': 2,
                'mensilita': 1,
                'dipendente': anagrafica_test.id,  # ✅ ID corretto
            }
            
            print(f"Test 4: attrs con dipendente come ID")
            print(f"  dipendente_id = {anagrafica_test.id} ({anagrafica_test.denominazione})")
            print(f"  codice anagrafica = {anagrafica_test.codice}")
            print(f"  attrs_correct = {attrs_correct}")
            result4 = build_document_filename(fake_doc, 'cedolino.pdf', attrs=attrs_correct)
            print(f"  Risultato: {result4}")
        else:
            print(f"Test 4: Nessuna anagrafica disponibile per il test")
    except Exception as e:
        print(f"Test 4: Errore - {e}")
    
    print()
    print("=" * 80)
    
    # Analizza il pattern template
    print("\nAnalisi pattern template:")
    pattern = tipo_bpag.nome_file_pattern
    print(f"Pattern: {pattern}")
    
    import re
    tokens = re.findall(r'\{([^}]+)\}', pattern)
    print(f"\nToken trovati:")
    for token in tokens:
        print(f"  - {{{token}}}")
    
except DocumentiTipo.DoesNotExist:
    print("❌ Tipo documento BPAG non trovato!")
    print("   Eseguire: python manage.py setup_cedolini")
