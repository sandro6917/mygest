@echo off
REM Quick Start SSH Server
REM Avvia rapidamente il server SSH su WSL

echo ================================================
echo   Quick Start SSH Server - MyGest
echo ================================================
echo.

REM Avvia SSH
echo Avvio del server SSH...
wsl -d Ubuntu-22.04 bash -c "sudo systemctl start ssh 2>/dev/null || sudo service ssh start 2>/dev/null"

timeout /t 2 /nobreak >nul

REM Verifica stato
wsl -d Ubuntu-22.04 bash -c "systemctl is-active ssh 2>/dev/null || service ssh status 2>/dev/null | grep -q 'running' && echo 'SSH Server ATTIVO' || echo 'SSH Server FERMO'"

echo.
echo ================================================
echo   Server SSH avviato!
echo   Connettiti con: ssh utente@localhost
echo ================================================
echo.

pause
