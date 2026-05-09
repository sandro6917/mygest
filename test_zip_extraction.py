"""
Test estrazione testo da file ZIP

Testa la nuova funzionalità di estrazione da archivi ZIP.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from ai_classifier.services.ml.ocr_service import OCRService
from documenti.models import Documento


def test_zip_files():
    """
    Testa l'estrazione da file ZIP reali nel database.
    """
    print("=" * 70)
    print("🧪 TEST ESTRAZIONE DA FILE ZIP")
    print("=" * 70)
    
    # Trova documenti con file .zip
    zip_docs = Documento.objects.filter(
        file__isnull=False,
        file__endswith='.zip'
    )[:5]  # Prendi primi 5 per test
    
    print(f"\n📦 Trovati {zip_docs.count()} documenti ZIP nel database")
    
    if not zip_docs.exists():
        print("⚠️ Nessun documento ZIP trovato nel database")
        return
    
    # Inizializza OCR Service
    ocr_service = OCRService()
    
    # Testa ogni documento ZIP
    for i, doc in enumerate(zip_docs, 1):
        print(f"\n{'=' * 70}")
        print(f"📄 Test #{i} - Documento ID: {doc.id}")
        print(f"   Codice: {doc.codice}")
        print(f"   Tipo: {doc.tipo.codice if doc.tipo else 'N/A'}")
        print(f"   File: {doc.file.name if doc.file else 'N/A'}")
        print(f"{'=' * 70}")
        
        # Verifica che il file esista
        if not doc.file:
            print("⚠️ Nessun file associato")
            continue
        
        file_path = doc.file.path
        
        if not os.path.exists(file_path):
            print(f"❌ File non trovato: {file_path}")
            continue
        
        try:
            # Estrai testo
            result = ocr_service.extract_text_from_file(file_path)
            
            print(f"\n📊 RISULTATI:")
            print(f"   Metodo: {result.get('method', 'N/A')}")
            print(f"   Pagine totali: {result.get('pages', 0)}")
            print(f"   Caratteri estratti: {len(result.get('text', ''))}")
            
            if result.get('metadata'):
                metadata = result['metadata']
                print(f"\n📋 METADATA:")
                print(f"   File ZIP: {metadata.get('zip_file', 'N/A')}")
                print(f"   File totali: {metadata.get('total_files', 0)}")
                print(f"   File processati: {len(metadata.get('processed_files', []))}")
                
                if metadata.get('processed_files'):
                    print(f"\n   📁 File processati con successo:")
                    for fname in metadata['processed_files']:
                        print(f"      • {fname}")
                
                if metadata.get('methods_used'):
                    print(f"\n   🔧 Metodi usati: {', '.join(metadata['methods_used'])}")
            
            # Mostra anteprima testo
            text = result.get('text', '')
            if text:
                preview = text[:500].replace('\n', ' ')
                print(f"\n📝 ANTEPRIMA TESTO (primi 500 caratteri):")
                print(f"   {preview}...")
            else:
                print(f"\n⚠️ Nessun testo estratto")
        
        except Exception as e:
            print(f"❌ ERRORE: {e}")
            import traceback
            traceback.print_exc()


def test_sample_zip():
    """
    Test con un file ZIP di esempio (se fornito come argomento).
    """
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
        
        if not os.path.exists(zip_path):
            print(f"❌ File non trovato: {zip_path}")
            return
        
        print(f"\n{'=' * 70}")
        print(f"🧪 TEST FILE ZIP PERSONALIZZATO")
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
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
            
            text = result.get('text', '')
            if text:
                print(f"\n📝 TESTO ESTRATTO:")
                print(text[:1000])
        
        except Exception as e:
            print(f"❌ ERRORE: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    # Test su file ZIP del database
    test_zip_files()
    
    # Test su file ZIP custom (se fornito)
    test_sample_zip()
    
    print(f"\n{'=' * 70}")
    print("✅ TEST COMPLETATO")
    print(f"{'=' * 70}")
