#!/usr/bin/env python
"""
Test End-to-End Codici Tributo F24
Verifica l'intera catena: Model → Serializer → ViewSet → API
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
django.setup()

from django.test import RequestFactory
from comunicazioni.api.views import CodiceTributoF24ViewSet
from comunicazioni.api.serializers import CodiceTributoF24Serializer
from scadenze.models import CodiceTributoF24

def test_model():
    """Test model e database"""
    print("📊 Test Model & Database")
    print("-" * 50)
    
    total = CodiceTributoF24.objects.count()
    attivi = CodiceTributoF24.objects.filter(attivo=True).count()
    
    print(f"✓ Totale codici: {total}")
    print(f"✓ Codici attivi: {attivi}")
    
    # Test per sezione
    sezioni = CodiceTributoF24.objects.values_list('sezione', flat=True).distinct()
    print(f"✓ Sezioni disponibili: {', '.join(sezioni)}")
    
    return total > 0

def test_serializer():
    """Test serializer"""
    print("\n🔧 Test Serializer")
    print("-" * 50)
    
    codice = CodiceTributoF24.objects.first()
    if not codice:
        print("❌ Nessun codice nel DB")
        return False
    
    serializer = CodiceTributoF24Serializer(codice)
    data = serializer.data
    
    print(f"✓ ID: {data['id']}")
    print(f"✓ Codice: {data['codice']}")
    print(f"✓ Sezione: {data['sezione']}")
    print(f"✓ Descrizione: {data['descrizione'][:50]}...")
    print(f"✓ Display: {data['display'][:60]}...")
    print(f"✓ Attivo: {data['attivo']}")
    
    # Verifica tutti i campi richiesti
    required_fields = ['id', 'codice', 'sezione', 'descrizione', 'display', 'attivo']
    for field in required_fields:
        assert field in data, f"Campo {field} mancante"
    
    return True

def test_viewset():
    """Test ViewSet"""
    print("\n🎯 Test ViewSet")
    print("-" * 50)
    
    factory = RequestFactory()
    
    # Test list
    request = factory.get('/api/v1/comunicazioni/codici-tributo/')
    viewset = CodiceTributoF24ViewSet()
    viewset.request = request
    viewset.format_kwarg = None
    
    queryset = viewset.get_queryset()
    print(f"✓ Queryset list: {queryset.count()} elementi")
    
    # Test filterset_fields
    print(f"✓ Filterset fields: {viewset.filterset_fields}")
    
    # Test search_fields
    print(f"✓ Search fields: {viewset.search_fields}")
    
    return queryset.count() > 0

def test_api_search():
    """Test ricerca API"""
    print("\n🔍 Test API Search")
    print("-" * 50)
    
    test_queries = [
        ('ritenute', 'Ricerca per descrizione'),
        ('1001', 'Ricerca per codice'),
        ('inps', 'Ricerca trasversale'),
    ]
    
    for query, descrizione in test_queries:
        results = CodiceTributoF24.objects.filter(
            codice__icontains=query
        ) | CodiceTributoF24.objects.filter(
            descrizione__icontains=query
        ) | CodiceTributoF24.objects.filter(
            causale__icontains=query
        )
        
        print(f"✓ {descrizione} ('{query}'): {results.count()} risultati")
        if results.exists():
            primo = results.first()
            print(f"  → {primo.codice} - {primo.descrizione[:40]}...")
    
    return True

def test_api_filter():
    """Test filtro per sezione"""
    print("\n🏷️  Test API Filter")
    print("-" * 50)
    
    sezioni = ['erario', 'inps', 'regioni', 'imu']
    
    for sezione in sezioni:
        count = CodiceTributoF24.objects.filter(sezione=sezione).count()
        print(f"✓ Sezione '{sezione}': {count} codici")
    
    return True

def test_integration():
    """Test integrazione completa"""
    print("\n🔗 Test Integrazione Template")
    print("-" * 50)
    
    # Verifica che il field_type esista
    from comunicazioni.models_template import TemplateContextField
    field_types = [choice[0] for choice in TemplateContextField.FieldType.choices]
    
    has_codice_tributo = 'codice_tributo' in field_types
    print(f"✓ Field type 'codice_tributo' disponibile: {has_codice_tributo}")
    
    if has_codice_tributo:
        print("✓ Integrazione template OK")
        return True
    else:
        print("❌ Field type mancante")
        return False

def main():
    """Main test runner"""
    print("\n" + "="*50)
    print("🧪 TEST END-TO-END CODICI TRIBUTO F24")
    print("="*50 + "\n")
    
    tests = [
        ("Model & Database", test_model),
        ("Serializer", test_serializer),
        ("ViewSet", test_viewset),
        ("API Search", test_api_search),
        ("API Filter", test_api_filter),
        ("Integrazione Template", test_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Errore in {name}: {e}")
            results.append((name, False))
    
    # Riepilogo
    print("\n" + "="*50)
    print("📋 RIEPILOGO TEST")
    print("="*50)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"\n🎯 Risultato: {passed}/{total} test passati")
    
    if passed == total:
        print("\n✅ TUTTI I TEST OK!")
        print("\n🚀 Per testare via HTTP:")
        print("   python manage.py runserver")
        print("   http://localhost:8000/api/v1/comunicazioni/codici-tributo/")
        return 0
    else:
        print("\n⚠️ Alcuni test falliti")
        return 1

if __name__ == '__main__':
    sys.exit(main())
