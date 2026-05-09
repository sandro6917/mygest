# Tech Debt Inventory - MyGest DMS

**Data**: 3 Marzo 2026  
**Versione**: 1.0  
**Owner**: Engineering Team  

---

## 📋 Executive Summary

Questo documento traccia il **debito tecnico** accumulato nel progetto MyGest, categorizzato per area e priorità di remediation.

**Total Tech Debt**: ~**18 settimane** sviluppo (2 dev full-time)  
**Interest Rate**: ~**20% velocity loss** per manutenzione/workaround  
**Break-Even Point**: Remediation entro Q2 2026 per evitare bankruptcy tecnico in V1.0

---

## 🏗️ Code Debt (Qualità Codice)

### TD-001: Validazione Business Rules in `clean()` ma Non DB

**Categoria**: Data Integrity  
**Severity**: 🟠 High  
**Effort**: 3 giorni  
**Interest**: Bug data integrity in produzione

**Problema**:
Business rules validate solo in `Model.clean()` (Python), non a livello DB constraint.

**Esempio**:
```python
# documenti/models.py:738
def clean(self):
    if self.digitale and self.ubicazione_id:
        raise ValidationError("Documenti digitali non possono avere ubicazione")
```

**Rischio**: Se bypass Django ORM (bulk_create, raw SQL, app esterna) → data corruption.

**Remediation**:
```python
# Aggiungere CheckConstraint nel Meta
class Documento(models.Model):
    # ...
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(digitale=True, ubicazione__isnull=False),
                name='digitale_no_ubicazione'
            )
        ]
```

**File interessati**: `documenti/models.py`, `fascicoli/models.py`, `pratiche/models.py`

---

### TD-002: Exception Handling Generico

**Categoria**: Error Handling  
**Severity**: 🟡 Medium  
**Effort**: 2 giorni  
**Interest**: Debugging difficile, errori mascherati

**Problema**:
Uso diffuso di `except Exception` senza logging/re-raise specifico.

**Esempio**:
```python
# documenti/import_cedolini.py:126
try:
    # ... logica complessa
except Exception as e:
    error_msg = f"Errore: {e}"
    logger.error(error_msg, exc_info=True)
    # ❌ Continua silenziosamente, potenziale data inconsistency
```

**Remediation**:
```python
try:
    # ... logica complessa
except SpecificError as e:
    # Handle specifico
    raise
except Exception as e:
    logger.exception("Unexpected error in import")
    raise  # ✅ Re-raise per visibilità
```

**Pattern da applicare**: Tutti i `try/except` in `documenti/`, `ai_classifier/`, `protocollo/`

---

### TD-003: Query N+1 Non Sistematici

**Categoria**: Performance  
**Severity**: 🟡 Medium  
**Effort**: 3 giorni  
**Interest**: API slowdown con dataset grandi

**Problema**:
`select_related`/`prefetch_related` non applicati sistematicamente nei ViewSet.

**Esempio**:
```python
# api/v1/documenti/views.py (ipotetico)
class DocumentoViewSet(viewsets.ModelViewSet):
    queryset = Documento.objects.all()  # ❌ N+1 su cliente, fascicolo, titolario
```

**Dovrebbe essere**:
```python
queryset = Documento.objects.select_related(
    'cliente', 'fascicolo', 'titolario', 'tipo_documento'
).prefetch_related('attributi_valori__definizione')
```

**Remediation**:
1. Audit con Django Debug Toolbar
2. Aggiungere `select_related` in tutti i ViewSet
3. Test caricamento con 10k+ records

**File interessati**: Tutti i ViewSet in `api/v1/*/views.py`

---

### TD-004: Codice Duplicato Pattern Naming

**Categoria**: DRY Violation  
**Severity**: 🟢 Low  
**Effort**: 2 giorni  
**Interest**: Manutenzione multipla per same logic

**Problema**:
Logica generazione codici documenti/fascicoli/pratiche duplicata in ogni model.

**Esempio**:
```python
# documenti/models.py
def generate_codice(self):
    # Logica pattern CLI-TIT-ANNO-SEQ
    
# fascicoli/models.py
def generate_codice(self):
    # Stessa logica con varianti
    
# pratiche/models.py
def generate_codice(self):
    # Ancora stessa logica
```

**Remediation**:
```python
# core/utils/codice_generator.py
class CodiceGenerator:
    @staticmethod
    def generate(pattern, context):
        """Generate codice from pattern template"""
        # Logica unificata
        return pattern.format(**context)
```

**Benefit**: Single source of truth, testabile isolatamente

---

### TD-005: String Literals Magic Values

**Categoria**: Maintainability  
**Severity**: 🟢 Low  
**Effort**: 1 giorno  
**Interest**: Typo bugs, refactoring difficile

**Problema**:
Stati, tipi, codici hardcoded come string literals invece di constants/enums.

**Esempio**:
```python
# documenti/models.py (ipotetico)
if documento.stato == "definitivo":  # ❌ Magic string
    # ...
```

**Remediation**:
```python
# documenti/constants.py
class DocumentoStato(models.TextChoices):
    BOZZA = 'bozza', 'Bozza'
    DEFINITIVO = 'definitivo', 'Definitivo'
    ARCHIVIATO = 'archiviato', 'Archiviato'

# Usage
if documento.stato == DocumentoStato.DEFINITIVO:  # ✅ Type-safe
```

**File interessati**: Tutti i models con `choices` inline

---

## 🏛️ Architecture Debt

### TD-006: Storage Logic Tight Coupling

**Categoria**: Architecture  
**Severity**: 🟠 High  
**Effort**: 5 giorni  
**Interest**: Impossibile cambio storage backend

**Problema**:
Logica path NAS accoppiata strettamente a `FilePathField`, impossibile migrare a S3/MinIO.

**Evidenza**:
```python
# documenti/models.py
file = models.FileField(storage=NASPathStorage())  # ❌ Hardcoded NAS

# fascicoli/utils.py
def ensure_archivio_path(...):
    full_path = Path(settings.ARCHIVIO_BASE_PATH) / ...  # ❌ Assume filesystem
    full_path.mkdir(...)  # ❌ Crash se S3
```

**Remediation**:
```python
# mygest/storages.py
class AbstractArchivioStorage(ABC):
    @abstractmethod
    def save(self, name, content): pass
    @abstractmethod
    def url(self, name): pass

class NASStorage(AbstractArchivioStorage):
    # Implementazione filesystem

class S3Storage(AbstractArchivioStorage):
    # Implementazione S3

# settings.py
ARCHIVIO_STORAGE = 'mygest.storages.NASStorage'  # Configurabile
```

**Benefit**: Plug-and-play storage backend, cloud migration ready

---

### TD-007: Monolithic Settings File

**Categoria**: Configuration Management  
**Severity**: 🟡 Medium  
**Effort**: 1 giorno  
**Interest**: Merge conflicts, setting override complesso

**Problema**:
`settings.py` monolitico (544 linee) con configurazione inline.

**Remediation**:
```python
# mygest/settings/
├── __init__.py        # Import environment-specific
├── base.py            # Settings comuni
├── development.py     # Dev overrides
├── production.py      # Prod overrides
└── testing.py         # Test overrides

# mygest/settings/__init__.py
import os
env = os.getenv('DJANGO_ENV', 'development')
if env == 'production':
    from .production import *
elif env == 'testing':
    from .testing import *
else:
    from .development import *
```

---

### TD-008: Frontend State Management Inconsistente

**Categoria**: Frontend Architecture  
**Severity**: 🟡 Medium  
**Effort**: 3 giorni  
**Interest**: Bug state sync, performance issues

**Problema** (assunto da best practices):
Mix di Zustand (auth) e React Query (data) senza pattern chiaro quando usare cosa.

**Remediation**:
```
Regola:
- Zustand: Global UI state (auth, theme, sidebar)
- React Query: Server state (cache API data)
- useState: Local component state
```

**Documentare in**: `frontend/docs/STATE_MANAGEMENT.md`

---

## 🗄️ Data Debt

### TD-009: Migration Squashing Non Fatto

**Categoria**: Database  
**Severity**: 🟢 Low  
**Effort**: 2 giorni  
**Interest**: Slow migration apply, developer onboarding lento

**Problema**:
100+ migration files accumulati, alcuni obsoleti.

**Remediation**:
```bash
# Squash migrations fino a baseline stabile
python manage.py squashmigrations documenti 0001 0050 --squashed-name baseline_2024

# Rimuovere migrations pre-squash dopo deploy produzione
```

**Benefit**: Onboarding nuovo dev da 30min → 5min (migration apply time)

---

### TD-010: Index Mancanti su Foreign Keys

**Categoria**: Performance  
**Severity**: 🟡 Medium  
**Effort**: 1 giorno  
**Interest**: Slow queries su JOIN

**Problema**:
Non tutti i FK hanno index espliciti (Django li crea auto, ma meglio esplicito).

**Remediation**:
```python
# documenti/models.py
class Meta:
    indexes = [
        models.Index(fields=['cliente', 'data_documento']),  # Query comuni
        models.Index(fields=['tipo_documento', 'stato']),
        models.Index(fields=['fascicolo', 'digitale']),
    ]
```

**Audit**:
```sql
-- Query slow query log PostgreSQL
SELECT * FROM pg_stat_user_tables WHERE seq_scan > idx_scan;
```

---

### TD-011: Soft Delete Non Implementato

**Categoria**: Data Recovery  
**Severity**: 🟡 Medium  
**Effort**: 4 giorni  
**Interest**: Data loss irrecuperabile

**Problema**:
Hard delete con CASCADE → dati persi permanentemente.

**Remediation**:
```python
# core/models.py
class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Include deleted
    
    def delete(self, hard=False):
        if hard:
            super().delete()
        else:
            self.deleted_at = timezone.now()
            self.save()
    
    class Meta:
        abstract = True

# Usage
class Documento(SoftDeleteModel):
    # ...
```

---

## 🧪 Test Debt

### TD-012: Test Coverage Disomogenea

**Categoria**: Testing  
**Severity**: 🟠 High  
**Effort**: 10 giorni  
**Interest**: Bug produzione, refactoring rischioso

**Problema**:
Coverage varia wildly per app (stimato):
- ✅ `anagrafiche/`: ~70%
- ⚠️ `documenti/`: ~50%
- ❌ `protocollo/`: ~20%
- ❌ `ai_classifier/`: ~30%

**Remediation**:
```bash
# Baseline coverage attuale
pytest --cov=. --cov-report=html --cov-report=term

# Target per app
- documenti: 75% (core business logic)
- protocollo: 90% (critical compliance)
- ai_classifier: 60% (ML non deterministico)
```

**Priorità test mancanti**:
1. ✅ Protocollazione concorrente (race conditions)
2. ✅ Validazioni business rules
3. ✅ AI classifier edge cases
4. ⚠️ Integration test API completi

---

### TD-013: Integration Test Mancanti

**Categoria**: Testing  
**Severity**: 🟡 Medium  
**Effort**: 5 giorni  
**Interest**: Bug integration solo in produzione

**Problema**:
Molti unit test, pochi integration test end-to-end.

**Remediation**:
```python
# tests/integration/test_documento_workflow.py
def test_documento_full_lifecycle(api_client, cliente):
    """Test: Upload → Classificazione AI → Protocollazione → Archivio"""
    # 1. Upload documento
    response = api_client.post('/api/v1/documenti/', {...})
    doc_id = response.data['id']
    
    # 2. AI Classification
    response = api_client.post(f'/api/v1/documenti/{doc_id}/classify/')
    assert response.data['tipo'] == 'FAT'
    
    # 3. Protocollazione
    response = api_client.post(f'/api/v1/protocollo/entrata/', {...})
    assert response.data['numero_protocollo'].startswith('PROT-')
    
    # 4. Movimentazione archivio fisico
    response = api_client.post('/api/v1/archivio-fisico/operazioni/', {...})
    assert response.status_code == 201
```

---

### TD-014: Test Fixtures Duplicati

**Categoria**: Test Maintainability  
**Severity**: 🟢 Low  
**Effort**: 2 giorni  
**Interest**: Manutenzione test lenta

**Problema**:
Ogni test file ricrea fixture comuni invece di riutilizzare.

**Remediation**:
```python
# conftest.py (già presente, ma estendere)
@pytest.fixture
def documento_base(cliente, tipo_documento):
    """Documento standard per test"""
    return baker.make('documenti.Documento',
        cliente=cliente,
        tipo_documento=tipo_documento,
        digitale=True
    )

# Usage in test
def test_protocollazione(documento_base):
    # Riutilizza fixture invece di ricreare
```

---

## 📚 Documentation Debt

### TD-015: API Documentation Obsoleta

**Categoria**: Documentation  
**Severity**: 🟡 Medium  
**Effort**: 3 giorni  
**Interest**: Developer onboarding lento

**Problema**:
Nessun Swagger/OpenAPI docs aggiornato automaticamente.

**Remediation**:
```python
# requirements.txt
drf-spectacular==0.27.0

# mygest/settings.py
INSTALLED_APPS += ['drf_spectacular']

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# mygest/urls.py
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

**Access**: `http://localhost:8000/api/docs/` → Interactive Swagger UI

---

### TD-016: Inline Comments in Italian vs Code in English

**Categoria**: Code Consistency  
**Severity**: 🟢 Low  
**Effort**: 1 giorno  
**Interest**: Confusione team internazionale

**Problema**:
Mix di commenti italiani e codice/docstring inglesi.

```python
# Esempio misto
def generate_codice(self):
    """Generate unique document code"""  # ✅ English
    # Genera codice con pattern CLI-TIT-ANNO  # ❌ Italian
```

**Decisione strategica necessaria**:
- **Opzione A**: All English (international team ready)
- **Opzione B**: All Italian (stakeholder locale)

---

### TD-017: ADR (Architecture Decision Records) Assenti

**Categoria**: Knowledge Management  
**Severity**: 🟡 Medium  
**Effort**: Ongoing  
**Interest**: Decisioni architetturali perse nella storia

**Problema**:
Nessuna documentazione del "perché" di scelte architetturali.

**Esempi decisioni non documentate**:
- Perché NAS invece di S3?
- Perché ML locale invece di cloud API?
- Perché JWT + Token + Session auth tutte insieme?

**Remediation**:
```markdown
# docs/adr/001-storage-nas-vs-s3.md

# ADR 001: NAS Local Storage vs Cloud S3

## Status
Accepted

## Context
Documenti sensibili (buste paga, CF) richiedono compliance GDPR.
Cloud storage richiede data processing agreement con provider.

## Decision
Usare NAS locale `/mnt/archivio` per data sovereignty.

## Consequences
- ✅ Compliance GDPR (dati on-premise)
- ✅ Zero costi storage ricorrenti
- ❌ Scalabilità limitata (capacity NAS)
- ❌ Backup manuale richiesto

## Alternatives Considered
- AWS S3 (rejected: GDPR complexity)
- MinIO self-hosted (future migration path)
```

---

## 🔧 Process Debt

### TD-018: Code Review Non Sistematico

**Categoria**: Quality Process  
**Severity**: 🟠 High  
**Effort**: 0 (process change)  
**Interest**: Bug in produzione, knowledge silos

**Problema**:
Commit diretti su `main` senza review (evidenza da git log).

**Remediation**:
1. **Branch protection**:
   ```yaml
   # GitHub settings
   - Require pull request before merge
   - Require 1 approval
   - Require status checks (CI) to pass
   ```

2. **PR Template**:
   ```markdown
   ## Descrizione
   <!-- Cosa fa questa PR? -->
   
   ## Checklist
   - [ ] Test aggiunti/aggiornati
   - [ ] Docs aggiornati
   - [ ] Migration create (se modelli cambiati)
   - [ ] Backward compatible
   ```

---

### TD-019: Dependency Updates Manuali

**Categoria**: Security  
**Severity**: 🟡 Medium  
**Effort**: 1 giorno setup  
**Interest**: Vulnerabilità note in dipendenze

**Problema**:
`requirements.txt` con versioni pinned, nessun update automatico.

**Remediation**:
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    reviewers:
      - "engineering-team"
    labels:
      - "dependencies"
```

**Benefit**: Security patches automatici via PR

---

### TD-020: Feature Flags Assenti

**Categoria**: Deployment  
**Severity**: 🟢 Low  
**Effort**: 2 giorni  
**Interest**: Rollback richiede re-deploy

**Problema**:
Nuove feature rilasciate all-or-nothing, no gradual rollout.

**Remediation**:
```python
# core/feature_flags.py
from django.conf import settings

FLAGS = {
    'AI_CLASSIFIER_ENABLED': True,
    'PORTAL_CLIENTI_ENABLED': False,  # V1.0 not ready
    'VERSIONING_ENABLED': False,
}

def is_enabled(flag_name):
    # Override da env var
    env_val = os.getenv(f'FEATURE_{flag_name}')
    if env_val:
        return env_val.lower() in ('true', '1', 'yes')
    return FLAGS.get(flag_name, False)

# Usage
if is_enabled('AI_CLASSIFIER_ENABLED'):
    resultado = classify_document(doc)
```

---

## 📊 Debt Metrics

### Quantificazione Debito

| Categoria | # Items | Total Effort | Interest Rate |
|-----------|---------|--------------|---------------|
| Code Debt | 5 | 11 giorni | 10% velocity loss |
| Architecture | 3 | 9 giorni | 15% rigidità |
| Data Debt | 3 | 7 giorni | 5% perf degradation |
| Test Debt | 3 | 17 giorni | 20% bug escape |
| Documentation | 3 | 5 giorni | 30% onboarding time |
| Process | 3 | 3 giorni | 15% deployment risk |
| **TOTAL** | **20** | **~52 giorni** | **~20% avg** |

**Conversione**: 52 giorni × 2 dev = ~**10 settimane** full-time

---

## 🎯 Prioritization Matrix

```
Impact vs Effort
│
High ├─ TD-001, TD-006, TD-012 ◄─ Quick Wins
     │
     ├─ TD-008, TD-010, TD-018 ◄─ Strategic Investments
     │
Low  ├─ TD-004, TD-005, TD-014 ◄─ Nice to Have
     │
     └──────────────────────────────
        Low           High (Effort)
```

---

## 📅 Remediation Roadmap

### Q2 2026 (Debt Reduction Sprint)

**Week 1-2**: Code Quality
- TD-001: DB constraints (3d)
- TD-002: Exception handling (2d)
- TD-003: Query optimization (3d)

**Week 3-4**: Architecture
- TD-006: Storage abstraction (5d)
- TD-010: DB indexes (1d)

**Week 5-6**: Testing
- TD-012: Coverage baseline 80% (10d)

**Total**: 24 giorni → 20% debt reduction

### Q3 2026 (Continuous Debt Payment)

**Allocare 20% sprint capacity** a debt remediation ogni sprint.

**Formula**:
```
Velocity = 40 SP/sprint
Debt budget = 8 SP/sprint (20%)
Feature budget = 32 SP/sprint (80%)
```

---

## 🔄 Debt Prevention

### Engineering Standards

1. **Definition of Done** checklist:
   - [ ] Test coverage ≥80% for new code
   - [ ] Migration included (if model changed)
   - [ ] API docs updated (Swagger)
   - [ ] Code review approved
   - [ ] No new lint warnings

2. **Debt Review Quarterly**:
   - Q1, Q2, Q3, Q4: Team review di questo documento
   - Aggiornare metriche, riprioritizzare

3. **Boy Scout Rule**:
   > "Leave code better than you found it"
   
   Ogni PR dovrebbe migliorare qualcosa oltre la feature.

---

**Owner**: Engineering Team  
**Review Cycle**: Quarterly  
**Next Review**: Q2 2026

**Documenti correlati**:
- [GAP_ANALYSIS.md](GAP_ANALYSIS.md) - Gap prodotto vs implementazione
- [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md) - Security audit
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architettura target
