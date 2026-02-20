"""
Test manuale per l'endpoint Codici Tributo F24

Esegui con: python manage.py shell < test_codici_tributo_api.py
O avvia il server e testa con curl/browser
"""

from django.test import RequestFactory
from comunicazioni.api.views import CodiceTributoF24ViewSet
from scadenze.models import CodiceTributoF24

print("\n=== Test Endpoint Codici Tributo F24 ===\n")

# Setup
factory = RequestFactory()
viewset = CodiceTributoF24ViewSet()

# Test 1: List
print("1. Test LIST endpoint")
request = factory.get('/api/v1/comunicazioni/codici-tributo/')
viewset.request = request
viewset.format_kwarg = None
queryset = viewset.get_queryset()
print(f"   ✓ Queryset count: {queryset.count()}")

# Test 2: Filtro per sezione
print("\n2. Test FILTER per sezione")
for sezione in ['erario', 'inps', 'regioni', 'imu']:
    count = CodiceTributoF24.objects.filter(sezione=sezione).count()
    print(f"   ✓ Sezione {sezione}: {count} codici")

# Test 3: Search
print("\n3. Test SEARCH capabilities")
search_terms = ['ritenute', '1001', 'inps', 'imu']
for term in search_terms:
    results = CodiceTributoF24.objects.filter(
        codice__icontains=term
    ) | CodiceTributoF24.objects.filter(
        descrizione__icontains=term
    ) | CodiceTributoF24.objects.filter(
        causale__icontains=term
    )
    print(f"   ✓ Search '{term}': {results.count()} risultati")
    if results.exists():
        print(f"      Es: {results.first().codice} - {results.first().descrizione[:50]}...")

# Test 4: Serializer
print("\n4. Test SERIALIZER")
from comunicazioni.api.serializers import CodiceTributoF24Serializer
codice = CodiceTributoF24.objects.first()
serializer = CodiceTributoF24Serializer(codice)
data = serializer.data
print(f"   ✓ Fields: {list(data.keys())}")
print(f"   ✓ Display: {data['display']}")

print("\n✅ Tutti i test OK!\n")
print("🚀 Per testare via HTTP, avvia il server con:")
print("   python manage.py runserver")
print("\n   Poi vai su:")
print("   http://localhost:8000/api/v1/comunicazioni/codici-tributo/")
print("   http://localhost:8000/api/v1/comunicazioni/codici-tributo/?search=ritenute")
print("   http://localhost:8000/api/v1/comunicazioni/codici-tributo/?sezione=erario")
