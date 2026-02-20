@echo off
REM Quick Restart SSH Server
REM Riavvia rapidamente il server SSH su WSL

echo ================================================
echo   Quick Restart SSH Server - MyGest
echo ================================================
echo.

REM Riavvia SSH
echo Riavvio del server SSH...
wsl -d Ubuntu-22.04 bash -c "sudo systemctl restart ssh 2>/dev/null || sudo service ssh restart 2>/dev/null"

timeout /t 2 /nobreak >nul

REM Verifica stato
wsl -d Ubuntu-22.04 bash -c "systemctl is-active ssh 2>/dev/null || service ssh status 2>/dev/null | grep -q 'running' && echo 'SSH Server ATTIVO' || echo 'SSH Server FERMO'"

echo.
echo ================================================
echo   Server SSH riavviato!
echo   Connettiti con: ssh utente@localhost
echo ================================================
echo.

pause
