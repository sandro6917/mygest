#!/usr/bin/env python
"""
Script di test per l'importazione cedolini.
Testa il flusso completo senza richiedere l'interfaccia web.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from documenti.import_cedolini import CedolinoImporter

def main():
    zip_file_path = 'Cedolini_Fortezza_202512.zip'
    
    if not os.path.exists(zip_file_path):
        print(f"❌ File non trovato: {zip_file_path}")
        return 1
    
    print("🚀 Inizio test importazione cedolini...")
    print(f"📁 File: {zip_file_path}")
    print()
    
    # Leggi file ZIP
    with open(zip_file_path, 'rb') as f:
        zip_content = f.read()
    
    # Crea uploaded file simulato
    zip_file = SimpleUploadedFile(
        name=zip_file_path,
        content=zip_content,
        content_type='application/zip'
    )
    
    # Importa
    importer = CedolinoImporter(zip_file)
    risultati = importer.importa()
    
    # Mostra risultati
    print("\n" + "="*60)
    print("📊 RISULTATI IMPORTAZIONE")
    print("="*60)
    print(f"✅ Documenti creati: {risultati['created']}")
    print(f"❌ Errori: {len(risultati['errors'])}")
    print(f"⚠️  Warning: {len(risultati['warnings'])}")
    print()
    
    if risultati['documenti']:
        print("📄 Documenti creati:")
        for doc in risultati['documenti']:
            print(f"  - {doc['codice']}: {doc['descrizione']}")
            print(f"    File: {doc['filename']}")
            print(f"    ID: {doc['id']}")
            print()
    
    if risultati['errors']:
        print("❌ Errori:")
        for error in risultati['errors']:
            print(f"  - {error}")
        print()
    
    if risultati['warnings']:
        print("⚠️  Warning:")
        for warning in risultati['warnings']:
            print(f"  - {warning}")
        print()
    
    # Verifica creazione nel database
    from documenti.models import Documento
    from fascicoli.models import Fascicolo
    from anagrafiche.models import Anagrafica, Cliente
    
    print("="*60)
    print("🔍 VERIFICA DATABASE")
    print("="*60)
    
    bpag_docs = Documento.objects.filter(tipo__codice='BPAG').order_by('-creato_il')[:10]
    print(f"Documenti BPAG totali nel DB: {bpag_docs.count()}")
    
    if bpag_docs.exists():
        ultimo = bpag_docs.first()
        print(f"\nUltimo documento BPAG creato:")
        print(f"  Codice: {ultimo.codice}")
        print(f"  Descrizione: {ultimo.descrizione}")
        print(f"  Cliente: {ultimo.cliente}")
        print(f"  Fascicolo: {ultimo.fascicolo}")
        print(f"  Data: {ultimo.data_documento}")
        
        # Attributi
        attributi = ultimo.attributi_valori.select_related('definizione').all()
        if attributi.exists():
            print(f"\n  Attributi:")
            for attr in attributi:
                print(f"    - {attr.definizione.nome}: {attr.valore}")
    
    # Fascicoli paghe
    fascicoli_pag = Fascicolo.objects.filter(titolario_voce__codice='PAG')
    print(f"\nFascicoli PAG totali: {fascicoli_pag.count()}")
    for fasc in fascicoli_pag:
        print(f"  - {fasc.titolo} (Cliente: {fasc.cliente})")
    
    print("\n✅ Test completato!")
    
    return 0 if risultati['created'] > 0 else 1

if __name__ == '__main__':
    sys.exit(main())
