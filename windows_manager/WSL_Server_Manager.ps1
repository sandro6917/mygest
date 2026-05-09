# WSL Server Manager per Django e Frontend
# Gestisce i server Django e Frontend su WSL da Windows

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'menu')]
    [string]$Action = 'menu'
)

# Configurazione
$WSL_DISTRO = "Ubuntu-22.04"  # Cambia con il nome della tua distribuzione WSL
$PROJECT_PATH = "/home/sandro/mygest"
$DJANGO_PORT = 8000
$FRONTEND_PORT = 5173
$SSH_PORT = 22  # Porta SSH standard
$SCANNER_PORT = 8765  # Porta servizio scanner

# Variabili globali per tracciare i PID delle finestre PowerShell
$Global:DjangoWindowPID = $null
$Global:FrontendWindowPID = $null

# Colori per output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Show-Banner {
    Clear-Host
    Write-ColorOutput Cyan "============================================================"
    Write-ColorOutput Cyan "          WSL Server Manager - MyGest                      "
    Write-ColorOutput Cyan "          Django + Frontend Controller                     "
    Write-ColorOutput Cyan "============================================================"
    Write-Output ""
}

function Get-DjangoProcessId {
    $result = wsl -d $WSL_DISTRO bash -c "pgrep -f 'manage.py runserver'"
    return $result
}

function Get-FrontendProcessId {
    $result = wsl -d $WSL_DISTRO bash -c "pgrep -f 'vite'"
    return $result
}

function Get-SSHStatus {
    $result = wsl -d $WSL_DISTRO bash -c "systemctl is-active ssh 2>/dev/null || service ssh status 2>/dev/null | grep -q 'running' && echo 'active' || echo 'inactive'"
    return ($result -eq "active")
}

function Get-ScannerProcessId {
    $result = wsl -d $WSL_DISTRO bash -c "pgrep -f 'scanner_service.py'"
    return $result
}

function Start-DjangoServer {
    Write-ColorOutput Yellow "Avvio del server Django..."
    
    $processId = Get-DjangoProcessId
    if ($processId) {
        Write-ColorOutput Red "Il server Django e' gia' in esecuzione (PID: $processId)"
        return $false
    }
    
    # Crea un nuovo processo PowerShell che avvia WSL e salva il PID della finestra
    $cmd = "wsl -d $WSL_DISTRO bash -c 'cd $PROJECT_PATH && source venv/bin/activate 2>/dev/null || true && python manage.py runserver 0.0.0.0:$DJANGO_PORT'"
    $process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -PassThru
    $Global:DjangoWindowPID = $process.Id
    
    Start-Sleep -Seconds 3
    
    $processId = Get-DjangoProcessId
    if ($processId) {
        Write-ColorOutput Green "Server Django avviato con successo (PID: $processId)"
        Write-ColorOutput Green "  URL: http://localhost:$DJANGO_PORT"
        Write-ColorOutput Cyan "  Finestra PowerShell PID: $Global:DjangoWindowPID"
        return $true
    } else {
        Write-ColorOutput Red "Errore nell'avvio del server Django"
        # Se l'avvio fallisce, chiudi la finestra
        if ($Global:DjangoWindowPID) {
            Stop-Process -Id $Global:DjangoWindowPID -Force -ErrorAction SilentlyContinue
            $Global:DjangoWindowPID = $null
        }
        return $false
    }
}

function Start-FrontendServer {
    Write-ColorOutput Yellow "Avvio del server Frontend..."
    
    $processId = Get-FrontendProcessId
    if ($processId) {
        Write-ColorOutput Red "Il server Frontend e' gia' in esecuzione (PID: $processId)"
        return $false
    }
    
    # Crea un nuovo processo PowerShell che avvia WSL e salva il PID della finestra
    $cmd = "wsl -d $WSL_DISTRO bash -c 'cd $PROJECT_PATH/frontend && npm run dev -- --host 0.0.0.0'"
    $process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -PassThru
    $Global:FrontendWindowPID = $process.Id
    
    Start-Sleep -Seconds 3
    
    $processId = Get-FrontendProcessId
    if ($processId) {
        Write-ColorOutput Green "Server Frontend avviato con successo (PID: $processId)"
        Write-ColorOutput Green "  URL: http://localhost:$FRONTEND_PORT"
        Write-ColorOutput Cyan "  Finestra PowerShell PID: $Global:FrontendWindowPID"
        return $true
    } else {
        Write-ColorOutput Red "Errore nell'avvio del server Frontend"
        # Se l'avvio fallisce, chiudi la finestra
        if ($Global:FrontendWindowPID) {
            Stop-Process -Id $Global:FrontendWindowPID -Force -ErrorAction SilentlyContinue
            $Global:FrontendWindowPID = $null
        }
        return $false
    }
}

function Stop-DjangoServer {
    Write-ColorOutput Yellow "Arresto del server Django..."
    
    $processId = Get-DjangoProcessId
    if (-not $processId) {
        Write-ColorOutput Red "Il server Django non e' in esecuzione"
        # Chiudi comunque la finestra se esiste
        if ($Global:DjangoWindowPID) {
            Write-ColorOutput Yellow "Chiusura finestra PowerShell..."
            Stop-Process -Id $Global:DjangoWindowPID -Force -ErrorAction SilentlyContinue
            $Global:DjangoWindowPID = $null
        }
        return $false
    }
    
    wsl -d $WSL_DISTRO bash -c "kill $processId 2>/dev/null"
    Start-Sleep -Seconds 2
    
    $processId = Get-DjangoProcessId
    if (-not $processId) {
        Write-ColorOutput Green "Server Django arrestato con successo"
        # Chiudi la finestra PowerShell associata
        if ($Global:DjangoWindowPID) {
            Write-ColorOutput Cyan "Chiusura finestra PowerShell (PID: $Global:DjangoWindowPID)..."
            Stop-Process -Id $Global:DjangoWindowPID -Force -ErrorAction SilentlyContinue
            $Global:DjangoWindowPID = $null
        }
        return $true
    } else {
        Write-ColorOutput Yellow "Tentativo di arresto forzato..."
        wsl -d $WSL_DISTRO bash -c "kill -9 $processId 2>/dev/null"
        Start-Sleep -Seconds 1
        Write-ColorOutput Green "Server Django arrestato forzatamente"
        # Chiudi la finestra PowerShell associata
        if ($Global:DjangoWindowPID) {
            Write-ColorOutput Cyan "Chiusura finestra PowerShell (PID: $Global:DjangoWindowPID)..."
            Stop-Process -Id $Global:DjangoWindowPID -Force -ErrorAction SilentlyContinue
            $Global:DjangoWindowPID = $null
        }
        return $true
    }
}

function Stop-FrontendServer {
    Write-ColorOutput Yellow "Arresto del server Frontend..."
    
    $processId = Get-FrontendProcessId
    if (-not $processId) {
        Write-ColorOutput Red "Il server Frontend non e' in esecuzione"
        # Chiudi comunque la finestra se esiste
        if ($Global:FrontendWindowPID) {
            Write-ColorOutput Yellow "Chiusura finestra PowerShell..."
            Stop-Process -Id $Global:FrontendWindowPID -Force -ErrorAction SilentlyContinue
            $Global:FrontendWindowPID = $null
        }
        return $false
    }
    
    wsl -d $WSL_DISTRO bash -c "kill $processId 2>/dev/null"
    Start-Sleep -Seconds 2
    
    $processId = Get-FrontendProcessId
    if (-not $processId) {
        Write-ColorOutput Green "Server Frontend arrestato con successo"
        # Chiudi la finestra PowerShell associata
        if ($Global:FrontendWindowPID) {
            Write-ColorOutput Cyan "Chiusura finestra PowerShell (PID: $Global:FrontendWindowPID)..."
            Stop-Process -Id $Global:FrontendWindowPID -Force -ErrorAction SilentlyContinue
            $Global:FrontendWindowPID = $null
        }
        return $true
    } else {
        Write-ColorOutput Yellow "Tentativo di arresto forzato..."
        wsl -d $WSL_DISTRO bash -c "kill -9 $processId 2>/dev/null"
        Start-Sleep -Seconds 1
        Write-ColorOutput Green "Server Frontend arrestato forzatamente"
        # Chiudi la finestra PowerShell associata
        if ($Global:FrontendWindowPID) {
            Write-ColorOutput Cyan "Chiusura finestra PowerShell (PID: $Global:FrontendWindowPID)..."
            Stop-Process -Id $Global:FrontendWindowPID -Force -ErrorAction SilentlyContinue
            $Global:FrontendWindowPID = $null
        }
        return $true
    }
}

function Start-SSHServer {
    Write-ColorOutput Yellow "Avvio del server SSH..."
    
    $isActive = Get-SSHStatus
    if ($isActive) {
        Write-ColorOutput Red "Il server SSH e' gia' in esecuzione"
        return $false
    }
    
    # Prova con systemctl, se fallisce usa service
    $result = wsl -d $WSL_DISTRO bash -c "sudo systemctl start ssh 2>/dev/null || sudo service ssh start 2>/dev/null"
    Start-Sleep -Seconds 2
    
    $isActive = Get-SSHStatus
    if ($isActive) {
        Write-ColorOutput Green "Server SSH avviato con successo"
        Write-ColorOutput Green "  Connessione: ssh utente@localhost (porta $SSH_PORT)"
        Write-ColorOutput Yellow "  Nota: Assicurati che il servizio SSH sia configurato correttamente in WSL"
        return $true
    } else {
        Write-ColorOutput Red "Errore nell'avvio del server SSH"
        Write-ColorOutput Yellow "  Verifica che SSH sia installato: sudo apt install openssh-server"
        return $false
    }
}

function Stop-SSHServer {
    Write-ColorOutput Yellow "Arresto del server SSH..."
    
    $isActive = Get-SSHStatus
    if (-not $isActive) {
        Write-ColorOutput Red "Il server SSH non e' in esecuzione"
        return $false
    }
    
    # Prova con systemctl, se fallisce usa service
    $result = wsl -d $WSL_DISTRO bash -c "sudo systemctl stop ssh 2>/dev/null || sudo service ssh stop 2>/dev/null"
    Start-Sleep -Seconds 2
    
    $isActive = Get-SSHStatus
    if (-not $isActive) {
        Write-ColorOutput Green "Server SSH arrestato con successo"
        return $true
    } else {
        Write-ColorOutput Red "Errore nell'arresto del server SSH"
        return $false
    }
}

function Restart-SSHServer {
    Write-ColorOutput Yellow "Riavvio del server SSH..."
    
    # Prova con systemctl, se fallisce usa service
    $result = wsl -d $WSL_DISTRO bash -c "sudo systemctl restart ssh 2>/dev/null || sudo service ssh restart 2>/dev/null"
    Start-Sleep -Seconds 2
    
    $isActive = Get-SSHStatus
    if ($isActive) {
        Write-ColorOutput Green "Server SSH riavviato con successo"
        return $true
    } else {
        Write-ColorOutput Red "Errore nel riavvio del server SSH"
        return $false
    }
}

function Start-ScannerServer {
    Write-ColorOutput Yellow "Avvio del servizio Scanner..."
    
    $processId = Get-ScannerProcessId
    if ($processId) {
        Write-ColorOutput Red "Il servizio Scanner e' gia' in esecuzione (PID: $processId)"
        return $false
    }
    
    # Avvia il servizio scanner usando script daemon wrapper
    $result = wsl -d $WSL_DISTRO bash -c "$PROJECT_PATH/scripts/start_scanner_daemon.sh" 2>$null
    Start-Sleep -Seconds 4
    
    $processId = Get-ScannerProcessId
    if ($processId) {
        Write-ColorOutput Green "Servizio Scanner avviato con successo (PID: $processId)"
        Write-ColorOutput Green "  URL: http://localhost:$SCANNER_PORT"
        Write-ColorOutput Cyan "  Log: logs/scanner_service.log"
        
        # Verifica che il servizio risponda
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$SCANNER_PORT/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-ColorOutput Green "  Health check: OK"
            }
        } catch {
            Write-ColorOutput Yellow "  Health check non disponibile (il servizio potrebbe essere ancora in fase di avvio)"
        }
        
        return $true
    } else {
        Write-ColorOutput Red "Errore nell'avvio del servizio Scanner"
        Write-ColorOutput Yellow "  Verifica i log in logs/scanner_service.log"
        return $false
    }
}

function Stop-ScannerServer {
    Write-ColorOutput Yellow "Arresto del servizio Scanner..."
    
    $processId = Get-ScannerProcessId
    if (-not $processId) {
        Write-ColorOutput Red "Il servizio Scanner non e' in esecuzione"
        return $false
    }
    
    $result = wsl -d $WSL_DISTRO bash -c "pkill -f 'scanner_service.py'"
    Start-Sleep -Seconds 2
    
    $processId = Get-ScannerProcessId
    if (-not $processId) {
        Write-ColorOutput Green "Servizio Scanner arrestato con successo"
        return $true
    } else {
        Write-ColorOutput Red "Errore nell'arresto del servizio Scanner"
        return $false
    }
}

function Restart-ScannerServer {
    Write-ColorOutput Yellow "Riavvio del servizio Scanner..."
    
    Stop-ScannerServer
    Start-Sleep -Seconds 2
    Start-ScannerServer
}

# === AGENT AUTO-DETECTION FUNCTIONS ===

function Get-AgentProcessId {
    $result = wsl -d $WSL_DISTRO bash -c "pgrep -f 'mygest_agent_autodetect.py'"
    return $result
}

function Start-AgentServer {
    Write-ColorOutput Yellow "Avvio MyGest Agent con Auto-Detection..."
    
    $processId = Get-AgentProcessId
    if ($processId) {
        Write-ColorOutput Red "MyGest Agent e' gia' in esecuzione (PID: $processId)"
        return $false
    }
    
    # Verifica che la configurazione esista
    $configExists = wsl -d $WSL_DISTRO bash -c "test -f ~/.mygest-agent.conf && echo 'exists' || echo 'missing'"
    if ($configExists -ne "exists") {
        Write-ColorOutput Red "File configurazione non trovato: ~/.mygest-agent.conf"
        Write-ColorOutput Yellow "  Crea la configurazione con:"
        Write-ColorOutput Yellow "  cp $PROJECT_PATH/config/mygest-agent.conf.example ~/.mygest-agent.conf"
        return $false
    }
    
    # Verifica che watchdog sia installato
    $watchdogInstalled = wsl -d $WSL_DISTRO bash -c "cd $PROJECT_PATH && source venv/bin/activate 2>/dev/null && python -c 'import watchdog' 2>/dev/null && echo 'ok' || echo 'missing'"
    if ($watchdogInstalled -ne "ok") {
        Write-ColorOutput Yellow "  Installazione watchdog in corso..."
        wsl -d $WSL_DISTRO bash -c "cd $PROJECT_PATH && source venv/bin/activate 2>/dev/null && pip install -q watchdog"
        Write-ColorOutput Green "  Watchdog installato"
    }
    
    # Crea directory log se non esiste
    wsl -d $WSL_DISTRO bash -c "mkdir -p $PROJECT_PATH/logs"
    
    # Avvia agent usando script daemon wrapper
    $result = wsl -d $WSL_DISTRO bash -c "$PROJECT_PATH/scripts/start_agent_daemon.sh" 2>$null
    Start-Sleep -Seconds 4
    
    $processId = Get-AgentProcessId
    if ($processId) {
        Write-ColorOutput Green "MyGest Agent avviato con successo (PID: $processId)"
        
        # Mostra info configurazione
        $cartelle = wsl -d $WSL_DISTRO bash -c "grep '^monitor_' ~/.mygest-agent.conf 2>/dev/null | grep -v '^#' | wc -l" 2>$null
        Write-ColorOutput Cyan "  Cartelle monitorate: $cartelle"
        Write-ColorOutput Cyan "  Log servizio: logs/agent_autodetect.log"
        
        # Mostra ultimi log (attendi che si popolino)
        Start-Sleep -Seconds 3
        Write-ColorOutput Yellow "`n  Ultimi log agent:"
        wsl -d $WSL_DISTRO bash -c "tail -n 8 $PROJECT_PATH/logs/agent_autodetect.log 2>/dev/null | sed 's/^/    /'" 2>$null
        
        return $true
    } else {
        Write-ColorOutput Red "Errore nell'avvio di MyGest Agent"
        Write-ColorOutput Yellow "  Verifica i log in:"
        Write-ColorOutput Yellow "    - ~/.mygest-agent.log"
        Write-ColorOutput Yellow "    - logs/agent_autodetect.log"
        return $false
    }
}

function Stop-AgentServer {
    Write-ColorOutput Yellow "Arresto MyGest Agent..."
    
    $processId = Get-AgentProcessId
    if (-not $processId) {
        Write-ColorOutput Red "MyGest Agent non e' in esecuzione"
        return $false
    }
    
    # Usa SIGTERM per arresto pulito (agent gestisce segnale)
    $result = wsl -d $WSL_DISTRO bash -c "pkill -TERM -f 'mygest_agent_autodetect.py'"
    Start-Sleep -Seconds 3
    
    # Verifica arresto
    $processId = Get-AgentProcessId
    if (-not $processId) {
        Write-ColorOutput Green "MyGest Agent arrestato con successo"
        
        # Mostra statistiche finali dall'ultimo log agent_autodetect.log
        Write-ColorOutput Yellow "`n  Statistiche sessione (se disponibili):"
        wsl -d $WSL_DISTRO bash -c "tail -n 20 $PROJECT_PATH/logs/agent_autodetect.log 2>/dev/null | grep -E 'Statistiche|File eliminati|Fallimenti|Auto-detected|manuale' | sed 's/^/    /'" 2>$null
        
        return $true
    } else {
        Write-ColorOutput Yellow "  Arresto normale fallito, forzatura in corso..."
        # Force kill se necessario
        wsl -d $WSL_DISTRO bash -c "pkill -9 -f 'mygest_agent_autodetect.py'"
        Start-Sleep -Seconds 1
        Write-ColorOutput Green "MyGest Agent arrestato forzatamente"
        return $true
    }
}

function Restart-AgentServer {
    Write-ColorOutput Yellow "Riavvio MyGest Agent..."
    
    Stop-AgentServer
    Start-Sleep -Seconds 2
    Start-AgentServer
}

function Show-AgentStats {
    Write-ColorOutput Cyan "`n======================================="
    Write-ColorOutput Cyan "     STATISTICHE MYGEST AGENT"
    Write-ColorOutput Cyan "======================================="
    
    $processId = Get-AgentProcessId
    if (-not $processId) {
        Write-ColorOutput Red "MyGest Agent non e' in esecuzione"
        Write-Output ""
        return
    }
    
    Write-ColorOutput Green "Agent attivo (PID: $processId)"
    Write-Output ""
    
    # Mostra configurazione
    Write-ColorOutput Yellow "Configurazione:"
    $serverUrl = wsl -d $WSL_DISTRO bash -c "grep '^url' ~/.mygest-agent.conf 2>/dev/null | cut -d'=' -f2 | xargs"
    $pollInterval = wsl -d $WSL_DISTRO bash -c "grep '^poll_interval' ~/.mygest-agent.conf 2>/dev/null | cut -d'=' -f2 | xargs"
    $cacheRetention = wsl -d $WSL_DISTRO bash -c "grep '^cache_retention_hours' ~/.mygest-agent.conf 2>/dev/null | cut -d'=' -f2 | xargs"
    
    Write-Output "  Server: $serverUrl"
    Write-Output "  Poll interval: $pollInterval secondi"
    Write-Output "  Cache retention: $cacheRetention ore"
    Write-Output ""
    
    # Mostra cartelle monitorate
    Write-ColorOutput Yellow "Cartelle monitorate:"
    wsl -d $WSL_DISTRO bash -c "grep '^monitor_' ~/.mygest-agent.conf 2>/dev/null | grep -v '^#' | cut -d'=' -f2 | xargs -I {} echo '  - {}'" 2>$null
    Write-Output ""
    
    # Mostra statistiche da log attuale (agent_autodetect.log)
    Write-ColorOutput Yellow "Stato Agent:"
    $logExists = wsl -d $WSL_DISTRO bash -c "test -f $PROJECT_PATH/logs/agent_autodetect.log && echo 'exists' || echo 'missing'" 2>$null
    
    if ($logExists -eq "exists") {
        # Estrai info dalla scansione iniziale
        $fileTracciati = wsl -d $WSL_DISTRO bash -c "grep 'file unici tracciati' $PROJECT_PATH/logs/agent_autodetect.log 2>/dev/null | tail -1 | grep -oP '\d+(?= file)'" 2>$null
        if ($fileTracciati) {
            Write-Output "  File tracciati in cache: $fileTracciati"
        }
        
        # Mostra data/ora avvio
        $avvioAgent = wsl -d $WSL_DISTRO bash -c "grep 'Agent avviato con auto-detection' $PROJECT_PATH/logs/agent_autodetect.log 2>/dev/null | tail -1 | cut -d' ' -f1-2" 2>$null
        if ($avvioAgent) {
            Write-Output "  Avviato: $avvioAgent"
        }
        
        Write-Output ""
        Write-ColorOutput Yellow "Ultimi log (15 righe):"
        wsl -d $WSL_DISTRO bash -c "tail -n 15 $PROJECT_PATH/logs/agent_autodetect.log 2>/dev/null | sed 's/^/  /'" 2>$null
    } else {
        Write-ColorOutput Red "  Log agent_autodetect.log non trovato"
    }
    
    Write-Output ""
    Write-ColorOutput Cyan "======================================="
}

function Show-ServerStatus {
    Write-ColorOutput Cyan "======================================="
    Write-ColorOutput Cyan "         STATO DEI SERVIZI"
    Write-ColorOutput Cyan "======================================="
    Write-Output ""
    
    # Django Status
    $djangoProcessId = Get-DjangoProcessId
    if ($djangoProcessId) {
        Write-ColorOutput Green "Django Server:    IN ESECUZIONE (PID: $djangoProcessId)"
        Write-Output "                  http://localhost:$DJANGO_PORT"
    } else {
        Write-ColorOutput Red "Django Server:    FERMO"
    }
    
    Write-Output ""
    
    # Frontend Status
    $frontendProcessId = Get-FrontendProcessId
    if ($frontendProcessId) {
        Write-ColorOutput Green "Frontend Server:  IN ESECUZIONE (PID: $frontendProcessId)"
        Write-Output "                  http://localhost:$FRONTEND_PORT"
    } else {
        Write-ColorOutput Red "Frontend Server:  FERMO"
    }
    
    Write-Output ""
    
    # SSH Status
    $sshActive = Get-SSHStatus
    if ($sshActive) {
        Write-ColorOutput Green "SSH Server:       IN ESECUZIONE"
        Write-Output "                  ssh utente@localhost (porta $SSH_PORT)"
    } else {
        Write-ColorOutput Red "SSH Server:       FERMO"
    }
    
    Write-Output ""
    
    # Scanner Status
    $scannerProcessId = Get-ScannerProcessId
    if ($scannerProcessId) {
        Write-ColorOutput Green "Scanner Service:  IN ESECUZIONE (PID: $scannerProcessId)"
        Write-Output "                  http://localhost:$SCANNER_PORT"
    } else {
        Write-ColorOutput Red "Scanner Service:  FERMO"
    }
    
    Write-Output ""
    
    # Agent Status
    $agentProcessId = Get-AgentProcessId
    if ($agentProcessId) {
        Write-ColorOutput Green "MyGest Agent:     IN ESECUZIONE (PID: $agentProcessId)"
        $cartelle = wsl -d $WSL_DISTRO bash -c "grep '^monitor_' ~/.mygest-agent.conf 2>/dev/null | grep -v '^#' | wc -l" 2>$null
        $fileTracciati = wsl -d $WSL_DISTRO bash -c "grep 'file unici tracciati' $PROJECT_PATH/logs/agent_autodetect.log 2>/dev/null | tail -1 | grep -oP '\d+(?= file)'" 2>$null
        Write-Output "                  $cartelle cartelle, $fileTracciati file tracciati"
        Write-Output "                  Log: logs/agent_autodetect.log"
    } else {
        Write-ColorOutput Red "MyGest Agent:     FERMO"
    }
    
    Write-Output ""
    Write-ColorOutput Cyan "======================================="
}

function Show-Menu {
    Show-Banner
    Show-ServerStatus
    Write-Output ""
    Write-ColorOutput Cyan "MENU PRINCIPALE:"
    Write-Output ""
    Write-Output "  === Server Applicazione ==="
    Write-Output "  1. Avvia tutti i server"
    Write-Output "  2. Avvia solo Django"
    Write-Output "  3. Avvia solo Frontend"
    Write-Output "  4. Ferma tutti i server"
    Write-Output "  5. Ferma solo Django"
    Write-Output "  6. Ferma solo Frontend"
    Write-Output "  7. Riavvia tutti i server"
    Write-Output "  8. Riavvia solo Django"
    Write-Output "  9. Riavvia solo Frontend"
    Write-Output ""
    Write-Output "  === Server SSH (Accesso Remoto) ==="
    Write-Output "  A. Avvia SSH"
    Write-Output "  B. Ferma SSH"
    Write-Output "  C. Riavvia SSH"
    Write-Output ""
    Write-Output "  === Servizio Scanner ==="
    Write-Output "  D. Avvia Scanner"
    Write-Output "  E. Ferma Scanner"
    Write-Output "  F. Riavvia Scanner"
    Write-Output ""
    Write-Output "  === MyGest Agent (Auto-Detection) ==="
    Write-Output "  G. Avvia Agent"
    Write-Output "  H. Ferma Agent"
    Write-Output "  I. Riavvia Agent"
    Write-Output "  J. Statistiche Agent"
    Write-Output ""
    Write-Output "  === Generale ==="
    Write-Output "  S. Mostra stato"
    Write-Output "  Q. Esci"
    Write-Output ""
    
    $choice = Read-Host "Seleziona un opzione"
    
    switch ($choice.ToUpper()) {
        "1" {
            Write-Output ""
            Start-DjangoServer
            Start-FrontendServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "2" {
            Write-Output ""
            Start-DjangoServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "3" {
            Write-Output ""
            Start-FrontendServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "4" {
            Write-Output ""
            Stop-DjangoServer
            Stop-FrontendServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "5" {
            Write-Output ""
            Stop-DjangoServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "6" {
            Write-Output ""
            Stop-FrontendServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "7" {
            Write-Output ""
            Stop-DjangoServer
            Stop-FrontendServer
            Start-Sleep -Seconds 2
            Start-DjangoServer
            Start-FrontendServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "8" {
            Write-Output ""
            Stop-DjangoServer
            Start-Sleep -Seconds 2
            Start-DjangoServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "9" {
            Write-Output ""
            Stop-FrontendServer
            Start-Sleep -Seconds 2
            Start-FrontendServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "A" {
            Write-Output ""
            Start-SSHServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "B" {
            Write-Output ""
            Stop-SSHServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "C" {
            Write-Output ""
            Restart-SSHServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "D" {
            Write-Output ""
            Start-ScannerServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "E" {
            Write-Output ""
            Stop-ScannerServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "F" {
            Write-Output ""
            Restart-ScannerServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "G" {
            Write-Output ""
            Start-AgentServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "H" {
            Write-Output ""
            Stop-AgentServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "I" {
            Write-Output ""
            Restart-AgentServer
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "J" {
            Write-Output ""
            Show-AgentStats
            Write-Output ""
            Read-Host "Premi INVIO per continuare"
            Show-Menu
        }
        "S" {
            Show-Menu
        }
        "Q" {
            Write-ColorOutput Green "Arrivederci!"
            exit 0
        }
        default {
            Write-ColorOutput Red "Opzione non valida!"
            Start-Sleep -Seconds 2
            Show-Menu
        }
    }
}

# Esecuzione basata sul parametro
switch ($Action) {
    'start' {
        Show-Banner
        Start-DjangoServer
        Start-FrontendServer
    }
    'stop' {
        Show-Banner
        Stop-DjangoServer
        Stop-FrontendServer
    }
    'restart' {
        Show-Banner
        Stop-DjangoServer
        Stop-FrontendServer
        Start-Sleep -Seconds 2
        Start-DjangoServer
        Start-FrontendServer
    }
    'status' {
        Show-Banner
        Show-ServerStatus
    }
    'menu' {
        Show-Menu
    }
}
