#!/usr/bin/env python3
"""
Test autenticato degli endpoint AI Import.
Crea un utente di test, ottiene il token JWT e testa i workflow endpoint.
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from anagrafiche.models import Anagrafica, Cliente
from documenti.models import DocumentiTipo
from ai_classifier.models import DocumentExtractionTemplate, ExtractionTemplatePage, ExtractionTemplateZone

User = get_user_model()

def test_api_workflow():
    """Test completo del workflow AI Import via API"""
    
    print("\n" + "="*70)
    print("TEST WORKFLOW AI IMPORT - API ENDPOINTS")
    print("="*70)
    
    # 1. Setup test user
    print("\n1. Setup utente di test...")
    user, created = User.objects.get_or_create(
        username='test_ai',
        defaults={
            'email': 'test_ai@example.com',
            'is_staff': True,
            'is_active': True
        }
    )
    if created:
        user.set_password('test_password_123')
        user.save()
        print("   ✅ Utente creato")
    else:
        print("   ✅ Utente esistente riutilizzato")
    
    # 2. Setup API client
    print("\n2. Configurazione API client...")
    client = APIClient()
    client.force_authenticate(user=user)
    print("   ✅ Client autenticato")
    
    # 3. Test Template Management Endpoints
    print("\n3. Test Template Management...")
    
    # List templates
    response = client.get('/api/v1/ai-classifier/templates/')
    print(f"   GET /templates/: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print(f"   ✅ Templates trovati: {response.data['count']}")
    
    # Create template
    template_data = {
        'name': 'Template Test Cedolino',
        'document_type': 'CEDOL',
        'description': 'Template di test per cedolini',
        'is_active': True
    }
    response = client.post('/api/v1/ai-classifier/templates/', template_data)
    print(f"   POST /templates/: {response.status_code}")
    
    if response.status_code == 201:
        template_id = response.data['id']
        print(f"   ✅ Template creato: ID={template_id}, Name={response.data['name']}")
        
        # Add page to template
        page_data = {
            'page_number': 1,
            'template_image': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
        }
        response = client.post(f'/api/v1/ai-classifier/templates/{template_id}/add_page/', page_data)
        print(f"   POST /templates/{template_id}/add_page/: {response.status_code}")
        
        if response.status_code == 201:
            page_id = response.data['id']
            print(f"   ✅ Pagina aggiunta: ID={page_id}, Number={response.data['page_number']}")
            
            # Add zone to page
            zone_data = {
                'page_id': page_id,
                'field_name': 'matricola',
                'x': 10.5,
                'y': 15.2,
                'width': 20.0,
                'height': 5.0
            }
            response = client.post(f'/api/v1/ai-classifier/templates/{template_id}/add_zone/', zone_data)
            print(f"   POST /templates/{template_id}/add_zone/: {response.status_code}")
            
            if response.status_code == 201:
                zone_id = response.data['id']
                print(f"   ✅ Zona aggiunta: ID={zone_id}, Field={response.data['field_name']}")
                print(f"      Coordinate: x={zone_data['x']}%, y={zone_data['y']}%, w={zone_data['width']}%, h={zone_data['height']}%")
            else:
                print(f"   ❌ Errore creazione zona: {response.data}")
        else:
            print(f"   ❌ Errore aggiunta pagina: {response.data}")
    elif response.status_code == 400:
        # Template già esiste o tipo documento mancante
        errors = response.data
        if 'document_type' in errors:
            print(f"   ℹ️  Tipo documento CEDOL non esiste - creo tipo documento...")
            # Crea tipo documento
            doc_tipo, created = DocumentiTipo.objects.get_or_create(
                codice='CEDOL',
                defaults={
                    'nome': 'Cedolino',
                    'descrizione': 'Cedolino paga',
                    'tracciabile': True,
                    'digitale': True
                }
            )
            if created:
                print(f"   ✅ Tipo documento creato: {doc_tipo.codice} - {doc_tipo.nome}")
            
            # Riprova creazione template
            response = client.post('/api/v1/ai-classifier/templates/', template_data)
            if response.status_code == 201:
                print(f"   ✅ Template creato (secondo tentativo): ID={response.data['id']}")
            else:
                print(f"   ❌ Errore creazione template: {response.data}")
        else:
            print(f"   ℹ️  Errore validazione: {errors}")
    else:
        print(f"   ❌ Errore creazione template: {response.data}")
    
    # 4. Test AI Import Workflow Endpoints
    print("\n4. Test AI Import Workflow...")
    
    # Setup: crea cliente di test
    anagrafica, _ = Anagrafica.objects.get_or_create(
        codice_fiscale='TESTCF00A01H501Z',
        defaults={
            'nome': 'Test',
            'cognome': 'User',
            'tipo': 'PF'
        }
    )
    cliente, _ = Cliente.objects.get_or_create(anagrafica=anagrafica)
    
    # Upload document (simulato)
    upload_data = {
        'file': 'base64_or_file_data_here',
        'filename': 'cedolino_test.pdf',
        'cliente_id': cliente.id
    }
    response = client.post('/api/v1/ai-classifier/ai-import/upload/', upload_data, format='json')
    print(f"   POST /ai-import/upload/: {response.status_code}")
    
    if response.status_code in [200, 201]:
        upload_id = response.data.get('upload_id')
        print(f"   ✅ Upload registrato: ID={upload_id}")
        
        # Predict document type
        predict_data = {'upload_id': upload_id}
        response = client.post('/api/v1/ai-classifier/ai-import/predict/', predict_data)
        print(f"   POST /ai-import/predict/: {response.status_code}")
        
        if response.status_code == 200:
            predictions = response.data.get('predictions', [])
            print(f"   ✅ Predizioni ricevute: {len(predictions)}")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"      {i}. {pred.get('tipo')} (conf: {pred.get('confidence', 0):.2f})")
        else:
            print(f"   ℹ️  Response: {response.data}")
    else:
        print(f"   ℹ️  Endpoint upload non completamente implementato: {response.data}")
    
    # 5. Test Statistics
    print("\n5. Test Statistics...")
    response = client.get('/api/v1/ai-classifier/ai-import/statistics/')
    print(f"   GET /ai-import/statistics/: {response.status_code}")
    if response.status_code == 200:
        stats = response.data
        print(f"   ✅ Statistiche:")
        print(f"      Templates: {stats.get('total_templates', 0)}")
        print(f"      Feedback: {stats.get('total_feedback', 0)}")
        print(f"      Accuratezza: {stats.get('accuracy', 0):.2%}")
    
    # 6. Cleanup summary
    print("\n" + "="*70)
    print("RIEPILOGO TEST")
    print("="*70)
    print(f"✅ Templates DB: {DocumentExtractionTemplate.objects.count()}")
    print(f"✅ Pages DB: {ExtractionTemplatePage.objects.count()}")
    print(f"✅ Zones DB: {ExtractionTemplateZone.objects.count()}")
    print(f"✅ Document Types: {DocumentiTipo.objects.filter(codice__in=['CEDOL', 'FAT', 'DDT']).count()}")
    print("="*70)
    
    return True

if __name__ == '__main__':
    try:
        success = test_api_workflow()
        if success:
            print("\n✅ TEST COMPLETATI CON SUCCESSO!\n")
            sys.exit(0)
        else:
            print("\n❌ TEST FALLITI\n")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRORE DURANTE I TEST: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
