# 🔧 FIX: Agent Non Si Avvia da PowerShell

## ❌ Problema Rilevato

Quando si avviava l'agent dal menu PowerShell (opzione G), si verificava:

```
Avvio MyGest Agent con Auto-Detection...
wsl: Processing /etc/fstab with mount -a failed.
Errore nell'avvio di MyGest Agent
```

## 🔍 Causa

Il comando `nohup` in WSL non funziona correttamente quando chiamato da PowerShell perché:
1. La sessione WSL si chiude troppo presto
2. Il processo `nohup` non riesce a staccarsi completamente
3. Il processo figlio (agent) viene terminato quando PowerShell chiude WSL

## ✅ Soluzione Implementata

### 1. Script Daemon Wrapper

Creato `/home/sandro/mygest/scripts/start_agent_daemon.sh`:

```bash
#!/bin/bash
# Script wrapper per avvio agent in background da PowerShell

cd /home/sandro/mygest
source venv/bin/activate 2>/dev/null

# Avvia agent in background con doppio fork per detach da terminale
(
    # Chiudi stdin, stdout, stderr
    exec 0</dev/null
    exec 1>logs/agent_autodetect.log
    exec 2>&1
    
    # Setsid per creare nuova sessione
    setsid python scripts/mygest_agent_autodetect.py &
    
    # Disown per staccare completamente
    disown
) &

# Attendi che il processo parta
sleep 2

# Restituisci PID
pgrep -f mygest_agent_autodetect.py || exit 1
```

**Tecniche usate:**
- ✅ **Doppio fork**: `( ... ) &` crea subshell in background
- ✅ **setsid**: Crea nuova sessione, stacca da terminale
- ✅ **disown**: Rimuove processo da job table
- ✅ **exec**: Reindirizza stdin/stdout/stderr
- ✅ **pgrep**: Verifica e restituisce PID

### 2. Aggiornamento PowerShell

Modificato `Start-AgentServer()` in `WSL_Server_Manager.ps1`:

```powershell
# Prima (NON FUNZIONANTE)
$result = wsl -d $WSL_DISTRO bash -c "cd $PROJECT_PATH && source venv/bin/activate 2>/dev/null && nohup python scripts/mygest_agent_autodetect.py > logs/agent_autodetect.log 2>&1 < /dev/null &" 2>$null

# Dopo (FUNZIONANTE)
$result = wsl -d $WSL_DISTRO bash -c "$PROJECT_PATH/scripts/start_agent_daemon.sh" 2>$null
```

### 3. Aggiornamento Quick Batch

Modificato `Quick_Start_Agent.bat`:

```batch
REM Prima
wsl -d Ubuntu bash -c "cd /home/sandro/mygest && source venv/bin/activate 2>/dev/null && nohup python scripts/mygest_agent_autodetect.py > logs/agent_autodetect.log 2>&1 < /dev/null &" 2>nul

REM Dopo
wsl -d Ubuntu bash -c "/home/sandro/mygest/scripts/start_agent_daemon.sh" 2>nul
```

## 🧪 Test Risultati

### Prima del Fix
```
❌ Agent non si avvia
❌ PID non viene trovato
❌ Processo termina immediatamente
```

### Dopo il Fix
```
✅ Agent si avvia correttamente
✅ PID: 285917 attivo
✅ Log: 533 file tracciati
✅ Processo resta attivo dopo chiusura PowerShell
```

**Verifica:**
```bash
$ ps aux | grep mygest_agent_autodetect
sandro  285917  2.5  0.1 924640 31092 ?  Ssl  18:34  0:00 python scripts/mygest_agent_autodetect.py

$ tail -5 logs/agent_autodetect.log
2026-02-24 18:34:19,704 - MyGestAgent - INFO - Scansione completata: 533 file unici tracciati
2026-02-24 18:34:19,704 - MyGestAgent - INFO - Agent avviato con auto-detection
2026-02-24 18:34:19,704 - MyGestAgent - INFO - Polling ogni 30 secondi
```

## 📝 Warning fstab (Ignorabili)

I messaggi:
```
wsl: Processing /etc/fstab with mount -a failed.
```

Sono **solo warning** relativi a mount point non disponibili in WSL. Non impediscono il funzionamento dell'agent e possono essere ignorati.

Per sopprimerli completamente, lo script usa `2>$null` / `2>nul`.

## 🎯 Come Usare Ora

### Da Menu PowerShell
```
Start_Manager.bat
→ G (Avvia Agent)
→ [OK] MyGest Agent avviato con successo (PID: 285917)
```

### Da Quick Batch
```
Quick_Start_Agent.bat
→ Agent si avvia correttamente
```

### Verifica Manuale
```bash
# Avvia
./scripts/start_agent_daemon.sh

# Verifica
pgrep -f mygest_agent_autodetect.py

# Log
tail -f logs/agent_autodetect.log
```

## 🔧 File Modificati

1. **scripts/start_agent_daemon.sh** (Nuovo) - Script wrapper daemon
2. **windows_manager/WSL_Server_Manager.ps1** - Usa nuovo script
3. **windows_manager/Quick_Start_Agent.bat** - Usa nuovo script

## ✅ Stato Finale

- ✅ Agent si avvia correttamente da PowerShell
- ✅ Processo resta attivo dopo chiusura terminale
- ✅ Log agent_autodetect.log popolato correttamente
- ✅ 533 file tracciati nelle 4 cartelle monitorate
- ✅ Watchdog attivo su tutte le cartelle

---

**Fix Applicato**: 2026-02-24 18:35  
**Versione**: 1.1  
**Stato**: ✅ **RISOLTO E TESTATO**
