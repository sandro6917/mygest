import requests
import sys

# Login
login_url = "http://localhost:8000/api/v1/auth/login/"
response = requests.post(login_url, json={"username": "admin", "password": "admin"})
if response.status_code != 200:
    print(f"Login fallito: {response.status_code}")
    print(response.text)
    sys.exit(1)

token = response.json().get("access")
print(f"✓ Login riuscito")

# Test scadenze list
headers = {"Authorization": f"Bearer {token}"}
scadenze_url = "http://localhost:8000/api/v1/scadenze/"
response = requests.get(scadenze_url, headers=headers)
print(f"\nGET {scadenze_url}")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Scadenze trovate: {data.get('count', 0)}")
    if data.get('results'):
        print(f"Prima scadenza: {data['results'][0].get('titolo')}")

# Test occorrenze con filtro
occorrenze_url = "http://localhost:8000/api/v1/scadenze/occorrenze/?scadenza=9"
response = requests.get(occorrenze_url, headers=headers)
print(f"\nGET {occorrenze_url}")
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Occorrenze trovate: {data.get('count', 0)}")
else:
    print(f"Errore: {response.text}")
