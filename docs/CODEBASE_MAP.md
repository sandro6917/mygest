# Mappa Codebase MyGest

**Versione:** 1.0  
**Data:** 3 Marzo 2026  
**Autore:** Analisi Automatica Codebase

---

## 📋 Indice

- [1. Struttura Directory Root](#1-struttura-directory-root)
- [2. Backend Django](#2-backend-django)
- [3. Frontend React](#3-frontend-react)
- [4. API v1 Endpoints](#4-api-v1-endpoints)
- [5. Modelli Django Dettagliati](#5-modelli-django-dettagliati)
- [6. ViewSets e Serializers](#6-viewsets-e-serializers)
- [7. Management Commands](#7-management-commands)
- [8. Testing](#8-testing)
- [9. Scripts e Utility](#9-scripts-e-utility)

---

## 1. Struttura Directory Root

```
/home/sandro/mygest/
├── mygest/                 # Django project settings
│   ├── settings.py        # Configurazione principale
│   ├── urls.py            # URL routing root
│   ├── wsgi.py            # WSGI entry point
│   ├── storages.py        # Custom NAS storage
│   ├── schema.py          # GraphQL schema
│   └── context_processors.py
│
├── api/                   # REST API v1 (modular)
│   └── v1/
│       ├── auth/          # JWT authentication
│       ├── anagrafiche/   # Anagrafiche API
│       ├── documenti/     # Documenti API
│       ├── pratiche/      # Pratiche API
│       ├── fascicoli/     # Fascicoli API
│       ├── scadenze/      # Scadenze API
│       ├── protocollo/    # Protocollo API
│       ├── archivio_fisico/  # Archivio fisico API
│       ├── ai_classifier/    # AI/ML API
│       ├── agent/         # Agent desktop API
│       ├── urls.py        # API routing
│       ├── views.py       # Dashboard stats
│       └── health.py      # Health checks
│
├── anagrafiche/           # App: Gestione anagrafiche
│   ├── models.py          # Anagrafica, Cliente, EmailContatto, Indirizzo
│   ├── models_comuni.py   # ComuneItaliano (database comuni italiani)
│   ├── admin.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── utils.py           # Codice CLI generator
│   ├── signals.py
│   └── management/
│       └── commands/
│           └── import_anagrafiche.py
│
├── documenti/             # App: Gestione documenti
│   ├── models.py          # Documento, DocumentiTipo, AttributoValore, ImportSession
│   ├── admin.py
│   ├── views.py
│   ├── urls.py
│   ├── utils.py           # build_document_filename
│   └── management/
│       └── commands/
│
├── fascicoli/             # App: Gestione fascicoli
│   ├── models.py          # Fascicolo, FascicoloCounter
│   ├── utils.py           # ensure_archivio_path, build_titolario_parts
│   ├── admin.py
│   ├── views.py
│   └── urls.py
│
├── pratiche/              # App: Gestione pratiche
│   ├── models.py          # Pratica, PraticheTipo, PraticaNota, PraticaRelazione
│   ├── admin.py
│   ├── views.py
│   └── urls.py
│
├── scadenze/              # App: Scadenze e calendario
│   ├── models.py          # Scadenza, ScadenzaOccorrenza, ScadenzaAlert, CodiceTributoF24
│   ├── admin.py
│   ├── views.py
│   ├── urls.py
│   └── management/
│       └── commands/
│           ├── genera_occorrenze_scadenze.py
│           └── invia_notifiche_scadenze.py
│
├── archivio_fisico/       # App: Archivio fisico
│   ├── models.py          # UnitaFisica, OperazioneArchivio, CollocazioneFisica
│   ├── admin.py
│   ├── views.py
│   └── urls.py
│
├── protocollo/            # App: Protocollazione
│   ├── models.py          # MovimentoProtocollo, ProtocolloCounter
│   ├── admin.py
│   ├── views.py
│   └── urls.py
│
├── comunicazioni/         # App: Email/PEC management
│   ├── models.py          # Comunicazione, AllegatoComunicazione, Mailbox, EmailImport
│   ├── admin.py
│   ├── views.py
│   ├── urls.py
│   └── api/
│       ├── serializers.py
│       └── urls.py
│
├── whatsapp/              # App: WhatsApp Cloud API
│   ├── models.py
│   ├── admin.py
│   ├── views.py
│   └── urls.py
│
├── titolario/             # App: Classificazione titolario
│   ├── models.py          # TitolarioVoce (gerarchia)
│   ├── admin.py
│   └── fixtures/
│       └── titolario.json
│
├── ai_classifier/         # App: AI Document Classifier
│   ├── models.py          # MLModel, DocumentPrediction, TrainingJob, ExtractionTemplate
│   ├── serializers.py
│   ├── admin.py
│   ├── views.py
│   ├── urls.py
│   └── management/
│       └── commands/
│           ├── train_classifier.py
│           └── extract_training_texts.py
│
├── stampe/                # App: Stampa etichette/report
│   ├── models.py          # StampaFormato, StampaModulo, StampaCampo
│   ├── admin.py
│   ├── views.py
│   └── urls.py
│
├── core/                  # App: RBAC, User Profiles, Core utilities
│   ├── models.py          # UserProfile, UserRole (TextChoices)
│   ├── permissions.py     # RBACPermission, IsAdminOrManager, CanCreate, CanEdit, CanDelete
│   ├── admin.py           # UserProfileInline, UserProfileAdmin
│   ├── apps.py
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_rbac.py   # Test RBAC isolamento dati
│   └── migrations/
│       └── 0001_initial.py  # UserProfile model
│
├── frontend/              # React SPA (TypeScript + Vite)
│   ├── src/
│   │   ├── api/           # API client layer
│   │   ├── components/    # React components
│   │   ├── pages/         # Route pages
│   │   ├── routes/        # React Router config
│   │   ├── store/         # Zustand state
│   │   ├── types/         # TypeScript types
│   │   ├── hooks/         # Custom hooks
│   │   ├── utils/         # Utilities
│   │   ├── theme/         # MUI theme
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── scripts/               # Deployment scripts
│   ├── deploy.sh          # Deploy VPS
│   └── ...
│
├── templates/             # Django templates (legacy)
│   └── ...
│
├── static/                # Static files
│   └── ...
│
├── media/                 # Media files (temp uploads)
│   └── tmp/
│
├── logs/                  # Application logs
│   └── protocollazione.log
│
├── ml_models/             # ML models (development)
│   └── *.pkl
│
├── fixtures/              # Django fixtures
│   └── ...
│
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    (questo documento)
│   ├── CODEBASE_MAP.md    (questa mappa)
│   └── ...
│
├── tests/                 # Test files (root level)
│   └── ...
│
├── manage.py              # Django management
├── requirements.txt       # Python dependencies
├── pytest.ini             # Pytest configuration
├── .env                   # Environment variables
├── .gitignore
└── README.md
```

---

## 2. Backend Django

### 2.1 Django Apps (Moduli)

| App | Path | Responsabilità | Modelli |
|-----|------|---------------|---------|
| **anagrafiche** | `/anagrafiche/` | Gestione anagrafiche, clienti | `Anagrafica`, `Cliente`, `ClientiTipo`, `EmailContatto`, `Indirizzo`, `MailingList`, `ComuneItaliano` |
| **documenti** | `/documenti/` | Upload, classificazione, storage | `Documento`, `DocumentiTipo`, `Ubicazione`, `DocumentoCounter`, `AttributoDefinizione`, `AttributoValore`, `ImportSession`, `ImportSessionDocument` |
| **fascicoli** | `/fascicoli/` | Organizzazione gerarchica | `Fascicolo`, `FascicoloCounter`, `SottofascicoloCounter` |
| **pratiche** | `/pratiche/` | Workflow pratiche | `Pratica`, `PraticheTipo`, `PraticaNota`, `PraticaRelazione` |
| **scadenze** | `/scadenze/` | Scadenze ricorrenti + alert | `Scadenza`, `ScadenzaOccorrenza`, `ScadenzaAlert`, `ScadenzaNotificaLog`, `ScadenzaWebhookPayload`, `CodiceTributoF24` |
| **archivio_fisico** | `/archivio_fisico/` | Tracciamento ubicazioni fisiche | `UnitaFisica`, `OperazioneArchivio`, `RigaOperazioneArchivio`, `CollocazioneFisica`, `Ubicazione`, `VerbaleConsegnaTemplate`, `CatalogoUnitaFisica`, `UnitaFisicaSubunita` |
| **protocollo** | `/protocollo/` | Protocollazione | `MovimentoProtocollo`, `ProtocolloCounter` |
| **comunicazioni** | `/comunicazioni/` | Email IMAP/SMTP, PEC | `Comunicazione`, `AllegatoComunicazione`, `Mailbox`, `EmailImportBlacklist`, `EmailImport` |
| **whatsapp** | `/whatsapp/` | WhatsApp Cloud API | (Modelli WhatsApp) |
| **titolario** | `/titolario/` | Classificazione gerarchica | `TitolarioVoce` |
| **ai_classifier** | `/ai_classifier/` | ML classificazione documenti | `ClassificationJob`, `ClassificationResult`, `ClassifierConfig`, `TrainingExample`, `MLModel`, `DocumentPrediction`, `TrainingQueue`, `TrainingJob`, `DocumentExtractionTemplate`, `ExtractionTemplatePage`, `ExtractionTemplateZone`, `ExtractionFieldMapping`, `AIPredictionFeedback`, `ExtractionCorrection` |
| **stampe** | `/stampe/` | Etichette, report PDF | `StampaFormato`, `StampaModulo`, `StampaCampo`, `StampaLista`, `StampaColonna` |
| **core** | `/core/` | RBAC, User Profiles, utilities | `UserProfile`, `UserRole` (TextChoices) |

### 2.2 Settings Module (`mygest/settings.py`)

**Configurazione chiave**:

```python
# Apps installate (ordine importante)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'graphene_django',
    'compressor',
    'anagrafiche',
    'archivio_fisico',
    'documenti',
    'fascicoli',
    'pratiche',
    'scadenze',
    'stampe',
    'titolario',
    'django_addanother',
    'protocollo',
    'crispy_forms',
    'crispy_bootstrap5',
    'comunicazioni',
    'whatsapp',
    'ai_classifier',
    'core',
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.postgresql',
        'NAME': 'mygest',
        'USER': 'mygest_user',
        'PASSWORD': '***',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 20,
            'RECYCLE': 3600,
            'PRE_PING': True,
        },
    }
}

# Cache (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'KEY_PREFIX': 'mygest',
        'TIMEOUT': 300,
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'KEY_PREFIX': 'mygest_session',
        'TIMEOUT': 86400,
    },
}

# Storage
ARCHIVIO_BASE_PATH = '/mnt/archivio'  # NAS path
NAS_ML_MODELS_PATH = '/mnt/archivio/ml_models'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# CORS (per React SPA)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True
```

### 2.3 URL Routing (`mygest/urls.py`)

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API v1 (REST)
    path('api/v1/', include('api.v1.urls')),
    
    # Traditional Django URLs (legacy/backwards compatibility)
    path('accounts/', include('django.contrib.auth.urls')),
    path('anagrafiche/', include('anagrafiche.urls', namespace='anagrafiche')),
    path('documenti/', include('documenti.urls', namespace='documenti')),
    path('comunicazioni/', include('comunicazioni.urls', namespace='comunicazioni')),
    path('fascicoli/', include('fascicoli.urls', namespace='fascicoli')),
    path('etichette/', include('stampe.urls', namespace='stampe')),
    path('archivio-fisico/', include('archivio_fisico.urls', namespace='archivio_fisico')),
    path('protocollo/', include('protocollo.urls', namespace='protocollo')),
    path('pratiche/', include('pratiche.urls', namespace='pratiche')),
    path('scadenze/', include('scadenze.urls', namespace='scadenze')),
    path('whatsapp/', include('whatsapp.urls', namespace='whatsapp')),
    
    # GraphQL
    path('graphql/', login_required(GraphQLView.as_view(graphiql=True))),
    
    # Help endpoints
    path('api/v1/help/topics/', help_topics_api, name='help-topics-api'),
    path('help/', help_index, name='help-index'),
    path('help/<slug:slug>/', help_topic, name='help-topic'),
    
    # Home
    path('', home, name='home'),
    
    # React SPA catch-all (MUST BE LAST!)
    re_path(r'^.*$', react_spa, name='react-spa'),
]
```

---

## 3. Frontend React

### 3.1 Directory Structure

```
frontend/src/
├── api/                      # API client layer
│   ├── client.ts            # Axios instance + interceptors
│   ├── anagrafiche.ts       # Anagrafiche API service
│   ├── documenti.ts         # Documenti API service
│   ├── pratiche.ts          # Pratiche API service
│   ├── fascicoli.ts         # Fascicoli API service
│   ├── scadenze.ts          # Scadenze API service
│   ├── protocolloApi.ts     # Protocollo API service
│   ├── archivioFisico.ts    # Archivio fisico API service
│   ├── comunicazioni.ts     # Comunicazioni API service
│   ├── aiClassifier.ts      # AI classifier API service
│   ├── aiImport.ts          # AI import API service
│   ├── import.ts            # Import session API service
│   ├── archivio.ts          # Archivio generico
│   └── help.ts              # Help system API
│
├── components/              # React components
│   ├── layout/             # Layout components
│   │   ├── MainLayout.tsx
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   ├── Breadcrumbs.tsx
│   │   └── Footer.tsx
│   ├── common/             # Generic UI components
│   │   ├── LoadingSpinner.tsx
│   │   ├── ErrorMessage.tsx
│   │   ├── ConfirmDialog.tsx
│   │   ├── DataTable.tsx
│   │   ├── SearchBar.tsx
│   │   └── ...
│   └── features/           # Feature-specific components
│       ├── AnagraficaAutocomplete.tsx
│       ├── DocumentiTable.tsx
│       ├── FascicoloTree.tsx
│       ├── PraticaCard.tsx
│       ├── ScadenzaCalendar.tsx
│       ├── UnitaFisicaSelector.tsx
│       └── ...
│
├── pages/                   # Route pages (containers)
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   ├── AnagraficheListPage.tsx
│   ├── AnagraficaDetailPage.tsx
│   ├── AnagraficaFormPage.tsx
│   ├── AnagraficheImportPage.tsx
│   ├── DocumentiListPage.tsx
│   ├── DocumentoDetailPage.tsx
│   ├── DocumentoFormPage.tsx
│   ├── ImportSelectionPage.tsx
│   ├── ImportDocumentsListPage.tsx
│   ├── ImportDocumentPreviewPage.tsx
│   ├── ImportaCedoliniPage.tsx
│   ├── ImportaUnilavPage.tsx
│   ├── PraticheListPage.tsx
│   ├── PraticaDetailPage.tsx
│   ├── PraticaFormPage.tsx
│   ├── FascicoliListPage.tsx
│   ├── FascicoloDetailPage.tsx
│   ├── FascicoloFormPage.tsx
│   ├── ScadenzeListPage.tsx
│   ├── ScadenzaDetailPage.tsx
│   ├── ScadenzaFormPage.tsx
│   ├── ScadenziarioPage.tsx
│   ├── CalendarioPage.tsx
│   ├── ComunicazioniListPage.tsx
│   ├── ComunicazioneDetailPage.tsx
│   ├── ComunicazioneFormPage.tsx
│   ├── MovimentoProtocolloListPage.tsx
│   ├── MovimentoProtocolloDetailPage.tsx
│   ├── ProtocollazionePopupPage.tsx
│   ├── ArchivioPage.tsx
│   ├── UnitaFisicaDetailPage.tsx
│   ├── ArchivioFisico/
│   │   ├── OperazioniArchivioList.tsx
│   │   ├── OperazioneArchivioDetail.tsx
│   │   └── OperazioneArchivioForm.tsx
│   ├── help/
│   │   ├── HelpIndexPage.tsx
│   │   ├── HelpDocumentiPage.tsx
│   │   └── HelpDocumentoTipoDetailPage.tsx
│   └── aiClassifier/
│       └── ...
│
├── routes/                  # React Router configuration
│   ├── index.tsx           # Router definition
│   └── ProtectedRoute.tsx  # Auth guard
│
├── store/                   # Zustand state stores
│   └── authStore.ts        # Global auth state
│
├── types/                   # TypeScript type definitions
│   ├── api.ts              # API response types
│   ├── models.ts           # Domain models
│   └── ...
│
├── hooks/                   # Custom React hooks
│   ├── useAnagrafiche.ts
│   ├── useDocumenti.ts
│   ├── usePratiche.ts
│   ├── useFascicoli.ts
│   ├── useScadenze.ts
│   └── ...
│
├── utils/                   # Utility functions
│   ├── formatters.ts       # Date/number formatters
│   ├── validators.ts       # Form validators
│   └── helpers.ts          # Generic helpers
│
├── theme/                   # MUI theme customization
│   └── theme.ts
│
├── styles/                  # Global CSS
│   └── ...
│
├── config.ts               # App configuration
├── App.tsx                 # Root component
├── App.css
├── main.tsx                # Entry point
└── index.css
```

---

## 4. API v1 Endpoints

### 4.1 Complete Endpoints List

**Authentication**
```
POST   /api/v1/auth/login/              # Login (JWT)
POST   /api/v1/auth/refresh/            # Refresh token
POST   /api/v1/auth/verify/             # Verify token
GET    /api/v1/auth/me/                 # Current user
```

**Anagrafiche**
```
GET    /api/v1/anagrafiche/             # List
POST   /api/v1/anagrafiche/             # Create
GET    /api/v1/anagrafiche/{id}/        # Retrieve
PATCH  /api/v1/anagrafiche/{id}/        # Update
DELETE /api/v1/anagrafiche/{id}/        # Delete
GET    /api/v1/anagrafiche/autocomplete/ # Autocomplete
POST   /api/v1/anagrafiche/import_csv/  # Bulk import
```

**Documenti**
```
GET    /api/v1/documenti/               # List
POST   /api/v1/documenti/               # Create + upload
GET    /api/v1/documenti/{id}/          # Retrieve
PATCH  /api/v1/documenti/{id}/          # Update
DELETE /api/v1/documenti/{id}/          # Delete
POST   /api/v1/documenti/{id}/protocolla/ # Protocolla
GET    /api/v1/documenti/statistiche/   # Stats
GET    /api/v1/documenti/tipi/          # Tipi documento
```

**Fascicoli**
```
GET    /api/v1/fascicoli/               # List
POST   /api/v1/fascicoli/               # Create
GET    /api/v1/fascicoli/{id}/          # Retrieve
PATCH  /api/v1/fascicoli/{id}/          # Update
DELETE /api/v1/fascicoli/{id}/          # Delete
POST   /api/v1/fascicoli/{id}/collega_documento/ # Collega doc
POST   /api/v1/fascicoli/{id}/protocolla/ # Protocolla
GET    /api/v1/fascicoli/{id}/documenti/ # List documenti
```

**Pratiche**
```
GET    /api/v1/pratiche/                # List
POST   /api/v1/pratiche/                # Create
GET    /api/v1/pratiche/{id}/           # Retrieve
PATCH  /api/v1/pratiche/{id}/           # Update
DELETE /api/v1/pratiche/{id}/           # Delete
POST   /api/v1/pratiche/{id}/chiudi/    # Chiudi
GET    /api/v1/pratiche/{id}/note/      # List note
```

**Scadenze**
```
GET    /api/v1/scadenze/                # List
POST   /api/v1/scadenze/                # Create
GET    /api/v1/scadenze/{id}/           # Retrieve
PATCH  /api/v1/scadenze/{id}/           # Update
DELETE /api/v1/scadenze/{id}/           # Delete
POST   /api/v1/scadenze/{id}/genera_occorrenze/ # Genera
GET    /api/v1/scadenze/occorrenze/     # List occorrenze
```

**Archivio Fisico**
```
GET    /api/v1/archivio-fisico/unita/   # List unità
POST   /api/v1/archivio-fisico/unita/   # Create unità
GET    /api/v1/archivio-fisico/unita/{id}/ # Retrieve
PATCH  /api/v1/archivio-fisico/unita/{id}/ # Update
DELETE /api/v1/archivio-fisico/unita/{id}/ # Delete
POST   /api/v1/archivio-fisico/unita/{id}/stampa_etichetta/ # Etichetta
GET    /api/v1/archivio-fisico/operazioni/ # List operazioni
POST   /api/v1/archivio-fisico/operazioni/ # Create operazione
```

---

## 5. Modelli Django Dettagliati

### Relazioni Chiave tra Modelli

```
User (Django) (1) ──────── (1) UserProfile (RBAC)
UserProfile (N) ──────── (N) Cliente (assigned_clients M2M)

Cliente (1) ──────── (N) Documento
Cliente (1) ──────── (N) Fascicolo
Cliente (1) ──────── (N) Pratica
Cliente (1) ──────── (N) Scadenza

Fascicolo (1) ──────── (N) Documento
Fascicolo (N) ──────── (N) Pratica (M2M)
Fascicolo (1) ──────── (N) Fascicolo (parent: sottofascicoli)

Pratica (N) ──────── (N) Pratica (genitori/figli via PraticaRelazione)
Pratica (N) ──────── (1) User (responsabile FK)

Documento (N) ──────── (1) TitolarioVoce
Fascicolo (N) ──────── (1) TitolarioVoce

Documento (N) ──────── (1) UnitaFisica (ubicazione, solo cartacei)
Fascicolo (N) ──────── (1) UnitaFisica (ubicazione, optional)

UnitaFisica (1) ──────── (N) UnitaFisica (parent: gerarchia)

Scadenza (1) ──────── (N) ScadenzaAlert
Scadenza (1) ──────── (N) ScadenzaOccorrenza

Documento (1) ──────── (N) MovimentoProtocollo
Fascicolo (1) ──────── (N) MovimentoProtocollo
```

### Core Models (RBAC)

**UserProfile** (`core.models.UserProfile`):
- `user`: OneToOne User (Django auth)
- `role`: CharField (ADMIN, MANAGER, OPERATORE, VIEWER)
- `assigned_clients`: M2M Cliente (isolamento dati per OPERATORE/VIEWER)

**Properties**:
- `can_view_all`: Bool (True for ADMIN/MANAGER)
- `can_create`, `can_edit`, `can_delete`: Bool (permission helpers)
- `get_accessible_clients_ids()`: List[int] | None (filtro clienti)

**Signal**: auto-create UserProfile on User creation (default role=VIEWER)

---

## 6. ViewSets e Serializers

Ogni modulo API ha:
- **ViewSet**: gestisce CRUD e custom actions
- **Serializer**: valida e trasforma dati
- **Permissions**: RBAC via `RBACPermission` (documenti, fascicoli, pratiche, anagrafiche)

**Pattern comune**:
```python
class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.select_related('cliente', 'tipo')
    serializer_class = DocumentoSerializer
    permission_classes = [RBACPermission]  # RBAC enforcement
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['cliente', 'tipo', 'stato']
    search_fields = ['codice', 'descrizione']
    
    def get_queryset(self):
        """RBAC data isolation"""
        qs = super().get_queryset()
        
        if not hasattr(self.request.user, 'profile'):
            return qs.none()
        
        profile = self.request.user.profile
        
        # ADMIN/MANAGER: tutti i documenti
        if profile.can_view_all:
            return qs
        
        # OPERATORE/VIEWER: solo clienti assegnati
        accessible_clients_ids = profile.get_accessible_clients_ids()
        if accessible_clients_ids is not None:
            qs = qs.filter(cliente_id__in=accessible_clients_ids)
        
        return qs
    
    @action(detail=True, methods=['post'])
    def protocolla(self, request, pk=None):
        # Custom action
        pass
```

**ViewSets con RBAC implementato**:
- ✅ `DocumentoViewSet`
- ✅ `FascicoloViewSet`
- ✅ `PraticaViewSet` (+ filtro responsabile)
- ✅ `AnagraficaViewSet`

---

## 7. Management Commands

**Scadenze**:
```bash
python manage.py genera_occorrenze_scadenze  # Daily cron
python manage.py invia_notifiche_scadenze    # Hourly cron
```

**AI Classifier**:
```bash
python manage.py train_classifier --tipo documento
python manage.py extract_training_texts
```

**Anagrafiche**:
```bash
python manage.py import_anagrafiche --file data.csv
```

---

## 8. Testing

**Pytest** con fixtures:

```python
@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_documento(api_client):
    response = api_client.post('/api/v1/documenti/', {...})
    assert response.status_code == 201
```

**Coverage**:
```bash
pytest --cov=. --cov-report=html
```

---

## 9. Scripts e Utility

**Deploy** (`scripts/deploy.sh`):
```bash
./scripts/deploy.sh  # VPS deployment
```

**Backup**:
```bash
# Database daily
pg_dump mygest > backup.sql

# NAS weekly
rsync -av /mnt/archivio/ /backup/
```

---

**Documento generato automaticamente il 3 Marzo 2026**  
**Per architettura:** Vedi [ARCHITECTURE.md](ARCHITECTURE.md)
