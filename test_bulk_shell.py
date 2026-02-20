from titolario.models import TitolarioVoce
from anagrafiche.models import Anagrafica
from django.contrib.auth import get_user_model

User = get_user_model()

print("\n" + "="*70)
print("TEST BULK CREATION - Voci Titolario Intestate")
print("="*70)

# 1. Stato iniziale
print("\n📊 STATO INIZIALE")
print("-" * 70)

voce_hr_pers = TitolarioVoce.objects.filter(codice='HR-PERS').first()
if not voce_hr_pers:
    print("❌ Voce HR-PERS non trovata")
else:
    print(f"✓ Voce parent: {voce_hr_pers.codice} - {voce_hr_pers.titolo}")
    print(f"  Consente intestazione: {voce_hr_pers.consente_intestazione}")
    
    voci_esistenti = TitolarioVoce.objects.filter(parent=voce_hr_pers, anagrafica__isnull=False)
    print(f"  Voci intestate esistenti: {voci_esistenti.count()}")
    
    anagrafiche_disponibili = voce_hr_pers.get_anagrafiche_disponibili()
    if anagrafiche_disponibili:
        anagrafiche_con_codice = anagrafiche_disponibili.exclude(codice__isnull=True).exclude(codice='')
        print(f"  Anagrafiche disponibili: {anagrafiche_con_codice.count()}")
        
        # 2. Test API Endpoint
        print("\n🌐 TEST API ENDPOINT BULK")
        print("-" * 70)
        
        from rest_framework.test import APIClient
        
        client = APIClient()
        
        # Utente per test
        user, created = User.objects.get_or_create(
            username='test_bulk',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        client.force_authenticate(user=user)
        
        # Test 1: Dry-run con 5 anagrafiche
        print("\n1️⃣ DRY-RUN con 5 anagrafiche + sotto-voci")
        test_ids = list(anagrafiche_con_codice[:5].values_list('id', flat=True))
        
        response = client.post(
            f'/api/v1/fascicoli/titolario-voci/{voce_hr_pers.id}/crea_voci_bulk/',
            data={
                'anagrafica_ids': test_ids,
                'crea_sottovoci': True,
                'dry_run': True
            },
            format='json'
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✓ Voci da creare: {result['voci_create']}")
            print(f"   ✓ Sotto-voci da creare: {result['sottovoci_create']}")
            print(f"   ✓ Già esistenti: {result['gia_esistenti']}")
            print(f"   ✓ Errori: {len(result['errori'])}")
        
        # Test 2: Creazione reale di 1 voce con sotto-voci
        print("\n2️⃣ CREAZIONE REALE di 1 voce + sotto-voci")
        test_anagrafica = anagrafiche_con_codice.exclude(
            id__in=voci_esistenti.values_list('anagrafica_id', flat=True)
        ).first()
        
        if test_anagrafica:
            print(f"   Anagrafica test: {test_anagrafica.display_name()}")
            
            response = client.post(
                f'/api/v1/fascicoli/titolario-voci/{voce_hr_pers.id}/crea_voci_bulk/',
                data={
                    'anagrafica_ids': [test_anagrafica.id],
                    'crea_sottovoci': True,
                    'dry_run': False
                },
                format='json'
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"   ✓ Voci create: {result['voci_create']}")
                print(f"   ✓ Sotto-voci create: {result['sottovoci_create']}")
                
                if result['voci']:
                    voce_data = result['voci'][0]
                    print(f"\n   📄 Dettagli voce creata:")
                    print(f"      ID: {voce_data['id']}")
                    print(f"      Codice: {voce_data['codice']}")
                    print(f"      Titolo: {voce_data['titolo']}")
                    
                    # Verifica sotto-voci
                    voce_creata = TitolarioVoce.objects.get(id=voce_data['id'])
                    sottovoci = voce_creata.figli.all()
                    print(f"\n   📁 Sotto-voci ({sottovoci.count()}):")
                    for sv in sottovoci:
                        print(f"      - {sv.codice}: {sv.titolo} [{sv.pattern_codice}]")
        
        # Test 3: Bulk creation tutte disponibili (dry-run)
        print("\n3️⃣ BULK TUTTE LE DISPONIBILI (dry-run)")
        
        response = client.post(
            f'/api/v1/fascicoli/titolario-voci/{voce_hr_pers.id}/crea_voci_bulk/',
            data={
                'tutte_disponibili': True,
                'crea_sottovoci': False,
                'dry_run': True
            },
            format='json'
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✓ Voci da creare: {result['voci_create']}")
            print(f"   ✓ Già esistenti: {result['gia_esistenti']}")

# 3. Statistiche finali
print("\n📊 STATISTICHE FINALI")
print("-" * 70)

if voce_hr_pers:
    voci_finali = TitolarioVoce.objects.filter(parent=voce_hr_pers, anagrafica__isnull=False)
    print(f"✓ Totale voci intestate: {voci_finali.count()}")
    
    totale_sottovoci = sum(voce.figli.count() for voce in voci_finali)
    print(f"✓ Totale sotto-voci: {totale_sottovoci}")
    
    anagrafiche_disponibili_finali = voce_hr_pers.get_anagrafiche_disponibili()
    if anagrafiche_disponibili_finali:
        disponibili = anagrafiche_disponibili_finali.exclude(codice__isnull=True).exclude(codice='')
        print(f"✓ Anagrafiche ancora disponibili: {disponibili.count()}")

print("\n" + "="*70)
print("✅ TEST COMPLETATO")
print("="*70 + "\n")
