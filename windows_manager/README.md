# WSL Server Manager - Guida Completa

## 📋 Panoramica

Questo strumento consente di gestire facilmente i server Django, Frontend e SSH del progetto MyGest che girano su WSL (Windows Subsystem for Linux) direttamente da Windows 11.

## 🎯 Funzionalità

- ✅ Avvio/Arresto/Riavvio dei server Django e Frontend con un click
- 🔐 Gestione completa del server SSH per accesso remoto
- 📷 Gestione servizio Scanner per scansioni documenti
- 🤖 Gestione MyGest Agent per auto-detection ed eliminazione file
- 🎨 Interfaccia grafica e a menu interattiva
- 📊 Monitoraggio dello stato dei servizi in tempo reale
- 🪟 Apertura automatica di terminali separati per ogni server
- 🔄 Supporto per comandi da linea di comando
- 🌐 Configurazione port forwarding per accesso da rete esterna

## 📁 Struttura dei File

```
windows_manager/
├── WSL_Server_Manager.ps1           # Script principale PowerShell (console)
├── WSL_Server_Manager_GUI.ps1       # Versione con interfaccia grafica
├── Start_Manager.bat                # Launcher menu interattivo
├── Start_GUI.bat                    # Launcher interfaccia grafica
├── Build_Executable.ps1             # Script per creare l'eseguibile
├── Quick_Start_All.bat              # Avvio rapido Django + Frontend
├── Quick_Stop_All.bat               # Arresto rapido Django + Frontend
├── Quick_Restart_All.bat            # Riavvio rapido Django + Frontend
├── Quick_Start_SSH.bat              # Avvio rapido SSH
├── Quick_Stop_SSH.bat               # Arresto rapido SSH
├── Quick_Restart_SSH.bat            # Riavvio rapido SSH
├── Quick_Start_Scanner.bat          # Avvio rapido Scanner Service
├── Quick_Start_Agent.bat            # Avvio rapido MyGest Agent
├── Quick_Stop_Agent.bat             # Arresto rapido MyGest Agent
├── Setup_SSH_PortForward.ps1        # Configurazione port forwarding SSH
├── SSH_SETUP_GUIDE.md               # Guida completa configurazione SSH
└── README.md                        # Questa guida
```

## 🚀 Installazione e Uso

### Metodo 1: Uso Diretto (Consigliato per test)

1. **Apri PowerShell come Amministratore**
2. **Naviga nella cartella del progetto su Windows:**
   ```powershell
   cd \\wsl$\Ubuntu\home\sandro\mygest\windows_manager
   ```
3. **Esegui lo script:**
   ```powershell
   .\Start_Manager.bat
   ```

### Metodo 2: Creazione Eseguibile Standalone

1. **Apri PowerShell come Amministratore**
2. **Naviga nella cartella:**
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
5. **L'eseguibile `WSL_Server_Manager.exe` sarà creato nella stessa cartella**

### Metodo 3: Copia su Windows

Dopo aver creato l'eseguibile, puoi:
1. Copiare `WSL_Server_Manager.exe` in una cartella su Windows (es. `C:\Tools\`)
2. Creare un collegamento sul Desktop
3. Avviarlo con doppio click

## 🎮 Uso del Menu Interattivo

Quando avvii il manager con `Start_Manager.bat`, vedrai un menu con queste opzioni:

```
=== Server Applicazione ===
1. Avvia tutti i server          - Avvia Django + Frontend
2. Avvia solo Django            - Avvia solo il backend Django
3. Avvia solo Frontend          - Avvia solo il server Vite
4. Ferma tutti i server         - Arresta Django + Frontend
5. Ferma solo Django            - Arresta solo Django
6. Ferma solo Frontend          - Arresta solo Frontend
7. Riavvia tutti i server       - Riavvia Django + Frontend
8. Riavvia solo Django          - Riavvia solo Django
9. Riavvia solo Frontend        - Riavvia solo Frontend

=== Server SSH (Accesso Remoto) ===
A. Avvia SSH                    - Avvia server SSH per accesso remoto
B. Ferma SSH                    - Arresta server SSH
C. Riavvia SSH                  - Riavvia server SSH

=== Generale ===
S. Mostra stato                 - Controlla lo stato di tutti i servizi
Q. Esci                         - Chiude il manager
```

## 🖼️ Interfaccia Grafica (GUI)

Avvia l'interfaccia grafica con `Start_GUI.bat` per una gestione visuale dei servizi:

- **Django Server**: Controlli per avvio, arresto e riavvio del backend
- **Frontend Server**: Controlli per avvio, arresto e riavvio del frontend
- **SSH Server**: Controlli per avvio, arresto e riavvio del server SSH
- **Indicatori di Stato**: In tempo reale (● ATTIVO / ○ FERMO)
- **Pulsanti Globali**: Gestione rapida di tutti i servizi
- **Auto-refresh**: Aggiornamento automatico dello stato ogni 5 secondi

## 🖥️ Uso da Linea di Comando

Puoi anche usare il manager senza menu interattivo:

```powershell
# Avvia tutti i server
.\WSL_Server_Manager.ps1 -Action start

# Ferma tutti i server
.\WSL_Server_Manager.ps1 -Action stop

# Riavvia tutti i server
.\WSL_Server_Manager.ps1 -Action restart

# Mostra lo stato
.\WSL_Server_Manager.ps1 -Action status

# Apri il menu interattivo (default)
.\WSL_Server_Manager.ps1 -Action menu
```

## ⚙️ Configurazione

### Personalizzazione dello Script

Apri `WSL_Server_Manager.ps1` o `WSL_Server_Manager_GUI.ps1` e modifica queste variabili se necessario:

```powershell
$WSL_DISTRO = "Ubuntu-22.04"              # Nome della distribuzione WSL
$PROJECT_PATH = "/home/sandro/mygest"     # Percorso del progetto su WSL
$DJANGO_PORT = 8000                       # Porta del server Django
$FRONTEND_PORT = 5173                     # Porta del server Frontend (Vite)
$SSH_PORT = 22                            # Porta SSH (default 22)
```

### Verifica della Distribuzione WSL

Per vedere il nome della tua distribuzione WSL:
```powershell
wsl --list --verbose
```

## 🔐 Configurazione SSH per Accesso Remoto

### Quick Start SSH

Per una configurazione rapida dell'SSH:

1. **Installa SSH Server su WSL** (se non già installato):
   ```bash
   sudo apt update
   sudo apt install openssh-server -y
   ```

2. **Configura Port Forwarding** (da PowerShell come Amministratore):
   ```powershell
   cd \\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager
   .\Setup_SSH_PortForward.ps1
   ```

3. **Avvia SSH** usando uno di questi metodi:
   - GUI: `Start_GUI.bat` → Clicca "▶ Avvia" nella sezione SSH
   - Menu: `Start_Manager.bat` → Premi "A"
   - Batch: `Quick_Start_SSH.bat`

4. **Connettiti da un altro PC**:
   ```bash
   ssh tuo_utente@IP_PC_WINDOWS
   ```

### Configurazione Completa

Per una guida dettagliata su:
- Configurazione sicura di SSH
- Autenticazione con chiavi SSH
- Firewall e port forwarding
- Accesso da Internet
- Troubleshooting

Consulta: **[SSH_SETUP_GUIDE.md](SSH_SETUP_GUIDE.md)**

### Comandi Rapidi SSH

```batch
# Avvia SSH
Quick_Start_SSH.bat

# Ferma SSH
Quick_Stop_SSH.bat

# Riavvia SSH
Quick_Restart_SSH.bat
```

## 🔧 Risoluzione Problemi

### Problema: "Impossibile eseguire script PowerShell"

**Soluzione:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problema: "WSL non trovato"

**Soluzione:**
Assicurati che WSL sia installato e configurato correttamente:
```powershell
wsl --status
```

### Problema: "I server non si avviano"

**Verifiche:**
1. WSL è in esecuzione?
2. Il percorso del progetto è corretto?
3. Le dipendenze sono installate?

**Comandi di verifica:**
```powershell
# Verifica WSL
wsl echo "WSL funziona!"

# Verifica percorso progetto
wsl ls /home/sandro/mygest

# Verifica Python Django
wsl python /home/sandro/mygest/manage.py --version

# Verifica Node.js per Frontend
wsl node --version
```

### Problema: "Porta già in uso"

Se i server sono già in esecuzione su altre istanze:
```powershell
# Trova e termina processi sulla porta 8000 (Django)
wsl bash -c "fuser -k 8000/tcp"

# Trova e termina processi sulla porta 5173 (Frontend)
wsl bash -c "fuser -k 5173/tcp"
```

## 📝 Note Importanti

### Virtual Environment Python

Lo script tenta automaticamente di attivare il virtual environment Python se presente in `venv/`.

Se il tuo virtual environment ha un nome diverso, modifica questa riga nello script:
```powershell
'cd $PROJECT_PATH && source venv/bin/activate 2>/dev/null || true && python manage.py runserver'
```

### Accesso ai Server da Windows

I server sono configurati per essere accessibili da Windows:
- Django: `http://localhost:8000`
- Frontend: `http://localhost:5173`

L'opzione `0.0.0.0` negli script fa sì che i server siano accessibili dall'host Windows.

## 📷 Gestione Servizio Scanner

Il servizio scanner gestisce le scansioni documenti con scanner Brother e Kyocera.

### Avvio Rapido Scanner

```batch
Quick_Start_Scanner.bat   # Avvia scanner service su porta 8765
```

### Funzionalità Scanner

- ✅ Supporto scanner Brother ADS-2400N (192.168.1.7)
- ✅ Supporto scanner Kyocera ECOSYS M2540dn (192.168.1.151)
- ✅ Scansione duplex automatica
- ✅ PDF/A, 300 DPI, grayscale
- ✅ Ottimizzazione B/N con compressione
- ✅ Health check endpoint: `http://localhost:8765/health`

### Dal Menu Interattivo

```
D. Avvia Scanner    - Avvia servizio scanner
E. Ferma Scanner    - Arresta servizio scanner
F. Riavvia Scanner  - Riavvia servizio scanner
```

## 🤖 Gestione MyGest Agent (Auto-Detection)

Il MyGest Agent monitora le cartelle e elimina automaticamente i file dopo l'upload su MyGest.

### Prima Configurazione

1. **Copia template configurazione**:
   ```bash
   wsl cp /home/sandro/mygest/config/mygest-agent.conf.example ~/.mygest-agent.conf
   ```

2. **Modifica configurazione** (inserisci token API):
   ```bash
   wsl nano ~/.mygest-agent.conf
   ```

3. **Verifica configurazione**:
   ```batch
   wsl cd /home/sandro/mygest && source venv/bin/activate && python scripts/mygest_agent_config.py --show-config
   ```

### Avvio Rapido Agent

```batch
Quick_Start_Agent.bat     # Avvia agent con auto-detection
Quick_Stop_Agent.bat      # Arresta agent con statistiche
```

### Dal Menu Interattivo

```
G. Avvia Agent          - Avvia agent auto-detection
H. Ferma Agent          - Arresta agent (con statistiche)
I. Riavvia Agent        - Riavvia agent
J. Statistiche Agent    - Mostra statistiche e log dettagliati
```

### Funzionalità Agent

- ✅ **Auto-Detection**: Trova automaticamente file per nome+dimensione (95%+ accuracy)
- ✅ **Real-time**: Monitora cartelle con watchdog (no polling overhead)
- ✅ **Cache 24h**: Mantiene traccia file recenti
- ✅ **Sicurezza**: Path protetti (impossibile eliminare file sistema)
- ✅ **Statistiche**: Report dettagliato operazioni
- ✅ **Log**: `~/.mygest-agent.log` con rotazione

### Documentazione Agent

- `AGENT_AUTODETECTION_READY.md` - Quick start
- `GUIDA_CONFIGURAZIONE_CARTELLE_AGENT.md` - Configurazione completa
- `GESTIONE_FILE_DOCUMENTI.md` - Workflow file management

## 🎨 Personalizzazione Icona (Opzionale)

Per aggiungere un'icona personalizzata all'eseguibile:

1. Crea o scarica un file `.ico` (dimensione consigliata: 256x256)
2. Salvalo come `icon.ico` nella cartella `windows_manager`
3. Riesegui `Build_Executable.ps1`

## 📦 Creazione Installer (Avanzato)

Se vuoi creare un installer completo per distribuire il tool:

### Con Inno Setup

1. Installa [Inno Setup](https://jrsoftware.org/isinfo.php)
2. Crea un file `setup.iss`:

```iss
[Setup]
AppName=WSL Server Manager
AppVersion=1.0
DefaultDirName={pf}\WSL Server Manager
DefaultGroupName=WSL Server Manager
OutputDir=.
OutputBaseFilename=WSL_Server_Manager_Setup

[Files]
Source: "WSL_Server_Manager.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\WSL Server Manager"; Filename: "{app}\WSL_Server_Manager.exe"
Name: "{userdesktop}\WSL Server Manager"; Filename: "{app}\WSL_Server_Manager.exe"
```

3. Compila con Inno Setup

## 🔄 Aggiornamenti

Per aggiornare lo script:

1. Modifica `WSL_Server_Manager.ps1`
2. Ricrea l'eseguibile con `Build_Executable.ps1`
3. Sostituisci il vecchio eseguibile

## 🤝 Supporto

Per problemi o domande:
- Verifica la configurazione WSL
- Controlla i log dei server nei terminali aperti
- Verifica le porte non siano già occupate

## 📄 Licenza

Questo strumento è parte del progetto MyGest.

---

**Versione:** 1.0  
**Data:** Dicembre 2024  
**Compatibilità:** Windows 11 + WSL2
