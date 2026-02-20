# Script Installazione Task Scheduler - MyGest Tunnel SSH
# Versione semplificata

if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERRORE: Richiesti privilegi amministratore!" -ForegroundColor Red
    exit 1
}

Write-Host "Installazione Task Scheduler MyGest..." -ForegroundColor Cyan

$TaskName = "MyGest_SSH_Tunnel"
$ScriptDir = "C:\MyGest"
$PowerShellScript = "$ScriptDir\startup_tunnel.ps1"
$BatchScript = "$ScriptDir\startup_tunnel.bat"

# Crea directory
New-Item -ItemType Directory -Path $ScriptDir -Force | Out-Null
New-Item -ItemType Directory -Path "$ScriptDir\logs" -Force | Out-Null

# Copia script
$content = wsl -e cat "/home/sandro/mygest/scripts/windows_startup_tunnel.ps1"
Set-Content -Path $PowerShellScript -Value $content

$content = wsl -e cat "/home/sandro/mygest/scripts/windows_startup_tunnel.bat"
Set-Content -Path $BatchScript -Value $content

Write-Host "Script copiati in C:\MyGest" -ForegroundColor Green

# Rimuovi task esistente
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Task precedente rimosso" -ForegroundColor Yellow
}

# Crea task
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchScript`""
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Trigger.Delay = "PT30S"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Tunnel SSH MyGest verso VPS" | Out-Null

Write-Host "Task Scheduler installato!" -ForegroundColor Green
Write-Host ""
Write-Host "Vuoi avviare il task ora per testarlo? (S/N): " -NoNewline
$response = Read-Host

if ($response -eq "S" -or $response -eq "s") {
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    Write-Host "Task avviato! Controlla il log in: C:\MyGest\logs\tunnel_startup.log" -ForegroundColor Green
}
