#!/usr/bin/env python
"""
Test rendering template con widget anagrafica
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from comunicazioni.models import Comunicazione
from comunicazioni.models_template import TemplateComunicazione

# Trova una comunicazione con template e dati_template contenente 'cliente'
comunicazioni = Comunicazione.objects.filter(
    template__isnull=False,
    dati_template__has_key='cliente'
).select_related('template')

if not comunicazioni.exists():
    print("❌ Nessuna comunicazione trovata con template e campo 'cliente'")
    print("\nCrea prima una comunicazione usando il template 'Invio presenze edac'")
    print("e compila il campo 'cliente'")
    exit(1)

comunicazione = comunicazioni.first()
print(f"📄 Comunicazione ID: {comunicazione.id}")
print(f"📋 Template: {comunicazione.template.nome}")
print(f"📦 dati_template: {comunicazione.dati_template}")

# Ottieni il context
context = comunicazione.get_template_context()

print("\n📚 Context generato:")
for key, value in context.items():
    value_str = str(value)[:100]
    print(f"  {key}: {type(value).__name__} = {value_str}")

# Verifica campo cliente
if 'cliente' in context:
    cliente = context['cliente']
    print(f"\n✅ Campo 'cliente' trovato nel context:")
    print(f"   Tipo: {type(cliente).__name__}")
    print(f"   Valore: {cliente}")
    
    if hasattr(cliente, 'denominazione_anagrafica'):
        print(f"   denominazione_anagrafica: {cliente.denominazione_anagrafica}")
    else:
        print("   ⚠️  L'oggetto non ha l'attributo 'denominazione_anagrafica'")
        if hasattr(cliente, 'nominativo'):
            print(f"   nominativo: {cliente.nominativo}")
else:
    print("\n❌ Campo 'cliente' NON trovato nel context!")

# Test rendering del template
print("\n🎨 Test rendering oggetto:")
print(f"   oggetto template: {comunicazione.template.oggetto}")

try:
    from comunicazioni.utils_template import render_template_comunicazione
    rendered = render_template_comunicazione(comunicazione.template, context, comunicazione)
    print(f"\n✅ Oggetto renderizzato: {rendered.oggetto}")
    print(f"   Corpo (primi 200 caratteri): {rendered.corpo_testo[:200]}")
except Exception as e:
    print(f"\n❌ Errore rendering: {e}")
    import traceback
    traceback.print_exc()
