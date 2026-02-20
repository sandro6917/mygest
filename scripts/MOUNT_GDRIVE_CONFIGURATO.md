# 🚀 Mount Drive Configurati - MyGest Agent

## Riepilogo Configurazione

### ✅ Drive Montati

| Drive | Mount Point | Tipo | Dimensione | Stato |
|-------|-------------|------|------------|-------|
| **C:** | `/mnt/c` | Windows System | 476 GB | ✅ Attivo |
| **G:** | `/mnt/g` | **Google Drive** | 100 GB | ✅ Attivo |
| **Archivio** | `/mnt/archivio` | NAS (192.168.1.4) | 3.6 TB | ✅ Attivo 🛡️ PROTETTO |

### 📁 Contenuto Google Drive (G:)

- **147 elementi** in "Il mio Drive"
- Accessibile in lettura/scrittura
- Mount permanente configurato in `/etc/fstab`

## 🔧 Configurazione Applicata

### 1. Creazione punto di mount
```bash
sudo mkdir -p /mnt/g
```

### 2. Mount iniziale
```bash
sudo mount -t drvfs 'G:' /mnt/g
```

### 3. Mount automatico (permanente)
Aggiunto a `/etc/fstab`:
```
G:  /mnt/g  drvfs  defaults,metadata,uid=1000,gid=1000,umask=22,fmask=11  0  0
```

## 📝 Come Usare nel Form MyGest

### Esempio 1: File su Google Drive

**Path Windows:**
```
G:\Il mio Drive\Documenti\Clienti\fattura_123.pdf
```

**Path da inserire nel form:**
```
/mnt/g/Il mio Drive/Documenti/Clienti/fattura_123.pdf
```

### Esempio 2: File sul Desktop (C:)

**Path Windows:**
```
C:\Users\Sandro\Desktop\contratto.pdf
```

**Path da inserire nel form:**
```
/mnt/c/Users/Sandro/Desktop/contratto.pdf
```

### ⚠️ Path da NON usare (PROTETTI)

```
❌ /mnt/archivio/...           # Archivio MyGest - PROTETTO
❌ /home/sandro/mygest/...     # Progetto - PROTETTO
❌ /etc/...                    # Sistema - PROTETTO
```

## 🧪 Test File su Google Drive

### File di test creato:
```bash
/mnt/g/Il mio Drive/test_mygest_gdrive.txt
```

### Verifica:
```bash
ls -lh "/mnt/g/Il mio Drive/test_mygest_gdrive.txt"
# Output: -rwxrwxrwx 0 root root 53 Nov 20 18:45 test_mygest_gdrive.txt
```

### Test eliminazione con MyGest:

1. **Carica documento** nel browser MyGest
2. **Path file origine:** `/mnt/g/Il mio Drive/test_mygest_gdrive.txt`
3. ✅ **Seleziona:** "Elimina file di origine dopo archiviazione"
4. **Salva** documento

L'agent eliminerà il file da Google Drive entro 30 secondi.

## 🔍 Verifica Stato Mount

### Script di controllo
```bash
/home/sandro/mygest/scripts/check_mounts.sh
```

Output esempio:
```
✅ C: /mnt/c (476GiB - 31% usato)
✅ G: /mnt/g (Google Drive - 100GiB - 41% usato)
   📁 Elementi in 'Il mio Drive': 147
✅ Archivio /mnt/archivio (3.6TiB - 🛡️ PROTETTO)
```

### Comandi utili

```bash
# Lista tutti i mount
df -h | grep /mnt

# Verifica accesso Google Drive
ls -la "/mnt/g/Il mio Drive/" | head -10

# Test scrittura
echo "test" > "/mnt/g/Il mio Drive/.test_$(date +%s)"

# Remount se necessario
sudo umount /mnt/g
sudo mount -t drvfs 'G:' /mnt/g
```

## 🛡️ Sicurezza e Protezione

### Path Protetti dall'Agent

L'agent **NON eliminerà MAI** file in:

- ✅ `/mnt/archivio` - Archivio documenti MyGest
- ✅ `/home/sandro/mygest` - Progetto MyGest
- ✅ `/var/www` - Web server
- ✅ `/usr`, `/etc`, `/bin`, `/sbin` - Sistema

### Path Eliminabili

L'agent **PUÒ eliminare** file in:

- ✅ `/mnt/c/Users/...` - File utente Windows
- ✅ `/mnt/g/Il mio Drive/...` - File Google Drive
- ✅ `/tmp/...` - File temporanei
- ✅ Qualsiasi path NON in lista protetti

### Test Protezione

```bash
/home/sandro/mygest/scripts/test_path_protection.sh
```

## 📊 Workflow Completo con Google Drive

### Scenario: Fattura su Google Drive da archiviare

1. **File originale:**
   ```
   G:\Il mio Drive\Documenti\Fatture\fattura_cliente_ABC_2025.pdf
   ```

2. **Apri MyGest** nel browser

3. **Crea nuovo documento:**
   - Cliente: ABC S.r.l.
   - Tipo: Fattura
   - Carica file: `fattura_cliente_ABC_2025.pdf`
   - Titolario: Contabilità > Fatture Attive

4. **Configurazione eliminazione:**
   - Path origine: `/mnt/g/Il mio Drive/Documenti/Fatture/fattura_cliente_ABC_2025.pdf`
   - ✅ Elimina file di origine dopo archiviazione

5. **Salva**

6. **MyGest archivia:**
   ```
   Destination: /mnt/archivio/2025/ABC_Srl/FATTURE/DOC001-11-2025-001.pdf
   ```

7. **Agent elimina** (entro 30 sec):
   ```
   Source: /mnt/g/Il mio Drive/Documenti/Fatture/fattura_cliente_ABC_2025.pdf
   ```

8. **Risultato:**
   - ✅ File archiviato su NAS (permanente)
   - ✅ File originale eliminato da Google Drive
   - ✅ Spazio liberato su quota Google Drive
   - ✅ File sincronizzato su tutti i dispositivi (eliminato ovunque)

## 🔄 Sincronizzazione Google Drive

### Vantaggi

- **Eliminazione sincronizzata:** Il file viene eliminato su:
  - PC Windows
  - Google Drive cloud
  - Tutti i dispositivi sincronizzati
  - App mobile Google Drive

- **Spazio liberato su quota:** L'eliminazione libera spazio nella quota Google Drive

### Considerazioni

⚠️ **Attenzione:** 
- L'eliminazione da G: elimina anche dalla cloud Google
- Verifica che il file sia stato archiviato correttamente prima che l'agent lo elimini
- Google Drive ha un **Cestino** (Trash) dove i file rimangono 30 giorni

### Recupero da Cestino Google

Se elimini per errore:

1. Apri **Google Drive** web o app
2. Vai su **Cestino** / **Trash**
3. Cerca il file eliminato
4. Click destro → **Ripristina**

Il file sarà ripristinato entro pochi secondi anche su G:

## 🆘 Troubleshooting

### G: non montato dopo riavvio WSL

```bash
# Verifica mount
df -h | grep /mnt/g

# Se non montato, monta manualmente
sudo mount -t drvfs 'G:' /mnt/g

# Verifica fstab
cat /etc/fstab | grep "/mnt/g"
```

### Google Drive non sincronizza

1. Verifica app **Google Drive per Desktop** sia avviata su Windows
2. Controlla icona system tray (deve essere verde)
3. Click destro icona → Settings → Verifica login

### Permesso negato su G:

```bash
# Verifica permessi
ls -la "/mnt/g/Il mio Drive/"

# Se necessario, remount con permessi corretti
sudo umount /mnt/g
sudo mount -t drvfs 'G:' /mnt/g -o metadata,uid=1000,gid=1000
```

### File non viene eliminato

**Possibili cause:**

1. **File aperto in Google Docs/Sheets/Slides**
   - Chiudi l'editor Google prima dell'eliminazione

2. **Sincronizzazione in corso**
   - Attendi che Google Drive termini la sync
   - Icona Google Drive deve essere verde (non in sync)

3. **Path errato**
   - Controlla maiuscole/minuscole
   - Usa `/mnt/g/Il mio Drive/` (con "Il mio" maiuscolo)

## 📈 Statistiche Utilizzo

### Controlla statistiche agent

```bash
curl -s -H "Authorization: Token IL_TUO_TOKEN" \
  http://localhost:8000/api/v1/agent/status/ | jq
```

### Log eliminazioni da G:

```bash
grep "Il mio Drive" ~/.mygest-agent.log | tail -20
```

### Spazio liberato oggi su Google Drive:

```bash
grep "File eliminato.*Il mio Drive" ~/.mygest-agent.log | \
  grep "$(date +%Y-%m-%d)" | \
  grep -oP '\(\K[0-9]+(?= bytes)' | \
  awk '{sum+=$1} END {print "Spazio liberato: " sum/1024/1024 " MB"}'
```

## ✅ Checklist Pre-Produzione

- [x] Drive G: montato e accessibile
- [x] Mount permanente configurato in `/etc/fstab`
- [x] Test scrittura/lettura su G: funzionante
- [x] Path protetti configurati (archivio escluso)
- [x] Script di verifica `check_mounts.sh` creato
- [x] Test eliminazione file da G: completato
- [x] Documentazione aggiornata
- [x] Google Drive Desktop app attiva su Windows

## 📚 Documentazione Correlata

- `GUIDA_WSL_PATHS.md` - Guida completa path Windows/WSL
- `check_mounts.sh` - Script verifica mount
- `test_path_protection.sh` - Test protezione path
- `QUICK_START_AGENT.md` - Avvio rapido agent
- `AGENT_WINDOWS_GUIDE.md` - Agent Windows nativo

## 🎯 Prossimi Passi

1. **Test in produzione** con file reale da Google Drive
2. **Monitoraggio** eliminazioni nelle prime 24 ore
3. **Backup** preventivo su NAS prima dell'eliminazione
4. **Training** utenti su workflow corretto

---

**Ultimo aggiornamento:** 20 Novembre 2025  
**Configurazione testata:** ✅ FUNZIONANTE  
**Drive montati:** C:, G: (Google Drive), Archivio NAS
