# Guida Configurazione SSH per Accesso Remoto

## 📋 Panoramica

Questa guida spiega come configurare il server SSH su WSL per consentire l'accesso remoto al sistema MyGest da altri dispositivi nella rete locale o dall'esterno.

## 🔧 Prerequisiti

### 1. Installazione SSH Server su WSL

Apri un terminale WSL e installa il server SSH:

```bash
# Aggiorna i repository
sudo apt update

# Installa OpenSSH Server
sudo apt install openssh-server -y
```

### 2. Configurazione di Base

Modifica il file di configurazione SSH:

```bash
sudo nano /etc/ssh/sshd_config
```

Assicurati che queste opzioni siano impostate:

```
Port 22
PermitRootLogin no
PasswordAuthentication yes  # Per ora, poi passeremo a chiavi SSH
PubkeyAuthentication yes
```

Salva e chiudi il file (CTRL+X, poi Y, poi INVIO).

### 3. Avvio Automatico SSH

Per far partire SSH automaticamente quando avvii WSL:

#### Metodo 1: Con systemd (Ubuntu 22.04+)

```bash
# Abilita systemd in WSL (se non già fatto)
echo -e "[boot]\nsystemd=true" | sudo tee -a /etc/wsl.conf

# Riavvia WSL da PowerShell (Windows)
wsl --shutdown

# Riapri WSL e abilita SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

#### Metodo 2: Senza systemd (metodo tradizionale)

Crea uno script di avvio:

```bash
# Crea lo script
sudo nano /etc/init.d/ssh-autostart

# Aggiungi questo contenuto:
#!/bin/bash
sudo service ssh start
```

Rendilo eseguibile:

```bash
sudo chmod +x /etc/init.d/ssh-autostart
```

Aggiungi al file `.bashrc` o `.profile`:

```bash
echo "sudo /etc/init.d/ssh-autostart" >> ~/.bashrc
```

### 4. Configurazione Firewall Windows

Per consentire connessioni SSH dall'esterno:

#### Apri PowerShell come Amministratore:

```powershell
# Crea regola firewall per SSH
New-NetFirewallRule -Name "WSL SSH" -DisplayName "WSL SSH Server" -Direction Inbound -LocalPort 22 -Protocol TCP -Action Allow

# Verifica la regola
Get-NetFirewallRule -Name "WSL SSH"
```

### 5. Port Forwarding (per accesso esterno a WSL)

WSL usa NAT, quindi dobbiamo configurare il port forwarding:

#### Script PowerShell (da eseguire come Amministratore):

```powershell
# Ottieni l'IP di WSL
$wslIp = (wsl hostname -I).Trim()

# Aggiungi port forwarding dalla porta 22 di Windows a WSL
netsh interface portproxy add v4tov4 listenport=22 listenaddress=0.0.0.0 connectport=22 connectaddress=$wslIp

# Verifica la configurazione
netsh interface portproxy show all
```

**IMPORTANTE**: Questo comando va rieseguito ogni volta che riavvii il PC perché l'IP di WSL potrebbe cambiare.

#### Script Automatico per Port Forwarding

Salva questo script come `Setup_SSH_PortForward.ps1` nella cartella `windows_manager`:

```powershell
# Setup SSH Port Forwarding per WSL
$wslIp = (wsl -d Ubuntu-22.04 hostname -I).Trim().Split()[0]
Write-Host "WSL IP: $wslIp"

# Rimuovi vecchi port forwarding
netsh interface portproxy delete v4tov4 listenport=22 listenaddress=0.0.0.0

# Aggiungi nuovo port forwarding
netsh interface portproxy add v4tov4 listenport=22 listenaddress=0.0.0.0 connectport=22 connectaddress=$wslIp

# Verifica
Write-Host "`nPort Forwarding configurato:"
netsh interface portproxy show all

Write-Host "`nPer connetterti da rete locale usa:"
Write-Host "ssh utente@$((Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" | Select-Object -First 1).IPAddress)"
```

Eseguilo da PowerShell come Amministratore:

```powershell
.\Setup_SSH_PortForward.ps1
```

## 🌐 Accesso da Rete Locale

### Trova l'IP del PC Windows

```powershell
# Da PowerShell
ipconfig | findstr IPv4
```

Oppure:

```powershell
Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" | Select-Object IPAddress
```

### Connettiti da altro PC nella LAN

```bash
ssh tuo_utente_wsl@IP_PC_WINDOWS
```

Esempio:
```bash
ssh sandro@192.168.1.100
```

## 🔐 Sicurezza: Autenticazione con Chiave SSH

### 1. Genera chiave SSH sul client

Sul PC da cui vuoi connetterti:

```bash
# Genera coppia di chiavi
ssh-keygen -t ed25519 -C "tuo_email@example.com"

# Premi INVIO per accettare il percorso predefinito
# Inserisci una password (consigliato)
```

### 2. Copia la chiave pubblica sul server WSL

```bash
# Metodo 1: Con ssh-copy-id
ssh-copy-id tuo_utente@IP_PC_WINDOWS

# Metodo 2: Manualmente
cat ~/.ssh/id_ed25519.pub | ssh tuo_utente@IP_PC_WINDOWS "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

### 3. Disabilita autenticazione con password

Sul server WSL:

```bash
sudo nano /etc/ssh/sshd_config
```

Modifica:
```
PasswordAuthentication no
```

Riavvia SSH:
```bash
sudo systemctl restart ssh
# oppure
sudo service ssh restart
```

## 🔄 Gestione SSH con Windows Manager

### Uso del Manager GUI

1. Apri `Start_GUI.bat`
2. Troverai la sezione "SSH Server" con:
   - **▶ Avvia**: Avvia il server SSH
   - **⏹ Ferma**: Arresta il server SSH
   - **🔄 Riavvia**: Riavvia il server SSH
   - **Stato**: Indicatore in tempo reale (● ATTIVO / ○ FERMO)

### Uso del Manager da Linea di Comando

Non implementato direttamente, ma puoi usare i file batch:

- `Quick_Start_SSH.bat`: Avvia SSH
- `Quick_Stop_SSH.bat`: Ferma SSH
- `Quick_Restart_SSH.bat`: Riavvia SSH

### Menu Interattivo

Esegui `Start_Manager.bat` e usa:

- **A**: Avvia SSH
- **B**: Ferma SSH
- **C**: Riavvia SSH

## 📊 Monitoraggio

### Verifica stato SSH

```bash
# Da WSL
sudo systemctl status ssh
# oppure
sudo service ssh status
```

### Verifica connessioni attive

```bash
# Vedi chi è connesso
who

# Vedi connessioni SSH
sudo netstat -tnpa | grep 'ESTABLISHED.*sshd'
```

### Log SSH

```bash
# Visualizza log in tempo reale
sudo tail -f /var/log/auth.log
```

## 🚨 Troubleshooting

### SSH non si avvia

```bash
# Verifica errori
sudo systemctl status ssh
# oppure
sudo service ssh status

# Verifica configurazione
sudo sshd -t
```

### Impossibile connettersi dall'esterno

1. **Verifica Firewall Windows**:
   ```powershell
   Get-NetFirewallRule -Name "WSL SSH"
   ```

2. **Verifica Port Forwarding**:
   ```powershell
   netsh interface portproxy show all
   ```

3. **Testa connessione locale**:
   ```bash
   ssh localhost
   ```

### WSL non ha privilegi sudo senza password

Per eseguire comandi sudo senza password (necessario per gestione automatica):

```bash
# Apri sudoers
sudo visudo

# Aggiungi questa riga alla fine (sostituisci 'tuo_utente' con il tuo username):
tuo_utente ALL=(ALL) NOPASSWD: /usr/sbin/service ssh *, /bin/systemctl * ssh
```

Questo consente di avviare/fermare SSH senza password ma mantiene la sicurezza per altri comandi.

## 🌍 Accesso da Internet (Opzionale)

### Prerequisiti

- Router con possibilità di port forwarding
- IP pubblico (o servizio Dynamic DNS se hai IP dinamico)

### Configurazione Router

1. Accedi al pannello del router (di solito http://192.168.1.1)
2. Trova la sezione "Port Forwarding" o "Virtual Server"
3. Crea regola:
   - **Porta Esterna**: 22 (o altra porta custom per sicurezza, es. 2222)
   - **Porta Interna**: 22
   - **IP Locale**: IP del tuo PC Windows nella LAN
   - **Protocollo**: TCP

### Dynamic DNS (se IP pubblico dinamico)

Usa servizi come:
- No-IP (https://www.noip.com)
- DuckDNS (https://www.duckdns.org)
- DynDNS

Configurali per aggiornare automaticamente l'hostname quando l'IP cambia.

### Connessione da Internet

```bash
# Con IP pubblico
ssh utente@TUO_IP_PUBBLICO

# Con Dynamic DNS
ssh utente@tuodominio.ddns.net
```

### ⚠️ Avviso Sicurezza

**NON esporre SSH direttamente su Internet** senza:
1. ✅ Autenticazione solo con chiave SSH (no password)
2. ✅ Porta custom (non 22)
3. ✅ Fail2ban installato
4. ✅ UFW (Uncomplicated Firewall) configurato
5. ✅ Aggiornamenti di sicurezza automatici

## 📝 Best Practices

1. **Usa chiavi SSH invece di password**
2. **Cambia porta SSH da 22 a un'altra (es. 2222)**
3. **Installa fail2ban per bloccare tentativi di accesso**:
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```
4. **Limita accesso a utenti specifici** nel file `sshd_config`:
   ```
   AllowUsers tuo_utente
   ```
5. **Disabilita accesso root**:
   ```
   PermitRootLogin no
   ```

## 📚 Risorse Utili

- [OpenSSH Official Documentation](https://www.openssh.com/manual.html)
- [SSH Hardening Guide](https://www.ssh.com/academy/ssh/sshd_config)
- [WSL Networking](https://learn.microsoft.com/en-us/windows/wsl/networking)

---

**Versione**: 1.0  
**Data**: Febbraio 2026  
**Autore**: Sandro Chimenti
