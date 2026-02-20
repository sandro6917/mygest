# WSL Server Manager - Versione GUI
# Interfaccia grafica semplificata con Windows Forms

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Configurazione
$WSL_DISTRO = "Ubuntu-22.04"  # Cambia con il nome della tua distribuzione WSL
$PROJECT_PATH = "/home/sandro/mygest"
$DJANGO_PORT = 8000
$FRONTEND_PORT = 5173
$SSH_PORT = 22  # Porta SSH standard

# Variabili globali per tracciare i PID delle finestre PowerShell
$Global:DjangoWindowPID = $null
$Global:FrontendWindowPID = $null

# Funzioni di controllo
function Get-DjangoStatus {
    $processId = wsl -d $WSL_DISTRO bash -c "pgrep -f 'manage.py runserver'"
    return [bool]$processId
}

function Get-FrontendStatus {
    $processId = wsl -d $WSL_DISTRO bash -c "pgrep -f 'vite'"
    return [bool]$processId
}

function Get-SSHStatus {
    $result = wsl -d $WSL_DISTRO bash -c "systemctl is-active ssh 2>/dev/null || service ssh status 2>/dev/null | grep -q 'running' && echo 'active' || echo 'inactive'"
    return ($result -eq "active")
}

function Start-Django {
    $cmd = "wsl -d $WSL_DISTRO bash -c 'cd $PROJECT_PATH && source venv/bin/activate 2>/dev/null || true && python manage.py runserver 0.0.0.0:$DJANGO_PORT'"
    $process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -PassThru
    $Global:DjangoWindowPID = $process.Id
    Start-Sleep -Seconds 2
}

function Start-Frontend {
    $cmd = "wsl -d $WSL_DISTRO bash -c 'cd $PROJECT_PATH/frontend && npm run dev -- --host 0.0.0.0'"
    $process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -PassThru
    $Global:FrontendWindowPID = $process.Id
    Start-Sleep -Seconds 2
}

function Stop-Django {
    $processId = wsl -d $WSL_DISTRO bash -c "pgrep -f 'manage.py runserver'"
    if ($processId) {
        wsl -d $WSL_DISTRO bash -c "kill $processId 2>/dev/null"
        Start-Sleep -Seconds 1
    }
    # Chiudi la finestra PowerShell associata
    if ($Global:DjangoWindowPID) {
        Stop-Process -Id $Global:DjangoWindowPID -Force -ErrorAction SilentlyContinue
        $Global:DjangoWindowPID = $null
    }
}

function Stop-Frontend {
    $processId = wsl -d $WSL_DISTRO bash -c "pgrep -f 'vite'"
    if ($processId) {
        wsl -d $WSL_DISTRO bash -c "kill $processId 2>/dev/null"
        Start-Sleep -Seconds 1
    }
    # Chiudi la finestra PowerShell associata
    if ($Global:FrontendWindowPID) {
        Stop-Process -Id $Global:FrontendWindowPID -Force -ErrorAction SilentlyContinue
        $Global:FrontendWindowPID = $null
    }
}

function Start-SSH {
    wsl -d $WSL_DISTRO bash -c "sudo systemctl start ssh 2>/dev/null || sudo service ssh start 2>/dev/null"
    Start-Sleep -Seconds 2
}

function Stop-SSH {
    wsl -d $WSL_DISTRO bash -c "sudo systemctl stop ssh 2>/dev/null || sudo service ssh stop 2>/dev/null"
    Start-Sleep -Seconds 1
}

function Restart-SSH {
    wsl -d $WSL_DISTRO bash -c "sudo systemctl restart ssh 2>/dev/null || sudo service ssh restart 2>/dev/null"
    Start-Sleep -Seconds 2
}

function Update-Status {
    $djangoRunning = Get-DjangoStatus
    $frontendRunning = Get-FrontendStatus
    $sshRunning = Get-SSHStatus
    
    if ($djangoRunning) {
        $labelDjangoStatus.Text = "● ATTIVO"
        $labelDjangoStatus.ForeColor = [System.Drawing.Color]::Green
        $btnStartDjango.Enabled = $false
        $btnStopDjango.Enabled = $true
    } else {
        $labelDjangoStatus.Text = "○ FERMO"
        $labelDjangoStatus.ForeColor = [System.Drawing.Color]::Red
        $btnStartDjango.Enabled = $true
        $btnStopDjango.Enabled = $false
    }
    
    if ($frontendRunning) {
        $labelFrontendStatus.Text = "● ATTIVO"
        $labelFrontendStatus.ForeColor = [System.Drawing.Color]::Green
        $btnStartFrontend.Enabled = $false
        $btnStopFrontend.Enabled = $true
    } else {
        $labelFrontendStatus.Text = "○ FERMO"
        $labelFrontendStatus.ForeColor = [System.Drawing.Color]::Red
        $btnStartFrontend.Enabled = $true
        $btnStopFrontend.Enabled = $false
    }
    
    if ($sshRunning) {
        $labelSSHStatus.Text = "● ATTIVO"
        $labelSSHStatus.ForeColor = [System.Drawing.Color]::Green
        $btnStartSSH.Enabled = $false
        $btnStopSSH.Enabled = $true
    } else {
        $labelSSHStatus.Text = "○ FERMO"
        $labelSSHStatus.ForeColor = [System.Drawing.Color]::Red
        $btnStartSSH.Enabled = $true
        $btnStopSSH.Enabled = $false
    }
    
    # Aggiorna pulsanti globali
    $btnStartAll.Enabled = -not ($djangoRunning -and $frontendRunning)
    $btnStopAll.Enabled = $djangoRunning -or $frontendRunning
}

# Crea la finestra principale
$form = New-Object System.Windows.Forms.Form
$form.Text = "WSL Server Manager - MyGest"
$form.Size = New-Object System.Drawing.Size(500, 600)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 240)

# Font
$fontTitle = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fontNormal = New-Object System.Drawing.Font("Segoe UI", 10)
$fontButton = New-Object System.Drawing.Font("Segoe UI", 9)

# Titolo
$labelTitle = New-Object System.Windows.Forms.Label
$labelTitle.Location = New-Object System.Drawing.Point(20, 20)
$labelTitle.Size = New-Object System.Drawing.Size(460, 30)
$labelTitle.Text = "🖥️ Gestione Server WSL"
$labelTitle.Font = $fontTitle
$labelTitle.TextAlign = "MiddleCenter"
$form.Controls.Add($labelTitle)

# Separatore
$separator1 = New-Object System.Windows.Forms.Label
$separator1.Location = New-Object System.Drawing.Point(20, 55)
$separator1.Size = New-Object System.Drawing.Size(460, 2)
$separator1.BorderStyle = "Fixed3D"
$form.Controls.Add($separator1)

# === DJANGO SECTION ===
$y = 70

$labelDjango = New-Object System.Windows.Forms.Label
$labelDjango.Location = New-Object System.Drawing.Point(30, $y)
$labelDjango.Size = New-Object System.Drawing.Size(200, 25)
$labelDjango.Text = "Django Server (Port $DJANGO_PORT)"
$labelDjango.Font = $fontNormal
$form.Controls.Add($labelDjango)

$labelDjangoStatus = New-Object System.Windows.Forms.Label
$labelDjangoStatus.Location = New-Object System.Drawing.Point(350, $y)
$labelDjangoStatus.Size = New-Object System.Drawing.Size(120, 25)
$labelDjangoStatus.Text = "○ FERMO"
$labelDjangoStatus.Font = $fontNormal
$labelDjangoStatus.ForeColor = [System.Drawing.Color]::Red
$labelDjangoStatus.TextAlign = "MiddleRight"
$form.Controls.Add($labelDjangoStatus)

$y += 35

$btnStartDjango = New-Object System.Windows.Forms.Button
$btnStartDjango.Location = New-Object System.Drawing.Point(30, $y)
$btnStartDjango.Size = New-Object System.Drawing.Size(100, 30)
$btnStartDjango.Text = "▶ Avvia"
$btnStartDjango.Font = $fontButton
$btnStartDjango.BackColor = [System.Drawing.Color]::FromArgb(76, 175, 80)
$btnStartDjango.ForeColor = [System.Drawing.Color]::White
$btnStartDjango.FlatStyle = "Flat"
$btnStartDjango.Add_Click({
    Start-Django
    Update-Status
})
$form.Controls.Add($btnStartDjango)

$btnStopDjango = New-Object System.Windows.Forms.Button
$btnStopDjango.Location = New-Object System.Drawing.Point(140, $y)
$btnStopDjango.Size = New-Object System.Drawing.Size(100, 30)
$btnStopDjango.Text = "⏹ Ferma"
$btnStopDjango.Font = $fontButton
$btnStopDjango.BackColor = [System.Drawing.Color]::FromArgb(244, 67, 54)
$btnStopDjango.ForeColor = [System.Drawing.Color]::White
$btnStopDjango.FlatStyle = "Flat"
$btnStopDjango.Enabled = $false
$btnStopDjango.Add_Click({
    Stop-Django
    Update-Status
})
$form.Controls.Add($btnStopDjango)

$btnRestartDjango = New-Object System.Windows.Forms.Button
$btnRestartDjango.Location = New-Object System.Drawing.Point(250, $y)
$btnRestartDjango.Size = New-Object System.Drawing.Size(100, 30)
$btnRestartDjango.Text = "🔄 Riavvia"
$btnRestartDjango.Font = $fontButton
$btnRestartDjango.BackColor = [System.Drawing.Color]::FromArgb(33, 150, 243)
$btnRestartDjango.ForeColor = [System.Drawing.Color]::White
$btnRestartDjango.FlatStyle = "Flat"
$btnRestartDjango.Add_Click({
    Stop-Django
    Start-Sleep -Seconds 2
    Start-Django
    Update-Status
})
$form.Controls.Add($btnRestartDjango)

# === FRONTEND SECTION ===
$y += 50

$separator2 = New-Object System.Windows.Forms.Label
$separator2.Location = New-Object System.Drawing.Point(20, $y)
$separator2.Size = New-Object System.Drawing.Size(460, 2)
$separator2.BorderStyle = "Fixed3D"
$form.Controls.Add($separator2)

$y += 15

$labelFrontend = New-Object System.Windows.Forms.Label
$labelFrontend.Location = New-Object System.Drawing.Point(30, $y)
$labelFrontend.Size = New-Object System.Drawing.Size(200, 25)
$labelFrontend.Text = "Frontend Server (Port $FRONTEND_PORT)"
$labelFrontend.Font = $fontNormal
$form.Controls.Add($labelFrontend)

$labelFrontendStatus = New-Object System.Windows.Forms.Label
$labelFrontendStatus.Location = New-Object System.Drawing.Point(350, $y)
$labelFrontendStatus.Size = New-Object System.Drawing.Size(120, 25)
$labelFrontendStatus.Text = "○ FERMO"
$labelFrontendStatus.Font = $fontNormal
$labelFrontendStatus.ForeColor = [System.Drawing.Color]::Red
$labelFrontendStatus.TextAlign = "MiddleRight"
$form.Controls.Add($labelFrontendStatus)

$y += 35

$btnStartFrontend = New-Object System.Windows.Forms.Button
$btnStartFrontend.Location = New-Object System.Drawing.Point(30, $y)
$btnStartFrontend.Size = New-Object System.Drawing.Size(100, 30)
$btnStartFrontend.Text = "▶ Avvia"
$btnStartFrontend.Font = $fontButton
$btnStartFrontend.BackColor = [System.Drawing.Color]::FromArgb(76, 175, 80)
$btnStartFrontend.ForeColor = [System.Drawing.Color]::White
$btnStartFrontend.FlatStyle = "Flat"
$btnStartFrontend.Add_Click({
    Start-Frontend
    Update-Status
})
$form.Controls.Add($btnStartFrontend)

$btnStopFrontend = New-Object System.Windows.Forms.Button
$btnStopFrontend.Location = New-Object System.Drawing.Point(140, $y)
$btnStopFrontend.Size = New-Object System.Drawing.Size(100, 30)
$btnStopFrontend.Text = "⏹ Ferma"
$btnStopFrontend.Font = $fontButton
$btnStopFrontend.BackColor = [System.Drawing.Color]::FromArgb(244, 67, 54)
$btnStopFrontend.ForeColor = [System.Drawing.Color]::White
$btnStopFrontend.FlatStyle = "Flat"
$btnStopFrontend.Enabled = $false
$btnStopFrontend.Add_Click({
    Stop-Frontend
    Update-Status
})
$form.Controls.Add($btnStopFrontend)

$btnRestartFrontend = New-Object System.Windows.Forms.Button
$btnRestartFrontend.Location = New-Object System.Drawing.Point(250, $y)
$btnRestartFrontend.Size = New-Object System.Drawing.Size(100, 30)
$btnRestartFrontend.Text = "🔄 Riavvia"
$btnRestartFrontend.Font = $fontButton
$btnRestartFrontend.BackColor = [System.Drawing.Color]::FromArgb(33, 150, 243)
$btnRestartFrontend.ForeColor = [System.Drawing.Color]::White
$btnRestartFrontend.FlatStyle = "Flat"
$btnRestartFrontend.Add_Click({
    Stop-Frontend
    Start-Sleep -Seconds 2
    Start-Frontend
    Update-Status
})
$form.Controls.Add($btnRestartFrontend)

# === SSH SECTION ===
$y += 50

$separator3 = New-Object System.Windows.Forms.Label
$separator3.Location = New-Object System.Drawing.Point(20, $y)
$separator3.Size = New-Object System.Drawing.Size(460, 2)
$separator3.BorderStyle = "Fixed3D"
$form.Controls.Add($separator3)

$y += 15

$labelSSH = New-Object System.Windows.Forms.Label
$labelSSH.Location = New-Object System.Drawing.Point(30, $y)
$labelSSH.Size = New-Object System.Drawing.Size(200, 25)
$labelSSH.Text = "SSH Server (Porta $SSH_PORT)"
$labelSSH.Font = $fontNormal
$form.Controls.Add($labelSSH)

$labelSSHStatus = New-Object System.Windows.Forms.Label
$labelSSHStatus.Location = New-Object System.Drawing.Point(350, $y)
$labelSSHStatus.Size = New-Object System.Drawing.Size(120, 25)
$labelSSHStatus.Text = "○ FERMO"
$labelSSHStatus.Font = $fontNormal
$labelSSHStatus.ForeColor = [System.Drawing.Color]::Red
$labelSSHStatus.TextAlign = "MiddleRight"
$form.Controls.Add($labelSSHStatus)

$y += 35

$btnStartSSH = New-Object System.Windows.Forms.Button
$btnStartSSH.Location = New-Object System.Drawing.Point(30, $y)
$btnStartSSH.Size = New-Object System.Drawing.Size(100, 30)
$btnStartSSH.Text = "▶ Avvia"
$btnStartSSH.Font = $fontButton
$btnStartSSH.BackColor = [System.Drawing.Color]::FromArgb(76, 175, 80)
$btnStartSSH.ForeColor = [System.Drawing.Color]::White
$btnStartSSH.FlatStyle = "Flat"
$btnStartSSH.Add_Click({
    Start-SSH
    Update-Status
})
$form.Controls.Add($btnStartSSH)

$btnStopSSH = New-Object System.Windows.Forms.Button
$btnStopSSH.Location = New-Object System.Drawing.Point(140, $y)
$btnStopSSH.Size = New-Object System.Drawing.Size(100, 30)
$btnStopSSH.Text = "⏹ Ferma"
$btnStopSSH.Font = $fontButton
$btnStopSSH.BackColor = [System.Drawing.Color]::FromArgb(244, 67, 54)
$btnStopSSH.ForeColor = [System.Drawing.Color]::White
$btnStopSSH.FlatStyle = "Flat"
$btnStopSSH.Enabled = $false
$btnStopSSH.Add_Click({
    Stop-SSH
    Update-Status
})
$form.Controls.Add($btnStopSSH)

$btnRestartSSH = New-Object System.Windows.Forms.Button
$btnRestartSSH.Location = New-Object System.Drawing.Point(250, $y)
$btnRestartSSH.Size = New-Object System.Drawing.Size(100, 30)
$btnRestartSSH.Text = "🔄 Riavvia"
$btnRestartSSH.Font = $fontButton
$btnRestartSSH.BackColor = [System.Drawing.Color]::FromArgb(33, 150, 243)
$btnRestartSSH.ForeColor = [System.Drawing.Color]::White
$btnRestartSSH.FlatStyle = "Flat"
$btnRestartSSH.Add_Click({
    Restart-SSH
    Update-Status
})
$form.Controls.Add($btnRestartSSH)

# === GLOBAL ACTIONS ===
$y += 50

$separator4 = New-Object System.Windows.Forms.Label
$separator4.Location = New-Object System.Drawing.Point(20, $y)
$separator4.Size = New-Object System.Drawing.Size(460, 2)
$separator4.BorderStyle = "Fixed3D"
$form.Controls.Add($separator4)

$y += 15

$btnStartAll = New-Object System.Windows.Forms.Button
$btnStartAll.Location = New-Object System.Drawing.Point(30, $y)
$btnStartAll.Size = New-Object System.Drawing.Size(140, 35)
$btnStartAll.Text = "▶ Avvia Tutto"
$btnStartAll.Font = $fontButton
$btnStartAll.BackColor = [System.Drawing.Color]::FromArgb(76, 175, 80)
$btnStartAll.ForeColor = [System.Drawing.Color]::White
$btnStartAll.FlatStyle = "Flat"
$btnStartAll.Add_Click({
    Start-Django
    Start-Frontend
    Update-Status
})
$form.Controls.Add($btnStartAll)

$btnStopAll = New-Object System.Windows.Forms.Button
$btnStopAll.Location = New-Object System.Drawing.Point(180, $y)
$btnStopAll.Size = New-Object System.Drawing.Size(140, 35)
$btnStopAll.Text = "⏹ Ferma Tutto"
$btnStopAll.Font = $fontButton
$btnStopAll.BackColor = [System.Drawing.Color]::FromArgb(244, 67, 54)
$btnStopAll.ForeColor = [System.Drawing.Color]::White
$btnStopAll.FlatStyle = "Flat"
$btnStopAll.Enabled = $false
$btnStopAll.Add_Click({
    Stop-Django
    Stop-Frontend
    Update-Status
})
$form.Controls.Add($btnStopAll)

$btnRefresh = New-Object System.Windows.Forms.Button
$btnRefresh.Location = New-Object System.Drawing.Point(330, $y)
$btnRefresh.Size = New-Object System.Drawing.Size(140, 35)
$btnRefresh.Text = "🔄 Aggiorna"
$btnRefresh.Font = $fontButton
$btnRefresh.BackColor = [System.Drawing.Color]::FromArgb(158, 158, 158)
$btnRefresh.ForeColor = [System.Drawing.Color]::White
$btnRefresh.FlatStyle = "Flat"
$btnRefresh.Add_Click({
    Update-Status
})
$form.Controls.Add($btnRefresh)

# Timer per aggiornamento automatico ogni 5 secondi
$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 5000
$timer.Add_Tick({ Update-Status })
$timer.Start()

# Aggiorna stato iniziale
Update-Status

# Mostra la finestra
[void]$form.ShowDialog()

# Cleanup
$timer.Stop()
$form.Dispose()
