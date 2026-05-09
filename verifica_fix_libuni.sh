#!/bin/bash
# Script per verificare il flusso completo di importazione LIBUNI

cd /home/sandro/mygest
source venv/bin/activate

python manage.py shell << 'PYTHON_SCRIPT'

import os
from documenti.models import DocumentiTipo, Documento, AttributoValore, AttributoDefinizione
from documenti.utils import build_document_filename

print("=" * 80)
print("VERIFICA 1: Configurazione tipo LIBUNI")
print("=" * 80)

try:
    tipo_libuni = DocumentiTipo.objects.get(codice='LIBUNI')
    print(f"✓ Tipo LIBUNI trovato")
    print(f"  Codice: {tipo_libuni.codice}")
    print(f"  Nome: {tipo_libuni.nome}")
    print(f"  Pattern codice: {tipo_libuni.pattern_codice}")
    print(f"  Pattern nome file: {tipo_libuni.nome_file_pattern}")
    print()
    
    # Verifica attributi
    attributi = AttributoDefinizione.objects.filter(tipo_documento=tipo_libuni).order_by('ordine')
    print(f"Attributi definiti ({attributi.count()}):")
    for attr in attributi:
        print(f"  - {attr.codice}: {attr.nome} (tipo: {attr.tipo_dato}, required: {attr.required})")
    print()
    
    # Analizza pattern template
    pattern = tipo_libuni.nome_file_pattern
    import re
    tokens = re.findall(r'\{([^}]+)\}', pattern)
    print(f"Token nel pattern:")
    for token in tokens:
        print(f"  {{{token}}}")
    print()
    
except DocumentiTipo.DoesNotExist:
    print("✗ Tipo LIBUNI non trovato!")
    exit(1)

print("=" * 80)
print("VERIFICA 2: Documenti LIBUNI esistenti")
print("=" * 80)

docs_libuni = Documento.objects.filter(tipo=tipo_libuni).order_by('-creato_il')[:3]

if docs_libuni.exists():
    print(f"Ultimi {docs_libuni.count()} documenti LIBUNI:")
    for doc in docs_libuni:
        print(f"\n  ID: {doc.id}")
        print(f"  Codice: {doc.codice}")
        print(f"  Descrizione: {doc.descrizione}")
        print(f"  File: {os.path.basename(doc.file.name) if doc.file else 'N/A'}")
        print(f"  Cliente: {doc.cliente.anagrafica.codice if doc.cliente and doc.cliente.anagrafica else 'N/A'}")
        
        # Mostra attributi
        print(f"  Attributi:")
        attrs = AttributoValore.objects.filter(documento=doc).select_related('definizione')
        if attrs.exists():
            for av in attrs:
                print(f"    - {av.definizione.codice}: {av.valore}")
        else:
            print("    (nessun attributo)")
else:
    print("Nessun documento LIBUNI trovato nel database")

print()
print("=" * 80)
print("VERIFICA 3: Test build_document_filename con attrs simulati")
print("=" * 80)

class FakeDoc:
    def __init__(self):
        self.pk = 9999
        self.codice = "TEST-LIBUNI-2026-001"
        self.tipo = tipo_libuni

fake_doc = FakeDoc()

# Simula attrs_map come dovrebbe essere dopo la correzione
attrs_map = {
    'anno': 2026,
    'mese': 2,
    'mensilita': 2,
    'periodo': 'Febbraio 2026',
    'num_cedolini': 15
}

# Test pattern template
from anagrafiche.models import Cliente
cliente_test = Cliente.objects.first()

if cliente_test:
    fake_doc.cliente = cliente_test
    print(f"Cliente test: {cliente_test.anagrafica.codice if cliente_test.anagrafica else 'N/A'}")
else:
    class FakeCliente:
        class anagrafica:
            codice = "TESTCLI01"
    fake_doc.cliente = FakeCliente()
    print(f"Cliente test: TESTCLI01 (fake)")

print(f"attrs_map = {attrs_map}")
print()

# Test con attrs passati
result = build_document_filename(fake_doc, 'test.zip', attrs=attrs_map)
print(f"Risultato con attrs: {result}")

# Verifica componenti
if '2026' in result:
    print("  ✓ Anno presente")
else:
    print("  ✗ Anno mancante")

if '2' in result or '02' in result:
    print("  ✓ Mese presente")
else:
    print("  ✗ Mese mancante")

if cliente_test and cliente_test.anagrafica:
    if cliente_test.anagrafica.codice in result:
        print(f"  ✓ Codice cliente presente ({cliente_test.anagrafica.codice})")
    else:
        print(f"  ✗ Codice cliente mancante")
elif 'TESTCLI01' in result:
    print(f"  ✓ Codice cliente presente (TESTCLI01)")

print()
print("=" * 80)
print("VERIFICA 4: Controllo funzione _salva_attributi_libro_unico")
print("=" * 80)

from api.v1.documenti.importa_libro_unico import _salva_attributi_libro_unico
import inspect

# Verifica la firma della funzione
sig = inspect.signature(_salva_attributi_libro_unico)
print(f"Firma: {sig}")

# Verifica che restituisca un valore
source = inspect.getsource(_salva_attributi_libro_unico)
if 'return attributi_map' in source:
    print("✓ La funzione restituisce attributi_map")
else:
    print("✗ La funzione NON restituisce attributi_map")

if "attributi_map = {" in source:
    print("✓ La funzione crea attributi_map")
    
    # Verifica attributi inclusi
    if "'mensilita':" in source:
        print("✓ Attributo 'mensilita' presente")
    else:
        print("✗ Attributo 'mensilita' mancante")
    
    if "anno,  # " in source or "'anno': anno" in source:
        print("✓ Attributo 'anno' è int (non convertito a str)")
    elif "str(anno)" in source and "anno': str(anno)" in source:
        print("✗ Attributo 'anno' convertito a str (ERRORE)")
        
    if "mese,  # " in source or "'mese': mese" in source:
        print("✓ Attributo 'mese' è int (non convertito a str)")
    elif "str(mese)" in source and "mese': str(mese)" in source:
        print("✗ Attributo 'mese' convertito a str (ERRORE)")

print()
print("=" * 80)
print("RIEPILOGO VERIFICA")
print("=" * 80)

print("""
La correzione è stata implementata correttamente se:

1. ✓ Tipo LIBUNI ha pattern template con token {attr:...}
2. ✓ AttributoDefinizione per anno, mese, mensilita esistono
3. ✓ _salva_attributi_libro_unico restituisce Dict[str, Any]
4. ✓ attributi_map contiene 'mensilita' 
5. ✓ attributi_map mantiene int per anno/mese (non str)
6. ✓ build_document_filename genera nome corretto

Per verificare il flusso completo:
- Importa un nuovo ZIP Libro Unico
- Controlla il nome file generato
- Verifica i log per "applica_rename_con_attributi"
""")

PYTHON_SCRIPT
