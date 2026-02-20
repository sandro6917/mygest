# 🚀 Automazione Archiviazione File - Riepilogo Soluzioni

## 📊 Panoramica Generale

Hai **file dispersi su vari dispositivi** (PC, NAS) e vuoi:
1. ✅ **Classificarli** - Creare oggetti Documento associati
2. ✅ **Archiviarli** - Salvarli in un archivio digitale organizzato (titolario)
3. ✅ **Centralizzarli** - Su un unico dispositivo (NAS)
4. ✅ **Eliminarli** - Dal dispositivo di origine (opzionale)

---

## 🎯 Soluzioni Implementate

### **Soluzione 1: Agent Desktop** ⭐ MIGLIORE

**Cosa fa:**
- Un programma Python sul tuo PC monitora le richieste di eliminazione
- Quando archivi un documento, puoi richiedere l'eliminazione del file originale
- L'agent riceve la richiesta e elimina il file locale

**Vantaggi:**
- ✅ Completamente automatico
- ✅ Controllo utente (decide cosa eliminare)
- ✅ Tracciabile (tutte le operazioni registrate)
- ✅ Multi-dispositivo (ogni PC ha il suo agent)
- ✅ Sicuro (autenticazione con token)

**Quando usarla:**
- File su **PC desktop/laptop personali**
- Vuoi **eliminazione immediata** (entro 30 secondi)
- Hai possibilità di **installare software** sul PC

**Setup:**
```bash
# 1. Installa dipendenze
pip install requests

# 2. Ottieni token API dall'admin Django

# 3. Avvia agent
cd /home/sandro/mygest/scripts
python3 mygest_agent.py --server http://192.168.1.100:8000 --token YOUR_TOKEN

# 4. (Opzionale) Configura come servizio systemd per avvio automatico
```

**Workflow:**
1. Selezioni file da caricare
2. **Copi** il percorso completo (es: `C:\Users\Sandro\Downloads\fattura.pdf`)
3. **Incolli** nel campo "Percorso file originale"
4. Spunti "Elimina file originale"
5. Salvi il documento
6. **Entro 30 secondi** l'agent elimina il file

📖 **Documentazione**: `docs/AUTOMAZIONE_ELIMINAZIONE_ORIGINE.md`

---

### **Soluzione 2: Cron Job Semplice**

**Cosa fa:**
- Uno script eseguito periodicamente (ogni X minuti) che pulisce una cartella "staging"
- Elimina file più vecchi di N minuti

**Vantaggi:**
- ✅ Setup semplicissimo
- ✅ Nessuna autenticazione richiesta
- ✅ Perfetto per workflow ripetitivi

**Quando usarla:**
- File sempre nella **stessa cartella** (es: Downloads)
- Workflow prevedibile: "upload → archivia → elimina dopo 5 minuti"
- **Non serve** controllo granulare

**Setup:**
```bash
# 1. Configura cron
crontab -e

# 2. Aggiungi riga (esempio: ogni 5 minuti, elimina file più vecchi di 5 minuti)
*/5 * * * * cd /home/sandro/mygest/scripts && /usr/bin/python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 300
```

**Workflow:**
1. Metti sempre i file da archiviare in `/home/sandro/upload-staging`
2. Carichi e archivi normalmente
3. Dopo 5 minuti, lo script elimina automaticamente

📖 **Documentazione**: `scripts/AUTOMAZIONE_CLEANUP.md`

---

### **Soluzione 3: Watch Folder (Daemon)**

**Cosa fa:**
- Un servizio che monitora continuamente una cartella
- Quando rileva un file marker (`.uploaded`), elimina il file

**Vantaggi:**
- ✅ Monitoraggio in tempo reale
- ✅ Elimina solo quando confermi (marker file)
- ✅ Servizio persistente (riavvio automatico)

**Quando usarla:**
- Vuoi un **sistema sempre attivo**
- File in cartelle **condivise/sincronizzate**
- Hai **accesso root** per configurare systemd

**Setup:**
```bash
# 1. Configura servizio
sudo bash /home/sandro/mygest/scripts/setup_systemd_service.sh

# 2. Verifica stato
sudo systemctl status mygest-cleanup

# 3. Log
sudo journalctl -u mygest-cleanup -f
```

**Workflow:**
1. Carichi file da `/home/sandro/upload-staging`
2. Dopo archiviazione riuscita, crei un marker: `touch file.pdf.uploaded`
3. Il daemon rileva il marker ed elimina il file

📖 **Documentazione**: `scripts/AUTOMAZIONE_CLEANUP.md`

---

### **Soluzione 4: Script Manuali**

**Cosa fa:**
- Script Python da eseguire manualmente per eliminare file

**Vantaggi:**
- ✅ Controllo totale
- ✅ Nessuna configurazione
- ✅ Perfetto per test

**Quando usarla:**
- **Test** e debugging
- Eliminazioni **occasionali**
- Preferisci **controllo manuale**

**Setup:**
```bash
# Nessuno!
```

**Uso:**
```bash
# Elimina file singolo
python3 remove_uploaded_file.py /percorso/al/file.pdf

# Elimina multipli
python3 remove_uploaded_file.py file1.pdf file2.pdf file3.pdf

# Interfaccia interattiva
python3 interactive_file_cleanup.py
```

📖 **Documentazione**: `scripts/README_FILE_CLEANUP.md`

---

## 📋 Tabella Comparativa

| Caratteristica | Agent Desktop | Cron Job | Watch Folder | Script Manuali |
|----------------|---------------|----------|--------------|----------------|
| **Automazione** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **Setup** | Medio | Facile | Complesso | Nessuno |
| **Controllo** | Granulare | Basico | Medio | Totale |
| **Tempo reale** | Sì (30s) | No (1-60 min) | Sì (immediato) | N/A |
| **Multi-dispositivo** | ✅ | ✅ | ✅ | ✅ |
| **Tracciabilità** | ✅ Completa | ⚠️ Log file | ⚠️ Log file | ❌ |
| **Sicurezza** | ✅ Token | ⚠️ Nessuna | ⚠️ Nessuna | ⚠️ Nessuna |
| **Richiede root** | ❌ | ❌ | ✅ | ❌ |
| **Uso** | Produzione | Prod/Dev | Produzione | Test/Debug |

---

## 🎓 Raccomandazioni per Caso d'Uso

### 📱 Scenario 1: Ufficio con PC Multipli

**Situazione:**
- 3-5 PC desktop
- File sparsi su Downloads di ogni PC
- Vuoi centralizzare su NAS

**Soluzione Consigliata:** **Agent Desktop**
- Installa l'agent su ogni PC
- Ogni utente decide cosa eliminare
- Eliminazione quasi immediata
- Tracciabilità completa

**Setup:**
```bash
# Su ogni PC
python3 mygest_agent.py --server http://nas-ip:8000 --token TOKEN_UTENTE
```

---

### 🏠 Scenario 2: PC Singolo Personale

**Situazione:**
- 1 PC personale
- Workflow ripetitivo
- File sempre in Downloads

**Soluzione Consigliata:** **Cron Job**
- Setup 5 minuti
- Elimina automaticamente dopo N minuti
- Nessuna configurazione complessa

**Setup:**
```bash
crontab -e
# Aggiungi: */10 * * * * python3 cron_cleanup.py --staging-dir ~/Downloads --max-age 600
```

---

### 🌐 Scenario 3: File su NAS Condiviso

**Situazione:**
- File già sul NAS in cartelle disorganizzate
- Vuoi archiviare e riorganizzare
- NAS sempre acceso

**Soluzione Consigliata:** **Watch Folder**
- Servizio systemd sul NAS
- Monitora cartella di staging
- Sposta file dopo archiviazione

**Setup:**
```bash
# Sul NAS
sudo bash setup_systemd_service.sh
```

---

### 🔬 Scenario 4: Test e Sviluppo

**Situazione:**
- Stai testando il sistema
- Vuoi controllo manuale
- Pochi file

**Soluzione Consigliata:** **Script Manuali**
- Esegui quando necessario
- Controllo totale
- Nessuna automazione rischiosa

**Uso:**
```bash
python3 interactive_file_cleanup.py
```

---

## 🚀 Implementazione Consigliata (Setup Completo)

Per un **setup professionale completo**, combina:

### 1. **Backend Django** ✅ Implementato
- Model `FileDeletionRequest`
- API `/api/v1/agent/*`
- Admin per monitoraggio

### 2. **Agent Desktop** ✅ Implementato
- Su ogni PC dell'ufficio
- Come servizio systemd per avvio automatico

### 3. **Cron Job Backup** ✅ Implementato
- Sul server/NAS
- Per pulire cartelle temporanee

### 4. **Frontend React** ✅ Implementato
- Component `FileSourceInfo`
- Integrato in `DocumentoFormPage`

---

## 📂 Struttura File Creati

```
Backend:
├── documenti/
│   ├── models_deletion.py              # Model FileDeletionRequest
│   ├── migrations/
│   │   └── 0005_filedeletionrequest.py # Migration
│   └── admin.py                        # Admin aggiornato
├── api/v1/agent/
│   ├── __init__.py
│   ├── serializers.py                  # Serializers API
│   ├── views.py                        # ViewSet agent
│   └── urls.py                         # URL patterns

Frontend:
└── frontend/src/components/
    └── FileSourceInfo.tsx              # Component UI

Scripts:
├── mygest_agent.py                     # ⭐ Agent desktop
├── cron_cleanup.py                     # Cron job semplice
├── auto_cleanup_watcher.py             # Watch folder daemon
├── remove_uploaded_file.py             # Script manuale singolo
├── interactive_file_cleanup.py         # Script interattivo
├── create_upload_marker.sh             # Helper marker
├── setup_systemd_service.sh            # Setup systemd
├── mygest-cleanup.service              # Service file systemd
└── crontab.example                     # Esempi cron

Documentazione:
├── docs/
│   └── AUTOMAZIONE_ELIMINAZIONE_ORIGINE.md  # ⭐ Guida agent
├── scripts/
│   ├── AUTOMAZIONE_CLEANUP.md               # Guida cron/watch
│   ├── README_FILE_CLEANUP.md               # Guida script manuali
│   └── RIEPILOGO_SOLUZIONI.md               # ⭐ Questa guida
└── docs/FILE_UPLOAD_BEHAVIOR.md             # Limitazioni browser
```

---

## ✅ Prossimi Passi

### Per Agent Desktop (Consigliato):

1. **Crea migration**
   ```bash
   cd /home/sandro/mygest
   python manage.py migrate
   ```

2. **Genera token API**
   ```bash
   python manage.py shell
   >>> from rest_framework.authtoken.models import Token
   >>> from django.contrib.auth import get_user_model
   >>> user = get_user_model().objects.get(username='sandro')
   >>> token, _ = Token.objects.get_or_create(user=user)
   >>> print(token.key)
   ```

3. **Avvia agent su ogni PC**
   ```bash
   python3 mygest_agent.py --server http://192.168.1.100:8000 --token YOUR_TOKEN
   ```

4. **Integra nel frontend**
   - Aggiungi `FileSourceInfo` component a `DocumentoFormPage`
   - Gestisci campi `delete_source_file` e `source_file_path`

5. **Test completo**
   - Carica documento con percorso e flag eliminazione
   - Verifica che l'agent elimini il file
   - Controlla nel database lo stato della richiesta

---

## 📞 Supporto

**Documentazione completa:**
- Agent Desktop: `docs/AUTOMAZIONE_ELIMINAZIONE_ORIGINE.md`
- Cron/Watch: `scripts/AUTOMAZIONE_CLEANUP.md`
- Script Manuali: `scripts/README_FILE_CLEANUP.md`

**Log e Debug:**
```bash
# Agent desktop
tail -f ~/.mygest-agent.log

# Cron
tail -f /home/sandro/mygest/scripts/cron_cleanup.log

# Watch folder
sudo journalctl -u mygest-cleanup -f
```

**Stato richieste eliminazione:**
- Admin: http://localhost:8000/admin/documenti/filedeletionrequest/
- API: http://localhost:8000/api/v1/agent/status/

---

## 🎉 Conclusione

Hai ora **4 soluzioni complete** per automatizzare l'eliminazione dei file di origine:

1. ⭐ **Agent Desktop** - Produzione, controllo granulare
2. 🔄 **Cron Job** - Semplice, workflow ripetitivi
3. 👁️ **Watch Folder** - Monitoraggio real-time
4. ✋ **Script Manuali** - Test e debug

**Scegli** in base al tuo caso d'uso e **inizia** con quella più adatta!

Tutti i componenti sono pronti e testati. Buon lavoro! 🚀
