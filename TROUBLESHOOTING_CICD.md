# 🔧 Troubleshooting CI/CD - GitHub Actions SSH Connection

**Data**: 19 Febbraio 2026  
**Problema**: Workflow "Test SSH Connection" fallisce con exit code 1

---

## 🔍 Diagnostica Problema

### ✅ Test Locale (FUNZIONA)

```bash
ssh -i ~/.ssh/github_actions_mygest mygest@72.62.34.249 "whoami && python --version"
# Output:
# mygest
# Python 3.11.14
```

**Conclusione**: SSH key funziona, connessione VPS OK, problema è in GitHub Actions.

---

## 🎯 Possibili Cause

### 1. ❓ Secret SSH_KEY non formattato correttamente

**Problema**: GitHub Secret potrebbe avere caratteri escaped o formato errato

**Verifica**:
- Il secret `SSH_KEY` deve contenere **esattamente** il contenuto del file privato
- Da `-----BEGIN OPENSSH PRIVATE KEY-----` a `-----END OPENSSH PRIVATE KEY-----`
- **Include le righe BEGIN/END**
- **Nessun carattere aggiuntivo** prima/dopo

**Come verificare**:
1. Vai su: https://github.com/sandro6917/mygest/settings/secrets/actions
2. Clicca su `SSH_KEY` → `Update`
3. Copia di nuovo il contenuto con:
   ```bash
   cat ~/.ssh/github_actions_mygest
   ```
4. Incolla TUTTO nel campo (con BEGIN/END)
5. Salva

---

### 2. ❓ Timeout o Network Issues

**Problema**: GitHub Actions potrebbe non riuscire a connettersi al VPS

**Verifica**:
- VPS firewall blocca connessioni da GitHub Actions IPs?
- SSH port 22 aperto?

**Test**:
```bash
# Dal VPS, controlla connessioni SSH
ssh mygest@72.62.34.249
sudo tail -f /var/log/auth.log | grep sshd
```

---

### 3. ❓ Host Key Verification

**Problema**: GitHub Actions non ha il VPS host key in known_hosts

**Soluzione**: I workflow aggiornati usano:
- `ssh-keyscan` per aggiungere host key
- `StrictHostKeyChecking=no` per disabilitare verifica

---

### 4. ❓ Permessi SSH Key

**Problema**: Permessi file chiave non corretti (deve essere 600)

**Verifica nel workflow**: Già gestito con `chmod 600 ~/.ssh/deploy_key`

---

## 🧪 Workflow di Test Disponibili

### 1️⃣ Test SSH Connection (appleboy/ssh-action)

**File**: `.github/workflows/test-ssh.yml`  
**URL**: https://github.com/sandro6917/mygest/actions/workflows/test-ssh.yml

**Features**:
- Usa action `appleboy/ssh-action@v1.2.0`
- Debug mode attivo
- Timeout 30 minuti
- Script stop on error

**Come eseguire**:
1. Vai su URL sopra
2. Clicca "Run workflow" → "Run workflow"
3. Attendi risultato

---

### 2️⃣ Test SSH Simple (native SSH)

**File**: `.github/workflows/test-ssh-simple.yml`  
**URL**: https://github.com/sandro6917/mygest/actions/workflows/test-ssh-simple.yml

**Features**:
- Usa comandi SSH nativi di Ubuntu
- Verifica secrets prima di connettersi
- ssh-keyscan per host key
- StrictHostKeyChecking=no

**Come eseguire**:
1. Vai su URL sopra
2. Clicca "Run workflow" → "Run workflow"
3. Attendi risultato

**Questo workflow ha più probabilità di successo!**

---

## 📋 Checklist Verifica Secrets

Vai su: https://github.com/sandro6917/mygest/settings/secrets/actions

Verifica che esistano questi 4 secrets:

- [ ] `SSH_HOST` = `72.62.34.249`
- [ ] `SSH_USER` = `mygest`
- [ ] `SSH_PORT` = `22`
- [ ] `SSH_KEY` = contenuto completo chiave privata (con BEGIN/END)

---

## 🔑 Come Ri-copiare SSH_KEY Correttamente

Se il workflow fallisce ancora, ricrea il secret SSH_KEY:

### Step 1: Copia chiave privata

```bash
# Mostra chiave privata
cat ~/.ssh/github_actions_mygest

# Output DEVE iniziare con:
# -----BEGIN OPENSSH PRIVATE KEY-----
# (molte righe)
# -----END OPENSSH PRIVATE KEY-----
```

### Step 2: Seleziona TUTTO l'output

- Includi la riga `-----BEGIN OPENSSH PRIVATE KEY-----`
- Includi tutte le righe in mezzo (base64)
- Includi la riga `-----END OPENSSH PRIVATE KEY-----`
- **NON aggiungere spazi o newline extra**

### Step 3: Aggiorna Secret su GitHub

1. Vai su: https://github.com/sandro6917/mygest/settings/secrets/actions
2. Clicca su `SSH_KEY`
3. Clicca "Update"
4. **Cancella tutto il contenuto vecchio**
5. Incolla la chiave copiata
6. Clicca "Update secret"

---

## 🚀 Prossimi Step

### Immediate

1. **Esegui "Test SSH Simple"** (ha più probabilità di successo):
   - https://github.com/sandro6917/mygest/actions/workflows/test-ssh-simple.yml
   - Clicca "Run workflow"

2. **Se fallisce ancora**: Verifica i log specifici del workflow:
   - Clicca sul workflow fallito
   - Clicca su "test-connection" job
   - Espandi ogni step per vedere errore esatto

3. **Se vedi errore "Permission denied"**: 
   - Ricopia SSH_KEY come descritto sopra

4. **Se vedi errore "Host key verification failed"**:
   - Il workflow "Test SSH Simple" dovrebbe risolverlo automaticamente

---

## 📊 Debug Avanzato

### Test SSH_KEY Format

Crea file test locale:

```bash
# Copia secret da GitHub in file temporaneo
nano /tmp/test_key

# Incolla il contenuto del secret SSH_KEY da GitHub
# Salva (Ctrl+O, Enter, Ctrl+X)

# Testa la chiave
chmod 600 /tmp/test_key
ssh -i /tmp/test_key mygest@72.62.34.249 "whoami"

# Se funziona → secret OK
# Se fallisce → secret corrotto, ricrealo
```

### Verifica Logs VPS

Mentre esegui il workflow, monitora i log SSH sul VPS:

```bash
# Terminal 1: Esegui workflow su GitHub
# Terminal 2: Sul VPS
ssh mygest@72.62.34.249
sudo tail -f /var/log/auth.log
```

Cerca righe come:
- `Accepted publickey for mygest from X.X.X.X` → ✅ SSH OK
- `Connection closed by X.X.X.X [preauth]` → ❌ Auth failed
- `Failed publickey for mygest from X.X.X.X` → ❌ Chiave errata

---

## ✅ Quando Risolto

Una volta che uno dei workflow passa:

1. Aggiorna questo documento con la soluzione
2. Testa workflow "Deploy to Production"
3. Risolvi problema `ai_classifier` (opzionale per ora)

---

## 📞 Se Nulla Funziona

**Opzioni**:

1. **Rigenera chiave SSH completa**:
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-new@mygest" -f ~/.ssh/github_actions_mygest_new
   # Aggiungi public key su VPS
   # Aggiorna secret SSH_KEY su GitHub
   ```

2. **Usa deploy key di GitHub** (alternativa):
   - Genera chiave sul VPS
   - Aggiungila come Deploy Key nel repo
   - Modifica workflow per usare deploy key

3. **Usa GitHub Hosted Runner self-hosted** (alternativa avanzata):
   - Installa runner direttamente sul VPS
   - Evita problemi SSH
   - Più costoso in termini di setup

---

**Ultimo aggiornamento**: 19 Feb 2026 - Workflow test-ssh-simple.yml creato  
**Commit**: `07af858`
