# Changelog - Windows Manager

## [1.2.0] - 2026-02-15

### Aggiunto
- **Chiusura Automatica Finestre**: Le finestre PowerShell dei server vengono chiuse automaticamente quando il server viene arrestato
  - Variabili globali `$Global:DjangoWindowPID` e `$Global:FrontendWindowPID` per tracciare PID finestre
  - Parametro `-PassThru` in `Start-Process` per ottenere PID della finestra
  - Chiusura automatica finestra in tutte le funzioni `Stop-*`
  
### Modificato
- **WSL_Server_Manager.ps1**:
  - `Start-DjangoServer()` ora salva PID finestra PowerShell
  - `Start-FrontendServer()` ora salva PID finestra PowerShell
  - `Stop-DjangoServer()` chiude automaticamente la finestra PowerShell
  - `Stop-FrontendServer()` chiude automaticamente la finestra PowerShell
  
- **WSL_Server_Manager_GUI.ps1**:
  - `Start-Django()` ora salva PID finestra PowerShell
  - `Start-Frontend()` ora salva PID finestra PowerShell
  - `Stop-Django()` chiude automaticamente la finestra PowerShell
  - `Stop-Frontend()` chiude automaticamente la finestra PowerShell

### Migliorato
- **User Experience**: Solo finestre di server attivi rimangono aperte
- **Gestione Risorse**: Finestre chiuse liberano memoria
- **Organizzazione**: Desktop più pulito con meno finestre aperte

### Documentazione
- **FEATURE_AUTO_CLOSE_WINDOWS.md** - Documentazione completa della feature

---

## [1.1.0] - 2026-02-15

### Aggiunto
- **Gestione Server SSH**: Funzionalità completa per avviare, arrestare e riavviare il server SSH
  - Funzione `Get-SSHStatus()` per verificare stato SSH
  - Funzione `Start-SSHServer()` per avviare SSH
  - Funzione `Stop-SSHServer()` per arrestare SSH
  - Funzione `Restart-SSHServer()` per riavviare SSH
  
- **Menu Interattivo**: Nuove opzioni SSH nel menu console
  - Opzione A: Avvia SSH
  - Opzione B: Ferma SSH
  - Opzione C: Riavvia SSH
  
- **Interfaccia Grafica**: Sezione dedicata SSH nella GUI
  - Pannello SSH Server con indicatore stato in tempo reale
  - Pulsanti Avvia, Ferma, Riavvia per SSH
  - Auto-refresh stato ogni 5 secondi
  
- **Script Batch Rapidi**:
  - `Quick_Start_SSH.bat` - Avvio rapido SSH
  - `Quick_Stop_SSH.bat` - Arresto rapido SSH
  - `Quick_Restart_SSH.bat` - Riavvio rapido SSH
  
- **Setup Port Forwarding**:
  - `Setup_SSH_PortForward.ps1` - Script automatico per configurazione port forwarding Windows → WSL
  - Rilevamento automatico IP WSL
  - Configurazione automatica regole Firewall
  - Opzione Task Scheduler per avvio automatico
  
- **Documentazione**:
  - `SSH_SETUP_GUIDE.md` - Guida completa configurazione SSH (installazione, sicurezza, port forwarding, troubleshooting)
  - `FEATURE_SSH_MANAGEMENT.md` - Documentazione tecnica della feature
  - `CHANGELOG.md` - Questo file

### Modificato
- **WSL_Server_Manager.ps1**:
  - Aggiunta configurazione `$SSH_PORT = 22`
  - Aggiornato `Show-ServerStatus()` per includere stato SSH
  - Aggiornato `Show-Menu()` con opzioni SSH
  
- **WSL_Server_Manager_GUI.ps1**:
  - Aggiunta configurazione `$SSH_PORT = 22`
  - Aggiornato `Update-Status()` per gestire stato SSH
  - Aumentata altezza finestra da 450px a 600px
  
- **README.md**:
  - Aggiornata panoramica con funzionalità SSH
  - Aggiornata struttura file
  - Aggiunto menu completo con opzioni SSH
  - Aggiunta sezione configurazione SSH
  - Aggiunti riferimenti a guide SSH

### Note Tecniche
- Compatibilità con systemd (Ubuntu 22.04+) e init.d (versioni precedenti)
- Supporto automatico fallback tra `systemctl` e `service`
- Gestione errori con messaggi informativi
- Integrazione completa con monitoraggio stato esistente

---

## [1.0.0] - 2026-01-XX

### Aggiunto
- **Gestione Server Django**: Avvio, arresto, riavvio del backend Django
- **Gestione Server Frontend**: Avvio, arresto, riavvio del server Vite (React)
- **Menu Interattivo Console**: Interfaccia testuale per gestione servizi
- **Interfaccia Grafica**: GUI Windows Forms per controllo visuale
- **Script Batch Rapidi**:
  - `Quick_Start_All.bat`
  - `Quick_Stop_All.bat`
  - `Quick_Restart_All.bat`
- **Documentazione**: README.md completo con guide di utilizzo
- **Build Script**: `Build_Executable.ps1` per creare eseguibili standalone

### Caratteristiche Iniziali
- Monitoraggio stato servizi in tempo reale
- Apertura terminali separati per ogni server
- Supporto comandi da linea di comando
- Configurazione personalizzabile
- Compatibilità WSL2 su Windows 10/11
