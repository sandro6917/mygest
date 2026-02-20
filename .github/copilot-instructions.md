# Copilot Instructions - MyGest

## 🎯 Panoramica Progetto

**MyGest** è un sistema di gestione pratiche full-stack con:
- **Backend**: Django 4.2 + Django REST Framework + PostgreSQL
- **Frontend**: React 19 + TypeScript + Vite + Material-UI (MUI)
- **Architettura**: API REST con autenticazione JWT
- **Storage**: NAS personalizzato per documenti e archivio fisico
- **Deploy**: VPS Hostinger con Gunicorn + Nginx

## 📁 Struttura Progetto

### Backend Django (`/`)
```
mygest/                 # Configurazione Django principale
├── settings.py        # Settings con Redis cache, JWT, CORS
├── urls.py           # URL routing principale
└── storages.py       # NAS storage personalizzato

api/v1/               # REST API endpoints
├── auth/            # JWT authentication
├── anagrafiche/     # API anagrafiche/clienti
├── documenti/       # API documenti
├── pratiche/        # API pratiche
├── fascicoli/       # API fascicoli
├── scadenze/        # API scadenze
├── protocollo/      # API protocollo
└── archivio_fisico/ # API archivio fisico

anagrafiche/         # App gestione anagrafiche/clienti
documenti/           # App gestione documenti
pratiche/            # App gestione pratiche
fascicoli/           # App gestione fascicoli
scadenze/            # App gestione scadenze/calendari
comunicazioni/       # App gestione comunicazioni
protocollo/          # App protocollo
archivio_fisico/     # App archivio fisico/ubicazioni
titolario/           # App classificazione titolario
whatsapp/            # Integrazione WhatsApp
```

### Frontend React (`/frontend`)
```
src/
├── api/              # API client e services
│   ├── client.ts    # Axios client con JWT interceptors
│   └── *.ts         # Services per ogni modulo
├── components/       # Componenti riutilizzabili
│   ├── layout/      # Layout e navigazione
│   ├── common/      # Componenti UI comuni
│   └── features/    # Componenti specifici per feature
├── pages/           # Pagine/Route components
├── routes/          # React Router configuration
├── store/           # Zustand state management
│   └── authStore.ts # Auth state globale
├── types/           # TypeScript types/interfaces
├── hooks/           # Custom React hooks
└── utils/           # Utility functions
```

## 🔧 Stack Tecnologico

### Backend
- **Framework**: Django 4.2.16
- **API**: Django REST Framework 3.15.2
- **Database**: PostgreSQL con connection pooling
- **Cache**: Redis + django-redis
- **Auth**: JWT (rest_framework_simplejwt)
- **Storage**: NAS personalizzato (`NASPathStorage`)
- **GraphQL**: Graphene-Django 3.2.2
- **Test**: pytest + pytest-django + coverage

### Frontend
- **Framework**: React 19.2 + TypeScript 5.9
- **Build Tool**: Vite 7.2
- **UI Library**: Material-UI v7 (@mui/material)
- **State Management**: Zustand 5.0
- **Data Fetching**: TanStack Query v5 (React Query)
- **HTTP Client**: Axios 1.13
- **Routing**: React Router DOM v7
- **Charts**: Chart.js + react-chartjs-2
- **Calendar**: FullCalendar 6.1
- **Notifications**: react-toastify 11.0
- **WebSockets**: socket.io-client 4.8

### DevOps
- **Server**: Gunicorn 21.2
- **Reverse Proxy**: Nginx
- **Process Manager**: systemd
- **Deploy Script**: `/scripts/deploy.sh`

## 🎨 Convenzioni di Sviluppo

### Backend Django

#### Models
```python
# Usa type hints e annotations
from __future__ import annotations
from typing import Optional

class Documento(models.Model):
    """Documentazione completa del modello"""
    
    # Fields con verbose_name e help_text
    titolo = models.CharField(
        max_length=200,
        verbose_name=_("Titolo"),
        help_text=_("Titolo del documento")
    )
    
    # Usa get_or_create_default per valori di default
    titolario = models.ForeignKey(
        TitolarioVoce,
        on_delete=models.SET(get_or_create_default_titolario),
        related_name="documenti"
    )
    
    class Meta:
        verbose_name = _("Documento")
        verbose_name_plural = _("Documenti")
        ordering = ["-data_creazione"]
        indexes = [
            models.Index(fields=["cliente", "data_documento"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.codice} - {self.titolo}"
```

#### ViewSets (API)
```python
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

class DocumentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet per gestione documenti.
    Endpoint: /api/v1/documenti/
    """
    queryset = Documento.objects.select_related(
        'cliente', 'fascicolo', 'titolario'
    ).prefetch_related('allegati')
    serializer_class = DocumentoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['cliente', 'tipo', 'stato']
    search_fields = ['titolo', 'codice', 'note']
    ordering_fields = ['data_documento', 'data_creazione']
    
    @action(detail=True, methods=['post'])
    def protocolla(self, request, pk=None):
        """Action personalizzata per protocollare documento"""
        documento = self.get_object()
        # ... logica
        return Response({'status': 'success'})
```

#### Serializers
```python
from rest_framework import serializers

class DocumentoSerializer(serializers.ModelSerializer):
    # Read-only computed fields
    cliente_nome = serializers.CharField(source='cliente.anagrafica.nome', read_only=True)
    
    # Nested serializers per dettaglio
    allegati = AllegatoSerializer(many=True, read_only=True)
    
    class Meta:
        model = Documento
        fields = '__all__'
        read_only_fields = ['codice', 'data_creazione', 'utente_creazione']
    
    def validate(self, attrs):
        """Validazione custom"""
        # ... validazione
        return attrs
    
    def create(self, validated_data):
        """Override create per logica personalizzata"""
        # ... logica
        return super().create(validated_data)
```

#### Testing
```python
import pytest
from model_bakery import baker

@pytest.mark.django_db
class TestDocumentoAPI:
    """Test API Documenti"""
    
    def test_create_documento(self, api_client, user):
        """Test creazione documento"""
        api_client.force_authenticate(user=user)
        cliente = baker.make('anagrafiche.Cliente')
        
        data = {
            'titolo': 'Test Doc',
            'cliente': cliente.id,
            'tipo': 'FAT',
        }
        
        response = api_client.post('/api/v1/documenti/', data)
        assert response.status_code == 201
        assert response.data['titolo'] == 'Test Doc'
```

### Frontend React/TypeScript

#### Types
```typescript
// src/types/api.ts
export interface Documento {
  id: number;
  codice: string;
  titolo: string;
  cliente: number;
  cliente_nome?: string;
  data_documento: string;
  file?: string;
  note?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

#### API Services
```typescript
// src/api/documenti.ts
import { apiClient } from './client';
import type { Documento, PaginatedResponse } from '@/types/api';

export const documentiApi = {
  list: async (params?: Record<string, any>) => {
    const { data } = await apiClient.get<PaginatedResponse<Documento>>(
      '/documenti/',
      { params }
    );
    return data;
  },
  
  get: async (id: number) => {
    const { data } = await apiClient.get<Documento>(`/documenti/${id}/`);
    return data;
  },
  
  create: async (documento: Partial<Documento>) => {
    const { data } = await apiClient.post<Documento>('/documenti/', documento);
    return data;
  },
  
  update: async (id: number, documento: Partial<Documento>) => {
    const { data } = await apiClient.patch<Documento>(`/documenti/${id}/`, documento);
    return data;
  },
  
  delete: async (id: number) => {
    await apiClient.delete(`/documenti/${id}/`);
  },
};
```

#### Custom Hooks con React Query
```typescript
// src/hooks/useDocumenti.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentiApi } from '@/api/documenti';

export const useDocumenti = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['documenti', params],
    queryFn: () => documentiApi.list(params),
  });
};

export const useDocumento = (id: number) => {
  return useQuery({
    queryKey: ['documenti', id],
    queryFn: () => documentiApi.get(id),
    enabled: !!id,
  });
};

export const useCreateDocumento = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: documentiApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documenti'] });
    },
  });
};
```

#### Components
```typescript
// src/components/DocumentiTable.tsx
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { useDocumenti } from '@/hooks/useDocumenti';

export const DocumentiTable: React.FC = () => {
  const { data, isLoading } = useDocumenti();
  
  const columns: GridColDef[] = [
    { field: 'codice', headerName: 'Codice', width: 150 },
    { field: 'titolo', headerName: 'Titolo', flex: 1 },
    { field: 'cliente_nome', headerName: 'Cliente', width: 200 },
    { field: 'data_documento', headerName: 'Data', type: 'date', width: 120 },
  ];
  
  return (
    <DataGrid
      rows={data?.results ?? []}
      columns={columns}
      loading={isLoading}
      pagination
      paginationMode="server"
      rowCount={data?.count ?? 0}
    />
  );
};
```

#### Pages
```typescript
// src/pages/DocumentiListPage.tsx
import { Container, Typography, Button, Box } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { DocumentiTable } from '@/components/DocumentiTable';

export const DocumentiListPage: React.FC = () => {
  const navigate = useNavigate();
  
  return (
    <Container maxWidth="xl">
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Documenti</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/documenti/nuovo')}
        >
          Nuovo Documento
        </Button>
      </Box>
      
      <DocumentiTable />
    </Container>
  );
};
```

## 🔐 Autenticazione

### Backend JWT
- Usa `rest_framework_simplejwt` per JWT tokens
- Login endpoint: `POST /api/v1/auth/login/` (returns `access`, `refresh`, `user`)
- Refresh endpoint: `POST /api/v1/auth/refresh/` (returns new `access`)
- Token lifetime: configurato in `settings.py`

### Frontend Auth Flow
```typescript
// Login con Zustand store
import { useAuthStore } from '@/store/authStore';

const { login, logout, isAuthenticated } = useAuthStore();

// Login
await login({ username: 'user', password: 'pass' });

// Logout
logout();

// Protected routes
if (!isAuthenticated) {
  navigate('/login');
}
```

### API Client (Axios)
- Axios interceptor aggiunge automaticamente `Authorization: Bearer <token>`
- Auto-refresh token su 401 response
- Token salvati in `localStorage`

## 📦 Moduli Principali

### Anagrafiche
- **Modelli**: `Anagrafica`, `Cliente`, `ContattoEmail`, `Indirizzo`
- **Validazioni**: Codice Fiscale (PF 16 char + checksum, PG 11 digit)
- **API**: CRUD completo + autocomplete endpoint
- **Frontend**: List, Detail, Form, Import CSV

### Documenti
- **Storage**: NAS personalizzato con pattern `{CLI}-{TIT}-{ANNO}-{SEQ}`
- **Protocollo**: Auto-generazione numero protocollo
- **Modelli**: `Documento`, `DocumentiTipo`, `Allegato`
- **Features**: Upload file, preview PDF, versioning

### Fascicoli
- **Struttura**: Cliente → Fascicolo → Documenti
- **Titolario**: Classificazione gerarchica
- **Path Storage**: Automatico basato su titolario e cliente

### Pratiche
- **Workflow**: Stati personalizzabili
- **Note**: Sistema note con timestamp
- **Relazioni**: Cliente, Fascicolo, Documenti collegati

### Scadenze
- **Tipi**: Singola, Ricorrente (giornaliera, settimanale, mensile, annuale)
- **Alert**: Multi-alert configurabili (email, notifica, WhatsApp)
- **Calendar**: Integrazione FullCalendar

### Archivio Fisico
- **Modelli**: `UnitaFisica`, `CollocazioneFisica`, `OperazioneArchivio`
- **Movimenti**: Versamento, Prelievo, Scarto
- **Tracciabilità**: Storia completa movimentazioni

## 🔒 Business Rules & Constraints

### Documenti

#### Documento.digitale vs Archivio Fisico
```python
# VINCOLO: Documenti digitali NON possono avere ubicazione fisica
if documento.digitale:
    documento.ubicazione = None  # SEMPRE None
    # ❌ NON consentito: assegnare ubicazione a documento digitale
    # ❌ NON consentito: movimentare in archivio fisico
```

**Validazione in `Documento.clean()`**:
```python
if self.digitale:
    if documento_ubicazione_id:
        raise ValidationError("I documenti digitali non prevedono un'ubicazione fisica.")
```

#### Documento.tracciabile (Carte di lavoro)
```python
# VINCOLO: Documenti non tracciabili NON entrano nel protocollo
if not documento.tracciabile:
    # ❌ NON consentito: protocollare
    # ❌ NON consentito: movimentare in archivio fisico
    # ℹ️  Stato magazzino: "Non tracciato"
```

**Validazione in `MovimentoProtocollo.registra_uscita()`**:
```python
if not documento.tracciabile:
    raise ValidationError("Documento non tracciabile: impossibile registrare uscita")
```

#### Documenti Cartacei Fascicolati
```python
# VINCOLO: Se cartaceo + fascicolato → ubicazione DEVE coincidere con fascicolo
if not documento.digitale and documento.fascicolo:
    if fascicolo.ubicazione_id:
        # Auto-allineamento
        documento.ubicazione_id = fascicolo.ubicazione_id
    else:
        # Errore: fascicolo senza ubicazione
        raise ValidationError(
            "I documenti cartacei possono essere collegati solo a "
            "fascicoli con ubicazione fisica."
        )
```

**Validazione in `Documento.clean()`**:
```python
if fascicolo and getattr(fascicolo, "ubicazione_id", None):
    if documento_ubicazione_id and documento_ubicazione_id != fascicolo.ubicazione_id:
        raise ValidationError(
            "Per i documenti cartacei fascicolati l'ubicazione deve "
            "coincidere con quella del fascicolo."
        )
```

#### Documenti Cartacei NON Fascicolati
```python
# VINCOLO: Se cartaceo + NON fascicolato → ubicazione OBBLIGATORIA
if not documento.digitale and not documento.fascicolo:
    if not documento.ubicazione_id:
        raise ValidationError(
            "I documenti cartacei non fascicolati richiedono un'ubicazione fisica."
        )
```

### Archivio Fisico

#### Operazioni su Documenti
```python
# VINCOLO: Solo documenti protocollati possono essere movimentati
if documento and not documento.movimenti.exists():
    raise ValidationError("Il documento non risulta protocollato.")

# VINCOLO: Solo documenti cartacei possono essere movimentati
if documento.digitale:
    raise ValidationError(
        "I documenti digitali non possono essere movimentati in archivio fisico."
    )

# VINCOLO: Solo documenti tracciabili possono essere movimentati
if not documento.tracciabile:
    raise ValidationError(
        "Il documento deve essere tracciabile per partecipare alle operazioni di archivio."
    )
```

**Validazione in `RigaOperazioneArchivio.clean()`**:
```python
if self.documento:
    if self.documento.digitale:
        errors["documento"] = "I documenti digitali non possono essere movimentati."
    if not self.documento.tracciabile:
        errors["documento"] = "Il documento deve essere tracciabile."
```

#### Operazioni su Fascicoli
```python
# VINCOLO: Solo fascicoli protocollati possono essere movimentati
if fascicolo and not fascicolo.movimenti_protocollo.exists():
    raise ValidationError("Il fascicolo non risulta protocollato.")

# VINCOLO: Solo fascicoli con ubicazione fisica possono essere movimentati
if fascicolo and not fascicolo.ubicazione_id:
    raise ValidationError(
        "Il fascicolo deve avere un'ubicazione fisica per essere movimentato."
    )
```

#### Gerarchia Unità Fisiche
```python
# VINCOLO: Gerarchia tipo padre → figli ammessi
TIPO_FIGLI_AMMESSI = {
    'ufficio': {'stanza'},
    'stanza': {'scaffale', 'mobile', 'ripiano'},
    'mobile': {'anta', 'ripiano', 'contenitore'},
    'anta': {'ripiano'},
    'scaffale': {'ripiano'},
    'ripiano': {'contenitore'},
    'contenitore': {'cartellina'},
    'cartellina': set(),  # Nessun figlio
}
```

### Protocollo

#### Protocollazione Documenti Digitali
```python
# VINCOLO: Documenti digitali → ubicazione resta None
if documento.digitale:
    ubicazione = None  # Ignorata anche se passata
```

**Implementazione in `MovimentoProtocollo.registra_entrata()`**:
```python
nuova_ubicazione = None if documento.digitale else ubicazione
```

#### Movimento Uscita Documenti Cartacei Fascicolati
```python
# VINCOLO: Se documento cartaceo fascicolato esce → fascicolo va in USCITO
if not documento.digitale and documento.fascicolo_id:
    documento.fascicolo.stato_fisico = "USCITO"
    documento.fascicolo.save()
```

### Anagrafiche

#### Validazione Codice Fiscale
```python
# VINCOLO: CF Persona Fisica (16 caratteri alfanumerici + checksum)
if tipo == "PF" and len(codice_fiscale) == 16:
    # Validazione algoritmo checksum ufficiale
    if not _cf_pf_is_valid(codice_fiscale):
        raise ValidationError("Codice fiscale persona fisica non valido.")

# VINCOLO: CF Persona Giuridica (11 cifre numeriche = Partita IVA)
if tipo == "PG" and len(codice_fiscale) == 11:
    # Validazione algoritmo mod 10
    if not _piva_is_valid(codice_fiscale):
        raise ValidationError("Codice fiscale numerico/Partita IVA non valido.")
```

#### Validazione Partita IVA
```python
# VINCOLO: P.IVA italiana (11 cifre + checksum mod 10)
def _piva_is_valid(piva: str) -> bool:
    if len(piva) != 11 or not piva.isdigit():
        return False
    # Algoritmo ministeriale checksum
    # ...
    return check == digits[10]
```

### Fascicoli

#### Ubicazione Fisica
```python
# VINCOLO: Fascicoli possono avere ubicazione fisica opzionale
# Se presente, documenti cartacei collegati DEVONO avere stessa ubicazione
if fascicolo.ubicazione_id:
    # Tutti i documenti cartacei devono allinearsi
    DocumentoModel.objects.filter(
        fascicolo_id=fascicolo.pk, 
        digitale=False
    ).update(ubicazione_id=fascicolo.ubicazione_id)
```

## 🎯 Development Guidelines per Business Rules

### Quando implementi nuove features

1. **SEMPRE validare in `Model.clean()`**
   - Logica di business nel modello
   - Sollevare `ValidationError` con messaggi chiari
   
2. **SEMPRE validare in Serializer**
   - Doppia validazione: backend model + API layer
   - Messaggi di errore user-friendly
   
3. **SEMPRE gestire errori in Frontend**
   - Mostrare errori di validazione nei form
   - Disabilitare azioni non consentite (es. pulsante "Movimenta" per doc digitali)

### Esempio completo validazione

**Backend Model**:
```python
def clean(self):
    if self.digitale and self.ubicazione_id:
        raise ValidationError({
            'ubicazione': 'I documenti digitali non prevedono ubicazione fisica.'
        })
```

**Backend Serializer**:
```python
def validate(self, attrs):
    if attrs.get('digitale') and attrs.get('ubicazione'):
        raise serializers.ValidationError({
            'ubicazione': 'I documenti digitali non possono avere ubicazione fisica.'
        })
    return attrs
```

**Frontend Form**:
```typescript
// Disabilita campo ubicazione se digitale=true
<FormControl disabled={formData.digitale}>
  <UbicazioneAutocomplete
    value={formData.ubicazione}
    onChange={(value) => setFormData({ ...formData, ubicazione: value })}
    error={!!errors.ubicazione}
    helperText={
      formData.digitale 
        ? 'Non disponibile per documenti digitali' 
        : errors.ubicazione
    }
  />
</FormControl>
```

**Frontend UI Logic**:
```typescript
// Nascondi azioni non consentite
{!documento.digitale && documento.tracciabile && (
  <Button onClick={() => movimentaInArchivio(documento)}>
    Movimenta in Archivio
  </Button>
)}
```

## 🎨 UI/UX Standards

### Material-UI Theme
- Usa componenti MUI v7
- Dark/Light mode supportato
- Responsive design (mobile-first)

### Navigazione
- Sidebar collapsabile
- Breadcrumbs automatici
- Menu contestuale

### Forms
- Validazione real-time
- Error handling consistente
- Autocomplete per relazioni (Cliente, Fascicolo, etc.)

### Notifications
- Toast notifications con `react-toastify`
- 4 tipi: success, error, warning, info
- Auto-dismiss dopo 3-5 secondi

### Data Display
- Tabelle con DataGrid (MUI X)
- Paginazione server-side
- Filtri e ordinamento
- Export Excel/PDF

## 🧪 Testing

### Backend
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific app
pytest anagrafiche/tests/

# Run parallel
pytest -n auto
```

### Frontend
```bash
# Run tests (se configurato)
npm test

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

## 🚀 Workflow di Sviluppo

### Local Development
```bash
# Backend
source venv/bin/activate
python manage.py runserver

# Frontend
cd frontend
npm run dev  # Runs on http://localhost:5173
```

### Vite Proxy Configuration
Il frontend Vite proxya le richieste API al backend Django:
- `/api/*` → `http://100.99.234.12:8000`
- `/etichette/*` → Backend Django
- `/ws/*` → WebSocket server

### Git Workflow
1. Create feature branch: `git checkout -b feature/nome-feature`
2. Develop and test locally
3. Commit: `git commit -m "feat: descrizione"`
4. Merge to main: `git checkout main && git merge feature/nome-feature`
5. Tag release: `git tag -a v1.0.1 -m "Release notes"`
6. Push: `git push origin main --tags`

### Deploy su VPS
```bash
ssh mygest@72.62.34.249
cd /srv/mygest/app
./scripts/deploy.sh  # Auto: pull, migrate, collectstatic, restart
```

## 📝 Commit Message Convention

Usa Conventional Commits:
- `feat:` - nuova feature
- `fix:` - bug fix
- `docs:` - documentazione
- `style:` - formattazione
- `refactor:` - refactoring
- `test:` - aggiunta test
- `chore:` - maintenance

Esempi:
```
feat(documenti): aggiungi upload multiplo
fix(api): correggi validazione CF
docs(readme): aggiorna istruzioni deploy
```

## 🔍 Code Review Checklist

### Backend
- [ ] Models hanno `__str__` e `Meta` appropriati
- [ ] API usa select_related/prefetch_related per ottimizzazione
- [ ] Serializers hanno validazione custom dove necessario
- [ ] ViewSets usano filtri e ordinamento
- [ ] Test coverage > 80%
- [ ] Migrations committate

### Frontend
- [ ] Types TypeScript corretti e completi
- [ ] Components seguono naming convention
- [ ] Hooks per data fetching (React Query)
- [ ] Error handling implementato
- [ ] Loading states gestiti
- [ ] Responsive design verificato
- [ ] Accessibility (a11y) considerato

## 🛠️ Troubleshooting

### Backend Issues
- **PostgreSQL connection**: Verifica `DATABASES` in `settings.py`
- **Redis cache**: Controlla `CACHES` e Redis server running
- **Static files**: Run `python manage.py collectstatic`
- **Migrations**: `python manage.py migrate`

### Frontend Issues
- **API 401**: Verifica token in localStorage
- **CORS errors**: Controlla `CORS_ALLOWED_ORIGINS` in Django settings
- **Proxy errors**: Verifica `vite.config.ts` proxy configuration
- **Build errors**: Pulisci cache `rm -rf node_modules dist && npm install`

## 📚 Documentazione Aggiuntiva

- **User Guide**: `docs/GUIDA_UTENTE_NUOVA_UI.md`
- **Developer Guide**: `docs/GUIDA_NUOVE_FUNZIONALITA_UI.md`
- **Import Guide**: `anagrafiche/GUIDA_IMPORTAZIONE_ANAGRAFICHE.md`
- **API Docs**: GraphiQL disponibile su `/graphql/` (quando autenticati)

## 🎯 Best Practices

1. **NON usare Django Templates** - Il frontend è React SPA
2. **Usa sempre TypeScript** - No JavaScript plain nel frontend
3. **API First** - Ogni feature deve avere endpoint API REST
4. **Ottimizza query** - Usa select_related/prefetch_related
5. **Cache intelligente** - Usa Redis per query frequenti
6. **Validazione doppia** - Backend (Django) + Frontend (React)
7. **Error handling** - Gestisci sempre errori API
8. **Loading states** - Mostra feedback utente durante caricamenti
9. **Mobile friendly** - Testa su dispositivi mobile
10. **Security first** - JWT tokens, CORS configurato, validazione input

## 🔄 Migration Path

Quando lavori su questo progetto:
1. **Backend**: Scrivi API REST con DRF
2. **Frontend**: Consuma API con React + TypeScript
3. **NO Django Templates**: Il rendering è lato client (React)
4. **NO Django Forms**: Usa React Hook Form o controlli MUI
5. **NO Django Static**: File statici serviti da Vite (dev) o build (prod)

## ⚡ Performance Tips

- **Backend**: Connection pooling, Redis cache, query optimization
- **Frontend**: Code splitting, lazy loading, React Query cache
- **Database**: Indexes su foreign keys e campi filtrati frequentemente
- **Network**: Compress responses, use CDN per assets statici

---

**Versione**: 1.0
**Ultimo aggiornamento**: Gennaio 2026
**Maintainer**: Sandro Chimenti
