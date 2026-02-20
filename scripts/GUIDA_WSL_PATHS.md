# Guida Path Windows in WSL - MyGest Agent

## Come Funzionano i Path in WSL

WSL2 monta automaticamente i drive Windows sotto `/mnt/`:

```bash
C:\Users\Sandro\Desktop\  →  /mnt/c/Users/Sandro/Desktop/
D:\Documenti\             →  /mnt/d/Documenti/
G:\                       →  /mnt/g/ (Google Drive)
\\NAS\Share\              →  /mnt/archivio/ (se montato)
```

## Path per Utenti Windows

### Formato da Usare nel Form React

Quando carichi un documento da **Windows** e vuoi che venga eliminato dopo l'archiviazione:

#### File locali su C:
```
Windows:  C:\Users\Sandro\Desktop\fattura.pdf
Nel form: /mnt/c/Users/Sandro/Desktop/fattura.pdf
```

#### File locali su D:
```
Windows:  D:\Documenti\contratti\contratto.pdf
Nel form: /mnt/d/Documenti/contratti/contratto.pdf
```

#### File su Google Drive (G:)
```
Windows:  G:\Il mio Drive\fattura.pdf
Nel form: /mnt/g/Il mio Drive/fattura.pdf
```

#### File su NAS/rete (se montato in WSL)
```
Windows:  \\NAS\Documenti\file.pdf
WSL:      Verifica dove è montato con: df -h
Nel form: /mnt/nas/Documenti/file.pdf (esempio)
```

## Conversione Automatica Path Windows → WSL

Puoi usare questi comandi per convertire:

```bash
# Da Windows a WSL
wslpath "C:\Users\Sandro\Desktop\file.pdf"
# Output: /mnt/c/Users/Sandro/Desktop/file.pdf

# Da WSL a Windows
wslpath -w /mnt/c/Users/Sandro/Desktop/file.pdf
# Output: C:\Users\Sandro\Desktop\file.pdf
```

## Percorsi Protetti ⚠️

L'agent **NON** eliminerà MAI file in queste directory:

- `/mnt/archivio` → Archivio documenti MyGest
- `/home/sandro/mygest` → Progetto MyGest
- `/var/www` → Web server
- `/usr`, `/etc`, `/bin`, `/sbin` → Sistema

Se provi a eliminare un file protetto:
```
🛡️ BLOCCATO: Path protetto: /mnt/archivio/documenti/file.pdf
```

## Test Percorsi

### 1. Verifica accesso al file da WSL
```bash
# Lista file in Desktop Windows
ls -la /mnt/c/Users/Sandro/Desktop/

# Leggi un file Windows da WSL
cat /mnt/c/Users/Sandro/Desktop/test.txt
```

### 2. Crea file di test
```bash
# In Windows, crea: C:\Users\Sandro\Desktop\test_mygest.txt
# Oppure da WSL:
echo "Test MyGest" > /mnt/c/Users/Sandro/Desktop/test_mygest.txt

# Verifica esistenza
ls -la /mnt/c/Users/Sandro/Desktop/test_mygest.txt
```

### 3. Prova eliminazione tramite MyGest
1. Apri MyGest nel browser
2. Crea nuovo documento
3. Carica il file
4. In "Percorso file origine": `/mnt/c/Users/Sandro/Desktop/test_mygest.txt`
5. ✅ Seleziona "Elimina file di origine"
6. Salva

Entro 30 secondi l'agent lo eliminerà.

### 4. Verifica eliminazione
```bash
# Dovrebbe dire "File not found"
ls -la /mnt/c/Users/Sandro/Desktop/test_mygest.txt
```

## Montare Cartelle di Rete in WSL

Se hai file su un NAS o server Windows, montali in WSL:

### Montaggio temporaneo
```bash
# Crea punto di mount
sudo mkdir -p /mnt/nas

# Monta share CIFS/SMB
sudo mount -t cifs //192.168.1.4/documenti /mnt/nas \
  -o username=tuo_utente,password=tua_password,uid=1000,gid=1000
```

### Montaggio permanente
Aggiungi a `/etc/fstab`:

```bash
sudo nano /etc/fstab
```

Aggiungi riga:
```
//192.168.1.4/documenti /mnt/nas cifs username=utente,password=pass,uid=1000,gid=1000,_netdev 0 0
```

Salva e monta:
```bash
sudo mount -a
```

Verifica:
```bash
df -h | grep nas
ls -la /mnt/nas/
```

### Credenziali sicure
Per non mettere password in chiaro:

```bash
# Crea file credenziali
sudo nano /etc/samba/credentials

# Contenuto:
username=tuo_utente
password=tua_password
domain=DOMINIO (se necessario)

# Proteggi file
sudo chmod 600 /etc/samba/credentials

# In /etc/fstab usa:
//192.168.1.4/documenti /mnt/nas cifs credentials=/etc/samba/credentials,uid=1000,gid=1000,_netdev 0 0
```

## Workflow Completo

### Scenario: File sul Desktop Windows da archiviare

1. **Hai il file**: `C:\Users\Sandro\Desktop\fattura_cliente_123.pdf`

2. **Apri MyGest** nel browser

3. **Crea documento**:
   - Cliente: Cliente ABC
   - Tipo: Fattura
   - File: Carica `fattura_cliente_123.pdf`
   - Titolario: Seleziona voce appropriata

4. **Configurazione eliminazione**:
   - Path origine: `/mnt/c/Users/Sandro/Desktop/fattura_cliente_123.pdf`
   - ✅ Elimina file di origine dopo archiviazione

5. **Salva**

6. **MyGest**:
   - Salva file in: `/mnt/archivio/2025/CLIENTI/Cliente_ABC/FATTURE/DOC001-10-2025-001.pdf`
   - Crea richiesta eliminazione in DB

7. **Agent** (entro 30 sec):
   - Legge richiesta da DB
   - Elimina: `/mnt/c/Users/Sandro/Desktop/fattura_cliente_123.pdf`
   - Conferma al server

8. **Risultato**:
   - ✅ File archiviato in `/mnt/archivio/...` (CONSERVATO)
   - ✅ File originale su Desktop ELIMINATO
   - ✅ Spazio liberato sul PC

## Errori Comuni

### "File non trovato"
```
❌ File non trovato: /mnt/c/Users/Sandro/Desktop/file.pdf
```
**Cause**:
- Path sbagliato (controlla maiuscole/minuscole)
- File già spostato/eliminato
- Drive non montato

**Soluzione**:
```bash
ls -la /mnt/c/Users/Sandro/Desktop/
```

### "Permesso negato"
```
❌ PermissionError: [Errno 13] Permission denied
```
**Cause**:
- File aperto in un programma Windows
- Permessi insufficienti

**Soluzione**:
- Chiudi il file in Windows
- Verifica permessi: `ls -la /mnt/c/.../file.pdf`

### "Path protetto"
```
🛡️ BLOCCATO: Path protetto: /mnt/archivio/file.pdf
```
**Causa**: Stai cercando di eliminare un file nell'archivio MyGest

**Soluzione**: È normale! L'archivio è protetto per evitare perdite di dati.

## Script Helper

### Converti path Windows → WSL
Crea `convert_path.sh`:

```bash
#!/bin/bash
# Converte path Windows in path WSL

if [ -z "$1" ]; then
    echo "Uso: $0 'C:\Path\To\File.pdf'"
    exit 1
fi

wslpath "$1"
```

Uso:
```bash
chmod +x convert_path.sh
./convert_path.sh 'C:\Users\Sandro\Desktop\file.pdf'
# Output: /mnt/c/Users/Sandro/Desktop/file.pdf
```

### Verifica file esiste
Crea `check_file.sh`:

```bash
#!/bin/bash
# Verifica se un file Windows esiste in WSL

FILE="$1"
if [ -f "$FILE" ]; then
    echo "✅ File esiste: $FILE"
    ls -lh "$FILE"
else
    echo "❌ File non trovato: $FILE"
fi
```

Uso:
```bash
./check_file.sh /mnt/c/Users/Sandro/Desktop/file.pdf
```

## FAQ

**Q: Posso usare path Windows come `C:\...` direttamente?**  
A: No, devi convertirli in formato WSL `/mnt/c/...`

**Q: L'agent funziona anche se Windows è spento?**  
A: No, WSL gira su Windows. Se Windows è spento, l'agent non può eliminare file.

**Q: Posso eliminare file su drive esterni USB?**  
A: Sì, se montati in WSL (es. `/mnt/d`, `/mnt/e`, ecc.)

**Q: E se il file è su OneDrive/Google Drive?**  
A: Se sincronizzato localmente, usa il path locale: `/mnt/c/Users/Sandro/OneDrive/file.pdf`

**Q: Posso avere un agent anche su PC Windows remoto?**  
A: Sì! Usa `mygest_agent_windows.py` (vedi `AGENT_WINDOWS_GUIDE.md`)

## Sicurezza

✅ **Path protetti**: L'archivio MyGest non può essere toccato  
✅ **Solo file**: L'agent elimina solo file, non cartelle  
✅ **Conferma DB**: Ogni eliminazione è tracciata nel database  
✅ **Log completi**: Tutto è registrato in `~/.mygest-agent.log`  
✅ **Permessi utente**: L'agent può eliminare solo file accessibili all'utente WSL

## Monitoraggio

Controlla gli ultimi log:
```bash
tail -f ~/.mygest-agent.log
```

Verifica statistiche agent:
```bash
curl -H "Authorization: Token IL_TUO_TOKEN" \
  http://localhost:8000/api/v1/agent/status/ | jq
```

Conta file eliminati oggi:
```bash
grep "File eliminato" ~/.mygest-agent.log | grep "$(date +%Y-%m-%d)" | wc -l
```
