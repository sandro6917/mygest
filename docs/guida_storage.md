# Guida alla Gestione dello Storage in MyGest

## Panoramica

MyGest utilizza una configurazione di storage centralizzata che separa completamente i file dell'archivio dalla directory `media/` di default di Django. Tutti i file vengono salvati in una directory configurabile tramite la variabile d'ambiente `ARCHIVIO_BASE_PATH`.

## Architettura dello Storage

### Struttura Generale

```
ARCHIVIO_BASE_PATH/
├── documenti/              # Documenti gestiti dal sistema
│   ├── 2024/
│   │   ├── CLI001/
│   │   └── CLI002/
│   └── 2025/
├── archivio_fisico/        # File dell'archivio fisico
│   ├── operazioni/         # Scansioni verbali operazioni
│   └── verbali/            # Template verbali
└── fascicoli/              # Fascicoli e documenti correlati
```

### Configurazione per Ambiente

#### Ambiente Locale (WSL)
- **Percorso**: `/mnt/archivio` (montaggio NAS)
- **Configurazione**: `.env`

```env
ARCHIVIO_BASE_PATH=/mnt/archivio
```

#### Ambiente Produzione (VPS)
- **Percorso**: `/srv/mygest/archivio`
- **Configurazione**: `.env` o `.env.production`

```env
ARCHIVIO_BASE_PATH=/srv/mygest/archivio
```

## Implementazione Tecnica

### NASPathStorage

Il progetto utilizza una classe di storage personalizzata (`NASPathStorage`) definita in `mygest/storages.py`:

```python
from mygest.storages import NASPathStorage

nas_storage = NASPathStorage()
```

Questa classe:
- Legge dinamicamente il percorso da `settings.ARCHIVIO_BASE_PATH`
- Garantisce che i file vengano salvati nella directory corretta
- Supporta test e ambienti multipli

### Utilizzo nei Model

I model che gestiscono file devono usare `nas_storage`:

```python
from mygest.storages import NASPathStorage

nas_storage = NASPathStorage()

class Documento(models.Model):
    file = models.FileField(
        storage=nas_storage,
        upload_to="documenti/...",
        max_length=500
    )
```

## Migrazione da media/ al Nuovo Storage

### Prerequisiti

1. **Ambiente Locale**: Assicurati che il NAS sia montato in `/mnt/archivio`
   ```bash
   # Verifica il montaggio
   ls -la /mnt/archivio
   
   # Se non montato, monta il NAS
   sudo mount -t drvfs '\\NAS\share' /mnt/archivio
   ```

2. **Ambiente Produzione**: Crea la directory archivio
   ```bash
   sudo mkdir -p /srv/mygest/archivio
   sudo chown www-data:www-data /srv/mygest/archivio
   sudo chmod 755 /srv/mygest/archivio
   ```

### Esecuzione Migrazione

1. **Simulazione (Dry-run)**
   ```bash
   cd /home/sandro/mygest
   python scripts/migrate_storage.py --dry-run
   ```

2. **Migrazione Reale**
   ```bash
   python scripts/migrate_storage.py
   ```

3. **Verifica**
   - Accedi all'applicazione
   - Verifica che i documenti siano accessibili
   - Controlla i log per eventuali errori

4. **Pulizia (dopo verifica)**
   ```bash
   # ATTENZIONE: Esegui solo dopo aver verificato che tutto funzioni!
   rm -rf /home/sandro/mygest/media
   ```

## Messa in Produzione

### 1. Preparazione VPS

```bash
# Connettiti alla VPS
ssh user@your-vps

# Crea la directory archivio
sudo mkdir -p /srv/mygest/archivio
sudo chown www-data:www-data /srv/mygest/archivio
sudo chmod 755 /srv/mygest/archivio
```

### 2. Configurazione Environment

Crea o aggiorna `/srv/mygest/app/.env`:

```env
ARCHIVIO_BASE_PATH=/srv/mygest/archivio
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

### 3. Deploy Applicazione

```bash
cd /srv/mygest/app
git pull origin main

# Attiva virtual environment
source /srv/mygest/venv/bin/activate

# Installa/aggiorna dipendenze
pip install -r requirements.txt

# Migra il database (se necessario)
python manage.py migrate

# Raccogli file statici
python manage.py collectstatic --noinput

# Riavvia servizi
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### 4. Migrazione File Esistenti (se necessario)

```bash
cd /srv/mygest/app
python scripts/migrate_storage.py --dry-run
python scripts/migrate_storage.py
```

## Backup e Sincronizzazione

### Backup Locale → VPS

```bash
# Usa rsync per sincronizzare i file
rsync -avz --progress /mnt/archivio/ user@vps:/srv/mygest/archivio/
```

### Backup VPS → Locale

```bash
# Backup dalla VPS al NAS locale
rsync -avz --progress user@vps:/srv/mygest/archivio/ /mnt/archivio/
```

### Backup Automatico (VPS)

Lo script `scripts/backup.sh` nella VPS dovrebbe includere anche l'archivio:

```bash
#!/bin/bash
# Backup database
pg_dump mygest > /srv/mygest/backups/mygest_$(date +%Y%m%d).sql

# Backup archivio
tar -czf /srv/mygest/backups/archivio_$(date +%Y%m%d).tar.gz /srv/mygest/archivio/

# Upload su Google Drive (opzionale)
# rclone copy /srv/mygest/backups/ gdrive:mygest-backups/
```

## Risoluzione Problemi

### File non trovati dopo migrazione

1. Verifica che `ARCHIVIO_BASE_PATH` sia configurato correttamente:
   ```bash
   python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.ARCHIVIO_BASE_PATH)
   ```

2. Verifica i permessi:
   ```bash
   ls -la /mnt/archivio  # locale
   ls -la /srv/mygest/archivio  # VPS
   ```

3. Controlla i log:
   ```bash
   tail -f /srv/mygest/logs/gunicorn.log
   tail -f /srv/mygest/logs/nginx-error.log
   ```

### Errori di permesso

```bash
# Locale (WSL)
sudo chown -R sandro:sandro /mnt/archivio

# VPS
sudo chown -R www-data:www-data /srv/mygest/archivio
sudo chmod -R 755 /srv/mygest/archivio
```

### NAS non montato (WSL)

```bash
# Verifica il montaggio
mount | grep /mnt/archivio

# Monta manualmente
sudo mkdir -p /mnt/archivio
sudo mount -t drvfs '\\192.168.1.X\share' /mnt/archivio

# Montaggio automatico in /etc/fstab
echo '\\192.168.1.X\share /mnt/archivio drvfs defaults 0 0' | sudo tee -a /etc/fstab
```

## Test

### Test Storage Locale

```python
# Test nel Django shell
python manage.py shell

from django.core.files.base import ContentFile
from mygest.storages import NASPathStorage

storage = NASPathStorage()
name = storage.save('test/prova.txt', ContentFile(b'Hello World'))
print(f"File salvato in: {storage.path(name)}")
storage.delete(name)
```

### Test Upload Documento

1. Accedi all'admin Django
2. Crea un nuovo documento
3. Carica un file
4. Verifica che il file sia in `/mnt/archivio` o `/srv/mygest/archivio`

## Checklist Migrazione

- [ ] Backup completo del database
- [ ] Backup completo della directory media/
- [ ] NAS montato in `/mnt/archivio` (locale) o directory creata (VPS)
- [ ] File `.env` aggiornato con `ARCHIVIO_BASE_PATH`
- [ ] Test in dry-run completato
- [ ] Migrazione file eseguita
- [ ] Test applicazione completato
- [ ] File media/ eliminato (dopo verifica)
- [ ] Deploy in produzione completato
- [ ] Backup post-migrazione completato

## Riferimenti

- **Settings**: `mygest/settings.py`
- **Storage**: `mygest/storages.py`
- **Script Migrazione**: `scripts/migrate_storage.py`
- **Environment**: `.env`, `.env.example`, `.env.production`
