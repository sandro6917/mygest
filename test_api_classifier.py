"""
Test API AI Classifier

Testa gli endpoint REST API per predizioni ML.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from documenti.models import Documento
import json

User = get_user_model()


def get_auth_client():
    """
    Crea client autenticato per test API.
    """
    # Crea/ottieni user di test
    user, created = User.objects.get_or_create(
        username='test_ml',
        defaults={'email': 'test_ml@example.com'}
    )
    
    if created:
        user.set_password('test123')
        user.save()
    
    client = Client()
    client.force_login(user)
    
    return client


def test_models_endpoint():
    """
    Test GET /api/v1/ai-classifier/models/
    """
    print("\n" + "=" * 70)
    print("🧪 TEST: GET /api/v1/ai-classifier/models/")
    print("=" * 70)
    
    client = get_auth_client()
    
    response = client.get('/api/v1/ai-classifier/models/')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Modelli trovati: {len(data)}")
        
        if data:
            model = data[0]
            print(f"\n📊 Primo modello:")
            print(f"   Version: {model.get('version')}")
            print(f"   Accuracy: {model.get('accuracy', 0):.2%}")
            print(f"   Active: {model.get('is_active')}")
    else:
        print(f"❌ Errore: {response.status_code}")
        print(response.content)


def test_active_model_endpoint():
    """
    Test GET /api/v1/ai-classifier/models/active/
    """
    print("\n" + "=" * 70)
    print("🧪 TEST: GET /api/v1/ai-classifier/models/active/")
    print("=" * 70)
    
    client = get_auth_client()
    
    response = client.get('/api/v1/ai-classifier/models/active/')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Modello attivo:")
        print(f"   Version: {data.get('version')}")
        print(f"   Accuracy: {data.get('accuracy', 0):.2%}")
        print(f"   F1-Score: {data.get('f1_score', 0):.2%}")
        print(f"   Trained: {data.get('trained_at_formatted')}")
    else:
        print(f"❌ Errore: {response.status_code}")


def test_predict_endpoint():
    """
    Test POST /api/v1/ai-classifier/predict/
    """
    print("\n" + "=" * 70)
    print("🧪 TEST: POST /api/v1/ai-classifier/predict/")
    print("=" * 70)
    
    # Trova un documento con file
    doc = Documento.objects.filter(
        file__isnull=False,
        tipo__isnull=False
    ).exclude(file__endswith='.zip').first()
    
    if not doc or not os.path.exists(doc.file.path):
        print("⚠️ Nessun documento valido trovato per test")
        return
    
    print(f"\n📄 Test con documento: {doc.codice} (Tipo reale: {doc.tipo.codice})")
    
    client = get_auth_client()
    
    with open(doc.file.path, 'rb') as f:
        response = client.post(
            '/api/v1/ai-classifier/predict/',
            {
                'file': f,
                'return_top_n': 5,
                'save_prediction': True,
                'documento_id': doc.id,
            },
            format='multipart'
        )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('success'):
            predictions = data.get('predictions', {})
            tipo_pred = predictions.get('tipo', {})
            
            print(f"\n✅ PREDIZIONE COMPLETATA:")
            print(f"   Predetto: {tipo_pred.get('top_prediction')}")
            print(f"   Confidence: {tipo_pred.get('confidence', 0):.1%}")
            print(f"   Reale: {doc.tipo.codice}")
            
            if tipo_pred.get('top_prediction') == doc.tipo.codice:
                print(f"   ✅ CORRETTO!")
            else:
                print(f"   ❌ Errato")
            
            print(f"\n📊 Top 5 predizioni:")
            for i, (tipo, conf) in enumerate(tipo_pred.get('all_predictions', [])[:5], 1):
                marker = "✅" if tipo == doc.tipo.codice else "  "
                print(f"   {marker} {i}. {tipo:10} {conf:5.1%}")
            
            print(f"\n📋 Metadata:")
            metadata = data.get('metadata', {})
            print(f"   OCR: {metadata.get('ocr_method')}")
            print(f"   Caratteri: {metadata.get('text_length')}")
            
            if data.get('prediction_id'):
                print(f"\n💾 Predizione salvata: ID {data.get('prediction_id')}")
        else:
            print(f"❌ Predizione fallita: {data.get('error')}")
    else:
        print(f"❌ Errore HTTP: {response.status_code}")
        print(response.content)


def test_predictions_list_endpoint():
    """
    Test GET /api/v1/ai-classifier/predictions/
    """
    print("\n" + "=" * 70)
    print("🧪 TEST: GET /api/v1/ai-classifier/predictions/")
    print("=" * 70)
    
    client = get_auth_client()
    
    response = client.get('/api/v1/ai-classifier/predictions/')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Predizioni trovate: {len(data)}")
        
        if data:
            pred = data[0]
            print(f"\n📊 Ultima predizione:")
            print(f"   ID: {pred.get('id')}")
            print(f"   Documento: {pred.get('documento_codice')}")
            print(f"   Tipo predetto: {pred.get('predicted_type')}")
            print(f"   Confidence: {pred.get('confidence_tipo', 0):.1%}")
            print(f"   Confermata: {pred.get('user_confirmed')}")
            print(f"   Corretta: {pred.get('user_corrected')}")
    else:
        print(f"❌ Errore: {response.status_code}")


def test_feedback_endpoint():
    """
    Test POST /api/v1/ai-classifier/predictions/{id}/feedback/
    """
    print("\n" + "=" * 70)
    print("🧪 TEST: POST /api/v1/ai-classifier/predictions/{id}/feedback/")
    print("=" * 70)
    
    # Trova una predizione recente
    from ai_classifier.models import DocumentPrediction
    
    prediction = DocumentPrediction.objects.order_by('-created_at').first()
    
    if not prediction:
        print("⚠️ Nessuna predizione trovata per test feedback")
        return
    
    print(f"\n📄 Test feedback su predizione ID: {prediction.id}")
    print(f"   Tipo predetto: {prediction.predicted_type}")
    
    client = get_auth_client()
    
    response = client.post(
        f'/api/v1/ai-classifier/predictions/{prediction.id}/feedback/',
        data=json.dumps({
            'confirmed': True,
            'feedback_text': 'Test feedback from API',
            'add_to_training': False,  # Non aggiungere a training per test
        }),
        content_type='application/json'
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Feedback registrato:")
        print(f"   Success: {data.get('success')}")
        print(f"   Message: {data.get('message')}")
    else:
        print(f"❌ Errore: {response.status_code}")
        print(response.content)


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 TEST API AI CLASSIFIER")
    print("=" * 70)
    
    # Test endpoint
    test_models_endpoint()
    test_active_model_endpoint()
    test_predict_endpoint()
    test_predictions_list_endpoint()
    test_feedback_endpoint()
    
    print("\n" + "=" * 70)
    print("✅ TUTTI I TEST COMPLETATI")
    print("=" * 70 + "\n")
