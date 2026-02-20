# Configurazione Google Calendar per MyGest

## Problema Riscontrato

```
✗ Errore per [Nome Scadenza]: Nessun calendar ID configurato
```

Questo errore indica che:
1. Il file delle credenziali Google non è configurato correttamente
2. Oppure il Calendar ID non è impostato

## Soluzione: Configurazione Completa

### Passo 1: Crea un Progetto Google Cloud

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto o seleziona uno esistente
3. Vai su **APIs & Services** > **Library**
4. Cerca "Google Calendar API" e abilitala

### Passo 2: Crea un Service Account

1. Vai su **APIs & Services** > **Credentials**
2. Clicca su **Create Credentials** > **Service Account**
3. Dai un nome al service account (es: "mygest-calendar-sync")
4. Clicca su **Create and Continue**
5. Salta la sezione "Grant this service account access to project" (opzionale)
6. Clicca su **Done**

### Passo 3: Genera le Credenziali JSON

1. Nella lista dei Service Accounts, clicca sul service account appena creato
2. Vai alla tab **Keys**
3. Clicca su **Add Key** > **Create new key**
4. Seleziona **JSON** come tipo
5. Clicca su **Create** - il file verrà scaricato automaticamente

### Passo 4: Configura le Credenziali in MyGest

1. Crea la directory per i secrets (se non esiste):
   ```bash
   mkdir -p /home/sandro/mygest/secrets
   ```

2. Copia il file JSON scaricato:
   ```bash
   cp ~/Downloads/mygest-calendar-*.json /home/sandro/mygest/secrets/google_credentials.json
   ```

3. Imposta i permessi corretti:
   ```bash
   chmod 600 /home/sandro/mygest/secrets/google_credentials.json
   ```

### Passo 5: Ottieni l'ID del Calendario Google

1. Apri [Google Calendar](https://calendar.google.com/)
2. Vai su **Settings** (ingranaggio in alto a destra)
3. Nella barra laterale, seleziona il calendario che vuoi usare
4. Scorri fino a "Integrate calendar"
5. Copia il **Calendar ID** (formato: `xxxxxxxx@group.calendar.google.com`)

### Passo 6: Condividi il Calendario con il Service Account

**IMPORTANTE**: Il Service Account deve avere accesso al calendario!

1. In Google Calendar, vai su **Settings** > **Settings for my calendars**
2. Seleziona il calendario
3. Clicca su "Share with specific people"
4. Clicca su **Add people**
5. Incolla l'email del service account (si trova nel file JSON, campo `client_email`)
6. Imposta i permessi su **Make changes to events** o **Make changes and manage sharing**
7. Clicca su **Send**

### Passo 7: Configura le Variabili d'Ambiente

Ci sono due opzioni:

#### Opzione A: Variabili d'Ambiente (Raccomandato per produzione)

Aggiungi al tuo file `.env` o `.bashrc`:
```bash
export GOOGLE_CALENDAR_CREDENTIALS_FILE="/home/sandro/mygest/secrets/google_credentials.json"
export GOOGLE_CALENDAR_ID="your-calendar-id@group.calendar.google.com"
```

Poi ricarica:
```bash
source ~/.bashrc
```

#### Opzione B: Modifica Diretta in settings_local.py

Modifica `/home/sandro/mygest/mygest/settings_local.py`:
```python
GOOGLE_CALENDAR_CREDENTIALS_FILE = '/home/sandro/mygest/secrets/google_credentials.json'
GOOGLE_CALENDAR_DEFAULT_ID = 'your-calendar-id@group.calendar.google.com'
```

### Passo 8: Verifica la Configurazione

Esegui un test di sincronizzazione in dry-run:
```bash
python manage.py sync_google_calendar --dry-run
```

Se la configurazione è corretta, dovresti vedere:
```
Trovate X occorrenze da sincronizzare...
Modalità DRY RUN - nessuna sincronizzazione effettiva
  [✗ Non sincronizzata] Nome Scadenza - YYYY-MM-DD HH:MM
```

### Passo 9: Sincronizza le Occorrenze

Una volta verificato che tutto funziona:
```bash
# Sincronizza solo le occorrenze future non ancora sincronizzate
python manage.py sync_google_calendar

# Oppure sincronizza tutte le occorrenze
python manage.py sync_google_calendar --all
```

## Troubleshooting

### Errore: "Nessun calendar ID configurato"

**Causa**: `GOOGLE_CALENDAR_DEFAULT_ID` è vuoto

**Soluzione**: 
1. Verifica che la variabile d'ambiente `GOOGLE_CALENDAR_ID` sia impostata
2. Oppure modifica direttamente `settings_local.py` con l'ID del calendario

### Errore: "GOOGLE_CALENDAR_CREDENTIALS_FILE non configurato nelle settings"

**Causa**: Il file delle credenziali non esiste o il path è errato

**Soluzione**:
```bash
# Verifica che il file esista
ls -la /home/sandro/mygest/secrets/google_credentials.json

# Se non esiste, crea la directory e copia il file
mkdir -p /home/sandro/mygest/secrets
cp /path/to/your/credentials.json /home/sandro/mygest/secrets/google_credentials.json
```

### Errore: "403 Forbidden" o "Access Denied"

**Causa**: Il Service Account non ha accesso al calendario

**Soluzione**: Condividi il calendario con l'email del service account (vedi Passo 6)

### Errore: "Invalid credentials"

**Causa**: Il file JSON delle credenziali è corrotto o non valido

**Soluzione**:
1. Verifica che il file JSON sia valido:
   ```bash
   python -m json.tool /home/sandro/mygest/secrets/google_credentials.json
   ```
2. Se è corrotto, scarica nuovamente le credenziali da Google Cloud Console

### Verificare la Configurazione Attuale

Esegui questo script Python per vedere la configurazione:
```python
from django.conf import settings
print(f"Credentials file: {settings.GOOGLE_CALENDAR_CREDENTIALS_FILE}")
print(f"Calendar ID: {settings.GOOGLE_CALENDAR_DEFAULT_ID}")

# Verifica se il file esiste
import os
if os.path.exists(settings.GOOGLE_CALENDAR_CREDENTIALS_FILE):
    print("✓ File credenziali trovato")
else:
    print("✗ File credenziali NON trovato")
```

## Test di Sincronizzazione

Dopo la configurazione, puoi testare con:
```bash
# Test senza modifiche
python manage.py sync_google_calendar --dry-run

# Sincronizza una singola occorrenza per test
python manage.py sync_google_calendar --occorrenza-id 1

# Sincronizza tutte le occorrenze future
python manage.py sync_google_calendar --all
```

## Sincronizzazione Automatica

Una volta configurato, la sincronizzazione avviene automaticamente quando:
- Crei una nuova occorrenza
- Modifichi un'occorrenza esistente
- Cambi lo stato di un'occorrenza

Non è necessario eseguire manualmente il comando se non per:
- Ri-sincronizzare occorrenze esistenti
- Sincronizzare occorrenze create prima della configurazione
- Risolvere problemi di sincronizzazione

## Configurazione per Produzione

Per l'ambiente di produzione, assicurati di:

1. **Proteggere il file delle credenziali**:
   ```bash
   chmod 600 /srv/mygest/secrets/google_credentials.json
   chown www-data:www-data /srv/mygest/secrets/google_credentials.json
   ```

2. **Usare variabili d'ambiente**:
   Aggiungi al file systemd o supervisor:
   ```ini
   Environment="GOOGLE_CALENDAR_CREDENTIALS_FILE=/srv/mygest/secrets/google_credentials.json"
   Environment="GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com"
   ```

3. **Non committare le credenziali su Git**:
   Il file `secrets/` è già nel `.gitignore`

4. **Backup delle credenziali**:
   Mantieni una copia sicura del file JSON in un vault o password manager
