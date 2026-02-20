# 📦 WSL Server Manager - Package Completo

## ✅ Cosa è stato creato

Ho creato un sistema completo per gestire i server Django e Frontend da Windows 11:

### 📁 File Creati in `windows_manager/`

| File | Descrizione |
|------|-------------|
| `WSL_Server_Manager.ps1` | Script principale PowerShell con tutte le funzionalità |
| `Start_Manager.bat` | Launcher principale con menu interattivo |
| `Build_Executable.ps1` | Script per creare un file .exe standalone |
| `Quick_Start_All.bat` | Avvio rapido di tutti i server |
| `Quick_Stop_All.bat` | Arresto rapido di tutti i server |
| `Quick_Restart_All.bat` | Riavvio rapido di tutti i server |
| `Check_Configuration.bat` | Verifica della configurazione WSL |
| `README.md` | Documentazione completa |
| `QUICK_START.md` | Guida rapida per iniziare |
| `PACKAGE_INFO.md` | Questo file |

---

## 🚀 Come Usare SUBITO (Da WSL/Linux)

### Opzione A: Copia su Windows e Usa

1. **Copia la cartella su Windows:**
   ```bash
   # Dalla WSL, copia tutto sul Desktop di Windows
   cp -r /home/sandro/mygest/windows_manager /mnt/c/Users/TUO_USERNAME/Desktop/
   ```

2. **Vai al Desktop di Windows ed esegui:**
   - Doppio click su `Check_Configuration.bat` per verificare la configurazione
   - Doppio click su `Start_Manager.bat` per aprire il menu
   - OPPURE usa `Quick_Start_All.bat` per avviare tutto subito

### Opzione B: Accedi via Esplora Risorse Windows

1. **Apri Esplora Risorse Windows**
2. **Nella barra degli indirizzi digita:**
   ```
   \\wsl$\Ubuntu\home\sandro\mygest\windows_manager
   ```
3. **Doppio click sui file `.bat` direttamente da lì**

### Opzione C: Crea Eseguibile Standalone

1. **Apri PowerShell come Amministratore in Windows**
2. **Vai alla cartella:**
   ```powershell
   cd \\wsl$\Ubuntu\home\sandro\mygest\windows_manager
   ```
3. **Installa PS2EXE (solo la prima volta):**
   ```powershell
   .\Build_Executable.ps1 -Install
   ```
4. **Crea l'eseguibile:**
   ```powershell
   .\Build_Executable.ps1
   ```
5. **Copia `WSL_Server_Manager.exe` dove vuoi e usalo**

---

## 🎯 Funzionalità Principali

### Menu Interattivo Completo
- ✅ Avvia/Ferma/Riavvia singolarmente Django o Frontend
- ✅ Gestione di entrambi i server insieme
- ✅ Monitoraggio stato in tempo reale
- ✅ Interfaccia colorata e user-friendly

### Script Rapidi
- ⚡ Avvio rapido con un click
- ⛔ Arresto rapido con un click
- 🔄 Riavvio rapido con un click

### Verifica Configurazione
- 🔍 Controllo automatico di WSL, Python, Node.js
- 📋 Report dettagliato della configurazione

---

## 📝 Configurazione Personalizzata

Se i tuoi server usano porte diverse o hai una configurazione diversa:

1. **Apri `WSL_Server_Manager.ps1`**
2. **Modifica queste righe all'inizio del file:**

```powershell
$WSL_DISTRO = "Ubuntu"                    # Cambia se usi altra distro
$PROJECT_PATH = "/home/sandro/mygest"     # Il tuo percorso progetto
$DJANGO_PORT = 8000                       # Porta Django (default 8000)
$FRONTEND_PORT = 5173                     # Porta Vite (default 5173)
```

3. **Salva e usa lo script aggiornato**

---

## 🎨 Personalizzazioni Avanzate

### Aggiungere un'Icona all'Eseguibile

1. Crea o scarica un file `.ico` (256x256 pixel)
2. Salvalo come `icon.ico` nella cartella `windows_manager/`
3. Riesegui `Build_Executable.ps1`

### Cambiare i Colori del Menu

Nel file `WSL_Server_Manager.ps1`, cerca la funzione `Write-ColorOutput` e modifica i colori:
- `Cyan` (azzurro)
- `Green` (verde)
- `Yellow` (giallo)
- `Red` (rosso)

---

## 🔧 Risoluzione Problemi Comuni

### Problema: "Impossibile eseguire script"
**Soluzione:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problema: "WSL non trovato"
**Soluzione:** Verifica che WSL sia installato:
```powershell
wsl --status
wsl --list --verbose
```

### Problema: "Server non si avvia"
**Soluzione:** 
1. Esegui `Check_Configuration.bat` per diagnosticare
2. Controlla che le porte 8000 e 5173 non siano già occupate
3. Verifica i terminali aperti per vedere eventuali errori

### Problema: "Porta già in uso"
**Soluzione:** Usa l'opzione "Riavvia" nel menu, che termina i vecchi processi prima di riavviare

---

## 📱 Uso nei Vari Scenari

### Scenario 1: Sviluppo Giornaliero
```
Mattina:  Quick_Start_All.bat
Lavoro:   Sviluppa normalmente
Sera:     Quick_Stop_All.bat
```

### Scenario 2: Debug di un Singolo Server
```
1. Start_Manager.bat
2. Opzione 2 o 3 (avvia solo Django o Frontend)
3. Controlla il terminale per gli errori
4. Opzione 5 o 6 per fermare
```

### Scenario 3: Presentazione/Demo
```
1. Quick_Start_All.bat
2. Apri browser su localhost:5173
3. Dopo la demo: Quick_Stop_All.bat
```

---

## 🚢 Distribuzione ad Altri Utenti

Se vuoi condividere questo tool con altri sviluppatori del team:

### Metodo 1: Condividi i File Sorgenti
1. Zippa la cartella `windows_manager/`
2. Gli altri devono solo estrarre e usare i file `.bat`

### Metodo 2: Condividi l'Eseguibile
1. Crea l'eseguibile con `Build_Executable.ps1`
2. Condividi solo `WSL_Server_Manager.exe`
3. Gli altri possono usarlo direttamente (se hanno la stessa configurazione WSL)

### Metodo 3: Crea un Installer
Usa Inno Setup (vedi README.md) per creare un installer professionale.

---

## 📊 Monitoring e Logs

### Vedere i Log dei Server

I server vengono avviati in terminali separati, quindi puoi:
1. Vedere gli output in tempo reale nelle finestre dei terminali
2. Fare Ctrl+C in un terminale per fermare quel server specifico

### Stato dei Servizi

Usa l'opzione "S" nel menu o esegui:
```powershell
.\WSL_Server_Manager.ps1 -Action status
```

---

## 🔄 Aggiornamenti Futuri

Per aggiornare lo script:
1. Modifica `WSL_Server_Manager.ps1`
2. Se hai creato un .exe, riesegui `Build_Executable.ps1`
3. Sostituisci i vecchi file

---

## 📚 Documentazione Disponibile

- `README.md` - Documentazione completa e dettagliata
- `QUICK_START.md` - Guida rapida per iniziare subito
- `PACKAGE_INFO.md` - Questo file (panoramica generale)

---

## 🎓 Comandi Utili da PowerShell

```powershell
# Avvia con menu interattivo
.\WSL_Server_Manager.ps1

# Avvia tutti i server (senza menu)
.\WSL_Server_Manager.ps1 -Action start

# Ferma tutti i server
.\WSL_Server_Manager.ps1 -Action stop

# Riavvia tutti i server
.\WSL_Server_Manager.ps1 -Action restart

# Mostra solo lo stato
.\WSL_Server_Manager.ps1 -Action status
```

---

## 💡 Tips & Tricks

### Avvio Automatico all'Accesso Windows
1. Premi `Win + R`
2. Digita `shell:startup`
3. Copia il collegamento a `Quick_Start_All.bat` in quella cartella

### Collegamento Rapido sulla Taskbar
1. Crea un collegamento a `Start_Manager.bat` sul Desktop
2. Trascina il collegamento sulla Taskbar

### Alias da PowerShell
Aggiungi al tuo profilo PowerShell (`$PROFILE`):
```powershell
function Start-MyGest { & "\\wsl$\Ubuntu\home\sandro\mygest\windows_manager\WSL_Server_Manager.ps1" -Action start }
function Stop-MyGest { & "\\wsl$\Ubuntu\home\sandro\mygest\windows_manager\WSL_Server_Manager.ps1" -Action stop }
```

Poi usa semplicemente:
```powershell
Start-MyGest
Stop-MyGest
```

---

## ✨ Caratteristiche Tecniche

- **Linguaggio:** PowerShell 5.1+
- **Compatibilità:** Windows 11 + WSL2
- **Requisiti:** WSL con Ubuntu (o altra distro Linux)
- **Dipendenze:** Nessuna per l'uso base
- **Dipendenze per .exe:** PS2EXE module

---

## 🆘 Supporto

Se incontri problemi:

1. **Esegui la diagnostica:**
   ```
   Check_Configuration.bat
   ```

2. **Verifica manualmente WSL:**
   ```powershell
   wsl echo "Test OK"
   wsl ls /home/sandro/mygest
   ```

3. **Controlla i terminali aperti** per vedere gli errori dei server

4. **Consulta README.md** per la risoluzione dettagliata dei problemi

---

## 📋 Checklist Pre-Utilizzo

- [ ] WSL installato e funzionante
- [ ] Distribuzione Ubuntu configurata
- [ ] Progetto presente in `/home/sandro/mygest`
- [ ] Python 3.x installato su WSL
- [ ] Node.js installato su WSL
- [ ] Virtual environment Python creato (opzionale ma consigliato)
- [ ] Dipendenze npm installate in `frontend/`
- [ ] File `.bat` testati

---

**Buon lavoro! 🚀**

Per domande o problemi, consulta la documentazione completa in README.md.
