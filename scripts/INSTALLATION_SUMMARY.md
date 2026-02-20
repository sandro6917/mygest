# 🎯 RIEPILOGO INSTALLAZIONE TUNNEL SSH - MyGest

## ✅ Cosa è stato configurato

### 1. Script Windows (Task Scheduler)
📁 Percorso: `/home/sandro/mygest/scripts/`
- ✅ `windows_startup_tunnel.ps1` - Script PowerShell principale con monitor
- ✅ `windows_startup_tunnel.bat` - Launcher per Task Scheduler
- ✅ `install_task_scheduler.ps1` - Installer automatico

### 2. Script WSL Ubuntu
📁 Percorso: `/home/sandro/mygest/scripts/`
- ✅ `ssh_tunnel_to_vps.sh` - Tunnel SSH inverso (già esistente)

### 3. Configurazione VPS
📁 VPS: `72.62.34.249`
- ✅ SSH Server con `GatewayPorts yes` abilitato
- ✅ Script mount: `/usr/local/bin/mount_nas_archive.sh`
- ✅ Systemd service: `mount-nas-archive.service` (abilitato)
- ✅ Credenziali CIFS: `/etc/samba/cred_nas` (chmod 600)
- ✅ Mount point: `/srv/mygest/archivio`
- ✅ Nginx configurato per servire `/archivio/`

### 4. Documentazione
📁 Percorso: `/home/sandro/mygest/scripts/`
- ✅ `TUNNEL_SSH_SETUP.md` - Guida completa

---

## 🚀 PROSSIMI PASSI - Installazione su Windows

### Step 1: Installa il Task Scheduler (dal tuo PC Windows)

**Apri PowerShell come Amministratore** e esegui:

```powershell
# 1. Consenti esecuzione script
Set-ExecutionPolicy Bypass -Scope Process

# 2. Naviga nella directory script
cd \\wsl$\Ubuntu\home\sandro\mygest\scripts

# 3. Esegui installer
.\install_task_scheduler.ps1

# 4. Segui le istruzioni interattive
#    - Risponderà "S" per avviare il task per test
#    - Visualizza il log per verificare che funzioni
```

### Step 2: Verifica funzionamento

Dopo l'installazione, verifica che tutto funzioni:

#### Su Windows (PowerShell):
```powershell
# Controlla stato task
Get-ScheduledTask -TaskName "MyGest_SSH_Tunnel"

# Visualizza log
Get-Content C:\MyGest\logs\tunnel_startup.log -Tail 20

# Se vedi messaggi tipo:
# ✅ WSL in esecuzione
# ✅ NAS montato correttamente  
# ✅ Tunnel SSH operativo
# Allora è tutto OK!
```

#### Su WSL (bash):
```bash
# Verifica processo tunnel
pgrep -f "ssh.*10445" && echo "✅ Tunnel attivo" || echo "❌ Tunnel inattivo"

# Test connessione VPS
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "ss -tuln | grep 10445"
```

#### Su VPS (verifica mount):
```bash
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "
  echo '=== Status Tunnel ===' && \
  ss -tuln | grep 10445 && \
  echo '' && \
  echo '=== Status Mount ===' && \
  mountpoint /srv/mygest/archivio && \
  df -h /srv/mygest/archivio && \
  echo '' && \
  echo '=== Test accesso file ===' && \
  ls -la /srv/mygest/archivio | head -10
"
```

### Step 3: Test accesso file da web

Apri browser e prova ad accedere a un file (esempio):
```
https://mygest.sandrochimenti.it/archivio/ARKLAB01/AF%20-%20Amministrazione,%20Finanza%20e%20Controllo/AF_LIBF%20-%20Libri%20e%20registri%20fiscali/2026/ARKLABS%20SOCIETA'%20A%20RESPONSABILITA'%20LIMITATA%20TRA%20PROFESSIONISTI.pdf
```

**Oppure testa con curl**:
```bash
curl -I https://mygest.sandrochimenti.it/archivio/ARKLAB01/
```

Dovresti vedere risposta `200 OK` o `403 Forbidden` (normale per directory).

---

## 🔧 Comandi Utili Post-Installazione

### Windows - Gestione Task
```powershell
# Avvia task manualmente (per test)
Start-ScheduledTask -TaskName "MyGest_SSH_Tunnel"

# Ferma task
Stop-ScheduledTask -TaskName "MyGest_SSH_Tunnel"

# Visualizza log live
Get-Content C:\MyGest\logs\tunnel_startup.log -Wait

# Disabilita task (non parte all'avvio)
Disable-ScheduledTask -TaskName "MyGest_SSH_Tunnel"

# Riabilita task
Enable-ScheduledTask -TaskName "MyGest_SSH_Tunnel"
```

### VPS - Gestione Mount
```bash
# Status service mount
sudo systemctl status mount-nas-archive.service

# Riavvia service mount
sudo systemctl restart mount-nas-archive.service

# Log service
sudo journalctl -u mount-nas-archive.service -f

# Smonta manualmente (per manutenzione)
sudo umount /srv/mygest/archivio

# Rimonta manualmente
sudo /usr/local/bin/mount_nas_archive.sh
```

---

## 🎯 Comportamento Atteso

### All'avvio di Windows:
1. ⏱️  Windows Task Scheduler parte dopo 30 secondi dal boot
2. 🔧 Script PowerShell avvia WSL
3. ✅ Verifica mount NAS locale (`/mnt/archivio`)
4. 🚀 Avvia tunnel SSH verso VPS (porta 10445)
5. 👀 Monitor controlla tunnel ogni 60 secondi
6. 🔄 Se tunnel cade, riavvia automaticamente dopo 3 controlli falliti

### Sulla VPS:
1. 🔍 Service `mount-nas-archive` parte al boot
2. ⏳ Attende che tunnel sia attivo (max 10 tentativi = 50 secondi)
3. 💾 Monta archivio NAS via CIFS su `/srv/mygest/archivio`
4. 🔄 Nginx reload per servire nuovi file

### Durante utilizzo:
- 📂 Utenti accedono ai file via `https://mygest.sandrochimenti.it/archivio/...`
- 🌐 Nginx serve file statici dal mount CIFS
- 🔒 Django controlla autenticazione/permessi
- ⚡ Latenza: +20-50ms rispetto a file locali VPS

---

## ⚠️ IMPORTANTE - Requisiti

### Per funzionare correttamente:

✅ **PC Windows/WSL sempre acceso**
- Se il PC si spegne, i file NON saranno accessibili
- Considera UPS per protezione blackout

✅ **Connessione internet stabile**
- Upload minimo: 5 Mbps (consigliato 20+ Mbps)
- Latenza stabile <100ms

✅ **NAS sempre acceso e accessibile**
- Mount `/mnt/archivio` funzionante su WSL
- Credenziali CIFS valide

### Cosa succede se qualcosa va offline:

| Componente Offline | Effetto | Ripristino |
|-------------------|---------|------------|
| PC Windows spento | ❌ File non accessibili | Automatico al riavvio PC |
| WSL crashato | ❌ Tunnel cade | Automatico in <3 min |
| Tunnel SSH cade | ❌ File non accessibili | Automatico in <3 min |
| NAS offline | ❌ Mount fallisce | Riavvia NAS, poi `sudo systemctl restart mount-nas-archive` |
| VPS offline | ❌ Applicazione offline | Attendi ripristino VPS Hostinger |

---

## 📊 Monitoraggio Consigliato

### Dashboard Status (TODO - da implementare)
Aggiungi endpoint Django per verificare stato in tempo reale:
- ✅ Tunnel attivo (porta 10445 in ascolto)
- ✅ Mount archivio funzionante
- ✅ Spazio disco disponibile
- ✅ Ultimo file accesso

### Alert Email (TODO - opzionale)
Configura cron sulla VPS per alert se:
- Mount archivio fallisce per >10 minuti
- Tunnel SSH non attivo per >5 minuti
- Spazio disco <10% disponibile

---

## 🆘 Troubleshooting Veloce

### Problema: File non accessibili da web

**Diagnosi rapida**:
```bash
# 1. Verifica tunnel (su WSL)
pgrep -f "ssh.*10445" || echo "TUNNEL MORTO!"

# 2. Verifica mount (su VPS)
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "mountpoint /srv/mygest/archivio || echo 'MOUNT FALLITO!'"

# 3. Test diretto file (su VPS)
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "ls -la /srv/mygest/archivio | head -5 || echo 'FILE NON LEGGIBILI!'"
```

**Soluzione rapida**:
```powershell
# Su Windows PowerShell Amministratore
Stop-ScheduledTask -TaskName "MyGest_SSH_Tunnel"
Start-Sleep -Seconds 5
Start-ScheduledTask -TaskName "MyGest_SSH_Tunnel"

# Attendi 2 minuti
Start-Sleep -Seconds 120

# Verifica log
Get-Content C:\MyGest\logs\tunnel_startup.log -Tail 30
```

---

## ✅ CHECKLIST FINALE

Prima di considerare l'installazione completa, verifica:

- [ ] Task Scheduler installato su Windows
- [ ] Task avviato e log mostra "Tunnel SSH operativo"
- [ ] Comando `pgrep -f "ssh.*10445"` su WSL restituisce un PID
- [ ] Comando `ss -tuln | grep 10445` sulla VPS mostra porta in LISTEN
- [ ] Mount `/srv/mygest/archivio` è attivo sulla VPS
- [ ] `ls /srv/mygest/archivio` mostra directory clienti
- [ ] Accesso web a un file PDF funziona
- [ ] Django riesce ad accedere ai file (`doc.file.path` exists)
- [ ] Riavvio Windows → tutto si riavvia automaticamente
- [ ] Monitor PowerShell riavvia tunnel se cade

---

## 📞 Supporto

Per problemi:
1. Controlla log in ordine:
   - `C:\MyGest\logs\tunnel_startup.log`
   - `/tmp/ssh_tunnel.log`
   - `sudo journalctl -u mount-nas-archive.service`
   
2. Consulta `TUNNEL_SSH_SETUP.md` per guida dettagliata

3. Test manuali per isolare il problema:
   - WSL funzionante? `wsl -e echo OK`
   - NAS accessibile? `ls /mnt/archivio`
   - Tunnel funziona manualmente? `/home/sandro/mygest/scripts/ssh_tunnel_to_vps.sh`
   - Mount funziona manualmente? `sudo /usr/local/bin/mount_nas_archive.sh`

---

**Data configurazione**: 2026-02-20
**Versione**: 1.0
**Status**: ✅ Configurato e pronto per installazione
