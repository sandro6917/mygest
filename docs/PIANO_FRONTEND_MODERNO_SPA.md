# 🚀 Piano Implementazione Frontend Moderno MyGest

## 📋 Executive Summary

Migrazione progressiva di MyGest da architettura template Django tradizionale a **Single Page Application (SPA)** moderna con:
- ⚛️ **React 18** con TypeScript
- 📱 **Progressive Web App** (PWA)
- 🔄 **Real-time updates** con WebSockets
- 🎨 **UI/UX moderna** già implementata
- 🔌 **API REST** con Django REST Framework (già presente)

---

## 🎯 Obiettivi

### Obiettivi Principali

1. **Performance**: Caricamento iniziale <2s, interazioni <100ms
2. **User Experience**: Navigazione fluida senza page refresh
3. **Real-time**: Notifiche e aggiornamenti live
4. **Offline**: Funzionalità base anche senza connessione
5. **Mobile-first**: App installabile su smartphone/tablet

### Metriche di Successo

| Metrica | Attuale | Target | Strumento |
|---------|---------|--------|-----------|
| First Contentful Paint | ~2.5s | <1.5s | Lighthouse |
| Time to Interactive | ~3.5s | <2.0s | Lighthouse |
| Bundle Size | N/A | <300KB gzipped | Webpack Analyzer |
| API Response Time | ~200ms | <100ms | Django Debug Toolbar |
| Lighthouse Score | N/A | >90/100 | Chrome DevTools |

---

## 🏗️ Architettura Proposta

### Stack Tecnologico

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
├─────────────────────────────────────────────────────┤
│  React 18 + TypeScript                              │
│  Vite (Build Tool)                                  │
│  React Router v6 (SPA Routing)                      │
│  Zustand (State Management - lightweight)          │
│  TanStack Query (Data Fetching + Cache)            │
│  Axios (HTTP Client)                                │
│  Socket.IO Client (WebSocket)                       │
│  Workbox (Service Worker)                           │
└─────────────────────────────────────────────────────┘
                         ↕ HTTP/WS
┌─────────────────────────────────────────────────────┐
│                    BACKEND                           │
├─────────────────────────────────────────────────────┤
│  Django 4.2 (Core)                                  │
│  Django REST Framework 3.14+ (API REST)             │
│  Django Channels 4+ (WebSocket)                     │
│  Daphne (ASGI Server)                               │
│  Redis (Channel Layer + Cache)                      │
│  Celery (Background Tasks)                          │
└─────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────┐
│                   DATABASE                           │
├─────────────────────────────────────────────────────┤
│  PostgreSQL (Primary DB)                            │
│  Redis (Cache + PubSub)                             │
└─────────────────────────────────────────────────────┘
```

### Perché React invece di Vue?

| Criterio | React | Vue | Scelta |
|----------|-------|-----|--------|
| Ecosistema | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | React |
| TypeScript | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | React |
| Performance | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Pari |
| Curva Apprendimento | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Vue |
| Job Market | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | React |
| Corporate Support | ⭐⭐⭐⭐⭐ (Meta) | ⭐⭐⭐ (Community) | React |

**Decisione**: **React** per:
- Ecosistema più maturo
- Migliore integrazione TypeScript
- Maggiore disponibilità librerie enterprise
- Team familiarity (se applicabile)

---

## 📁 Struttura Directory Proposta

```
mygest/
├── backend/                    # Django backend (rinomina da root)
│   ├── mygest/                # Settings Django
│   ├── apps/                  # Django apps
│   │   ├── anagrafiche/
│   │   ├── pratiche/
│   │   ├── documenti/
│   │   └── ...
│   ├── api/                   # API REST centralizzata
│   │   ├── v1/
│   │   │   ├── serializers/
│   │   │   ├── views/
│   │   │   ├── urls.py
│   │   │   └── permissions.py
│   │   └── websockets/       # Channels consumers
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/                  # React SPA
│   ├── public/
│   │   ├── manifest.json     # PWA manifest
│   │   ├── sw.js             # Service Worker
│   │   └── icons/
│   ├── src/
│   │   ├── api/              # API client layer
│   │   │   ├── client.ts
│   │   │   ├── endpoints/
│   │   │   └── websocket.ts
│   │   ├── components/       # React components
│   │   │   ├── common/       # Button, Input, Modal, etc.
│   │   │   ├── layout/       # Navbar, Sidebar, Footer
│   │   │   └── features/     # Business components
│   │   ├── pages/            # Page components (routes)
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Pratiche/
│   │   │   ├── Anagrafiche/
│   │   │   └── Documenti/
│   │   ├── hooks/            # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useToast.ts
│   │   ├── store/            # Zustand stores
│   │   │   ├── authStore.ts
│   │   │   ├── uiStore.ts
│   │   │   └── notificationStore.ts
│   │   ├── routes/           # React Router config
│   │   │   └── index.tsx
│   │   ├── styles/           # Global CSS
│   │   │   ├── theme.css     # Variables (riuso esistente)
│   │   │   └── global.css
│   │   ├── types/            # TypeScript types
│   │   │   └── api.d.ts
│   │   ├── utils/            # Helper functions
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── .env.development
│
└── docs/
    ├── API.md                # Documentazione API REST
    ├── WEBSOCKET.md          # Documentazione WebSocket
    └── DEPLOYMENT.md         # Guida deployment SPA+Django
```

---

## 🔄 Strategia Migrazione Progressiva

### Fase 1: Setup & Infrastructure (Settimana 1-2)

**Obiettivo**: Preparare ambiente senza rompere l'esistente

#### 1.1 Setup Frontend

```bash
# Creare progetto React con Vite
npm create vite@latest frontend -- --template react-ts

# Installare dipendenze core
cd frontend
npm install react-router-dom zustand @tanstack/react-query axios socket.io-client
npm install -D @types/node
```

#### 1.2 Configurare Django per SPA

**Modifiche `settings.py`:**

```python
# CORS per sviluppo
INSTALLED_APPS += [
    'corsheaders',
    'channels',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Prima di tutto
    # ... altri middleware
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
]

CORS_ALLOW_CREDENTIALS = True

# Django Channels
ASGI_APPLICATION = 'mygest.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

#### 1.3 Setup API REST

```bash
# Installare dipendenze
pip install djangorestframework-simplejwt django-cors-headers channels channels-redis
```

**Struttura API:**

```python
# api/v1/urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()
router.register(r'pratiche', PraticheViewSet)
router.register(r'anagrafiche', AnagraficheViewSet)
router.register(r'documenti', DocumentiViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('api.v1.auth.urls')),
]
```

### Fase 2: Autenticazione JWT (Settimana 2)

**Backend:**

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}
```

**Frontend:**

```typescript
// src/api/client.ts
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  withCredentials: true,
});

// Interceptor per JWT
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh token automatico
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token logic
    }
    return Promise.reject(error);
  }
);
```

### Fase 3: Primo Modulo SPA - Dashboard (Settimana 3-4)

**Migrazione strategica**: Iniziare con dashboard (meno critica, visibile, wow-factor)

```typescript
// src/pages/Dashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/common/Card';
import { BarChart } from '@/components/charts/BarChart';

export function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.get('/dashboard/stats'),
  });

  return (
    <div className="dashboard">
      <h1>Dashboard MyGest</h1>
      
      <div className="stats-grid">
        <Card title="Pratiche Attive" value={stats?.pratiche_attive} />
        <Card title="Documenti" value={stats?.documenti_count} />
        <Card title="Scadenze Oggi" value={stats?.scadenze_oggi} />
      </div>

      <BarChart data={stats?.pratiche_per_mese} />
    </div>
  );
}
```

### Fase 4: WebSocket Real-time (Settimana 5)

**Backend - Channels Consumer:**

```python
# api/websockets/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['user'].id
        self.room_group_name = f'user_{self.user_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': event['message']
        }))
```

**Frontend - Hook WebSocket:**

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

export function useWebSocket(url: string) {
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    socketRef.current = io(url, {
      auth: {
        token: localStorage.getItem('access_token'),
      },
    });

    socketRef.current.on('notification', (data) => {
      // Mostra toast notification
      toast.info(data.message);
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, [url]);

  return socketRef.current;
}
```

### Fase 5: PWA Configuration (Settimana 6)

**Manifest.json:**

```json
{
  "name": "MyGest - Gestionale Moderno",
  "short_name": "MyGest",
  "description": "Sistema di gestione pratiche e documenti",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0d47a1",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Service Worker con Workbox:**

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    VitePWA({
      registerType: 'autoUpdate',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.mygest\.com\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24, // 24 ore
              },
            },
          },
        ],
      },
    }),
  ],
});
```

### Fase 6: Migrazione Moduli Progressiva (Settimana 7-12)

**Ordine priorità migrazione:**

1. ✅ Dashboard (Settimana 3-4)
2. 📋 Pratiche (Settimana 7-8) - Modulo core
3. 📄 Documenti (Settimana 9-10)
4. 👥 Anagrafiche (Settimana 10-11)
5. 📅 Scadenze (Settimana 11)
6. 🗃️ Archivio Fisico (Settimana 12)
7. 📧 Comunicazioni (Settimana 12)

**Strategia per ogni modulo:**

```typescript
// Pattern standard per ogni modulo
src/pages/Pratiche/
├── index.tsx              # Lista pratiche
├── Detail.tsx             # Dettaglio singola pratica
├── Create.tsx             # Form creazione
├── Edit.tsx               # Form modifica
├── components/            # Componenti specifici
│   ├── PraticaCard.tsx
│   └── PraticaFilters.tsx
└── hooks/                 # Logic isolata
    └── usePratiche.ts
```

---

## 📊 Piano Dettagliato Implementazione

### Timeline Completa (12 settimane)

```
Settimana 1-2:  🏗️  Setup & Infrastructure
                    - Vite + React + TypeScript
                    - Django Channels + Redis
                    - CORS & API structure

Settimana 2:    🔐  Autenticazione JWT
                    - Backend: SimpleJWT
                    - Frontend: Auth context + hooks
                    - Login/Logout pages

Settimana 3-4:  📊  Dashboard SPA
                    - Statistiche real-time
                    - Grafici Chart.js/Recharts
                    - Skeleton loaders

Settimana 5:    🔄  WebSocket Real-time
                    - Channels consumers
                    - Socket.IO client
                    - Toast notifications live

Settimana 6:    📱  PWA Setup
                    - Manifest.json
                    - Service Worker
                    - Offline mode

Settimana 7-8:  📋  Modulo Pratiche
                    - CRUD completo
                    - Filtri avanzati
                    - Export/Import

Settimana 9-10: 📄  Modulo Documenti
                    - Upload multipli
                    - Preview files
                    - Versioning

Settimana 11:   👥  Anagrafiche + Scadenze
                    - Form intelligenti
                    - Notifiche scadenze

Settimana 12:   🗃️  Archivio + Comunicazioni
                    - Gestione archivio fisico
                    - Email integration

Post-Release:   🚀  Ottimizzazioni
                    - Performance tuning
                    - SEO
                    - Analytics
```

---

## 💻 Esempi Codice Chiave

### React Component con TypeScript

```typescript
// src/components/features/PraticaCard.tsx
interface Pratica {
  id: number;
  numero: string;
  oggetto: string;
  stato: 'aperta' | 'chiusa' | 'sospesa';
  data_apertura: string;
  cliente: {
    nome: string;
    cognome: string;
  };
}

interface PraticaCardProps {
  pratica: Pratica;
  onEdit?: (id: number) => void;
  onDelete?: (id: number) => void;
}

export function PraticaCard({ pratica, onEdit, onDelete }: PraticaCardProps) {
  const statusColor = {
    aperta: 'bg-green-500',
    chiusa: 'bg-gray-500',
    sospesa: 'bg-yellow-500',
  }[pratica.stato];

  return (
    <div className="card hover:shadow-lg transition-shadow">
      <div className="card-header">
        <h3>{pratica.numero}</h3>
        <span className={`badge ${statusColor}`}>
          {pratica.stato}
        </span>
      </div>
      
      <div className="card-body">
        <p className="text-lg font-semibold">{pratica.oggetto}</p>
        <p className="text-sm text-gray-600">
          Cliente: {pratica.cliente.nome} {pratica.cliente.cognome}
        </p>
        <time className="text-xs text-gray-500">
          {new Date(pratica.data_apertura).toLocaleDateString('it-IT')}
        </time>
      </div>

      <div className="card-footer">
        {onEdit && (
          <button onClick={() => onEdit(pratica.id)} className="btn-primary">
            Modifica
          </button>
        )}
        {onDelete && (
          <button onClick={() => onDelete(pratica.id)} className="btn-danger">
            Elimina
          </button>
        )}
      </div>
    </div>
  );
}
```

### Custom Hook con TanStack Query

```typescript
// src/hooks/usePratiche.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

interface PraticaFilters {
  stato?: string;
  cliente?: number;
  data_da?: string;
  data_a?: string;
}

export function usePratiche(filters?: PraticaFilters) {
  const queryClient = useQueryClient();

  // Query per lista pratiche
  const { data, isLoading, error } = useQuery({
    queryKey: ['pratiche', filters],
    queryFn: () => apiClient.get('/pratiche/', { params: filters }),
    staleTime: 5 * 60 * 1000, // 5 minuti
  });

  // Mutation per creare pratica
  const createMutation = useMutation({
    mutationFn: (newPratica: Partial<Pratica>) =>
      apiClient.post('/pratiche/', newPratica),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pratiche'] });
      toast.success('Pratica creata con successo!');
    },
  });

  // Mutation per aggiornare pratica
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Pratica> }) =>
      apiClient.patch(`/pratiche/${id}/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pratiche'] });
      toast.success('Pratica aggiornata!');
    },
  });

  // Mutation per eliminare pratica
  const deleteMutation = useMutation({
    mutationFn: (id: number) => apiClient.delete(`/pratiche/${id}/`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pratiche'] });
      toast.success('Pratica eliminata!');
    },
  });

  return {
    pratiche: data?.data || [],
    isLoading,
    error,
    create: createMutation.mutate,
    update: updateMutation.mutate,
    delete: deleteMutation.mutate,
  };
}
```

### Zustand Store per State Management

```typescript
// src/store/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (username, password) => {
        const response = await apiClient.post('/auth/login/', {
          username,
          password,
        });
        
        set({
          user: response.data.user,
          accessToken: response.data.access,
          refreshToken: response.data.refresh,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get();
        const response = await apiClient.post('/auth/refresh/', {
          refresh: refreshToken,
        });
        
        set({ accessToken: response.data.access });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

---

## 🔒 Sicurezza

### Best Practices

1. **JWT Storage**: 
   - ✅ AccessToken in memoria (state)
   - ✅ RefreshToken in httpOnly cookie (se possibile)
   - ❌ Mai in localStorage (XSS risk)

2. **CORS Stricto**:
   ```python
   # Production
   CORS_ALLOWED_ORIGINS = [
       "https://mygest.com",
   ]
   ```

3. **CSP Headers**:
   ```python
   # settings.py
   SECURE_CONTENT_TYPE_NOSNIFF = True
   SECURE_BROWSER_XSS_FILTER = True
   X_FRAME_OPTIONS = 'DENY'
   ```

4. **Rate Limiting**:
   ```python
   # REST_FRAMEWORK settings
   'DEFAULT_THROTTLE_RATES': {
       'anon': '100/hour',
       'user': '1000/hour'
   }
   ```

---

## 📈 Performance Optimization

### Bundle Optimization

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query'],
          'ui-vendor': ['chart.js', 'date-fns'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
});
```

### Lazy Loading Routes

```typescript
// src/routes/index.tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Pratiche = lazy(() => import('@/pages/Pratiche'));
const Documenti = lazy(() => import('@/pages/Documenti'));

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={
        <Suspense fallback={<PageLoader />}>
          <Dashboard />
        </Suspense>
      } />
      <Route path="/pratiche" element={
        <Suspense fallback={<PageLoader />}>
          <Pratiche />
        </Suspense>
      } />
    </Routes>
  );
}
```

### API Response Caching

```typescript
// TanStack Query default config
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 min
      cacheTime: 10 * 60 * 1000, // 10 min
      refetchOnWindowFocus: false,
    },
  },
});
```

---

## 🧪 Testing Strategy

### Frontend Tests

```typescript
// src/components/PraticaCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { PraticaCard } from './PraticaCard';

describe('PraticaCard', () => {
  const mockPratica = {
    id: 1,
    numero: 'PR001',
    oggetto: 'Test Pratica',
    stato: 'aperta',
    data_apertura: '2025-11-17',
    cliente: { nome: 'Mario', cognome: 'Rossi' },
  };

  it('renders pratica info correctly', () => {
    render(<PraticaCard pratica={mockPratica} />);
    
    expect(screen.getByText('PR001')).toBeInTheDocument();
    expect(screen.getByText('Test Pratica')).toBeInTheDocument();
    expect(screen.getByText(/Mario Rossi/)).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', () => {
    const onEdit = jest.fn();
    render(<PraticaCard pratica={mockPratica} onEdit={onEdit} />);
    
    fireEvent.click(screen.getByText('Modifica'));
    expect(onEdit).toHaveBeenCalledWith(1);
  });
});
```

### E2E Tests con Playwright

```typescript
// e2e/pratiche.spec.ts
import { test, expect } from '@playwright/test';

test('create new pratica', async ({ page }) => {
  await page.goto('/pratiche');
  await page.click('text=Nuova Pratica');
  
  await page.fill('[name="oggetto"]', 'Test E2E Pratica');
  await page.selectOption('[name="stato"]', 'aperta');
  await page.click('text=Salva');
  
  await expect(page.locator('text=Pratica creata con successo')).toBeVisible();
});
```

---

## 🚀 Deployment

### Build Production

```bash
# Frontend
cd frontend
npm run build
# Output: frontend/dist/

# Backend
cd backend
python manage.py collectstatic --noinput
```

### Docker Compose

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mygest
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  daphne:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: daphne -b 0.0.0.0 -p 8001 mygest.asgi:application
    ports:
      - "8001:8001"
    depends_on:
      - redis

volumes:
  postgres_data:
```

### Nginx Config per SPA

```nginx
server {
    listen 80;
    server_name mygest.com;

    # Frontend SPA
    location / {
        root /var/www/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://daphne:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 📊 Costi & Risorse

### Tempo Sviluppo

| Fase | Durata | Sviluppatori | Effort |
|------|--------|--------------|--------|
| Setup | 2 settimane | 1 senior | 80h |
| Auth + Dashboard | 3 settimane | 1 senior | 120h |
| WebSocket + PWA | 2 settimane | 1 senior | 80h |
| Migrazione Moduli | 5 settimane | 2 devs | 400h |
| Testing + Deploy | 2 settimane | 2 devs | 160h |
| **TOTALE** | **12 settimane** | **2 devs** | **840h** |

### Budget Hosting (mensile)

- VPS/Cloud (4vCPU, 8GB RAM): €50-100
- Database PostgreSQL managed: €30-50
- Redis managed: €20-30
- CDN: €10-20
- **TOTALE**: €110-200/mese

---

## ✅ Checklist Go-Live

### Pre-Release

- [ ] Testing E2E completo
- [ ] Performance audit (Lighthouse >90)
- [ ] Security audit (OWASP Top 10)
- [ ] Load testing (Artillery/k6)
- [ ] Backup strategy
- [ ] Rollback plan
- [ ] Monitoring setup (Sentry)
- [ ] Documentation completa

### Post-Release

- [ ] User training
- [ ] Bug tracking setup
- [ ] Analytics setup (GA4)
- [ ] Feedback loop
- [ ] Performance monitoring
- [ ] A/B testing framework

---

## 🎯 Next Steps Immediati

### Questa Settimana

1. **Setup ambiente**:
   ```bash
   npm create vite@latest frontend -- --template react-ts
   pip install channels channels-redis django-cors-headers
   ```

2. **Configurare CORS** in settings.py

3. **Creare API endpoints** per Dashboard

4. **Implementare auth JWT** (backend + frontend)

### Prossime 2 Settimane

1. Completare Dashboard con grafici
2. Setup WebSocket per notifiche
3. Primo deploy su staging

---

## 📚 Risorse

### Tutorial & Docs

- [React 18 Docs](https://react.dev/)
- [Django Channels](https://channels.readthedocs.io/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Vite Guide](https://vitejs.dev/guide/)

### Librerie Consigliate

- **UI**: Shadcn/ui (Tailwind + Radix)
- **Forms**: React Hook Form + Zod
- **Charts**: Recharts o Chart.js
- **Dates**: date-fns
- **Icons**: Lucide React

---

**Data Documento**: 17 Novembre 2025  
**Versione**: 1.0  
**Autore**: GitHub Copilot AI Assistant  
**Status**: 📋 Planning Phase
