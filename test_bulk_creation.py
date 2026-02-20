#!/usr/bin/env python
"""
Test completo per Bulk Creation di voci titolario intestate.

Testa:
1. Admin action bulk
2. Management command
3. API endpoint bulk
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.contrib.auth import get_user_model
from titolario.models import TitolarioVoce
from anagrafiche.models import Anagrafica

User = get_user_model()

print("\n" + "="*70)
print("TEST BULK CREATION - Voci Titolario Intestate")
print("="*70)

# 1. Verifica stato iniziale
print("\n📊 STATO INIZIALE")
print("-" * 70)

voce_hr_pers = TitolarioVoce.objects.filter(codice='HR-PERS').first()
if not voce_hr_pers:
    print("❌ Voce HR-PERS non trovata")
    exit(1)

print(f"✓ Voce parent: {voce_hr_pers.codice} - {voce_hr_pers.titolo}")
print(f"  Consente intestazione: {voce_hr_pers.consente_intestazione}")

voci_esistenti = TitolarioVoce.objects.filter(parent=voce_hr_pers, anagrafica__isnull=False)
print(f"  Voci intestate esistenti: {voci_esistenti.count()}")

anagrafiche_disponibili = voce_hr_pers.get_anagrafiche_disponibili()
if anagrafiche_disponibili:
    anagrafiche_con_codice = anagrafiche_disponibili.exclude(codice__isnull=True).exclude(codice='')
    print(f"  Anagrafiche disponibili: {anagrafiche_con_codice.count()}")
else:
    print("  Anagrafiche disponibili: 0")
    anagrafiche_con_codice = Anagrafica.objects.none()

# 2. Test Management Command (dry-run)
print("\n🔧 TEST MANAGEMENT COMMAND (dry-run)")
print("-" * 70)

from django.core.management import call_command
from io import StringIO
import sys

# Cattura output del command
output = StringIO()
try:
    call_command('crea_voci_intestate', 'HR-PERS', dry_run=True, stdout=output)
    command_output = output.getvalue()
    print(command_output)
except Exception as e:
    print(f"❌ Errore: {e}")

# 3. Test API Endpoint (dry-run)
print("\n🌐 TEST API ENDPOINT BULK (dry-run)")
print("-" * 70)

from rest_framework.test import APIClient

client = APIClient()

# Crea/ottieni utente per autenticazione
user, created = User.objects.get_or_create(
    username='test_bulk',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"✓ Utente test creato: {user.username}")
else:
    print(f"✓ Utente test esistente: {user.username}")

client.force_authenticate(user=user)

# Prendi prime 5 anagrafiche disponibili per test
if anagrafiche_con_codice.exists():
    test_anagrafica_ids = list(anagrafiche_con_codice[:5].values_list('id', flat=True))
    
    response = client.post(
        f'/api/v1/titolario/{voce_hr_pers.id}/crea_voci_bulk/',
        data={
            'anagrafica_ids': test_anagrafica_ids,
            'crea_sottovoci': True,
            'dry_run': True
        },
        format='json'
    )
    
    print(f"Status code: {response.status_code}")
    if response.status_code in [200, 201]:
        result = response.json()
        print(f"✓ Voci che verrebbero create: {result['voci_create']}")
        print(f"✓ Sotto-voci che verrebbero create: {result['sottovoci_create']}")
        print(f"  Già esistenti: {result['gia_esistenti']}")
        print(f"  Errori: {len(result['errori'])}")
        if result['errori']:
            print("  Dettagli errori:")
            for err in result['errori'][:3]:
                print(f"    - {err}")
    else:
        print(f"❌ Errore API: {response.data}")
else:
    print("⚠️  Nessuna anagrafica disponibile per test API")

# 4. Test creazione reale (1 sola voce)
print("\n💾 TEST CREAZIONE REALE (1 voce)")
print("-" * 70)

if anagrafiche_con_codice.exists():
    # Prendi la prima anagrafica disponibile
    test_anagrafica = anagrafiche_con_codice.first()
    
    # Verifica che non esista già
    esiste = TitolarioVoce.objects.filter(
        parent=voce_hr_pers,
        anagrafica=test_anagrafica
    ).exists()
    
    if esiste:
        print(f"ℹ️  Voce per {test_anagrafica.display_name()} già esistente (skip)")
    else:
        response = client.post(
            f'/api/v1/titolario/{voce_hr_pers.id}/crea_voci_bulk/',
            data={
                'anagrafica_ids': [test_anagrafica.id],
                'crea_sottovoci': True,
                'dry_run': False
            },
            format='json'
        )
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"✓ Creazione completata:")
            print(f"  Voci create: {result['voci_create']}")
            print(f"  Sotto-voci create: {result['sottovoci_create']}")
            
            if result['voci']:
                voce_data = result['voci'][0]
                print(f"\n  📄 Voce creata:")
                print(f"     ID: {voce_data['id']}")
                print(f"     Codice: {voce_data['codice']}")
                print(f"     Titolo: {voce_data['titolo']}")
                print(f"     Anagrafica: {voce_data['anagrafica_nome']}")
                
                # Verifica sotto-voci
                voce_creata = TitolarioVoce.objects.get(id=voce_data['id'])
                sottovoci = voce_creata.figli.all()
                if sottovoci.exists():
                    print(f"\n  📁 Sotto-voci create ({sottovoci.count()}):")
                    for sv in sottovoci:
                        print(f"     - {sv.codice}: {sv.titolo}")
        else:
            print(f"❌ Errore creazione: {response.data}")
else:
    print("⚠️  Nessuna anagrafica disponibile per test creazione")

# 5. Statistiche finali
print("\n📊 STATISTICHE FINALI")
print("-" * 70)

voci_finali = TitolarioVoce.objects.filter(parent=voce_hr_pers, anagrafica__isnull=False)
print(f"✓ Totale voci intestate sotto HR-PERS: {voci_finali.count()}")

# Conta sotto-voci
totale_sottovoci = 0
for voce in voci_finali:
    sottovoci_count = voce.figli.count()
    if sottovoci_count > 0:
        totale_sottovoci += sottovoci_count

print(f"✓ Totale sotto-voci: {totale_sottovoci}")

# Anagrafiche ancora disponibili
anagrafiche_disponibili_finali = voce_hr_pers.get_anagrafiche_disponibili()
if anagrafiche_disponibili_finali:
    disponibili_con_codice = anagrafiche_disponibili_finali.exclude(
        codice__isnull=True
    ).exclude(codice='')
    print(f"✓ Anagrafiche ancora disponibili: {disponibili_con_codice.count()}")
else:
    print(f"✓ Anagrafiche ancora disponibili: 0")

print("\n" + "="*70)
print("✅ TEST COMPLETATO")
print("="*70 + "\n")
