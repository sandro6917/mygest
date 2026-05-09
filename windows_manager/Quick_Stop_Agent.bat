@echo off
REM Quick Stop MyGest Agent Auto-Detection
REM Arresta il servizio agent con statistiche finali

echo.
echo ===============================================
echo   Arresto MyGest Agent (Auto-Detection)
echo ===============================================
echo.

REM Verifica se il processo è attivo
wsl -d Ubuntu bash -c "pgrep -f mygest_agent_autodetect.py" >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [INFO] MyGest Agent non e' in esecuzione
    echo.
    pause
    exit /b 0
)

echo [INFO] Agent in esecuzione. Arresto in corso...
echo.

REM Arresto pulito con SIGTERM
wsl -d Ubuntu bash -c "pkill -TERM -f mygest_agent_autodetect.py"

REM Attendi arresto pulito
timeout /t 3 /nobreak >nul

REM Verifica se si è fermato
wsl -d Ubuntu bash -c "pgrep -f mygest_agent_autodetect.py" >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [OK] MyGest Agent arrestato con successo
    echo.
    echo Statistiche sessione:
    echo.
    wsl -d Ubuntu bash -c "tail -n 20 ~/.mygest-agent.log 2>/dev/null | grep -E 'Statistiche|File eliminati|Fallimenti|Auto-detected|manuale' | sed 's/^/   /'"
) else (
    echo [WARN] Arresto normale fallito. Forzatura in corso...
    wsl -d Ubuntu bash -c "pkill -9 -f mygest_agent_autodetect.py"
    timeout /t 1 /nobreak >nul
    echo [OK] MyGest Agent arrestato forzatamente
)

echo.
pause
