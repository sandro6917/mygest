# Feature: Chiusura Automatica Finestre Server

## 📋 Panoramica

Aggiunta la funzionalità di **chiusura automatica delle finestre PowerShell** quando i server vengono arrestati. Ora solo le finestre dei server in esecuzione rimangono aperte, rendendo l'ambiente di lavoro più pulito e organizzato.

## ✨ Comportamento Precedente vs Nuovo

### Prima (v1.1.0)

```
1. Avvia Django   → Apre finestra PowerShell
2. Avvia Frontend → Apre finestra PowerShell
3. Ferma Django   → Finestra rimane aperta ❌
4. Ferma Frontend → Finestra rimane aperta ❌

Risultato: 2 finestre vuote rimangono aperte
```

### Adesso (v1.2.0)

```
1. Avvia Django   → Apre finestra PowerShell
2. Avvia Frontend → Apre finestra PowerShell
3. Ferma Django   → Chiude automaticamente la finestra ✅
4. Ferma Frontend → Chiude automaticamente la finestra ✅

Risultato: Solo finestre server attivi visibili
```

## 🔧 Modifiche Tecniche

### Variabili Globali Aggiunte

```powershell
# Tracciamento PID delle finestre PowerShell
$Global:DjangoWindowPID = $null
$Global:FrontendWindowPID = $null
```

### Funzioni Modificate

#### 1. `Start-DjangoServer()`

**Prima**:
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
```

**Adesso**:
```powershell
$process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -PassThru
$Global:DjangoWindowPID = $process.Id
```

- ✅ Usa parametro `-PassThru` per ottenere l'oggetto processo
- ✅ Salva il PID in variabile globale `$Global:DjangoWindowPID`
- ✅ Mostra il PID della finestra nel messaggio di successo

#### 2. `Start-FrontendServer()`

**Prima**:
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd
```

**Adesso**:
```powershell
$process = Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -PassThru
$Global:FrontendWindowPID = $process.Id
```

- ✅ Salva il PID in variabile globale `$Global:FrontendWindowPID`

#### 3. `Stop-DjangoServer()`

**Aggiunto**:
```powershell
# Chiudi la finestra PowerShell associata
if ($Global:DjangoWindowPID) {
    Write-ColorOutput Cyan "Chiusura finestra PowerShell (PID: $Global:DjangoWindowPID)..."
    Stop-Process -Id $Global:DjangoWindowPID -Force -ErrorAction SilentlyContinue
    $Global:DjangoWindowPID = $null
}
```

- ✅ Chiude la finestra PowerShell dopo aver fermato il server
- ✅ Usa `-Force` per chiusura immediata
- ✅ Usa `-ErrorAction SilentlyContinue` per evitare errori se finestra già chiusa
- ✅ Resetta la variabile globale a `$null`
- ✅ Funziona anche se server non era in esecuzione

#### 4. `Stop-FrontendServer()`

**Aggiunto**:
```powershell
# Chiudi la finestra PowerShell associata
if ($Global:FrontendWindowPID) {
    Write-ColorOutput Cyan "Chiusura finestra PowerShell (PID: $Global:FrontendWindowPID)..."
    Stop-Process -Id $Global:FrontendWindowPID -Force -ErrorAction SilentlyContinue
    $Global:FrontendWindowPID = $null
}
```

### GUI - Funzioni Modificate

Stesse modifiche applicate a:
- `Start-Django()`
- `Start-Frontend()`
- `Stop-Django()`
- `Stop-Frontend()`

## 📝 File Modificati

1. **WSL_Server_Manager.ps1**
   - Aggiunte variabili globali `$Global:DjangoWindowPID` e `$Global:FrontendWindowPID`
   - Modificata `Start-DjangoServer()` per salvare PID finestra
   - Modificata `Start-FrontendServer()` per salvare PID finestra
   - Modificata `Stop-DjangoServer()` per chiudere finestra
   - Modificata `Stop-FrontendServer()` per chiudere finestra

2. **WSL_Server_Manager_GUI.ps1**
   - Aggiunte variabili globali `$Global:DjangoWindowPID` e `$Global:FrontendWindowPID`
   - Modificata `Start-Django()` per salvare PID finestra
   - Modificata `Start-Frontend()` per salvare PID finestra
   - Modificata `Stop-Django()` per chiudere finestra
   - Modificata `Stop-Frontend()` per chiudere finestra

## 🎯 Vantaggi

### 1. **Ambiente Più Pulito**
- ✅ Solo finestre server attivi visibili
- ✅ Nessuna finestra vuota lasciata aperta
- ✅ Facile identificare quali server sono in esecuzione

### 2. **Gestione Risorse**
- ✅ Risparmio memoria: finestre chiuse liberano risorse
- ✅ Meno processi PowerShell in background
- ✅ Taskbar meno affollata

### 3. **User Experience**
- ✅ Più intuitivo: vedi solo ciò che è attivo
- ✅ Meno confusione visiva
- ✅ Più professionale

## 🚀 Come Funziona

### Scenario 1: Avvio e Arresto Sequenziale

```powershell
# 1. Avvia Django
Start-DjangoServer
# → Apre finestra PowerShell
# → Salva PID in $Global:DjangoWindowPID

# 2. Ferma Django
Stop-DjangoServer
# → Ferma processo Django su WSL
# → Chiude finestra PowerShell (usando PID salvato)
# → Resetta $Global:DjangoWindowPID = $null
```

### Scenario 2: Riavvio

```powershell
# Menu opzione 8: Riavvia solo Django
Stop-DjangoServer        # Chiude vecchia finestra
Start-Sleep -Seconds 2
Start-DjangoServer       # Apre nuova finestra

# Risultato: 1 sola finestra (la nuova)
```

### Scenario 3: Avvio Tutti + Ferma Tutti

```powershell
# Avvia tutti
Start-DjangoServer   # Finestra 1, PID salvato
Start-FrontendServer # Finestra 2, PID salvato

# Ferma tutti
Stop-DjangoServer    # Chiude Finestra 1
Stop-FrontendServer  # Chiude Finestra 2

# Risultato: Nessuna finestra aperta
```

## 🧪 Test

### Test 1: Avvio e Arresto Singolo

1. ✅ Avvia Django → Verifica 1 finestra aperta
2. ✅ Ferma Django → Verifica finestra chiusa automaticamente

### Test 2: Avvio Multiplo e Arresto Selettivo

1. ✅ Avvia Django + Frontend → Verifica 2 finestre aperte
2. ✅ Ferma solo Django → Verifica solo finestra Django chiusa
3. ✅ Verifica finestra Frontend ancora aperta

### Test 3: Riavvio

1. ✅ Avvia Django → Verifica finestra aperta
2. ✅ Riavvia Django → Verifica vecchia finestra chiusa, nuova aperta
3. ✅ Verifica solo 1 finestra presente

### Test 4: GUI

1. ✅ Usa GUI per avviare Django
2. ✅ Usa GUI per fermare Django
3. ✅ Verifica finestra chiusa automaticamente

### Test 5: Chiusura Manuale Finestra

1. ✅ Avvia Django
2. ✅ Chiudi manualmente la finestra PowerShell (X)
3. ✅ Usa Manager per fermare Django
4. ✅ Verifica nessun errore (ErrorAction SilentlyContinue)

## 🐛 Edge Cases Gestiti

### 1. Finestra Già Chiusa

```powershell
# Se l'utente ha chiuso manualmente la finestra
Stop-Process -Id $Global:DjangoWindowPID -Force -ErrorAction SilentlyContinue
# → Nessun errore grazie a SilentlyContinue
```

### 2. PID Non Esistente

```powershell
if ($Global:DjangoWindowPID) {
    # Chiudi solo se PID esiste
}
# → Verifica prima di tentare chiusura
```

### 3. Server Non Avviato da Manager

Se avvii manualmente il server da un'altra finestra:
- ✅ `$Global:DjangoWindowPID` = `$null`
- ✅ Stop funziona comunque (ferma processo WSL)
- ✅ Nessuna finestra viene chiusa (perché non tracciata)

### 4. Crash Server

Se il server crasha:
- ✅ La finestra PowerShell mostra l'errore
- ✅ Quando fermi il server, la finestra viene chiusa
- ✅ Puoi vedere l'errore prima della chiusura

## 📊 Confronto Output

### Prima

```
Server Django arrestato con successo
# Finestra PowerShell rimane aperta con messaggio "Processo terminato"
```

### Adesso

```
Server Django arrestato con successo
Chiusura finestra PowerShell (PID: 12345)...
# Finestra PowerShell chiusa automaticamente ✅
```

## ⚠️ Note Importanti

### Limitazioni

1. **Solo finestre avviate dal Manager**: Se avvii un server manualmente da un'altra finestra, quella non verrà chiusa
2. **PID persistono solo durante la sessione**: Se chiudi e riapri il Manager, i PID salvati vengono persi
3. **Server già in esecuzione**: Se riapri il Manager con server già attivi, non avrà i PID delle finestre

### Comportamento Atteso

- ✅ **Migliore per uso normale**: Avvii/fermi server dal Manager
- ⚠️ **Limitato per server esterni**: Server avviati manualmente non vengono tracciati

## 🎉 Benefici Utente

### Prima della Feature
```
Desktop dopo 1 ora di lavoro:
[Finestra Manager]
[Finestra Django - vuota]
[Finestra Django - vuota] (da riavvio)
[Finestra Frontend - vuota]
[Finestra Frontend - vuota] (da riavvio)
...
❌ Confusione totale
```

### Con la Feature
```
Desktop dopo 1 ora di lavoro:
[Finestra Manager]
[Finestra Django - attiva] ✅
[Finestra Frontend - attiva] ✅

✅ Pulito, organizzato, chiaro
```

## 📚 Compatibilità

- ✅ Windows 10/11
- ✅ PowerShell 5.1+
- ✅ WSL2
- ✅ Tutte le distribuzioni Linux

## 🔄 Versioning

- **Versione Precedente**: 1.1.0
- **Versione Corrente**: 1.2.0
- **Data**: 15 Febbraio 2026

## 🎯 Conclusioni

Questa funzionalità migliora significativamente l'esperienza utente:

✅ **Più pulito**: Solo finestre necessarie aperte  
✅ **Più chiaro**: Vedi subito cosa è attivo  
✅ **Più efficiente**: Meno risorse sprecate  
✅ **Più professionale**: Ambiente di lavoro ordinato  

La chiusura automatica delle finestre rende il Windows Manager più intelligente e user-friendly, eliminando il fastidio di finestre vuote che si accumulano durante la giornata di lavoro.

---

**Versione**: 1.2.0  
**Feature**: Auto-close terminal windows  
**Data**: 15 Febbraio 2026  
**Autore**: GitHub Copilot + Sandro Chimenti
