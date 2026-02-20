#!/usr/bin/env python
"""Test autoescape off per evitare HTML escaping"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from django.template import Context, Template
from anagrafiche.models import Anagrafica

# Prendi un'anagrafica con apostrofi nel nome (usa ragione_sociale)
anagrafica = Anagrafica.objects.filter(
    ragione_sociale__icontains="'"
).first()

if not anagrafica:
    # Usa la prima disponibile
    anagrafica = Anagrafica.objects.first()

print(f'🏢 Anagrafica: {anagrafica.denominazione_anagrafica}')
print(f'   Ragione sociale: {anagrafica.ragione_sociale or "N/A"}')
apostrofi_count = (anagrafica.denominazione_anagrafica or '').count("'")
print(f'   Apostrofi nel nome: {apostrofi_count}')

# Test 1: Con autoescape (default)
context = Context({'cliente': anagrafica})
template_text = 'Presenze {{cliente.denominazione_anagrafica}} mese/anno'
template_with_escape = Template(template_text)
result_with_escape = template_with_escape.render(context)

print(f'\n🔒 Con autoescape (default):')
print(f'   Risultato: {result_with_escape}')
if '&#x27;' in result_with_escape or '&#39;' in result_with_escape:
    print(f'   ❌ HTML escaping presente')
    escaped_count = result_with_escape.count('&#x27;') + result_with_escape.count('&#39;')
    print(f'   Escape trovati: {escaped_count}')
else:
    print(f'   ✅ Nessun escaping')

# Test 2: Con autoescape off
template_text_no_escape = '{% autoescape off %}Presenze {{cliente.denominazione_anagrafica}} mese/anno{% endautoescape %}'
template_no_escape = Template(template_text_no_escape)
result_no_escape = template_no_escape.render(context)

print(f'\n🔓 Con autoescape off:')
print(f'   Risultato: {result_no_escape}')
if '&#x27;' in result_no_escape or '&#39;' in result_no_escape:
    print(f'   ❌ HTML escaping ancora presente')
else:
    print(f'   ✅ Nessun escaping - Perfetto!')
    apostrofi_result = result_no_escape.count("'")
    print(f'   Apostrofi nel risultato: {apostrofi_result}')
