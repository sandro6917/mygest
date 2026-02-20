# Feature: Gestione Server SSH - Windows Manager

## 📋 Sommario

Aggiunta la funzionalità completa di gestione del server SSH al Windows Manager, consentendo l'avvio, l'arresto e il riavvio del server SSH per consentire il collegamento remoto al sistema MyGest da altri dispositivi.

## ✨ Nuove Funzionalità

### 1. Gestione SSH nel Manager Console (`WSL_Server_Manager.ps1`)

**Funzioni Aggiunte**:
- `Get-SSHStatus()`: Verifica se SSH è attivo o fermo
- `Start-SSHServer()`: Avvia il server SSH su WSL
- `Stop-SSHServer()`: Arresta il server SSH su WSL
- `Restart-SSHServer()`: Riavvia il server SSH su WSL

**Menu Aggiornato**:
```
=== Server SSH (Accesso Remoto) ===
A. Avvia SSH
B. Ferma SSH
C. Riavvia SSH
```

**Monitoraggio Stato**:
Lo stato SSH è ora incluso nella visualizzazione dello stato dei servizi:
```
SSH Server:       IN ESECUZIONE
                  ssh utente@localhost (porta 22)
```

### 2. Gestione SSH nella GUI (`WSL_Server_Manager_GUI.ps1`)

**Sezione Aggiunta**: Pannello dedicato SSH Server con:
- Indicatore di stato in tempo reale (● ATTIVO / ○ FERMO)
- Pulsante "▶ Avvia" - Avvia il server SSH
- Pulsante "⏹ Ferma" - Arresta il server SSH
- Pulsante "🔄 Riavvia" - Riavvia il server SSH
- Auto-aggiornamento stato ogni 5 secondi

**Dimensioni Finestra**: Aumentate da 450px a 600px in altezza per ospitare la nuova sezione.

### 3. Script Batch per Gestione Rapida SSH

Creati 3 nuovi file batch per operazioni rapide:

#### `Quick_Start_SSH.bat`
Avvia rapidamente il server SSH senza aprire il manager completo.

#### `Quick_Stop_SSH.bat`
Arresta rapidamente il server SSH.

#### `Quick_Restart_SSH.bat`
Riavvia rapidamente il server SSH.

### 4. Setup Automatico Port Forwarding

#### `Setup_SSH_PortForward.ps1`
Script PowerShell completo che:
- Rileva automaticamente l'IP di WSL
- Configura il port forwarding da Windows a WSL per la porta 22
- Crea/verifica regola Firewall Windows
- Mostra informazioni di connessione (IP locale)
- **Opzione per Task Scheduler**: Avvio automatico al boot di Windows

**Uso**:
```powershell
# Da PowerShell come Amministratore
.\Setup_SSH_PortForward.ps1
```

**Funzionalità**:
- ✅ Rimozione automatica vecchie configurazioni
- ✅ Configurazione nuovo port forwarding
- ✅ Verifica/Creazione regola Firewall
- ✅ Visualizzazione IP per connessione remota
- ✅ Opzione Task Scheduler per avvio automatico

### 5. Documentazione Completa SSH

#### `SSH_SETUP_GUIDE.md`
Guida completa che copre:

**Configurazione Base**:
- Installazione OpenSSH Server su WSL
- Configurazione `/etc/ssh/sshd_config`
- Avvio automatico SSH (con systemd e metodo tradizionale)
- Configurazione Firewall Windows
- Port Forwarding WSL ↔ Windows

**Accesso Rete Locale**:
- Come trovare l'IP del PC Windows
- Connessione da altri PC nella LAN
- Test connessione

**Sicurezza**:
- Generazione chiavi SSH (ed25519)
- Copia chiave pubblica sul server
- Disabilitazione autenticazione password
- Configurazione sudo senza password per comandi SSH

**Accesso Remoto da Internet** (Opzionale):
- Configurazione port forwarding su router
- Dynamic DNS per IP pubblici dinamici
- Best practices sicurezza

**Monitoraggio e Troubleshooting**:
- Comandi verifica stato SSH
- Visualizzazione connessioni attive
- Analisi log
- Risoluzione problemi comuni

**Best Practices**:
- Uso chiavi SSH invece di password
- Cambio porta SSH
- Installazione fail2ban
- Limitazione accesso utenti
- Hardening SSH

## 🔧 Modifiche Tecniche

### WSL_Server_Manager.ps1

**Configurazione**:
```powershell
$SSH_PORT = 22  # Porta SSH standard
```

**Funzione Get-SSHStatus**:
```powershell
function Get-SSHStatus {
    $result = wsl -d $WSL_DISTRO bash -c "systemctl is-active ssh 2>/dev/null || service ssh status 2>/dev/null | grep -q 'running' && echo 'active' || echo 'inactive'"
    return ($result -eq "active")
}
```
- Compatibile sia con systemd che init.d
- Ritorna boolean per facile integrazione

**Funzioni Start/Stop/Restart SSH**:
- Usano `sudo systemctl` o `sudo service` in fallback
- Verificano lo stato prima/dopo l'operazione
- Forniscono feedback colorato all'utente
- Gestiscono errori con messaggi appropriati

### WSL_Server_Manager_GUI.ps1

**Nuove Variabili**:
```powershell
$labelSSH, $labelSSHStatus
$btnStartSSH, $btnStopSSH, $btnRestartSSH
```

**Update-Status** aggiornato:
Ora gestisce anche lo stato SSH con:
- Aggiornamento label stato
- Abilitazione/disabilitazione pulsanti appropriati
- Cambio colori indicatore (Verde/Rosso)

**Layout**:
- Sezione SSH posizionata dopo Frontend, prima dei pulsanti globali
- Separatore visivo tra sezioni
- Consistenza stilistica con altre sezioni

## 📝 File Modificati

1. **WSL_Server_Manager.ps1**
   - Aggiunta configurazione `$SSH_PORT`
   - Aggiunta funzione `Get-SSHStatus()`
   - Aggiunta funzione `Start-SSHServer()`
   - Aggiunta funzione `Stop-SSHServer()`
   - Aggiunta funzione `Restart-SSHServer()`
   - Aggiornato `Show-ServerStatus()` per includere SSH
   - Aggiornato menu `Show-Menu()` con opzioni A/B/C per SSH

2. **WSL_Server_Manager_GUI.ps1**
   - Aggiunta configurazione `$SSH_PORT`
   - Aggiunta funzione `Get-SSHStatus()`
   - Aggiunta funzione `Start-SSH()`
   - Aggiunta funzione `Stop-SSH()`
   - Aggiunta funzione `Restart-SSH()`
   - Aggiornato `Update-Status()` per gestire SSH
   - Aumentata dimensione finestra (600px altezza)
   - Aggiunta sezione UI completa per SSH

3. **README.md**
   - Aggiornata panoramica con menzione SSH
   - Aggiornata lista funzionalità
   - Aggiornata struttura file con nuovi script
   - Aggiornato menu interattivo con opzioni SSH
   - Aggiunta sezione "Configurazione SSH per Accesso Remoto"
   - Aggiunti riferimenti a SSH_SETUP_GUIDE.md

## 📦 File Creati

1. **Quick_Start_SSH.bat** - Avvio rapido SSH
2. **Quick_Stop_SSH.bat** - Arresto rapido SSH
3. **Quick_Restart_SSH.bat** - Riavvio rapido SSH
4. **Setup_SSH_PortForward.ps1** - Configurazione automatica port forwarding
5. **SSH_SETUP_GUIDE.md** - Guida completa configurazione SSH
6. **FEATURE_SSH_MANAGEMENT.md** - Questo documento

## 🚀 Come Usare

### Metodo 1: Interfaccia Grafica

```batch
cd \\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager
Start_GUI.bat
```

Nella GUI:
- Vai alla sezione "SSH Server (Porta 22)"
- Clicca "▶ Avvia" per avviare SSH
- Clicca "⏹ Ferma" per arrestare SSH
- Clicca "🔄 Riavvia" per riavviare SSH
- Osserva lo stato in tempo reale (● ATTIVO / ○ FERMO)

### Metodo 2: Menu Interattivo

```batch
cd \\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager
Start_Manager.bat
```

Nel menu:
- Premi `A` per avviare SSH
- Premi `B` per fermare SSH
- Premi `C` per riavviare SSH
- Premi `S` per vedere lo stato di tutti i servizi

### Metodo 3: Script Batch Rapidi

```batch
# Avvia SSH
Quick_Start_SSH.bat

# Ferma SSH
Quick_Stop_SSH.bat

# Riavvia SSH
Quick_Restart_SSH.bat
```

### Setup Iniziale (Una tantum)

1. **Installa SSH su WSL**:
   ```bash
   sudo apt update
   sudo apt install openssh-server -y
   ```

2. **Configura Port Forwarding** (da PowerShell come Amministratore):
   ```powershell
   cd \\wsl$\Ubuntu-22.04\home\sandro\mygest\windows_manager
   .\Setup_SSH_PortForward.ps1
   ```
   
3. **Configura sudo senza password per SSH** (opzionale ma consigliato):
   ```bash
   sudo visudo
   # Aggiungi:
   tuo_utente ALL=(ALL) NOPASSWD: /usr/sbin/service ssh *, /bin/systemctl * ssh
   ```

4. **Avvia SSH** usando uno dei metodi sopra

5. **Testa la connessione**:
   ```bash
   ssh localhost
   # oppure da altro PC:
   ssh tuo_utente@IP_PC_WINDOWS
   ```

## 🔒 Sicurezza

### Requisiti Minimi

Prima di esporre SSH su rete locale/Internet:

1. ✅ **Autenticazione con chiavi SSH** (no password)
2. ✅ **Porta custom** (non usare 22 se esposto su Internet)
3. ✅ **Firewall configurato** correttamente
4. ✅ **fail2ban** installato e attivo
5. ✅ **Aggiornamenti** di sicurezza automatici

### Comandi Utili

```bash
# Verifica stato SSH
sudo systemctl status ssh

# Vedi chi è connesso
who

# Vedi connessioni SSH attive
sudo netstat -tnpa | grep 'ESTABLISHED.*sshd'

# Log SSH in tempo reale
sudo tail -f /var/log/auth.log
```

## 🎯 Benefici

1. **Accesso Remoto**: Possibilità di gestire MyGest da qualsiasi luogo
2. **Manutenzione**: Amministrazione sistema senza accesso fisico al PC
3. **Automazione**: Possibilità di script remoti e deploy
4. **Sicurezza**: Controllo granulare su chi può accedere
5. **Integrazione**: Facile integrazione con CI/CD e strumenti DevOps

## 📊 Compatibilità

- ✅ Windows 11
- ✅ Windows 10 (con WSL2)
- ✅ Ubuntu 22.04 LTS (WSL)
- ✅ Ubuntu 20.04 LTS (WSL)
- ✅ Altre distribuzioni Linux su WSL (con adattamenti)

## 🐛 Troubleshooting

### SSH non si avvia

**Problema**: SSH non parte quando clicchi "Avvia"

**Soluzione**:
```bash
# Verifica installazione
sudo apt install openssh-server -y

# Verifica configurazione
sudo sshd -t

# Verifica log
sudo tail -f /var/log/auth.log
```

### Port Forwarding non funziona

**Problema**: Non riesci a connetterti da rete locale

**Soluzione**:
```powershell
# Verifica port forwarding
netsh interface portproxy show all

# Verifica firewall
Get-NetFirewallRule -Name "WSL SSH"

# Ri-esegui setup
.\Setup_SSH_PortForward.ps1
```

### Richiesta password sudo

**Problema**: Il manager chiede password sudo

**Soluzione**:
```bash
sudo visudo
# Aggiungi alla fine:
tuo_utente ALL=(ALL) NOPASSWD: /usr/sbin/service ssh *, /bin/systemctl * ssh
```

## 📚 Risorse

- [SSH_SETUP_GUIDE.md](SSH_SETUP_GUIDE.md) - Guida completa configurazione
- [README.md](README.md) - Guida generale Windows Manager
- [OpenSSH Documentation](https://www.openssh.com/manual.html)
- [WSL Networking](https://learn.microsoft.com/en-us/windows/wsl/networking)

## 🎉 Conclusioni

Il Windows Manager ora offre una gestione completa di tutti i servizi necessari per MyGest:
- ✅ Django Backend
- ✅ React Frontend  
- ✅ SSH Server (nuovo!)

Tutto controllabile con:
- 🖼️ Interfaccia grafica intuitiva
- 📋 Menu interattivo console
- ⚡ Script batch rapidi
- 🔧 Automazione completa

---

**Versione**: 1.0  
**Data**: 15 Febbraio 2026  
**Autore**: GitHub Copilot + Sandro Chimenti
