"""
Test per verificare la correzione del pattern template dei cedolini.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import DocumentiTipo
from documenti.utils import build_document_filename, _format_value
from anagrafiche.models import Anagrafica

print("=" * 80)
print("TEST 1: Verifica _format_value con formati Python")
print("=" * 80)

# Test formati Python
test_cases = [
    (2, '02d', '02'),
    (10, '02d', '10'),
    (2026, '04d', '2026'),
    (3.14, '.2f', '3.14'),
    (3.1, '.2f', '3.10'),
    ('test', 's', 'test'),
]

for value, fmt, expected in test_cases:
    result = _format_value(value, fmt)
    status = "✓" if result == expected else "✗"
    print(f"{status} _format_value({value!r}, {fmt!r}) = {result!r} (expected: {expected!r})")

print()
print("=" * 80)
print("TEST 2: Verifica build_document_filename con pattern BPAG")
print("=" * 80)

try:
    tipo_bpag = DocumentiTipo.objects.get(codice='BPAG')
    print(f"Pattern: {tipo_bpag.nome_file_pattern}")
    print()
    
    # Trova un'anagrafica di test
    anagrafica_test = Anagrafica.objects.filter(tipo='PF').first()
    
    if anagrafica_test:
        # Simula documento con attrs corretti (ID anagrafica)
        class FakeDoc:
            def __init__(self):
                self.pk = 9999
                self.codice = "TEST-BPAG-2026-999"
                self.tipo = tipo_bpag
        
        fake_doc = FakeDoc()
        
        # Simula attrs_map come dovrebbe essere DOPO la correzione
        attrs_map_corretto = {
            'anno_riferimento': 2026,
            'mese_riferimento': 2,
            'mensilita': '02',
            'dipendente': anagrafica_test.id,  # ✅ ID corretto
        }
        
        print("Test con attributi CORRETTI (ID anagrafica):")
        print(f"  attrs_map = {attrs_map_corretto}")
        print(f"  anagrafica dipendente: {anagrafica_test.denominazione} (ID: {anagrafica_test.id}, codice: {anagrafica_test.codice})")
        
        result = build_document_filename(fake_doc, 'cedolino.pdf', attrs=attrs_map_corretto)
        print(f"  Risultato: {result}")
        print()
        
        # Test con attrs sbagliati (nome invece di ID) per confronto
        attrs_map_sbagliato = {
            'anno_riferimento': 2026,
            'mese_riferimento': 2,
            'mensilita': '02',
            'dipendente': 'Rossi Mario',  # ❌ Nome invece di ID
        }
        
        print("Test con attributi SBAGLIATI (nome dipendente):")
        print(f"  attrs_map = {attrs_map_sbagliato}")
        
        result_sbagliato = build_document_filename(fake_doc, 'cedolino.pdf', attrs=attrs_map_sbagliato)
        print(f"  Risultato: {result_sbagliato}")
        print()
        
        # Confronto
        if 'anagrafica_test.codice' in result or anagrafica_test.codice in result:
            print("✓ La correzione funziona! Il codice dipendente è presente nel filename.")
        else:
            print("⚠ Il codice dipendente non appare nel filename.")
            
    else:
        print("⚠ Nessuna anagrafica di tipo PF trovata per il test")
        
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("TEST 3: Pattern template suggestions")
print("=" * 80)

suggestions = [
    # Pattern attuale (presunto)
    "{attr:tipo}_{attr:anno_riferimento}-{attr:mese_riferimento:02d}_{attr:dipendente.codice}",
    
    # Pattern alternativo con cliente
    "Cedolini_{attr:anno_riferimento}_{attr:mese_riferimento:02d}_{cliente.anagrafica.codice}",
    
    # Pattern semplice
    "LibroUnico_{attr:anno_riferimento}-{attr:mese_riferimento:02d}_{cliente.anagrafica.codice}",
]

print("Pattern consigliati:")
for i, pattern in enumerate(suggestions, 1):
    print(f"{i}. {pattern}")
