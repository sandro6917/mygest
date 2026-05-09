# RBAC Testing Guide

**Data**: 3 Marzo 2026  
**Versione**: 1.0  
**Target**: RBAC Implementation (13 ViewSet)

---

## 🎯 Obiettivo

Validare che l'implementazione RBAC funzioni correttamente per tutti i 13 ViewSet modificati, garantendo:

1. **Data Isolation**: Utenti vedono solo i dati dei clienti assegnati
2. **Role-Based Access**: ADMIN/MANAGER/OPERATORE/VIEWER hanno permessi corretti
3. **Performance**: Nessun N+1 query, filtri ottimizzati
4. **Consistency**: Comportamento uniforme su tutti gli endpoint

---

## 📋 Setup Test Environment

### 1. Crea Utenti Test

```python
# management/commands/create_rbac_test_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import UserProfile
from anagrafiche.models import Cliente

User = get_user_model()

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # ADMIN - vede tutti i clienti
        admin_user = User.objects.create_user(
            username='admin_test',
            password='Test123!',
            email='admin@test.com',
            is_staff=True
        )
        UserProfile.objects.create(
            user=admin_user,
            ruolo='ADMIN',
            # assigned_clients vuoto → vede tutti
        )
        
        # OPERATORE - vede solo 3 clienti
        operatore_user = User.objects.create_user(
            username='operatore_test',
            password='Test123!',
            email='operatore@test.com'
        )
        operatore_profile = UserProfile.objects.create(
            user=operatore_user,
            ruolo='OPERATORE'
        )
        # Assegna 3 clienti specifici
        clienti = Cliente.objects.all()[:3]
        operatore_profile.assigned_clients.set(clienti)
        
        # VIEWER - vede solo 1 cliente
        viewer_user = User.objects.create_user(
            username='viewer_test',
            password='Test123!',
            email='viewer@test.com'
        )
        viewer_profile = UserProfile.objects.create(
            user=viewer_user,
            ruolo='VIEWER'
        )
        viewer_profile.assigned_clients.set([clienti[0]])
        
        self.stdout.write(self.style.SUCCESS('Utenti test creati con successo'))
```

**Run**:
```bash
python manage.py create_rbac_test_users
```

---

## 🧪 Test Template

### Test Unitario Generico

```python
# api/v1/tests/test_rbac_viewsets.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import UserProfile
from anagrafiche.models import Cliente

User = get_user_model()

@pytest.fixture
def admin_client(db):
    """Client autenticato come ADMIN (vede tutti)"""
    user = User.objects.create_user(username='admin', password='test')
    profile = UserProfile.objects.create(user=user, ruolo='ADMIN')
    
    client = APIClient()
    client.force_authenticate(user=user)
    return client, profile

@pytest.fixture
def operatore_client(db):
    """Client autenticato come OPERATORE (vede solo assigned_clients)"""
    user = User.objects.create_user(username='operatore', password='test')
    profile = UserProfile.objects.create(user=user, ruolo='OPERATORE')
    
    # Assegna 2 clienti
    clienti = Cliente.objects.all()[:2]
    profile.assigned_clients.set(clienti)
    
    client = APIClient()
    client.force_authenticate(user=user)
    return client, profile

@pytest.fixture
def viewer_client(db):
    """Client autenticato come VIEWER (read-only)"""
    user = User.objects.create_user(username='viewer', password='test')
    profile = UserProfile.objects.create(user=user, ruolo='VIEWER')
    
    # Assegna 1 cliente
    cliente = Cliente.objects.first()
    profile.assigned_clients.set([cliente])
    
    client = APIClient()
    client.force_authenticate(user=user)
    return client, profile

@pytest.mark.django_db
class TestClienteViewSetRBAC:
    """Test RBAC per ClienteViewSet"""
    
    def test_admin_sees_all_clients(self, admin_client):
        """ADMIN vede tutti i clienti"""
        client, profile = admin_client
        
        total_clients = Cliente.objects.count()
        response = client.get('/api/v1/anagrafiche/clienti/')
        
        assert response.status_code == 200
        assert len(response.data) == total_clients
    
    def test_operatore_sees_only_assigned_clients(self, operatore_client):
        """OPERATORE vede solo i clienti assegnati"""
        client, profile = operatore_client
        
        assigned_count = profile.assigned_clients.count()
        response = client.get('/api/v1/anagrafiche/clienti/')
        
        assert response.status_code == 200
        assert len(response.data) == assigned_count
        
        # Verifica che siano esattamente i clienti assegnati
        returned_ids = {c['id'] for c in response.data}
        expected_ids = set(profile.assigned_clients.values_list('id', flat=True))
        assert returned_ids == expected_ids
    
    def test_viewer_sees_only_assigned_clients(self, viewer_client):
        """VIEWER vede solo i clienti assegnati (1)"""
        client, profile = viewer_client
        
        response = client.get('/api/v1/anagrafiche/clienti/')
        
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == profile.assigned_clients.first().id
    
    def test_viewer_cannot_create_client(self, viewer_client):
        """VIEWER non può creare clienti (read-only)"""
        client, profile = viewer_client
        
        response = client.post('/api/v1/anagrafiche/clienti/', {
            'anagrafica': {
                'nome': 'Test Cliente',
                'tipo': 'PF'
            }
        })
        
        assert response.status_code == 403  # Forbidden
```

---

## 🧪 Test per Tutti i ViewSet (Checklist)

### ✅ Critical ViewSet (7)

#### 1. ClienteViewSet
```bash
pytest api/v1/anagrafiche/tests/test_rbac_cliente.py -v
```

**Test Cases**:
- [x] ADMIN vede tutti i clienti
- [x] OPERATORE vede solo assigned_clients
- [x] VIEWER vede solo assigned_clients (read-only)
- [x] VIEWER non può modificare/eliminare

---

#### 2-4. ScadenzaViewSet, ScadenzaOccorrenzaViewSet, ScadenzaAlertViewSet
```bash
pytest api/v1/scadenze/tests/test_rbac_scadenze.py -v
```

**Test Cases**:
- [x] ADMIN vede tutte le scadenze
- [x] OPERATORE vede solo scadenze collegate a pratiche/fascicoli/documenti dei suoi clienti
- [x] VIEWER read-only
- [x] Filtro via M2M (pratiche, fascicoli, documenti) funziona
- [x] Nessun duplicato (`.distinct()` applicato)

**Test Specifico**:
```python
@pytest.mark.django_db
def test_scadenza_filtering_via_pratica(operatore_client):
    """Test filtro scadenza via pratica → cliente"""
    client, profile = operatore_client
    
    # Crea pratica per cliente assegnato
    cliente_assegnato = profile.assigned_clients.first()
    pratica = Pratica.objects.create(
        cliente=cliente_assegnato,
        titolo='Pratica Test'
    )
    
    # Crea scadenza collegata a pratica
    scadenza = Scadenza.objects.create(titolo='Scadenza Test')
    scadenza.pratiche.add(pratica)
    
    # Crea pratica per cliente NON assegnato
    cliente_non_assegnato = Cliente.objects.exclude(
        id__in=profile.assigned_clients.values_list('id', flat=True)
    ).first()
    pratica_altra = Pratica.objects.create(
        cliente=cliente_non_assegnato,
        titolo='Pratica Altra'
    )
    scadenza_altra = Scadenza.objects.create(titolo='Scadenza Altra')
    scadenza_altra.pratiche.add(pratica_altra)
    
    # Test: operatore vede solo scadenza del suo cliente
    response = client.get('/api/v1/scadenze/scadenze/')
    
    assert response.status_code == 200
    returned_ids = {s['id'] for s in response.data['results']}
    assert scadenza.id in returned_ids
    assert scadenza_altra.id not in returned_ids
```

---

#### 5. DocumentoTracciabileViewSet
```bash
pytest api/v1/archivio_fisico/tests/test_rbac_documenti_tracciabili.py -v
```

**Test Cases**:
- [x] ADMIN vede tutti i documenti tracciabili
- [x] OPERATORE vede solo documenti dei suoi clienti
- [x] Filtro `cliente_id__in` funziona

---

#### 6. MovimentoProtocolloViewSet
```bash
pytest api/v1/protocollo/tests/test_rbac_protocollo.py -v
```

**Test Cases**:
- [x] ADMIN vede tutti i movimenti
- [x] OPERATORE vede solo movimenti dei suoi clienti
- [x] Filtro `cliente_id__in` applicato prima dei filtri custom

---

#### 7. OperazioneArchivioViewSet
```bash
pytest api/v1/archivio_fisico/tests/test_rbac_operazioni.py -v
```

**Test Cases**:
- [x] ADMIN vede tutte le operazioni
- [x] OPERATORE vede solo operazioni con righe collegate a documenti/fascicoli dei suoi clienti
- [x] Filtro via `righe` → `documento/fascicolo` → `cliente` funziona
- [x] `.distinct()` evita duplicati

**Test Query Performance**:
```python
from django.test.utils import override_settings
from django.db import connection
from django.test import TestCase

@override_settings(DEBUG=True)
def test_operazione_archivio_no_n_plus_1(operatore_client):
    """Verifica nessun N+1 query"""
    client, profile = operatore_client
    
    # Reset query counter
    from django.db import reset_queries
    reset_queries()
    
    # Request API
    response = client.get('/api/v1/archivio-fisico/operazioni/')
    
    # Verifica numero query
    queries = len(connection.queries)
    print(f"Numero query: {queries}")
    
    # Dovrebbe essere < 10 query (select_related + prefetch_related)
    assert queries < 10, f"Troppe query: {queries}"
```

---

### ✅ High Priority ViewSet (4)

#### 8. PraticaNotaViewSet
```bash
pytest api/v1/pratiche/tests/test_rbac_note.py -v
```

**Test Cases**:
- [x] OPERATORE vede solo note di pratiche dei suoi clienti
- [x] Filtro `pratica__cliente_id__in` funziona

---

#### 9. UnitaFisicaViewSet
```bash
pytest api/v1/archivio_fisico/tests/test_rbac_unita.py -v
```

**Test Cases**:
- [x] ADMIN/MANAGER possono create/update/delete
- [x] OPERATORE/VIEWER possono solo leggere
- [x] Nessun filtro cliente (metadata condiviso)

**Test Permissions**:
```python
def test_operatore_cannot_create_unita(operatore_client):
    """OPERATORE non può creare unità fisiche"""
    client, profile = operatore_client
    
    response = client.post('/api/v1/archivio-fisico/unita/', {
        'codice': 'TEST',
        'nome': 'Test Unità',
        'tipo': 'mobile'
    })
    
    # RBACPermission dovrebbe negare (solo ADMIN/MANAGER)
    assert response.status_code == 403
```

---

#### 10. RigaOperazioneArchivioViewSet
```bash
pytest api/v1/archivio_fisico/tests/test_rbac_righe.py -v
```

**Test Cases**:
- [x] OPERATORE vede solo righe con documenti/fascicoli dei suoi clienti
- [x] Filtro via Q objects funziona

---

#### 11. ImportSessionViewSet
```bash
pytest api/v1/documenti/tests/test_rbac_import.py -v
```

**Test Cases**:
- [x] Utente vede solo le proprie sessioni (filter `utente=request.user`)
- [x] RBACPermission applicato

---

### ✅ Medium Priority ViewSet (2)

#### 12. CollocazioneFisicaViewSet
```bash
pytest api/v1/archivio_fisico/tests/test_rbac_collocazioni.py -v
```

**Test Cases**:
- [x] OPERATORE vede solo collocazioni di documenti dei suoi clienti
- [x] Filtro `documento__cliente_id__in` funziona

---

#### 13. DocumentPredictionViewSet
```bash
pytest api/v1/ai_classifier/tests/test_rbac_predictions.py -v
```

**Test Cases**:
- [x] OPERATORE vede solo predizioni di documenti dei suoi clienti
- [x] Filtro `documento__cliente_id__in` funziona

---

## 🔍 Integration Tests

### Test End-to-End Workflow

```python
@pytest.mark.django_db
def test_operatore_workflow_complete():
    """Test workflow completo operatore: crea pratica, scadenza, documento"""
    
    # Setup
    user = User.objects.create_user(username='op', password='test')
    profile = UserProfile.objects.create(user=user, ruolo='OPERATORE')
    cliente = Cliente.objects.first()
    profile.assigned_clients.set([cliente])
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    # 1. Create Pratica (del suo cliente)
    response = client.post('/api/v1/pratiche/pratiche/', {
        'cliente': cliente.id,
        'titolo': 'Pratica Test',
        'tipo': 'GEN'
    })
    assert response.status_code == 201
    pratica_id = response.data['id']
    
    # 2. Create Scadenza collegata a pratica
    response = client.post('/api/v1/scadenze/scadenze/', {
        'titolo': 'Scadenza Test',
        'pratiche': [pratica_id]
    })
    assert response.status_code == 201
    scadenza_id = response.data['id']
    
    # 3. Verifica che veda scadenza in lista
    response = client.get('/api/v1/scadenze/scadenze/')
    assert response.status_code == 200
    assert any(s['id'] == scadenza_id for s in response.data['results'])
    
    # 4. Create Documento collegato a pratica
    response = client.post('/api/v1/documenti/documenti/', {
        'cliente': cliente.id,
        'titolo': 'Documento Test',
        'tipo': 'GEN',
        'pratiche': [pratica_id]
    })
    assert response.status_code == 201
    documento_id = response.data['id']
    
    # 5. Verifica che veda documento tracciabile
    response = client.get('/api/v1/archivio-fisico/documenti-tracciabili/')
    # (solo se documento è tracciabile e non digitale)
    
    # 6. Tentativo di accedere a cliente NON assegnato (deve fallire)
    altro_cliente = Cliente.objects.exclude(id=cliente.id).first()
    response = client.get(f'/api/v1/anagrafiche/clienti/{altro_cliente.id}/')
    assert response.status_code == 404  # Non trovato (fuori dal queryset filtrato)
```

---

## 📊 Performance Tests

### Query Count Monitoring

```python
@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_query_count_all_viewsets():
    """Monitora numero query per ogni ViewSet"""
    
    client = APIClient()
    user = User.objects.create_user(username='test', password='test')
    UserProfile.objects.create(user=user, ruolo='OPERATORE')
    client.force_authenticate(user=user)
    
    endpoints = [
        '/api/v1/anagrafiche/clienti/',
        '/api/v1/scadenze/scadenze/',
        '/api/v1/scadenze/occorrenze/',
        '/api/v1/protocollo/movimenti/',
        '/api/v1/archivio-fisico/operazioni/',
        '/api/v1/archivio-fisico/documenti-tracciabili/',
        '/api/v1/pratiche/note/',
        '/api/v1/documenti/import-sessions/',
    ]
    
    from django.db import reset_queries, connection
    
    for endpoint in endpoints:
        reset_queries()
        response = client.get(endpoint)
        queries = len(connection.queries)
        
        print(f"{endpoint}: {queries} queries")
        
        # Soglia: max 15 query per endpoint
        assert queries < 15, f"{endpoint} troppo lento: {queries} queries"
```

---

## 🚦 CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/rbac-tests.yml
name: RBAC Security Tests

on:
  push:
    paths:
      - 'api/v1/*/views.py'
      - 'core/permissions.py'
      - 'core/models.py'
  pull_request:
    paths:
      - 'api/v1/*/views.py'

jobs:
  rbac-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-django pytest-cov
      
      - name: Run RBAC tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/test
        run: |
          pytest api/v1/tests/test_rbac_*.py \
            --cov=api/v1 \
            --cov-report=html \
            --cov-report=term \
            -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## 📝 Manual Testing Checklist

### Browser/Postman Tests

1. **Login come ADMIN**
   ```bash
   POST /api/v1/auth/login/
   {
     "username": "admin_test",
     "password": "Test123!"
   }
   ```
   - [ ] Ricevi access token
   - [ ] GET `/api/v1/anagrafiche/clienti/` → vedi tutti i clienti

2. **Login come OPERATORE**
   - [ ] GET `/api/v1/anagrafiche/clienti/` → vedi solo 3 clienti
   - [ ] GET `/api/v1/scadenze/scadenze/` → vedi solo scadenze dei tuoi clienti
   - [ ] GET `/api/v1/protocollo/movimenti/` → vedi solo movimenti dei tuoi clienti

3. **Login come VIEWER**
   - [ ] GET `/api/v1/anagrafiche/clienti/` → vedi solo 1 cliente
   - [ ] POST `/api/v1/anagrafiche/clienti/` → 403 Forbidden (read-only)
   - [ ] PATCH `/api/v1/anagrafiche/clienti/1/` → 403 Forbidden

---

## 🐛 Debugging Tips

### Query SQL Inspection

```python
# Abilita query logging in settings.py (solo in development)
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

Poi in shell:
```python
from api.v1.anagrafiche.views import ClienteViewSet
from rest_framework.test import APIRequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='operatore_test')

factory = APIRequestFactory()
request = factory.get('/api/v1/anagrafiche/clienti/')
request.user = user

viewset = ClienteViewSet()
viewset.request = request

qs = viewset.get_queryset()
print(qs.query)  # Stampa SQL generato
```

---

## ✅ Success Criteria

- [ ] **100% Test Pass Rate** - Tutti i test unitari passano
- [ ] **< 15 Query per Endpoint** - Performance ottimale
- [ ] **0 Data Leakage** - Nessun cliente non assegnato visibile
- [ ] **Role Enforcement** - VIEWER read-only, OPERATORE write limitato
- [ ] **Coverage > 85%** - Code coverage sui ViewSet modificati

---

## 📚 Riferimenti

- **RBAC Implementation Report**: `docs/RBAC_IMPLEMENTATION_REPORT.md`
- **RBACPermission Class**: `core/permissions.py`
- **Pytest Documentation**: https://docs.pytest.org/
- **DRF Testing**: https://www.django-rest-framework.org/api-guide/testing/

---

**Guida Creata**: 3 Marzo 2026  
**Versione**: 1.0  
**Prossimo Step**: Eseguire test suite completa
