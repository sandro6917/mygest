@echo off
REM Quick Start MyGest Agent Auto-Detection
REM Avvia il servizio agent per eliminazione automatica file

echo.
echo ===============================================
echo   Avvio MyGest Agent (Auto-Detection)
echo ===============================================
echo.

REM Verifica configurazione
wsl -d Ubuntu bash -c "test -f ~/.mygest-agent.conf && echo exists" >temp_check.txt 2>nul
set /p CONFIG_EXISTS=<temp_check.txt
del temp_check.txt 2>nul

if not "%CONFIG_EXISTS%"=="exists" (
    echo [ERRORE] File configurazione non trovato: ~/.mygest-agent.conf
    echo.
    echo Crea la configurazione con:
    echo   wsl cp /home/sandro/mygest/config/mygest-agent.conf.example ~/.mygest-agent.conf
    echo.
    echo Poi modifica ~/.mygest-agent.conf con il tuo token API
    echo.
    pause
    exit /b 1
)

echo [INFO] Configurazione trovata: ~/.mygest-agent.conf
echo.

REM Verifica watchdog installato
wsl -d Ubuntu bash -c "cd /home/sandro/mygest && source venv/bin/activate 2>/dev/null && python -c 'import watchdog' 2>/dev/null && echo ok || echo missing" >temp_watchdog.txt 2>nul
set /p WATCHDOG_STATUS=<temp_watchdog.txt
del temp_watchdog.txt 2>nul

if not "%WATCHDOG_STATUS%"=="ok" (
    echo [WARN] Watchdog non installato. Installazione in corso...
    wsl -d Ubuntu bash -c "cd /home/sandro/mygest && source venv/bin/activate 2>/dev/null && pip install -q watchdog"
    echo [OK] Watchdog installato
    echo.
)

# Crea directory log se non esiste
wsl -d Ubuntu bash -c "mkdir -p /home/sandro/mygest/logs" 2>nul

REM Esegui script daemon wrapper per avvio agent
wsl -d Ubuntu bash -c "/home/sandro/mygest/scripts/start_agent_daemon.sh" 2>nul

REM Attendi qualche secondo per permettere l'avvio
timeout /t 4 /nobreak >nul

REM Verifica se il processo è attivo
wsl -d Ubuntu bash -c "pgrep -f mygest_agent_autodetect.py" >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [OK] MyGest Agent avviato con successo
    echo.
    
    REM Mostra info configurazione
    echo Informazioni configurazione:
    echo.
    
    wsl -d Ubuntu bash -c "grep '^monitor_' ~/.mygest-agent.conf 2>/dev/null | grep -v '^#' | wc -l" >temp_folders.txt 2>nul
    set /p NUM_FOLDERS=<temp_folders.txt
    del temp_folders.txt 2>nul
    
    echo   Cartelle monitorate: %NUM_FOLDERS%
    wsl -d Ubuntu bash -c "grep '^monitor_' ~/.mygest-agent.conf 2>/dev/null | grep -v '^#' | cut -d'=' -f2 | sed 's/^/     - /'"
    echo.
    echo   Log agent: ~/.mygest-agent.log
    echo   Log servizio: logs/agent_autodetect.log
    echo.
    echo Ultimi log agent:
    timeout /t 2 /nobreak >nul
    wsl -d Ubuntu bash -c "tail -n 5 ~/.mygest-agent.log 2>/dev/null | sed 's/^/   /'"
    echo.
    echo [INFO] Agent operativo e in ascolto delle richieste di eliminazione
) else (
    echo [ERRORE] Impossibile avviare MyGest Agent
    echo.
    echo Controlla i log per maggiori dettagli:
    echo   - ~/.mygest-agent.log
    echo   - logs/agent_autodetect.log
    echo.
    echo Debug info:
    wsl -d Ubuntu bash -c "tail -n 10 logs/agent_autodetect.log 2>/dev/null"
)

echo.
pause
