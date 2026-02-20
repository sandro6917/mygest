# MyGest Agent - Guida Windows
================================

## Installazione su Windows

### 1. Installa Python (se non presente)
- Scarica da: https://www.python.org/downloads/
- Durante installazione, **seleziona "Add Python to PATH"**

### 2. Installa dipendenze
```cmd
pip install requests
```

### 3. Copia i file necessari
Metti in una cartella (es. `C:\MyGest\Agent\`):
- `mygest_agent_windows.py`
- `config_agent_windows.ini.example`

### 4. Configura l'agent
Rinomina `config_agent_windows.ini.example` in `config_agent.ini` e modifica:

```ini
[server]
url = http://192.168.1.100:8000  # IP del server MyGest
token = aa35a2945ce816d87c5c714732312274f0b6c116  # Tuo token

[agent]
poll_interval = 30  # Polling ogni 30 secondi
```

Per ottenere il token, sul server esegui:
```bash
python manage_agent_tokens.py show tuo_username
```

## Esecuzione Manuale

### Avvio semplice
```cmd
cd C:\MyGest\Agent
python mygest_agent_windows.py
```

### Test con percorsi Windows
L'agent supporta:
- **Path locali**: `C:\Users\Sandro\Desktop\documento.pdf`
- **Path di rete UNC**: `\\NAS\Documenti\fatture\fattura.pdf`
- **Drive mappati**: `Z:\archivio\documento.pdf`

## Esecuzione Automatica all'Avvio

### Metodo 1: Task Scheduler (Consigliato)

1. Apri **Task Scheduler** (Utilità di pianificazione)
2. Click su "Crea attività..."
3. **Generale**:
   - Nome: `MyGest Agent`
   - Esegui indipendentemente dalla connessione dell'utente
   - Esegui con privilegi più elevati (se necessario)

4. **Trigger**:
   - Nuovo → All'avvio del computer
   - (Opzionale) Ritarda di 1 minuto

5. **Azioni**:
   - Nuovo → Avvio programma
   - Programma: `C:\Python311\python.exe` (path tuo Python)
   - Argomenti: `C:\MyGest\Agent\mygest_agent_windows.py`
   - Inizia da: `C:\MyGest\Agent\`

6. **Impostazioni**:
   - ✅ Consenti esecuzione su richiesta
   - ✅ Riavvia se non riuscita (ogni 1 minuto, max 3 tentativi)
   - ✅ Se attività già in esecuzione: non avviare nuova istanza

7. Salva e testa con "Esegui"

### Metodo 2: NSSM (Windows Service)

Più avanzato ma più robusto:

1. Scarica NSSM: https://nssm.cc/download
2. Estrai in `C:\MyGest\nssm\`
3. Apri cmd come amministratore:

```cmd
cd C:\MyGest\nssm\win64
nssm install MyGestAgent
```

4. Nella finestra:
   - Path: `C:\Python311\python.exe`
   - Startup directory: `C:\MyGest\Agent`
   - Arguments: `mygest_agent_windows.py`
   - Service name: `MyGestAgent`

5. Tab "Details":
   - Display name: MyGest Agent
   - Description: Agent per eliminazione automatica file MyGest

6. Tab "Log on":
   - Seleziona account con accesso ai file da eliminare

7. Click "Install service"

8. Avvia il servizio:
```cmd
nssm start MyGestAgent
```

Gestione servizio:
```cmd
nssm status MyGestAgent   # Stato
nssm stop MyGestAgent     # Ferma
nssm restart MyGestAgent  # Riavvia
nssm remove MyGestAgent   # Rimuovi servizio
```

## Accesso a File di Rete

### Credenziali per UNC Paths

Se i file sono su un NAS/server Windows con autenticazione:

#### Opzione A: Mappa come drive
```cmd
net use Z: \\NAS\Documenti /user:DOMINIO\utente password /persistent:yes
```
Poi nel form React usa: `Z:\fatture\documento.pdf`

#### Opzione B: Esegui agent come utente di dominio
Nel Task Scheduler o NSSM, configura "Esegui come" con:
- Utente: `DOMINIO\utente`
- Password: la password dell'utente

Così l'agent eredita i permessi di rete dell'utente.

## Verifica Funzionamento

### 1. Test manuale
```cmd
python mygest_agent_windows.py
```
Dovresti vedere:
```
✅ Connessione al server OK
⏰ Polling ogni 30 secondi
```

### 2. Test con file di prova
Crea un file di test:
```cmd
echo Test > C:\temp\test_mygest.txt
```

Dal browser MyGest:
1. Carica un documento
2. In "Percorso file origine": `C:\temp\test_mygest.txt`
3. ✅ Seleziona "Elimina file di origine"
4. Salva

Entro 30-60 secondi l'agent dovrebbe eliminarlo.

### 3. Controlla i log
Il file `mygest_agent_windows.log` contiene:
```
2025-11-20 19:30:15 - Trovate 1 richieste di eliminazione
2025-11-20 19:30:15 - ✅ File eliminato: C:\temp\test_mygest.txt (5 bytes)
```

## Troubleshooting

### Agent non si connette al server
- Verifica che `url` in config sia corretto
- Controlla che il server sia raggiungibile: `ping 192.168.1.100`
- Verifica firewall Windows non blocchi Python

### File non viene eliminato
- Controlla il file esista: `dir "C:\path\al\file.pdf"`
- Verifica permessi: l'utente che esegue l'agent deve poter eliminare il file
- Se è un file di rete, verifica credenziali

### "Permesso negato"
- File potrebbe essere aperto in un programma
- L'utente non ha permessi sufficienti
- Per file di rete, verifica autenticazione (vedi "Accesso a File di Rete")

### Agent non si avvia automaticamente
- Task Scheduler: controlla "Ultima esecuzione" e "Risultato ultima esecuzione"
- NSSM: `nssm status MyGestAgent` per vedere stato servizio
- Controlla Event Viewer di Windows (Registri di Windows → Applicazione)

## Path in Frontend

Nel form React, gli utenti Windows devono usare:

### Path locali
```
C:\Users\Sandro\Desktop\documento.pdf
```

### Path UNC (rete)
```
\\192.168.1.50\Documenti\fatture\fattura.pdf
\\NAS\archivio\contratti\contratto.pdf
```

### Drive mappati
```
Z:\documenti\documento.pdf
```

⚠️ **Nota**: NON usare slash Unix (`/`) ma backslash Windows (`\`)

## Monitoraggio

### Script PowerShell per statistiche
Crea `check_agent.ps1`:
```powershell
# Controlla se agent è in esecuzione
$process = Get-Process -Name python -ErrorAction SilentlyContinue | 
           Where-Object { $_.CommandLine -like "*mygest_agent_windows*" }

if ($process) {
    Write-Host "✅ Agent in esecuzione (PID: $($process.Id))" -ForegroundColor Green
} else {
    Write-Host "❌ Agent NON in esecuzione" -ForegroundColor Red
}

# Mostra ultime righe del log
Write-Host "`nUltimi 10 log:" -ForegroundColor Cyan
Get-Content mygest_agent_windows.log -Tail 10
```

Esegui con:
```powershell
powershell -ExecutionPolicy Bypass -File check_agent.ps1
```

## Aggiornamento Agent

1. Ferma agent/servizio
2. Sostituisci `mygest_agent_windows.py` con nuova versione
3. Riavvia agent/servizio

## Sicurezza

- **Token**: Mantieni segreto il token nel config
- **Permessi file**: L'agent può eliminare solo file accessibili dall'utente che lo esegue
- **Log**: I log contengono path completi dei file - proteggi il file log
- **Rete**: Usa HTTPS se il server è esposto su Internet

## Alternative

### Se non vuoi agent Windows
Usa path di rete montati su Linux (dove gira il server Django):

```bash
# Sul server Linux
sudo apt install cifs-utils
sudo mount -t cifs //192.168.1.50/Documenti /mnt/windows_share \
  -o username=utente,password=pass,uid=1000,gid=1000

# Nel form React usa path Linux
/mnt/windows_share/fatture/documento.pdf
```

Così l'agent Linux originale può eliminare file Windows via SMB/CIFS.
