# Quick Start - Performance Optimization

## ✅ Configurazione Completata

Hai già un file `settings_local.py` configurato per lo **sviluppo**. 

Le ottimizzazioni sono state implementate ma alcune sono **opzionali** in sviluppo:

### 🔧 Cosa è Attivo Ora (senza setup aggiuntivo):

- ✅ **Django Debug Toolbar** - Attivo automaticamente quando DEBUG=True
- ✅ **Database Connection Pooling** - Configurato in settings.py
- ✅ **Query Optimization Helpers** - Utility pronte in `mygest/query_optimization.py`
- ✅ **Paginazione** - Configurata per API REST
- ✅ **Compressione Statica** - Configurata (attiva in produzione)

### 📦 Opzionale: Redis Cache (Raccomandato)

Se vuoi attivare il caching Redis anche in sviluppo:

#### 1. Installa Redis
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

#### 2. Verifica
```bash
redis-cli ping
# Dovrebbe rispondere: PONG
```

#### 3. Test
```bash
python scripts/test_performance.py
```

**Nota:** Senza Redis, il sistema usa il cache backend di default di Django (in-memory), che funziona ma è meno efficiente.

---

## 🎯 Come Usare le Ottimizzazioni

### 1. Debug Toolbar

Dopo aver avviato il server:
```bash
python manage.py runserver
```

Vedrai una barra laterale sulla destra con:
- **SQL**: Numero di query e tempo di esecuzione
- **Cache**: Hit/miss ratio
- **Time**: Tempo totale di rendering

### 2. Query Optimization

Nelle tue viste, usa gli helper:

```python
from mygest.query_optimization import get_optimized_documento_qs

def my_view(request):
    # Query ottimizzata con select_related/prefetch_related
    documenti = get_optimized_documento_qs()
    # ...
```

O usa il mixin per ListView:

```python
from mygest.query_optimization import OptimizedListView

class MyListView(OptimizedListView):
    model = Documento
    paginate_by = 20
    select_related_fields = ['tipo', 'cliente']
    prefetch_related_fields = ['movimenti']
```

### 3. Caching (se hai Redis)

```python
from mygest.cache_utils import cache_view

@cache_view(timeout=600)  # Cache per 10 minuti
def expensive_view(request):
    # Vista cachata
    pass
```

---

## 📊 Verificare le Performance

### Check Query Count
1. Apri una pagina nel browser
2. Guarda il panel **SQL** della Debug Toolbar
3. Obiettivo: **< 20 query per pagina**

### Test Automatico
```bash
python scripts/test_performance.py
```

Questo script verifica:
- Connessione Redis (se attivo)
- Database connection pool
- Query optimization
- Configurazioni

---

## 🚀 Deploy in Produzione

Quando sei pronto per il deploy:

1. Copia il template produzione:
```bash
cp mygest/settings_local_production.py.example mygest/settings_local.py
```

2. Modifica `settings_local.py`:
   - `DEBUG = False`
   - Genera nuova `SECRET_KEY`
   - Imposta `ALLOWED_HOSTS`
   - Configura password database e Redis
   - Decommenta sezioni HTTPS/SSL

3. Segui la checklist completa:
```bash
cat docs/PERFORMANCE_INSTALLATION_CHECKLIST.md
```

---

## 📚 Documentazione

- **Guida Completa**: `docs/PERFORMANCE_OPTIMIZATION_GUIDE.md`
- **Checklist Installazione**: `docs/PERFORMANCE_INSTALLATION_CHECKLIST.md`
- **README Produzione**: `docs/PERFORMANCE_README.md`

---

## 🆘 Problemi Comuni

### Import Error django_redis
Se vedi errori su `django_redis`:
```bash
pip install django-redis redis
```

### Redis non connette
Redis non è obbligatorio in sviluppo. Il sistema funziona anche senza, usando il cache di default di Django.

### Debug Toolbar non appare
Verifica in `settings_local.py`:
```python
DEBUG = True
# INTERNAL_IPS è già configurato in settings.py
```

---

## ✅ Prossimi Passi

1. **Ora**: Avvia il server e verifica Debug Toolbar
   ```bash
   python manage.py runserver
   ```

2. **Opzionale**: Installa Redis per caching avanzato

3. **Prima del deploy**: Segui checklist produzione

Tutto pronto! 🎉
