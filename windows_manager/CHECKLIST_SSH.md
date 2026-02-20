# ✅ Checklist Verifica Funzionalità SSH

## 📋 Checklist File Modificati/Creati

### File Modificati
- [x] `WSL_Server_Manager.ps1` - Aggiunta gestione SSH
- [x] `WSL_Server_Manager_GUI.ps1` - Aggiunta sezione SSH nella GUI
- [x] `README.md` - Aggiornato con info SSH

### File Creati
- [x] `Quick_Start_SSH.bat` - Script batch avvio SSH
- [x] `Quick_Stop_SSH.bat` - Script batch arresto SSH
- [x] `Quick_Restart_SSH.bat` - Script batch riavvio SSH
- [x] `Setup_SSH_PortForward.ps1` - Setup automatico port forwarding
- [x] `SSH_SETUP_GUIDE.md` - Guida completa configurazione SSH
- [x] `FEATURE_SSH_MANAGEMENT.md` - Documentazione tecnica
- [x] `SSH_QUICK_START.md` - Guida rapida per utente
- [x] `CHANGELOG.md` - Registro modifiche
- [x] `CHECKLIST_SSH.md` - Questo file

## 🧪 Test da Eseguire

### Test 1: Menu Interattivo Console

```batch
Start_Manager.bat
```

Verifica che il menu mostri:
- [ ] Opzione "A. Avvia SSH"
- [ ] Opzione "B. Ferma SSH"
- [ ] Opzione "C. Riavvia SSH"
- [ ] Stato SSH quando premi "S"

**Test A - Avvia SSH**:
1. [ ] Premi "A"
2. [ ] Verifica messaggio "Avvio del server SSH..."
3. [ ] Verifica stato diventa "IN ESECUZIONE"

**Test B - Ferma SSH**:
1. [ ] Premi "B"
2. [ ] Verifica messaggio "Arresto del server SSH..."
3. [ ] Verifica stato diventa "FERMO"

**Test C - Riavvia SSH**:
1. [ ] Premi "C"
2. [ ] Verifica messaggio "Riavvio del server SSH..."
3. [ ] Verifica stato rimane "IN ESECUZIONE"

### Test 2: Interfaccia Grafica

```batch
Start_GUI.bat
```

Verifica GUI:
- [ ] Sezione "SSH Server (Porta 22)" presente
- [ ] Indicatore stato visibile (● ATTIVO / ○ FERMO)
- [ ] Pulsante "▶ Avvia" presente
- [ ] Pulsante "⏹ Ferma" presente
- [ ] Pulsante "🔄 Riavvia" presente

**Test Pulsanti**:
1. [ ] Click "▶ Avvia" → Stato cambia in "● ATTIVO" (verde)
2. [ ] Pulsante "▶ Avvia" si disabilita
3. [ ] Pulsante "⏹ Ferma" si abilita
4. [ ] Click "⏹ Ferma" → Stato cambia in "○ FERMO" (rosso)
5. [ ] Click "🔄 Riavvia" → SSH si riavvia correttamente

**Test Auto-refresh**:
1. [ ] Avvia SSH da terminale WSL: `sudo service ssh start`
2. [ ] Verifica che GUI rilevi il cambio stato entro 5 secondi
3. [ ] Ferma SSH da terminale WSL: `sudo service ssh stop`
4. [ ] Verifica che GUI rilevi il cambio stato entro 5 secondi

### Test 3: Script Batch Rapidi

**Test Quick_Start_SSH.bat**:
1. [ ] Doppio click sul file
2. [ ] Verifica output "Avvio del server SSH..."
3. [ ] Verifica output finale "SSH Server ATTIVO"
4. [ ] Chiudi finestra

**Test Quick_Stop_SSH.bat**:
1. [ ] Doppio click sul file
2. [ ] Verifica output "Arresto del server SSH..."
3. [ ] Verifica output finale "SSH Server FERMO"
4. [ ] Chiudi finestra

**Test Quick_Restart_SSH.bat**:
1. [ ] Doppio click sul file
2. [ ] Verifica output "Riavvio del server SSH..."
3. [ ] Verifica output finale "SSH Server ATTIVO"
4. [ ] Chiudi finestra

### Test 4: Setup Port Forwarding

**Prerequisito**: Esegui da PowerShell come Amministratore

```powershell
.\Setup_SSH_PortForward.ps1
```

Verifica:
- [ ] Script rileva IP di WSL correttamente
- [ ] Rimuove vecchie configurazioni port forwarding
- [ ] Crea nuovo port forwarding porta 22
- [ ] Verifica/crea regola Firewall "WSL SSH"
- [ ] Mostra configurazione port forwarding attiva
- [ ] Mostra IP Windows per connessione remota
- [ ] Chiede se aggiungere a Task Scheduler

**Se si sceglie Task Scheduler**:
- [ ] Task "WSL SSH Port Forwarding" creato correttamente
- [ ] Verifica task in Task Scheduler Windows

### Test 5: Connessione SSH

**Test Connessione Locale (Windows → WSL)**:

```bash
ssh localhost
# oppure
ssh sandro@localhost
```

Verifica:
- [ ] Connessione riuscita
- [ ] Prompt WSL visualizzato
- [ ] Comando `whoami` ritorna username corretto
- [ ] Comando `hostname` ritorna hostname WSL
- [ ] Disconnessione con `exit` funziona

**Test Connessione da Rete Locale** (altro PC/smartphone):

1. [ ] Trova IP del PC Windows: `ipconfig`
2. [ ] Da altro dispositivo: `ssh sandro@IP_WINDOWS`
3. [ ] Verifica connessione riuscita
4. [ ] Verifica prompt WSL
5. [ ] Disconnessione funziona

### Test 6: Verifica Stato Manuale

**Da WSL**:

```bash
# Verifica stato SSH
sudo systemctl status ssh
# oppure
sudo service ssh status
```

Verifica:
- [ ] Stato riportato correttamente
- [ ] PID presente quando attivo
- [ ] Porta 22 in ascolto: `sudo netstat -tlnp | grep :22`

**Da Windows Manager**:
1. [ ] Menu: Premi "S" → Stato SSH visualizzato correttamente
2. [ ] GUI: Stato aggiornato automaticamente

### Test 7: Compatibilità systemd vs service

**Test systemd (Ubuntu 22.04+)**:

```bash
# Verifica systemd attivo
systemctl --version
```

Se systemd presente:
- [ ] Avvio SSH usa `systemctl start ssh`
- [ ] Arresto SSH usa `systemctl stop ssh`
- [ ] Riavvio SSH usa `systemctl restart ssh`
- [ ] Stato SSH usa `systemctl is-active ssh`

**Test service (Fallback)**:

Se systemd non presente o disabilitato:
- [ ] Avvio SSH usa `service ssh start`
- [ ] Arresto SSH usa `service ssh stop`
- [ ] Riavvio SSH usa `service ssh restart`
- [ ] Stato SSH usa `service ssh status`

## 📄 Test Documentazione

### README.md
- [ ] Panoramica aggiornata con SSH
- [ ] Funzionalità SSH elencate
- [ ] Struttura file include nuovi script SSH
- [ ] Menu mostra opzioni A/B/C
- [ ] Sezione "Configurazione SSH" presente
- [ ] Link a SSH_SETUP_GUIDE.md funzionante

### SSH_SETUP_GUIDE.md
- [ ] File esiste e leggibile
- [ ] Sezioni complete: Installazione, Configurazione, Sicurezza
- [ ] Esempi comandi corretti
- [ ] Troubleshooting completo
- [ ] Best practices incluse

### SSH_QUICK_START.md
- [ ] File esiste e leggibile
- [ ] Guida rapida chiara per utente
- [ ] Setup iniziale ben spiegato
- [ ] Esempi pratici funzionanti

### FEATURE_SSH_MANAGEMENT.md
- [ ] Documentazione tecnica completa
- [ ] Tutte le funzioni documentate
- [ ] Modifiche file elencate
- [ ] File creati elencati

### CHANGELOG.md
- [ ] Versione 1.1.0 presente
- [ ] Tutte le modifiche elencate
- [ ] Data corretta (2026-02-15)

## 🔒 Test Sicurezza

### Configurazione Base
- [ ] SSH richiede password o chiave per accesso
- [ ] Root login disabilitato (default)
- [ ] PermitEmptyPasswords = no

### Firewall
- [ ] Regola "WSL SSH" presente in Windows Firewall
- [ ] Porta 22 aperta solo per connessioni necessarie

### Port Forwarding
- [ ] Port forwarding configurato solo per porta 22
- [ ] Non ci sono altri port forwarding non autorizzati

## 🛠️ Test Edge Cases

### Test 1: SSH già avviato
1. [ ] Avvia SSH da WSL: `sudo service ssh start`
2. [ ] Prova ad avviare da Manager
3. [ ] Verifica messaggio "già in esecuzione"
4. [ ] Nessun errore generato

### Test 2: SSH già fermo
1. [ ] Ferma SSH da WSL: `sudo service ssh stop`
2. [ ] Prova a fermare da Manager
3. [ ] Verifica messaggio "non è in esecuzione"
4. [ ] Nessun errore generato

### Test 3: WSL non disponibile
1. [ ] Ferma WSL: `wsl --shutdown` (da PowerShell)
2. [ ] Prova ad avviare SSH da Manager
3. [ ] Verifica gestione errore appropriata

### Test 4: Distribuzione WSL errata
1. [ ] Modifica `$WSL_DISTRO` in script con nome errato
2. [ ] Prova ad avviare SSH
3. [ ] Verifica messaggio errore chiaro

## 📊 Risultati Attesi

### Funzionalità Core
- ✅ SSH si avvia correttamente
- ✅ SSH si arresta correttamente
- ✅ SSH si riavvia correttamente
- ✅ Stato SSH rilevato accuratamente
- ✅ GUI aggiorna stato in tempo reale
- ✅ Menu console mostra opzioni SSH
- ✅ Script batch funzionano standalone

### Port Forwarding
- ✅ Port forwarding configurato correttamente
- ✅ Firewall permette connessioni SSH
- ✅ Connessione da rete locale funziona
- ✅ IP Windows rilevato correttamente

### Documentazione
- ✅ Tutte le guide presenti e complete
- ✅ Esempi funzionanti
- ✅ Collegamenti tra documenti corretti

## ❌ Problemi Noti / Limitazioni

### Da Documentare
- [ ] Port forwarding si perde dopo riavvio PC (richiede re-esecuzione script)
- [ ] sudo senza password richiede configurazione manuale
- [ ] IP WSL può cambiare dopo riavvio

### Soluzioni Previste
- [x] Task Scheduler per port forwarding automatico
- [x] Guida per configurare sudoers
- [x] Script rileva sempre IP aggiornato

## 🎯 Prossimi Passi (Opzionale)

### Miglioramenti Futuri
- [ ] Comando per configurare chiavi SSH automaticamente
- [ ] Integrazione fail2ban nella GUI
- [ ] Monitoraggio connessioni SSH attive
- [ ] Export configurazione SSH
- [ ] Backup/Restore configurazione SSH

---

## ✍️ Note Test

**Testato da**: _____________________  
**Data**: _____________________  
**Versione**: 1.1.0  

**Esito Generale**: ⭕ PASS / ❌ FAIL  

**Note**:
```
[Spazio per annotazioni]
```

---

**Promemoria**: Dopo aver completato tutti i test, firma e data questo documento per tenere traccia della verifica.
