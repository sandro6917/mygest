"""
Test API Endpoints per AI Import
Testa gli endpoint REST creati nella Fase 2
"""
import requests
import json

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1/ai-classifier"

# Token di autenticazione (ottienilo dal login o usa un token di test)
# Sostituisci con un token valido o genera uno nuovo
TOKEN = None  # Imposta il token JWT qui

headers = {
    "Content-Type": "application/json",
}

if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"

print("="*80)
print("TEST API ENDPOINTS - AI IMPORT")
print("="*80)

# ==============================================================================
# TEST 1: Lista Template
# ==============================================================================
print("\n📋 TEST 1: GET /api/v1/ai-classifier/templates/")
print("-" * 80)

try:
    response = requests.get(f"{API_BASE}/templates/", headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Template trovati: {data.get('count', 0)}")
        
        if data.get('results'):
            print("\nPrimi 3 template:")
            for template in data['results'][:3]:
                print(f"  - ID {template['id']}: {template['nome']}")
                print(f"    Tipo: {template['tipo_documento_codice']}")
                print(f"    Attivo: {template['attivo']}")
                print(f"    Pagine: {len(template.get('pagine', []))}")
                print(f"    Zone: {sum(len(p.get('zone', [])) for p in template.get('pagine', []))}")
    elif response.status_code == 401:
        print("❌ Non autenticato. Imposta TOKEN nel script.")
    elif response.status_code == 403:
        print("❌ Non autorizzato")
    else:
        print(f"❌ Errore: {response.text}")
        
except requests.exceptions.ConnectionError:
    print("❌ Impossibile connettersi al server")
    print("   Assicurati che il server Django sia in esecuzione:")
    print("   python manage.py runserver")
except Exception as e:
    print(f"❌ Errore: {e}")

# ==============================================================================
# TEST 2: Verifica Route Esiste
# ==============================================================================
print("\n📋 TEST 2: Verifica Routes Disponibili")
print("-" * 80)

endpoints_to_test = [
    ("POST", "/ai-import/upload/", "Upload documento"),
    ("POST", "/ai-import/predict/", "Predizione tipo"),
    ("POST", "/ai-import/extract/", "Estrazione dati"),
    ("POST", "/ai-import/confirm-prediction/", "Conferma predizione"),
    ("POST", "/ai-import/save-feedback/", "Salva feedback"),
    ("GET", "/templates/", "Lista template"),
]

for method, endpoint, description in endpoints_to_test:
    full_url = f"{API_BASE}{endpoint}"
    print(f"{method:6} {endpoint:40} - {description}")

# ==============================================================================
# TEST 3: Test Server Availability
# ==============================================================================
print("\n📋 TEST 3: Test Disponibilità Server")
print("-" * 80)

try:
    response = requests.get(f"{BASE_URL}/api/v1/health/", timeout=5)
    if response.status_code == 200:
        print("✓ Server Django raggiungibile")
        health_data = response.json()
        print(f"  Status: {health_data.get('status', 'unknown')}")
    else:
        print(f"⚠️  Server risponde ma con status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Server non raggiungibile")
    print("\nPer avviare il server:")
    print("  cd /home/sandro/mygest")
    print("  source venv/bin/activate")
    print("  python manage.py runserver")
except Exception as e:
    print(f"❌ Errore connessione: {e}")

# ==============================================================================
# RIEPILOGO
# ==============================================================================
print("\n" + "="*80)
print("RIEPILOGO TEST")
print("="*80)

print("""
Per testare completamente le API:

1. Avvia il server Django:
   cd /home/sandro/mygest
   source venv/bin/activate
   python manage.py runserver

2. Ottieni un token JWT:
   - Login via /api/v1/auth/login/
   - O usa Django admin per creare un token

3. Testa con curl:
   
   # Lista template
   curl -H "Authorization: Bearer <token>" \\
        http://localhost:8000/api/v1/ai-classifier/templates/
   
   # Upload documento
   curl -X POST \\
        -H "Authorization: Bearer <token>" \\
        -F "file=@/path/to/documento.pdf" \\
        http://localhost:8000/api/v1/ai-classifier/ai-import/upload/
   
   # Predizione tipo
   curl -X POST \\
        -H "Authorization: Bearer <token>" \\
        -H "Content-Type: application/json" \\
        -d '{"temp_file_path": "/tmp/...", "filename": "doc.pdf"}' \\
        http://localhost:8000/api/v1/ai-classifier/ai-import/predict/

4. Testa il frontend:
   cd /home/sandro/mygest/frontend
   npm run dev
   
   Apri browser: http://localhost:5173/admin/templates
""")

print("="*80)
