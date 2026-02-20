@echo off
REM Quick Stop SSH Server
REM Arresta rapidamente il server SSH su WSL

echo ================================================
echo   Quick Stop SSH Server - MyGest
echo ================================================
echo.

REM Ferma SSH
echo Arresto del server SSH...
wsl -d Ubuntu-22.04 bash -c "sudo systemctl stop ssh 2>/dev/null || sudo service ssh stop 2>/dev/null"

timeout /t 2 /nobreak >nul

REM Verifica stato
wsl -d Ubuntu-22.04 bash -c "systemctl is-active ssh 2>/dev/null || service ssh status 2>/dev/null | grep -q 'running' && echo 'SSH Server ATTIVO' || echo 'SSH Server FERMO'"

echo.
echo ================================================
echo   Server SSH arrestato!
echo ================================================
echo.

pause
