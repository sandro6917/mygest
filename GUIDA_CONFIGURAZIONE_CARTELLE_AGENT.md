# Guida Configurazione Cartelle - MyGest Agent

## 🎯 Quick Start

### 1. Copia File Configurazione

```bash
# Copia template nella home
cp config/mygest-agent.conf.example ~/.mygest-agent.conf

# Modifica con il tuo editor preferito
nano ~/.mygest-agent.conf
# oppure
code ~/.mygest-agent.conf
```

### 2. Configura Token API

```ini
[server]
url = http://localhost:8000
token = TUO_TOKEN_QUI  # ← Inserisci il tuo token
```

**Come ottenere il token**:
1. Accedi a Django Admin: `http://localhost:8000/admin/`
2. Vai su **Auth Token** → **Tokens**
3. Clicca **Add Token** → Seleziona il tuo utente → Salva
4. Copia il token generato

### 3. Aggiungi Le Tue Cartelle

```ini
[folders]
# Cartelle da monitorare (commentare con # quelle non necessarie)

# ✅ Downloads (CONSIGLIATA)
monitor_downloads = /mnt/c/Users/TUO_NOME/Downloads

# ✅ Desktop
monitor_desktop = /mnt/c/Users/TUO_NOME/Desktop

# ✅ Documenti
monitor_documents = /mnt/c/Users/TUO_NOME/Documents

# Google Drive (se mappato come G:)
monitor_gdrive = /mnt/g/Il mio Drive

# Dropbox (se mappato come D:)
monitor_dropbox = /mnt/d/Dropbox

# OneDrive
monitor_onedrive = /mnt/c/Users/TUO_NOME/OneDrive

# Cartelle personalizzate
monitor_progetti = /mnt/c/Progetti/Documenti
monitor_scansioni = /mnt/e/Archivio/Scansioni
```

### 4. Verifica Configurazione

```bash
# Mostra configurazione caricata
python scripts/mygest_agent_config.py --show-config

# Output esempio:
# === CONFIGURAZIONE ===
# [server]
#   url = http://localhost:8000
#   token = 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
# 
# === CARTELLE MONITORATE ===
#   ✓ /mnt/c/Users/Sandro/Downloads
#   ✓ /mnt/c/Users/Sandro/Desktop
#   ✓ /mnt/g/Il mio Drive
```

### 5. Avvia Agent

```bash
# Avvia con configurazione
python scripts/mygest_agent_config.py
```

---

## 📁 Trovare i Path delle Cartelle

### Windows → WSL Path Conversion

| Cartella Windows | Path WSL | Note |
|------------------|----------|------|
| `C:\Users\Nome\Downloads` | `/mnt/c/Users/Nome/Downloads` | Browser downloads |
| `C:\Users\Nome\Desktop` | `/mnt/c/Users/Nome/Desktop` | Desktop |
| `C:\Users\Nome\Documents` | `/mnt/c/Users/Nome/Documents` | Documenti |
| `G:\Il mio Drive` | `/mnt/g/Il mio Drive` | Google Drive (G:) |
| `D:\Dropbox` | `/mnt/d/Dropbox` | Dropbox (D:) |
| `C:\Users\Nome\OneDrive` | `/mnt/c/Users/Nome/OneDrive` | OneDrive |

### Come Trovare il Path Esatto

#### Metodo 1: Da Windows Explorer

1. Apri la cartella in Windows Explorer
2. Click destro sulla barra indirizzi → **Copia indirizzo come testo**
3. Converti seguendo la tabella sopra

#### Metodo 2: Da WSL Terminal

```bash
# Naviga nella cartella da Windows Explorer
# Poi da WSL:
pwd

# Output: /mnt/c/Users/Sandro/Downloads
```

#### Metodo 3: Script Helper

```bash
# Da dentro WSL
cd /mnt/c/Users
ls
# Vedi il tuo username

cd /mnt/c/Users/TUO_USERNAME
ls
# Vedi Downloads, Desktop, Documents, etc
```

---

## 🔧 Esempi Configurazioni Comuni

### Configurazione Minima (Solo Downloads)

```ini
[server]
url = http://localhost:8000
token = YOUR_TOKEN

[folders]
monitor_downloads = /mnt/c/Users/Sandro/Downloads
```

### Configurazione Standard

```ini
[server]
url = http://localhost:8000
token = YOUR_TOKEN

[folders]
monitor_downloads = /mnt/c/Users/Sandro/Downloads
monitor_desktop = /mnt/c/Users/Sandro/Desktop
monitor_documents = /mnt/c/Users/Sandro/Documents
```

### Configurazione Avanzata (Cloud Storage)

```ini
[server]
url = http://localhost:8000
token = YOUR_TOKEN

[folders]
# Locale
monitor_downloads = /mnt/c/Users/Sandro/Downloads
monitor_desktop = /mnt/c/Users/Sandro/Desktop

# Cloud storage
monitor_gdrive = /mnt/g/Il mio Drive/Documenti Studio
monitor_onedrive = /mnt/c/Users/Sandro/OneDrive/Lavoro
monitor_dropbox = /mnt/d/Dropbox/Progetti

# Custom
monitor_scansioni = /mnt/e/Archivio/Scansioni/2026
```

---

## ⚙️ Opzioni Avanzate

### Retention Cache

Controllo durata cache file tracker:

```ini
[agent]
# Ore di mantenimento cache (default: 24)
cache_retention_hours = 48  # ← 48 ore invece di 24
```

**Quando aumentare**:
- Upload file vecchi (scaricati giorni prima)
- Workflow lenti

**Quando diminuire**:
- Memoria limitata
- Solo file recenti

### Poll Interval

Frequenza check richieste eliminazione:

```ini
[agent]
# Secondi tra un check e l'altro (default: 30)
poll_interval = 60  # ← Controlla ogni minuto
```

**Valori consigliati**:
- `15` - Eliminazione quasi immediata (più CPU)
- `30` - Bilanciato (default)
- `60` - Meno risorse, eliminazione dopo ~1 minuto

### Path Protetti Personalizzati

Aggiungi cartelle che NON devono mai essere eliminate:

```ini
[protection]
protected_path1 = /mnt/archivio
protected_path2 = /home/sandro/mygest
protected_path3 = /var/www
# Aggiungi i tuoi:
protected_path4 = /mnt/c/Backup
protected_path5 = /mnt/e/ArchivioImportante
```

### Logging

Controllo verbosità log:

```ini
[logging]
# Livello: DEBUG, INFO, WARNING, ERROR
level = INFO  # ← Cambia in DEBUG per troubleshooting

# File log
file = ~/.mygest-agent.log

# Dimensione massima (MB)
max_size_mb = 10

# Numero backup da mantenere
backup_count = 3
```

---

## 🚀 Avvio Automatico (Systemd)

### 1. Crea File Service

```bash
sudo nano /etc/systemd/system/mygest-agent.service
```

### 2. Configurazione Service

```ini
[Unit]
Description=MyGest Desktop Agent
After=network.target

[Service]
Type=simple
User=sandro
WorkingDirectory=/home/sandro/mygest
ExecStart=/usr/bin/python3 /home/sandro/mygest/scripts/mygest_agent_config.py
Restart=on-failure
RestartSec=10

# Variabili ambiente (opzionale)
Environment="MYGEST_CONFIG=/home/sandro/.mygest-agent.conf"

[Install]
WantedBy=multi-user.target
```

### 3. Abilita e Avvia

```bash
# Ricarica configurazione systemd
sudo systemctl daemon-reload

# Abilita avvio automatico
sudo systemctl enable mygest-agent

# Avvia servizio
sudo systemctl start mygest-agent

# Verifica stato
sudo systemctl status mygest-agent

# Visualizza log
journalctl -u mygest-agent -f
```

---

## 🐛 Troubleshooting

### Cartella Non Trovata

**Problema**:
```
⚠ Cartella non esiste (ignorata): /mnt/g/Il mio Drive
```

**Soluzione**:
1. Verifica che il drive sia montato in Windows
2. Da WSL: `ls /mnt/g/`
3. Se non esiste: Google Drive non mappato come drive G:

### Path Windows Non Convertito

**Problema**: Hai inserito `C:\Users\...` invece di `/mnt/c/Users/...`

**Soluzione**: Lo script converte automaticamente! Puoi usare entrambi i formati:
- ✅ `C:\Users\Sandro\Downloads` → Convertito in `/mnt/c/Users/Sandro/Downloads`
- ✅ `/mnt/c/Users/Sandro/Downloads` → Usato direttamente

### Token Non Valido

**Problema**:
```
✗ Impossibile connettersi al server
```

**Soluzione**:
1. Verifica server Django attivo: `http://localhost:8000/admin/`
2. Rigenera token in Django Admin
3. Aggiorna `~/.mygest-agent.conf`

### Nessuna Cartella Monitorata

**Problema**: Agent non trova nessuna cartella

**Soluzione**: Agent usa cartelle default se config vuota:
```
/mnt/c/Users/{username}/Downloads
/mnt/c/Users/{username}/Desktop
/mnt/c/Users/{username}/Documents
```

Verifica username: `echo $USER`

---

## 📊 Test Configurazione

### Verifica Cartelle Accessibili

```bash
# Test manuale accesso cartelle
ls -la /mnt/c/Users/Sandro/Downloads
ls -la /mnt/c/Users/Sandro/Desktop
ls -la /mnt/g/  # Google Drive

# Se errore "Permission denied": problema permessi WSL
```

### Mostra Config Caricata

```bash
python scripts/mygest_agent_config.py --show-config
```

### Test Connessione Server

```bash
# Ping server (senza avviare agent)
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/v1/agent/ping/

# Response OK: {"status": "ok"}
```

---

## 💡 Consigli Best Practice

1. **✅ Monitora solo cartelle necessarie**
   - Più cartelle = più memoria cache
   - Concentrati su Downloads e Desktop

2. **✅ Testa prima con --show-config**
   - Verifica che tutte le cartelle esistano
   - Controlla path protetti

3. **✅ Usa path assoluti**
   - Evita `~/Downloads`, usa `/mnt/c/Users/Nome/Downloads`
   - Più esplicito e affidabile

4. **✅ Backup configurazione**
   ```bash
   cp ~/.mygest-agent.conf ~/.mygest-agent.conf.backup
   ```

5. **✅ Monitora log inizialmente**
   ```bash
   tail -f ~/.mygest-agent.log
   ```

---

## 🔄 Ricarica Configurazione

Dopo aver modificato `~/.mygest-agent.conf`:

### Con Systemd

```bash
sudo systemctl restart mygest-agent
```

### Manuale

```bash
# Ferma agent (Ctrl+C)
# Riavvia
python scripts/mygest_agent_config.py
```

---

## 📚 Riferimenti

- **File Config Template**: `config/mygest-agent.conf.example`
- **Script Agent**: `scripts/mygest_agent_config.py`
- **Documentazione Completa**: `ELIMINAZIONE_AUTOMATICA_SENZA_INPUT.md`

---

**Ultimo Aggiornamento**: 2026-02-24  
**Versione**: 1.0
