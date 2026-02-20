# Setup Archivio per Ambiente Locale (WSL)

## Problema
La directory `/mnt/archivio` esiste ma non è scrivibile dall'utente corrente.

## Soluzione

### Opzione 1: Cambiare i permessi (Temporaneo)

```bash
sudo chown -R sandro:sandro /mnt/archivio
sudo chmod -R 755 /mnt/archivio
```

### Opzione 2: Montare il NAS con permessi corretti (Raccomandato)

Se `/mnt/archivio` deve essere un punto di montaggio per un NAS, monta con le opzioni corrette:

```bash
# Smonta se già montato
sudo umount /mnt/archivio 2>/dev/null

# Crea il punto di montaggio
sudo mkdir -p /mnt/archivio

# Monta il NAS con permessi utente
# Sostituisci IP_NAS e SHARE con i tuoi valori
sudo mount -t drvfs '\\IP_NAS\SHARE' /mnt/archivio -o uid=$(id -u),gid=$(id -g),metadata

# Verifica
ls -ld /mnt/archivio
touch /mnt/archivio/test.txt && rm /mnt/archivio/test.txt && echo "✓ Scrittura OK"
```

### Opzione 3: Usare una directory locale alternativa (Solo sviluppo)

Se non hai un NAS disponibile o per test rapidi:

```bash
# Crea una directory locale
mkdir -p ~/mygest_archivio
chmod 755 ~/mygest_archivio

# Aggiorna .env
echo "ARCHIVIO_BASE_PATH=$HOME/mygest_archivio" >> .env
```

## Montaggio Automatico NAS (WSL)

Per montare automaticamente il NAS all'avvio di WSL:

1. Crea uno script di mount:

```bash
sudo nano /usr/local/bin/mount-nas.sh
```

2. Inserisci il contenuto:

```bash
#!/bin/bash
# Mount NAS for MyGest

if ! mountpoint -q /mnt/archivio; then
    mkdir -p /mnt/archivio
    mount -t drvfs '\\IP_NAS\SHARE' /mnt/archivio -o uid=1000,gid=1000,metadata
    if [ $? -eq 0 ]; then
        echo "✓ NAS montato in /mnt/archivio"
    else
        echo "✗ Errore nel montaggio del NAS"
    fi
else
    echo "✓ NAS già montato"
fi
```

3. Rendi eseguibile:

```bash
sudo chmod +x /usr/local/bin/mount-nas.sh
```

4. Aggiungi a `.bashrc` o `.profile`:

```bash
echo '/usr/local/bin/mount-nas.sh' >> ~/.bashrc
```

## Verifica Setup

Dopo aver configurato l'archivio, verifica che tutto funzioni:

```bash
cd ~/mygest
source venv/bin/activate

# Verifica configurazione Django
DJANGO_SETTINGS_MODULE=mygest.settings python -c "
import django
django.setup()
from django.conf import settings
from mygest.storages import NASPathStorage

storage = NASPathStorage()
print(f'✓ Storage location: {storage.location}')

# Test scrittura
from django.core.files.base import ContentFile
try:
    name = storage.save('test/prova.txt', ContentFile(b'Test MyGest'))
    print(f'✓ File test salvato in: {storage.path(name)}')
    storage.delete(name)
    print('✓ File test eliminato')
    print('\n✓✓✓ STORAGE CONFIGURATO CORRETTAMENTE ✓✓✓')
except Exception as e:
    print(f'✗ Errore: {e}')
"
```

## Risoluzione Problemi

### Errore "Permission denied"
- Verifica i permessi: `ls -ld /mnt/archivio`
- Cambia proprietario: `sudo chown -R $(whoami):$(whoami) /mnt/archivio`

### NAS non raggiungibile
- Verifica connessione: `ping IP_NAS`
- Verifica condivisione: `smbclient -L \\\\IP_NAS`

### Directory non esiste
- Crea directory: `sudo mkdir -p /mnt/archivio`
- Monta NAS (vedi sopra)

## Prossimi Passi

Una volta che lo storage è configurato correttamente:

1. Esegui la migrazione dei file esistenti:
   ```bash
   python scripts/migrate_storage.py --dry-run
   python scripts/migrate_storage.py
   ```

2. Testa l'applicazione:
   ```bash
   python manage.py runserver
   ```

3. Verifica che i documenti siano accessibili dall'interfaccia web
