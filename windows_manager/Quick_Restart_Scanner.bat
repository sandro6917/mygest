@echo off
REM Quick Restart Scanner Service
REM Riavvia il servizio di gestione scanner

echo.
echo ====================================
echo   Riavvio Scanner Service MyGest
echo ====================================
echo.

echo Arresto Scanner Service in corso...
wsl -d Ubuntu bash -c "pkill -f 'scanner_service.py'" 2>nul
timeout /t 2 /nobreak >nul

echo Avvio Scanner Service in corso...
wsl -d Ubuntu bash -c "cd /home/sandro/mygest && source venv/bin/activate 2>/dev/null && nohup python scripts/scanner_service.py > logs/scanner_service.log 2>&1 < /dev/null &" 2>nul

REM Attendi l'avvio
timeout /t 3 /nobreak >nul

REM Verifica se il processo è attivo
wsl -d Ubuntu bash -c "pgrep -f scanner_service.py" >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [OK] Scanner Service riavviato con successo
    echo.
    echo Il servizio e' disponibile su: http://localhost:8765
    echo.
    echo Verifica dello stato...
    curl -s http://localhost:8765/health >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Health check positivo - servizio operativo
    ) else (
        echo [WARN] Servizio avviato ma health check non disponibile
    )
) else (
    echo [ERRORE] Impossibile riavviare Scanner Service
    echo Controlla i log in logs/scanner_service.log
)

echo.
pause
