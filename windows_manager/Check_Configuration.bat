@echo off
REM Script di verifica configurazione WSL

echo.
echo ========================================
echo   Verifica Configurazione WSL
echo ========================================
echo.

echo [1/5] Verifica WSL disponibile...
wsl --status >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] WSL e' disponibile
) else (
    echo [ERRORE] WSL non e' disponibile o non e' installato
    goto :error
)

echo.
echo [2/5] Verifica distribuzione Ubuntu-22.04...
wsl -d Ubuntu-22.04 echo "OK" >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Distribuzione Ubuntu-22.04 trovata
) else (
    echo [ERRORE] Distribuzione Ubuntu-22.04 non trovata
    echo Distribuzioni disponibili:
    wsl --list --verbose
    goto :error
)

echo.
echo [3/5] Verifica percorso progetto...
wsl -d Ubuntu test -d /home/sandro/mygest
if %errorlevel% equ 0 (
    echo [OK] Progetto trovato in /home/sandro/mygest
) else (
    echo [ERRORE] Progetto non trovato in /home/sandro/mygest
    goto :error
)

echo.
echo [4/5] Verifica Python...
wsl -d Ubuntu python3 --version
if %errorlevel% equ 0 (
    echo [OK] Python e' disponibile
) else (
    echo [ERRORE] Python non e' disponibile
    goto :error
)

echo.
echo [5/5] Verifica Node.js...
wsl -d Ubuntu node --version
if %errorlevel% equ 0 (
    echo [OK] Node.js e' disponibile
) else (
    echo [ERRORE] Node.js non e' disponibile
    goto :error
)

echo.
echo ========================================
echo   VERIFICA COMPLETATA CON SUCCESSO!
echo ========================================
echo.
echo Tutto e' configurato correttamente.
echo Puoi procedere con l'avvio dei server.
echo.
goto :end

:error
echo.
echo ========================================
echo   VERIFICA FALLITA
echo ========================================
echo.
echo Alcuni controlli hanno fallito.
echo Consulta la guida README.md per la risoluzione dei problemi.
echo.

:end
pause
