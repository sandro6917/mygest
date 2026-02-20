# Automazione Eliminazione File di Origine

Soluzioni per automatizzare l'eliminazione del file originale dopo l'archiviazione.

## 🎯 Obiettivo

Al momento del salvataggio di un documento nell'applicazione:
1. ✅ Creare oggetto Documento nel database
2. ✅ Copiare il file nell'archivio organizzato (NAS)
3. ✅ Eliminare automaticamente il file di origine (se richiesto dall'utente)

---

## 🚧 Limitazione Tecnica

**Il browser non può eliminare file dal filesystem locale per motivi di sicurezza.**

Questo è un vincolo fondamentale del web. Esistono però diverse soluzioni alternative.

---

## 🔧 Soluzione 1: Agent Desktop (⭐ Consigliato)

Un piccolo programma che gira sul PC dell'utente e monitora le richieste di eliminazione.

### Architettura

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │  HTTP   │    MyGest    │  HTTP   │ Agent Local │
│  (Frontend) │────────▶│   (Server)   │◀────────│   (Python)  │
└─────────────┘         └──────────────┘         └─────────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │  Filesystem │
                                                   │    Locale   │
                                                   └─────────────┘
```

### Come Funziona

1. **Upload**: L'utente carica un documento dal browser
2. **Archiviazione**: Il file viene salvato nel NAS organizzato
3. **Richiesta**: L'utente inserisce il percorso originale e spunta "Elimina file originale"
4. **Coda**: Viene creato un `FileDeletionRequest` nel database con stato PENDING
5. **Polling**: L'agent locale (sul PC) interroga periodicamente il server
6. **Eliminazione**: L'agent riceve la richiesta e elimina il file locale
7. **Conferma**: L'agent conferma al server (stato → COMPLETED)

### Componenti

#### 1. Backend Django

**Model**: `documenti/models_deletion.py`
```python
class FileDeletionRequest(models.Model):
    documento = ForeignKey(Documento)
    source_path = CharField()  # Percorso file originale
    status = CharField(choices=['pending', 'completed', 'failed'])
    requested_by = ForeignKey(User)
    created_at = DateTimeField()
    processed_at = DateTimeField()
    error_message = TextField()
```

**API Endpoints**: `/api/v1/agent/`
- `GET /pending-deletions/` - Lista richieste pendenti
- `POST /confirm-deletion/` - Conferma eliminazione
- `GET /ping/` - Test connessione
- `GET /status/` - Statistiche

#### 2. Agent Desktop

**Script**: `scripts/mygest_agent.py`

```bash
# Installazione
pip install requests

# Avvio
python mygest_agent.py --server http://localhost:8000 --token YOUR_TOKEN

# Test connessione
python mygest_agent.py --server http://localhost:8000 --token YOUR_TOKEN --test
```

**Configurazione**:
- `--server`: URL del server MyGest
- `--token`: Token API per autenticazione
- `--poll-interval`: Intervallo polling in secondi (default: 30)

#### 3. Frontend React

**Component**: `FileSourceInfo.tsx`

Interfaccia utente che permette di:
- Inserire il percorso del file originale
- Spuntare checkbox "Elimina file originale"
- Visualizzare avvisi di sicurezza

---

## 📋 Setup Completo

### Passo 1: Backend (Django)

```bash
cd /home/sandro/mygest

# Crea le migrazioni per il nuovo model
python manage.py makemigrations

# Applica le migrazioni
python manage.py migrate

# Riavvia il server
python manage.py runserver
```

### Passo 2: Token API

Crea un token di autenticazione per l'agent:

```bash
# Metodo 1: Admin Django
# Vai su http://localhost:8000/admin/authtoken/token/
# Crea nuovo token per il tuo utente

# Metodo 2: Shell Django
python manage.py shell
>>> from rest_framework.authtoken.models import Token
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> user = User.objects.get(username='sandro')
>>> token, created = Token.objects.get_or_create(user=user)
>>> print(token.key)
```

### Passo 3: Agent Desktop (Ogni PC)

```bash
# Installa dipendenze
pip install requests

# Testa connessione
cd /home/sandro/mygest/scripts
python mygest_agent.py \
  --server http://192.168.1.100:8000 \
  --token YOUR_TOKEN_HERE \
  --test

# Avvia agent (manuale)
python mygest_agent.py \
  --server http://192.168.1.100:8000 \
  --token YOUR_TOKEN_HERE \
  --poll-interval 30
```

### Passo 4: Servizio Systemd (Opzionale)

Per avviare l'agent automaticamente all'avvio del PC:

```bash
# Crea file service
sudo nano /etc/systemd/system/mygest-agent.service
```

Contenuto:
```ini
[Unit]
Description=MyGest Desktop Agent
After=network.target

[Service]
Type=simple
User=sandro
WorkingDirectory=/home/sandro/mygest/scripts
Environment="MYGEST_SERVER=http://192.168.1.100:8000"
Environment="MYGEST_TOKEN=YOUR_TOKEN_HERE"
ExecStart=/usr/bin/python3 /home/sandro/mygest/scripts/mygest_agent.py --server $MYGEST_SERVER --token $MYGEST_TOKEN
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Abilita e avvia
sudo systemctl daemon-reload
sudo systemctl enable mygest-agent
sudo systemctl start mygest-agent

# Controlla stato
sudo systemctl status mygest-agent

# Log
sudo journalctl -u mygest-agent -f
```

---

## 💻 Uso dall'Applicazione

### 1. Modifica DocumentoFormPage

Integra il componente `FileSourceInfo`:

```typescript
import FileSourceInfo from '../components/FileSourceInfo';

function DocumentoFormPage() {
  const [sourceFilePath, setSourceFilePath] = useState('');
  const [deleteSourceFile, setDeleteSourceFile] = useState(false);
  
  const handleSourcePathChange = (path: string, shouldDelete: boolean) => {
    setSourceFilePath(path);
    setDeleteSourceFile(shouldDelete);
  };
  
  const handleSubmit = async (data: DocumentoFormData) => {
    const formData = new FormData();
    // ... altri campi ...
    
    if (deleteSourceFile && sourceFilePath) {
      formData.append('delete_source_file', 'true');
      formData.append('source_file_path', sourceFilePath);
    }
    
    await api.post('/api/v1/documenti/', formData);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* ... altri campi ... */}
      
      <FileSourceInfo onSourcePathChange={handleSourcePathChange} />
      
      <button type="submit">Salva Documento</button>
    </form>
  );
}
```

### 2. Workflow Utente

1. L'utente apre la form di creazione documento
2. Seleziona il file da caricare (es: `C:\Users\Sandro\Downloads\fattura.pdf`)
3. **Copia manualmente** il percorso del file (dal file explorer)
4. **Incolla** il percorso nel campo "Percorso file originale"
5. Spunta "Elimina automaticamente il file originale"
6. Compila gli altri campi del documento
7. Clicca "Salva"

**Cosa succede:**
- Il browser **copia** il file nel NAS
- Il documento viene salvato nel database
- Viene creato un `FileDeletionRequest` con stato PENDING
- L'agent desktop (se in esecuzione) lo rileva entro 30 secondi
- L'agent elimina il file da `C:\Users\Sandro\Downloads\fattura.pdf`
- L'agent conferma al server (stato → COMPLETED)

---

## 🔒 Sicurezza

### Autorizzazione

L'agent richiede un token API valido:
- Il token è legato a un utente specifico
- Solo utenti autenticati possono creare richieste di eliminazione
- Solo richieste PENDING vengono elaborate

### Validazione Path

L'agent **NON** valida i percorsi per sicurezza:
- L'utente è responsabile del percorso inserito
- Non ci sono restrizioni sulle directory
- L'agent può eliminare qualsiasi file accessibile

⚠️ **Raccomandazioni**:
1. Esegui l'agent con un utente con permessi limitati
2. Configura l'agent per accettare solo percorsi in directory specifiche (es: Downloads)
3. Implementa una whitelist di directory permesse

### Backup

Prima di eliminare definitivamente:
1. Verifica che il file sia stato archiviato correttamente
2. Controlla che il documento sia presente nel NAS
3. Considera di spostare in una cartella temporanea invece di eliminare

---

## 📊 Monitoraggio

### Dashboard Admin

Accedi a `/admin/documenti/filedeletionrequest/` per vedere:
- Richieste pendenti
- Richieste completate
- Richieste fallite
- Tempi di elaborazione

### API Status

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/agent/status/
```

Risposta:
```json
{
  "stats": {
    "pending": 3,
    "completed": 127,
    "failed": 2,
    "total": 132
  },
  "recent": [...]
}
```

### Log Agent

```bash
# Log locale
tail -f ~/.mygest-agent.log

# Se systemd
sudo journalctl -u mygest-agent -f
```

---

## 🔧 Troubleshooting

### Agent non si connette

```bash
# Verifica connessione
ping 192.168.1.100

# Verifica porta
curl http://192.168.1.100:8000/api/v1/agent/ping/

# Verifica token
python mygest_agent.py --server http://192.168.1.100:8000 --token YOUR_TOKEN --test
```

### File non viene eliminato

```bash
# Controlla permessi
ls -la /path/to/file.pdf

# Controlla log agent
tail -f ~/.mygest-agent.log

# Verifica richiesta pendente
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/agent/pending-deletions/
```

### Percorso non valido

L'agent logga gli errori ma non blocca:
- `File non trovato`: Il percorso non esiste
- `Permesso negato`: L'agent non ha permessi
- Status → FAILED con messaggio di errore

---

## 🚀 Vantaggi

✅ **Sicurezza**: Il browser non accede mai al filesystem locale  
✅ **Flessibilità**: L'utente controlla cosa eliminare  
✅ **Tracciabilità**: Tutte le eliminazioni sono registrate  
✅ **Affidabilità**: Gestione degli errori e retry automatico  
✅ **Multi-dispositivo**: Ogni PC ha il suo agent indipendente  

---

## 🔄 Soluzioni Alternative

### Soluzione 2: Cartella Sincronizzata

Usa servizi di sincronizzazione (Dropbox, OneDrive, Nextcloud):

1. L'utente salva i file in una cartella sincronizzata
2. MyGest monitora quella cartella (via inotify/watchdog)
3. Quando un file viene archiviato, viene spostato in `.archived/`
4. Il servizio di sync propaga la modifica

**Pro**: Automatico, multi-dispositivo  
**Contro**: Richiede servizio sync, conflitti possibili

### Soluzione 3: Estensione Browser

Crea un'estensione Chrome/Firefox che:

1. Intercetta il file upload
2. Salva il percorso locale (con permessi estensione)
3. Dopo upload riuscito, elimina il file

**Pro**: Più integrato  
**Contro**: Richiede installazione estensione, permessi elevati

### Soluzione 4: Applicazione Desktop

Applicazione nativa (Electron, PyQt) che:

1. Ha accesso completo al filesystem
2. Gestisce upload e eliminazione in un'unica operazione

**Pro**: Controllo completo  
**Contro**: Abbandona l'interfaccia web

---

## 📝 Conclusioni

La **Soluzione 1 (Agent Desktop)** è il miglior compromesso tra:
- Sicurezza del browser
- Flessibilità dell'utente
- Semplicità di implementazione
- Compatibilità multi-dispositivo

Il sistema è completamente implementato e pronto all'uso!

---

## 📚 File Creati

```
Backend:
- documenti/models_deletion.py      # Model FileDeletionRequest
- api/v1/agent/serializers.py       # Serializers API
- api/v1/agent/views.py              # ViewSet agent
- api/v1/agent/urls.py               # URL patterns
- api/v1/urls.py                     # Include agent URLs

Frontend:
- frontend/src/components/FileSourceInfo.tsx  # Component UI

Agent:
- scripts/mygest_agent.py            # Agent desktop Python
- scripts/mygest-agent.service       # Systemd service (da creare)

Docs:
- docs/AUTOMAZIONE_ELIMINAZIONE_ORIGINE.md    # Questa guida
```
