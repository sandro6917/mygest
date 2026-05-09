# Architettura MyGest

**Versione:** 1.0  
**Data:** 3 Marzo 2026  
**Autore:** Analisi Architettonica Automatica

---

## 📋 Indice

- [1. Panoramica Sistema](#1-panoramica-sistema)
- [2. Stack Tecnologico](#2-stack-tecnologico)
- [3. Architettura Generale](#3-architettura-generale)
- [4. Layer Applicativo](#4-layer-applicativo)
- [5. Modello Dati](#5-modello-dati)
- [6. Flussi Applicativi](#6-flussi-applicativi)
- [7. Sicurezza e Autenticazione](#7-sicurezza-e-autenticazione)
- [8. Storage e File Management](#8-storage-e-file-management)
- [9. Cache e Performance](#9-cache-e-performance)
- [10. API Architecture](#10-api-architecture)
- [11. Frontend Architecture](#11-frontend-architecture)
- [12. Integrazioni](#12-integrazioni)
- [13. Deployment](#13-deployment)

---

## 1. Panoramica Sistema

**MyGest** è un sistema full-stack per la gestione documentale, pratiche e archivio fisico con le seguenti caratteristiche:

- **Tipo**: Web Application (SPA + REST API)
- **Dominio**: Document Management System (DMS), Workflow Management, Archivio Fisico
- **Utenti**: Studio professionale, dipendenti, amministratori
- **Scale**: Single-tenant, deployment VPS

### Funzionalità Core

1. **Gestione Anagrafiche** - Persone fisiche/giuridiche, clienti, contatti
2. **Gestione Documenti** - Upload, classificazione, protocollazione, archiviazione
3. **Gestione Fascicoli** - Organizzazione gerarchica documenti per titolario
4. **Gestione Pratiche** - Workflow pratiche multicliente con stati e relazioni
5. **Scadenze e Calendario** - Sistema scadenze ricorrenti con alert multipli
6. **Archivio Fisico** - Tracciamento ubicazioni fisiche e movimentazioni
7. **Protocollo** - Protocollazione automatica con numerazione progressiva
8. **Comunicazioni** - Gestione email IMAP/SMTP, PEC, WhatsApp
9. **AI Classifier** - Classificazione automatica documenti con ML locale

---

## 2. Stack Tecnologico

### Backend

| Componente | Tecnologia | Versione |
|------------|-----------|----------|
| **Framework** | Django | 4.2.16 |
| **API** | Django REST Framework | 3.15.2 |
| **Database** | PostgreSQL | - |
| **Connection Pool** | dj-db-conn-pool | - |
| **Cache** | Redis + django-redis | - |
| **Auth** | rest_framework_simplejwt | JWT |
| **GraphQL** | Graphene-Django | 3.2.2 |
| **WSGI Server** | Gunicorn | 21.2 |
| **Task Queue** | (Non presente - potenziale Celery) | - |

### Frontend

| Componente | Tecnologia | Versione |
|------------|-----------|----------|
| **Framework** | React | 19.2 |
| **Language** | TypeScript | 5.9 |
| **Build Tool** | Vite | 7.2 |
| **UI Library** | Material-UI (MUI) | v7 |
| **State** | Zustand | 5.0 |
| **Data Fetching** | TanStack Query (React Query) | v5 |
| **HTTP Client** | Axios | 1.13 |
| **Routing** | React Router DOM | v7 |
| **Charts** | Chart.js + react-chartjs-2 | - |
| **Calendar** | FullCalendar | 6.1 |
| **Notifications** | react-toastify | 11.0 |
| **WebSockets** | socket.io-client | 4.8 |

### Infrastructure

| Componente | Tecnologia |
|------------|-----------|
| **Reverse Proxy** | Nginx |
| **Process Manager** | systemd |
| **Storage** | NAS (custom path storage) |
| **Email** | SMTP (Aruba) + IMAP |
| **VPS** | Hostinger |
| **OS** | Linux (produzione) / WSL (sviluppo) |

---

## 3. Architettura Generale

### Pattern Architetturale

**Architettura a 3 Tier + SPA**

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT TIER                          │
│  React SPA (TypeScript + MUI + Zustand + React Query)  │
│           Vite Dev Server / Static Files                │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTPS/HTTP (REST API + JWT)
                      │
┌─────────────────────▼───────────────────────────────────┐
│                 APPLICATION TIER                        │
│   Django + DRF (REST API) + Gunicorn + Nginx           │
│   - ViewSets (CRUD operations)                          │
│   - Serializers (Data validation/transformation)        │
│   - Business Logic (Models + Services)                  │
│   - Authentication (JWT + Token + Session)              │
└─────────────────────┬───────────────────────────────────┘
                      │ PostgreSQL Protocol
                      │
┌─────────────────────▼───────────────────────────────────┐
│                   DATA TIER                             │
│   PostgreSQL Database (connection pooling)              │
│   Redis Cache (sessions + API cache)                    │
│   NAS Storage (documenti fisici + ML models)            │
└─────────────────────────────────────────────────────────┘
```

### Comunicazione Client-Server

1. **Development**:
   - Frontend: `http://localhost:5173` (Vite)
   - Backend: `http://100.99.234.12:8000` (Django)
   - Vite proxy: `/api/*` → Backend

2. **Production**:
   - Nginx: Reverse proxy su porta 80/443
   - Static files: Serviti da Nginx (WhiteNoise)
   - API: `/api/v1/*` → Gunicorn Django

---

## 4. Layer Applicativo

### Backend - Django Apps

MyGest è organizzato in **app Django modulari**:

| App | Responsabilità | Modelli Principali |
|-----|---------------|-------------------|
| **anagrafiche** | Gestione anagrafiche, clienti, contatti | `Anagrafica`, `Cliente`, `EmailContatto`, `Indirizzo` |
| **documenti** | Upload, classificazione, storage documenti | `Documento`, `DocumentiTipo`, `AttributoValore`, `ImportSession` |
| **fascicoli** | Organizzazione gerarchica documenti | `Fascicolo`, `FascicoloCounter` |
| **pratiche** | Workflow pratiche con stati | `Pratica`, `PraticheTipo`, `PraticaNota`, `PraticaRelazione` |
| **scadenze** | Sistema scadenze ricorrenti + alert | `Scadenza`, `ScadenzaOccorrenza`, `ScadenzaAlert`, `CodiceTributoF24` |
| **archivio_fisico** | Tracciamento ubicazioni fisiche | `UnitaFisica`, `OperazioneArchivio`, `CollocazioneFisica` |
| **protocollo** | Protocollazione documenti/fascicoli | `MovimentoProtocollo`, `ProtocolloCounter` |
| **comunicazioni** | Email IMAP/SMTP, tracking | `Comunicazione`, `AllegatoComunicazione`, `Mailbox`, `EmailImport` |
| **whatsapp** | Integrazione WhatsApp Cloud API | (Modelli WhatsApp) |
| **titolario** | Classificazione gerarchica documenti | `TitolarioVoce` |
| **ai_classifier** | ML per classificazione automatica | `MLModel`, `DocumentPrediction`, `TrainingJob`, `DocumentExtractionTemplate` |
| **stampe** | Generazione etichette/report | `StampaFormato`, `StampaModulo`, `StampaCampo` |
| **core** | Funzionalità condivise | Management commands |

### Frontend - React Structure

```
frontend/src/
├── api/              # API client layer (Axios)
├── components/       # Componenti riutilizzabili
│   ├── layout/      # Layout (Sidebar, Header, Breadcrumbs)
│   ├── common/      # UI comuni (Button, Card, Table, etc.)
│   └── features/    # Feature-specific components
├── pages/           # Route pages
├── routes/          # React Router config
├── store/           # Zustand stores (authStore)
├── types/           # TypeScript types/interfaces
├── hooks/           # Custom React hooks
└── utils/           # Utility functions
```

---

## 5. Modello Dati

### 5.1 Entità Core

#### Anagrafica
```
Anagrafica
├── tipo: PF | PG
├── codice_fiscale (unique)
├── partita_iva
├── codice (CLI - 8 char)
├── nome/cognome (PF)
├── ragione_sociale (PG)
└── contatti (email, pec, telefono)

Cliente (FK → Anagrafica)
└── tipo: FK → ClientiTipo
```

#### Documento
```
Documento
├── codice (univoco, pattern-based)
├── tipo: FK → DocumentiTipo
├── cliente: FK → Cliente
├── fascicolo: FK → Fascicolo (optional)
├── titolario: FK → TitolarioVoce (default: "99 - Varie")
├── ubicazione: FK → UnitaFisica (solo cartacei)
├── file: FilePathField (NAS storage)
├── digitale: Boolean
├── tracciabile: Boolean
├── stato: bozza | definitivo | archiviato | uscito | consegnato | scaricato
├── data_documento
└── attributi dinamici: [AttributoValore]
```

#### Fascicolo
```
Fascicolo
├── codice (univoco)
├── cliente: FK → Cliente
├── titolario_voce: FK → TitolarioVoce
├── parent: FK → Fascicolo (sottofascicoli)
├── pratiche: M2M → Pratica
├── fascicoli_collegati: M2M → Fascicolo
├── anno
├── progressivo / sub_progressivo
├── ubicazione: FK → UnitaFisica (optional)
├── stato: corrente | storico | chiuso | deposito | scaricato
└── path_archivio: CharField (path NAS)
```

#### Pratica
```
Pratica
├── codice (univoco, pattern-based)
├── cliente: FK → Cliente
├── tipo: FK → PraticheTipo
├── genitori: M2M → Pratica (relazioni padre-figlio)
├── stato: aperta | lavorazione | attesa | chiusa
├── responsabile: FK → User
├── periodo_riferimento: anno | annomese | annomesegiorno
├── data_riferimento
├── periodo_key (computed)
└── progressivo
```

#### Scadenza
```
Scadenza
├── cliente: FK → Cliente (optional)
├── pratica: FK → Pratica (optional)
├── tipo_ricorrenza: SINGOLA | GIORNALIERA | SETTIMANALE | MENSILE | ANNUALE
├── data_inizio
├── ora_scadenza
├── alerts: [ScadenzaAlert]  # alert multipli (email, notifica, WhatsApp)
└── occorrenze: [ScadenzaOccorrenza]  # generate dinamicamente
```

#### Archivio Fisico
```
UnitaFisica
├── tipo: ufficio | stanza | scaffale | mobile | anta | ripiano | contenitore | cartellina
├── codice (univoco, auto-padded)
├── parent: FK → UnitaFisica (gerarchia)
├── cliente: FK → Cliente (optional, per cartellina)
├── ubicazione: CharField (descrizione testuale)
└── stato: disponibile | in_uso | pieno | danneggiato | scaricato

OperazioneArchivio
├── tipo: versamento | prelievo | ricollocazione | scarto
├── data_operazione
├── unita_destinazione: FK → UnitaFisica
├── righe: [RigaOperazioneArchivio]
└── completata: Boolean

RigaOperazioneArchivio
├── operazione: FK → OperazioneArchivio
├── documento: FK → Documento (optional)
├── fascicolo: FK → Fascicolo (optional)
└── note
```

### 5.2 Relazioni Chiave

```
Cliente (1) ──────── (N) Documento
Cliente (1) ──────── (N) Fascicolo
Cliente (1) ──────── (N) Pratica
Cliente (1) ──────── (N) Scadenza

Fascicolo (1) ──────── (N) Documento
Fascicolo (N) ──────── (N) Pratica (M2M)
Fascicolo (1) ──────── (N) Fascicolo (parent: sottofascicoli)

Pratica (N) ──────── (N) Pratica (genitori/figli via PraticaRelazione)

Documento (N) ──────── (1) TitolarioVoce
Fascicolo (N) ──────── (1) TitolarioVoce

Documento (N) ──────── (1) UnitaFisica (ubicazione, solo cartacei)
Fascicolo (N) ──────── (1) UnitaFisica (ubicazione, optional)

UnitaFisica (1) ──────── (N) UnitaFisica (parent: gerarchia)

Scadenza (1) ──────── (N) ScadenzaAlert
Scadenza (1) ──────── (N) ScadenzaOccorrenza (generate)

Documento (1) ──────── (N) MovimentoProtocollo
Fascicolo (1) ──────── (N) MovimentoProtocollo
```

---

## 6. Flussi Applicativi

### 6.1 Flusso Upload Documento

```
1. Frontend: User seleziona file + compila form
   ↓
2. Frontend: POST /api/v1/documenti/
   - multipart/form-data (file + metadata)
   ↓
3. Backend: DocumentoViewSet.create()
   ↓
4. Serializer validation:
   - Tipo documento valido
   - Cliente esistente
   - Fascicolo (se presente) con ubicazione coerente
   ↓
5. Model.save():
   - Upload file temporaneo (tmp/<anno>/<CLI>/<filename>)
   - Generazione codice documento (pattern-based)
   - Se attributi dinamici → salva AttributoValore
   - Costruzione path_archivio NAS
   - Spostamento file → NAS storage
   ↓
6. Response: JSON documento creato
   ↓
7. Frontend: Redirect a DocumentoDetailPage
   ↓
8. (Opzionale) Protocollazione:
   - POST /api/v1/protocollo/movimenti/registra_entrata/
   - Genera numero protocollo progressivo
   - Registra MovimentoProtocollo
```

### 6.2 Flusso Protocollazione

```
1. Frontend: Click "Protocolla" su documento/fascicolo
   ↓
2. Frontend: POST /api/v1/protocollo/movimenti/registra_entrata/
   - documento_id o fascicolo_id
   - ubicazione_id (se documento cartaceo)
   ↓
3. Backend: MovimentoProtocolloViewSet.registra_entrata()
   ↓
4. Logica protocollazione:
   - Verifica: già protocollato? → errore
   - Documento digitale → ubicazione = None
   - Documento cartaceo fascicolato → ubicazione = fascicolo.ubicazione
   - Documento cartaceo non fascicolato → ubicazione obbligatoria
   ↓
5. Generazione numero protocollo:
   - Lock su ProtocolloCounter
   - Incrementa progressivo annuale
   - Formato: "PROT-{ANNO}-{SEQ:06d}"
   ↓
6. Salvataggio MovimentoProtocollo:
   - numero_protocollo
   - direzione: IN
   - data_movimento
   - content_type (Documento/Fascicolo)
   ↓
7. Aggiorna stato documento:
   - stato_protocollo = "PROTOCOLLATO"
   ↓
8. Response: JSON movimento creato
   ↓
9. Frontend: Aggiorna UI con numero protocollo
```

### 6.3 Flusso Import Documenti (AI)

```
1. Frontend: Upload ZIP/file multipli
   ↓
2. POST /api/v1/ai-classifier/import/start/
   ↓
3. Backend: Crea ImportSession
   - Estrae ZIP
   - Salva file temporanei
   ↓
4. Analisi documenti:
   - Per ogni file: estrai testo (PDF/OCR)
   - ML prediction: tipo documento
   - ML extraction: campi dinamici (es. cedolino → matricola, mese)
   ↓
5. Response: session_id + predictions preview
   ↓
6. Frontend: ImportSelectionPage
   - Mostra anteprima documenti
   - User conferma/corregge classificazione
   ↓
7. POST /api/v1/ai-classifier/import/{session_id}/confirm/
   ↓
8. Backend: Bulk creation Documento
   - Per ogni documento: crea + salva attributi
   - Sposta file → NAS storage
   ↓
9. (Opzionale) Feedback loop:
   - User corregge → salva AIPredictionFeedback
   - Trigger re-training model
```

### 6.4 Flusso Scadenza Ricorrente

```
1. Frontend: Crea scadenza ricorrente (es. F24 mensile)
   ↓
2. POST /api/v1/scadenze/
   - tipo_ricorrenza: MENSILE
   - data_inizio: 2026-01-16
   - giorno_mese: 16
   - alerts: [
       {metodo: EMAIL, giorni_anticipo: 7},
       {metodo: WHATSAPP, giorni_anticipo: 1}
     ]
   ↓
3. Backend: ScadenzaViewSet.create()
   ↓
4. Model.save():
   - Crea Scadenza
   - Crea ScadenzaAlert (M2M)
   ↓
5. Management command (cron daily):
   - python manage.py genera_occorrenze_scadenze
   ↓
6. Generazione occorrenze:
   - Per ogni scadenza ricorrente
   - Calcola prossimi 3 mesi di occorrenze
   - Crea ScadenzaOccorrenza (se non esiste)
   ↓
7. Management command (cron ogni ora):
   - python manage.py invia_notifiche_scadenze
   ↓
8. Invio notifiche:
   - Per ogni occorrenza futura
   - Per ogni alert configurato
   - Calcola: data_occorrenza - giorni_anticipo
   - Se oggi >= data_invio → invia email/WhatsApp
   - Salva ScadenzaNotificaLog
```

---

## 7. Sicurezza e Autenticazione

### 7.1 Autenticazione

**Multi-method Authentication**:

1. **JWT (Primary)** - Frontend React SPA
   - Access token: 1 ora
   - Refresh token: 7 giorni
   - Auto-refresh su 401
   - Storage: localStorage

2. **Token Authentication** - Agent Desktop (external tool)
   - Token persistente
   - Per integrazione desktop app

3. **Session Authentication** - Django Admin
   - Cookie-based
   - Redis session storage

### 7.2 Autorizzazione Base

- **Default**: `IsAuthenticated` su tutte le API
- **RBAC**: Sistema Role-Based Access Control implementato (vedi 7.3)
- **Ownership**: Controlli impliciti nei ViewSets + isolamento dati RBAC

### 7.3 RBAC (Role-Based Access Control)

**Implementazione**: `core` app - `UserProfile` model

#### Gerarchia Ruoli

```python
class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Amministratore'
    MANAGER = 'MANAGER', 'Manager'
    OPERATORE = 'OPERATORE', 'Operatore'
    VIEWER = 'VIEWER', 'Visualizzatore'
```

| Ruolo | Visualizzazione | Creazione | Modifica | Eliminazione | Gestione Utenti |
|-------|----------------|-----------|----------|--------------|-----------------|
| **ADMIN** | Tutti i dati | ✅ | ✅ | ✅ | ✅ |
| **MANAGER** | Tutti i dati | ✅ | ✅ | ✅ | ❌ |
| **OPERATORE** | Solo clienti assegnati | ✅ | ✅ (propri dati) | ❌ | ❌ |
| **VIEWER** | Solo clienti assegnati | ❌ | ❌ | ❌ | ❌ |

#### Modello Dati

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.VIEWER)
    assigned_clients = models.ManyToManyField('anagrafiche.Cliente', blank=True)
    
    @property
    def can_view_all(self):
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def get_accessible_clients_ids(self):
        if self.can_view_all:
            return None  # All clients
        return list(self.assigned_clients.values_list('id', flat=True))
```

**Auto-creazione**: Signal `post_save` User → crea UserProfile (ruolo default: VIEWER)

#### Permission Classes

**RBACPermission** (`core/permissions.py`):
```python
class RBACPermission(BasePermission):
    def has_permission(self, request, view):
        profile = request.user.profile
        
        # Lettura: tutti
        if request.method in SAFE_METHODS:
            return True
        
        # Creazione/Modifica: ADMIN, MANAGER, OPERATORE
        if request.method in ['POST', 'PUT', 'PATCH']:
            return profile.can_create and profile.can_edit
        
        # Eliminazione: solo ADMIN, MANAGER
        if request.method == 'DELETE':
            return profile.can_delete
        
        return False
    
    def has_object_permission(self, request, view, obj):
        profile = request.user.profile
        
        # ADMIN/MANAGER: accesso completo
        if profile.can_view_all:
            return True
        
        # OPERATORE/VIEWER: verifica cliente assegnato
        if request.method in SAFE_METHODS:
            return True
        
        accessible_ids = profile.get_accessible_clients_ids()
        if accessible_ids is None:
            return True
        
        return getattr(obj, 'cliente_id', None) in accessible_ids
```

#### Isolamento Dati

**QuerySet Filtering** nei ViewSets:

```python
class DocumentoViewSet(viewsets.ModelViewSet):
    permission_classes = [RBACPermission]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        if not hasattr(self.request.user, 'profile'):
            return qs.none()
        
        profile = self.request.user.profile
        
        # ADMIN/MANAGER: tutti i documenti
        if profile.can_view_all:
            return qs
        
        # OPERATORE/VIEWER: solo documenti clienti assegnati
        accessible_clients_ids = profile.get_accessible_clients_ids()
        if accessible_clients_ids is not None:
            qs = qs.filter(cliente_id__in=accessible_clients_ids)
        
        return qs
```

**Caso Speciale - Pratiche**:
Gli OPERATORI vedono anche pratiche dove sono **responsabile**:

```python
# PraticaViewSet.get_queryset()
qs = qs.filter(
    Q(cliente_id__in=accessible_clients_ids) |
    Q(responsabile=self.request.user)
)
```

#### Assegnazione Clienti

**Django Admin**:
- Inline `UserProfileInline` in User admin
- Filtro orizzontale per selezione multipla clienti
- Solo ADMIN può modificare ruoli

**API** (futuro):
```python
# ADMIN può assegnare clienti via API
PATCH /api/v1/users/{id}/profile/
{
  "role": "OPERATORE",
  "assigned_clients": [1, 5, 10]
}
```

#### ViewSets con RBAC

Implementato su:
- ✅ `DocumentoViewSet`
- ✅ `FascicoloViewSet`
- ✅ `PraticaViewSet`
- ✅ `AnagraficaViewSet`

#### Testing RBAC

Test completo in `core/tests/test_rbac.py`:
- VIEWER non vede documenti non assegnati ✅
- VIEWER non può creare/modificare ✅
- OPERATORE può creare ma non eliminare ✅
- ADMIN/MANAGER accesso completo ✅

**Referenza**: Guida completa in [`docs/SECURITY_RBAC.md`](./SECURITY_RBAC.md)

### 7.4 CORS

**Development**:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

**Production**:
```python
CORS_ALLOWED_ORIGINS = [
    "https://mygest.secamonline.it",
]
CORS_ALLOW_CREDENTIALS = True
```

### 7.5 CSRF

- **CSRF token**: Letto dal cookie `csrftoken`
- **Header**: `X-CSRFToken` (Axios interceptor)
- **Cookie settings**:
  - `HTTPONLY = False` (leggibile da JavaScript)
  - `SAMESITE = 'Lax'`
  - `SECURE = True` (production HTTPS)

---

## 8. Storage e File Management

### 8.1 NAS Storage (Custom)

**Implementazione**: `mygest.storages.NASPathStorage`

```python
ARCHIVIO_BASE_PATH = "/mnt/archivio"  # Dev: WSL mount
                   # Prod: /srv/mygest/archivio

NAS_STORAGE = FileSystemStorage(location=ARCHIVIO_BASE_PATH)
```

**Struttura NAS**:
```
/mnt/archivio/
├── <CLI_codice>/
│   ├── <Titolario_path>/
│   │   ├── <ANNO>/
│   │   │   ├── Fascicolo_<codice>/
│   │   │   │   ├── documento_001.pdf
│   │   │   │   ├── documento_002.pdf
│   │   │   │   └── subfascicolo_001/
│   │   │   │       └── documento_003.pdf
│   │   │   └── senza_fascicolo/
│   │   │       └── documento_004.pdf
├── ml_models/
│   ├── cedolino_classifier.pkl
│   ├── unilav_extractor.pkl
│   └── vectorizer.pkl
└── importazioni/
    └── temp_uploads/
```

**Pattern Path Documenti**:
```
{CLI}/{TITOLARIO_PATH}/{ANNO}/Fascicolo_{CODICE}/{filename}

Esempio:
MRVLSN65/01_Personale/01_Cedolini/2025/Fascicolo_MRVLSN65-01.01-2025-001/
    CEDOL_123_MRVLSN65_202501_001.pdf
```

### 8.2 Upload Flow

1. **Temporary upload**:
   ```
   MEDIA_ROOT/tmp/<anno>/<CLI>/<original_filename>
   ```

2. **Documento.save()**:
   - Costruisce `path_archivio` basato su titolario/fascicolo
   - Crea directory NAS se non esiste
   - Rinomina file secondo `nome_file_pattern`
   - Sposta file → NAS
   - Aggiorna `Documento.file` → path NAS

3. **Serving**:
   - Dev: Django serve `/archivio/<path>`
   - Prod: Nginx serve statico

### 8.3 Pattern Nome File (Dynamic)

**Configurabile** per tipo documento:

```python
DocumentiTipo.nome_file_pattern = (
    "{tipo.codice}_{id}_{attr:matricola}_{data_documento:%Y%m%d}.pdf"
)

# Cedolino → CEDOL_123_MRVLSN65_20250131.pdf
# Unilav → UNILAV_456_1700026200007595_20250115.pdf
```

**Token supportati**:
- `{id}` - ID documento
- `{tipo.codice}` - Codice tipo
- `{data_documento:%Y%m%d}` - Data formattata
- `{attr:<codice>}` - Attributo dinamico
- `{attr:<codice>.<campo_anagrafica>}` - Attributo nested (es. dipendente.codice)
- `{cliente.<campo>}` - Campo cliente
- `{slug:descrizione}` - Slug da campo
- `{upper:...}` / `{lower:...}` - Transform case
- `{if:attr:<codice>:TESTO}` - Conditional

---

## 9. Cache e Performance

### 9.1 Redis Cache

**2 Redis databases**:
```python
CACHES = {
    'default': {  # API cache
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,  # 5 min
    },
    'session': {  # Django sessions
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'TIMEOUT': 86400,  # 24 ore
    },
}
```

### 9.2 Database Query Optimization

**Connection Pooling**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.postgresql',
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 20,
            'RECYCLE': 3600,
            'PRE_PING': True,
        },
    }
}
```

**Query Optimization** in ViewSets:
```python
queryset = Documento.objects.select_related(
    'cliente', 'fascicolo', 'titolario', 'tipo'
).prefetch_related('allegati', 'attributi')
```

### 9.3 Frontend Caching (React Query)

```typescript
// Default cache time: 5 minuti
const { data } = useQuery({
  queryKey: ['documenti', params],
  queryFn: () => documentiApi.list(params),
  staleTime: 5 * 60 * 1000,
});
```

---

## 10. API Architecture

### 10.1 REST API Design

**Base URL**: `/api/v1/`

**Standard endpoints** (DRF ViewSets):
```
GET    /api/v1/<resource>/              # List
POST   /api/v1/<resource>/              # Create
GET    /api/v1/<resource>/{id}/         # Retrieve
PUT    /api/v1/<resource>/{id}/         # Update
PATCH  /api/v1/<resource>/{id}/         # Partial Update
DELETE /api/v1/<resource>/{id}/         # Delete
```

**Paginazione**:
```json
{
  "count": 150,
  "next": "http://api/v1/documenti/?page=2",
  "previous": null,
  "results": [...]
}
```
- Default: 20 items/page
- Query param: `?page=2`

**Filtri**:
```
GET /api/v1/documenti/?cliente=5&tipo=CEDOL&stato=definitivo
```
- Backend: `django_filters.DjangoFilterBackend`
- Filterset su ogni ViewSet

**Search**:
```
GET /api/v1/documenti/?search=fattura
```
- Backend: `filters.SearchFilter`
- Search fields configurati per modello

**Ordinamento**:
```
GET /api/v1/documenti/?ordering=-data_documento
```
- Backend: `filters.OrderingFilter`

### 10.2 API Endpoints Overview

| Endpoint | ViewSet | Metodi | Descrizione |
|----------|---------|--------|-------------|
| `/api/v1/auth/login/` | - | POST | JWT login |
| `/api/v1/auth/refresh/` | - | POST | JWT refresh |
| `/api/v1/anagrafiche/` | AnagraficaViewSet | CRUD | Anagrafiche |
| `/api/v1/clienti/` | ClienteViewSet | Read | Clienti (read-only) |
| `/api/v1/documenti/` | DocumentoViewSet | CRUD | Documenti |
| `/api/v1/documenti/tipi/` | DocumentiTipoViewSet | Read | Tipi documento |
| `/api/v1/fascicoli/` | FascicoloViewSet | CRUD | Fascicoli |
| `/api/v1/pratiche/` | PraticaViewSet | CRUD | Pratiche |
| `/api/v1/scadenze/` | ScadenzaViewSet | CRUD | Scadenze |
| `/api/v1/protocollo/movimenti/` | MovimentoProtocolloViewSet | Read | Movimenti protocollo |
| `/api/v1/archivio-fisico/unita/` | UnitaFisicaViewSet | CRUD | Unità fisiche |
| `/api/v1/archivio-fisico/operazioni/` | OperazioneArchivioViewSet | CRUD | Operazioni archivio |
| `/api/v1/ai-classifier/predict/` | PredictViewSet | POST | Classificazione AI |
| `/api/v1/ai-classifier/import/` | - | POST | Import documenti AI |

### 10.3 Custom Actions

**ViewSet actions** (@action decorator):

```python
# DocumentoViewSet
@action(detail=True, methods=['post'])
def protocolla(self, request, pk=None):
    """Protocolla documento"""
    
@action(detail=False, methods=['get'])
def statistiche(self, request):
    """Statistiche documenti"""

# FascicoloViewSet
@action(detail=True, methods=['post'])
def collega_documento(self, request, pk=None):
    """Collega documento a fascicolo"""

# ScadenzaViewSet
@action(detail=True, methods=['post'])
def genera_occorrenze(self, request, pk=None):
    """Genera occorrenze future"""
```

### 10.4 GraphQL API (Secondary)

**Endpoint**: `/graphql/`

- **Framework**: Graphene-Django
- **Authentication**: Required (login_required)
- **GraphiQL**: Enabled in DEBUG mode
- **Status**: Legacy (non attivamente sviluppato, focus su REST)

---

## 11. Frontend Architecture

### 11.1 Component Architecture

**Atomic Design Pattern**:

```
components/
├── layout/             # Containers/Layout
│   ├── MainLayout     # Main app shell
│   ├── Sidebar        # Navigation
│   └── Breadcrumbs    # Path navigation
├── common/            # Generic UI components
│   ├── Button
│   ├── Card
│   ├── Table
│   ├── Dialog
│   └── Form controls
└── features/          # Feature-specific (domain)
    ├── DocumentiTable
    ├── FascicoloTree
    ├── ScadenzaCard
    └── PraticaTimeline
```

### 11.2 State Management

**Zustand** (global state):
```typescript
// authStore.ts
export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  login: async (credentials) => { ... },
  logout: () => { ... },
}));
```

**React Query** (server state):
```typescript
// useDocumenti.ts
export const useDocumenti = (params?: Record<string, any>) => {
  return useQuery({
    queryKey: ['documenti', params],
    queryFn: () => documentiApi.list(params),
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

### 11.3 Routing

**React Router v7**:

```typescript
// routes/index.tsx
const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    children: [
      { path: '', element: <DashboardPage /> },
      { path: 'anagrafiche', element: <AnagraficheListPage /> },
      { path: 'anagrafiche/:id', element: <AnagraficaDetailPage /> },
      { path: 'documenti', element: <DocumentiListPage /> },
      { path: 'documenti/:id', element: <DocumentoDetailPage /> },
      // ... etc
    ],
  },
  { path: '/login', element: <LoginPage /> },
]);
```

**Protected Routes**:
```typescript
<Route element={<ProtectedRoute />}>
  <Route path="/" element={<MainLayout />}>
    {/* Protected pages */}
  </Route>
</Route>
```

### 11.4 API Client Layer

**Axios client** with interceptors:

```typescript
// api/client.ts
const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
});

// Request interceptor: add JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: auto-refresh token
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Attempt token refresh
      const refreshToken = localStorage.getItem('refresh_token');
      const { data } = await axios.post('/api/v1/auth/refresh/', {
        refresh: refreshToken,
      });
      localStorage.setItem('access_token', data.access);
      // Retry original request
      return apiClient.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

**Service layer**:
```typescript
// api/documenti.ts
export const documentiApi = {
  list: (params) => apiClient.get('/documenti/', { params }),
  get: (id) => apiClient.get(`/documenti/${id}/`),
  create: (data) => apiClient.post('/documenti/', data),
  update: (id, data) => apiClient.patch(`/documenti/${id}/`, data),
  delete: (id) => apiClient.delete(`/documenti/${id}/`),
};
```

---

## 12. Integrazioni

### 12.1 Email (IMAP/SMTP)

**Configurazione**:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtps.aruba.it'
EMAIL_PORT = 465
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'sandrochimenti@secamonline.it'

EMAIL_IMAP_HOST = 'imaps.aruba.it'
EMAIL_IMAP_PORT = 993
```

**Funzionalità**:
- Invio email transazionali (scadenze, notifiche)
- Import email IMAP → Comunicazione
- Salvataggio email inviate su IMAP (cartella "Inviati")
- Blacklist email (filtro anti-spam)

### 12.2 WhatsApp (Cloud API)

**Configurazione**:
```python
WHATSAPP_CLOUD_API_VERSION = 'v20.0'
WHATSAPP_CLOUD_BASE_URL = 'https://graph.facebook.com'
WHATSAPP_CLOUD_PHONE_NUMBER_ID = '<phone_id>'
WHATSAPP_CLOUD_ACCESS_TOKEN = '<token>'
```

**Funzionalità**:
- Invio messaggi WhatsApp (alert scadenze)
- Webhook receiver (messaggi in arrivo)
- Template messaging

### 12.3 Google Calendar

**Configurazione**:
```python
GOOGLE_CALENDAR_CREDENTIALS_FILE = '/path/to/google_credentials.json'
GOOGLE_CALENDAR_DEFAULT_ID = '<calendar_id>@group.calendar.google.com'
```

**Funzionalità**:
- Sync scadenze → Google Calendar
- Management command: `sync_google_calendar`

### 12.4 AI/ML (Local)

**Framework**: scikit-learn + joblib

**Modelli**:
1. **Document Classifier** (tipo documento)
   - Input: testo estratto da PDF/OCR
   - Output: tipo documento + confidence
   - Storage: `/mnt/archivio/ml_models/classifier.pkl`

2. **Field Extractor** (campi dinamici)
   - Input: testo documento
   - Output: dizionario campi (es. cedolino → matricola, mese, importo)
   - Template-based extraction zones

**Training**:
- Supervised: esempi da `TrainingExample`
- Feedback loop: `AIPredictionFeedback`
- Retrain: `python manage.py retrain_classifier`

---

## 13. Deployment

### 13.1 Infrastructure

**VPS Hostinger**:
- IP: `72.62.34.249`
- User: `mygest`
- Path: `/srv/mygest/app`

**Nginx**:
- Reverse proxy porta 80/443
- Serve static files (`/static/`, `/media/`)
- Proxy pass `/api/` → Gunicorn

**Gunicorn**:
- Workers: 4 (CPU cores * 2)
- Bind: `127.0.0.1:8000`
- Worker class: `sync`

**systemd**:
- Service: `mygest.service`
- Auto-restart on failure
- Logging: `/var/log/mygest/`

### 13.2 Deploy Process

**Script**: `/srv/mygest/app/scripts/deploy.sh`

```bash
#!/bin/bash
cd /srv/mygest/app

# Git pull
git pull origin main

# Backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Frontend
cd frontend
npm install
npm run build
cd ..

# Restart services
sudo systemctl restart mygest
sudo systemctl reload nginx
```

### 13.3 Environment Variables

**Production** (`.env`):
```bash
DEBUG=False
SECRET_KEY=<random_secret_key>
ALLOWED_HOSTS=mygest.secamonline.it,72.62.34.249

DATABASE_URL=postgresql://user:pass@localhost:5432/mygest
REDIS_URL=redis://127.0.0.1:6379/1

ARCHIVIO_BASE_PATH=/srv/mygest/archivio

EMAIL_HOST_USER=<email>
EMAIL_HOST_PASSWORD=<password>

OPENAI_API_KEY=<key>  # Se usato
```

### 13.4 Backup Strategy

**Database**:
```bash
# Daily cron
pg_dump mygest > /backups/mygest_$(date +%Y%m%d).sql
```

**NAS Files**:
```bash
# Weekly rsync to external storage
rsync -av /srv/mygest/archivio/ /mnt/backup/archivio/
```

---

## Conclusioni

MyGest è un sistema **moderno**, **scalabile** e **ben architettato** che segue best practice:

✅ **Separazione frontend/backend** (SPA + REST API)  
✅ **Modularità** (Django apps isolate per dominio)  
✅ **Type safety** (TypeScript frontend)  
✅ **Caching multi-livello** (Redis + React Query)  
✅ **Storage personalizzato** (NAS con pattern intelligenti)  
✅ **Autenticazione robusta** (JWT + multi-method)  
✅ **ML integrato** (classificazione locale senza dipendenze cloud)  
✅ **Performance** (Connection pooling, query optimization)  
✅ **Deployment automatizzato** (systemd + script)

### Aree di Miglioramento

1. **Task Queue**: Implementare Celery per task asincroni (import, ML training)
2. **Testing**: Aumentare coverage (attualmente parziale)
3. **Monitoring**: Aggiungere Sentry/Prometheus per error tracking
4. **CI/CD**: Pipeline automatizzata (GitHub Actions)
5. **Documentazione API**: OpenAPI/Swagger spec

---

**Documento generato automaticamente il 3 Marzo 2026**  
**Ultima revisione RBAC**: Gennaio 2026 (RBAC implementato e documentato)
