# Guida Completa Testing - MyGest

Documentazione completa per testing, coverage, CI/CD e quality assurance.

## Indice

1. [Quick Start](#quick-start)
2. [Struttura Test](#struttura-test)
3. [Test Unitari](#test-unitari)
4. [Test di Integrazione](#test-di-integrazione)
5. [Test API](#test-api)
6. [Coverage](#coverage)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Load Testing](#load-testing)
9. [Best Practices](#best-practices)

---

## Quick Start

### Installazione Dipendenze

```bash
pip install -r requirements.txt
```

### Esegui Tutti i Test

```bash
# Test completi con coverage
pytest -v --cov=. --cov-report=html

# Solo test unitari (veloci)
pytest -m unit

# Solo test di integrazione
pytest -m integration

# Solo test API
pytest -m api

# Test in parallelo (più veloce)
pytest -n auto
```

### Visualizza Coverage

```bash
# Apri report HTML
open htmlcov/index.html

# Report nel terminale
pytest --cov=. --cov-report=term-missing
```

---

## Struttura Test

```
mygest/
├── conftest.py                    # Fixtures globali
├── pytest.ini                     # Configurazione pytest
├── .coveragerc                    # Configurazione coverage
├── tests/
│   ├── test_integration.py        # Test integrazione tra app
│   ├── test_api_rest.py           # Test API REST
│   ├── test_api_graphql.py        # Test GraphQL
│   └── test_load.py               # Load testing (Locust)
├── anagrafiche/
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       ├── test_validators.py
│       └── test_utils.py
├── documenti/
│   └── tests/
│       ├── test_models.py
│       ├── test_views.py
│       └── test_validators.py
└── [altre app...]
```

---

## Test Unitari

### Validatori CF e P.IVA

```python
# anagrafiche/tests/test_validators.py
import pytest
from anagrafiche.models import Anagrafica

@pytest.mark.unit
def test_codice_fiscale_valido(db):
    """Test CF valido"""
    anag = Anagrafica(
        tipo='PF',
        nome='Mario',
        cognome='Rossi',
        codice_fiscale='RSSMRA80A01H501U'
    )
    anag.full_clean()  # Non solleva eccezioni
    assert anag.codice_fiscale == 'RSSMRA80A01H501U'

@pytest.mark.unit
def test_partita_iva_valida(db):
    """Test P.IVA valida"""
    anag = Anagrafica(
        tipo='PG',
        ragione_sociale='Acme SRL',
        partita_iva='12345678901'
    )
    anag.full_clean()
    assert anag.partita_iva == '12345678901'
```

### Test Models

```python
@pytest.mark.unit
def test_create_pratica(db, cliente_pf, pratica_tipo):
    """Test creazione pratica"""
    from pratiche.models import Pratica
    
    pratica = Pratica.objects.create(
        cliente=cliente_pf,
        tipo=pratica_tipo,
        codice='TEST-001',
        oggetto='Pratica di test'
    )
    
    assert pratica.pk is not None
    assert pratica.cliente == cliente_pf
    assert str(pratica) == 'TEST-001'
```

### Test Views

```python
@pytest.mark.unit
def test_pratiche_list_view(authenticated_client, pratica):
    """Test vista lista pratiche"""
    response = authenticated_client.get('/pratiche/')
    
    assert response.status_code == 200
    assert pratica.codice in response.content.decode()
```

### Esecuzione Test Unitari

```bash
# Solo test unitari (veloci)
pytest -m unit -v

# Con coverage
pytest -m unit --cov=anagrafiche --cov=documenti

# Test specifico
pytest anagrafiche/tests/test_validators.py::TestCodiceFiscaleValidator::test_codice_fiscale_valido
```

---

## Test di Integrazione

### Flussi Completi

```python
# tests/test_integration.py
@pytest.mark.integration
def test_flusso_documento_protocollo_archivio(
    db, cliente_pf, documento_tipo, fascicolo, unita_archivio
):
    """Test flusso end-to-end"""
    from documenti.models import Documento
    from protocollo.models import MovimentoProtocollo
    from archivio_fisico.models import CollocazioneFisica
    
    # 1. Crea documento
    documento = Documento.objects.create(
        cliente=cliente_pf,
        tipo=documento_tipo,
        fascicolo=fascicolo,
        descrizione='Doc test'
    )
    
    # 2. Protocolla
    movimento = MovimentoProtocollo.objects.create(
        content_object=documento,
        tipo='IN',
        numero_protocollo=1
    )
    
    # 3. Archivia
    collocazione = CollocazioneFisica.objects.create(
        content_object=documento,
        unita=unita_archivio,
        posizione=1
    )
    
    # Verifica tutto collegato
    assert movimento.content_object == documento
    assert collocazione.content_object == documento
```

### Esecuzione Test Integrazione

```bash
# Solo test integrazione
pytest -m integration -v

# Con coverage
pytest -m integration --cov=.

# Specifica file
pytest tests/test_integration.py
```

---

## Test API

### Test REST API

```python
# tests/test_api_rest.py
@pytest.mark.api
def test_api_comunicazioni_list(authenticated_api_client):
    """Test GET /api/comunicazioni/"""
    response = authenticated_api_client.get('/api/comunicazioni/')
    
    assert response.status_code == 200
    assert 'results' in response.data or isinstance(response.data, list)

@pytest.mark.api
def test_api_create_comunicazione(authenticated_api_client, cliente_pf):
    """Test POST /api/comunicazioni/"""
    data = {
        'destinatario': cliente_pf.anagrafica.id,
        'oggetto': 'Test API',
        'testo': 'Messaggio test',
        'tipo': 'EMAIL'
    }
    
    response = authenticated_api_client.post(
        '/api/comunicazioni/',
        data,
        format='json'
    )
    
    assert response.status_code == 201
    assert response.data['oggetto'] == 'Test API'
```

### Test GraphQL

```python
# tests/test_api_graphql.py
@pytest.mark.api
def test_graphql_query_pratiche(authenticated_client, pratica):
    """Test query GraphQL"""
    query = """
    query {
        allPratiche {
            edges {
                node {
                    id
                    codice
                }
            }
        }
    }
    """
    
    response = authenticated_client.post(
        '/graphql/',
        json.dumps({'query': query}),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    assert 'allPratiche' in data['data']
```

### Esecuzione Test API

```bash
# Solo test API
pytest -m api -v

# REST API
pytest tests/test_api_rest.py

# GraphQL
pytest tests/test_api_graphql.py

# Con coverage
pytest -m api --cov=comunicazioni.api --cov=mygest.schema
```

---

## Coverage

### Target Coverage

- **Minimo**: 70%
- **Target**: 80%+
- **Ideale**: 90%+

### Eseguire Coverage

```bash
# Coverage completo
pytest --cov=. --cov-report=html --cov-report=term-missing

# Coverage per app specifica
pytest --cov=anagrafiche --cov-report=html

# Coverage con branch coverage
pytest --cov=. --cov-branch --cov-report=html

# Mostra solo file con coverage < 80%
pytest --cov=. --cov-report=term-missing --cov-fail-under=80
```

### Report Coverage

```bash
# Report HTML (dettagliato)
open htmlcov/index.html

# Report terminale
pytest --cov=. --cov-report=term

# Report XML (per CI/CD)
pytest --cov=. --cov-report=xml

# Coverage summary
coverage report

# Coverage dettagliato per file
coverage report -m anagrafiche/models.py
```

### Migliorare Coverage

1. **Identifica gaps**:
```bash
coverage report --show-missing
```

2. **Priorità**:
   - Models (80%+)
   - Validators e Utils (90%+)
   - Views (70%+)
   - API (75%+)

3. **Escludi codice non testabile**:
```python
# .coveragerc
exclude_lines =
    pragma: no cover
    def __repr__
    if __name__ == .__main__.:
```

---

## CI/CD Pipeline

### GitHub Actions

Pipeline automatica su push/PR:

1. **Lint** - Ruff, Black, isort, mypy
2. **Test** - Pytest con coverage
3. **Integration Tests** - Test integrazione
4. **Security Scan** - Safety, Bandit
5. **Build** - Collectstatic, migrations check
6. **Deploy** - Staging (develop) / Production (main)

### Workflow File

`.github/workflows/ci-cd.yml` già configurato con:

- PostgreSQL 14
- Redis 7
- Python 3.10
- Coverage report su Codecov
- Deploy automatico

### Esecuzione Locale

Simula CI localmente:

```bash
# Lint
ruff check .
black --check .
isort --check-only .
mypy .

# Test
pytest -v --cov=. --cov-report=xml

# Security
safety check
bandit -r .

# Django checks
python manage.py check --deploy
python manage.py makemigrations --check --dry-run
```

### Badge Status

Aggiungi al README.md:

```markdown
![Tests](https://github.com/sandro6917/mygest/workflows/Django%20CI%2FCD%20Pipeline/badge.svg)
![Coverage](https://codecov.io/gh/sandro6917/mygest/branch/main/graph/badge.svg)
```

---

## Load Testing

### Locust Setup

```bash
# Installa Locust
pip install locust

# Avvia load test
locust -f tests/test_load.py --host=http://localhost:8000

# Apri web UI
# Visita: http://localhost:8089
```

### Scenari di Test

1. **WebUser** - Navigazione web standard (peso: 3)
2. **APIUser** - Chiamate API REST (peso: 2)
3. **GraphQLUser** - Query GraphQL (peso: 1)
4. **PeakLoadUser** - Picchi di carico
5. **HeavyQueryUser** - Query pesanti
6. **ReadOnlyUser** - Solo lettura (peso: 5, più comune)
7. **CreateUpdateUser** - Creazione/modifica (peso: 1, meno comune)

### Test di Carico Tipici

```bash
# Test leggero (10 utenti)
locust -f tests/test_load.py --host=http://localhost:8000 -u 10 -r 2

# Test medio (50 utenti)
locust -f tests/test_load.py --host=http://localhost:8000 -u 50 -r 5

# Test pesante (200 utenti)
locust -f tests/test_load.py --host=http://localhost:8000 -u 200 -r 10

# Headless (senza web UI)
locust -f tests/test_load.py --host=http://localhost:8000 -u 100 -r 10 --headless --run-time 5m
```

### Metriche da Monitorare

- **Response time**: < 500ms (p95)
- **Throughput**: > 100 req/sec
- **Error rate**: < 1%
- **CPU**: < 70%
- **Memory**: < 80%
- **Database connections**: stabile

### Report Load Test

```bash
# Genera report HTML
locust -f tests/test_load.py --host=http://localhost:8000 --headless --html=loadtest-report.html
```

---

## Best Practices

### 1. Organizzazione Test

✅ **DO**:
```python
# test_models.py
class TestAnagraficaModel:
    def test_create_persona_fisica(self):
        ...
    
    def test_create_persona_giuridica(self):
        ...
```

❌ **DON'T**:
```python
def test_everything():  # Troppo generico
    ...
```

### 2. Fixtures

✅ **DO**:
```python
@pytest.fixture
def pratica_completa(db, cliente_pf, pratica_tipo, fascicolo):
    """Fixture complessa riutilizzabile"""
    pratica = create_pratica(cliente_pf, pratica_tipo)
    pratica.fascicoli.add(fascicolo)
    return pratica
```

✅ **DO**:
```python
@pytest.fixture
def make_pratica(db):
    """Factory fixture"""
    def _make(**kwargs):
        return baker.make(Pratica, **kwargs)
    return _make
```

### 3. Markers

```python
@pytest.mark.unit  # Test veloce, isolato
@pytest.mark.integration  # Multiple app
@pytest.mark.api  # Test API
@pytest.mark.slow  # Test lento
@pytest.mark.performance  # Performance test
```

### 4. Parametrize

✅ **DO**:
```python
@pytest.mark.parametrize('cf_valido', [
    'RSSMRA80A01H501U',
    'BNCGNN85T10A944S',
    'VRDDNC90D41F205X',
])
def test_codici_fiscali_validi(cf_valido):
    ...
```

### 5. Assertion Messages

✅ **DO**:
```python
assert response.status_code == 200, f"Expected 200, got {response.status_code}"
assert documento.cliente == cliente_pf, "Cliente non corretto"
```

### 6. Test Naming

✅ **DO**:
```python
def test_create_pratica_with_valid_data()
def test_update_pratica_requires_authentication()
def test_delete_pratica_cascades_to_documents()
```

❌ **DON'T**:
```python
def test_1()
def test_stuff()
def test()
```

---

## Comandi Utili

```bash
# Test veloci (skip slow)
pytest -m "not slow"

# Test falliti nell'ultima run
pytest --lf

# Test specifico con output completo
pytest -vvs tests/test_integration.py::TestFlussoPratica::test_creazione_completa

# Debug con pdb
pytest --pdb

# Coverage con branch coverage
pytest --cov=. --cov-branch

# Parallel execution
pytest -n auto

# Stop al primo fallimento
pytest -x

# Report dettagliato
pytest -v --tb=long

# Quiet mode (solo summary)
pytest -q

# Warnings come errori
pytest -W error
```

---

## Troubleshooting

### Test Lenti

```bash
# Identifica test lenti
pytest --durations=10

# Skip database
pytest --no-db

# Use in-memory SQLite
# settings_test.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

### Coverage Basso

1. Controlla quali file mancano:
```bash
coverage report --show-missing
```

2. Aggiungi test per:
   - Models: `__str__`, `save()`, custom methods
   - Views: GET, POST, errori
   - Utils: edge cases
   - Validators: casi validi e invalidi

### CI/CD Fails

1. Riprod uci localmente:
```bash
# Setup come CI
python -m pytest -v --cov=. --cov-report=xml
```

2. Verifica migrations:
```bash
python manage.py makemigrations --check --dry-run
```

3. Check deploy:
```bash
python manage.py check --deploy
```

---

## Obiettivi Coverage per App

| App | Target | Priorità |
|-----|--------|----------|
| anagrafiche | 85% | Alta |
| documenti | 80% | Alta |
| pratiche | 80% | Alta |
| fascicoli | 75% | Media |
| protocollo | 80% | Alta |
| scadenze | 75% | Media |
| comunicazioni | 70% | Media |
| archivio_fisico | 75% | Media |
| stampe | 60% | Bassa |
| whatsapp | 65% | Bassa |

**Coverage Globale Target**: **75%+**

---

## Risorse

- [Pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/4.2/topics/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)
- [GitHub Actions](https://docs.github.com/en/actions)

---

**Prossimi step**: Esegui `pytest -v --cov=. --cov-report=html` e analizza il report!
