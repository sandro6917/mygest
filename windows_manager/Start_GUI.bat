@echo off
REM Launcher per la versione GUI del manager

echo.
echo Avvio interfaccia grafica...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0WSL_Server_Manager_GUI.ps1"
