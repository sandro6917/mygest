@echo off
REM Script di avvio rapido - Start All Servers

echo Avvio di tutti i server...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0WSL_Server_Manager.ps1" -Action start
pause
