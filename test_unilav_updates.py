#!/usr/bin/env python
"""
Test delle modifiche UNILAV:
1. Ubicazione = None
2. Voce titolario intestata al dipendente
3. Attributo tipo con scelte
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from documenti.models import DocumentiTipo, AttributoDefinizione
from titolario.models import TitolarioVoce
from anagrafiche.models import Anagrafica

print("=" * 80)
print("🧪 TEST CONFIGURAZIONE UNILAV")
print("=" * 80)

# Test 1: Verifica tipo documento UNILAV
print("\n1️⃣ TIPO DOCUMENTO UNILAV")
print("-" * 80)
try:
    tipo_unilav = DocumentiTipo.objects.get(codice='UNILAV')
    print(f"✅ Tipo UNILAV trovato: {tipo_unilav.nome} (ID: {tipo_unilav.id})")
except DocumentiTipo.DoesNotExist:
    print("❌ Tipo UNILAV non trovato!")

# Test 2: Verifica attributi dinamici
print("\n2️⃣ ATTRIBUTI DINAMICI")
print("-" * 80)
attrs = AttributoDefinizione.objects.filter(tipo_documento=tipo_unilav).order_by('ordine')
print(f"Totale attributi: {attrs.count()}")
for attr in attrs:
    print(f"  - {attr.codice}: {attr.nome}")
    print(f"    Tipo dato: {attr.tipo_dato}")
    if attr.choices:
        print(f"    Scelte: {attr.choices}")
    print()

# Test 3: Verifica attributo 'tipo' con scelte
print("\n3️⃣ ATTRIBUTO 'tipo' (SELECT)")
print("-" * 80)
try:
    attr_tipo = AttributoDefinizione.objects.get(tipo_documento=tipo_unilav, codice='tipo')
    print(f"✅ Attributo 'tipo' trovato")
    print(f"   Tipo dato: {attr_tipo.tipo_dato}")
    print(f"   Scelte configurate: {attr_tipo.choices}")
    
    if attr_tipo.tipo_dato == 'choice':
        print(f"   ✅ Configurato come SELECT (tipo_dato='choice')")
    else:
        print(f"   ⚠️  ATTENZIONE: tipo_dato è '{attr_tipo.tipo_dato}' invece di 'choice'")
    
    # Parse scelte
    scelte = attr_tipo.scelte()
    print(f"\n   Scelte disponibili ({len(scelte)}):")
    for valore, etichetta in scelte:
        print(f"     - {valore} = {etichetta}")
        
except AttributoDefinizione.DoesNotExist:
    print("❌ Attributo 'tipo' non trovato!")

# Test 4: Verifica voce titolario HR-PERS
print("\n4️⃣ VOCE TITOLARIO HR-PERS")
print("-" * 80)
try:
    voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
    print(f"✅ Voce HR-PERS trovata: {voce_hr_pers.titolo} (ID: {voce_hr_pers.id})")
    print(f"   Consente intestazione: {voce_hr_pers.consente_intestazione}")
    print(f"   Pattern codice: {voce_hr_pers.pattern_codice}")
    
    # Conta voci intestate
    voci_intestate = TitolarioVoce.objects.filter(parent=voce_hr_pers, anagrafica__isnull=False)
    print(f"\n   Voci intestate a dipendenti: {voci_intestate.count()}")
    
    if voci_intestate.exists():
        print(f"   Esempi (prime 5):")
        for voce in voci_intestate[:5]:
            print(f"     - {voce.codice}: {voce.titolo} (Anagrafica: {voce.anagrafica.codice if voce.anagrafica else 'N/A'})")
    
except TitolarioVoce.DoesNotExist:
    print("❌ Voce HR-PERS non trovata!")

# Test 5: Simula creazione voce per un dipendente di test
print("\n5️⃣ SIMULAZIONE CREAZIONE VOCE INTESTATA")
print("-" * 80)

# Trova un'anagrafica di esempio (o crea una fittizia)
anagrafica_test = Anagrafica.objects.filter(tipo='PF', codice__isnull=False).first()

if anagrafica_test:
    print(f"📌 Anagrafica test: {anagrafica_test.display_name()} (Codice: {anagrafica_test.codice})")
    
    # Verifica se esiste già voce intestata
    voce_esistente = TitolarioVoce.objects.filter(
        parent=voce_hr_pers,
        anagrafica=anagrafica_test
    ).first()
    
    if voce_esistente:
        print(f"   ✅ Voce già esistente:")
        print(f"      Codice: {voce_esistente.codice}")
        print(f"      Titolo: {voce_esistente.titolo}")
        print(f"      Pattern: {voce_esistente.pattern_codice}")
    else:
        print(f"   ℹ️  Nessuna voce esistente per questo dipendente")
        print(f"   Durante l'import UNILAV verrebbe creata:")
        print(f"      Codice: {anagrafica_test.codice}")
        print(f"      Titolo: Dossier {anagrafica_test.display_name()}")
        print(f"      Pattern: {{CLI}}-{{ANA}}-UNILAV-{{ANNO}}-{{SEQ:03d}}")
        print(f"      Esempio codice doc: CLI001-{anagrafica_test.codice}-UNILAV-2026-001")
else:
    print("⚠️  Nessuna anagrafica disponibile per test")

print("\n" + "=" * 80)
print("✅ TEST COMPLETATO")
print("=" * 80)
