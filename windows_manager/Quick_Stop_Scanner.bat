@echo off
REM Quick Stop Scanner Service
REM Ferma il servizio di gestione scanner

echo.
echo ====================================
echo   Arresto Scanner Service MyGest
echo ====================================
echo.

REM Trova e termina il processo scanner_service.py
wsl -d Ubuntu bash -c "pkill -f 'python.*scanner_service.py'"

if %ERRORLEVEL% EQU 0 (
    echo [OK] Scanner Service arrestato con successo
) else (
    echo [INFO] Nessun processo Scanner Service trovato o gia' arrestato
)

echo.
pause
