# Sincronizzazione Google Calendar

## Script di Sincronizzazione Manuale

È disponibile un comando Django per sincronizzare manualmente le occorrenze con Google Calendar.

### Comandi Disponibili

#### Sincronizzazione Base (Future non sincronizzate)
```bash
python manage.py sync_google_calendar
```
Sincronizza solo le occorrenze future che non sono ancora state sincronizzate.

#### Modalità Dry-Run (Anteprima)
```bash
python manage.py sync_google_calendar --dry-run
```
Mostra quali occorrenze verrebbero sincronizzate senza effettuare modifiche.

#### Sincronizza Tutte le Occorrenze
```bash
python manage.py sync_google_calendar --all
```
Ri-sincronizza tutte le occorrenze, incluse quelle già sincronizzate.

#### Sincronizza Solo Non Sincronizzate
```bash
python manage.py sync_google_calendar --non-synced
```
Sincronizza tutte le occorrenze che non sono mai state sincronizzate (incluse quelle passate).

#### Sincronizza da una Data Specifica
```bash
python manage.py sync_google_calendar --from-date 2025-12-01
```
Sincronizza le occorrenze a partire da una data specifica.

#### Sincronizza una Singola Occorrenza
```bash
python manage.py sync_google_calendar --occorrenza-id 123
```
Sincronizza una specifica occorrenza tramite il suo ID.

#### Forza Sincronizzazione (Incluse Annullate)
```bash
python manage.py sync_google_calendar --all --force
```
⚠️ **Attenzione**: Include anche le occorrenze annullate (sconsigliato).

### Combinazioni Utili

#### Ri-sincronizza occorrenze del mese corrente
```bash
python manage.py sync_google_calendar --from-date 2025-11-01 --all
```

#### Anteprima di tutte le occorrenze non sincronizzate
```bash
python manage.py sync_google_calendar --non-synced --dry-run
```

#### Sincronizza occorrenze future con conferma
```bash
python manage.py sync_google_calendar
# Ti chiederà conferma se ci sono più di 10 occorrenze
```

## Sincronizzazione Automatica

La sincronizzazione avviene automaticamente tramite signal Django quando:
- Viene creata una nuova occorrenza
- Viene modificata un'occorrenza esistente
- Lo stato dell'occorrenza cambia (eccetto quando viene annullata)

### Configurazione Richiesta

Assicurati che nelle settings Django siano configurati:
```python
GOOGLE_CALENDAR_CREDENTIALS_FILE = "/path/to/credentials.json"
GOOGLE_CALENDAR_DEFAULT_ID = "your-calendar-id@group.calendar.google.com"
```

## Test

Per testare la sincronizzazione:
```bash
python manage.py test scadenze.tests.test_google_calendar_sync
```

Gli 8 test disponibili verificano:
- Creazione nuovi eventi
- Aggiornamento eventi esistenti
- Eliminazione eventi
- Calendari personalizzati
- Signal automatici
- Gestione errori
- Fallback titolo/descrizione
- Esclusione occorrenze annullate

## Troubleshooting

### Errore di autenticazione
Se ricevi errori di autenticazione:
1. Verifica che il file credentials.json esista e sia leggibile
2. Controlla che le credenziali non siano scadute
3. Verifica gli scope necessari nel file credentials

### Occorrenze non sincronizzate
Se alcune occorrenze non vengono sincronizzate:
```bash
# Verifica lo stato
python manage.py sync_google_calendar --dry-run

# Forza la sincronizzazione
python manage.py sync_google_calendar --all
```

### Loop infiniti nei test
I test gestiscono automaticamente i signal per evitare loop. In produzione, il flag `_syncing_calendar` previene loop infiniti durante il salvataggio.

## Logging

I log di sincronizzazione sono salvati nel modello `ScadenzaNotificaLog` con evento `CALENDAR_SYNC`.

Per vedere gli ultimi log:
```python
from scadenze.models import ScadenzaNotificaLog

# Ultimi 10 sync
logs = ScadenzaNotificaLog.objects.filter(
    evento='calendar_sync'
).order_by('-registrato_il')[:10]

for log in logs:
    print(f"{log.registrato_il}: {log.messaggio} - {'✓' if log.esito else '✗'}")
```
