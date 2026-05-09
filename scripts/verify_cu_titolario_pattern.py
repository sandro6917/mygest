#!/usr/bin/env python
"""
Script per verificare pattern titolario CU prima di deploy fix.

Uso:
    python manage.py shell < scripts/verify_cu_titolario_pattern.py
"""

from titolario.models import TitolarioVoce
from documenti.models import Documento, DocumentiTipo

print("\n" + "="*80)
print("VERIFICA PATTERN TITOLARIO CU")
print("="*80 + "\n")

voce_cu = TitolarioVoce.objects.filter(codice='CU').first()

if voce_cu:
    print(f"✅ Voce CU: {voce_cu.codice}")
    print(f"   Pattern: {voce_cu.pattern_codice}")
    
    if voce_cu.pattern_codice and '{ATTR:' in voce_cu.pattern_codice:
        print("\n✅ Pattern usa attributi dinamici")
    else:
        print("\n⚠️  Pattern NON usa attributi - rename userà timestamp")
else:
    print("❌ Voce CU non trovata!")

tipo_cu = DocumentiTipo.objects.filter(codice='CU').first()
if tipo_cu:
    orfani = Documento.objects.filter(tipo=tipo_cu, file__isnull=True).count()
    print(f"\n📊 Documenti CU orfani: {orfani}")

print("\n" + "="*80 + "\n")