# Performance Optimization - MyGest

## 🚀 Panoramica

Questo documento descrive tutti i miglioramenti per le performance implementati nel sistema MyGest.

## 📋 Miglioramenti Implementati

### 1. ✅ Sistema di Caching con Redis

**Status:** Implementato  
**Impact:** 🚀🚀🚀 Alto

- **Backend:** django-redis con Redis server
- **Due cache separate:**
  - `default`: Cache generale (database 1)
  - `session`: Sessioni utente (database 2)
- **Features:**
  - Compressione automatica (zlib)
  - Connection pooling (50 connessioni max)
  - Timeout configurabili per tipologia
  - Utility functions in `mygest/cache_utils.py`
  - Template tags personalizzati

**Files:**
- `mygest/settings.py`: Configurazione CACHES
- `mygest/cache_utils.py`: Helper e decoratori
- `mygest/templatetags/cache_tags.py`: Template tags

### 2. ✅ Django Debug Toolbar

**Status:** Implementato  
**Impact:** 📊 Analisi

- **Attivo solo in sviluppo** (DEBUG=True)
- **Features:**
  - Analisi query SQL in tempo reale
  - Rilevamento query N+1
  - Profiling template rendering
  - Cache hit/miss statistics
  - Signal tracking

**Accesso:** `http://localhost:8000/__debug__/`

**Files:**
- `mygest/settings.py`: Configurazione middleware
- `mygest/urls.py`: URL debug toolbar

### 3. ✅ Ottimizzazione Query N+1

**Status:** Implementato  
**Impact:** 🚀🚀🚀 Alto

- **Helper functions** per query ottimizzate
- **Configurazioni predefinite** per ogni modello:
  - `DOCUMENTO_RELATED`
  - `PRATICA_RELATED`
  - `FASCICOLO_RELATED`
  - `MOVIMENTO_PROTOCOLLO_RELATED`
  - `SCADENZA_RELATED`
- **Mixin per ListView:** `OptimizedListView`
- **Decoratore per analisi:** `@count_queries`

**Files:**
- `mygest/query_optimization.py`: Utility e configurazioni

**Esempio uso:**
```python
from mygest.query_optimization import get_optimized_documento_qs

documenti = get_optimized_documento_qs()
```

### 4. ✅ Paginazione Consistente

**Status:** Implementato  
**Impact:** 🚀🚀 Medio

- **REST Framework:** PageNumberPagination (20 items/page)
- **ListView:** OptimizedListView con paginazione automatica
- **Custom paginator:** Configurabile per viste function-based
- **Classi disponibili:**
  - `StandardPagination`: 20 items/page
  - `LargePagination`: 50 items/page

**Files:**
- `mygest/settings.py`: REST_FRAMEWORK config
- `mygest/query_optimization.py`: Pagination classes

### 5. ✅ Database Connection Pooling

**Status:** Implementato  
**Impact:** 🚀🚀 Medio

- **django-db-connection-pool** integrato
- **Configurazione:**
  - Pool size: 10 connessioni permanenti
  - Max overflow: 20 connessioni temporanee
  - Recycle: 3600s (1 ora)
  - Pre-ping: Verifica connessioni prima dell'uso
- **pgBouncer:** Documentato per produzione

**Files:**
- `mygest/settings.py`: DATABASES config
- `docs/PERFORMANCE_INSTALLATION_CHECKLIST.md`: Setup pgBouncer

### 6. ✅ Compressione Statica

**Status:** Implementato  
**Impact:** 🚀 Basso-Medio

- **django-compressor:** Minificazione CSS/JS
- **WhiteNoise:** Compressione Brotli/Gzip
- **Features:**
  - Compressione offline in produzione
  - Cache headers automatici (1 anno)
  - Manifest per versioning
  - Template tags `{% compress %}`

**Files:**
- `mygest/settings.py`: COMPRESS e STORAGES config
- `mygest/templatetags/`: Template tags

**Build command:**
```bash
python manage.py collectstatic --noinput
python manage.py compress
```

## 📁 File Struttura

```
mygest/
├── docs/
│   ├── PERFORMANCE_OPTIMIZATION_GUIDE.md      # Guida completa
│   └── PERFORMANCE_INSTALLATION_CHECKLIST.md  # Checklist installazione
├── mygest/
│   ├── settings.py                            # Configurazioni principali
│   ├── settings_local.py.example              # Template settings locali
│   ├── settings_local_production.py.example   # Template produzione
│   ├── cache_utils.py                         # Utility caching
│   ├── query_optimization.py                  # Ottimizzazione query
│   ├── urls.py                                # URL con debug toolbar
│   └── templatetags/
│       ├── __init__.py
│       └── cache_tags.py                      # Template tags cache
├── scripts/
│   └── test_performance.py                    # Script test automatico
└── requirements.txt                           # Dipendenze aggiornate
```

## 🔧 Quick Start

### 1. Installa Dipendenze

```bash
cd /home/sandro/mygest
pip install -r requirements.txt
```

### 2. Installa e Avvia Redis

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test
redis-cli ping  # Deve rispondere: PONG
```

### 3. Configura Django

```bash
# Crea settings_local.py
cp mygest/settings_local_production.py.example mygest/settings_local.py
nano mygest/settings_local.py

# Modifica almeno:
# - SECRET_KEY
# - DEBUG
# - ALLOWED_HOSTS
# - DATABASES password
# - REDIS_PASSWORD (se configurato)
```

### 4. Migrazioni e Staticfiles

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py compress  # Solo produzione
```

### 5. Test Configurazione

```bash
# Test automatico
python scripts/test_performance.py

# Oppure manuale
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
'value'
```

### 6. Avvia Server

```bash
# Sviluppo
python manage.py runserver

# Visita: http://localhost:8000/
# Debug Toolbar dovrebbe essere visibile a destra
```

## 📊 Verifica Performance

### 1. Debug Toolbar (Sviluppo)

- Apri qualsiasi pagina
- Controlla panel "SQL"
- Query >50: ottimizzazione necessaria
- Query duplicate: problema N+1

### 2. Redis Statistics

```bash
redis-cli INFO stats
redis-cli INFO memory

# Metriche chiave:
# - keyspace_hits/keyspace_misses
# - used_memory
# - connected_clients
```

### 3. Database Queries

```bash
python manage.py shell
>>> from django.db import connection, reset_queries
>>> from documenti.models import Documento
>>> reset_queries()
>>> list(Documento.objects.select_related('tipo')[:10])
>>> len(connection.queries)  # Numero query eseguite
```

### 4. Cache Hit Rate

```python
from django_redis import get_redis_connection
conn = get_redis_connection("default")
info = conn.info('stats')
hits = info['keyspace_hits']
misses = info['keyspace_misses']
hit_rate = hits / (hits + misses) * 100
print(f"Cache hit rate: {hit_rate:.1f}%")
# Target: >80%
```

## 📈 Performance Attese

| Metrica | Prima | Dopo | Miglioramento |
|---------|-------|------|---------------|
| Response Time | ~800ms | ~200-300ms | **-60% a -70%** |
| Query Count | 100+ | <20 | **-80%** |
| Page Load | ~2s | ~0.8s | **-60%** |
| Cache Hit Rate | 0% | >80% | **Nuovo** |
| DB Connections | Variabili | 5-10 stabili | **Stabile** |

## 🛠️ Comandi Utili

```bash
# Gestione Cache
python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Redis
redis-cli FLUSHDB           # Svuota database
redis-cli FLUSHALL          # Svuota tutto
redis-cli KEYS "mygest:*"   # Lista chiavi

# Database
python manage.py dbshell -c "SELECT * FROM pg_stat_activity;"

# Staticfiles
python manage.py collectstatic --noinput
python manage.py compress --force

# Test performance
python scripts/test_performance.py

# Check deploy
python manage.py check --deploy
```

## 📚 Documentazione

### Guide Complete

1. **[PERFORMANCE_OPTIMIZATION_GUIDE.md](docs/PERFORMANCE_OPTIMIZATION_GUIDE.md)**
   - Guida completa a tutte le funzionalità
   - Best practices
   - Esempi di utilizzo
   - Troubleshooting

2. **[PERFORMANCE_INSTALLATION_CHECKLIST.md](docs/PERFORMANCE_INSTALLATION_CHECKLIST.md)**
   - Checklist passo-passo
   - Setup Redis, PostgreSQL, pgBouncer
   - Configurazione produzione
   - Monitoring e manutenzione

### Script e Utility

- `scripts/test_performance.py`: Test automatico configurazione
- `mygest/cache_utils.py`: Helper per caching
- `mygest/query_optimization.py`: Ottimizzazione query

## 🔐 Sicurezza

### Produzione Checklist

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` cambiata
- [ ] `ALLOWED_HOSTS` configurato
- [ ] Redis con password
- [ ] SSL/HTTPS attivo
- [ ] Security headers attivi
- [ ] Log rotation configurato
- [ ] Backup automatico attivo

### Redis Security

```bash
# In /etc/redis/redis.conf
bind 127.0.0.1 ::1
requirepass TUA_PASSWORD_SICURA
maxmemory 256mb
maxmemory-policy allkeys-lru
```

## 🆘 Troubleshooting

### Redis non si connette

```bash
sudo systemctl status redis-server
sudo systemctl restart redis-server
redis-cli ping
```

### Query ancora lente

1. Attiva Debug Toolbar
2. Controlla panel SQL
3. Identifica query N+1
4. Usa `select_related` o `prefetch_related`
5. Testa con `@count_queries` decorator

### Cache non funziona

```python
# Test in shell
from django.core.cache import cache
cache.set('test', 'value', 60)
print(cache.get('test'))  # Deve stampare 'value'
```

### Staticfiles non compressi

```bash
# Verifica compressor
python manage.py compress --force

# Verifica storage
python manage.py collectstatic --dry-run
```

## 🎯 Prossimi Step

1. **Monitoring Avanzato:**
   - Sentry per error tracking
   - Prometheus + Grafana per metriche
   - New Relic o DataDog (opzionale)

2. **Ulteriori Ottimizzazioni:**
   - CDN per staticfiles
   - Elasticsearch per ricerche
   - Celery per task asincroni
   - Read replicas PostgreSQL

3. **Load Testing:**
   - Apache Bench (ab)
   - Locust per test carico
   - Django Silk per profiling dettagliato

## 📞 Supporto

Per problemi o domande:

1. Consulta le guide in `docs/`
2. Esegui `python scripts/test_performance.py`
3. Controlla log: `logs/django.log`
4. Debug Toolbar: `/__debug__/`

## 📝 Changelog

### v1.0.0 (2025-01-17)

- ✅ Redis caching implementato
- ✅ Django Debug Toolbar configurato
- ✅ Query N+1 ottimizzate
- ✅ Paginazione consistente
- ✅ Connection pooling attivo
- ✅ Compressione statica configurata
- ✅ Documentazione completa
- ✅ Script di test automatico

---

**Performance Optimization by MyGest Team**  
Ultimo aggiornamento: Novembre 2025
