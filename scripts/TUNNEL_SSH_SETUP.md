# Configurazione Tunnel SSH Automatico - MyGest

## Panoramica

Questo setup configura un tunnel SSH permanente dal tuo PC Windows/WSL verso la VPS Hostinger, permettendo alla VPS di accedere al NAS locale (192.168.1.4) in tempo reale per servire i file dell'archivio.

## Architettura

```
NAS (192.168.1.4:445 SMB)
    ↓
Windows WSL Ubuntu (/mnt/archivio)
    ↓ [Tunnel SSH Inverso]
VPS Hostinger (72.62.34.249:10445)
    ↓ [Mount CIFS]
Django App (/srv/mygest/archivio)
    ↓ [Nginx /archivio/]
Utenti Web (https://mygest.sandrochimenti.it/archivio/...)
```

## File Componenti

### Windows (C:\MyGest\)
- `startup_tunnel.ps1` - Script PowerShell principale
- `startup_tunnel.bat` - Launcher batch per Task Scheduler
- `install_task_scheduler.ps1` - Script installazione automatica

### WSL Ubuntu (/home/sandro/mygest/scripts/)
- `ssh_tunnel_to_vps.sh` - Script tunnel SSH

### VPS (/srv/mygest/)
- `archivio/` - Mount point CIFS del NAS
- `/etc/samba/cred_nas` - Credenziali mount CIFS

## Installazione

### 1. Preparazione WSL

```bash
# Verifica che lo script esista e sia eseguibile
ls -la /home/sandro/mygest/scripts/ssh_tunnel_to_vps.sh
chmod +x /home/sandro/mygest/scripts/ssh_tunnel_to_vps.sh

# Test manuale tunnel
/home/sandro/mygest/scripts/ssh_tunnel_to_vps.sh
# Premi Ctrl+C per interrompere dopo il test
```

### 2. Installazione Task Scheduler su Windows

**Opzione A - Automatica (Consigliata)**

1. Apri PowerShell come **Amministratore**
2. Esegui:
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process
   cd \\wsl$\Ubuntu\home\sandro\mygest\scripts
   .\install_task_scheduler.ps1
   ```
3. Segui le istruzioni interattive

**Opzione B - Manuale**

1. Copia gli script in Windows:
   ```powershell
   mkdir C:\MyGest
   mkdir C:\MyGest\logs
   
   # Copia da WSL
   copy \\wsl$\Ubuntu\home\sandro\mygest\scripts\windows_startup_tunnel.ps1 C:\MyGest\startup_tunnel.ps1
   copy \\wsl$\Ubuntu\home\sandro\mygest\scripts\windows_startup_tunnel.bat C:\MyGest\startup_tunnel.bat
   ```

2. Apri **Task Scheduler** (Win+R → `taskschd.msc`)

3. Crea nuovo task:
   - **General**: 
     - Name: `MyGest_SSH_Tunnel`
     - Run with highest privileges: ☑️
     - Run whether user is logged on or not: ☑️
   
   - **Triggers**: 
     - New → At startup
     - Delay task for: 30 seconds
   
   - **Actions**: 
     - New → Start a program
     - Program: `cmd.exe`
     - Arguments: `/c "C:\MyGest\startup_tunnel.bat"`
   
   - **Conditions**:
     - Start only if network available: ☑️
     - Stop if computer switches to battery: ☐
   
   - **Settings**:
     - Allow task to run on demand: ☑️
     - If running task does not end when requested: Do not stop
     - Do not start a new instance

4. Salva e testa: Click destro → Run

### 3. Configurazione Mount Permanente su VPS

**IMPORTANTE**: Il mount CIFS sulla VPS dipende dal tunnel SSH attivo. Non usare `/etc/fstab` perché il tunnel potrebbe non essere pronto al boot della VPS.

Invece, crea uno script di mount che si esegue dopo che il tunnel è attivo:

```bash
# SSH nella VPS
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249

# Crea script mount
sudo tee /usr/local/bin/mount_nas_archive.sh > /dev/null <<'EOF'
#!/bin/bash
# Monta l'archivio NAS attraverso il tunnel SSH

MAX_ATTEMPTS=10
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    # Verifica se tunnel è attivo (porta 10445 in ascolto)
    if ss -tuln | grep -q ":10445 "; then
        echo "✅ Tunnel SSH rilevato"
        
        # Verifica se già montato
        if mountpoint -q /srv/mygest/archivio; then
            echo "✅ Archivio già montato"
            exit 0
        fi
        
        # Monta
        mount -t cifs //localhost/documenti/archivio /srv/mygest/archivio \
            -o credentials=/etc/samba/cred_nas,vers=3.0,port=10445,uid=1000,gid=33,file_mode=0664,dir_mode=0775,noperm
        
        if [ $? -eq 0 ]; then
            echo "✅ Archivio montato con successo"
            systemctl reload nginx
            exit 0
        else
            echo "❌ Errore nel mount"
            exit 1
        fi
    else
        echo "⏳ Tunnel non ancora attivo, attendo... (tentativo $((ATTEMPT+1))/$MAX_ATTEMPTS)"
        sleep 5
    fi
    
    ATTEMPT=$((ATTEMPT+1))
done

echo "❌ Timeout: tunnel non disponibile dopo $MAX_ATTEMPTS tentativi"
exit 1
EOF

# Rendi eseguibile
sudo chmod +x /usr/local/bin/mount_nas_archive.sh

# Crea systemd service per mount automatico
sudo tee /etc/systemd/system/mount-nas-archive.service > /dev/null <<'EOF'
[Unit]
Description=Mount NAS Archive via SSH Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/mount_nas_archive.sh
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Abilita il service
sudo systemctl daemon-reload
sudo systemctl enable mount-nas-archive.service

# Test manuale
sudo systemctl start mount-nas-archive.service
sudo systemctl status mount-nas-archive.service
```

## Gestione

### Comandi Windows (PowerShell Amministratore)

```powershell
# Visualizza stato task
Get-ScheduledTask -TaskName "MyGest_SSH_Tunnel"

# Avvia manualmente
Start-ScheduledTask -TaskName "MyGest_SSH_Tunnel"

# Ferma task
Stop-ScheduledTask -TaskName "MyGest_SSH_Tunnel"

# Visualizza log
Get-Content C:\MyGest\logs\tunnel_startup.log -Tail 50

# Visualizza log in tempo reale
Get-Content C:\MyGest\logs\tunnel_startup.log -Wait

# Rimuovi task (disinstalla)
Unregister-ScheduledTask -TaskName "MyGest_SSH_Tunnel" -Confirm:$false
```

### Comandi WSL

```bash
# Verifica tunnel attivo
pgrep -f "ssh.*10445" && echo "Tunnel attivo" || echo "Tunnel inattivo"

# Verifica porta tunnel sulla VPS
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "ss -tuln | grep 10445"

# Kill tunnel manuale
pkill -f "ssh.*10445"

# Test tunnel manuale
/home/sandro/mygest/scripts/ssh_tunnel_to_vps.sh
```

### Comandi VPS

```bash
# Verifica tunnel attivo (porta 10445)
ss -tuln | grep 10445

# Verifica mount
mountpoint /srv/mygest/archivio
df -h /srv/mygest/archivio

# Test accesso file
ls -la /srv/mygest/archivio/ | head -10

# Rimonta archivio (se tunnel è attivo)
sudo umount /srv/mygest/archivio
sudo /usr/local/bin/mount_nas_archive.sh

# Verifica service mount
sudo systemctl status mount-nas-archive.service

# Log service mount
sudo journalctl -u mount-nas-archive.service -n 50
```

## Troubleshooting

### Il tunnel non parte all'avvio di Windows

1. Verifica log: `C:\MyGest\logs\tunnel_startup.log`
2. Controlla Task Scheduler: Win+R → `taskschd.msc`
3. Verifica che il task sia abilitato e con trigger "At Startup"
4. Prova ad eseguire manualmente: `Start-ScheduledTask -TaskName "MyGest_SSH_Tunnel"`

### Il tunnel cade spesso

- Il monitor automatico lo riavvierà entro 3 minuti
- Controlla connessione internet
- Verifica log: `cat /tmp/ssh_tunnel.log`
- Aumenta `ServerAliveInterval` nello script

### File non accessibili dalla VPS

```bash
# 1. Verifica tunnel
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "ss -tuln | grep 10445"

# 2. Verifica mount
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "mountpoint /srv/mygest/archivio && df -h /srv/mygest/archivio"

# 3. Test accesso file Django
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "cd /srv/mygest/app && /srv/mygest/venv/bin/python manage.py shell -c 'from documenti.models import Documento; import os; doc = Documento.objects.exclude(file=\"\").first(); print(f\"File exists: {os.path.exists(doc.file.path)}\")'"

# 4. Test accesso web
curl -I https://mygest.sandrochimenti.it/archivio/ARKLAB01/test.pdf
```

### Mount CIFS fallisce sulla VPS

```bash
# Verifica credenziali
sudo cat /etc/samba/cred_nas

# Verifica tunnel attivo
ss -tuln | grep 10445

# Test mount manuale
sudo mount -t cifs //localhost/documenti/archivio /tmp/test \
    -o credentials=/etc/samba/cred_nas,vers=3.0,port=10445

# Controlla kernel log
dmesg | tail -20
```

## Monitoraggio

### Dashboard Status (da creare)

Puoi creare un endpoint Django per verificare lo stato:

```python
# api/v1/system/views.py
@api_view(['GET'])
def storage_status(request):
    import os
    import subprocess
    
    archivio_path = '/srv/mygest/archivio'
    
    status = {
        'archivio_mounted': os.path.ismount(archivio_path),
        'archivio_accessible': os.path.exists(archivio_path),
        'tunnel_active': False,
    }
    
    # Check tunnel
    try:
        result = subprocess.run(['ss', '-tuln'], capture_output=True, text=True)
        status['tunnel_active'] = ':10445' in result.stdout
    except:
        pass
    
    # Check disk space
    if status['archivio_mounted']:
        stat = os.statvfs(archivio_path)
        status['disk_total_gb'] = (stat.f_blocks * stat.f_frsize) / (1024**3)
        status['disk_free_gb'] = (stat.f_bavail * stat.f_frsize) / (1024**3)
    
    return Response(status)
```

## Sicurezza

- ✅ Tunnel SSH cifrato end-to-end
- ✅ Nessuna porta aperta sul router locale
- ✅ Credenziali CIFS protette (chmod 600)
- ✅ Mount CIFS solo su localhost VPS (non esposto pubblicamente)
- ✅ Nginx serve file con autenticazione Django

## Performance

- **Latenza**: +20-50ms rispetto a file locali (dipende da connessione)
- **Throughput**: ~10-50 MB/s (dipende da upload locale e connessione VPS)
- **Limite pratico**: 5-10 utenti concorrenti che scaricano file grandi

## Note

- Il PC Windows/WSL deve rimanere acceso 24/7 per servire i file
- Se il PC si spegne, i file non saranno accessibili sulla VPS
- Considera una soluzione VPN/Tailscale per latenza migliore in futuro
- Per production con alta disponibilità, valuta sincronizzazione periodica (rsync) invece di mount in tempo reale

## Support

Per problemi o domande, controlla:
1. Log Windows: `C:\MyGest\logs\tunnel_startup.log`
2. Log WSL tunnel: `/tmp/ssh_tunnel.log`
3. Log VPS mount: `sudo journalctl -u mount-nas-archive.service`
4. Log Nginx VPS: `sudo tail -f /var/log/nginx/mygest.error.log`
