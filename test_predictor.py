"""
Test Predictor Service

Testa il servizio di predizione ML su documenti reali.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from ai_classifier.services.ml.predictor import Predictor
from documenti.models import Documento


def test_predictor_single():
    """
    Test predizione su singolo documento.
    """
    print("=" * 70)
    print("🧪 TEST PREDICTOR SERVICE - Singolo Documento")
    print("=" * 70)
    
    # Inizializza predictor
    try:
        predictor = Predictor()
        print(f"\n✅ Predictor inizializzato")
        print(f"   Modello attivo: {predictor.ml_model.version if predictor.ml_model else 'N/A'}")
        if predictor.ml_model:
            print(f"   Accuracy: {predictor.ml_model.accuracy:.2%}")
    except Exception as e:
        print(f"\n❌ Errore inizializzazione: {e}")
        return
    
    # Trova un documento di test
    test_docs = Documento.objects.filter(
        file__isnull=False,
        tipo__isnull=False,
    ).exclude(
        file__endswith='.zip'  # Esclude ZIP per test più veloce
    )[:5]
    
    if not test_docs.exists():
        print("\n⚠️ Nessun documento trovato per test")
        return
    
    print(f"\n📄 Trovati {test_docs.count()} documenti per test")
    
    # Testa primo documento
    doc = test_docs.first()
    
    print(f"\n{'=' * 70}")
    print(f"📄 TEST DOCUMENTO")
    print(f"{'=' * 70}")
    print(f"   ID: {doc.id}")
    print(f"   Codice: {doc.codice}")
    print(f"   Tipo reale: {doc.tipo.codice} ({doc.tipo.descrizione})")
    print(f"   File: {doc.file.name if doc.file else 'N/A'}")
    
    if not os.path.exists(doc.file.path):
        print(f"\n❌ File non trovato: {doc.file.path}")
        return
    
    print(f"\n🔍 Esecuzione predizione...")
    
    try:
        # Fa predizione
        result = predictor.predict(
            file_path=doc.file.path,
            filename=os.path.basename(doc.file.name),
            return_top_n=5,
        )
        
        if not result['success']:
            print(f"\n❌ Predizione fallita: {result['error']}")
            return
        
        # Mostra risultati
        print(f"\n{'=' * 70}")
        print(f"📊 RISULTATI PREDIZIONE")
        print(f"{'=' * 70}")
        
        tipo_pred = result['predictions']['tipo']
        print(f"\n🎯 TIPO DOCUMENTO:")
        print(f"   Predetto: {tipo_pred['top_prediction']}")
        print(f"   Confidence: {tipo_pred['confidence']:.1%}")
        print(f"   Reale: {doc.tipo.codice}")
        
        # Verifica correttezza
        if tipo_pred['top_prediction'] == doc.tipo.codice:
            print(f"   ✅ PREDIZIONE CORRETTA!")
        else:
            print(f"   ❌ Predizione errata")
        
        # Mostra top 5 predizioni
        print(f"\n📊 TOP 5 PREDIZIONI:")
        for i, (tipo, conf) in enumerate(tipo_pred['all_predictions'], 1):
            marker = "✅" if tipo == doc.tipo.codice else "  "
            bar = "█" * int(conf * 50)
            print(f"   {marker} {i}. {tipo:12} {conf:6.1%} {bar}")
        
        # Mostra metadata estratti
        print(f"\n📋 METADATA ESTRATTI:")
        metadata = result['metadata']['extracted_features']
        
        if metadata.get('codici_fiscali'):
            print(f"   Codici Fiscali: {', '.join(metadata['codici_fiscali'][:3])}")
        
        if metadata.get('partite_iva'):
            print(f"   Partite IVA: {', '.join(metadata['partite_iva'][:3])}")
        
        if metadata.get('importi'):
            print(f"   Importi: {', '.join(metadata['importi'][:3])}")
        
        if metadata.get('date'):
            print(f"   Date: {', '.join(metadata['date'][:3])}")
        
        print(f"   Entità Persone: {metadata.get('entities_persone', 0)}")
        print(f"   Entità Organizzazioni: {metadata.get('entities_org', 0)}")
        print(f"   Parole: {metadata.get('word_count', 0)}")
        
        print(f"\n🔧 INFO ELABORAZIONE:")
        print(f"   Metodo OCR: {result['metadata']['ocr_method']}")
        print(f"   Pagine: {result['metadata']['ocr_pages']}")
        print(f"   Caratteri: {result['metadata']['text_length']}")
        
        print(f"\n🤖 INFO MODELLO:")
        print(f"   Versione: {result['model_info']['version']}")
        print(f"   Accuracy: {result['model_info']['accuracy']:.2%}")
        
        return result
    
    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_predictor_batch():
    """
    Test predizioni batch su più documenti.
    """
    print(f"\n{'=' * 70}")
    print("🧪 TEST BATCH PREDICTIONS")
    print(f"{'=' * 70}")
    
    # Inizializza predictor
    predictor = Predictor()
    
    # Trova documenti di test (uno per tipo)
    test_docs = []
    seen_types = set()
    
    for doc in Documento.objects.filter(
        file__isnull=False,
        tipo__isnull=False,
    ).exclude(file__endswith='.zip')[:50]:
        if doc.tipo.codice not in seen_types:
            if os.path.exists(doc.file.path):
                test_docs.append(doc)
                seen_types.add(doc.tipo.codice)
        
        if len(test_docs) >= 10:  # Max 10 per velocità
            break
    
    print(f"\n📄 Test su {len(test_docs)} documenti ({len(seen_types)} tipi diversi)")
    
    # Statistiche
    correct = 0
    total = 0
    results_by_type = {}
    
    for doc in test_docs:
        print(f"\n  📄 {doc.codice} ({doc.tipo.codice})...", end=" ")
        
        try:
            result = predictor.predict(doc.file.path, return_top_n=1)
            
            if result['success']:
                predicted = result['predictions']['tipo']['top_prediction']
                confidence = result['predictions']['tipo']['confidence']
                actual = doc.tipo.codice
                
                is_correct = predicted == actual
                if is_correct:
                    correct += 1
                    print(f"✅ {confidence:.0%}")
                else:
                    print(f"❌ Predetto: {predicted} ({confidence:.0%})")
                
                total += 1
                
                # Salva per tipo
                if actual not in results_by_type:
                    results_by_type[actual] = {'correct': 0, 'total': 0}
                
                results_by_type[actual]['total'] += 1
                if is_correct:
                    results_by_type[actual]['correct'] += 1
            else:
                print(f"⚠️ Errore: {result['error']}")
        
        except Exception as e:
            print(f"❌ Eccezione: {e}")
    
    # Mostra risultati aggregati
    print(f"\n{'=' * 70}")
    print(f"📊 RISULTATI BATCH")
    print(f"{'=' * 70}")
    print(f"\n🎯 ACCURACY COMPLESSIVA: {correct}/{total} = {correct/total*100:.1f}%")
    
    print(f"\n📊 ACCURACY PER TIPO:")
    for tipo, stats in sorted(results_by_type.items()):
        acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"   {tipo:12} {stats['correct']}/{stats['total']} = {acc:5.1f}%")


if __name__ == '__main__':
    # Test singolo documento
    test_predictor_single()
    
    # Test batch (opzionale)
    if '--batch' in sys.argv:
        test_predictor_batch()
    
    print(f"\n{'=' * 70}")
    print("✅ TEST COMPLETATI")
    print(f"{'=' * 70}\n")
