# 🔍 Verifica Sincronizzazione Google Calendar - MyGest

**Data verifica**: 2 Febbraio 2026  
**Stato**: ❌ **NON FUNZIONANTE** - Configurazione incompleta

---

## 📋 Cosa Manca per Far Funzionare la Sincronizzazione

### ❌ **PROBLEMA 1: Tipo di Credenziali Sbagliato**

**Situazione attuale:**
- File presente: `/home/sandro/mygest/secrets/google-calendar.json`
- Tipo credenziali: **OAuth 2.0 Client ID** (tipo `web`)
- Richiesto: **Service Account** (tipo `service_account`)

**Perché non funziona:**
Il file contiene credenziali OAuth2 per applicazioni web (`"web":{"client_id"...}`), mentre la sincronizzazione automatica richiede un **Service Account** che può operare senza interazione utente.

**File attuale:**
```json
{
  "web": {
    "client_id": "854310708609-co4i3kmiojgdp83nsmmbs3n4oknjh5ou...",
    "project_id": "mygest-478007",
    "client_secret": "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"
  }
}
```

**File richiesto (esempio):**
```json
{
  "type": "service_account",
  "project_id": "mygest-478007",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "mygest-calendar@mygest-478007.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
}
```

---

### ❌ **PROBLEMA 2: Librerie Google Non Installate**

**Librerie mancanti:**
```
google-api-python-client  # Client per Google Calendar API
google-auth              # Autenticazione Google
google-auth-oauthlib     # OAuth flow (opzionale)
google-auth-httplib2     # HTTP transport
```

**Verifica in `requirements.txt`:**
- ❌ Nessuna libreria Google presente
- ✅ C'è solo un commento: `# google-cloud-storage==2.18.2` (commentato)

---

### ⚠️ **PROBLEMA 3: Signal Disabilitati**

**File:** `/home/sandro/mygest/scadenze/models.py` (righe 594-598)

**Stato attuale:**
```python
# Google Calendar sync temporaneamente disabilitato
# Per riabilitare, decommentare le righe seguenti e configurare le credenziali Google
# (vedi docs/GOOGLE_CALENDAR_SETUP.md per istruzioni complete)
# post_save.connect(_sync_calendar_after_save, sender=ScadenzaOccorrenza, ...)
# post_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza, ...)
```

**Impatto:**
Anche con credenziali corrette, la sincronizzazione **NON è automatica** perché i signal Django sono commentati.

---

### ✅ **Cosa Funziona Già**

1. **Configurazione Settings**:
   - ✅ `GOOGLE_CALENDAR_CREDENTIALS_FILE` configurato
   - ✅ `GOOGLE_CALENDAR_DEFAULT_ID` configurato
   - ✅ Path corretti in `settings_local.py`

2. **Codice di Sincronizzazione**:
   - ✅ Classe `GoogleCalendarSync` implementata (`scadenze/services.py`)
   - ✅ Metodi `upsert_occurrence()` e `delete_occurrence()` pronti
   - ✅ Log tracking con `ScadenzaNotificaLog`

3. **Database**:
   - ✅ Campo `google_calendar_event_id` su `ScadenzaOccorrenza`
   - ✅ Campo `google_calendar_synced_at` per tracking
   - ✅ Campo `google_calendar_calendar_id` su `Scadenza`

4. **Script di Verifica**:
   - ✅ `check_google_calendar_config.py` disponibile
   - ✅ Documentazione completa in `docs/GOOGLE_CALENDAR_SETUP.md`

---

## 🔧 Passi per Abilitare la Sincronizzazione

### **PASSO 1: Crea Service Account Google**

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Seleziona progetto `mygest-478007` (già esistente!)
3. Vai su **APIs & Services** > **Credentials**
4. Clicca **Create Credentials** > **Service Account**
5. Nome: `mygest-calendar-sync`
6. Ruolo: (opzionale, non necessario)
7. Clicca **Done**

### **PASSO 2: Genera Chiave JSON del Service Account**

1. Clicca sul service account appena creato
2. Vai su tab **Keys**
3. Clicca **Add Key** > **Create new key**
4. Tipo: **JSON**
5. Clicca **Create** → scarica il file

### **PASSO 3: Sostituisci il File Credenziali**

```bash
# Backup del file attuale (sbagliato)
cd /home/sandro/mygest/secrets
mv google-calendar.json google-calendar.json.backup

# Copia il nuovo file (service account)
cp ~/Downloads/mygest-478007-*.json google-calendar.json

# Verifica che sia un service account
cat google-calendar.json | grep '"type"'
# Output atteso: "type": "service_account"

# Permessi corretti
chmod 600 google-calendar.json
```

### **PASSO 4: Abilita Google Calendar API**

1. In Google Cloud Console
2. **APIs & Services** > **Library**
3. Cerca "Google Calendar API"
4. Clicca **Enable** (se non già abilitata)

### **PASSO 5: Condividi Calendario con Service Account**

1. Apri [Google Calendar](https://calendar.google.com/)
2. Vai su **Settings** > **Settings for my calendars**
3. Seleziona il calendario da usare
4. Clicca **Share with specific people**
5. Aggiungi l'email del service account (es: `mygest-calendar@mygest-478007.iam.gserviceaccount.com`)
   - Trovi l'email nel file JSON, campo `client_email`
6. Permessi: **Make changes to events**
7. Clicca **Send**

### **PASSO 6: Installa Librerie Google**

```bash
cd /home/sandro/mygest
source venv/bin/activate

# Installa dipendenze Google
pip install google-api-python-client google-auth google-auth-httplib2
```

**Aggiungi al `requirements.txt`:**
```txt
# Google Calendar API
google-api-python-client==2.153.0
google-auth==2.36.0
google-auth-httplib2==0.2.0
```

### **PASSO 7: Verifica Configurazione**

```bash
cd /home/sandro/mygest
source venv/bin/activate
python check_google_calendar_config.py
```

**Output atteso:**
```
✅ CONFIGURAZIONE OK!

Prossimi passi:
1. Assicurati di aver condiviso il calendario con:
   mygest-calendar@mygest-478007.iam.gserviceaccount.com

2. Testa la sincronizzazione con:
   python manage.py sync_google_calendar --dry-run
```

### **PASSO 8: Abilita Signal di Sincronizzazione Automatica**

Modifica `/home/sandro/mygest/scadenze/models.py` (righe finali):

**DA:**
```python
# Google Calendar sync temporaneamente disabilitato
# Per riabilitare, decommentare le righe seguenti e configurare le credenziali Google
# (vedi docs/GOOGLE_CALENDAR_SETUP.md per istruzioni complete)
# post_save.connect(_sync_calendar_after_save, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_sync_google")
# post_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_delete_google")
```

**A:**
```python
# Google Calendar sync ABILITATO
post_save.connect(_sync_calendar_after_save, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_sync_google")
post_delete.connect(_delete_calendar_event, sender=ScadenzaOccorrenza, dispatch_uid="scadenze_delete_google")
```

### **PASSO 9: Riavvia Server**

```bash
# Development
cd /home/sandro/mygest
source venv/bin/activate
python manage.py runserver

# Production (se su VPS)
sudo systemctl restart mygest
```

### **PASSO 10: Sincronizza Occorrenze Esistenti**

```bash
# Test senza modifiche (dry-run)
python manage.py sync_google_calendar --dry-run

# Sincronizza tutte le occorrenze future
python manage.py sync_google_calendar --all

# Sincronizza solo le prossime 30 occorrenze
python manage.py sync_google_calendar --count 30
```

---

## 📊 Riepilogo Situazione

| Componente | Stato | Azione Richiesta |
|------------|-------|------------------|
| Settings configurati | ✅ OK | Nessuna |
| Codice sincronizzazione | ✅ OK | Nessuna |
| Database schema | ✅ OK | Nessuna |
| File credenziali | ❌ TIPO SBAGLIATO | Sostituire con Service Account |
| Librerie Google | ❌ NON INSTALLATE | `pip install google-api-python-client...` |
| Signal abilitati | ❌ DISABILITATI | Decommentare in `models.py` |
| Google Calendar API | ⚠️ DA VERIFICARE | Abilitare in Google Cloud Console |
| Calendario condiviso | ❌ NON FATTO | Condividere con service account email |

---

## 🎯 Checklist Completa

- [ ] Crea Service Account in Google Cloud Console
- [ ] Scarica file JSON service account
- [ ] Sostituisci `/home/sandro/mygest/secrets/google-calendar.json`
- [ ] Verifica che contenga `"type": "service_account"`
- [ ] Abilita Google Calendar API nel progetto Google Cloud
- [ ] Condividi calendario Google con email service account
- [ ] Installa librerie: `pip install google-api-python-client google-auth google-auth-httplib2`
- [ ] Aggiungi librerie a `requirements.txt`
- [ ] Esegui `python check_google_calendar_config.py` → deve dare OK
- [ ] Decommenta signal in `scadenze/models.py`
- [ ] Riavvia server Django
- [ ] Testa: `python manage.py sync_google_calendar --dry-run`
- [ ] Sincronizza: `python manage.py sync_google_calendar --all`

---

## 🚀 Dopo l'Attivazione

Una volta completati tutti i passi:

1. **Ogni volta che crei/modifichi una `ScadenzaOccorrenza`**:
   - ✅ Viene automaticamente creato/aggiornato l'evento su Google Calendar
   - ✅ Il campo `google_calendar_event_id` viene popolato
   - ✅ Timestamp salvato in `google_calendar_synced_at`

2. **Ogni volta che elimini una `ScadenzaOccorrenza`**:
   - ✅ L'evento viene rimosso da Google Calendar

3. **Log di tutte le operazioni**:
   - ✅ Salvato in `ScadenzaNotificaLog` con evento `CALENDAR_SYNC`

---

## 📞 Supporto

- **Documentazione completa**: `docs/GOOGLE_CALENDAR_SETUP.md`
- **Troubleshooting**: `GOOGLE_CALENDAR_ERROR.md`
- **Stato sincronizzazione**: `docs/GOOGLE_CALENDAR_DISABLED.md`

---

**Prossima azione consigliata**: Inizia dal PASSO 1 (creazione Service Account)
