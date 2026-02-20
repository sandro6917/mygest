#!/usr/bin/env python
"""
Script per testare il rendering del form con attributi anagrafica
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/sandro/mygest')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import DocumentiTipo
from documenti.forms import DocumentoDinamicoForm

# Prendi un tipo con attributo anagrafica
tipo = DocumentiTipo.objects.filter(codice='CT_LAV').first()

if not tipo:
    print("Tipo documento CT_LAV non trovato")
    sys.exit(1)

print(f"Tipo: {tipo.codice} - {tipo.nome}")
print(f"\nCreazione form...\n")

# Crea il form
form = DocumentoDinamicoForm(tipo=tipo)

# Verifica attributi dinamici
for field_name, field in form.fields.items():
    if field_name.startswith('attr_'):
        print(f"\n{'='*60}")
        print(f"Campo: {field_name}")
        print(f"Tipo: {type(field).__name__}")
        print(f"Label: {field.label}")
        if hasattr(field, 'widget'):
            print(f"Widget: {type(field.widget).__name__}")
            if hasattr(field.widget, 'attrs'):
                print(f"Widget attrs: {field.widget.attrs}")
        
        # Rendering HTML
        print(f"\nHTML generato:")
        print("-" * 60)
        html = str(form[field_name])
        print(html[:500] if len(html) > 500 else html)
        print("-" * 60)
        
        # Verifica classe select2
        if 'select2' in html:
            print("✅ Classe 'select2' trovata nell'HTML")
        else:
            print("❌ Classe 'select2' NON trovata nell'HTML")
        
        if 'data-placeholder' in html:
            print("✅ Attributo 'data-placeholder' trovato")
        else:
            print("❌ Attributo 'data-placeholder' NON trovato")
