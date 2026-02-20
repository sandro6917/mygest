#!/usr/bin/env python
"""
Test per verificare il meccanismo di aggiunta del codice cliente al nome dell'unità fisica
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mygest.settings")
django.setup()

from archivio_fisico.models import UnitaFisica
from anagrafiche.models import Cliente, Anagrafica

def test_cliente_suffix():
    """
    Test del meccanismo di aggiunta/rimozione/sostituzione del codice cliente
    """
    print("\n🧪 Test UnitaFisica + Cliente - Automatismo Codice Anagrafica\n")
    
    # 1. Crea un cliente di test
    print("1️⃣  Creazione cliente di test...")
    anagrafica, _ = Anagrafica.objects.get_or_create(
        codice="CHISAN01",
        defaults={
            "tipo": "PF",
            "cognome": "Chimenti",
            "nome": "Sandro",
        }
    )
    cliente, _ = Cliente.objects.get_or_create(
        anagrafica=anagrafica
    )
    print(f"   ✅ Cliente creato: {cliente.anagrafica.display_name()} ({cliente.anagrafica.codice})")
    
    # 2. Crea unità fisica SENZA cliente
    print("\n2️⃣  Creazione unità fisica senza cliente...")
    unita = UnitaFisica.objects.create(
        prefisso_codice="TEST",
        nome="Documenti contabili 2025",
        tipo="contenitore"
    )
    print(f"   ✅ Unità creata: '{unita.nome}'")
    print(f"   📋 Nome atteso: 'Documenti contabili 2025'")
    assert unita.nome == "Documenti contabili 2025", f"❌ Nome non corretto: {unita.nome}"
    
    # 3. Aggiorna unità fisica AGGIUNGENDO cliente
    print("\n3️⃣  Aggiunta cliente all'unità esistente...")
    unita.cliente = cliente
    unita.save()
    unita.refresh_from_db()
    print(f"   ✅ Unità aggiornata: '{unita.nome}'")
    print(f"   📋 Nome atteso: 'Documenti contabili 2025 - CHISAN01'")
    assert unita.nome == "Documenti contabili 2025 - CHISAN01", f"❌ Nome non corretto: {unita.nome}"
    
    # 4. Modifica manuale del nome (con cliente già presente)
    print("\n4️⃣  Modifica manuale del nome con cliente presente...")
    unita.nome = "Fatture 2025"
    unita.save()
    unita.refresh_from_db()
    print(f"   ✅ Unità aggiornata: '{unita.nome}'")
    print(f"   📋 Nome atteso: 'Fatture 2025 - CHISAN01' (suffisso forzato)")
    assert unita.nome == "Fatture 2025 - CHISAN01", f"❌ Nome non corretto: {unita.nome}"
    
    # 5. Cambio cliente
    print("\n5️⃣  Cambio cliente...")
    anagrafica2, _ = Anagrafica.objects.get_or_create(
        codice="ROSMAR01",
        defaults={
            "tipo": "PF",
            "cognome": "Rossi",
            "nome": "Mario",
        }
    )
    cliente2, _ = Cliente.objects.get_or_create(
        anagrafica=anagrafica2
    )
    unita.cliente = cliente2
    unita.save()
    unita.refresh_from_db()
    print(f"   ✅ Cliente cambiato: {cliente2.anagrafica.display_name()} ({cliente2.anagrafica.codice})")
    print(f"   ✅ Unità aggiornata: '{unita.nome}'")
    print(f"   📋 Nome atteso: 'Fatture 2025 - ROSMAR01' (vecchio codice sostituito)")
    assert unita.nome == "Fatture 2025 - ROSMAR01", f"❌ Nome non corretto: {unita.nome}"
    
    # 6. Rimozione cliente
    print("\n6️⃣  Rimozione cliente...")
    unita.cliente = None
    unita.save()
    unita.refresh_from_db()
    print(f"   ✅ Cliente rimosso")
    print(f"   ✅ Unità aggiornata: '{unita.nome}'")
    print(f"   📋 Nome atteso: 'Fatture 2025' (suffisso rimosso)")
    assert unita.nome == "Fatture 2025", f"❌ Nome non corretto: {unita.nome}"
    
    # 7. Test creazione diretta con cliente
    print("\n7️⃣  Creazione diretta con cliente associato...")
    unita2 = UnitaFisica.objects.create(
        prefisso_codice="TEST2",
        nome="Archivio 2024",
        tipo="contenitore",
        cliente=cliente
    )
    print(f"   ✅ Unità creata: '{unita2.nome}'")
    print(f"   📋 Nome atteso: 'Archivio 2024 - CHISAN01'")
    assert unita2.nome == "Archivio 2024 - CHISAN01", f"❌ Nome non corretto: {unita2.nome}"
    
    # Cleanup
    print("\n🧹 Pulizia...")
    unita.delete()
    unita2.delete()
    
    print("\n✅ TUTTI I TEST SUPERATI! 🎉\n")


if __name__ == "__main__":
    test_cliente_suffix()
