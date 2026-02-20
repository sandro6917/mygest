#!/usr/bin/env python
"""
Script per debuggare la creazione di un documento e vedere i log.
"""

import os
import sys
import django
import logging

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

# Configura logging per vedere tutti i messaggi
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(name)s] %(message)s'
)

from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date
from documenti.models import DocumentiTipo
from documenti.forms import DocumentoDinamicoForm
from anagrafiche.models import Cliente

print("=" * 80)
print("DEBUG CREAZIONE DOCUMENTO")
print("=" * 80)

# Trova tipo documento e cliente esistenti
tipo = DocumentiTipo.objects.filter(nome_file_pattern__icontains="attr:").first()
if not tipo:
    print("✗ Nessun tipo documento con pattern contenente 'attr:' trovato")
    print("  Creane uno dall'interfaccia admin con pattern tipo:")
    print("  Presenze_{attr:anno_riferimento}{attr:mese_riferimento}_{cliente.anagrafica.codice}")
    sys.exit(1)

print(f"✓ Trovato tipo documento: {tipo.nome} (ID: {tipo.pk})")
print(f"  Pattern: {tipo.nome_file_pattern}")

cliente = Cliente.objects.select_related('anagrafica').first()
if not cliente:
    print("✗ Nessun cliente trovato nel database")
    sys.exit(1)

print(f"✓ Trovato cliente: {cliente.anagrafica.display_name()} (ID: {cliente.pk})")

# Trova attributi del tipo
from documenti.models import AttributoDefinizione
attrs_defs = AttributoDefinizione.objects.filter(tipo_documento=tipo).order_by('ordine')
print(f"✓ Attributi del tipo documento: {list(attrs_defs.values_list('codice', flat=True))}")

# Prepara dati form
file_content = b"Test content debug"
uploaded_file = SimpleUploadedFile("debug_test.pdf", file_content, content_type="application/pdf")

form_data = {
    "tipo": tipo.pk,
    "cliente": cliente.pk,
    "descrizione": "DEBUG - Test creazione documento",
    "data_documento": date.today(),
    "stato": "bozza",
    "digitale": True,
}

# Aggiungi attributi dinamici
for attr_def in attrs_defs:
    if attr_def.required:
        # Valori di test
        if 'anno' in attr_def.codice.lower():
            form_data[f"attr_{attr_def.codice}"] = "2024"
        elif 'mese' in attr_def.codice.lower():
            form_data[f"attr_{attr_def.codice}"] = "12"
        else:
            form_data[f"attr_{attr_def.codice}"] = "TEST"
        print(f"  - {attr_def.codice}: {form_data[f'attr_{attr_def.codice}']}")

print("\n" + "-" * 80)
print("CREAZIONE FORM E VALIDAZIONE")
print("-" * 80)

form = DocumentoDinamicoForm(
    data=form_data,
    files={"file": uploaded_file},
    tipo=tipo
)

if not form.is_valid():
    print(f"✗ Form non valido: {form.errors}")
    sys.exit(1)

print("✓ Form valido")

print("\n" + "-" * 80)
print("SALVATAGGIO DOCUMENTO (osserva i log sotto)")
print("-" * 80)

try:
    doc = form.save()
    print(f"\n✓ Documento salvato con ID: {doc.pk}")
except Exception as e:
    print(f"\n✗ Errore durante il salvataggio: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "-" * 80)
print("RISULTATO")
print("-" * 80)

if doc.file:
    filename = os.path.basename(doc.file.name)
    print(f"Nome file: {filename}")
    print(f"Path completo: {doc.file.name}")
    
    # Verifica presenza attributi
    for attr_def in attrs_defs:
        valore = form_data.get(f"attr_{attr_def.codice}", "")
        presente = str(valore) in filename
        status = "✓" if presente else "✗"
        print(f"{status} Attributo '{attr_def.codice}' = '{valore}': {'presente' if presente else 'MANCANTE'}")
    
    print(f"\nVuoi eliminare il documento di test? (s/n)")
    risposta = input().strip().lower()
    if risposta == 's':
        doc.delete()
        print("✓ Documento eliminato")
else:
    print("✗ Nessun file associato al documento")
