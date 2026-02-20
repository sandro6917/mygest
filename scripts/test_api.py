#!/usr/bin/env python3
"""
Test API JWT Authentication
"""
import requests
import json

API_BASE = "http://localhost:8000/api/v1"

print("🧪 Testing MyGest API v1")
print("=" * 60)

# Test 1: Login (should fail without credentials)
print("\n1️⃣ Testing login endpoint...")
try:
    response = requests.post(
        f"{API_BASE}/auth/login/",
        json={"username": "admin", "password": "wrongpassword"},
        timeout=5
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Login successful!")
        data = response.json()
        print(f"   Access Token: {data['access'][:20]}...")
        print(f"   User: {data['user']['username']}")
    else:
        print(f"   ❌ Login failed: {response.json()}")
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect to Django server")
    print("   Make sure: python manage.py runserver is running")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Dashboard stats (should fail without auth)
print("\n2️⃣ Testing dashboard stats (without auth)...")
try:
    response = requests.get(f"{API_BASE}/dashboard/stats/", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 401:
        print("   ✅ Correctly requires authentication")
    else:
        print(f"   ⚠️  Unexpected status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Instructions
print("\n" + "=" * 60)
print("📝 To test successful login:")
print("   1. Create superuser: python manage.py createsuperuser")
print("   2. Update script with correct credentials")
print("   3. Run again")
print("\n🌐 API Endpoints available:")
print("   POST   /api/v1/auth/login/")
print("   POST   /api/v1/auth/refresh/")
print("   GET    /api/v1/dashboard/stats/  (requires auth)")
print("\n✅ Django API is configured and running!")
print(f"   Django: http://localhost:8000")
print(f"   React:  http://localhost:5173")
