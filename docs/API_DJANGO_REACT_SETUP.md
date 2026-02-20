# ✅ API REST Django + React SPA - Setup Completato!

## 🎉 Risultato

**Backend Django e Frontend React configurati e funzionanti!**

### Servers Attivi

- 🐍 **Django API**: http://localhost:8000/api/v1/
- ⚛️ **React SPA**: http://localhost:5173/

---

## 📋 Cosa è Stato Implementato

### 1. Django Backend Configuration

#### Dipendenze Installate
```bash
✅ django-cors-headers (4.4.0)
✅ djangorestframework-simplejwt (5.5.1)
✅ djangorestframework (3.15.2) - già presente
```

#### Settings.py Modifiche

**INSTALLED_APPS aggiornate:**
```python
INSTALLED_APPS = [
    # ... apps esistenti
    'rest_framework',
    'rest_framework_simplejwt',  # ✨ NUOVO
    'corsheaders',                # ✨ NUOVO
    # ... altre apps
]
```

**MIDDLEWARE aggiornato:**
```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # ✨ NUOVO - Prima di tutto!
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... altri middleware
]
```

**CORS Configuration:**
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

CORS_ALLOW_CREDENTIALS = True
```

**JWT Configuration:**
```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

**REST_FRAMEWORK Authentication:**
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",  # ✨ JWT First!
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    # ... altre configurazioni
}
```

### 2. API Structure Creata

```
api/
├── __init__.py
└── v1/
    ├── __init__.py
    ├── urls.py                    # Main API router
    └── auth/
        ├── __init__.py
        ├── views.py               # CustomTokenObtainPairView
        └── urls.py                # Auth endpoints
```

### 3. API Endpoints Disponibili

#### Authentication

**POST /api/v1/auth/login/**
```json
Request:
{
  "username": "admin",
  "password": "password123"
}

Response (200):
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "is_staff": true
  }
}
```

**POST /api/v1/auth/refresh/**
```json
Request:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response (200):
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Dashboard

**GET /api/v1/dashboard/stats/**  
Requires: `Authorization: Bearer <access_token>`

```json
Response (200):
{
  "pratiche_attive": 42,
  "pratiche_chiuse": 128,
  "documenti_count": 356,
  "scadenze_oggi": 3,
  "pratiche_per_mese": [
    {"mese": "Gen", "count": 15},
    {"mese": "Feb", "count": 22},
    ...
  ]
}
```

---

## 🔧 Frontend React - Integrazione

### Axios Client (già configurato)

```typescript
// src/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  withCredentials: true,
});

// Auto-inject JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try refresh token
      const refreshToken = localStorage.getItem('refresh_token');
      const response = await axios.post('/auth/refresh/', {
        refresh: refreshToken,
      });
      localStorage.setItem('access_token', response.data.access);
      // Retry original request
      return apiClient(error.config);
    }
  }
);
```

### Auth Store (già configurato)

```typescript
// src/store/authStore.ts
export const useAuthStore = create()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      
      login: async (credentials) => {
        const response = await apiClient.post('/auth/login/', credentials);
        const { access, refresh, user } = response.data;
        
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        
        set({ user, isAuthenticated: true });
      },
      
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, isAuthenticated: false });
      },
    }),
    { name: 'auth-storage' }
  )
);
```

---

## 🧪 Testing

### Test con cURL

**1. Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}'
```

**2. Dashboard Stats (with token):**
```bash
TOKEN="your_access_token_here"

curl -X GET http://localhost:8000/api/v1/dashboard/stats/ \
  -H "Authorization: Bearer $TOKEN"
```

### Test con Python Script

```bash
python scripts/test_api.py
```

### Test nel Browser

1. Vai su http://localhost:5173/
2. Prova il login
3. Verifica il token in localStorage
4. Naviga alla dashboard

---

## 📊 Status Implementazione

### ✅ Completato

- [x] Django CORS configurato
- [x] JWT authentication setup
- [x] API v1 structure
- [x] Login endpoint (`/api/v1/auth/login/`)
- [x] Refresh token endpoint (`/api/v1/auth/refresh/`)
- [x] Dashboard stats endpoint
- [x] Custom serializer con user data
- [x] React Axios client con interceptors
- [x] React Auth store (Zustand)
- [x] Protected routes React
- [x] Login page React

### ⏳ TODO - Next Steps

#### 1. Creare più API Endpoints

```python
# api/v1/pratiche/
class PraticaViewSet(viewsets.ModelViewSet):
    queryset = Pratica.objects.all()
    serializer_class = PraticaSerializer
    permission_classes = [IsAuthenticated]
```

#### 2. Integrare TanStack Query in React

```typescript
// hooks/useDashboardStats.ts
import { useQuery } from '@tanstack/react-query';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.get('/dashboard/stats/'),
  });
}

// In DashboardPage.tsx
const { data, isLoading } = useDashboardStats();
```

#### 3. Creare Pagine React per Moduli

- [ ] Pratiche (lista, create, edit, detail)
- [ ] Documenti (upload, lista, preview)
- [ ] Anagrafiche (CRUD)
- [ ] Scadenze (calendario)

#### 4. WebSocket Real-time

```bash
pip install channels channels-redis
```

```python
# Install Redis
# Configure Django Channels
# Create consumers for real-time updates
```

#### 5. PWA Configuration

```typescript
// vite.config.ts - Add PWA plugin
import { VitePWA } from 'vite-plugin-pwa';
```

---

## 🐛 Troubleshooting

### CORS Error

**Problema**: `Access to XMLHttpRequest blocked by CORS policy`

**Soluzione**: Verifica `CORS_ALLOWED_ORIGINS` in settings.py include l'origin React

### 401 Unauthorized

**Problema**: API ritorna 401 anche con token

**Soluzione**: 
1. Verifica token in localStorage
2. Controlla header Authorization
3. Verifica token non sia scaduto

### Cannot Connect to Server

**Problema**: `Connection refused`

**Soluzione**:
```bash
# Verifica server Django
python manage.py runserver

# Verifica server React
cd frontend && npm run dev
```

---

## 📚 Documentazione API

### Swagger/OpenAPI (TODO)

Installare per docs automatiche:
```bash
pip install drf-spectacular
```

```python
# settings.py
INSTALLED_APPS += ['drf_spectacular']

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

URL docs: http://localhost:8000/api/schema/swagger-ui/

---

## 🚀 Comandi Utili

### Backend

```bash
# Avvia Django
python manage.py runserver

# Crea superuser
python manage.py createsuperuser

# Migrations
python manage.py makemigrations
python manage.py migrate

# Test API
python scripts/test_api.py
```

### Frontend

```bash
# Avvia React
cd frontend
npm run dev

# Build production
npm run build

# Preview build
npm run preview
```

### Entrambi

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: React
cd frontend && npm run dev
```

---

## ✨ Summary

🎉 **Setup completato con successo!**

### Architettura

```
┌─────────────────────────────────────┐
│   React SPA (localhost:5173)        │
│   - TypeScript                       │
│   - React Router                     │
│   - Zustand (auth)                   │
│   - Axios + Interceptors             │
└──────────────┬──────────────────────┘
               │ HTTP/JWT
               ↓
┌─────────────────────────────────────┐
│   Django API (localhost:8000)        │
│   - REST Framework                   │
│   - JWT Authentication               │
│   - CORS enabled                     │
│   - /api/v1/ endpoints               │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   PostgreSQL Database                │
└─────────────────────────────────────┘
```

### Prossimo Step

1. ✅ Testare login da React UI
2. ⏳ Implementare dashboard con dati reali
3. ⏳ Creare API per Pratiche
4. ⏳ Creare pagine React per moduli
5. ⏳ Implementare WebSocket
6. ⏳ Configurare PWA

**Tutto pronto per sviluppo full-stack!** 🚀

---

**Data**: 17 Novembre 2025  
**Versione**: 1.0  
**Status**: ✅ Production Ready (Dev Environment)
