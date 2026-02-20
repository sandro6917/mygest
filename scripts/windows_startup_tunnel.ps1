# ============================================================================
# Script di Startup per Windows: Avvio WSL + Tunnel SSH verso VPS
# ============================================================================
# 
# Questo script viene eseguito all'avvio di Windows e si occupa di:
# 1. Avviare WSL (Ubuntu)
# 2. Verificare il mount del NAS (/mnt/archivio)
# 3. Creare tunnel SSH verso VPS per accesso archivio
# 4. Monitorare il tunnel e riavviarlo se cade
#
# Installazione:
# 1. Salvare questo file in: C:\MyGest\startup_tunnel.ps1
# 2. Creare Scheduled Task con trigger "At Startup"
# 3. Run with highest privileges
#
# ============================================================================

# Configurazione
$LogFile = "C:\MyGest\logs\tunnel_startup.log"
$WSLDistro = "Ubuntu"
$TunnelCheckInterval = 60  # Secondi tra ogni controllo

# Crea directory log se non esiste
$LogDir = Split-Path -Parent $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Funzione per scrivere log
function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

# Funzione per verificare se WSL è in esecuzione
function Test-WSLRunning {
    try {
        # Prova ad eseguire un comando semplice in WSL
        $result = wsl.exe -- echo "OK" 2>$null
        return $result -match "OK"
    } catch {
        return $false
    }
}

# Funzione per verificare se il tunnel SSH è attivo
function Test-TunnelActive {
    try {
        $result = wsl.exe -- bash -c "pgrep -f 'ssh.*10445' > /dev/null && echo 'ACTIVE' || echo 'INACTIVE'" 2>$null
        return $result -match "ACTIVE"
    } catch {
        return $false
    }
}

# Funzione per verificare mount NAS
function Test-NASMounted {
    try {
        $result = wsl.exe -- bash -c "mountpoint -q /mnt/archivio && echo 'MOUNTED' || echo 'NOT_MOUNTED'" 2>$null
        return $result -match "MOUNTED"
    } catch {
        return $false
    }
}

# Funzione per avviare il tunnel SSH
function Start-SSHTunnel {
    Write-Log "Avvio tunnel SSH verso VPS..."
    
    # Usa script wrapper bash che gestisce il background
    $tunnelScript = "/home/sandro/mygest/scripts/start_tunnel_background.sh"
    
    # Esegui script wrapper
    $result = wsl.exe -- bash $tunnelScript 2>&1
    Write-Log $result
    
    Start-Sleep -Seconds 2
    
    # Verifica che sia partito
    if (Test-TunnelActive) {
        Write-Log "✅ Tunnel SSH avviato con successo"
        return $true
    } else {
        Write-Log "❌ Errore nell'avvio del tunnel SSH"
        return $false
    }
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

Write-Log "============================================"
Write-Log "Avvio script startup tunnel SSH"
Write-Log "============================================"

# 1. Verifica WSL
Write-Log "🔍 Verifico stato WSL..."
if (-not (Test-WSLRunning)) {
    Write-Log "⚠️  WSL non in esecuzione, avvio WSL..."
    # Avvia WSL in background
    Start-Process wsl.exe -ArgumentList "--" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 5
}

if (Test-WSLRunning) {
    Write-Log "✅ WSL in esecuzione"
} else {
    Write-Log "❌ Impossibile avviare WSL - SCRIPT TERMINATO"
    exit 1
}

# 2. Verifica mount NAS
Write-Log "🔍 Verifico mount NAS (/mnt/archivio)..."
if (Test-NASMounted) {
    Write-Log "✅ NAS montato correttamente"
} else {
    Write-Log "⚠️  NAS non montato, tento mount..."
    wsl.exe -- sudo mount -a 2>$null
    Start-Sleep -Seconds 3
    
    if (Test-NASMounted) {
        Write-Log "✅ NAS montato con successo"
    } else {
        Write-Log "❌ Impossibile montare NAS - CONTINUO COMUNQUE"
    }
}

# 3. Avvia tunnel SSH
Write-Log "🚀 Avvio tunnel SSH verso VPS..."
if (Start-SSHTunnel) {
    Write-Log "✅ Tunnel SSH operativo"
} else {
    Write-Log "❌ Errore nell'avvio del tunnel"
    exit 1
}

# 4. Monitor loop - Controlla tunnel ogni minuto
Write-Log "👀 Avvio monitoraggio tunnel (intervallo: ${TunnelCheckInterval}s)"
Write-Log "   Per terminare lo script, chiudere questa finestra PowerShell"
Write-Log ""

$consecutiveFailures = 0
$maxConsecutiveFailures = 3

while ($true) {
    Start-Sleep -Seconds $TunnelCheckInterval
    
    if (Test-TunnelActive) {
        if ($consecutiveFailures -gt 0) {
            Write-Log "✅ Tunnel ripristinato"
            $consecutiveFailures = 0
        }
        # Log silenzioso ogni 10 minuti (600 secondi / 60 = 10)
        if ((Get-Date).Minute % 10 -eq 0) {
            Write-Log "✓ Tunnel attivo (check periodico)"
        }
    } else {
        $consecutiveFailures++
        Write-Log "⚠️  Tunnel non attivo (tentativo $consecutiveFailures/$maxConsecutiveFailures)"
        
        if ($consecutiveFailures -ge $maxConsecutiveFailures) {
            Write-Log "❌ Tunnel caduto dopo $maxConsecutiveFailures controlli - RIAVVIO"
            
            if (Start-SSHTunnel) {
                Write-Log "✅ Tunnel riavviato con successo"
                $consecutiveFailures = 0
            } else {
                Write-Log "❌ Impossibile riavviare tunnel - RIPROVO TRA ${TunnelCheckInterval}s"
            }
        }
    }
}
