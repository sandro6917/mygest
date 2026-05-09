# JWT Authentication Security - MyGest

**Data**: 3 Marzo 2026  
**Feature**: JWT Authentication Hardening  
**Status**: ✅ **COMPLETATO E TESTATO**

---

## ✅ Obiettivo

Rafforzare l'autenticazione JWT di MyGest con best practice DRF:
- ✅ Token blacklist per invalidazione logout
- ✅ Refresh token rotation automatica
- ✅ Scadenze differenziate production/development
- ✅ Endpoint logout che invalida token
- ✅ Frontend compatibile con rotation e logout

---

## 📋 Architettura Autenticazione

### Stack Tecnologico

- **Backend**: Django REST Framework + `djangorestframework-simplejwt` 5.5.1
- **Frontend**: React 19 + TypeScript + Axios
- **Token Storage**: localStorage (access_token, refresh_token)
- **Blacklist**: Database PostgreSQL (tabelle `token_blacklist_outstandingtoken` e `token_blacklist_blacklistedtoken`)

### Flow Autenticazione

```
┌─────────────┐                  ┌─────────────┐                  ┌──────────────┐
│   Browser   │                  │  Django API │                  │  PostgreSQL  │
│   (React)   │                  │    (DRF)    │                  │  (Blacklist) │
└─────────────┘                  └─────────────┘                  └──────────────┘
       │                                │                                 │
       │  1. POST /auth/login/          │                                 │
       │  {username, password}          │                                 │
       ├───────────────────────────────>│                                 │
       │                                │                                 │
       │  2. Validate credentials       │                                 │
       │     + Generate tokens          │                                 │
       │                                │  3. Store OutstandingToken      │
       │                                ├────────────────────────────────>│
       │                                │                                 │
       │  4. {access, refresh, user}    │                                 │
       │<───────────────────────────────┤                                 │
       │                                │                                 │
       │  5. Store in localStorage      │                                 │
       │     access_token = "eyJ..."    │                                 │
       │     refresh_token = "eyJ..."   │                                 │
       │                                │                                 │
       │  6. API calls con              │                                 │
       │     Authorization: Bearer      │                                 │
       ├───────────────────────────────>│                                 │
       │                                │                                 │
       │  7. Validate JWT signature     │                                 │
       │                                │  8. Check blacklist             │
       │                                ├────────────────────────────────>│
       │                                │<────────────────────────────────┤
       │                                │  "Not blacklisted"              │
       │                                │                                 │
       │  9. Response data              │                                 │
       │<───────────────────────────────┤                                 │
       │                                │                                 │
       │ 10. Access scaduto (401)       │                                 │
       │<───────────────────────────────┤                                 │
       │                                │                                 │
       │ 11. POST /auth/refresh/        │                                 │
       │     {refresh: "eyJ..."}        │                                 │
       ├───────────────────────────────>│                                 │
       │                                │                                 │
       │                                │ 12. Check blacklist refresh     │
       │                                ├────────────────────────────────>│
       │                                │<────────────────────────────────┤
       │                                │  "Not blacklisted"              │
       │                                │                                 │
       │                                │ 13. Blacklist old refresh       │
       │                                ├────────────────────────────────>│
       │                                │                                 │
       │                                │ 14. Create new refresh token    │
       │                                ├────────────────────────────────>│
       │                                │  Store OutstandingToken         │
       │                                │                                 │
       │ 15. {access, refresh (new)}    │                                 │
       │<───────────────────────────────┤                                 │
       │                                │                                 │
       │ 16. Update localStorage        │                                 │
       │                                │                                 │
       │ 17. POST /auth/logout/         │                                 │
       │     {refresh: "eyJ..."}        │                                 │
       ├───────────────────────────────>│                                 │
       │                                │                                 │
       │                                │ 18. Blacklist refresh token     │
       │                                ├────────────────────────────────>│
       │                                │  INSERT BlacklistedToken        │
       │                                │                                 │
       │ 19. {detail: "Logout success"} │                                 │
       │<───────────────────────────────┤                                 │
       │                                │                                 │
       │ 20. Clear localStorage         │                                 │
       │     Remove access_token        │                                 │
       │     Remove refresh_token       │                                 │
       │                                │                                 │
```

---

## 🔧 Configurazione JWT

### Base Settings (mygest/settings/base.py)

```python
# JWT AUTHENTICATION
SIMPLE_JWT = {
    # Token lifetimes (overridati in prod/dev)
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),      # Default
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # Default
    
    # Rotation & Blacklist
    'ROTATE_REFRESH_TOKENS': True,                    # ✅ Rotation abilitata
    'BLACKLIST_AFTER_ROTATION': True,                 # ✅ Blacklist abilitata
    'UPDATE_LAST_LOGIN': True,                        # Aggiorna last_login al login
    
    # Algorithm
    'ALGORITHM': 'HS256',                             # HMAC SHA-256
    'SIGNING_KEY': SECRET_KEY,                        # Usa SECRET_KEY Django
    'VERIFYING_KEY': None,                            # Non usato con HS256
    'AUDIENCE': None,                                 # Opzionale
    'ISSUER': None,                                   # Opzionale
    
    # Headers
    'AUTH_HEADER_TYPES': ('Bearer',),                # Authorization: Bearer <token>
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Claims
    'USER_ID_FIELD': 'id',                           # Campo User.id
    'USER_ID_CLAIM': 'user_id',                      # Claim JWT user_id
    'TOKEN_TYPE_CLAIM': 'token_type',                # Claim tipo token
    'JTI_CLAIM': 'jti',                              # JWT ID (per blacklist)
    
    # Token classes
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}
```

### Production Settings (mygest/settings/production.py)

```python
# JWT AUTHENTICATION - PRODUCTION (STRINGENT)

# Scadenze più stringenti per produzione
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(minutes=15)  # 15 minuti
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=1)     # 1 giorno

print(f"✓ JWT: Access 15min, Refresh 1day, Blacklist ENABLED")
```

**Rationale Production**:
- **Access 15 minuti**: Finestra minima esposizione se token rubato
- **Refresh 1 giorno**: Forza re-login quotidiano, riduce rischio refresh token compromesso
- **Blacklist**: Token invalidati immediatamente al logout

### Development Settings (mygest/settings/development.py)

```python
# JWT AUTHENTICATION - DEVELOPMENT (EXTENDED)

# Scadenze più lunghe per comodità in sviluppo
SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'] = timedelta(hours=24)   # 24 ore
SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'] = timedelta(days=30)   # 30 giorni

print(f"✓ JWT: Access 24h, Refresh 30d, Blacklist ENABLED (dev mode)")
```

**Rationale Development**:
- **Access 24 ore**: Evita refresh continui durante sviluppo
- **Refresh 30 giorni**: Re-login mensile (comodità sviluppatori)
- **Blacklist**: Testata anche in dev per verificare funzionamento

---

## 🔐 Token Blacklist Implementation

### Database Schema

**Tabelle create da `djangorestframework-simplejwt.token_blacklist`**:

```sql
-- Token refresh emessi (outstanding = "in circolazione")
CREATE TABLE token_blacklist_outstandingtoken (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES auth_user(id),
    jti VARCHAR(255) UNIQUE NOT NULL,        -- JWT ID univoco
    token TEXT NOT NULL,                      -- Token completo
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

-- Token refresh blacklistati (invalidati)
CREATE TABLE token_blacklist_blacklistedtoken (
    id BIGSERIAL PRIMARY KEY,
    token_id BIGINT UNIQUE NOT NULL REFERENCES token_blacklist_outstandingtoken(id),
    blacklisted_at TIMESTAMP NOT NULL
);
```

### Come funziona

1. **Login**: `OutstandingToken` creato con refresh token JTI
2. **Refresh**: Vecchio refresh blacklistato, nuovo `OutstandingToken` creato
3. **Logout**: Refresh token aggiunto a `BlacklistedToken`
4. **Validazione**: JWT middleware controlla se JTI in blacklist

### Configurazione

```python
# mygest/settings/base.py

INSTALLED_APPS = [
    # ...
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # ✅ App blacklist
    # ...
]
```

### Migrations

```bash
# Auto-create migrations (già incluse in djangorestframework-simplejwt)
python manage.py migrate token_blacklist

# Output:
# Running migrations:
#   Applying token_blacklist.0001_initial... OK
#   Applying token_blacklist.0002_outstandingtoken_jti_hex... OK
#   Applying token_blacklist.0003_auto_20171017_2007... OK
```

---

## 📡 API Endpoints

### 1. Login (POST /api/v1/auth/login/)

**Request**:
```http
POST /api/v1/auth/login/ HTTP/1.1
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**Response (200 OK)**:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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

**Response (401 Unauthorized)**:
```json
{
  "detail": "No active account found with the given credentials"
}
```

**Custom Serializer**:
```python
# api/v1/auth/views.py

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Include user data in response"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_staff': self.user.is_staff,
        }
        
        return data
```

---

### 2. Refresh Token (POST /api/v1/auth/refresh/)

**Request**:
```http
POST /api/v1/auth/refresh/ HTTP/1.1
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK)** - Con rotation:
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  // Nuovo access
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // Nuovo refresh
}
```

**Response (401 Unauthorized)** - Token blacklistato:
```json
{
  "detail": "Token is blacklisted",
  "code": "token_not_valid"
}
```

**Behavior**:
- `ROTATE_REFRESH_TOKENS=True`: Ritorna nuovo refresh token
- `BLACKLIST_AFTER_ROTATION=True`: Vecchio refresh blacklistato automaticamente
- Frontend DEVE aggiornare entrambi i token in localStorage

---

### 3. Logout (POST /api/v1/auth/logout/) ✨ NEW

**Request**:
```http
POST /api/v1/auth/logout/ HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK)**:
```json
{
  "detail": "Logout effettuato con successo"
}
```

**Response (400 Bad Request)** - Token mancante:
```json
{
  "error": "Refresh token richiesto"
}
```

**Response (400 Bad Request)** - Token non valido:
```json
{
  "error": "Token non valido: Token is invalid or expired"
}
```

**Implementation**:
```python
# api/v1/auth/views.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Blacklist refresh token on logout"""
    try:
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token richiesto'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Blacklist token
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        return Response(
            {'detail': 'Logout effettuato con successo'},
            status=status.HTTP_200_OK
        )
        
    except TokenError as e:
        return Response(
            {'error': f'Token non valido: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
```

---

### 4. CSRF Token (GET /api/v1/auth/csrf/)

**Request**:
```http
GET /api/v1/auth/csrf/ HTTP/1.1
```

**Response (200 OK)**:
```json
{
  "detail": "CSRF cookie set"
}
```

**Headers**:
```http
Set-Cookie: csrftoken=abc123...; Path=/; SameSite=Lax
```

**Uso**: Frontend SPA chiama questo endpoint all'avvio per ottenere CSRF cookie.

---

## 🎨 Frontend Integration (React + TypeScript)

### Auth Store (Zustand)

```typescript
// frontend/src/store/authStore.ts

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Login action
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });

        try {
          const response = await apiClient.post<AuthResponse>(
            '/auth/login/', 
            credentials
          );
          
          const { access, refresh, user } = response.data;

          // Store tokens
          localStorage.setItem('access_token', access);
          localStorage.setItem('refresh_token', refresh);

          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: unknown) {
          const errorMessage = extractAuthError(error);
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
          });
          throw error;
        }
      },

      // Logout action (UPDATED)
      logout: async () => {
        const { refreshToken } = get();
        
        // Try to invalidate token on backend
        if (refreshToken) {
          try {
            await apiClient.post('/auth/logout/', { refresh: refreshToken });
          } catch (error) {
            // Logout locally even if backend fails
            console.warn('Backend logout failed, clearing local tokens:', error);
          }
        }
        
        // Clear local storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');

        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        });
      },

      // Refresh access token (UPDATED for rotation)
      refreshAccessToken: async () => {
        const { refreshToken } = get();

        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        try {
          const response = await apiClient.post<{ 
            access: string; 
            refresh?: string  // Nuovo refresh se rotation abilitata
          }>('/auth/refresh/', {
            refresh: refreshToken,
          });

          const { access, refresh: newRefresh } = response.data;
          localStorage.setItem('access_token', access);
          
          // Se rotation abilitata, aggiorna anche refresh token
          if (newRefresh) {
            localStorage.setItem('refresh_token', newRefresh);
            set({ accessToken: access, refreshToken: newRefresh });
          } else {
            set({ accessToken: access });
          }
        } catch (error: unknown) {
          // Refresh failed, logout user
          await get().logout();
          throw error;
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
```

---

### API Client (Axios Interceptors)

```typescript
// frontend/src/api/client.ts

import axios from 'axios';
import { API_BASE_URL } from '@/config';

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true,
});

// Request interceptor - Add JWT token
apiClient.interceptors.request.use(
  (config) => {
    // Add JWT token
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add CSRF token for non-GET requests
    if (config.method && ['post', 'put', 'patch', 'delete'].includes(config.method)) {
      const csrfToken = getCookie('csrftoken');
      if (csrfToken && config.headers) {
        config.headers['X-CSRFToken'] = csrfToken;
      }
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - Handle 401 and refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retried
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        // Attempt to refresh token
        const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
          refresh: refreshToken,
        });

        const { access, refresh: newRefresh } = response.data;
        localStorage.setItem('access_token', access);
        
        // Update refresh token if rotation enabled
        if (newRefresh) {
          localStorage.setItem('refresh_token', newRefresh);
        }

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // Refresh failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
```

---

### Login Component

```typescript
// frontend/src/pages/LoginPage.tsx

export function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading, error } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login({ username, password });
      navigate('/');  // Redirect to dashboard
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
        disabled={isLoading}
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
        disabled={isLoading}
      />
      {error && <div className="error">{error}</div>}
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

---

### Logout Component

```typescript
// frontend/src/components/layout/Navbar.tsx

export function Navbar() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuthStore();

  const handleLogout = async () => {
    await logout();  // Chiama backend /auth/logout/ + clear localStorage
    navigate('/login');
  };

  return (
    <nav>
      {isAuthenticated && (
        <>
          <span>Welcome, {user?.first_name || user?.username}</span>
          <button onClick={handleLogout}>Logout</button>
        </>
      )}
    </nav>
  );
}
```

---

## 🧪 Testing

### Test 1: Development JWT Config ✅

```bash
$ DJANGO_ENV=development python manage.py shell

>>> from django.conf import settings
>>> settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
datetime.timedelta(days=1)  # 24 ore

>>> settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
datetime.timedelta(days=30)  # 30 giorni

>>> settings.SIMPLE_JWT['BLACKLIST_AFTER_ROTATION']
True  # ✓ Abilitata
```

---

### Test 2: Production JWT Config ✅

```bash
$ DJANGO_ENV=production python manage.py shell

>>> from django.conf import settings
>>> settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
datetime.timedelta(seconds=900)  # 15 minuti

>>> settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']
datetime.timedelta(days=1)  # 1 giorno

>>> settings.SIMPLE_JWT['BLACKLIST_AFTER_ROTATION']
True  # ✓ Abilitata
```

---

### Test 3: Login + Token Generation

```bash
$ curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# Response:
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzA5NjU...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTcwO...",
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

**Verifica Database**:
```sql
SELECT * FROM token_blacklist_outstandingtoken 
WHERE user_id = 1 
ORDER BY created_at DESC 
LIMIT 1;

-- Output:
-- id | user_id | jti                              | token        | created_at           | expires_at
-- 1  | 1       | abc123...                        | eyJhbGci...  | 2026-03-03 10:00:00 | 2026-03-04 10:00:00
```

---

### Test 4: Refresh Token Rotation

```bash
# 1. Login
$ ACCESS=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access')

$ REFRESH=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.refresh')

# 2. Refresh token
$ curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"

# Response:
{
  "access": "eyJ...(nuovo access)...",
  "refresh": "eyJ...(nuovo refresh)..."  # ← Rotation!
}
```

**Verifica Blacklist**:
```sql
-- Vecchio refresh ora blacklistato
SELECT COUNT(*) FROM token_blacklist_blacklistedtoken;
-- 1

SELECT bt.blacklisted_at, ot.jti 
FROM token_blacklist_blacklistedtoken bt
JOIN token_blacklist_outstandingtoken ot ON bt.token_id = ot.id;

-- blacklisted_at        | jti
-- 2026-03-03 10:05:00  | abc123... (vecchio JTI)
```

---

### Test 5: Logout Token Blacklist

```bash
$ curl -X POST http://localhost:8000/api/v1/auth/logout/ \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"

# Response:
{
  "detail": "Logout effettuato con successo"
}

# Verifica token blacklistato
$ curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d "{\"refresh\":\"$REFRESH\"}"

# Response (401):
{
  "detail": "Token is blacklisted",
  "code": "token_not_valid"
}
```

---

### Test 6: Frontend Login Flow

**Console DevTools**:
```javascript
// 1. Login
const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin' })
});

const { access, refresh, user } = await response.json();

// Store tokens
localStorage.setItem('access_token', access);
localStorage.setItem('refresh_token', refresh);

console.log('User:', user);
// User: {id: 1, username: 'admin', email: 'admin@example.com', ...}

// 2. API call con token
const apiResponse = await fetch('http://localhost:8000/api/v1/anagrafiche/', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});

console.log('API Response:', await apiResponse.json());
// API Response: {count: 150, results: [...]}

// 3. Logout
await fetch('http://localhost:8000/api/v1/auth/logout/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ refresh: localStorage.getItem('refresh_token') })
});

localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

---

## 🔒 Security Best Practices

### ✅ Implemented

1. **Token Rotation**: Refresh token cambia ad ogni refresh → limita window riutilizzo se rubato
2. **Blacklist**: Token invalidati immediatamente al logout → no riutilizzo
3. **Short Access Lifetime (Prod)**: 15 minuti → riduce esposizione se token intercettato
4. **HttpOnly Cookies (Sessions)**: `SESSION_COOKIE_HTTPONLY=True` → XSS non può rubare session
5. **Secure Cookies (Prod)**: `SESSION_COOKIE_SECURE=True` → solo HTTPS
6. **HTTPS Enforcement (Prod)**: `SECURE_SSL_REDIRECT=True` → forza TLS
7. **CSRF Protection**: `X-CSRFToken` header + `csrftoken` cookie
8. **Algorithm HS256**: HMAC-SHA256 → performance + sicurezza bilanciata

---

### 🚧 Recommended (Future Enhancements)

#### 1. Rate Limiting Login

**Problem**: Brute force attacks su `/auth/login/`

**Solution**: `django-ratelimit` o `djangorestframework.throttling`

```python
# mygest/settings/production.py

REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
]
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10/hour',   # Max 10 login attempts/hour per IP
    'user': '1000/hour',
}

# Custom throttle per login endpoint
from rest_framework.throttling import AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    rate = '5/minute'  # Max 5 tentativi login al minuto

# api/v1/auth/views.py
class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]
```

---

#### 2. Multi-Factor Authentication (MFA/2FA)

**Solution**: `django-otp` + `djangorestframework-simplejwt` custom claims

```python
# pip install django-otp qrcode

# mygest/settings/base.py
INSTALLED_APPS += [
    'django_otp',
    'django_otp.plugins.otp_totp',
]

MIDDLEWARE += [
    'django_otp.middleware.OTPMiddleware',
]

# api/v1/auth/views.py
from django_otp import match_token

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    otp_token = serializers.CharField(required=False)
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Richiedi OTP se user ha 2FA abilitato
        if self.user.totpdevice_set.exists():
            otp_token = attrs.get('otp_token')
            if not otp_token or not match_token(self.user, otp_token):
                raise serializers.ValidationError("Invalid OTP token")
        
        return data
```

---

#### 3. Device/Session Fingerprinting

**Problem**: Token rubato usato da device/IP diverso

**Solution**: Salvare fingerprint in `OutstandingToken` e validare

```python
# Esempio: IP + User-Agent hash
import hashlib

def get_device_fingerprint(request):
    ip = request.META.get('REMOTE_ADDR')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    return hashlib.sha256(f"{ip}:{user_agent}".encode()).hexdigest()

# Salvare in OutstandingToken.token_metadata (custom field)
# Validare ad ogni richiesta se fingerprint match
```

---

#### 4. Token Introspection Endpoint

**Use Case**: Debugging, monitoring token attivi per user

```python
# api/v1/auth/views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_tokens(request):
    """List active tokens for current user"""
    from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
    
    tokens = OutstandingToken.objects.filter(
        user=request.user
    ).exclude(
        blacklistedtoken__isnull=False  # Escludi blacklistati
    ).values('jti', 'created_at', 'expires_at')
    
    return Response({'active_tokens': list(tokens)})
```

---

#### 5. Revoca Token Admin

**Admin Action**: Blacklist manuale token da Django Admin

```python
# api/v1/auth/admin.py

from django.contrib import admin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

@admin.register(OutstandingToken)
class OutstandingTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'jti', 'created_at', 'expires_at', 'is_blacklisted']
    list_filter = ['user', 'created_at']
    search_fields = ['user__username', 'jti']
    actions = ['blacklist_tokens']
    
    def is_blacklisted(self, obj):
        return hasattr(obj, 'blacklistedtoken')
    is_blacklisted.boolean = True
    
    @admin.action(description='Blacklist selected tokens')
    def blacklist_tokens(self, request, queryset):
        for token in queryset:
            if not hasattr(token, 'blacklistedtoken'):
                BlacklistedToken.objects.create(token=token)
        self.message_user(request, f'{queryset.count()} tokens blacklisted')
```

---

## 📊 Monitoring & Maintenance

### Database Growth

**Problem**: `OutstandingToken` cresce indefinitamente

**Solution**: Cleanup job periodico

```bash
# Cron job quotidiano (elimina token scaduti > 7 giorni fa)
0 3 * * * cd /srv/mygest/app && source venv/bin/activate && python manage.py flushexpiredtokens >> /var/log/mygest/token_cleanup.log 2>&1
```

**Django command** (già incluso in `djangorestframework-simplejwt`):
```bash
$ python manage.py flushexpiredtokens

# Output:
# Tokens deleted: 1532
```

---

### Metrics da Monitorare

1. **Login Failures Rate**: Alert se > 50/min (possibile brute force)
2. **Token Refresh Rate**: Baseline normale, alert se spike anomalo
3. **Blacklisted Tokens Count**: Trend crescita (logout frequency)
4. **Outstanding Tokens per User**: Alert se user ha > 10 token attivi (possibile leak)

**Esempio Prometheus Metrics**:
```python
# metrics.py (con django-prometheus)

from prometheus_client import Counter, Histogram

login_attempts = Counter('mygest_login_attempts_total', 'Total login attempts', ['status'])
token_refresh = Counter('mygest_token_refresh_total', 'Total token refreshes')
token_blacklist = Counter('mygest_token_blacklist_total', 'Total tokens blacklisted')

# In views:
login_attempts.labels(status='success').inc()
token_refresh.inc()
token_blacklist.inc()
```

---

## 🚀 Deployment Checklist

### Pre-Deploy

- [x] JWT app configurata (`rest_framework_simplejwt.token_blacklist` in INSTALLED_APPS)
- [x] Migrations applicate (`python manage.py migrate token_blacklist`)
- [x] Production settings (ACCESS 15min, REFRESH 1day)
- [x] Development settings (ACCESS 24h, REFRESH 30d)
- [x] Logout endpoint implementato (`/api/v1/auth/logout/`)
- [x] Frontend aggiornato (logout chiama backend, rotation support)
- [ ] Rate limiting login configurato (TODO)
- [ ] Cron job cleanup token configurato

---

### Deploy

```bash
# VPS Production
ssh mygest@72.62.34.249
cd /srv/mygest/app
source venv/bin/activate

# 1. Pull latest code
git pull origin main

# 2. Migrate database (token_blacklist tables)
DJANGO_ENV=production python manage.py migrate

# 3. Test JWT config
DJANGO_ENV=production python manage.py shell -c \
  "from django.conf import settings; \
   print(f'Access: {settings.SIMPLE_JWT[\"ACCESS_TOKEN_LIFETIME\"]}'); \
   print(f'Refresh: {settings.SIMPLE_JWT[\"REFRESH_TOKEN_LIFETIME\"]}'); \
   print(f'Blacklist: {settings.SIMPLE_JWT[\"BLACKLIST_AFTER_ROTATION\"]}')"

# Output atteso:
# Access: 0:15:00
# Refresh: 1 day, 0:00:00
# Blacklist: True

# 4. Restart Gunicorn
sudo systemctl restart mygest

# 5. Test login API
curl -X POST https://mygest.example.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<password>"}' | jq

# 6. Test logout API
# (usa access/refresh token dal login)
curl -X POST https://mygest.example.com/api/v1/auth/logout/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}' | jq

# 7. Verify token blacklisted
curl -X POST https://mygest.example.com/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"<refresh_token>"}' | jq

# Expect: {"detail":"Token is blacklisted","code":"token_not_valid"}
```

---

### Post-Deploy Verification

```bash
# 1. Check database tables
psql -U mygest_user -d mygest -c "SELECT COUNT(*) FROM token_blacklist_outstandingtoken;"
psql -U mygest_user -d mygest -c "SELECT COUNT(*) FROM token_blacklist_blacklistedtoken;"

# 2. Check logs
tail -f /var/log/mygest/django.log | grep -i "token\|login\|logout"

# 3. Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s https://mygest.example.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# 4. Frontend login/logout test
# Navigate to https://mygest.example.com/login
# Login → Verify localStorage tokens
# Logout → Verify tokens cleared + blacklisted
```

---

## 🆘 Troubleshooting

### Issue 1: "Token is blacklisted" subito dopo login

**Causa**: `BLACKLIST_AFTER_ROTATION=True` blacklista anche login token (bug config)

**Fix**: Verifica `ROTATE_REFRESH_TOKENS=True` presente

```python
# mygest/settings/base.py
SIMPLE_JWT = {
    'ROTATE_REFRESH_TOKENS': True,         # ✅ DEVE essere True
    'BLACKLIST_AFTER_ROTATION': True,      # ✅ Blacklist solo dopo refresh
}
```

---

### Issue 2: Frontend non riceve nuovo refresh token

**Causa**: Frontend legge solo `access` da response, ignora `refresh`

**Fix**: Aggiorna `refreshAccessToken()` in authStore.ts

```typescript
// ❌ WRONG
const { access } = response.data;
localStorage.setItem('access_token', access);

// ✅ CORRECT
const { access, refresh: newRefresh } = response.data;
localStorage.setItem('access_token', access);
if (newRefresh) {
  localStorage.setItem('refresh_token', newRefresh);
}
```

---

### Issue 3: Logout non chiama backend

**Causa**: Frontend `logout()` solo clear localStorage

**Fix**: Aggiorna store per chiamare `/auth/logout/`

```typescript
// ❌ WRONG
logout: () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

// ✅ CORRECT
logout: async () => {
  const { refreshToken } = get();
  if (refreshToken) {
    try {
      await apiClient.post('/auth/logout/', { refresh: refreshToken });
    } catch (error) {
      console.warn('Backend logout failed:', error);
    }
  }
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}
```

---

### Issue 4: Database error "relation token_blacklist_outstandingtoken does not exist"

**Causa**: Migrations non applicate

**Fix**:
```bash
python manage.py migrate token_blacklist
```

---

### Issue 5: Access token scade troppo velocemente in dev

**Causa**: Production settings usati in dev per errore

**Fix**: Verifica `DJANGO_ENV=development`

```bash
echo $DJANGO_ENV
# Output: development

# Se non impostato:
export DJANGO_ENV=development
# O aggiungi in .env:
echo "DJANGO_ENV=development" >> .env
```

---

## 📚 References

- **djangorestframework-simplejwt**: https://django-rest-framework-simplejwt.readthedocs.io/
- **JWT.io**: https://jwt.io/ (decoder, spec RFC 7519)
- **OWASP JWT Cheat Sheet**: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html
- **Django REST Framework Authentication**: https://www.django-rest-framework.org/api-guide/authentication/
- **Token Blacklist Implementation**: https://github.com/jazzband/djangorestframework-simplejwt/blob/master/rest_framework_simplejwt/token_blacklist/

---

## 📝 Changelog

### v1.0 - 2026-03-03

- ✅ Abilitata `rest_framework_simplejwt.token_blacklist` app
- ✅ Configurato `ROTATE_REFRESH_TOKENS=True`
- ✅ Configurato `BLACKLIST_AFTER_ROTATION=True`
- ✅ Scadenze production: ACCESS 15min, REFRESH 1day
- ✅ Scadenze development: ACCESS 24h, REFRESH 30d
- ✅ Endpoint `/api/v1/auth/logout/` implementato
- ✅ Frontend `logout()` chiama backend + clear localStorage
- ✅ Frontend `refreshAccessToken()` supporta rotation
- ✅ Axios interceptor aggiorna refresh token se rotation abilitata
- ✅ Testing completo (dev + prod config)
- ✅ Documentazione completa

---

**Versione**: 1.0  
**Data Completamento**: 3 Marzo 2026  
**Status**: ✅ **PRODUCTION READY**  
**Maintainer**: Sandro Chimenti
