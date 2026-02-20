@echo off
REM WSL Server Manager - Launcher
REM Questo file batch avvia lo script PowerShell per la gestione dei server

echo.
echo ============================================
echo   WSL Server Manager per MyGest
echo ============================================
echo.

REM Verifica se PowerShell è disponibile
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERRORE: PowerShell non trovato!
    pause
    exit /b 1
)

REM Avvia lo script PowerShell con la policy di esecuzione bypass
powershell.exe -ExecutionPolicy Bypass -File "%~dp0WSL_Server_Manager.ps1" -Action menu

pause
