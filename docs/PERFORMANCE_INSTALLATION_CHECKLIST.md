# Checklist Installazione Performance Optimization - MyGest

Questa checklist ti guida passo-passo nell'installazione e configurazione di tutti i miglioramenti per le performance.

## ✅ Fase 1: Installazione Dipendenze

### 1.1 Installa pacchetti Python

```bash
cd /home/sandro/mygest
pip install -r requirements.txt
```

Verifica installazione:
```bash
pip list | grep -E "django-redis|django-debug-toolbar|django-compressor|django-db-connection-pool"
```

Dovresti vedere:
- django-redis: 5.4.0
- django-debug-toolbar: 4.4.6
- django-compressor: 4.5.1
- django-db-connection-pool: 1.2.4

---

## ✅ Fase 2: Redis

### 2.1 Installa Redis

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server

# Verifica versione
redis-server --version
```

### 2.2 Configura Redis per produzione

Modifica `/etc/redis/redis.conf`:

```bash
sudo nano /etc/redis/redis.conf
```

Imposta:
```ini
# Bind solo localhost (sicurezza)
bind 127.0.0.1 ::1

# Password (raccomandato in produzione)
requirepass TUA_PASSWORD_SICURA

# Memoria massima
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistenza
save 900 1
save 300 10
save 60 10000
```

### 2.3 Avvia Redis

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl status redis-server
```

### 2.4 Test Redis

```bash
redis-cli ping
# Risposta attesa: PONG

# Se hai impostato password:
redis-cli -a TUA_PASSWORD ping
```

---

## ✅ Fase 3: Database Connection Pooling

### 3.1 PostgreSQL - Configurazione Base

Nessuna modifica necessaria se usi il pool integrato Django.

### 3.2 pgBouncer (Opzionale - Produzione ad alto traffico)

#### Installa pgBouncer

```bash
sudo apt install pgbouncer
```

#### Configura pgBouncer

Crea `/etc/pgbouncer/pgbouncer.ini`:

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
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
server_lifetime = 3600
server_idle_timeout = 600
```

#### Crea userlist

```bash
# Genera hash password
echo -n "PASSWORD_DB" | md5sum

# Aggiungi a /etc/pgbouncer/userlist.txt
sudo nano /etc/pgbouncer/userlist.txt
```

Formato:
```
"mygest_user" "md5<hash_generato>"
```

#### Avvia pgBouncer

```bash
sudo systemctl start pgbouncer
sudo systemctl enable pgbouncer
sudo systemctl status pgbouncer
```

#### Modifica Django settings_local.py

Se usi pgBouncer, cambia:
```python
DATABASES['default']['PORT'] = '6432'  # Invece di 5432
```

---

## ✅ Fase 4: Configurazione Django

### 4.1 Crea settings_local.py

```bash
cd /home/sandro/mygest/mygest
cp settings_local_production.py.example settings_local.py
nano settings_local.py
```

Modifica almeno:
- `SECRET_KEY`: Genera nuova chiave
- `DEBUG`: False in produzione
- `ALLOWED_HOSTS`: I tuoi domini
- `DATABASES`: Password database
- `REDIS_PASSWORD`: Se hai impostato password Redis
- `EMAIL_*`: Configurazioni email

### 4.2 Test configurazione

```bash
cd /home/sandro/mygest
python manage.py check --deploy
```

Risolvi eventuali warning mostrati.

---

## ✅ Fase 5: Migrazioni e Staticfiles

### 5.1 Applica migrazioni

```bash
python manage.py migrate
```

### 5.2 Raccogli file statici

```bash
python manage.py collectstatic --noinput
```

### 5.3 Comprimi file statici (produzione)

```bash
python manage.py compress
```

---

## ✅ Fase 6: Test in Sviluppo

### 6.1 Avvia server di sviluppo

```bash
python manage.py runserver
```

### 6.2 Verifica Debug Toolbar

1. Apri: http://localhost:8000/
2. Dovresti vedere la barra Debug Toolbar a destra
3. Clicca su "SQL" per vedere le query

### 6.3 Test Redis Cache

```bash
python manage.py shell
```

In shell:
```python
from django.core.cache import cache

# Test set/get
cache.set('test_key', 'test_value', timeout=60)
print(cache.get('test_key'))  # Deve stampare: test_value

# Test cache info
from django_redis import get_redis_connection
conn = get_redis_connection("default")
print(conn.info())  # Mostra statistiche Redis
```

### 6.4 Test Connection Pool

```bash
python manage.py shell
```

In shell:
```python
from django.db import connection

# Esegui query
from documenti.models import Documento
Documento.objects.count()

# Verifica pool
print(f"Pool size: {connection.pool.size()}")
print(f"Checked out: {connection.pool.checkedout()}")
```

---

## ✅ Fase 7: Ottimizzazione Viste

### 7.1 Identifica viste lente

Con Debug Toolbar attivo:
1. Naviga nelle sezioni principali (Documenti, Pratiche, Fascicoli)
2. Controlla panel "SQL"
3. Query >50: ottimizzazione necessaria
4. Cerca query duplicate (N+1 problem)

### 7.2 Applica ottimizzazioni

Usa helper in `mygest/query_optimization.py`:

```python
# views.py
from mygest.query_optimization import get_optimized_documento_qs

def documenti_list(request):
    documenti = get_optimized_documento_qs()
    # ... resto della vista
```

### 7.3 Aggiungi paginazione

```python
from mygest.query_optimization import OptimizedListView

class DocumentiListView(OptimizedListView):
    model = Documento
    paginate_by = 20
    select_related_fields = ['tipo', 'cliente', 'fascicolo']
    prefetch_related_fields = ['movimenti']
```

---

## ✅ Fase 8: Monitoraggio

### 8.1 Log Performance

Controlla log:
```bash
tail -f /srv/mygest/logs/django.log
```

### 8.2 Redis Statistics

```bash
redis-cli INFO stats
redis-cli INFO memory
```

Metriche chiave:
- `keyspace_hits`: Cache hits
- `keyspace_misses`: Cache misses
- Hit rate = hits / (hits + misses)
- Target: >80%

### 8.3 PostgreSQL Query Analysis

```sql
-- Connetti al database
psql -U mygest_user -d mygest

-- Query più lente
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- Reset statistiche
SELECT pg_stat_statements_reset();
```

### 8.4 pgBouncer Stats (se attivo)

```bash
psql -p 6432 -U mygest_user pgbouncer -c "SHOW STATS;"
psql -p 6432 -U mygest_user pgbouncer -c "SHOW POOLS;"
```

---

## ✅ Fase 9: Deploy Produzione

### 9.1 Preparazione

```bash
# Su VPS/Server produzione
cd /srv/mygest

# Backup database
pg_dump -U mygest_user mygest > backup_pre_performance.sql

# Pull codice aggiornato
git pull origin main

# Installa dipendenze
pip install -r requirements.txt
```

### 9.2 Configurazione produzione

```bash
# Crea settings_local.py per produzione
cp mygest/settings_local_production.py.example mygest/settings_local.py
nano mygest/settings_local.py

# Imposta:
# - DEBUG = False
# - SECRET_KEY (nuova!)
# - ALLOWED_HOSTS
# - Database password
# - Redis password
# - Email settings
```

### 9.3 Deploy

```bash
# Migrazioni
python manage.py migrate

# Staticfiles
python manage.py collectstatic --noinput
python manage.py compress

# Riavvia servizio
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 9.4 Verifica produzione

```bash
# Check deploy
python manage.py check --deploy

# Test Redis
redis-cli -a PASSWORD ping

# Test database
python manage.py dbshell -c "SELECT COUNT(*) FROM documenti_documento;"
```

---

## ✅ Fase 10: Automazione e Manutenzione

### 10.1 Cron Job - Cleanup Cache

Crea `/etc/cron.daily/mygest-cache-cleanup`:

```bash
#!/bin/bash
# Pulizia cache vecchia

# Redis: rimuovi chiavi scadute
redis-cli FLUSHDB

# Log
echo "$(date): Cache cleanup completed" >> /srv/mygest/logs/cache_cleanup.log
```

Rendi eseguibile:
```bash
sudo chmod +x /etc/cron.daily/mygest-cache-cleanup
```

### 10.2 Monitoraggio Automatico

Crea script `/srv/mygest/scripts/monitor_performance.sh`:

```bash
#!/bin/bash

LOG_FILE="/srv/mygest/logs/performance_monitor.log"

echo "=== Performance Check $(date) ===" >> $LOG_FILE

# Redis
echo "Redis Stats:" >> $LOG_FILE
redis-cli INFO stats | grep -E "keyspace_(hits|misses)" >> $LOG_FILE

# PostgreSQL
echo "DB Connections:" >> $LOG_FILE
psql -U mygest_user -d mygest -c "SELECT count(*) FROM pg_stat_activity WHERE datname='mygest';" >> $LOG_FILE

# Disk space
echo "Disk Usage:" >> $LOG_FILE
df -h /srv/mygest >> $LOG_FILE

echo "" >> $LOG_FILE
```

Aggiungi a crontab:
```bash
crontab -e

# Ogni ora
0 * * * * /srv/mygest/scripts/monitor_performance.sh
```

---

## 📊 Checklist Finale

### Sviluppo
- [ ] Dipendenze installate (`pip list`)
- [ ] Redis running (`redis-cli ping`)
- [ ] Debug Toolbar visibile
- [ ] Cache funziona (test shell)
- [ ] Query ottimizzate (<50 per pagina)
- [ ] Nessun errore console

### Produzione
- [ ] settings_local.py configurato
- [ ] DEBUG = False
- [ ] SECRET_KEY cambiata
- [ ] ALLOWED_HOSTS impostati
- [ ] SSL/HTTPS attivo
- [ ] Redis con password
- [ ] pgBouncer configurato (opzionale)
- [ ] Staticfiles compressi
- [ ] Log rotation attivo
- [ ] Monitoring configurato
- [ ] Backup automatico attivo

---

## 🆘 Troubleshooting

### Redis non si connette

```bash
# Verifica servizio
sudo systemctl status redis-server

# Verifica bind
sudo netstat -tlnp | grep 6379

# Test connessione
redis-cli -h 127.0.0.1 -p 6379 ping
```

### Connection pool errors

```bash
# Verifica connessioni PostgreSQL
psql -U mygest_user -d mygest -c "SELECT * FROM pg_stat_activity;"

# Aumenta pool size in settings_local.py
DATABASES['default']['POOL_OPTIONS']['POOL_SIZE'] = 20
```

### Staticfiles non compressi

```bash
# Verifica django-compressor
python manage.py compress --force

# Debug compressor
python manage.py collectstatic --noinput -v 2
```

### Debug Toolbar non appare

```python
# settings_local.py
DEBUG = True
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Verifica middleware
# debug_toolbar.middleware deve essere PRIMO
```

---

## 📚 Risorse Utili

- [Django Caching Docs](https://docs.djangoproject.com/en/4.2/topics/cache/)
- [Django Debug Toolbar](https://django-debug-toolbar.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)
- [pgBouncer Guide](https://www.pgbouncer.org/)
- [Performance Guide completo](./PERFORMANCE_OPTIMIZATION_GUIDE.md)

---

## ✅ Completato!

Dopo aver seguito tutti i passaggi:
1. Sistema di caching attivo e funzionante
2. Query ottimizzate (N+1 risolto)
3. Connection pooling configurato
4. Staticfiles compressi
5. Debug tools attivi in sviluppo
6. Monitoring configurato

**Performance attesa:**
- Response time: -50% to -70%
- Query count: da 100+ a <20
- Cache hit rate: >80%
- Load time: -40% to -60%
