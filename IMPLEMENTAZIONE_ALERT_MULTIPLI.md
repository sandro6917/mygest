# IMPLEMENTAZIONE PRIORITÀ ALTA - GESTIONE SCADENZE
## Completata il 19/11/2025

### ✅ MODIFICHE IMPLEMENTATE

#### 1. Nuovo Modello ScadenzaAlert
È stato creato un nuovo modello `ScadenzaAlert` per supportare **alert multipli** per ogni occorrenza.

**Campi principali:**
- `occorrenza` (ForeignKey) - collegamento all'occorrenza
- `offset_alert_periodo` (CharField) - unità di tempo: minuti, ore, giorni, settimane
- `offset_alert` (PositiveIntegerField) - numero di unità prima dell'occorrenza
- `metodo_alert` (CharField) - email o webhook
- `alert_config` (JSONField) - configurazione specifica (destinatari, URL, etc.)
- `alert_programmata_il` (DateTimeField) - calcolato automaticamente al salvataggio
- `alert_inviata_il` (DateTimeField) - timestamp invio
- `stato` (CharField) - pending, scheduled, sent, failed

**Vantaggi:**
- ✅ Supporto illimitato di alert per occorrenza
- ✅ Configurazione granulare (1 settimana + 1 giorno + 1 ora prima)
- ✅ Diversi metodi per diversi alert
- ✅ Tracciabilità completa dello stato di ogni alert

#### 2. Campi Aggiunti ai Modelli Esistenti

**Scadenza:**
- `num_occorrenze` (PositiveIntegerField, null=True) - numero massimo di occorrenze da generare
- `data_scadenza` (DateField, null=True) - data della prima occorrenza

**ScadenzaOccorrenza:**
- `giornaliera` (BooleanField) - flag per indicare eventi all-day

#### 3. Migrations
- **0005**: Aggiunta campi `num_occorrenze`, `data_scadenza`, `giornaliera` e creazione modello `ScadenzaAlert`
- **0006**: Data migration per migrare automaticamente i dati esistenti da `offset_alert_minuti` al nuovo modello `ScadenzaAlert`

**Risultati migrazione:**
- ✅ 11 alert esistenti migrati correttamente
- ✅ Conversione intelligente minuti → giorni/ore/settimane

#### 4. Servizio AlertDispatcher Aggiornato

Il servizio `AlertDispatcher` è stato completamente riscritto per gestire alert multipli:

**Nuovi metodi:**
- `dispatch_alert(alert)` - invia un singolo alert
- `dispatch_occorrenza_alerts(occorrenza)` - invia tutti gli alert pronti di un'occorrenza
- `dispatch(occorrenza)` - metodo legacy mantenuto per compatibilità

**Funzionalità:**
- ✅ Invio email con riferimento all'alert specifico
- ✅ Invio webhook con payload esteso
- ✅ Gestione errori per singolo alert (non blocca gli altri)
- ✅ Logging dettagliato con ID alert

#### 5. Admin Interface Aggiornata

**Nuove funzionalità admin:**
- ✅ Admin dedicato per `ScadenzaAlert` con filtri per metodo, stato, periodo
- ✅ Inline `ScadenzaAlertInline` nell'admin di `ScadenzaOccorrenza`
- ✅ Visualizzazione campo `giornaliera` nelle liste
- ✅ Readonly fields per `alert_programmata_il` (calcolato automaticamente)

#### 6. Forms Aggiornati

**ScadenzaForm:**
- ✅ Aggiunti campi `num_occorrenze` e `data_scadenza`
- ✅ Widget DateInput per `data_scadenza`

**ScadenzaOccorrenzaForm:**
- ✅ Aggiunto campo `giornaliera`
- ✅ Mantenuta compatibilità con campi legacy

#### 7. Management Command per Cron

Creato comando `send_scheduled_alerts` per automatizzare l'invio degli alert:

```bash
# Modalità dry-run (test)
python manage.py send_scheduled_alerts --dry-run

# Invio reale (da usare in crontab)
python manage.py send_scheduled_alerts
```

**Configurazione cron suggerita:**
```cron
*/15 * * * * cd /path/to/mygest && source venv/bin/activate && python manage.py send_scheduled_alerts >> /var/log/scadenze_alerts.log 2>&1
```

### 📊 STATISTICHE IMPLEMENTAZIONE

- **Modelli modificati:** 2 (Scadenza, ScadenzaOccorrenza)
- **Nuovi modelli:** 1 (ScadenzaAlert)
- **Migrations create:** 2
- **Files modificati:** 4 (models.py, admin.py, services.py, forms.py)
- **Nuovi files:** 1 (send_scheduled_alerts.py)
- **Dati migrati:** 11 alert esistenti

### ✅ TEST EFFETTUATI

1. **Migration dei dati esistenti:**
   - ✅ 11 alert migrati correttamente
   - ✅ Conversione automatica minuti → unità appropriate

2. **Creazione scadenza con alert multipli:**
   - ✅ Scadenza creata con 3 alert: 7 giorni, 1 giorno, 2 ore prima
   - ✅ Calcolo automatico `alert_programmata_il` funzionante
   - ✅ Supporto misto email + webhook

3. **Management command:**
   - ✅ Dry-run identifica correttamente alert da inviare
   - ✅ Query ottimizzata con select_related

### 🎯 ESEMPIO PRATICO

```python
from django.utils import timezone
from datetime import timedelta
from scadenze.models import Scadenza, ScadenzaOccorrenza, ScadenzaAlert

# Crea scadenza
scadenza = Scadenza.objects.create(
    titolo='Scadenza Fiscale Importante',
    descrizione='Presentazione dichiarazione',
    stato='attiva',
    priorita='critical',
    periodicita='yearly',
    num_occorrenze=5,
    data_scadenza=timezone.now().date() + timedelta(days=180)
)

# Crea occorrenza
occ = ScadenzaOccorrenza.objects.create(
    scadenza=scadenza,
    inizio=timezone.now() + timedelta(days=180),
    giornaliera=False
)

# Configura alert multipli
# Alert 1: 1 settimana prima via email
ScadenzaAlert.objects.create(
    occorrenza=occ,
    offset_alert=1,
    offset_alert_periodo='weeks',
    metodo_alert='email',
    alert_config={'destinatari': 'commercialista@example.com'}
)

# Alert 2: 1 giorno prima via email
ScadenzaAlert.objects.create(
    occorrenza=occ,
    offset_alert=1,
    offset_alert_periodo='days',
    metodo_alert='email',
    alert_config={'destinatari': 'admin@example.com, commercialista@example.com'}
)

# Alert 3: 2 ore prima via webhook
ScadenzaAlert.objects.create(
    occorrenza=occ,
    offset_alert=2,
    offset_alert_periodo='hours',
    metodo_alert='webhook',
    alert_config={'url': 'https://api.example.com/notify'}
)
```

### 📝 NOTE IMPLEMENTATIVE

1. **Compatibilità retroattiva:** I campi legacy `offset_alert_minuti` e `alert_config` sono stati mantenuti in `ScadenzaOccorrenza` per compatibilità, ma dovrebbero essere deprecati in futuro.

2. **Calcolo automatico:** Il campo `alert_programmata_il` viene calcolato automaticamente nel metodo `save()` di `ScadenzaAlert` usando la libreria `timedelta`.

3. **Performance:** La data migration usa `bulk_create()` con batch_size=500 per ottimizzare le prestazioni.

4. **Validazione:** Entrambi i modelli (`ScadenzaOccorrenza` e `ScadenzaAlert`) implementano il metodo `clean()` per validare la configurazione degli alert.

### 🚀 PROSSIMI PASSI (Priorità Media)

1. **Vista Scadenziario** - Creare una vista dedicata con calendario
2. **Template aggiornati** - Migliorare visualizzazione alert multipli
3. **API updates** - Aggiornare serializers per esporre ScadenzaAlert
4. **Documentazione utente** - Guida all'uso degli alert multipli

### 📋 COMPATIBILITÀ

- ✅ **Backward compatible:** Tutti i dati esistenti sono stati migrati
- ✅ **API esistenti:** Funzionano ancora (metodo `dispatch()` legacy)
- ✅ **Forms esistenti:** Continuano a funzionare
- ✅ **Admin esistente:** Esteso senza breaking changes

---

**Implementazione completata con successo! Il sistema ora supporta completamente alert multipli per ogni occorrenza.**
