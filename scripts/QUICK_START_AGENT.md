# 🚀 Quick Start - Agent Desktop MyGest

## ✅ Setup Completato!

L'agent desktop è configurato e pronto all'uso.

---

## 🔑 Il Tuo Token API

```
aa35a2945ce816d87c5c714732312274f0b6c116
```

**⚠️ Importante**: Conserva questo token in modo sicuro! Chiunque abbia accesso a questo token può eliminare file dal tuo computer.

---

## 🚀 Avvio Agent

### Test Connessione

```bash
cd /home/sandro/mygest/scripts
python3 mygest_agent.py \
  --server http://localhost:8000 \
  --token aa35a2945ce816d87c5c714732312274f0b6c116 \
  --test
```

**Risultato atteso**: `✓ Connessione al server riuscita`

### Avvio Normale

```bash
python3 mygest_agent.py \
  --server http://localhost:8000 \
  --token aa35a2945ce816d87c5c714732312274f0b6c116
```

L'agent:
- ✅ Controlla ogni 30 secondi se ci sono file da eliminare
- ✅ Elimina i file richiesti
- ✅ Conferma le eliminazioni al server
- ✅ Scrive log in `~/.mygest-agent.log`

### Parametri Opzionali

```bash
python3 mygest_agent.py \
  --server http://192.168.1.100:8000 \
  --token YOUR_TOKEN \
  --poll-interval 60  # Controlla ogni 60 secondi invece di 30
```

---

## 📱 Uso dall'Applicazione Web

### 1. Carica Documento

Vai alla form di creazione documento e seleziona il file da caricare.

### 2. Copia Percorso Originale

**Windows**:
- Shift + Click destro sul file → "Copia come percorso"
- Esempio: `C:\Users\Sandro\Downloads\fattura.pdf`

**Linux**:
- Click destro sul file → Proprietà → Copia percorso
- Esempio: `/home/sandro/Downloads/fattura.pdf`

**Mac**:
- Option + Click destro → "Copia ... come nome percorso"
- Esempio: `/Users/sandro/Downloads/fattura.pdf`

### 3. Incolla e Spunta

- Incolla il percorso nel campo "Percorso file originale"
- Spunta "Elimina automaticamente il file originale"

### 4. Salva

Il documento viene archiviato e:
- ✅ Il file viene copiato nel NAS organizzato
- ✅ Viene creata una richiesta di eliminazione (PENDING)
- ✅ Entro 30 secondi, l'agent elimina il file originale
- ✅ Lo stato diventa COMPLETED

---

## 🔍 Monitoraggio

### Log Agent

```bash
# Visualizza log in tempo reale
tail -f ~/.mygest-agent.log

# Ultimi 50 log
tail -50 ~/.mygest-agent.log
```

### Admin Django

**Token**: http://localhost:8000/admin/authtoken/token/
- Vedi tutti i token
- Crea nuovi token per altri utenti
- Elimina token compromessi

**Richieste Eliminazione**: http://localhost:8000/admin/documenti/filedeletionrequest/
- Stato delle richieste (PENDING, COMPLETED, FAILED)
- Errori di eliminazione
- Statistiche

### API Status

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/agent/status/
```

---

## 🛠️ Gestione Token

Ho creato uno script helper per gestire i token:

```bash
cd /home/sandro/mygest/scripts

# Mostra il tuo token
python3 manage_agent_tokens.py show sandro

# Lista tutti i token
python3 manage_agent_tokens.py list

# Crea token per nuovo utente
python3 manage_agent_tokens.py create username

# Lista tutti gli utenti
python3 manage_agent_tokens.py users

# Elimina token
python3 manage_agent_tokens.py delete username
```

---

## 🔄 Avvio Automatico (Opzionale)

### Systemd Service

Per avviare l'agent automaticamente all'avvio del computer:

```bash
# Crea file service
sudo nano /etc/systemd/system/mygest-agent.service
```

Contenuto:
```ini
[Unit]
Description=MyGest Desktop Agent
After=network.target

[Service]
Type=simple
User=sandro
WorkingDirectory=/home/sandro/mygest/scripts
ExecStart=/usr/bin/python3 /home/sandro/mygest/scripts/mygest_agent.py --server http://localhost:8000 --token aa35a2945ce816d87c5c714732312274f0b6c116
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Abilita e avvia
sudo systemctl daemon-reload
sudo systemctl enable mygest-agent
sudo systemctl start mygest-agent

# Verifica stato
sudo systemctl status mygest-agent

# Log
sudo journalctl -u mygest-agent -f
```

---

## ⚠️ Sicurezza

### Best Practices

1. **Non condividere il token**: È come una password
2. **Limita i percorsi**: Considera di modificare l'agent per accettare solo directory specifiche
3. **Verifica prima di eliminare**: Assicurati che il documento sia stato archiviato
4. **Backup**: Mantieni backup prima di abilitare l'eliminazione automatica
5. **Test**: Prova prima con file di test

### Permessi Agent

L'agent può eliminare **qualsiasi file** accessibile dall'utente che lo esegue.

**Consigliato**: Esegui l'agent con un utente con permessi limitati.

---

## 🧪 Test Completo

### 1. Crea File di Test

```bash
echo "Test file" > /tmp/test_mygest.txt
```

### 2. Avvia Agent (in un terminale)

```bash
cd /home/sandro/mygest/scripts
python3 mygest_agent.py --server http://localhost:8000 --token YOUR_TOKEN
```

### 3. Carica Documento (nel browser)

- Seleziona qualsiasi file
- Nel campo "Percorso file originale": `/tmp/test_mygest.txt`
- Spunta "Elimina file originale"
- Salva

### 4. Verifica (entro 30 secondi)

```bash
ls -la /tmp/test_mygest.txt
# Dovrebbe dare: No such file or directory
```

### 5. Controlla Admin

Vai su http://localhost:8000/admin/documenti/filedeletionrequest/
- Vedi la richiesta con stato COMPLETED

---

## 🆘 Troubleshooting

### Agent non si connette

```bash
# Verifica che il server sia in esecuzione
curl http://localhost:8000/api/v1/agent/ping/

# Verifica token
python3 manage_agent_tokens.py show sandro
```

### File non viene eliminato

```bash
# Controlla permessi file
ls -la /percorso/al/file

# Controlla log agent
tail -50 ~/.mygest-agent.log

# Controlla richieste pendenti
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/agent/pending-deletions/
```

### Richiesta rimane PENDING

- Verifica che l'agent sia in esecuzione
- Verifica che il percorso del file sia corretto
- Controlla i log: `tail -f ~/.mygest-agent.log`

---

## 📚 Documentazione Completa

- **Agent Desktop**: `docs/AUTOMAZIONE_ELIMINAZIONE_ORIGINE.md`
- **Tutte le soluzioni**: `scripts/RIEPILOGO_SOLUZIONI.md`
- **Alternative**: `scripts/AUTOMAZIONE_CLEANUP.md`

---

## 🎉 Pronto!

L'agent è configurato e funzionante!

**Prossimi passi**:
1. ✅ Testa con un file di prova
2. ✅ Integra `FileSourceInfo` nel frontend
3. ✅ (Opzionale) Configura avvio automatico con systemd

Buon lavoro! 🚀
