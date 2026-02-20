# 🚨 Errore: "Nessun calendar ID configurato"

## Problema

Quando esegui `python manage.py sync_google_calendar --all` ottieni:
```
✗ Errore per [Nome Scadenza]: Nessun calendar ID configurato
```

## Causa

La sincronizzazione con Google Calendar non è ancora configurata.

## Soluzione Rapida

### 1. Verifica la Configurazione

```bash
python check_google_calendar_config.py
```

Questo script ti dirà esattamente cosa manca.

### 2. Configura Google Calendar

Segui la guida completa: **[docs/GOOGLE_CALENDAR_SETUP.md](docs/GOOGLE_CALENDAR_SETUP.md)**

Oppure esegui questi passaggi rapidi:

#### A. Crea Service Account su Google Cloud

1. Vai su https://console.cloud.google.com/
2. Crea/seleziona un progetto
3. Abilita "Google Calendar API"
4. Crea un Service Account
5. Scarica le credenziali JSON

#### B. Configura le Credenziali

```bash
# Crea directory secrets
mkdir -p /home/sandro/mygest/secrets

# Copia le credenziali scaricate
cp ~/Downloads/your-credentials.json /home/sandro/mygest/secrets/google_credentials.json

# Imposta permessi
chmod 600 /home/sandro/mygest/secrets/google_credentials.json
```

#### C. Ottieni Calendar ID

1. Vai su https://calendar.google.com/
2. Settings > Seleziona il tuo calendario
3. Copia il "Calendar ID" (es: `xxx@group.calendar.google.com`)

#### D. Condividi il Calendario

**IMPORTANTE**: Condividi il calendario con l'email del service account (trovata nel file JSON)
- Vai su Google Calendar > Settings
- Share with specific people
- Aggiungi l'email del service account
- Permessi: "Make changes to events"

#### E. Configura in Django

Modifica `/home/sandro/mygest/mygest/settings_local.py`:
```python
GOOGLE_CALENDAR_CREDENTIALS_FILE = '/home/sandro/mygest/secrets/google_credentials.json'
GOOGLE_CALENDAR_DEFAULT_ID = 'your-calendar-id@group.calendar.google.com'
```

### 3. Testa la Configurazione

```bash
# Verifica configurazione
python check_google_calendar_config.py

# Test sincronizzazione (dry-run)
python manage.py sync_google_calendar --dry-run

# Sincronizza le occorrenze
python manage.py sync_google_calendar --all
```

## Alternative

### Opzione 1: Disabilita Sincronizzazione Google Calendar

Se non vuoi usare Google Calendar, puoi disabilitare i signal:

Modifica `/home/sandro/mygest/scadenze/models.py` alla fine del file:
```python
# Commenta queste righe per disabilitare la sincronizzazione automatica
# post_save.connect(_sync_calendar_after_save, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_sync_google")
# post_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_delete_google")
```

### Opzione 2: Usa un Calendario Diverso per Ogni Scadenza

Puoi impostare un `google_calendar_calendar_id` specifico per ogni scadenza invece di usare quello di default.

## Documentazione Completa

Per maggiori dettagli, consulta:
- **Setup completo**: [docs/GOOGLE_CALENDAR_SETUP.md](docs/GOOGLE_CALENDAR_SETUP.md)
- **Uso del comando sync**: [docs/GOOGLE_CALENDAR_SYNC.md](docs/GOOGLE_CALENDAR_SYNC.md)

## Supporto

Se riscontri problemi:
1. Esegui `python check_google_calendar_config.py` per diagnostica
2. Controlla i log in `ScadenzaNotificaLog` per errori specifici
3. Verifica che il service account abbia accesso al calendario
