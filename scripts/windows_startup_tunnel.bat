@echo off
REM ============================================================================
REM Launcher per startup_tunnel.ps1
REM Questo file viene eseguito da Windows Task Scheduler all'avvio
REM ============================================================================

REM Crea directory log se non esiste
if not exist "C:\MyGest\logs" mkdir "C:\MyGest\logs"

REM Esegui PowerShell script con bypass execution policy
PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\MyGest\startup_tunnel.ps1"

REM Se PowerShell termina con errore, registra nel log
if errorlevel 1 (
    echo [ERROR] PowerShell script terminated with error >> C:\MyGest\logs\launcher_error.log
    exit /b 1
)

exit /b 0
