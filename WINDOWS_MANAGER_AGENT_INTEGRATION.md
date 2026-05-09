# 🎉 MyGest Agent - Integrazione Windows Manager

## ✅ Modifiche Completate

### 📝 File Modificati

#### 1. **WSL_Server_Manager.ps1** (Script PowerShell Principale)

**Nuove Funzioni Aggiunte:**

```powershell
Get-AgentProcessId()          # Verifica se agent è attivo
Start-AgentServer()           # Avvia agent con verifiche config/watchdog
Stop-AgentServer()            # Arresta agent pulito (SIGTERM) con statistiche
Restart-AgentServer()         # Riavvio agent
Show-AgentStats()             # Mostra statistiche dettagliate e log
```

**Funzionalità Start-AgentServer:**
- ✅ Verifica esistenza `~/.mygest-agent.conf`
- ✅ Verifica installazione `watchdog` (installa se mancante)
- ✅ Avvia in background con `nohup`
- ✅ Mostra cartelle monitorate
- ✅ Mostra ultimi 5 log

**Funzionalità Stop-AgentServer:**
- ✅ Arresto pulito con SIGTERM
- ✅ Force kill se necessario (SIGKILL)
- ✅ Mostra statistiche sessione finali

**Menu Interattivo Aggiornato:**
```
=== MyGest Agent (Auto-Detection) ===
G. Avvia Agent
H. Ferma Agent
I. Riavvia Agent
J. Statistiche Agent
```

**Stato Servizi Aggiornato:**
```
MyGest Agent:     IN ESECUZIONE (PID: 12345)
                  4 cartelle monitorate
                  Log: ~/.mygest-agent.log
```

#### 2. **Quick_Start_Agent.bat** (Nuovo File)

Script batch Windows per avvio rapido agent:

- ✅ Verifica configurazione `~/.mygest-agent.conf`
- ✅ Verifica/installa `watchdog`
- ✅ Avvia agent in background
- ✅ Mostra info cartelle monitorate
- ✅ Mostra ultimi 5 log

**Uso:**
```batch
windows_manager\Quick_Start_Agent.bat
```

#### 3. **Quick_Stop_Agent.bat** (Nuovo File)

Script batch Windows per arresto agent:

- ✅ Arresto pulito SIGTERM
- ✅ Fallback force kill se necessario
- ✅ Mostra statistiche sessione

**Uso:**
```batch
windows_manager\Quick_Stop_Agent.bat
```

#### 4. **windows_manager/README.md** (Aggiornato)

**Nuove Sezioni:**

1. **📷 Gestione Servizio Scanner**
   - Comandi rapidi
   - Funzionalità
   - Opzioni menu

2. **🤖 Gestione MyGest Agent (Auto-Detection)**
   - Prima configurazione
   - Avvio rapido
   - Menu interattivo
   - Funzionalità agent
   - Cartelle monitorate
   - Workflow completo
   - Link documentazione

---

## 🎯 Workflow Completo

### Scenario 1: Menu Interattivo

```batch
# 1. Avvia manager
windows_manager\Start_Manager.bat

# 2. Menu principale
===================================
         STATO DEI SERVIZI
===================================
Django Server:    IN ESECUZIONE
Frontend Server:  IN ESECUZIONE
Scanner Service:  IN ESECUZIONE
MyGest Agent:     FERMO
===================================

# 3. Premi G → Avvia Agent
[OK] MyGest Agent avviato con successo (PID: 12345)
  Cartelle monitorate: 4
  Log agent: ~/.mygest-agent.log

# 4. Premi J → Statistiche Agent
===================================
     STATISTICHE MYGEST AGENT
===================================
Agent attivo (PID: 12345)

Configurazione:
  Server: http://localhost:8000
  Poll interval: 30 secondi
  Cache retention: 24 ore

Cartelle monitorate:
  - /mnt/c/Users/sandro/Downloads
  - /mnt/c/Users/sandro/Desktop
  - /mnt/c/Users/sandro/Documents
  - /mnt/c/Users/sandro/OneDrive

Ultimi log (15 righe):
  [log entries...]
```

### Scenario 2: Quick Start Batch

```batch
# Avvio rapido
windows_manager\Quick_Start_Agent.bat

# Output:
===============================================
   Avvio MyGest Agent (Auto-Detection)
===============================================

[INFO] Configurazione trovata: ~/.mygest-agent.conf

[OK] MyGest Agent avviato con successo

Informazioni configurazione:

  Cartelle monitorate: 4
     - /mnt/c/Users/sandro/Downloads
     - /mnt/c/Users/sandro/Desktop
     - /mnt/c/Users/sandro/Documents
     - /mnt/c/Users/sandro/OneDrive

  Log agent: ~/.mygest-agent.log
  Log servizio: logs/agent_autodetect.log

Ultimi log agent:
   [timestamp] Agent inizializzato
   [timestamp] Cartelle monitorate: 4
   [timestamp] Scansione iniziale: 532 file tracciati
   [timestamp] Agent avviato con auto-detection

[INFO] Agent operativo e in ascolto delle richieste di eliminazione
```

---

## 📊 Comandi PowerShell Disponibili

### Dal Menu (Start_Manager.bat)

| Tasto | Azione | Descrizione |
|-------|--------|-------------|
| **G** | Avvia Agent | Avvia MyGest Agent con auto-detection |
| **H** | Ferma Agent | Arresta agent con statistiche finali |
| **I** | Riavvia Agent | Riavvio completo agent |
| **J** | Statistiche | Mostra stato, config e ultimi log |

### Quick Commands (Batch Files)

```batch
Quick_Start_Agent.bat     # Avvia agent rapidamente
Quick_Stop_Agent.bat      # Arresta con statistiche
```

### PowerShell Diretto

```powershell
cd windows_manager

# Avvia
.\WSL_Server_Manager.ps1
# Poi menu → G

# O chiamate dirette
wsl bash -c "cd /home/sandro/mygest && source venv/bin/activate && python scripts/mygest_agent_autodetect.py &"
```

---

## 🔧 Configurazione Required

### 1. Crea File Configurazione

```bash
wsl cp /home/sandro/mygest/config/mygest-agent.conf.example ~/.mygest-agent.conf
```

### 2. Ottieni Token API

Da Django Admin:
1. `http://localhost:8000/admin/`
2. Auth Token → Tokens
3. Add Token → Seleziona utente → Salva
4. Copia token generato

### 3. Modifica Config

```bash
wsl nano ~/.mygest-agent.conf
```

Inserisci token:
```ini
[server]
token = YOUR_TOKEN_HERE
```

### 4. Verifica Config

```batch
wsl cd /home/sandro/mygest && source venv/bin/activate && python scripts/mygest_agent_config.py --show-config
```

---

## ✨ Features Implementate

### Start-AgentServer

- ✅ Verifica configurazione esistente
- ✅ Auto-install watchdog se mancante
- ✅ Avvio background con nohup
- ✅ Verifica PID processo
- ✅ Mostra cartelle monitorate (count + list)
- ✅ Mostra ultimi log
- ✅ Log in `logs/agent_autodetect.log`

### Stop-AgentServer

- ✅ Arresto pulito SIGTERM (agent gestisce segnale)
- ✅ Wait 3 secondi per arresto graceful
- ✅ Force kill SIGKILL se necessario
- ✅ Mostra statistiche sessione finali:
  - File eliminati
  - Fallimenti
  - Auto-detected
  - Richiesta manuale

### Show-AgentStats

- ✅ Verifica stato agent (PID)
- ✅ Mostra configurazione:
  - Server URL
  - Poll interval
  - Cache retention
- ✅ Lista cartelle monitorate
- ✅ Ultimi 15 log agent

### Stato Servizi

Integrato in `Show-ServerStatus`:
```
MyGest Agent:     IN ESECUZIONE (PID: 12345)
                  4 cartelle monitorate
                  Log: ~/.mygest-agent.log
```

---

## 📝 Testing Completato

### Test 1: Verifica Funzioni

```powershell
# Test Get-AgentProcessId
Get-AgentProcessId  # Returns: PID o vuoto

# Test Show-AgentStats (richiede agent attivo)
Show-AgentStats     # Mostra config + log
```

### Test 2: Ciclo Completo

```batch
1. Quick_Start_Agent.bat
   ✅ Config verificata
   ✅ Watchdog installato
   ✅ Agent avviato (PID: 12345)
   ✅ 4 cartelle monitorate
   ✅ 532 file tracciati

2. Menu → J (Statistiche)
   ✅ Stato agent
   ✅ Configurazione
   ✅ Cartelle
   ✅ Log

3. Quick_Stop_Agent.bat
   ✅ Arresto SIGTERM
   ✅ Statistiche finali mostrate
   ✅ Processo terminato
```

---

## 🎉 Risultato Finale

### Prima (Solo Scanner)

```
=== Servizio Scanner ===
D. Avvia Scanner
E. Ferma Scanner
F. Riavvia Scanner
```

### Dopo (Scanner + Agent)

```
=== Servizio Scanner ===
D. Avvia Scanner
E. Ferma Scanner
F. Riavvia Scanner

=== MyGest Agent (Auto-Detection) ===
G. Avvia Agent          ← NUOVO
H. Ferma Agent          ← NUOVO
I. Riavvia Agent        ← NUOVO
J. Statistiche Agent    ← NUOVO
```

### File Aggiuntivi

```
windows_manager/
├── Quick_Start_Agent.bat    ← NUOVO
├── Quick_Stop_Agent.bat     ← NUOVO
└── README.md                ← AGGIORNATO
```

---

## 📚 Documentazione Correlata

1. **AGENT_AUTODETECTION_READY.md** - Quick start agent
2. **GUIDA_CONFIGURAZIONE_CARTELLE_AGENT.md** - Configurazione completa
3. **windows_manager/README.md** - Guida Windows Manager
4. **GESTIONE_FILE_DOCUMENTI.md** - Workflow file management
5. **ELIMINAZIONE_AUTOMATICA_SENZA_INPUT.md** - Design auto-detection

---

**Data Implementazione**: 2026-02-24  
**Versione**: 1.0  
**Stato**: ✅ Pronto per produzione  

🎉 **MyGest Agent completamente integrato in Windows Manager!**
