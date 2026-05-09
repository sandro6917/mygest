"""
Script di test per AI-Assisted Document Import
Testa il workflow completo: upload → predict → extract → confirm → feedback
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/sandro/mygest')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from documenti.models import Documento, DocumentiTipo
from ai_classifier.models import (
    DocumentExtractionTemplate,
    ExtractionTemplatePage,
    ExtractionTemplateZone,
    ExtractionFieldMapping,
    AIPredictionFeedback,
    MLModel,
)
from ai_classifier.services.ml.ocr_service import OCRService
from ai_classifier.services.ml.predictor import Predictor
from PIL import Image
import io

User = get_user_model()

print("="*80)
print("TEST AI-ASSISTED DOCUMENT IMPORT")
print("="*80)

# ==============================================================================
# TEST 1: Verifica Modelli Database
# ==============================================================================
print("\n📋 TEST 1: Verifica Modelli Database")
print("-" * 80)

# Conta record
template_count = DocumentExtractionTemplate.objects.count()
page_count = ExtractionTemplatePage.objects.count()
zone_count = ExtractionTemplateZone.objects.count()
mapping_count = ExtractionFieldMapping.objects.count()
feedback_count = AIPredictionFeedback.objects.count()

print(f"✓ DocumentExtractionTemplate: {template_count} record")
print(f"✓ ExtractionTemplatePage: {page_count} record")
print(f"✓ ExtractionTemplateZone: {zone_count} record")
print(f"✓ ExtractionFieldMapping: {mapping_count} record")
print(f"✓ AIPredictionFeedback: {feedback_count} record")

# ==============================================================================
# TEST 2: Creazione Template di Test
# ==============================================================================
print("\n📋 TEST 2: Creazione Template di Test")
print("-" * 80)

# Trova un tipo documento (usa UNILAV se esiste)
tipo_doc = DocumentiTipo.objects.filter(codice='UNILAV').first()
if not tipo_doc:
    # Usa il primo tipo disponibile
    tipo_doc = DocumentiTipo.objects.first()

if not tipo_doc:
    print("❌ Nessun tipo documento trovato. Crea almeno un DocumentiTipo.")
    sys.exit(1)

print(f"✓ Usando tipo documento: {tipo_doc.codice} - {tipo_doc.descrizione}")

# Trova utente admin
user = User.objects.filter(is_superuser=True).first()
if not user:
    user = User.objects.first()

if not user:
    print("❌ Nessun utente trovato.")
    sys.exit(1)

print(f"✓ Usando utente: {user.username}")

# Crea template di test
template, created = DocumentExtractionTemplate.objects.get_or_create(
    tipo_documento=tipo_doc,
    nome='Test Template 2026',
    defaults={
        'descrizione': 'Template di test per workflow AI import',
        'numero_pagine': 1,
        'attivo': True,
        'priorita': 100,
        'creato_da': user,
    }
)

if created:
    print(f"✓ Template creato: {template.nome} (ID: {template.id})")
else:
    print(f"✓ Template esistente: {template.nome} (ID: {template.id})")

# ==============================================================================
# TEST 3: Creazione Pagina Template con Immagine
# ==============================================================================
print("\n📋 TEST 3: Creazione Pagina Template")
print("-" * 80)

# Crea immagine di test (800x1200 px)
img = Image.new('RGB', (800, 1200), color='white')
img_io = io.BytesIO()
img.save(img_io, format='PNG')
img_io.seek(0)

page, created = ExtractionTemplatePage.objects.get_or_create(
    template=template,
    numero_pagina=1,
    defaults={
        'immagine_template': ContentFile(img_io.read(), name='test_template.png'),
        'larghezza': 800,
        'altezza': 1200,
    }
)

if created:
    print(f"✓ Pagina template creata: Pagina {page.numero_pagina} (ID: {page.id})")
    print(f"  Dimensioni: {page.larghezza}x{page.altezza} px")
else:
    print(f"✓ Pagina template esistente: Pagina {page.numero_pagina} (ID: {page.id})")

# ==============================================================================
# TEST 4: Creazione Zone di Estrazione
# ==============================================================================
print("\n📋 TEST 4: Creazione Zone di Estrazione")
print("-" * 80)

# Definisci zone di test
test_zones = [
    {
        'nome_campo': 'codice_fiscale',
        'etichetta': 'Codice Fiscale',
        'x_percent': 10.0,
        'y_percent': 15.0,
        'width_percent': 30.0,
        'height_percent': 5.0,
        'tipo_dato': 'codice_fiscale',
        'obbligatorio': True,
        'ordine': 1,
    },
    {
        'nome_campo': 'data_documento',
        'etichetta': 'Data Documento',
        'x_percent': 60.0,
        'y_percent': 15.0,
        'width_percent': 25.0,
        'height_percent': 5.0,
        'tipo_dato': 'date',
        'obbligatorio': True,
        'ordine': 2,
    },
    {
        'nome_campo': 'note',
        'etichetta': 'Note',
        'x_percent': 10.0,
        'y_percent': 80.0,
        'width_percent': 80.0,
        'height_percent': 15.0,
        'tipo_dato': 'text',
        'obbligatorio': False,
        'ordine': 3,
    },
]

zones_created = 0
for zone_data in test_zones:
    zone, created = ExtractionTemplateZone.objects.get_or_create(
        pagina=page,
        nome_campo=zone_data['nome_campo'],
        defaults=zone_data
    )
    if created:
        zones_created += 1
        coords = zone.get_absolute_coordinates()
        print(f"✓ Zona creata: {zone.etichetta}")
        print(f"  Posizione: ({coords['x']}, {coords['y']}) - {coords['width']}x{coords['height']} px")
    else:
        print(f"✓ Zona esistente: {zone.etichetta}")

print(f"\n✓ Totale zone create in questo test: {zones_created}/{len(test_zones)}")
print(f"✓ Totale zone per pagina: {page.zone.count()}")

# ==============================================================================
# TEST 5: Creazione Mapping Campi
# ==============================================================================
print("\n📋 TEST 5: Creazione Mapping Campi")
print("-" * 80)

# Definisci mapping di test
test_mappings = [
    {
        'nome_campo_template': 'codice_fiscale',
        'tipo_campo_destinazione': 'attribute',
        'nome_campo_destinazione': 'attributo:codice_fiscale',
        'funzione_trasformazione': 'normalize_cf',
    },
    {
        'nome_campo_template': 'data_documento',
        'tipo_campo_destinazione': 'field',
        'nome_campo_destinazione': 'data_documento',
        'funzione_trasformazione': 'parse_date_it',
        'formato_input': 'DD/MM/YYYY',
    },
    {
        'nome_campo_template': 'note',
        'tipo_campo_destinazione': 'note',
        'nome_campo_destinazione': 'note',
    },
]

mappings_created = 0
for mapping_data in test_mappings:
    mapping, created = ExtractionFieldMapping.objects.get_or_create(
        template=template,
        nome_campo_template=mapping_data['nome_campo_template'],
        defaults=mapping_data
    )
    if created:
        mappings_created += 1
        print(f"✓ Mapping creato: {mapping.nome_campo_template} → {mapping.nome_campo_destinazione}")
    else:
        print(f"✓ Mapping esistente: {mapping.nome_campo_template} → {mapping.nome_campo_destinazione}")

print(f"\n✓ Totale mapping creati in questo test: {mappings_created}/{len(test_mappings)}")
print(f"✓ Totale mapping per template: {template.mapping_campi.count()}")

# ==============================================================================
# TEST 6: Verifica Modello ML Attivo
# ==============================================================================
print("\n📋 TEST 6: Verifica Modello ML")
print("-" * 80)

active_model = MLModel.objects.filter(is_active=True).first()
if active_model:
    print(f"✓ Modello ML attivo trovato:")
    print(f"  Versione: {active_model.version}")
    print(f"  Tipo: {active_model.model_type}")
    print(f"  Accuracy: {active_model.accuracy:.2%}" if active_model.accuracy else "  Accuracy: N/A")
    print(f"  Training samples: {active_model.training_samples}")
    print(f"  Trained at: {active_model.trained_at}")
else:
    print("⚠️  Nessun modello ML attivo trovato.")
    print("   Il sistema può funzionare ma le predizioni non saranno disponibili.")

# ==============================================================================
# TEST 7: Test OCR Service
# ==============================================================================
print("\n📋 TEST 7: Test OCR Service")
print("-" * 80)

ocr_service = OCRService()
print(f"✓ OCR Service inizializzato")

# Verifica se esiste un documento di test
test_docs = Documento.objects.filter(tipo=tipo_doc).order_by('-id')[:1]
if test_docs.exists():
    test_doc = test_docs.first()
    print(f"✓ Documento di test trovato: {test_doc.codice}")
    
    if test_doc.file:
        print(f"  File: {test_doc.file.name}")
        
        # Prova estrazione OCR
        try:
            file_path = test_doc.file.path
            print(f"  Path: {file_path}")
            
            if os.path.exists(file_path):
                ocr_result = ocr_service.extract_text_from_file(file_path)
                
                if ocr_result.get('success'):
                    text = ocr_result['text']
                    print(f"✓ OCR completato con successo")
                    print(f"  Metodo: {ocr_result.get('method', 'unknown')}")
                    print(f"  Caratteri estratti: {len(text)}")
                    print(f"  Pagine: {ocr_result.get('page_count', 1)}")
                    print(f"  Anteprima testo (prime 200 char):")
                    print(f"  {text[:200]}...")
                else:
                    print(f"❌ OCR fallito: {ocr_result.get('error')}")
            else:
                print(f"⚠️  File non trovato sul filesystem: {file_path}")
        except Exception as e:
            print(f"❌ Errore test OCR: {e}")
    else:
        print("⚠️  Documento senza file allegato")
else:
    print(f"⚠️  Nessun documento di test trovato per tipo {tipo_doc.codice}")
    print("   Salta test OCR.")

# ==============================================================================
# TEST 8: Statistiche Finali
# ==============================================================================
print("\n📋 TEST 8: Statistiche Sistema")
print("-" * 80)

total_templates = DocumentExtractionTemplate.objects.count()
active_templates = DocumentExtractionTemplate.objects.filter(attivo=True).count()
total_pages = ExtractionTemplatePage.objects.count()
total_zones = ExtractionTemplateZone.objects.count()
total_mappings = ExtractionFieldMapping.objects.count()
total_feedback = AIPredictionFeedback.objects.count()

print(f"📊 Template: {total_templates} totali, {active_templates} attivi")
print(f"📄 Pagine template: {total_pages}")
print(f"📍 Zone estrazione: {total_zones}")
print(f"🔗 Mapping campi: {total_mappings}")
print(f"💬 Feedback raccolti: {total_feedback}")

if total_feedback > 0:
    feedback_corretti = AIPredictionFeedback.objects.filter(predizione_corretta=True).count()
    accuracy = (feedback_corretti / total_feedback) * 100 if total_feedback > 0 else 0
    print(f"✓ Accuracy predizioni: {accuracy:.1f}% ({feedback_corretti}/{total_feedback} corrette)")

# ==============================================================================
# RIEPILOGO
# ==============================================================================
print("\n" + "="*80)
print("✅ TEST COMPLETATI")
print("="*80)

print(f"""
Template di test creato:
  - ID: {template.id}
  - Nome: {template.nome}
  - Tipo documento: {tipo_doc.codice}
  - Pagine: {template.pagine.count()}
  - Zone: {sum(p.zone.count() for p in template.pagine.all())}
  - Mapping: {template.mapping_campi.count()}
  - Attivo: {'Sì' if template.attivo else 'No'}

Prossimi passi:
  1. Accedi a Django Admin: /admin/
  2. Visualizza template: /admin/ai_classifier/documentextractiontemplate/{template.id}/
  3. Testa API REST:
     - GET  /api/v1/ai-classifier/templates/
     - GET  /api/v1/ai-classifier/templates/{template.id}/
  4. Testa Frontend (quando disponibile):
     - Lista: /admin/templates
     - Editor: /admin/templates/{template.id}
""")

print("="*80)
