@echo off
REM Script di arresto rapido - Stop All Servers

echo Arresto di tutti i server...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0WSL_Server_Manager.ps1" -Action stop
pause
