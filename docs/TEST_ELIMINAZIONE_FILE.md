# 🧪 Test Eliminazione File Originale

Procedura per testare l'eliminazione automatica del file originale.

---

## 📋 Prerequisiti

1. ✅ Agent desktop in esecuzione
2. ✅ Server Django in esecuzione  
3. ✅ Frontend React in esecuzione

---

## 🚀 Procedura Test

### 1. Prepara File di Test

```bash
# Crea un file di test nella directory Downloads
echo "Questo è un file di test per MyGest" > ~/Downloads/test_eliminazione.txt
```

### 2. Avvia Agent Desktop

In un terminale separato:

```bash
cd /home/sandro/mygest/scripts
python3 mygest_agent.py \
  --server http://localhost:8000 \
  --token aa35a2945ce816d87c5c714732312274f0b6c116
```

Dovresti vedere:
```
Agent inizializzato: server=http://localhost:8000, poll_interval=30s
Agent avviato
Connessione al server verificata ✓
```

### 3. Accedi all'Applicazione Web

Apri: http://localhost:5173/documenti/new

### 4. Compila il Form Documento

1. **Tipo Documento**: Seleziona un tipo qualsiasi
2. **Cliente**: Seleziona un cliente
3. **Descrizione**: "Test eliminazione automatica"
4. **Data Documento**: Oggi
5. **File**: Clicca "Scegli file" e seleziona `~/Downloads/test_eliminazione.txt`

### 5. Configura Eliminazione Automatica

Dopo aver caricato il file, dovresti vedere una nuova sezione:

**"Eliminazione automatica file originale"**

1. **Percorso file originale**: 
   - Incolla il percorso completo: `/home/sandro/Downloads/test_eliminazione.txt`
   
2. **Checkbox**: 
   - Spunta ✅ "Elimina automaticamente il file originale"

Dovresti vedere un avviso giallo:
> ⚠️ **Attenzione:** Il file verrà eliminato definitivamente dal tuo computer.

### 6. Salva il Documento

Clicca **"Crea Documento"**

Dovresti vedere:
- ✅ "Documento creato con successo!"
- Redirect alla lista documenti

### 7. Verifica Eliminazione (entro 30 secondi)

#### Nel terminale dell'agent:

Dovresti vedere log simili a:
```
INFO - Trovate 1 richieste di eliminazione
INFO - Elaborazione richiesta 1: documento=DOC-..., path=/home/sandro/Downloads/test_eliminazione.txt
INFO - File eliminato: /home/sandro/Downloads/test_eliminazione.txt (42 bytes)
```

#### Nel filesystem:

```bash
ls -la ~/Downloads/test_eliminazione.txt
```

Dovrebbe dare: **No such file or directory** ✅

### 8. Verifica nell'Admin Django

Apri: http://localhost:8000/admin/documenti/filedeletionrequest/

Dovresti vedere:
- **Richiesta ID**: 1
- **Documento**: Codice del documento creato
- **Percorso**: `/home/sandro/Downloads/test_eliminazione.txt`
- **Status**: ✅ **COMPLETED**
- **Processed at**: Timestamp

---

## 🎯 Risultati Attesi

| Passo | Risultato Atteso |
|-------|------------------|
| 1. Caricamento form | ✅ Sezione "Eliminazione automatica" visibile dopo caricamento file |
| 2. Inserimento percorso | ✅ Checkbox abilitata |
| 3. Spunta checkbox | ✅ Avviso giallo mostrato |
| 4. Salvataggio documento | ✅ Documento creato, FileDeletionRequest creato con status PENDING |
| 5. Agent polling (30s) | ✅ Agent riceve richiesta |
| 6. Eliminazione file | ✅ File eliminato dal filesystem |
| 7. Conferma al server | ✅ Status → COMPLETED |

---

## 🐛 Test Casi Errore

### Test 1: Percorso Inesistente

1. Inserisci percorso: `/tmp/file_che_non_esiste.txt`
2. Spunta checkbox
3. Salva documento

**Risultato atteso**:
- Agent tenta eliminazione
- Fallisce con log: `File non trovato: /tmp/file_che_non_esiste.txt`
- Status → **FAILED** con error_message
- Admin mostra il messaggio di errore

### Test 2: Percorso Senza Permessi

1. Crea file root: `sudo touch /root/test.txt`
2. Inserisci percorso: `/root/test.txt`
3. Salva documento

**Risultato atteso**:
- Agent tenta eliminazione
- Fallisce con: `Permesso negato per eliminare: /root/test.txt`
- Status → **FAILED**

### Test 3: Senza Agent Attivo

1. Ferma l'agent (Ctrl+C)
2. Crea documento con eliminazione richiesta
3. Salva

**Risultato atteso**:
- Documento creato correttamente
- FileDeletionRequest creato con status **PENDING**
- File rimane nel filesystem
- Quando riavvii l'agent, riceve la richiesta e elimina il file

---

## 📊 Monitoraggio

### Log Agent in Tempo Reale

```bash
tail -f ~/.mygest-agent.log
```

### Statistiche Agent

L'agent mostra statistiche quando lo fermi (Ctrl+C):

```
============================================================
Statistiche Agent
============================================================
Uptime: 0:05:23
File eliminati: 3
Errori: 0
Ultimo poll: 2025-11-20 18:15:42
============================================================
```

### API Status

```bash
curl -H "Authorization: Token aa35a2945ce816d87c5c714732312274f0b6c116" \
  http://localhost:8000/api/v1/agent/status/
```

Risposta:
```json
{
  "stats": {
    "pending": 0,
    "completed": 3,
    "failed": 1,
    "total": 4
  },
  "recent": [...]
}
```

---

## ✅ Checklist Test Completo

- [ ] File di test creato
- [ ] Agent avviato e connesso
- [ ] Form documento carica correttamente
- [ ] Sezione "Eliminazione automatica" appare dopo caricamento file
- [ ] Percorso inserito correttamente
- [ ] Checkbox funziona
- [ ] Avviso giallo mostrato
- [ ] Documento salvato con successo
- [ ] FileDeletionRequest creato in database
- [ ] Agent riceve richiesta entro 30 secondi
- [ ] File eliminato dal filesystem
- [ ] Status aggiornato a COMPLETED
- [ ] Admin mostra richiesta completata

---

## 🎉 Test Superato!

Se tutti i punti sono ✅, l'integrazione è **completa e funzionante**!

---

## 🔍 Debug

Se qualcosa non funziona:

1. **Agent non riceve richieste**:
   - Verifica: `curl http://localhost:8000/api/v1/agent/pending-deletions/ -H "Authorization: Token YOUR_TOKEN"`
   
2. **File non eliminato**:
   - Controlla permessi: `ls -la /path/to/file`
   - Verifica log agent: `tail -50 ~/.mygest-agent.log`

3. **Errore salvataggio documento**:
   - Apri console browser (F12)
   - Guarda Network tab per vedere la richiesta POST
   - Controlla console Django per errori

4. **Componente non appare**:
   - Verifica che hai caricato un file
   - Verifica che sei in modalità creazione (non edit)
   - Controlla console browser per errori React
