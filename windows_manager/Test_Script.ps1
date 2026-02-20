# Test rapido dello script GUI - versione corretta
# Questo file testa solo le funzioni base senza avviare la GUI

# Configurazione
$WSL_DISTRO = "Ubuntu-22.04"
$PROJECT_PATH = "/home/sandro/mygest"

# Test funzioni base
Write-Host "Test 1: Verifica WSL..." -ForegroundColor Cyan
$wslTest = wsl -d $WSL_DISTRO echo "OK"
if ($wslTest -eq "OK") {
    Write-Host "  [OK] WSL funziona correttamente" -ForegroundColor Green
} else {
    Write-Host "  [ERRORE] WSL non risponde" -ForegroundColor Red
    exit 1
}

Write-Host "`nTest 2: Verifica progetto..." -ForegroundColor Cyan
$projectTest = wsl -d $WSL_DISTRO test -d $PROJECT_PATH
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Progetto trovato" -ForegroundColor Green
} else {
    Write-Host "  [ERRORE] Progetto non trovato" -ForegroundColor Red
    exit 1
}

Write-Host "`nTest 3: Verifica stato processi..." -ForegroundColor Cyan
$djangoProcessId = wsl -d $WSL_DISTRO bash -c "pgrep -f 'manage.py runserver'"
$frontendProcessId = wsl -d $WSL_DISTRO bash -c "pgrep -f 'vite'"

if ($djangoProcessId) {
    Write-Host "  Django: IN ESECUZIONE (PID: $djangoProcessId)" -ForegroundColor Yellow
} else {
    Write-Host "  Django: FERMO" -ForegroundColor Gray
}

if ($frontendProcessId) {
    Write-Host "  Frontend: IN ESECUZIONE (PID: $frontendProcessId)" -ForegroundColor Yellow
} else {
    Write-Host "  Frontend: FERMO" -ForegroundColor Gray
}

Write-Host "`n[OK] Tutti i test base sono passati!" -ForegroundColor Green
Write-Host "Gli script dovrebbero funzionare correttamente." -ForegroundColor Green
