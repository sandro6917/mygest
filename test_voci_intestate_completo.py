"""
Script per testare l'implementazione completa delle voci intestate ad anagrafiche
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from titolario.models import TitolarioVoce
from anagrafiche.models import Anagrafica

print("="*70)
print("TEST IMPLEMENTAZIONE VOCI TITOLARIO INTESTATE")
print("="*70)

# 1. Verifica voci con consente_intestazione
print("\n1️⃣  VOCI CHE CONSENTONO INTESTAZIONE")
print("-" * 70)
voci_parent = TitolarioVoce.objects.filter(consente_intestazione=True)
print(f"Trovate {voci_parent.count()} voci:")
for v in voci_parent:
    print(f"  ✓ {v.codice}: {v.titolo}")
    
    # Conta voci intestate sotto questa
    voci_intestate = v.figli.filter(anagrafica__isnull=False)
    if voci_intestate.exists():
        print(f"    └─ {voci_intestate.count()} voci intestate:")
        for vi in voci_intestate[:5]:  # Max 5
            print(f"       • {vi.codice}: {vi.titolo} ({vi.anagrafica.display_name()})")

# 2. Verifica anagrafiche disponibili
print("\n2️⃣  ANAGRAFICHE DISPONIBILI PER INTESTAZIONE")
print("-" * 70)
hr_pers = TitolarioVoce.objects.filter(codice='HR-PERS').first()
if hr_pers:
    anagrafiche_disp = hr_pers.get_anagrafiche_disponibili()
    if anagrafiche_disp:
        count = anagrafiche_disp.count()
        print(f"Sotto '{hr_pers.codice}' ci sono {count} anagrafiche disponibili")
        if count > 0:
            print(f"Prime 5:")
            for ana in anagrafiche_disp[:5]:
                print(f"  • {ana.codice or '(no code)'}: {ana.display_name()}")
    else:
        print("Nessuna anagrafica disponibile (get_anagrafiche_disponibili() = None)")
else:
    print("✗ Voce HR-PERS non trovata")

# 3. Test creazione voce intestata (se ci sono anagrafiche disponibili)
print("\n3️⃣  TEST CREAZIONE VOCE INTESTATA")
print("-" * 70)
if hr_pers and anagrafiche_disp and anagrafiche_disp.exists():
    # Prendi prima anagrafica con codice
    ana_test = anagrafiche_disp.filter(codice__isnull=False).exclude(codice='').first()
    
    if ana_test:
        print(f"Anagrafica selezionata: {ana_test.display_name()} ({ana_test.codice})")
        
        # Verifica se esiste già
        existing = TitolarioVoce.objects.filter(
            parent=hr_pers,
            anagrafica=ana_test
        ).first()
        
        if existing:
            print(f"✓ Voce già esistente:")
            print(f"  - ID: {existing.id}")
            print(f"  - Codice: {existing.codice}")
            print(f"  - Titolo: {existing.titolo}")
            print(f"  - Pattern: {existing.pattern_codice}")
            print(f"  - Codice gerarchico: {existing.codice_gerarchico()}")
            
            # Mostra figli
            figli = existing.figli.all()
            if figli:
                print(f"  - Sotto-voci ({figli.count()}):")
                for figlio in figli:
                    print(f"     • {figlio.codice}: {figlio.titolo}")
        else:
            print(f"→ Creo nuova voce intestata...")
            try:
                nuova_voce = TitolarioVoce(
                    codice=ana_test.codice,
                    titolo=f"Dossier {ana_test.display_name()}",
                    parent=hr_pers,
                    anagrafica=ana_test,
                    pattern_codice='{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}'
                )
                nuova_voce.full_clean()
                nuova_voce.save()
                
                print(f"✓ Voce creata con successo!")
                print(f"  - ID: {nuova_voce.id}")
                print(f"  - Codice: {nuova_voce.codice}")
                print(f"  - Titolo: {nuova_voce.titolo}")
                print(f"  - Pattern: {nuova_voce.pattern_codice}")
                print(f"  - Is intestata: {nuova_voce.is_voce_intestata()}")
                
            except Exception as e:
                print(f"✗ Errore: {e}")
    else:
        print("✗ Nessuna anagrafica disponibile con codice valido")
else:
    print("Skipped (nessuna anagrafica disponibile o HR-PERS non trovata)")

# 4. Riepilogo finale
print("\n4️⃣  RIEPILOGO VOCI INTESTATE")
print("-" * 70)
voci_intestate_totali = TitolarioVoce.objects.filter(anagrafica__isnull=False).select_related('anagrafica', 'parent')
print(f"Totale voci intestate nel sistema: {voci_intestate_totali.count()}")

if voci_intestate_totali.exists():
    print("\nLista completa:")
    for voce in voci_intestate_totali:
        print(f"\n  📁 {voce.codice_gerarchico()}")
        print(f"     Titolo: {voce.titolo}")
        print(f"     Anagrafica: {voce.anagrafica.display_name()} (ID: {voce.anagrafica.id})")
        print(f"     Pattern: {voce.pattern_codice}")
        
        # Figli
        figli = voce.figli.all()
        if figli:
            print(f"     Sotto-voci ({figli.count()}):")
            for figlio in figli:
                print(f"       - {figlio.codice}: {figlio.titolo}")

print("\n" + "="*70)
print("✓ Test completato!")
print("="*70)
