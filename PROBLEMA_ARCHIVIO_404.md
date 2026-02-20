# Problema File Archivio - 404 Not Found

## Data analisi
17 Novembre 2025

## Problema riscontrato

Durante l'esecuzione del server di sviluppo, si verificano errori 404 quando si tenta di accedere ai file dell'archivio documentale:

```
Not Found: /archivio/SADOCC01/AF - Amministrazione, Finanza e Controllo/AF-DIC - Dichiarazioni fiscali/770 - Dichiarazione sostituti d'imposta/2021/7702021_anno2020.pdf
[17/Nov/2025 16:53:51] "GET /archivio/SADOCC01/AF%20-%20Amministrazione%2C%20Finanza%20e%20Controllo/AF-DIC%20-%20Dichiarazioni%20fiscali/770%20-%20Dichiarazione%20sostituti%20d'imposta/2021/7702021_anno2020.pdf HTTP/1.1" 404 4841
```

## Causa

1. **Configurazione storage**: In `mygest/settings.py`:
   ```python
   ARCHIVIO_BASE_PATH = os.getenv("ARCHIVIO_BASE_PATH", "/mnt/archivio")
   MEDIA_URL = '/archivio/'
   MEDIA_ROOT = ARCHIVIO_BASE_PATH
   ```

2. **Directory esistente ma vuota**: La directory `/mnt/archivio` esiste nel filesystem ma è completamente vuota:
   ```bash
   $ ls -la /mnt/archivio
   total 8
   drwxr-xr-x 2 root root 4096 May 13  2025 .
   drwxr-xr-x 7 root root 4096 Oct  4 11:50 ..
   ```

3. **Riferimenti nel database**: Il database contiene documenti con percorsi che puntano a `/mnt/archivio/...`:
   - I record in `documenti_documento` hanno il campo `file` popolato con path relativi (es: `SADOCC01/AF - Amministrazione.../...`)
   - Il campo `percorso_archivio` contiene path assoluti (es: `/mnt/archivio/SADOCC01/...`)
   - I file fisici **non esistono** nel filesystem

4. **File non trovati**: Nessun file PDF referenziato nel database è presente fisicamente in `/mnt/archivio`

## Soluzioni possibili

### Opzione 1: Ripristinare l'archivio da backup
Se esiste un backup dell'archivio documentale, ripristinarlo in `/mnt/archivio`:
```bash
# Esempio con rsync da backup
sudo rsync -av /path/to/backup/archivio/ /mnt/archivio/
```

### Opzione 2: Riconfigurare ARCHIVIO_BASE_PATH
Se i file esistono in un'altra location (es: `media/archivio`), modificare la variabile d'ambiente:
```bash
export ARCHIVIO_BASE_PATH="/home/sandro/mygest/media/archivio"
```

Oppure modificare direttamente `mygest/settings.py`:
```python
ARCHIVIO_BASE_PATH = os.getenv("ARCHIVIO_BASE_PATH", str(BASE_DIR / "media" / "archivio"))
```

### Opzione 3: Re-upload dei documenti
Se i file originali sono andati persi, sarà necessario:
1. Identificare i documenti mancanti dal database
2. Richiedere i file originali
3. Re-caricarli tramite interfaccia web o script

### Opzione 4: Pulire riferimenti orfani
Se i file non sono più necessari, rimuovere i riferimenti dal database:
```python
# Script per identificare documenti senza file fisico
from documenti.models import Documento
from django.conf import settings
import os

for doc in Documento.objects.exclude(file=''):
    full_path = os.path.join(settings.ARCHIVIO_BASE_PATH, doc.file.name)
    if not os.path.exists(full_path):
        print(f"Missing: {doc.id} - {doc.file.name}")
        # Opzionalmente: doc.file = None; doc.save()
```

## Stato attuale

- ✅ **Favicon 404 RISOLTO**: Creata `/home/sandro/mygest/static/img/favicon.ico`
- ✅ **Archivio 404 RISOLTO**: NAS montato correttamente su `/mnt/archivio`

### Dettagli mount NAS

**Configurazione fstab**:
```bash
//192.168.1.4/documenti/archivio  /mnt/archivio  cifs  credentials=/etc/samba/cred_nas,iocharset=utf8,vers=3.0,uid=1000,gid=1000,file_mode=0664,dir_mode=0775,noperm  0  0
```

**Problema riscontrato**:
- ✅ NAS raggiungibile (192.168.1.4 risponde al ping)
- ✅ File credenziali presente (`/etc/samba/cred_nas`)
- ❌ Mount fallisce con errore `STATUS_LOGON_FAILURE` (credenziali errate o permessi insufficienti)

**Errore kernel**:
```
CIFS: Status code returned 0xc000006d STATUS_LOGON_FAILURE
CIFS: VFS: \\192.168.1.4 Send error in SessSetup = -13
```

### Azioni necessarie per risolvere

✅ **PROBLEMA RISOLTO** - 17 Novembre 2025

**Soluzione applicata**:
1. Identificato errore nelle credenziali (case-sensitive nella password)
2. Aggiornate credenziali in `/etc/samba/cred_nas`:
   ```
   username=admin
   password=001CambiamI@
   ```
3. Montato il NAS: `sudo mount /mnt/archivio`
4. Verificato accesso ai file: ✅ File accessibili

**Verifica**:
```bash
$ mount | grep archivio
//192.168.1.4/documenti/archivio on /mnt/archivio type cifs (rw,relatime,vers=3.0,...)

$ ls /mnt/archivio | wc -l
80+ directory clienti disponibili

$ ls -lh "/mnt/archivio/SADOCC01/.../7702021_anno2020.pdf"
-rw-rw-r-- 1 sandro sandro 107K Oct 24 11:52 ...
```

**Note per il futuro**:
- Il mount è configurato in `/etc/fstab` per essere automatico al boot
- Se il NAS viene riavviato, potrebbe essere necessario rimontare: `sudo mount /mnt/archivio`
- Per mount automatico verificare che il NAS sia online prima del boot del sistema

---

### ~~Azioni necessarie per risolvere~~ (RISOLTO)

1. **Verificare credenziali NAS**:
   - Username: `admin`
   - Password: verificare che sia corretta sul NAS
   - Controllare che l'utente `admin` abbia permessi sulla share `documenti/archivio`

2. **Testare connessione manualmente**:
   ```bash
   # Installa smbclient per test
   sudo apt install smbclient
   
   # Testa connessione
   smbclient -L 192.168.1.4 -U admin
   ```

3. **Aggiornare credenziali** (se necessario):
   ```bash
   sudo nano /etc/samba/cred_nas
   # Modifica username/password corretti
   ```

4. **Montare il NAS**:
   ```bash
   sudo mount /mnt/archivio
   ```

5. **Verifica mount riuscito**:
   ```bash
   mount | grep archivio
   ls -la /mnt/archivio
   ```

6. **Mount automatico al boot** (già configurato in fstab, funzionerà dopo fix credenziali)

## Raccomandazioni

1. **Backup immediato del database**: Conservare lo stato attuale dei metadati
2. **Verifica backup archivio**: Cercare backup dei file in `/mnt/archivio`
3. **Documentazione path**: Verificare documentazione deployment per capire dove dovrebbero trovarsi i file
4. **Monitoring**: Implementare check di integrità per rilevare file mancanti

## File coinvolti

- `mygest/settings.py`: Configurazione `ARCHIVIO_BASE_PATH` e `MEDIA_URL`
- `mygest/urls.py`: Serving di file media in DEBUG mode
- `mygest/storages.py`: `NASPathStorage` per gestione file archivio
- `documenti/models.py`: Modello `Documento` con campo `file` e `percorso_archivio`
