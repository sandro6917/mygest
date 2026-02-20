# 🔍 Analisi Sistema Alert Scadenze MyGest

**Data analisi**: 2 Febbraio 2026  
**Analista**: GitHub Copilot  
**Status**: ⚠️ Sistema NON funzionante - Problemi critici identificati

---

## 📊 Stato Attuale del Sistema

### Database
- ✅ **Scadenze**: 14 totali, 2 attive
- ✅ **Occorrenze**: 76 totali, 61 future
- ⚠️  **Alert**: 18 totali
  - 17 pendenti (non inviati)
  - 1 inviato
  - 0 falliti
- ✅ **Log**: 139 eventi registrati
  - 71 successi
  - 68 errori (tutti Google Calendar, non alert)

### Test Funzionalità
- ✅ **Validazione email**: Funzionante
- ✅ **Validazione webhook**: Funzionante
- ✅ **Calcolo timing**: Funzionante
- ✅ **AlertDispatcher**: Tutti i metodi presenti
- ✅ **Comando send_scheduled_alerts**: Eseguibile manualmente
- ❌ **Cron job**: NON configurato (problema critico)

---

## 🚨 Problemi Critici Identificati

### 1️⃣ **CRON JOB MANCANTE** (CRITICO)

**Problema**: Il comando `send_scheduled_alerts` non è configurato nel crontab.

**Impatto**: Gli alert NON vengono inviati automaticamente, anche se sono correttamente configurati.

**Stato attuale crontab**:
```bash
# Solo questo comando è configurato:
0 1 * * * cd /home/sandro/mygest && .../python manage.py aggiorna_stati_scadenze
```

**Alert scaduti non inviati**: 5 alert (di cui 2 di oggi stesso)

**Soluzione**: Vedi sezione "Soluzioni" sotto.

---

### 2️⃣ **Alert Email senza Destinatari** (ALTO)

**Problema**: 9 alert email configurati SENZA destinatari.

**Alert problematici**:
- ID 18: "Invio emens dicembre 2025" (scaduto oggi)
- ID 16: "Piano di rateizzazione..."
- ID 3, 4, 1: Vari alert

**Configurazione attuale**:
- `scadenza.comunicazione_destinatari`: vuoto
- `alert.alert_config`: `{}`

**Impatto**: Questi alert falliranno durante l'invio con errore di validazione.

---

### 3️⃣ **Alert Webhook senza URL** (ALTO)

**Problema**: 2 alert webhook configurati SENZA URL.

**Alert problematici**:
- ID 17: "Invio emens dicembre 2025" (scaduto oggi)
- ID 15: "Piano di rateizzazione..."

**Configurazione attuale**:
- `alert.alert_config`: `{}`

**Impatto**: Questi alert falliranno durante l'invio con errore di validazione.

---

### 4️⃣ **Alert Scaduti Non Processati** (MEDIO)

**Problema**: 5 alert con `alert_programmata_il` nel passato e `stato=pending`.

**Alert scaduti**:
1. ID 12: Test Alert Multipli (7 giorni prima) - scaduto 19/11/2025
2. ID 13: Test Alert Multipli (1 giorno prima) - scaduto 25/11/2025
3. ID 14: Test Alert Multipli (webhook) - scaduto 26/11/2025
4. ID 18: Invio emens (35 min prima) - scaduto oggi 02/02/2026 11:25
5. ID 17: Invio emens (webhook 30 min prima) - scaduto oggi 02/02/2026 11:30

**Causa**: Cron job non configurato (problema #1).

---

## ✅ Aspetti Funzionanti

### Validazione
- ✅ Alert email senza destinatari vengono BLOCCATI in `clean()`
- ✅ Alert webhook senza URL vengono BLOCCATI in `clean()`
- ✅ Messaggi di errore chiari e comprensibili

### Calcolo Timing
- ✅ `alert_programmata_il` calcolato automaticamente al salvataggio
- ✅ Supporto per minuti, ore, giorni, settimane
- ✅ Precisione al millisecondo

### AlertDispatcher
- ✅ Tutti i metodi implementati correttamente
- ✅ `dispatch_alert()`: invio singolo alert
- ✅ `dispatch_occorrenza_alerts()`: invio multipli alert per occorrenza
- ✅ `_send_email_alert()`: creazione comunicazione
- ✅ `_send_webhook_alert()`: invio HTTP POST
- ✅ Gestione errori con logging

### Comando Management
- ✅ `send_scheduled_alerts` funziona correttamente
- ✅ Flag `--dry-run` per test
- ✅ Output dettagliato e informativo
- ✅ Gestione errori robusta

---

## 🔧 Soluzioni Proposte

### Soluzione #1: Configurare Cron Job (URGENTE)

**Azione**: Aggiungere il comando al crontab per esecuzione ogni 10 minuti.

**Comando crontab**:
```bash
*/10 * * * * cd /home/sandro/mygest && source venv/bin/activate && python manage.py send_scheduled_alerts >> /home/sandro/mygest/logs/alerts.log 2>&1
```

**Procedura**:
```bash
# 1. Aprire crontab
crontab -e

# 2. Aggiungere la riga sopra

# 3. Salvare e uscire

# 4. Verificare
crontab -l | grep send_scheduled_alerts
```

**Impatto**: Risolve completamente il problema dell'invio automatico.

---

### Soluzione #2: Correggere Alert Email Senza Destinatari

**Azione**: Configurare destinatari per i 9 alert email problematici.

**Opzione A - Destinatari nella Scadenza** (consigliato):
```python
# Per ogni scadenza problematica
scadenza = Scadenza.objects.get(pk=...)
scadenza.comunicazione_destinatari = "destinatario@example.com, altro@example.com"
scadenza.save()
```

**Opzione B - Destinatari nell'Alert**:
```python
# Per ogni alert problematico
alert = ScadenzaAlert.objects.get(pk=18)
alert.alert_config = {'destinatari': 'destinatario@example.com'}
alert.save()
```

**Script automatico** (vedi `fix_alert_configuration.py` sotto).

---

### Soluzione #3: Correggere Alert Webhook Senza URL

**Azione**: Configurare URL per i 2 alert webhook problematici.

```python
# Alert ID 17
alert = ScadenzaAlert.objects.get(pk=17)
alert.alert_config = {
    'url': 'https://api.example.com/webhooks/scadenze',
    'timeout': 10
}
alert.save()

# Alert ID 15
alert = ScadenzaAlert.objects.get(pk=15)
alert.alert_config = {
    'url': 'https://api.example.com/webhooks/scadenze',
    'timeout': 10
}
alert.save()
```

**Script automatico** (vedi `fix_alert_configuration.py` sotto).

---

### Soluzione #4: Processare Alert Scaduti

**Azione**: Decidere cosa fare con i 5 alert scaduti.

**Opzione A - Inviarli ora** (se ancora rilevanti):
```bash
cd /home/sandro/mygest
source venv/bin/activate
python manage.py send_scheduled_alerts
```

**Opzione B - Segnarli come completati** (se non più rilevanti):
```python
from scadenze.models import ScadenzaAlert
from django.utils import timezone

# Alert di test (ID 12, 13, 14)
ScadenzaAlert.objects.filter(pk__in=[12, 13, 14]).update(
    stato='cancelled'
)

# Alert reali (ID 17, 18) - VERIFICARE PRIMA SE INVIARE
```

---

## 📝 Script di Fix Automatico

Vedi file `fix_alert_configuration.py` per uno script completo che:
1. Identifica tutti gli alert problematici
2. Propone correzioni
3. Applica le fix (con conferma utente)

---

## 🧪 Test di Verifica Post-Fix

Dopo aver applicato le soluzioni, eseguire:

```bash
# 1. Verifica cron job
crontab -l | grep send_scheduled_alerts

# 2. Test manuale invio alert
cd /home/sandro/mygest
source venv/bin/activate
python manage.py send_scheduled_alerts --dry-run

# 3. Verifica configurazione alert
python manage.py shell -c "
from scadenze.models import ScadenzaAlert
email_no_dest = ScadenzaAlert.objects.filter(
    metodo_alert='email',
    alert_config={},
    occorrenza__scadenza__comunicazione_destinatari=''
).count()
webhook_no_url = ScadenzaAlert.objects.filter(
    metodo_alert='webhook',
    alert_config={}
).count()
print(f'Alert email senza dest: {email_no_dest}')
print(f'Alert webhook senza URL: {webhook_no_url}')
"

# 4. Monitora log
tail -f /home/sandro/mygest/logs/alerts.log
```

---

## 📈 Raccomandazioni Future

### Prevenzione

1. **Validazione UI**: Aggiungere validazione nel frontend per bloccare la creazione di alert senza configurazione completa.

2. **Alert Template**: Creare template di alert pre-configurati per facilitare la configurazione.

3. **Dashboard Monitoraggio**: Aggiungere una pagina di amministrazione che mostri:
   - Alert pendenti
   - Alert falliti
   - Configurazioni incomplete

4. **Notifiche Admin**: Inviare email agli admin quando un alert fallisce.

### Monitoraggio

1. **Log Rotation**: Configurare logrotate per `/home/sandro/mygest/logs/alerts.log`

2. **Healthcheck**: Creare endpoint API per verificare salute del sistema alert:
   ```python
   GET /api/v1/scadenze/alert-health/
   {
     "pending_alerts": 17,
     "overdue_alerts": 5,
     "misconfigured_alerts": 11,
     "last_cron_run": "2026-02-02 12:00:00",
     "status": "unhealthy"
   }
   ```

3. **Metrics**: Integrare con sistema di metriche (Prometheus, Grafana) per:
   - Alert inviati/falliti nel tempo
   - Tempo medio di invio
   - Rate di successo

---

## 📋 Checklist Completa

### Immediate (Oggi)
- [ ] Configurare cron job `send_scheduled_alerts`
- [ ] Correggere 9 alert email senza destinatari
- [ ] Correggere 2 alert webhook senza URL
- [ ] Decidere cosa fare con 5 alert scaduti
- [ ] Testare invio manuale alert

### Breve Termine (Questa settimana)
- [ ] Creare directory `/home/sandro/mygest/logs/` se non esiste
- [ ] Configurare log rotation
- [ ] Documentare processo di configurazione alert
- [ ] Aggiungere validazione nel frontend

### Medio Termine (Questo mese)
- [ ] Implementare dashboard monitoraggio alert
- [ ] Creare template alert predefiniti
- [ ] Implementare healthcheck endpoint
- [ ] Setup notifiche admin per alert falliti

---

## 📞 Contatti & Support

Per problemi o domande sul sistema di alert:
- **Developer**: Sandro Chimenti
- **Documentazione**: `/home/sandro/mygest/docs/`
- **Log**: `/home/sandro/mygest/logs/alerts.log`

---

**Fine Analisi** - Generato automaticamente da GitHub Copilot
