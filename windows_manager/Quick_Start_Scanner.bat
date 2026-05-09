@echo off
REM Quick Start Scanner Service
REM Avvia il servizio di gestione scanner per scansioni da MyGest

echo.
echo ====================================
echo   Avvio Scanner Service MyGest
echo ====================================
echo.

REM Esegui script daemon wrapper per avvio scanner
REM Reindirizza stderr per evitare messaggi di errore di mount
wsl -d Ubuntu bash -c "/home/sandro/mygest/scripts/start_scanner_daemon.sh" 2>nul

REM Attendi qualche secondo per permettere l'avvio
timeout /t 4 /nobreak >nul

REM Verifica se il processo è attivo
wsl -d Ubuntu bash -c "pgrep -f scanner_service.py" >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [OK] Scanner Service avviato con successo
    echo.
    echo Il servizio e' disponibile su: http://localhost:8765
    echo Log disponibile in: logs/scanner_service.log
    echo.
    echo Verifica dello stato...
    curl -s http://localhost:8765/health >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Health check positivo - servizio operativo
    ) else (
        echo [WARN] Servizio avviato ma health check non disponibile
        echo       Il servizio potrebbe essere ancora in fase di avvio
    )
) else (
    echo [ERRORE] Impossibile avviare Scanner Service
    echo Controlla i log in logs/scanner_service.log per maggiori dettagli
)

echo.
pause
