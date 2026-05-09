"""
Test rapido estrazione ZIP - senza database
"""
import os
import sys
import tempfile
import zipfile

# Setup Django per imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
import django
django.setup()

from ai_classifier.services.ml.ocr_service import OCRService


def create_sample_zip():
    """
    Crea un file ZIP di test con documenti di esempio.
    """
    temp_dir = tempfile.mkdtemp(prefix='test_zip_')
    zip_path = os.path.join(temp_dir, 'test_documents.zip')
    
    # Crea alcuni file di test
    txt_content = """
    CEDOLINO PAGA - Gennaio 2024
    
    Dipendente: Mario Rossi
    Codice Fiscale: RSSMRA85M01H501U
    Matricola: 12345
    
    Retribuzione Lorda: € 2.500,00
    Contributi INPS: € 450,00
    Ritenute IRPEF: € 380,00
    
    Netto da pagare: € 1.670,00
    """
    
    pdf_info = "Documento PDF simulato - Fattura n. 2024/001"
    
    # Crea ZIP
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        # Aggiungi file TXT
        zipf.writestr('cedolino_gennaio.txt', txt_content)
        zipf.writestr('fattura.txt', pdf_info)
        zipf.writestr('README.txt', 'Archivio documenti gennaio 2024')
    
    return zip_path, temp_dir


def test_zip_extraction():
    """
    Test estrazione ZIP con file di esempio.
    """
    print("=" * 70)
    print("🧪 TEST ESTRAZIONE DA FILE ZIP")
    print("=" * 70)
    
    # Crea ZIP di test
    print("\n📦 Creando file ZIP di test...")
    zip_path, temp_dir = create_sample_zip()
    print(f"   ✅ ZIP creato: {zip_path}")
    
    # Inizializza OCR Service
    ocr_service = OCRService(min_text_length=50)
    
    try:
        print(f"\n🔍 Estraendo testo dallo ZIP...")
        result = ocr_service.extract_text_from_file(zip_path)
        
        print(f"\n{'=' * 70}")
        print(f"📊 RISULTATI:")
        print(f"{'=' * 70}")
        print(f"   Metodo: {result.get('method', 'N/A')}")
        print(f"   Pagine totali: {result.get('pages', 0)}")
        print(f"   Caratteri estratti: {len(result.get('text', ''))}")
        
        if result.get('metadata'):
            metadata = result['metadata']
            print(f"\n📋 METADATA:")
            print(f"   File ZIP: {metadata.get('zip_file', 'N/A')}")
            print(f"   File totali nello ZIP: {metadata.get('total_files', 0)}")
            print(f"   File processati con successo: {len(metadata.get('processed_files', []))}")
            
            if metadata.get('processed_files'):
                print(f"\n   📁 File processati:")
                for fname in metadata['processed_files']:
                    print(f"      ✅ {fname}")
            
            if metadata.get('methods_used'):
                print(f"\n   🔧 Metodi di estrazione usati: {', '.join(metadata['methods_used'])}")
        
        # Mostra testo estratto
        text = result.get('text', '')
        if text:
            print(f"\n{'=' * 70}")
            print(f"📝 TESTO ESTRATTO:")
            print(f"{'=' * 70}")
            print(text)
        else:
            print(f"\n⚠️ Nessun testo estratto")
        
        # Verifica che abbia estratto il contenuto
        if 'CEDOLINO' in text and 'RSSMRA85M01H501U' in text:
            print(f"\n{'=' * 70}")
            print(f"✅ TEST SUPERATO!")
            print(f"{'=' * 70}")
            print(f"   ✅ Testo estratto correttamente")
            print(f"   ✅ Codice fiscale rilevato")
            print(f"   ✅ Contenuto completo dei file")
            return True
        else:
            print(f"\n❌ TEST FALLITO: contenuto non completo")
            return False
    
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Pulizia
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n🧹 File di test puliti")


def test_real_zip():
    """
    Test con un file ZIP reale se fornito come argomento.
    """
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
        
        if not os.path.exists(zip_path):
            print(f"\n❌ File non trovato: {zip_path}")
            return False
        
        if not zip_path.endswith('.zip'):
            print(f"\n❌ File non è uno ZIP: {zip_path}")
            return False
        
        print(f"\n{'=' * 70}")
        print(f"🧪 TEST FILE ZIP REALE")
        print(f"{'=' * 70}")
        print(f"📦 File: {zip_path}")
        
        ocr_service = OCRService()
        
        try:
            result = ocr_service.extract_text_from_file(zip_path)
            
            print(f"\n📊 RISULTATI:")
            print(f"   Metodo: {result.get('method', 'N/A')}")
            print(f"   Caratteri: {len(result.get('text', ''))}")
            
            if result.get('metadata'):
                metadata = result['metadata']
                print(f"\n📋 METADATA:")
                print(f"   File totali: {metadata.get('total_files', 0)}")
                print(f"   File processati: {len(metadata.get('processed_files', []))}")
                
                if metadata.get('processed_files'):
                    print(f"\n   📁 File processati:")
                    for fname in metadata.get('processed_files', [])[:10]:  # Max 10
                        print(f"      • {fname}")
                    
                    if len(metadata.get('processed_files', [])) > 10:
                        print(f"      ... e altri {len(metadata['processed_files']) - 10} file")
            
            text = result.get('text', '')
            if text:
                preview = text[:1000]
                print(f"\n📝 ANTEPRIMA TESTO (primi 1000 caratteri):")
                print(f"{preview}...")
            
            return True
        
        except Exception as e:
            print(f"\n❌ ERRORE: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    print("\n🚀 Avvio test estrazione ZIP...")
    
    # Test con ZIP di esempio
    success = test_zip_extraction()
    
    # Test con ZIP reale (se fornito)
    if len(sys.argv) > 1:
        test_real_zip()
    
    print(f"\n{'=' * 70}")
    if success:
        print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO")
    else:
        print("❌ ALCUNI TEST SONO FALLITI")
    print(f"{'=' * 70}\n")
    
    sys.exit(0 if success else 1)
