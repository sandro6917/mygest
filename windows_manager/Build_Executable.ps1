# Script per la creazione dell'eseguibile Windows
# Richiede PS2EXE per convertire PowerShell in EXE

param(
    [switch]$Install
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Creatore Eseguibile WSL Server Manager                   " -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Verifica se PS2EXE è installato
$ps2exeInstalled = Get-Module -ListAvailable -Name ps2exe

if (-not $ps2exeInstalled -and -not $Install) {
    Write-Host "ATTENZIONE: Il modulo PS2EXE non è installato." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Per installare PS2EXE, esegui questo script con il parametro -Install:" -ForegroundColor Yellow
    Write-Host "  .\Build_Executable.ps1 -Install" -ForegroundColor Green
    Write-Host ""
    Write-Host "Oppure installa manualmente:" -ForegroundColor Yellow
    Write-Host "  Install-Module -Name ps2exe -Scope CurrentUser" -ForegroundColor Green
    Write-Host ""
    exit 1
}

if ($Install) {
    Write-Host "Installazione del modulo PS2EXE..." -ForegroundColor Yellow
    try {
        Install-Module -Name ps2exe -Scope CurrentUser -Force
        Write-Host "✓ PS2EXE installato con successo!" -ForegroundColor Green
        Write-Host ""
    } catch {
        Write-Host "✗ Errore durante l'installazione di PS2EXE: $_" -ForegroundColor Red
        exit 1
    }
}

# Importa il modulo PS2EXE
Import-Module ps2exe

# Percorsi
$scriptPath = Join-Path $PSScriptRoot "WSL_Server_Manager.ps1"
$exePath = Join-Path $PSScriptRoot "WSL_Server_Manager.exe"
$iconPath = Join-Path $PSScriptRoot "icon.ico"

# Verifica che lo script esista
if (-not (Test-Path $scriptPath)) {
    Write-Host "✗ Errore: Script WSL_Server_Manager.ps1 non trovato!" -ForegroundColor Red
    exit 1
}

Write-Host "Creazione dell'eseguibile..." -ForegroundColor Yellow
Write-Host "  Input:  $scriptPath" -ForegroundColor Gray
Write-Host "  Output: $exePath" -ForegroundColor Gray
Write-Host ""

try {
    # Parametri per la compilazione
    $params = @{
        InputFile = $scriptPath
        OutputFile = $exePath
        NoConsole = $false
        NoOutput = $false
        NoError = $false
        RequireAdmin = $false
        Title = "WSL Server Manager"
        Description = "Gestione Server Django e Frontend su WSL"
        Company = "MyGest"
        Product = "WSL Server Manager"
        Copyright = "© 2024"
        Version = "1.0.0.0"
    }
    
    # Aggiungi icona se esiste
    if (Test-Path $iconPath) {
        $params.IconFile = $iconPath
    }
    
    Invoke-PS2EXE @params
    
    if (Test-Path $exePath) {
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "  ✓ Eseguibile creato con successo!                        " -ForegroundColor Green
        Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "Percorso: $exePath" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Puoi copiare l'eseguibile su Windows e avviarlo direttamente." -ForegroundColor White
        Write-Host ""
        
        # Chiedi se creare un collegamento sul desktop
        $createShortcut = Read-Host "Vuoi creare un collegamento sul Desktop? (S/N)"
        if ($createShortcut -eq "S" -or $createShortcut -eq "s") {
            $desktopPath = [Environment]::GetFolderPath("Desktop")
            $shortcutPath = Join-Path $desktopPath "WSL Server Manager.lnk"
            
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut($shortcutPath)
            $Shortcut.TargetPath = $exePath
            $Shortcut.WorkingDirectory = $PSScriptRoot
            $Shortcut.Description = "Gestione Server Django e Frontend su WSL"
            if (Test-Path $iconPath) {
                $Shortcut.IconLocation = $iconPath
            }
            $Shortcut.Save()
            
            Write-Host "✓ Collegamento creato sul Desktop!" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "✗ Errore durante la creazione dell'eseguibile: $_" -ForegroundColor Red
    exit 1
}
