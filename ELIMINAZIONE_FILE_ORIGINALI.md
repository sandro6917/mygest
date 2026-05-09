# Eliminazione File Originali - Workflow Completo

## 📋 Panoramica

Il sistema MyGest implementa un meccanismo **sicuro e tracciabile** per l'eliminazione automatica dei file originali dopo l'upload. Questo permette di:

- ✅ Liberare spazio su disco dell'utente dopo l'archiviazione
- ✅ Mantenere tracciabilità completa delle eliminazioni
- ✅ Proteggere percorsi critici del sistema
- ✅ Gestire errori e conferme

---

## 🔄 Flusso Completo

### 1️⃣ **Upload Documento (Frontend)**

**Componente**: `FileSourceInfo.tsx` + `DocumentoFormPage.tsx`

L'utente:
1. Carica un file (upload o scansione)
2. **Opzionalmente** inserisce il **percorso originale** del file sul suo PC
3. Spunta la checkbox **"Elimina automaticamente il file originale"**

```tsx
// FileSourceInfo.tsx - Conversione path automatica
const convertWindowsPathToWSL = (windowsPath: string): string => {
  // C:\Users\... → /mnt/c/Users/...
  // G:\... → /mnt/g/...
  const driveMatch = cleanPath.match(/^([A-Za-z]):[/\\](.*)/);
  if (driveMatch) {
    const [, drive, restPath] = driveMatch;
    const unixPath = restPath.replace(/\\/g, '/');
    return `/mnt/${drive.toLowerCase()}/${unixPath}`;
  }
  return cleanPath;
};
```

**Esempio Input Utente**:
```
Percorso: C:\Users\Sandro\Downloads\contratto.pdf
Checkbox: ☑ Elimina automaticamente
```

**Path Convertito Automaticamente**:
```
/mnt/c/Users/Sandro/Downloads/contratto.pdf
```

### 2️⃣ **Submit Form (Frontend → Backend)**

```typescript
// DocumentoFormPage.tsx
if (deleteSourceFile && sourceFilePath.trim()) {
  formPayload.append('delete_source_file', 'true');
  formPayload.append('source_file_path', sourceFilePath.trim());
}
```

**Payload inviato**:
```json
{
  "file": <File Object>,
  "descrizione": "Contratto...",
  "delete_source_file": "true",
  "source_file_path": "/mnt/c/Users/Sandro/Downloads/contratto.pdf",
  ...
}
```

### 3️⃣ **Creazione Documento (Backend)**

**File**: `api/v1/documenti/serializers.py`

```python
def create(self, validated_data):
    delete_source = validated_data.pop('delete_source_file', False)
    source_path = validated_data.pop('source_file_path', '')
    
    # 1. Crea documento
    documento = Documento(**validated_data)
    documento.save()
    
    # 2. Salva attributi
    if attributi_data:
        attrs_map = self._save_attributi(documento, attributi_data)
    
    # 3. Rinomina e sposta file in archivio
    documento._rename_file_if_needed(...)
    documento._move_file_into_archivio(attrs=attrs_map)
    
    # 4. ✅ Crea richiesta eliminazione
    if delete_source and source_path:
        self._create_deletion_request(documento, source_path)
    
    return documento
```

### 4️⃣ **Creazione Richiesta Eliminazione**

**File**: `api/v1/documenti/serializers.py`

```python
def _create_deletion_request(self, documento, source_path):
    from documenti.models_deletion import FileDeletionRequest
    
    deletion_request = FileDeletionRequest.objects.create(
        documento=documento,
        source_path=source_path,
        requested_by=request.user,
        status='pending',
        file_size=documento.file.size if documento.file else None
    )
    
    logger.info(
        f"Richiesta eliminazione creata: id={deletion_request.id}, "
        f"documento={documento.codice}, path={source_path}"
    )
```

**Record Database Creato**:
```python
FileDeletionRequest(
    id=123,
    documento=<Documento #456>,
    source_path='/mnt/c/Users/Sandro/Downloads/contratto.pdf',
    requested_by=<User: sandro>,
    status='pending',  # ⏳ In attesa
    created_at='2026-02-24 10:00:00',
    processed_at=None,
    error_message='',
    file_size=2048576  # 2 MB
)
```

### 5️⃣ **Agent Desktop - Polling**

**File**: `scripts/mygest_agent.py`

L'agent gira sul PC dell'utente e:

1. **Polling ogni 30 secondi** (configurabile)
2. Chiama API: `GET /api/v1/agent/pending-deletions/`
3. Riceve lista richieste con `status='pending'`

```python
def get_pending_deletions(self) -> List[Dict]:
    response = requests.get(
        f'{self.server_url}/api/v1/agent/pending-deletions/',
        headers={'Authorization': f'Token {self.api_token}'},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        return data.get('deletions', [])
    return []
```

**Risposta API**:
```json
{
  "count": 1,
  "deletions": [
    {
      "id": 123,
      "documento_id": 456,
      "documento_codice": "CLI-TIT-2026-001",
      "source_path": "/mnt/c/Users/Sandro/Downloads/contratto.pdf",
      "requested_by": "sandro",
      "created_at": "2026-02-24T10:00:00Z",
      "file_size": 2048576
    }
  ]
}
```

### 6️⃣ **Agent - Verifica Protezioni**

Prima di eliminare, l'agent verifica che il path **NON sia protetto**:

```python
# Percorsi protetti (NON verranno MAI eliminati)
self.protected_paths = [
    '/mnt/archivio',           # ❌ Archivio documenti MyGest
    '/home/sandro/mygest',     # ❌ Progetto MyGest
    '/var/www',                # ❌ Web server
    '/opt',                    # ❌ Software installato
    '/usr',                    # ❌ Sistema
    '/etc',                    # ❌ Configurazioni
    '/bin',                    # ❌ Eseguibili sistema
    '/sbin',                   # ❌ Eseguibili amministrazione
]

def is_protected_path(self, file_path: str) -> bool:
    path = Path(file_path).resolve()
    path_str = str(path)
    
    for protected in self.protected_paths:
        if path_str.startswith(protected):
            return True  # 🛡️ PROTETTO - NON eliminare
    return False
```

**Esempio Validazione**:
```python
is_protected('/mnt/c/Users/Sandro/Downloads/contratto.pdf')  # ✅ OK
is_protected('/mnt/archivio/CLI/TIT/2026/contratto.pdf')     # ❌ BLOCCATO
is_protected('/usr/bin/python')                              # ❌ BLOCCATO
```

### 7️⃣ **Agent - Eliminazione File**

Se il path è **sicuro**, l'agent elimina il file:

```python
def delete_file(self, file_path: str) -> bool:
    # Verifica protezione
    if self.is_protected_path(file_path):
        logger.error(f"🛡️  BLOCCATO: Path protetto: {file_path}")
        self.stats['protected_blocks'] += 1
        return False
    
    # Risolvi path e verifica esistenza
    path = Path(file_path).resolve()
    
    if not path.exists():
        logger.warning(f"File non trovato: {file_path}")
        return False
    
    if not path.is_file():
        logger.error(f"Non è un file: {file_path}")
        return False
    
    # Ottieni dimensione
    file_size = path.stat().st_size
    
    # ✅ ELIMINA IL FILE
    path.unlink()
    
    logger.info(f"✅ File eliminato: {file_path} ({file_size} bytes)")
    self.stats['deleted'] += 1
    
    return True
```

### 8️⃣ **Agent - Conferma al Server**

Dopo l'eliminazione (successo o fallimento), l'agent conferma al server:

```python
def confirm_deletion(self, deletion_id: int, success: bool, error_message: str = None):
    payload = {
        'deletion_id': deletion_id,
        'success': success
    }
    
    if error_message:
        payload['error_message'] = error_message
    
    response = requests.post(
        f'{self.server_url}/api/v1/agent/confirm-deletion/',
        headers=self._get_headers(),
        json=payload,
        timeout=30
    )
```

**Payload Conferma (Successo)**:
```json
{
  "deletion_id": 123,
  "success": true
}
```

**Payload Conferma (Fallimento)**:
```json
{
  "deletion_id": 123,
  "success": false,
  "error_message": "PermissionError: Access denied"
}
```

### 9️⃣ **Backend - Aggiornamento Stato**

**File**: `api/v1/agent/views.py`

```python
@action(detail=False, methods=['post'], url_path='confirm-deletion')
def confirm_deletion(self, request):
    deletion_id = request.data['deletion_id']
    success = request.data['success']
    error_message = request.data.get('error_message', '')
    
    deletion = FileDeletionRequest.objects.get(id=deletion_id)
    
    if success:
        deletion.mark_completed()  # ✅ status='completed'
        message = f"File eliminato con successo: {deletion.source_path}"
    else:
        deletion.mark_failed(error_message)  # ❌ status='failed'
        message = f"Eliminazione fallita: {error_message}"
    
    return Response({
        'status': 'ok',
        'message': message,
        'deletion_id': deletion_id,
        'new_status': deletion.status
    })
```

**Record Database Aggiornato**:
```python
FileDeletionRequest(
    id=123,
    documento=<Documento #456>,
    source_path='/mnt/c/Users/Sandro/Downloads/contratto.pdf',
    requested_by=<User: sandro>,
    status='completed',  # ✅ Completato
    created_at='2026-02-24 10:00:00',
    processed_at='2026-02-24 10:00:35',  # ✅ Processato
    error_message='',
    file_size=2048576
)
```

---

## 📊 Diagramma Flusso Completo

```
┌──────────────────────────────────────────────────────────────────────┐
│                     ELIMINAZIONE FILE ORIGINALE                       │
└──────────────────────────────────────────────────────────────────────┘

PC Utente                  Browser                Backend              Agent Desktop
    │                         │                       │                       │
    │  File: contratto.pdf    │                       │                       │
    │  (C:\Users\...\...)     │                       │                       │
    │                         │                       │                       │
    │  1. Upload documento    │                       │                       │
    ├────────────────────────>│                       │                       │
    │                         │                       │                       │
    │  2. Inserisce path      │                       │                       │
    │     C:\Users\...\...    │                       │                       │
    │  3. ☑ Elimina originale │                       │                       │
    │                         │                       │                       │
    │                         │  4. POST /documenti/  │                       │
    │                         │     + file            │                       │
    │                         │     + delete=true     │                       │
    │                         │     + path=...        │                       │
    │                         ├──────────────────────>│                       │
    │                         │                       │                       │
    │                         │                       │  5. Crea Documento    │
    │                         │                       │     - file in archivio│
    │                         │                       │                       │
    │                         │                       │  6. FileDeletionReq   │
    │                         │                       │     status='pending'  │
    │                         │                       │     ⏳                │
    │                         │                       │                       │
    │                         │  7. Response OK       │                       │
    │                         │<──────────────────────┤                       │
    │                         │                       │                       │
    │                         │                       │  8. Polling (30s)     │
    │                         │                       │  GET /pending-deletions│
    │                         │                       │<──────────────────────┤
    │                         │                       │                       │
    │                         │                       │  9. Lista richieste   │
    │                         │                       ├──────────────────────>│
    │                         │                       │                       │
    │                         │                       │  10. Verifica protezione│
    │                         │                       │      🛡️ Se OK         │
    │                         │                       │                       │
    │  11. File ELIMINATO     │                       │  12. path.unlink()    │
    │  ❌ contratto.pdf       │                       │      ✅ Successo      │
    │<────────────────────────┼───────────────────────┼───────────────────────┤
    │                         │                       │                       │
    │                         │                       │  13. POST /confirm     │
    │                         │                       │      success=true     │
    │                         │                       │<──────────────────────┤
    │                         │                       │                       │
    │                         │                       │  14. mark_completed() │
    │                         │                       │      status='completed'│
    │                         │                       │      ✅               │
    │                         │                       │                       │

RISULTATO FINALE:
- PC Utente: File originale ELIMINATO ❌
- Archivio NAS: Documento SALVATO ✅ (/mnt/archivio/CLI/TIT/2026/...)
- Database: Traccia completa ✅ (FileDeletionRequest completed)
```

---

## 🔐 Sicurezza e Protezioni

### 1. **Percorsi Protetti**

L'agent **blocca** automaticamente eliminazioni di:

| Percorso | Descrizione | Motivo |
|----------|-------------|--------|
| `/mnt/archivio` | Archivio documenti MyGest | ⚠️ Archivio centrale |
| `/home/sandro/mygest` | Progetto MyGest | ⚠️ Codice sorgente |
| `/var/www` | Web server | ⚠️ Siti pubblici |
| `/usr`, `/bin`, `/sbin` | Sistema operativo | ⚠️ Sistema critico |
| `/etc` | Configurazioni sistema | ⚠️ Config critiche |

**Log Agent (path protetto)**:
```
2026-02-24 10:00:35 - MyGestAgent - ERROR - 🛡️  BLOCCATO: Path protetto: /mnt/archivio/file.pdf
```

**Statistiche Agent**:
```python
self.stats = {
    'deleted': 15,             # ✅ File eliminati con successo
    'errors': 2,               # ❌ Errori (permessi, file non trovati)
    'protected_blocks': 3,     # 🛡️ Bloccati per protezione
}
```

### 2. **Conversione Path Automatica**

Il frontend converte automaticamente path Windows → WSL:

| Input Utente | Output Convertito | Tipo |
|--------------|-------------------|------|
| `C:\Users\Sandro\file.pdf` | `/mnt/c/Users/Sandro/file.pdf` | ✅ Drive locale |
| `G:\Il mio Drive\doc.pdf` | `/mnt/g/Il mio Drive/doc.pdf` | ✅ Google Drive |
| `D:\Backup\archivio.zip` | `/mnt/d/Backup/archivio.zip` | ✅ Drive secondario |
| `\\server\share\file.pdf` | `\\server\share\file.pdf` | ⚠️ UNC (invariato) |

### 3. **Tracciabilità Completa**

Ogni eliminazione è **tracciata** nel database:

```python
# Query tutte le eliminazioni di un documento
documento.deletion_requests.all()

# Query eliminazioni completate oggi
FileDeletionRequest.objects.filter(
    status='completed',
    processed_at__date=timezone.now().date()
)

# Query eliminazioni fallite ultimo mese
FileDeletionRequest.objects.filter(
    status='failed',
    created_at__gte=timezone.now() - timedelta(days=30)
).select_related('documento', 'requested_by')
```

---

## 📈 Stati Richiesta Eliminazione

| Stato | Descrizione | Visualizzazione | Azione Successiva |
|-------|-------------|-----------------|-------------------|
| **`pending`** | In attesa di elaborazione agent | ⏳ Pending | Agent lo elaborerà al prossimo poll |
| **`completed`** | File eliminato con successo | ✅ Completed | Nessuna, processo completato |
| **`failed`** | Eliminazione fallita | ❌ Failed | Verifica error_message, riprova manualmente |
| **`cancelled`** | Richiesta annullata manualmente | 🚫 Cancelled | Nessuna |

**Transizioni di Stato**:
```
┌─────────┐
│ pending │  ← Stato iniziale (creazione richiesta)
└────┬────┘
     │
     ├─→ Agent elabora con successo ──→ ✅ completed
     │
     ├─→ Agent fallisce ──────────────→ ❌ failed
     │
     └─→ Utente annulla ──────────────→ 🚫 cancelled
```

---

## 🛠️ Installazione e Configurazione Agent

### Installazione Dipendenze

```bash
pip install requests
```

### Esecuzione Manuale

```bash
python scripts/mygest_agent.py \
  --server http://localhost:8000 \
  --token YOUR_API_TOKEN \
  --poll-interval 30
```

### Configurazione Token API

1. Admin Django → **Token** (django-rest-framework)
2. Crea token per utente:
   ```python
   from rest_framework.authtoken.models import Token
   token = Token.objects.create(user=user)
   print(token.key)  # Es: 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
   ```

### Servizio Systemd (Avvio Automatico)

**File**: `/etc/systemd/system/mygest-agent.service`

```ini
[Unit]
Description=MyGest Desktop Agent
After=network.target

[Service]
Type=simple
User=sandro
WorkingDirectory=/home/sandro/mygest
ExecStart=/usr/bin/python3 /home/sandro/mygest/scripts/mygest_agent.py \
  --server http://localhost:8000 \
  --token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b \
  --poll-interval 30
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Comandi**:
```bash
# Abilita servizio
sudo systemctl enable mygest-agent

# Avvia servizio
sudo systemctl start mygest-agent

# Stato servizio
sudo systemctl status mygest-agent

# Log servizio
journalctl -u mygest-agent -f
```

---

## 📝 Log e Monitoring

### Log Agent Desktop

**File**: `~/.mygest-agent.log`

```
2026-02-24 10:00:30 - MyGestAgent - INFO - Agent inizializzato: server=http://localhost:8000, poll_interval=30s
2026-02-24 10:00:30 - MyGestAgent - INFO - ⚠️  Percorsi protetti: /mnt/archivio, /home/sandro/mygest, ...
2026-02-24 10:00:30 - MyGestAgent - INFO - Connessione al server verificata ✓
2026-02-24 10:00:30 - MyGestAgent - INFO - Agent avviato
2026-02-24 10:01:00 - MyGestAgent - INFO - Trovate 1 richieste di eliminazione
2026-02-24 10:01:00 - MyGestAgent - INFO - Elaborazione richiesta 123: documento=456, path=/mnt/c/Users/Sandro/Downloads/contratto.pdf
2026-02-24 10:01:00 - MyGestAgent - INFO - ✅ File eliminato: /mnt/c/Users/Sandro/Downloads/contratto.pdf (2048576 bytes)
2026-02-24 10:01:01 - MyGestAgent - INFO - ✅ Conferma inviata per deletion_id=123
```

### Statistiche Agent

Ogni arresto (CTRL+C) mostra statistiche:

```
============================================================
Statistiche Agent
============================================================
Uptime: 2:45:30
File eliminati: 15
🛡️  Bloccati (protetti): 3
Errori: 2
Ultimo poll: 2026-02-24 12:45:30
============================================================
```

### API Monitoring (Backend)

**Endpoint**: `GET /api/v1/agent/stats/`

```json
{
  "pending": 2,
  "completed": 15,
  "failed": 3,
  "total": 20,
  "recent": [
    {
      "id": 123,
      "documento_codice": "CLI-TIT-2026-001",
      "source_path": "/mnt/c/.../contratto.pdf",
      "status": "completed",
      "created_at": "2026-02-24T10:00:00Z",
      "processed_at": "2026-02-24T10:00:35Z"
    }
  ]
}
```

---

## ⚠️ Casi Particolari

### 1. Agent Non Attivo

Se l'agent non è attivo, la richiesta **resta pending**:

- ⏳ Stato: `pending`
- ⏰ Elaborazione: Quando l'agent si riconnetterà
- 📄 File originale: **Resta sul PC fino all'elaborazione**

### 2. File Non Trovato

Se il file non esiste più (es: già eliminato manualmente):

```
2026-02-24 10:00:35 - MyGestAgent - WARNING - File non trovato: /mnt/c/.../file.pdf
```

- Stato: `failed`
- Error: `"File non trovato"`
- Azione: Nessuna (file già assente)

### 3. Permessi Negati

```
2026-02-24 10:00:35 - MyGestAgent - ERROR - Permesso negato per eliminare: /mnt/c/.../file.pdf
```

- Stato: `failed`
- Error: `"PermissionError: Access denied"`
- Azione: Verificare permessi file o eseguire agent come utente proprietario

### 4. Path UNC Windows

Path di rete Windows (`\\server\share\...`):

- ⚠️ **Non convertiti** automaticamente in WSL
- Richiedono mount manuale: `sudo mount -t drvfs '\\server\share' /mnt/share`
- Alternative: Mappare come drive Windows (Z:) prima dell'upload

---

## 🎯 Best Practices

### Per Utenti

1. ✅ **Verifica path**: Usa "Copia come percorso" in Windows Explorer
2. ✅ **Attendi conferma**: Assicurati che l'agent sia attivo prima di eliminare manualmente
3. ✅ **Backup importante**: Per file critici, mantieni backup prima di chiedere eliminazione
4. ✅ **Monitora log agent**: Verifica che non ci siano errori ricorrenti

### Per Amministratori

1. ✅ **Agent sempre attivo**: Configura come servizio systemd
2. ✅ **Monitora pending**: Alert se richieste pending > 24h
3. ✅ **Review failed**: Controlla periodicamente eliminazioni fallite
4. ✅ **Cleanup database**: Archivia richieste `completed` oltre 90 giorni

---

## 📊 Vantaggi del Sistema

| Vantaggio | Descrizione |
|-----------|-------------|
| **Sicurezza** | Percorsi protetti, validazioni multiple |
| **Tracciabilità** | Ogni eliminazione registrata con timestamp e utente |
| **Reversibilità** | Possibile annullare richieste `pending` |
| **Affidabilità** | Retry automatici, gestione errori |
| **Autonomia** | Agent lavora in background senza intervento |
| **Trasparenza** | Log dettagliati lato client e server |

---

**Data Documento**: 2026-02-24  
**Versione**: 1.0  
**Autore**: System Analysis
