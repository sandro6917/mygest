# Guida Performance e Ottimizzazione - MyGest

Questa guida documenta tutti i miglioramenti implementati per ottimizzare le performance del sistema MyGest.

## Indice

1. [Sistema di Caching con Redis](#1-sistema-di-caching-con-redis)
2. [Django Debug Toolbar](#2-django-debug-toolbar)
3. [Ottimizzazione Query N+1](#3-ottimizzazione-query-n1)
4. [Paginazione Consistente](#4-paginazione-consistente)
5. [Database Connection Pooling](#5-database-connection-pooling)
6. [Compressione Statica](#6-compressione-statica)
7. [Best Practices](#7-best-practices)

---

## 1. Sistema di Caching con Redis

### Installazione Redis

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Avvia il servizio
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verifica funzionamento
redis-cli ping
# Risposta attesa: PONG
```

### Configurazione

Il sistema è configurato in `settings.py` con due cache separate:

- **default**: Cache generale per viste e query (database Redis 1)
- **session**: Cache dedicata alle sessioni utente (database Redis 2)

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,  # 5 minuti
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'TIMEOUT': 86400,  # 24 ore
    },
}
```

### Utilizzo del Caching

#### In Views (Function-Based)

```python
from mygest.cache_utils import cache_view

@cache_view(timeout=600, key_prefix='documenti_list')
@login_required
def documenti_list(request):
    # Questa vista viene cachata per 10 minuti
    documenti = Documento.objects.all()
    return render(request, 'documenti/list.html', {'documenti': documenti})
```

#### In Views (Class-Based)

```python
from mygest.cache_utils import CachedClassBasedView
from django.views.generic import ListView

class DocumentiListView(CachedClassBasedView, ListView):
    model = Documento
    cache_timeout = 600
    cache_key_prefix = 'documenti_list'
```

#### Caching di Property nei Model

```python
from mygest.cache_utils import cached_model_property

class Pratica(models.Model):
    # ... altri campi ...
    
    @cached_model_property(timeout=600)
    def documenti_count(self):
        # Calcolo pesante cachato
        return self.documenti.count()
```

#### Invalidazione Cache

```python
from mygest.cache_utils import invalidate_model_cache

# Dopo aver aggiornato un oggetto
pratica.save()
invalidate_model_cache(pratica, 'documenti_count', 'altre_property')
```

#### Nei Template

```django
{% load cache %}

{# Cache un blocco di template per 10 minuti #}
{% cache 600 sidebar request.user.id %}
    <div class="sidebar">
        {# Contenuto pesante da renderizzare #}
    </div>
{% endcache %}
```

### Comandi Utili Redis

```python
from django.core.cache import cache

# Svuota tutta la cache
cache.clear()

# Ottieni/imposta valori manualmente
cache.set('my_key', 'my_value', timeout=300)
value = cache.get('my_key')

# Elimina chiavi specifiche
cache.delete('my_key')
```

---

## 2. Django Debug Toolbar

### Attivazione

Django Debug Toolbar è configurato automaticamente in **modalità sviluppo** (DEBUG=True).

Dopo l'installazione delle dipendenze, vedrai una barra laterale nelle pagine web con informazioni su:

- **Query SQL**: Numero, tempo di esecuzione, query duplicate
- **Cache**: Hit/miss ratio, chiavi utilizzate
- **Templates**: Template renderizzati e tempo di rendering
- **Signals**: Signal Django attivati
- **Profiling**: Tempo di esecuzione per funzione

### Accesso

Vai su qualsiasi pagina del sito in sviluppo:
- Vedrai una barra laterale a destra con icone colorate
- Clicca su "SQL" per vedere tutte le query eseguite
- Query duplicate o N+1 saranno evidenziate in rosso

### Analisi Query N+1

1. Apri la pagina che vuoi analizzare
2. Clicca sul tab "SQL" della Debug Toolbar
3. Cerca query duplicate (stesso pattern ripetuto N volte)
4. Ottimizza usando `select_related` o `prefetch_related`

### URL Debug

La toolbar è accessibile anche via API REST:
```
http://localhost:8000/__debug__/
```

---

## 3. Ottimizzazione Query N+1

### Problema N+1

Quando si itera su una lista di oggetti accedendo a relazioni FK/M2M:

```python
# ❌ MALE - N+1 queries
pratiche = Pratica.objects.all()
for pratica in pratiche:
    print(pratica.cliente.nome)  # 1 query per ogni iterazione!
```

### Soluzione: select_related (FK e OneToOne)

```python
# ✅ BENE - 1 query con JOIN
pratiche = Pratica.objects.select_related('cliente', 'tipo').all()
for pratica in pratiche:
    print(pratica.cliente.nome)  # Nessuna query aggiuntiva
```

### Soluzione: prefetch_related (M2M e Reverse FK)

```python
# ✅ BENE - 2 queries (1 principale + 1 prefetch)
fascicoli = Fascicolo.objects.prefetch_related('pratiche', 'documenti').all()
for fascicolo in fascicoli:
    for pratica in fascicolo.pratiche.all():  # Usa dati pre-caricati
        print(pratica.codice)
```

### Utility Helper

Usa le funzioni helper in `mygest/query_optimization.py`:

```python
from mygest.query_optimization import get_optimized_documento_qs

# Ottiene automaticamente una queryset ottimizzata
documenti = get_optimized_documento_qs()
```

### Configurazioni Predefinite

In `query_optimization.py` sono definite configurazioni ottimali:

- `DOCUMENTO_RELATED`: Per query su Documenti
- `PRATICA_RELATED`: Per query su Pratiche
- `FASCICOLO_RELATED`: Per query su Fascicoli
- `MOVIMENTO_PROTOCOLLO_RELATED`: Per Movimenti Protocollo
- `SCADENZA_RELATED`: Per Scadenze

### Mixin per ListView

```python
from mygest.query_optimization import OptimizedListView

class PraticheListView(OptimizedListView):
    model = Pratica
    paginate_by = 20
    select_related_fields = ['cliente', 'cliente__anagrafica', 'tipo']
    prefetch_related_fields = ['documenti', 'note']
```

### Decoratore per Analisi Query (Sviluppo)

```python
from mygest.query_optimization import count_queries

@count_queries
def my_view(request):
    # Stampa il numero di query eseguite
    ...
```

---

## 4. Paginazione Consistente

### ListView con Paginazione

```python
from mygest.query_optimization import OptimizedListView

class DocumentiListView(OptimizedListView):
    model = Documento
    paginate_by = 20  # 20 elementi per pagina
    template_name = 'documenti/list.html'
```

### Function-Based Views

```python
from mygest.query_optimization import paginate_queryset

def documenti_list(request):
    documenti = Documento.objects.all()
    page_number = request.GET.get('page', 1)
    page_obj, paginator = paginate_queryset(documenti, page_number, per_page=20)
    
    return render(request, 'documenti/list.html', {
        'page_obj': page_obj,
        'paginator': paginator,
    })
```

### Template Paginazione

```django
{# Template con paginazione #}
{% for documento in page_obj %}
    {# Mostra documento #}
{% endfor %}

{# Controlli paginazione #}
<div class="pagination">
    {% if page_obj.has_previous %}
        <a href="?page=1">&laquo; Prima</a>
        <a href="?page={{ page_obj.previous_page_number }}">Precedente</a>
    {% endif %}
    
    <span>Pagina {{ page_obj.number }} di {{ page_obj.paginator.num_pages }}</span>
    
    {% if page_obj.has_next %}
        <a href="?page={{ page_obj.next_page_number }}">Successiva</a>
        <a href="?page={{ page_obj.paginator.num_pages }}">Ultima &raquo;</a>
    {% endif %}
</div>
```

### API REST Paginazione

```python
# settings.py già configurato
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Per ViewSet custom
from mygest.query_optimization import StandardPagination, LargePagination

class DocumentiViewSet(viewsets.ModelViewSet):
    pagination_class = StandardPagination  # 20 per pagina
    # o
    pagination_class = LargePagination  # 50 per pagina
```

---

## 5. Database Connection Pooling

### Configurazione

Il connection pooling è già configurato in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.postgresql',
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,        # Connessioni permanenti
            'MAX_OVERFLOW': 20,     # Connessioni aggiuntive temporanee
            'RECYCLE': 3600,        # Ricicla dopo 1 ora
            'PRE_PING': True,       # Verifica connessioni
        }
    }
}
```

### Vantaggi

- **Riduce latenza**: Riutilizza connessioni esistenti
- **Migliora throughput**: Gestisce meglio picchi di traffico
- **Più stabile**: Pre-ping previene errori "connection closed"

### pgBouncer in Produzione (Raccomandato)

Per ambienti produzione ad alto traffico, usa pgBouncer:

#### Installazione

```bash
sudo apt install pgbouncer
```

#### Configurazione `/etc/pgbouncer/pgbouncer.ini`

```ini
[databases]
mygest = host=127.0.0.1 port=5432 dbname=mygest

[pgbouncer]
listen_addr = 127.0.0.1
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
```

#### Userlist `/etc/pgbouncer/userlist.txt`

```
"mygest_user" "password_hash"
```

#### Modifica Django settings.py in produzione

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '127.0.0.1',
        'PORT': '6432',  # pgBouncer invece di 5432
        # ... altri parametri
    }
}
```

#### Avvia pgBouncer

```bash
sudo systemctl start pgbouncer
sudo systemctl enable pgbouncer
```

### Monitoraggio Connection Pool

```python
# In Django shell
from django.db import connection

# Statistiche connessioni
with connection.cursor() as cursor:
    cursor.execute("SELECT * FROM pg_stat_activity WHERE datname = 'mygest'")
    connections = cursor.fetchall()
    print(f"Connessioni attive: {len(connections)}")
```

---

## 6. Compressione Statica

### Configurazione

Sistema configurato con:
- **django-compressor**: Minifica CSS/JS
- **WhiteNoise**: Serve file statici compressi con Brotli/Gzip

### Build Statica per Produzione

```bash
# Raccoglie e comprime tutti i file statici
python manage.py collectstatic --noinput
python manage.py compress
```

### Template con Compressione

```django
{% load static %}
{% load compress %}

{# CSS compresso #}
{% compress css %}
    <link rel="stylesheet" href="{% static 'css/base.css' %}">
    <link rel="stylesheet" href="{% static 'css/forms.css' %}">
{% endcompress %}

{# JavaScript compresso #}
{% compress js %}
    <script src="{% static 'js/jquery.min.js' %}"></script>
    <script src="{% static 'js/app.js' %}"></script>
{% endcompress %}
```

### Verifica Compressione

```bash
# Controlla se Brotli è attivo
curl -H "Accept-Encoding: br" -I http://localhost:8000/static/css/style.css

# Cerca header:
# Content-Encoding: br
```

### Cache Headers per Statica

WhiteNoise aggiunge automaticamente:
- **Cache-Control**: `max-age=31536000` (1 anno)
- **ETag**: Per validazione cache
- **Last-Modified**: Timestamp file

---

## 7. Best Practices

### Checklist Ottimizzazione

#### Per Ogni Vista/ListView:

- [ ] Usa `select_related` per FK/OneToOne
- [ ] Usa `prefetch_related` per M2M/Reverse FK
- [ ] Implementa paginazione (20-50 elementi)
- [ ] Considera caching per viste statiche (>1 min)
- [ ] Usa `only()` o `defer()` per grandi tabelle
- [ ] Evita `.count()` in template loop

#### Per API ViewSet:

- [ ] Configura `pagination_class`
- [ ] Aggiungi `select_related` in `get_queryset()`
- [ ] Implementa throttling per rate limiting
- [ ] Usa `ListSerializer` per bulk operations
- [ ] Considera caching per endpoint read-only

#### Per Model Property Pesanti:

- [ ] Usa `@cached_model_property` decorator
- [ ] Invalida cache dopo `.save()`
- [ ] Considera annotate/aggregate invece di property

#### Per Template:

- [ ] Usa `{% cache %}` per sidebar/header statici
- [ ] Evita query nel loop (`with` tag)
- [ ] Comprimi CSS/JS con `{% compress %}`
- [ ] Usa `select_related` nella vista

### Strumenti di Monitoraggio

```python
# 1. Debug Toolbar (sviluppo)
# Verifica query SQL in __debug__ panel

# 2. Django Extensions (opzionale)
pip install django-extensions
python manage.py shell_plus --print-sql

# 3. Query logging in settings (sviluppo)
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
        },
    },
}
```

### Test Performance

```python
# Test con django-silk (opzionale)
pip install django-silk

# settings.py
INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

# Analizza profiling su /silk/
```

### Comandi Utili

```bash
# Controlla query slow in PostgreSQL
psql -U mygest_user -d mygest -c "
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;"

# Pulisci cache Redis
redis-cli FLUSHDB

# Verifica memoria Redis
redis-cli INFO memory

# Test connection pool
python manage.py shell -c "
from django.db import connection
print(connection.pool.size())
print(connection.pool.checkedout())
"
```

---

## Riepilogo Miglioramenti

### Performance Impact Atteso

| Ottimizzazione | Impatto | Difficoltà |
|---------------|---------|------------|
| Caching Redis | 🚀🚀🚀 Alto | Media |
| Query N+1 Fix | 🚀🚀🚀 Alto | Bassa |
| Connection Pool | 🚀🚀 Medio | Bassa |
| Compressione Statica | 🚀 Basso | Bassa |
| Paginazione | 🚀🚀 Medio | Bassa |
| Debug Toolbar | 📊 Analisi | Bassa |

### Metriche da Monitorare

1. **Response Time**: Deve ridursi del 30-70%
2. **Query Count**: Riduzione da 100+ a <20 per pagina
3. **Cache Hit Rate**: Target >80%
4. **Database Connections**: Stabile <10 in pool
5. **Static Load Time**: Riduzione 40-60%

### Prossimi Passi

1. Installa dipendenze: `pip install -r requirements.txt`
2. Avvia Redis: `sudo systemctl start redis-server`
3. Applica migrazioni: `python manage.py migrate`
4. Testa con Debug Toolbar: attiva viste principali
5. Monitora con `__debug__` panel
6. In produzione: configura pgBouncer e collectstatic

---

## Supporto

Per problemi o domande:
- Controlla log: `logs/protocollazione.log`
- Debug Toolbar: `/__debug__/`
- Cache: `redis-cli monitor`
- Database: `psql -U mygest_user mygest`
