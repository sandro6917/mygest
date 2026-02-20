# Setup SSH Port Forwarding per WSL
# Questo script configura il port forwarding da Windows a WSL per SSH
# DEVE essere eseguito come Amministratore

# Verifica privilegi Amministratore
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "Questo script richiede privilegi di Amministratore!"
    Write-Host "Riavvia PowerShell come Amministratore e riprova."
    exit 1
}

# Configurazione
$WSL_DISTRO = "Ubuntu-22.04"
$SSH_PORT = 22

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Setup SSH Port Forwarding WSL -> Windows  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Ottieni IP di WSL
Write-Host "Ottenendo IP di WSL..." -ForegroundColor Yellow
$wslIp = (wsl -d $WSL_DISTRO hostname -I 2>$null)
if ($wslIp) {
    $wslIp = $wslIp.Trim().Split()[0]
    Write-Host "WSL IP trovato: $wslIp" -ForegroundColor Green
} else {
    Write-Host "ERRORE: Impossibile ottenere IP di WSL" -ForegroundColor Red
    Write-Host "Verifica che WSL sia in esecuzione e la distribuzione '$WSL_DISTRO' sia installata." -ForegroundColor Yellow
    exit 1
}

# Rimuovi vecchi port forwarding per la porta SSH
Write-Host ""
Write-Host "Rimozione vecchie configurazioni port forwarding..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=$SSH_PORT listenaddress=0.0.0.0 2>$null
Write-Host "Fatto." -ForegroundColor Green

# Aggiungi nuovo port forwarding
Write-Host ""
Write-Host "Configurazione nuovo port forwarding..." -ForegroundColor Yellow
$result = netsh interface portproxy add v4tov4 listenport=$SSH_PORT listenaddress=0.0.0.0 connectport=$SSH_PORT connectaddress=$wslIp
if ($LASTEXITCODE -eq 0) {
    Write-Host "Port forwarding configurato con successo!" -ForegroundColor Green
} else {
    Write-Host "ERRORE durante la configurazione del port forwarding" -ForegroundColor Red
    exit 1
}

# Verifica configurazione Firewall
Write-Host ""
Write-Host "Verifica regola Firewall per SSH..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -Name "WSL SSH" -ErrorAction SilentlyContinue
if (-not $firewallRule) {
    Write-Host "Regola Firewall non trovata. Creazione in corso..." -ForegroundColor Yellow
    New-NetFirewallRule -Name "WSL SSH" -DisplayName "WSL SSH Server" -Direction Inbound -LocalPort $SSH_PORT -Protocol TCP -Action Allow | Out-Null
    Write-Host "Regola Firewall creata con successo!" -ForegroundColor Green
} else {
    Write-Host "Regola Firewall gia' presente." -ForegroundColor Green
}

# Mostra configurazione attuale
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Configurazione Port Forwarding Attiva     " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
netsh interface portproxy show all

# Ottieni IP del PC Windows nella LAN
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Informazioni di Connessione               " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
$windowsIp = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Ethernet*" -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress
if (-not $windowsIp) {
    $windowsIp = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*" -ErrorAction SilentlyContinue | Select-Object -First 1).IPAddress
}

if ($windowsIp) {
    Write-Host ""
    Write-Host "Per connetterti da rete locale usa:" -ForegroundColor Yellow
    Write-Host "  ssh utente@$windowsIp" -ForegroundColor Green
    Write-Host ""
    Write-Host "Oppure da localhost (Windows):" -ForegroundColor Yellow
    Write-Host "  ssh utente@localhost" -ForegroundColor Green
} else {
    Write-Host "Impossibile determinare IP locale di Windows" -ForegroundColor Red
}

Write-Host ""
Write-Host "NOTA: Questo port forwarding persiste fino al riavvio del PC." -ForegroundColor Yellow
Write-Host "      Riesegui questo script dopo ogni riavvio se necessario." -ForegroundColor Yellow
Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan

# Opzione per rendere permanente
Write-Host ""
$makePermanent = Read-Host "Vuoi aggiungere questo script all'avvio automatico? (S/N)"
if ($makePermanent.ToUpper() -eq "S") {
    # Crea task scheduler
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -WindowStyle Hidden"
    $trigger = New-ScheduledTaskTrigger -AtStartup
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName "WSL SSH Port Forwarding" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    
    Write-Host "Task Scheduler creato! Il port forwarding sara' configurato automaticamente ad ogni avvio." -ForegroundColor Green
}

Write-Host ""
Write-Host "Setup completato!" -ForegroundColor Green
Write-Host ""
