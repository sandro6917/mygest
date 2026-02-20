# Fix: IntegrityError su cancellazione Scadenza

## 🐛 Problema

Quando si elimina una `Scadenza` dall'admin Django, vengono sollevati errori di integrità referenziale:

### Errore 1: Violazione constraint su DELETE
```
IntegrityError: update or delete on table "scadenze_scadenzaoccorrenza" 
violates foreign key constraint "scadenze_scadenzanot_occorrenza_id_83672f59_fk_scadenze_" 
on table "scadenze_scadenzanotificalog"
DETAIL: Key (id)=(9) is still referenced from table "scadenze_scadenzanotificalog".
```

### Errore 2: Violazione constraint su INSERT (signal)
```
IntegrityError: insert or update on table "scadenze_scadenzanotificalog" 
violates foreign key constraint "scadenze_scadenzanot_occorrenza_id_83672f59_fk_scadenze_"
DETAIL: Key (occorrenza_id)=(11) is not present in table "scadenze_scadenzaoccorrenza".
```

## 🔍 Causa

Il problema aveva **due cause correlate**:

### Causa 1: Constraint non deferribili
I constraint delle foreign key nel database PostgreSQL non erano configurati come `DEFERRABLE`. 

Quando Django elimina una `Scadenza`:
1. Elimina tutte le `ScadenzaOccorrenza` correlate (CASCADE)
2. Ogni `ScadenzaOccorrenza` ha FK da:
   - `ScadenzaNotificaLog`
   - `ScadenzaAlert`
   - `ScadenzaWebhookPayload`

Anche se tutti i modelli Django hanno `on_delete=models.CASCADE`, i constraint nel database non erano deferribili, causando il fallimento dell'eliminazione quando PostgreSQL verificava i constraint prima che tutte le eliminazioni fossero completate.

### Causa 2: Signal post_delete problematico
Il signal `post_delete` per `_delete_calendar_event` cercava di creare un `ScadenzaNotificaLog` **dopo** che l'occorrenza era già stata eliminata dal database, violando il constraint FK.

```python
# PROBLEMA: post_delete viene eseguito DOPO l'eliminazione
post_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza)

def _delete_calendar_event(...):
    # L'occorrenza è già stata eliminata!
    ScadenzaNotificaLog.objects.create(
        occorrenza=instance,  # ❌ FK a record inesistente!
        ...
    )
```

## ✅ Soluzione

Implementate **3 fix complementari**:

### Fix 1: Migration `0009_fix_cascade_delete_constraints.py`

Ricrea i constraint FK con `ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED`:

1. **Ricrea constraint per `ScadenzaNotificaLog.occorrenza`**
   - Aggiunge `ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED`
   
2. **Ricrea constraint per `ScadenzaAlert.occorrenza`**
   - Aggiunge `ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED`
   
3. **Ricrea constraint per `ScadenzaWebhookPayload.occorrenza`**
   - Aggiunge `ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED`

### Fix 2: Signal modificati in `scadenze/models.py`

**Cambio da `post_delete` a `pre_delete`**:
```python
# PRIMA (❌ ERRORE):
post_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza)

# DOPO (✅ CORRETTO):
pre_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza)
```

**Gestione errori migliorata**:
```python
def _delete_calendar_event(sender, instance: ScadenzaOccorrenza, **_):
    """Signal pre_delete - l'occorrenza esiste ancora nel DB"""
    if not instance.google_calendar_event_id:
        return
    try:
        sync = GoogleCalendarSync()
        sync.delete_occurrence(instance)
    except Exception as exc:
        try:
            # ✅ L'occorrenza esiste ancora (pre_delete)
            ScadenzaNotificaLog.objects.create(
                occorrenza=instance,
                evento=ScadenzaNotificaLog.Evento.CALENDAR_SYNC,
                esito=False,
                messaggio=f"Delete failed: {exc}",
            )
        except Exception:
            # Ignora errori nel logging
            pass
```

**Signal `post_save` migliorato**:
```python
def _sync_calendar_after_save(sender, instance: ScadenzaOccorrenza, created, **kwargs):
    # ...
    try:
        sync.upsert_occurrence(instance)
    except Exception as exc:
        try:
            # ✅ Verifica che l'occorrenza esista prima di creare log
            if ScadenzaOccorrenza.objects.filter(pk=instance.pk).exists():
                ScadenzaNotificaLog.objects.create(...)
        except Exception:
            pass  # Non bloccare il salvataggio
```

### Fix 3: Migration `0010_cleanup_orphaned_logs.py`

Pulisce eventuali record orfani rimasti da operazioni precedenti:
- Elimina `ScadenzaNotificaLog` senza occorrenza valida
- Elimina `ScadenzaAlert` senza occorrenza valida
- Elimina `ScadenzaWebhookPayload` senza occorrenza valida

### Constraint Deferribili

L'opzione `DEFERRABLE INITIALLY DEFERRED` permette a PostgreSQL di:
- Posticipare il controllo dei constraint alla fine della transazione
- Permettere eliminazioni intermedie che temporaneamente violano i constraint
- Verificare la consistenza solo al COMMIT finale

## 📋 File Modificati

### Migration Create
- `scadenze/migrations/0009_fix_cascade_delete_constraints.py`
- `scadenze/migrations/0010_cleanup_orphaned_logs.py`

### Codice Modificato
- `scadenze/models.py`:
  - `_sync_calendar_after_save()` - Gestione errori migliorata
  - `_delete_calendar_event()` - Cambiato da `post_delete` a `pre_delete`
  - Signal connections - Usa `pre_delete` invece di `post_delete`

### Test Creati
- `scadenze/tests/test_cascade_delete.py`

### Documentazione
- `FIX_SCADENZA_DELETE_CASCADE.md` (questo file)

### Operazioni SQL
```sql
ALTER TABLE scadenze_scadenzanotificalog
DROP CONSTRAINT IF EXISTS scadenze_scadenzanot_occorrenza_id_83672f59_fk_scadenze_;

ALTER TABLE scadenze_scadenzanotificalog
ADD CONSTRAINT scadenze_scadenzanot_occorrenza_id_83672f59_fk_scadenze_
FOREIGN KEY (occorrenza_id)
REFERENCES scadenze_scadenzaoccorrenza(id)
ON DELETE CASCADE
DEFERRABLE INITIALLY DEFERRED;
```

## 🧪 Test

### Test Automatici

Creati test in `scadenze/tests/test_cascade_delete.py` che verificano:

1. **Eliminazione completa CASCADE**: Scadenza → Occorrenze → Log/Alert/Webhook
2. **Eliminazione singola occorrenza**: Mantiene altre occorrenze
3. **Eliminazione scadenza vuota**: Senza occorrenze
4. **Bulk delete**: Più scadenze contemporaneamente
5. **Isolamento dati**: Eliminazione non tocca scadenze non correlate

**Nota**: I test richiedono **PostgreSQL** e sono automaticamente skippati su SQLite (che non supporta completamente `DEFERRABLE` constraints).

Eseguire i test:

```bash
# Test specifici (richiede PostgreSQL configurato per test)
pytest scadenze/tests/test_cascade_delete.py -v

# I test verranno skippati se si usa SQLite
```

### Test Manuale dall'Admin Django

1. **Test manuale dall'Admin Django**:
   ```bash
   # Accedi a http://localhost:8000/admin/scadenze/scadenza/
   # Seleziona una scadenza
   # Elimina la scadenza
   # ✅ Dovrebbe essere eliminata senza errori
   ```

2. **Test da shell Django**:
   ```python
   from scadenze.models import Scadenza
   
   # Crea scadenza di test con occorrenze e log
   scadenza = Scadenza.objects.first()
   
   # Verifica che abbia occorrenze con log
   occorrenze = scadenza.occorrenze.all()
   for occ in occorrenze:
       print(f"Occorrenza {occ.id}: {occ.log_eventi.count()} log")
   
   # Elimina
   scadenza.delete()
   # ✅ Dovrebbe eliminare tutto in cascata
   ```

## 🔒 Business Rules Rispettate

Questa fix mantiene tutte le business rules esistenti:
- ✅ Eliminazione cascata di ScadenzaOccorrenza quando si elimina Scadenza
- ✅ Eliminazione cascata di ScadenzaNotificaLog quando si elimina ScadenzaOccorrenza
- ✅ Eliminazione cascata di ScadenzaAlert quando si elimina ScadenzaOccorrenza
- ✅ Eliminazione cascata di ScadenzaWebhookPayload quando si elimina ScadenzaOccorrenza
- ✅ Integrità referenziale mantenuta durante tutta la transazione

## 📝 Note Tecniche

### Perché DEFERRABLE?

I constraint deferribili sono essenziali quando si ha una catena di eliminazioni CASCADE:

```
Scadenza (DELETE)
  └─> ScadenzaOccorrenza (DELETE CASCADE)
       ├─> ScadenzaNotificaLog (DELETE CASCADE)
       ├─> ScadenzaAlert (DELETE CASCADE)
       └─> ScadenzaWebhookPayload (DELETE CASCADE)
```

Senza `DEFERRABLE`:
- PostgreSQL controlla i constraint immediatamente dopo ogni DELETE
- Quando elimina `ScadenzaOccorrenza`, trova ancora record in `ScadenzaNotificaLog`
- Solleva IntegrityError

Con `DEFERRABLE INITIALLY DEFERRED`:
- PostgreSQL accumula tutti i DELETE nella transazione
- Controlla i constraint solo al COMMIT
- Tutti i record sono già eliminati, nessun errore

### Compatibilità

- ✅ PostgreSQL 10+
- ✅ Django 4.2+
- ✅ Django REST Framework 3.15+
- ⚠️ Non compatibile con SQLite (non supporta `DEFERRABLE` completamente)

## 🚀 Deployment

```bash
# Applica migration sul server di produzione
ssh mygest@72.62.34.249
cd /srv/mygest/app
source venv/bin/activate
python manage.py migrate scadenze

# Restart gunicorn se necessario
sudo systemctl restart gunicorn-mygest
```

## 🎯 Checklist Post-Fix

- [x] Migration 0009 creata (constraint deferribili)
- [x] Migration 0010 creata (cleanup orfani)
- [x] Migrations applicate sul database locale
- [x] Signal modificati (`pre_delete` invece di `post_delete`)
- [x] Gestione errori migliorata nei signal
- [x] Test automatici creati (`test_cascade_delete.py`)
- [ ] Test manuale dall'admin Django con database PostgreSQL
- [ ] Deploy su produzione
- [ ] Verifica funzionamento in produzione

---

**Data Fix**: 03/02/2026  
**Django Version**: 5.2.8  
**PostgreSQL Version**: 14+  
**Sviluppatore**: Sandro Chimenti
