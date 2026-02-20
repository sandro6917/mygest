#!/usr/bin/env python
"""
Script di test manuale per verificare il problema degli attributi dinamici
nel pattern del nome file durante la creazione di un documento.

Uso:
    python test_attributi_nome_file_manuale.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date
from documenti.models import Documento, DocumentiTipo, AttributoDefinizione
from documenti.forms import DocumentoDinamicoForm
from anagrafiche.models import Anagrafica, Cliente

def test_creazione_documento():
    """Test di creazione documento con attributi dinamici nel pattern nome file."""
    
    print("=" * 80)
    print("TEST CREAZIONE DOCUMENTO CON ATTRIBUTI DINAMICI NEL PATTERN NOME FILE")
    print("=" * 80)
    
    # 1. Trova o crea tipo documento con pattern
    tipo, created = DocumentiTipo.objects.get_or_create(
        codice="PRES_TEST",
        defaults={
            "nome": "Presenze Test",
            "nome_file_pattern": "Presenze_{attr:anno_riferimento}{attr:mese_riferimento}_{cliente.anagrafica.codice}",
            "estensioni_permesse": "pdf,xlsx,docx"
        }
    )
    
    if created:
        print(f"✓ Creato tipo documento: {tipo.nome}")
        
        # Crea attributi dinamici
        AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="anno_riferimento",
            nome="Anno di riferimento",
            tipo_dato="string",
            required=True,
            ordine=1
        )
        
        AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="mese_riferimento",
            nome="Mese di riferimento",
            tipo_dato="string",
            required=True,
            ordine=2
        )
        print("✓ Creati attributi dinamici")
    else:
        print(f"✓ Trovato tipo documento esistente: {tipo.nome}")
    
    # 2. Trova o crea cliente
    try:
        anagrafica = Anagrafica.objects.filter(codice="TESTCLI").first()
        if not anagrafica:
            # Crea anagrafica di test
            anagrafica = Anagrafica.objects.create(
                tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
                ragione_sociale="TEST CLIENTE SRL",
                codice_fiscale="98765432109",
                codice="TESTCLI"
            )
            print(f"✓ Creata anagrafica di test: {anagrafica.display_name()}")
        else:
            print(f"✓ Trovata anagrafica esistente: {anagrafica.display_name()}")
        
        cliente = Cliente.objects.filter(anagrafica=anagrafica).first()
        if not cliente:
            cliente = Cliente.objects.create(anagrafica=anagrafica)
            print("✓ Creato cliente di test")
        else:
            print("✓ Trovato cliente esistente")
            
    except Exception as e:
        print(f"✗ Errore creazione cliente: {e}")
        return
    
    # 3. Crea documento con form
    print("\n" + "-" * 80)
    print("CREAZIONE DOCUMENTO CON FORM")
    print("-" * 80)
    
    file_content = b"Test content for manual test"
    uploaded_file = SimpleUploadedFile("test_manuale.pdf", file_content, content_type="application/pdf")
    
    form_data = {
        "tipo": tipo.pk,
        "cliente": cliente.pk,
        "descrizione": "Test documento presenze manuale",
        "data_documento": date.today(),
        "stato": "bozza",
        "digitale": True,
        "attr_anno_riferimento": "2024",
        "attr_mese_riferimento": "12",
    }
    
    form = DocumentoDinamicoForm(
        data=form_data,
        files={"file": uploaded_file},
        tipo=tipo
    )
    
    if not form.is_valid():
        print(f"✗ Form non valido: {form.errors}")
        return
    
    print("✓ Form valido")
    
    # Salva il documento
    try:
        doc = form.save()
        print(f"✓ Documento creato con ID: {doc.pk}")
    except Exception as e:
        print(f"✗ Errore durante il salvataggio: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Verifica risultato
    print("\n" + "-" * 80)
    print("VERIFICA RISULTATO")
    print("-" * 80)
    
    if doc.file:
        filename = os.path.basename(doc.file.name)
        print(f"Nome file: {filename}")
        
        # Verifica contenuto
        checks = [
            ("Anno 2024", "2024" in filename),
            ("Mese 12", "12" in filename),
            ("Codice cliente TESTCLI", "TESTCLI" in filename),
            ("Prefisso 'Presenze'", "Presenze" in filename or "presenze" in filename.lower()),
        ]
        
        all_ok = True
        for check_name, check_result in checks:
            status = "✓" if check_result else "✗"
            print(f"{status} {check_name}: {'OK' if check_result else 'FALLITO'}")
            if not check_result:
                all_ok = False
        
        if all_ok:
            print("\n" + "=" * 80)
            print("✓✓✓ TEST SUPERATO! Il nome file contiene tutti gli attributi dinamici ✓✓✓")
            print("=" * 80)
        else:
            print("\n" + "=" * 80)
            print("✗✗✗ TEST FALLITO! Il nome file NON contiene tutti gli attributi dinamici ✗✗✗")
            print("=" * 80)
            print(f"\nPattern atteso: Presenze_202412_TESTCLI.pdf")
            print(f"Pattern ottenuto: {filename}")
        
        # Cleanup (opzionale)
        print(f"\nDocumento creato: ID={doc.pk}, File={doc.file.name}")
        risposta = input("\nVuoi eliminare il documento di test? (s/n): ")
        if risposta.lower() == 's':
            doc.delete()
            print("✓ Documento eliminato")
        else:
            print("✓ Documento mantenuto per ispezione manuale")
    else:
        print("✗ Il documento non ha un file associato!")

if __name__ == "__main__":
    try:
        test_creazione_documento()
    except KeyboardInterrupt:
        print("\n\nTest interrotto dall'utente")
    except Exception as e:
        print(f"\n✗ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
