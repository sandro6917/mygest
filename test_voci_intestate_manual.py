"""
Script di test per verificare la creazione di voci titolario intestate ad anagrafiche
"""
from django.core.exceptions import ValidationError
from titolario.models import TitolarioVoce
from anagrafiche.models import Anagrafica

# Trova voce HR-PERS
hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
print(f"✓ Voce parent trovata: {hr_pers}")
print(f"  - Consente intestazione: {hr_pers.consente_intestazione}")

# Trova un'anagrafica di test (o creane una)
try:
    anagrafica = Anagrafica.objects.filter(tipo='PF', codice__isnull=False).exclude(codice='').first()
    if not anagrafica:
        print("✗ Nessuna anagrafica PF con codice trovata, creane una manualmente")
        print("\nPer creare una voce intestata serve un'anagrafica con:")
        print("  - Tipo: PF (Persona Fisica)")
        print("  - Codice: valorizzato (es. ROSMAR01)")
        print("  - Nome/Cognome: valorizzati")
    else:
        print(f"\n✓ Anagrafica trovata: {anagrafica.nome} ({anagrafica.codice})")
        
        # Verifica se esiste già voce intestata
        existing = TitolarioVoce.objects.filter(
            parent=hr_pers,
            anagrafica=anagrafica
        ).first()
        
        if existing:
            print(f"\n✓ Voce intestata già esistente:")
            print(f"  - ID: {existing.id}")
            print(f"  - Codice: {existing.codice}")
            print(f"  - Titolo: {existing.titolo}")
            print(f"  - Intestata a: {existing.anagrafica.nome}")
            print(f"  - Codice gerarchico: {existing.codice_gerarchico()}")
        else:
            # Crea voce intestata
            print(f"\n→ Creazione voce intestata...")
            voce_intestata = TitolarioVoce(
                codice=anagrafica.codice,
                titolo=f"Dossier {anagrafica.nome}",
                parent=hr_pers,
                anagrafica=anagrafica,
                pattern_codice='{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}'
            )
            
            # Valida
            try:
                voce_intestata.full_clean()
                voce_intestata.save()
                
                print(f"✓ Voce intestata creata con successo!")
                print(f"  - ID: {voce_intestata.id}")
                print(f"  - Codice: {voce_intestata.codice}")
                print(f"  - Titolo: {voce_intestata.titolo}")
                print(f"  - Intestata a: {voce_intestata.anagrafica.nome}")
                print(f"  - Is voce intestata: {voce_intestata.is_voce_intestata()}")
                print(f"  - Codice gerarchico: {voce_intestata.codice_gerarchico()}")
                
                # Testa creazione sotto-voce
                print(f"\n→ Creazione sotto-voce (Buste Paga)...")
                sottovoce = TitolarioVoce.objects.create(
                    codice='BUSTE-PAGA',
                    titolo='Buste Paga',
                    parent=voce_intestata,
                    pattern_codice='{CLI}-{ANA}-BUSTE-{ANNO}-{SEQ:03d}'
                )
                print(f"✓ Sotto-voce creata: {sottovoce.codice_gerarchico()}")
                
            except ValidationError as e:
                print(f"✗ Errore validazione: {e}")
                
except Exception as e:
    print(f"✗ Errore: {e}")

# Mostra riepilogo
print(f"\n" + "="*60)
print(f"RIEPILOGO VOCI INTESTATE")
print("="*60)

voci_intestate = TitolarioVoce.objects.filter(anagrafica__isnull=False).select_related('anagrafica', 'parent')
print(f"Totale voci intestate: {voci_intestate.count()}")

for voce in voci_intestate:
    print(f"\n  {voce.codice_gerarchico()}")
    print(f"    Titolo: {voce.titolo}")
    print(f"    Anagrafica: {voce.anagrafica.nome}")
    print(f"    Pattern: {voce.pattern_codice}")
    
    # Mostra figli
    figli = voce.figli.all()
    if figli:
        print(f"    Sotto-voci ({figli.count()}):")
        for figlio in figli:
            print(f"      - {figlio.codice}: {figlio.titolo}")

print("\n✓ Test completato!")
