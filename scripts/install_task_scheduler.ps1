# ============================================================================
# Script di Installazione - Task Scheduler per Tunnel SSH
# ============================================================================
#
# Esegui questo script con privilegi di amministratore per configurare
# il task automatico all'avvio di Windows
#
# Esecuzione:
# 1. Apri PowerShell come Amministratore
# 2. Esegui: Set-ExecutionPolicy Bypass -Scope Process
# 3. Esegui: .\install_task_scheduler.ps1
#
# ============================================================================

# Richiedi privilegi amministratore
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ Questo script richiede privilegi di amministratore!" -ForegroundColor Red
    Write-Host "   Riavvia PowerShell come Amministratore e riprova." -ForegroundColor Yellow
    exit 1
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Installazione Task Scheduler - Tunnel SSH" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Configurazione
$TaskName = "MyGest_SSH_Tunnel"
$ScriptDir = "C:\MyGest"
$PowerShellScript = "$ScriptDir\startup_tunnel.ps1"
$BatchScript = "$ScriptDir\startup_tunnel.bat"

# 1. Crea directory C:\MyGest se non esiste
Write-Host "📁 Creazione directory C:\MyGest..." -NoNewline
if (-not (Test-Path $ScriptDir)) {
    New-Item -ItemType Directory -Path $ScriptDir -Force | Out-Null
}
if (-not (Test-Path "$ScriptDir\logs")) {
    New-Item -ItemType Directory -Path "$ScriptDir\logs" -Force | Out-Null
}
Write-Host " ✅" -ForegroundColor Green

# 2. Copia script da WSL a Windows
Write-Host "📄 Copia script da WSL a Windows..." -NoNewline

$WSLScriptPath = "/home/sandro/mygest/scripts"

# Copia startup_tunnel.ps1
$content = wsl -e cat "$WSLScriptPath/windows_startup_tunnel.ps1"
Set-Content -Path $PowerShellScript -Value $content

# Copia startup_tunnel.bat
$content = wsl -e cat "$WSLScriptPath/windows_startup_tunnel.bat"
Set-Content -Path $BatchScript -Value $content

Write-Host " ✅" -ForegroundColor Green

# 3. Verifica esistenza task esistente e rimuovilo
Write-Host "🔍 Verifica task esistenti..." -NoNewline
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host " ⚠️  Task esistente trovato" -ForegroundColor Yellow
    Write-Host "🗑️  Rimozione task precedente..." -NoNewline
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host " ✅" -ForegroundColor Green
} else {
    Write-Host " ✅ Nessun task precedente" -ForegroundColor Green
}

# 4. Crea nuovo Scheduled Task
Write-Host "⚙️  Creazione nuovo Scheduled Task..." -NoNewline

# Azione: esegui batch script
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchScript`""

# Trigger: all'avvio di Windows (con ritardo di 30 secondi)
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Trigger.Delay = "PT30S"  # 30 secondi di ritardo

# Settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 0)  # Nessun limite di tempo

# Principal: esegui con massimi privilegi
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U `
    -RunLevel Highest

# Registra il task
Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Avvia WSL e tunnel SSH verso VPS MyGest per accesso archivio NAS" | Out-Null

Write-Host " ✅" -ForegroundColor Green

# 5. Verifica creazione
Write-Host ""
Write-Host "🔍 Verifica installazione..." -ForegroundColor Cyan
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($task) {
    Write-Host "✅ Task Scheduler installato con successo!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Dettagli Task:" -ForegroundColor Yellow
    Write-Host "  Nome: $TaskName"
    Write-Host "  Stato: $($task.State)"
    Write-Host "  Trigger: All`'avvio di Windows (+30s delay)"
    Write-Host "  Script: $PowerShellScript"
    Write-Host "  Log: $ScriptDir\logs\tunnel_startup.log"
    Write-Host ""
    
    # Chiedi se avviare subito il task per test
    $response = Read-Host "Vuoi avviare il task ora per testarlo? (S/N)"
    if ($response -eq "S" -or $response -eq "s") {
        Write-Host ""
        Write-Host "🚀 Avvio task per test..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 3
        
        Write-Host "✅ Task avviato!" -ForegroundColor Green
        Write-Host "   Controlla il log in: $ScriptDir\logs\tunnel_startup.log"
        Write-Host ""
        Write-Host "Vuoi visualizzare il log ora? (S/N)" -NoNewline
        $response = Read-Host
        if ($response -eq "S" -or $response -eq "s") {
            Start-Sleep -Seconds 2
            Get-Content "$ScriptDir\logs\tunnel_startup.log" -Tail 50
        }
    }
} else {
    Write-Host "❌ Errore nella creazione del task!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Installazione completata!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Il tunnel SSH si avviera` automaticamente ad ogni avvio di Windows." -ForegroundColor Yellow
Write-Host ""
Write-Host "Comandi utili:" -ForegroundColor Cyan
Write-Host '  - Visualizza task:  Get-ScheduledTask -TaskName MyGest_SSH_Tunnel'
Write-Host '  - Avvia manuale:    Start-ScheduledTask -TaskName MyGest_SSH_Tunnel'
Write-Host '  - Ferma task:       Stop-ScheduledTask -TaskName MyGest_SSH_Tunnel'
Write-Host '  - Rimuovi task:     Unregister-ScheduledTask -TaskName MyGest_SSH_Tunnel'
Write-Host '  - Visualizza log:   Get-Content C:\MyGest\logs\tunnel_startup.log'
Write-Host ""
