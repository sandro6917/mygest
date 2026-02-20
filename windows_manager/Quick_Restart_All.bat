@echo off
REM Script di riavvio rapido - Restart All Servers

echo Riavvio di tutti i server...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0WSL_Server_Manager.ps1" -Action restart
pause
