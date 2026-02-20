# WSL Server Manager - Windows 11

## 📋 Panoramica

Strumento completo per gestire i server Django, Frontend (Vite) e SSH su WSL direttamente da Windows 11.

## ✨ Caratteristiche

- 🎨 **Interfaccia Grafica (GUI)** - Windows Forms con pulsanti e indicatori visivi
- 📟 **Menu Interattivo** - Interfaccia testuale completa in PowerShell
- ⚡ **Script Rapidi** - Avvio/Arresto/Riavvio con un click
- 📊 **Monitoraggio Real-time** - Stato dei server aggiornato automaticamente
- 🪟 **Terminali Separati** - Un terminale per ogni server per log dedicati
- � **Gestione SSH** - Controllo completo server SSH per accesso remoto
- 🌐 **Port Forwarding** - Setup automatico per accesso da rete esterna
- �🔧 **Configurabile** - Personalizza porte, percorsi e distribuzioni WSL

## 📁 File Inclusi

### Script Principali
| File | Descrizione |
|------|-------------|
| `WSL_Server_Manager_GUI.ps1` | ⭐ Interfaccia grafica moderna |
| `WSL_Server_Manager.ps1` | Script principale con menu interattivo |
| `Start_GUI.bat` | Launcher per interfaccia grafica |
| `Start_Manager.bat` | Launcher per menu interattivo |
| `Build_Executable.ps1` | Crea file .exe standalone |

### Script Rapidi - Applicazione
| File | Descrizione |
|------|-------------|
| `Quick_Start_All.bat` | Avvio rapido Django + Frontend |
| `Quick_Stop_All.bat` | Arresto rapido Django + Frontend |
| `Quick_Restart_All.bat` | Riavvio rapido Django + Frontend |

### Script Rapidi - SSH (Nuovo!)
| File | Descrizione |
|------|-------------|
| `Quick_Start_SSH.bat` | ⭐ Avvio rapido server SSH |
| `Quick_Stop_SSH.bat` | ⭐ Arresto rapido server SSH |
| `Quick_Restart_SSH.bat` | ⭐ Riavvio rapido server SSH |

### Configurazione e Setup
| File | Descrizione |
|------|-------------|
| `Setup_SSH_PortForward.ps1` | ⭐ Setup automatico port forwarding SSH |
| `Check_Configuration.bat` | Verifica configurazione WSL |

### Documentazione
| File | Descrizione |
|------|-------------|
| `README.md` | 📖 Guida completa del manager |
| `SSH_SETUP_GUIDE.md` | 📖 Guida configurazione SSH completa |
| `SSH_QUICK_START.md` | ⚡ Guida rapida SSH per utenti |
| `FEATURE_SSH_MANAGEMENT.md` | 📝 Documentazione tecnica SSH |
| `CHANGELOG.md` | 📋 Registro modifiche versioni |
| `CHECKLIST_SSH.md` | ✅ Checklist test funzionalità SSH |
| `INDEX.md` | 📑 Questo file - indice generale |

## 🚀 Utilizzo Rapido

### Metodo 1: Interfaccia Grafica (Consigliata)

```powershell
# Da Esplora Risorse Windows, vai a:
\\wsl$\Ubuntu\home\sandro\mygest\windows_manager

# Doppio click su:
Start_GUI.bat
```

### Metodo 2: Menu Interattivo

```powershell
Start_Manager.bat
```

### Metodo 3: Comandi Rapidi

**Applicazione (Django + Frontend)**:
```powershell
Quick_Start_All.bat    # Avvia Django + Frontend
Quick_Stop_All.bat     # Ferma Django + Frontend
Quick_Restart_All.bat  # Riavvia Django + Frontend
```

**SSH (Accesso Remoto)**: ⭐ Nuovo!
```powershell
Quick_Start_SSH.bat    # Avvia SSH
Quick_Stop_SSH.bat     # Ferma SSH
Quick_Restart_SSH.bat  # Riavvia SSH
```

## 🎮 Funzionalità dell'Interfaccia Grafica

```
┌─────────────────────────────────────────┐
│     🖥️ Gestione Server WSL             │
├─────────────────────────────────────────┤
│                                          │
│ Django Server (Port 8000)     ● ATTIVO  │
│ [▶ Avvia] [⏹ Ferma] [🔄 Riavvia]       │
│                                          │
│ Frontend Server (Port 5173)   ○ FERMO   │
│ [▶ Avvia] [⏹ Ferma] [🔄 Riavvia]       │
│                                          │
│ SSH Server (Porta 22)         ● ATTIVO  │ ⭐ Nuovo!
│ [▶ Avvia] [⏹ Ferma] [🔄 Riavvia]       │
│                                          │
│ [▶ Avvia Tutto] [⏹ Ferma Tutto] [🔄]   │
└─────────────────────────────────────────┘
```

- ✅ Pulsanti colorati (Verde=Avvia, Rosso=Ferma, Blu=Riavvia)
- ✅ Indicatori di stato in tempo reale (● ATTIVO / ○ FERMO)
- ✅ Aggiornamento automatico ogni 5 secondi
- ✅ Pulsanti disabilitati quando non applicabili
- ✅ Sezione SSH per gestione accesso remoto ⭐ Nuovo!

## 📖 Menu Interattivo (Console)

```
=== Server Applicazione ===
1. Avvia tutti i server          
2. Avvia solo Django            
3. Avvia solo Frontend          
4. Ferma tutti i server         
5. Ferma solo Django            
6. Ferma solo Frontend          
7. Riavvia tutti i server       
8. Riavvia solo Django          
9. Riavvia solo Frontend        

=== Server SSH (Accesso Remoto) === ⭐ Nuovo!
A. Avvia SSH
B. Ferma SSH
C. Riavvia SSH

=== Generale ===
S. Mostra stato                 
Q. Esci
```                 
Q. Esci
```

## ⚙️ Configurazione

Apri `WSL_Server_Manager.ps1` (o `WSL_Server_Manager_GUI.ps1`) e modifica:

```powershell
$WSL_DISTRO = "Ubuntu"                    # Nome distribuzione WSL
$PROJECT_PATH = "/home/sandro/mygest"     # Percorso progetto
$DJANGO_PORT = 8000                       # Porta Django
$FRONTEND_PORT = 5173                     # Porta Frontend
```

## 🔧 Creazione Eseguibile

Per creare un file `.exe` standalone:

```powershell
# 1. Apri PowerShell come Amministratore
cd \\wsl$\Ubuntu\home\sandro\mygest\windows_manager

# 2. Installa PS2EXE (solo prima volta)
.\Build_Executable.ps1 -Install

# 3. Crea l'eseguibile
.\Build_Executable.ps1

# 4. Troverai WSL_Server_Manager.exe nella cartella
```

## 📦 Trasferimento su Windows

### Opzione A: Accesso Diretto (Zero Copia)

```
\\wsl$\Ubuntu\home\sandro\mygest\windows_manager
```

### Opzione B: Copia sul Desktop

```powershell
Copy-Item -Path "\\wsl$\Ubuntu\home\sandro\mygest\windows_manager" `
          -Destination "$env:USERPROFILE\Desktop\" -Recurse
```

### Opzione C: Usa l'Eseguibile

Copia solo `WSL_Server_Manager.exe` dove preferisci.

## 🎯 URL dei Server

Dopo l'avvio i server sono accessibili da Windows su:

- **Django Backend:** http://localhost:8000
- **Frontend Vite:** http://localhost:5173

## 🔍 Risoluzione Problemi

### Verifica Configurazione

```bat
Check_Configuration.bat
```

### Problem: "Script non autorizzato"

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problem: "Porta già in uso"

Usa l'opzione "Riavvia" che termina i vecchi processi.

### Problem: "WSL non trovato"

```powershell
wsl --status
wsl --list --verbose
```

## 📚 Documentazione Completa

- **README.md** - Documentazione dettagliata completa
- **QUICK_START.md** - Guida rapida per iniziare
- **PACKAGE_INFO.md** - Informazioni sul package
- **TRASFERIMENTO_WINDOWS.md** - Guide per il trasferimento
- **INDEX.md** - Questo file (indice generale)

## 🚦 Prerequisiti

- ✅ Windows 11
- ✅ WSL2 installato e configurato
- ✅ Distribuzione Ubuntu (o altra) su WSL
- ✅ Python 3.x installato su WSL
- ✅ Node.js installato su WSL
- ✅ Progetto MyGest in `/home/sandro/mygest`

## 💡 Tips

### Avvio Automatico Windows

Copia un collegamento a `Quick_Start_All.bat` in:
```
shell:startup
```

### Collegamento Desktop

Crea un collegamento a `Start_GUI.bat` sul Desktop per accesso rapido.

### Alias PowerShell

Aggiungi al tuo `$PROFILE`:
```powershell
function Start-MyGest { 
    & "\\wsl$\Ubuntu\home\sandro\mygest\windows_manager\WSL_Server_Manager.ps1" -Action start 
}
```

## 🆘 Supporto

Per problemi o domande, consulta la documentazione completa in `README.md` o esegui `Check_Configuration.bat` per diagnostica automatica.

## 📄 Licenza

Parte del progetto MyGest.

---

**Versione:** 1.0  
**Ultimo Aggiornamento:** Dicembre 2024  
**Compatibilità:** Windows 11 + WSL2
