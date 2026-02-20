# 🛠️ GUIDA RAPIDA: Risoluzione Problemi Alert Scadenze

**Data**: 2 Febbraio 2026  
**Versione**: 1.0  
**Urgenza**: 🔴 ALTA (sistema non funzionante)

---

## 🎯 Problema Principale

Il sistema di alert per le scadenze **NON sta inviando notifiche automaticamente**.

**Causa**: Cron job mancante + Alert mal configurati

---

## ⚡ Soluzione Rapida (5 minuti)

### Step 1: Configurare Cron Job (CRITICO)

```bash
# 1. Aprire crontab
crontab -e

# 2. Aggiungere questa riga alla fine del file:
*/10 * * * * cd /home/sandro/mygest && source venv/bin/activate && python manage.py send_scheduled_alerts >> /home/sandro/mygest/logs/alerts.log 2>&1

# 3. Salvare e uscire (Ctrl+X, poi Y, poi Enter in nano)

# 4. Verificare che sia stato aggiunto
crontab -l | grep send_scheduled_alerts
```

**Cosa fa**: Esegue il comando di invio alert ogni 10 minuti.

---

### Step 2: Creare Directory Log

```bash
mkdir -p /home/sandro/mygest/logs
touch /home/sandro/mygest/logs/alerts.log
```

---

### Step 3: Correggere Alert Mal Configurati

```bash
cd /home/sandro/mygest
source venv/bin/activate

# Analizza problemi (senza modificare nulla)
python fix_alert_configuration.py --dry-run

# Applica correzioni (interattivo)
python fix_alert_configuration.py
```

Lo script ti guiderà nella configurazione dei:
- **9 alert email** senza destinatari
- **2 alert webhook** senza URL
- **5 alert scaduti** da gestire

---

### Step 4: Test Funzionamento

```bash
# Test senza inviare (dry-run)
python manage.py send_scheduled_alerts --dry-run

# Dovrebbe mostrare gli alert pronti per essere inviati

# Invio effettivo (se ci sono alert scaduti da inviare)
python manage.py send_scheduled_alerts
```

---

## 📊 Problemi Identificati

### 1. Cron Job Mancante ⚠️ CRITICO
- **Problema**: Il comando `send_scheduled_alerts` non è nel crontab
- **Impatto**: Alert non vengono inviati automaticamente
- **Soluzione**: Vedi Step 1 sopra

### 2. Alert Email Senza Destinatari (9 alert)
- **Alert IDs**: 18, 16, 3, 4, 1, 7, 8, 5, 2
- **Problema**: Né `scadenza.comunicazione_destinatari` né `alert.alert_config` hanno email
- **Impatto**: Alert falliranno durante l'invio
- **Soluzione**: Script di fix (Step 3)

### 3. Alert Webhook Senza URL (2 alert)
- **Alert IDs**: 17, 15
- **Problema**: `alert.alert_config` non ha campo `url`
- **Impatto**: Webhook falliranno durante l'invio
- **Soluzione**: Script di fix (Step 3)

### 4. Alert Scaduti Non Inviati (5 alert)
- **Alert IDs**: 12, 13, 14 (test), 17, 18 (reali - oggi!)
- **Problema**: Tempo di invio già passato ma stato ancora "pending"
- **Impatto**: Notifiche mai ricevute
- **Soluzione**: Decidere se inviare ora o annullare (Step 3)

---

## 🧪 Verifica Finale

Dopo aver completato tutti gli step, verifica che tutto funzioni:

```bash
cd /home/sandro/mygest
source venv/bin/activate

# 1. Verifica cron job
echo "=== CRON JOB ==="
crontab -l | grep send_scheduled_alerts

# 2. Verifica alert mal configurati
echo -e "\n=== ALERT MAL CONFIGURATI ==="
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
print(f'Alert email senza destinatari: {email_no_dest}')
print(f'Alert webhook senza URL: {webhook_no_url}')
if email_no_dest == 0 and webhook_no_url == 0:
    print('✅ Tutti gli alert configurati correttamente!')
else:
    print('⚠️  Ci sono ancora alert da configurare')
"

# 3. Verifica alert pendenti
echo -e "\n=== ALERT PENDENTI ==="
python manage.py shell -c "
from scadenze.models import ScadenzaAlert
from django.utils import timezone
now = timezone.now()
pending = ScadenzaAlert.objects.filter(stato='pending').count()
overdue = ScadenzaAlert.objects.filter(stato='pending', alert_programmata_il__lt=now).count()
future = ScadenzaAlert.objects.filter(stato='pending', alert_programmata_il__gte=now).count()
print(f'Totale alert pendenti: {pending}')
print(f'  - Scaduti: {overdue}')
print(f'  - Futuri: {future}')
"

# 4. Test dry-run
echo -e "\n=== TEST DRY-RUN ==="
python manage.py send_scheduled_alerts --dry-run
```

**Output atteso**:
```
=== CRON JOB ===
*/10 * * * * cd /home/sandro/mygest && ...send_scheduled_alerts...

=== ALERT MAL CONFIGURATI ===
Alert email senza destinatari: 0
Alert webhook senza URL: 0
✅ Tutti gli alert configurati correttamente!

=== ALERT PENDENTI ===
Totale alert pendenti: 12
  - Scaduti: 0
  - Futuri: 12

=== TEST DRY-RUN ===
Nessun alert da inviare al momento.
```

---

## 📈 Monitoraggio Continuo

### Visualizza Log Alert

```bash
# Ultimi 50 log
tail -50 /home/sandro/mygest/logs/alerts.log

# Segui log in tempo reale
tail -f /home/sandro/mygest/logs/alerts.log

# Cerca errori
grep -i error /home/sandro/mygest/logs/alerts.log
```

### Controlla Stato Alert (Comando Rapido)

Crea un alias per controllo veloce:

```bash
# Aggiungi a ~/.bashrc
alias check-alerts="cd /home/sandro/mygest && source venv/bin/activate && python manage.py shell -c \"
from scadenze.models import ScadenzaAlert
from django.utils import timezone
now = timezone.now()
pending = ScadenzaAlert.objects.filter(stato='pending').count()
overdue = ScadenzaAlert.objects.filter(stato='pending', alert_programmata_il__lt=now).count()
sent = ScadenzaAlert.objects.filter(stato='sent').count()
failed = ScadenzaAlert.objects.filter(stato='failed').count()
print(f'Alert: {pending} pending ({overdue} overdue) | {sent} sent | {failed} failed')
\""

# Ricarica bashrc
source ~/.bashrc

# Usa comando
check-alerts
```

---

## 🔧 Troubleshooting

### "Cron job non esegue il comando"

**Possibili cause**:
1. Percorso errato al virtual environment
2. Variabili ambiente mancanti
3. Permessi file

**Soluzione**:
```bash
# Test manuale del comando esatto del cron
cd /home/sandro/mygest && source venv/bin/activate && python manage.py send_scheduled_alerts

# Se funziona manualmente, verifica il cron
# Controlla i log di sistema
grep CRON /var/log/syslog | tail -20
```

### "Alert inviati ma email non ricevute"

**Causa**: Il sistema crea `Comunicazione` ma non invia email SMTP direttamente.

**Soluzione**: Verifica configurazione app Comunicazioni per invio email effettivo.

### "Webhook falliscono con timeout"

**Soluzione**: Aumenta timeout nell'alert config:
```python
alert.alert_config = {
    'url': 'https://slow-api.example.com/webhook',
    'timeout': 30  # default è 10 secondi
}
alert.save()
```

---

## 📝 Configurazione Nuovi Alert

### Esempio: Alert Email

```python
from scadenze.models import Scadenza, ScadenzaOccorrenza, ScadenzaAlert
from django.utils import timezone
from datetime import timedelta

# 1. Crea/modifica scadenza con destinatari predefiniti
scadenza = Scadenza.objects.create(
    titolo="Scadenza Fiscale",
    comunicazione_destinatari="admin@studio.it, contabile@studio.it"
)

# 2. Crea occorrenza
occorrenza = ScadenzaOccorrenza.objects.create(
    scadenza=scadenza,
    inizio=timezone.now() + timedelta(days=30)  # tra 30 giorni
)

# 3. Crea alert (7 giorni prima)
alert = ScadenzaAlert.objects.create(
    occorrenza=occorrenza,
    offset_alert=7,
    offset_alert_periodo='days',
    metodo_alert='email',
    alert_config={
        'destinatari': 'cliente@example.com'  # destinatari aggiuntivi
    }
)
# alert_programmata_il viene calcolato automaticamente!
```

### Esempio: Alert Webhook

```python
alert_webhook = ScadenzaAlert.objects.create(
    occorrenza=occorrenza,
    offset_alert=2,
    offset_alert_periodo='hours',
    metodo_alert='webhook',
    alert_config={
        'url': 'https://api.example.com/scadenze/webhook',
        'timeout': 10,
        'payload': {  # opzionale - payload personalizzato
            'cliente_id': 123,
            'tipo': 'fiscale'
        }
    }
)
```

---

## 📚 File Utili

- **Analisi completa**: `/home/sandro/mygest/ANALISI_ALERT_SYSTEM.md`
- **Script fix**: `/home/sandro/mygest/fix_alert_configuration.py`
- **Script test**: `/home/sandro/mygest/test_alert_system.py`
- **Log alert**: `/home/sandro/mygest/logs/alerts.log`
- **Comando invio**: `scadenze/management/commands/send_scheduled_alerts.py`
- **Service alert**: `scadenze/services.py` (classe `AlertDispatcher`)

---

## ✅ Checklist Completamento

- [ ] Cron job configurato e verificato
- [ ] Directory `/home/sandro/mygest/logs/` creata
- [ ] Alert email configurati con destinatari
- [ ] Alert webhook configurati con URL
- [ ] Alert scaduti gestiti (inviati o annullati)
- [ ] Test dry-run eseguito con successo
- [ ] Monitoraggio log attivo
- [ ] Documentazione letta e compresa

---

## 🆘 Supporto

Se hai problemi o domande:

1. **Controlla log**: `tail -f /home/sandro/mygest/logs/alerts.log`
2. **Analisi problemi**: `python fix_alert_configuration.py --dry-run`
3. **Test manuale**: `python manage.py send_scheduled_alerts --dry-run`
4. **Documentazione**: Leggi `ANALISI_ALERT_SYSTEM.md`

---

**Ultimo aggiornamento**: 2 Febbraio 2026  
**Autore**: GitHub Copilot Assistant
