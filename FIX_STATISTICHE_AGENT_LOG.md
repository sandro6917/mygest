# 📊 Aggiornamento Statistiche Agent - Log Corretto

## 🔄 Problema

La funzione `Show-AgentStats` (opzione J) mostrava i log del **vecchio agent** (`~/.mygest-agent.log`) invece dei log dell'**agent autodetect** (`logs/agent_autodetect.log`).

**Risultato**: Venivano mostrati log datati (novembre 2025) invece dei log correnti (febbraio 2026).

## ✅ Correzione Applicata

### 1. **Show-AgentStats** - Mostra Log Corretti

**Prima:**
```powershell
wsl bash -c "tail -n 15 ~/.mygest-agent.log"
```

**Dopo:**
```powershell
wsl bash -c "tail -n 15 $PROJECT_PATH/logs/agent_autodetect.log"
```

**Aggiunte:**
- ✅ Estrae numero file tracciati dalla cache
- ✅ Mostra data/ora avvio agent
- ✅ Verifica esistenza log prima di leggerlo

### 2. **Start-AgentServer** - Log Avvio

**Prima:**
```powershell
tail -n 5 ~/.mygest-agent.log
```

**Dopo:**
```powershell
tail -n 8 logs/agent_autodetect.log
```

### 3. **Stop-AgentServer** - Statistiche Finali

**Prima:**
```powershell
tail -n 20 ~/.mygest-agent.log | grep Statistiche
```

**Dopo:**
```powershell
tail -n 20 logs/agent_autodetect.log | grep Statistiche
```

### 4. **Show-ServerStatus** - Info Agent

**Prima:**
```
MyGest Agent:     IN ESECUZIONE (PID: 287488)
                  4 cartelle monitorate
                  Log: ~/.mygest-agent.log
```

**Dopo:**
```
MyGest Agent:     IN ESECUZIONE (PID: 287488)
                  4 cartelle, 533 file tracciati
                  Log: logs/agent_autodetect.log
```

## 📝 Output Aggiornato

### Opzione J (Statistiche Agent)

```
=======================================
     STATISTICHE MYGEST AGENT
=======================================
Agent attivo (PID: 287488)

Configurazione:
  Server: http://localhost:8000
  Poll interval: 30 secondi
  Cache retention: 24 ore

Cartelle monitorate:
  - /mnt/c/Users/sandro/Downloads
  - /mnt/c/Users/sandro/Desktop
  - /mnt/c/Users/sandro/Documents
  - /mnt/c/Users/sandro/OneDrive

Stato Agent:
  File tracciati in cache: 533
  Avviato: 2026-02-24 18:39:03

Ultimi log (15 righe):
  2026-02-24 18:39:03 - Agent inizializzato
  2026-02-24 18:39:03 - Cartelle monitorate: 4
  2026-02-24 18:39:04 - 📂 Monitoraggio avviato: Downloads
  2026-02-24 18:39:04 - 📂 Monitoraggio avviato: Desktop
  2026-02-24 18:39:04 - 📂 Monitoraggio avviato: Documents
  2026-02-24 18:39:04 - 📂 Monitoraggio avviato: OneDrive
  2026-02-24 18:39:04 - Scansione iniziale cartelle...
  2026-02-24 18:39:06 - Scansione completata: 533 file tracciati
  2026-02-24 18:39:06 - Agent avviato con auto-detection
  2026-02-24 18:39:06 - Polling ogni 30 secondi
=======================================
```

### Opzione S (Stato Servizi)

```
MyGest Agent:     IN ESECUZIONE (PID: 287488)
                  4 cartelle, 533 file tracciati    ← NUOVO!
                  Log: logs/agent_autodetect.log
```

## 🔧 Warning fstab Soppressi

Aggiunto `2>$null` a tutti i comandi WSL per sopprimere:
```
wsl: Processing /etc/fstab with mount -a failed.
```

## ✅ Stato Finale

- ✅ Log corretti mostrati (agent_autodetect.log)
- ✅ Date aggiornate (febbraio 2026)
- ✅ Numero file tracciati visibile
- ✅ Warning fstab soppressi
- ✅ Info più utili nello stato servizi

---

**Aggiornamento Applicato**: 2026-02-24 18:40  
**File Modificato**: `windows_manager/WSL_Server_Manager.ps1`
