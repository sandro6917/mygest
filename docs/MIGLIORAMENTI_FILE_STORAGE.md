# Miglioramenti File Storage e Sicurezza Upload

## Data Analisi
17 Novembre 2025

## Problemi Identificati

### 1. Directory temporanea `tmp/` non viene pulita automaticamente
**Posizione**: `documenti/models.py` - funzione `documento_upload_to()`

**Problema**: 
I file vengono caricati inizialmente in `tmp/<anno>/<cliente_code>/<filename>` (sotto MEDIA_ROOT) e poi spostati nella destinazione finale dal metodo `_move_file_into_archivio()`. Tuttavia, NON esiste un meccanismo automatico per eliminare i file residui nella directory `tmp/` in caso di errori durante l'upload o il salvataggio.

**Scenario critico**:
```python
# documenti/models.py:61-87
def documento_upload_to(instance, filename):
    """
    Percorso provvisorio di upload (sotto MEDIA_ROOT).
    Il file verrà poi spostato nel NAS dentro 'percorso_archivio' in Documento.save().
    Struttura: tmp/<anno>/<cliente_code>/<filename>
    """
    # ... generazione path tmp
    return f"tmp/{year}/{cli_code}/{filename}"
```

**Rischi**:
- Accumulo progressivo di file orfani in `tmp/`
- Spreco di spazio disco
- Possibili conflitti di nomi file

---

### 2. Path hardcoded non portabili
**Posizioni**: `mygest/settings.py`

**Problema**:
Esistono path hardcoded che rendono il sistema non portabile:

```python
# mygest/settings.py:190
ARCHIVIO_BASE_PATH = os.getenv("ARCHIVIO_BASE_PATH", "/mnt/archivio")

# mygest/settings.py:201-202
IMPORTAZIONI_SOURCE_DIRS = [
    "/home/sandro/documenti",
    "/mnt/archivio/importazioni",
]
```

**Rischi**:
- Impossibile eseguire il deploy su sistemi diversi senza modifiche manuali
- Path `/home/sandro/documenti` è specifico dell'utente di sviluppo
- Path `/mnt/archivio` assume una struttura di montaggio specifica

---

### 3. Nessuna validazione dimensione massima file upload

**Problema**:
Django ha configurazioni di default per dimensione upload ma nel progetto **NON** sono configurate esplicitamente né a livello di settings né a livello di form validators.

**Configurazioni Django mancanti**:
```python
# NON presenti in settings.py
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # Default Django: 2.5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # Default Django: 2.5 MB
```

**Verifiche effettuate**:
- ❌ Nessun validator di dimensione nei form (`documenti/forms.py`)
- ❌ Nessun controllo di dimensione nei model validators
- ❌ Nessun setting esplicito in `settings.py`
- ✅ Solo `FileExtensionValidator` presente in `archivio_fisico/models.py` per validare estensioni

**Rischi**:
- Upload di file molto grandi può saturare la memoria
- Possibile DoS (Denial of Service) tramite upload massicci
- Nessun controllo preventivo sull'utente prima dell'upload

---

### 4. Mancano controlli antivirus sui file caricati

**Problema**:
NON esiste alcun meccanismo di scanning antivirus o validazione di sicurezza sui file uploadati.

**Verifiche effettuate**:
- ❌ Nessuna integrazione con ClamAV o altri antivirus
- ❌ Nessun controllo del contenuto del file (magic bytes)
- ❌ Nessuna quarantena per file sospetti
- ✅ Solo validazione estensione file (facilmente bypassabile)

**Esempio attuale**:
```python
# archivio_fisico/models.py:43-44
validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "tif", "tiff"])],
```

**Rischi**:
- Upload di malware travestiti con estensione valida
- Diffusione di virus attraverso l'archivio documentale
- Compromissione del NAS/storage
- Violazione GDPR se documenti sensibili vengono infettati

---

## Soluzioni Proposte

### Soluzione 1: Pulizia automatica directory temporanea

**Approccio A: Task periodico (RACCOMANDATO)**

Creare un comando Django management per pulizia periodica:

```python
# documenti/management/commands/cleanup_tmp.py
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Pulisce i file temporanei di upload più vecchi di N giorni"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Giorni di retention (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe eliminato senza eliminare',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        tmp_base = Path(settings.MEDIA_ROOT) / "tmp"
        if not tmp_base.exists():
            self.stdout.write(self.style.WARNING(f"Directory tmp non esiste: {tmp_base}"))
            return

        threshold = datetime.now() - timedelta(days=days)
        deleted_count = 0
        deleted_size = 0

        self.stdout.write(f"Scansione file più vecchi di {days} giorni...")

        for filepath in tmp_base.rglob("*"):
            if not filepath.is_file():
                continue
            
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            if mtime < threshold:
                size = filepath.stat().st_size
                if dry_run:
                    self.stdout.write(f"[DRY-RUN] Eliminerei: {filepath} ({size} bytes)")
                else:
                    try:
                        filepath.unlink()
                        deleted_count += 1
                        deleted_size += size
                        logger.info(f"Eliminato file temporaneo: {filepath}")
                    except Exception as e:
                        self.stderr.write(f"Errore eliminazione {filepath}: {e}")

        # Rimuovi directory vuote
        if not dry_run:
            for dirpath in sorted(tmp_base.rglob("*"), reverse=True):
                if dirpath.is_dir() and not any(dirpath.iterdir()):
                    try:
                        dirpath.rmdir()
                    except Exception:
                        pass

        size_mb = deleted_size / (1024 * 1024)
        msg = f"{'[DRY-RUN] ' if dry_run else ''}Eliminati {deleted_count} file ({size_mb:.2f} MB)"
        self.stdout.write(self.style.SUCCESS(msg))
```

**Configurazione cron** (da aggiungere al crontab del server):
```bash
# Pulizia tmp ogni notte alle 2:00
0 2 * * * cd /path/to/mygest && /path/to/venv/bin/python manage.py cleanup_tmp --days=7
```

**Approccio B: Signal post_save con cleanup**

Aggiungere cleanup nel signal esistente:

```python
# documenti/signals.py (creare se non esiste)
from django.db.models.signals import post_save
from django.dispatch import receiver
from pathlib import Path
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='documenti.Documento')
def cleanup_tmp_on_save(sender, instance, created, **kwargs):
    """
    Dopo il salvataggio di un documento, se il file è stato spostato da tmp/
    elimina il file temporaneo originale se ancora presente.
    """
    if not instance.file:
        return
    
    current_path = instance.file.name
    # Se il file è ancora in tmp/, il _move_file_into_archivio lo sposterà
    # Ma potrebbe rimanere una copia se c'è stato un errore
    
    # Cleanup aggiuntivo: cerca file orfani nella stessa directory tmp
    if not current_path.startswith("tmp/"):
        # Il file è stato spostato con successo, possiamo pulire
        try:
            # Pattern: tmp/<anno>/<cliente>/<vecchio_nome>
            parts = current_path.split("/")
            if len(parts) >= 3:
                tmp_dir = Path(settings.MEDIA_ROOT) / "tmp" / parts[0] / parts[1]
                if tmp_dir.exists():
                    # Elimina eventuali file vecchi (stessa pratica/cliente)
                    for old_file in tmp_dir.glob("*"):
                        if old_file.is_file():
                            age_hours = (datetime.now().timestamp() - old_file.stat().st_mtime) / 3600
                            if age_hours > 1:  # Più vecchio di 1 ora
                                old_file.unlink()
                                logger.info(f"Rimosso file temporaneo: {old_file}")
        except Exception as e:
            logger.warning(f"Errore cleanup tmp per documento {instance.pk}: {e}")
```

---

### Soluzione 2: Path configurabili e portabili

**Modifica settings.py**:

```python
# mygest/settings.py

# ====================================
# Storage e Path Configurazione
# ====================================

# Path base archivio documentale
# Ambiente sviluppo: /mnt/archivio (WSL mount NAS)
# Ambiente produzione: /srv/mygest/archivio (VPS)
# Test: usa BASE_DIR / "test_archivio"
ARCHIVIO_BASE_PATH = os.getenv(
    "ARCHIVIO_BASE_PATH", 
    str(BASE_DIR / "media" / "archivio") if DEBUG else "/srv/mygest/archivio"
)

# Directory temporanea upload (relativa a MEDIA_ROOT)
UPLOAD_TEMP_DIR = os.getenv("UPLOAD_TEMP_DIR", "tmp")

# Directory sorgente per importazioni
# Supporta path multipli separati da ":" (come PATH)
IMPORTAZIONI_SOURCE_DIRS_STR = os.getenv(
    "IMPORTAZIONI_SOURCE_DIRS",
    str(BASE_DIR / "importazioni")  # Default: <project>/importazioni
)
IMPORTAZIONI_SOURCE_DIRS = [
    p.strip() for p in IMPORTAZIONI_SOURCE_DIRS_STR.split(":")
    if p.strip()
]

# Media URL per servire i file dell'archivio
MEDIA_URL = '/archivio/'
MEDIA_ROOT = ARCHIVIO_BASE_PATH

# Validazione: assicurati che le directory esistano
Path(ARCHIVIO_BASE_PATH).mkdir(parents=True, exist_ok=True)
for imp_dir in IMPORTAZIONI_SOURCE_DIRS:
    Path(imp_dir).mkdir(parents=True, exist_ok=True)
```

**File .env di esempio**:

```bash
# .env.example
# Copia questo file in .env e personalizza i valori

# Archivio documentale
ARCHIVIO_BASE_PATH=/mnt/archivio
UPLOAD_TEMP_DIR=tmp

# Importazioni (multipli separati da ":")
IMPORTAZIONI_SOURCE_DIRS=/home/utente/documenti:/mnt/archivio/importazioni

# Database
DATABASE_URL=postgresql://user:pass@localhost/mygest

# Secret key (CAMBIARE IN PRODUZIONE!)
SECRET_KEY=your-secret-key-here
```

**File .env.production di esempio**:

```bash
# .env.production
ARCHIVIO_BASE_PATH=/srv/mygest/archivio
UPLOAD_TEMP_DIR=tmp
IMPORTAZIONI_SOURCE_DIRS=/srv/mygest/importazioni
DATABASE_URL=postgresql://mygest_user:secure_password@localhost/mygest_prod
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=mygest.example.com,www.mygest.example.com
```

**Aggiornare documento_upload_to**:

```python
# documenti/models.py

def documento_upload_to(instance, filename):
    """
    Percorso provvisorio di upload (sotto MEDIA_ROOT/UPLOAD_TEMP_DIR).
    Il file verrà poi spostato nel NAS dentro 'percorso_archivio' in Documento.save().
    Struttura: {UPLOAD_TEMP_DIR}/<anno>/<cliente_code>/<filename>
    """
    from django.conf import settings
    
    # Anno
    d = getattr(instance, "data_documento", None) or timezone.now().date()
    year = d.year

    # Cliente (anche via fascicolo)
    cli = getattr(instance, "cliente", None)
    if cli is None and getattr(instance, "fascicolo_id", None):
        cli = instance.fascicolo.cliente

    # CLI uniforme (6+2). Se manca il cliente, usa fallback "VARIE"
    if cli:
        anag = getattr(cli, "anagrafica", cli)
        cli_code = get_or_generate_cli(anag)
    else:
        cli_code = "VARIE"
    
    temp_dir = getattr(settings, "UPLOAD_TEMP_DIR", "tmp")
    return f"{temp_dir}/{year}/{cli_code}/{filename}"
```

---

### Soluzione 3: Validazione dimensione file upload

**A) Configurazione settings.py**:

```python
# mygest/settings.py

# ====================================
# Upload File - Limiti e Sicurezza
# ====================================

# Dimensione massima file in upload (in bytes)
# Default: 50 MB per file singolo
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv(
    "FILE_UPLOAD_MAX_MEMORY_SIZE", 
    50 * 1024 * 1024  # 50 MB
))

# Dimensione massima totale richiesta (tutti i file + form data)
# Default: 100 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv(
    "DATA_UPLOAD_MAX_MEMORY_SIZE",
    100 * 1024 * 1024  # 100 MB
))

# Numero massimo campi in una richiesta POST
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Estensioni file permesse (globali)
ALLOWED_FILE_EXTENSIONS = [
    'pdf', 'docx', 'doc', 'xlsx', 'xls', 'odt', 'ods',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tif', 'tiff',
    'txt', 'csv', 'zip', 'rar', '7z',
    'eml', 'msg',  # Email
    'p7m', 'p7s',  # Firma digitale
]

# Estensioni file proibite (blacklist)
FORBIDDEN_FILE_EXTENSIONS = [
    'exe', 'bat', 'cmd', 'com', 'pif', 'scr',  # Eseguibili Windows
    'sh', 'bash', 'run',  # Script Unix
    'js', 'vbs', 'vbe', 'jar',  # Script
    'msi', 'dll', 'sys',  # Componenti sistema
]

# MIME types permessi (opzionale, per double-check)
ALLOWED_MIME_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/tiff',
    'text/plain',
    'application/zip',
    'message/rfc822',  # Email
]
```

**B) Creare validator personalizzato**:

```python
# documenti/validators.py (nuovo file)
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import magic  # python-magic per verifica MIME
import os


def validate_file_size(file):
    """
    Valida che il file non superi la dimensione massima configurata.
    """
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 50 * 1024 * 1024)
    
    if file.size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        file_size_mb = file.size / (1024 * 1024)
        raise ValidationError(
            _('Il file è troppo grande (%(file_size).2f MB). Dimensione massima consentita: %(max_size).2f MB.'),
            params={'file_size': file_size_mb, 'max_size': max_size_mb},
            code='file_too_large'
        )


def validate_file_extension(file):
    """
    Valida che l'estensione del file sia nella whitelist e non nella blacklist.
    """
    ext = os.path.splitext(file.name)[1][1:].lower()  # Rimuove il punto
    
    forbidden = getattr(settings, 'FORBIDDEN_FILE_EXTENSIONS', [])
    if ext in forbidden:
        raise ValidationError(
            _('Tipo di file non consentito: .%(extension)s'),
            params={'extension': ext},
            code='forbidden_extension'
        )
    
    allowed = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', None)
    if allowed and ext not in allowed:
        raise ValidationError(
            _('Estensione file non consentita: .%(extension)s. Estensioni permesse: %(allowed)s'),
            params={'extension': ext, 'allowed': ', '.join(allowed)},
            code='invalid_extension'
        )


def validate_file_mime_type(file):
    """
    Valida il MIME type reale del file (magic bytes) per prevenire spoofing.
    Richiede python-magic installato: pip install python-magic
    """
    allowed_mimes = getattr(settings, 'ALLOWED_MIME_TYPES', None)
    if not allowed_mimes:
        return  # Skip se non configurato
    
    try:
        # Leggi i primi bytes per determinare il tipo
        file.seek(0)
        file_mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)  # Reset position
        
        if file_mime not in allowed_mimes:
            raise ValidationError(
                _('Tipo di file non consentito: %(mime_type)s'),
                params={'mime_type': file_mime},
                code='invalid_mime_type'
            )
    except Exception as e:
        # Se python-magic non è disponibile, logga warning
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Impossibile validare MIME type: {e}")


def validate_file_content(file):
    """
    Validatore combinato che esegue tutti i controlli.
    """
    validate_file_size(file)
    validate_file_extension(file)
    validate_file_mime_type(file)


def validate_no_path_traversal(filename):
    """
    Previene path traversal attacks nel nome file.
    """
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValidationError(
            _('Nome file non valido. Non sono ammessi caratteri speciali di path.'),
            code='invalid_filename'
        )
```

**C) Applicare validator ai model**:

```python
# documenti/models.py
from .validators import validate_file_content

class Documento(models.Model):
    # ...
    file = models.FileField(
        storage=nas_storage, 
        upload_to=documento_upload_to, 
        blank=True, 
        null=True, 
        max_length=500,
        validators=[validate_file_content],  # <-- AGGIUNGERE
    )
    # ...
```

```python
# archivio_fisico/models.py
from documenti.validators import validate_file_content

class OperazioneArchivio(models.Model):
    # ...
    verbale_scan = models.FileField(
        storage=nas_storage,
        upload_to="archivio_fisico/operazioni",
        null=True,
        blank=True,
        max_length=500,
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png", "tif", "tiff"]),
            validate_file_content,  # <-- AGGIUNGERE
        ],
        help_text="Facoltativo: carica la scansione del verbale firmato.",
    )
    # ...
```

**D) Form-level validation (extra layer)**:

```python
# documenti/forms.py

from .validators import validate_file_content

class DocumentoDinamicoForm(ModelForm):
    # ...
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Validazione extra a livello form
            try:
                validate_file_content(file)
            except ValidationError as e:
                raise forms.ValidationError(str(e))
        return file
```

**E) View-level validation (per upload via API)**:

```python
# documenti/views.py (esempio)

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .validators import validate_file_content

@require_POST
@login_required
def upload_documento_api(request):
    file = request.FILES.get('file')
    if not file:
        return JsonResponse({'error': 'Nessun file ricevuto'}, status=400)
    
    try:
        validate_file_content(file)
    except ValidationError as e:
        return JsonResponse({'error': str(e)}, status=400)
    
    # Procedi con il salvataggio...
```

---

### Soluzione 4: Controlli antivirus sui file caricati

**Approccio A: Integrazione ClamAV (RACCOMANDATO per produzione)**

**1. Installare ClamAV sul server**:

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install clamav clamav-daemon

# Avvia il daemon
sudo systemctl start clamav-daemon
sudo systemctl enable clamav-daemon

# Aggiorna le definizioni virus
sudo freshclam
```

**2. Installare python-clamd**:

```bash
pip install clamd
```

Aggiungere a `requirements.txt`:
```
clamd==1.0.2
```

**3. Creare validator antivirus**:

```python
# documenti/validators.py (aggiungere)

import clamd
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


def get_clamd_client():
    """
    Connessione al daemon ClamAV.
    """
    socket_path = getattr(settings, 'CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')
    
    try:
        if socket_path:
            return clamd.ClamdUnixSocket(socket_path)
        else:
            # Fallback a TCP
            host = getattr(settings, 'CLAMAV_HOST', 'localhost')
            port = getattr(settings, 'CLAMAV_PORT', 3310)
            return clamd.ClamdNetworkSocket(host, port)
    except Exception as e:
        logger.error(f"Impossibile connettersi a ClamAV: {e}")
        return None


def validate_antivirus(file):
    """
    Scansiona il file con ClamAV per rilevare virus/malware.
    """
    # Check se antivirus è abilitato
    if not getattr(settings, 'ANTIVIRUS_ENABLED', False):
        return  # Skip se disabilitato
    
    cd = get_clamd_client()
    if not cd:
        # Se ClamAV non disponibile, comportamento dipende dalla configurazione
        if getattr(settings, 'ANTIVIRUS_REQUIRED', False):
            raise ValidationError(
                _('Servizio antivirus non disponibile. Impossibile validare il file.'),
                code='antivirus_unavailable'
            )
        else:
            logger.warning("ClamAV non disponibile, skip scansione antivirus")
            return
    
    try:
        # Leggi il file in memoria
        file.seek(0)
        file_data = file.read()
        file.seek(0)  # Reset position
        
        # Scansione
        result = cd.instream(file_data)
        
        # Analizza risultato
        # result = {'stream': ('FOUND', 'Eicar-Test-Signature')} se virus trovato
        # result = {'stream': ('OK', None)} se pulito
        status = result.get('stream')
        
        if status and status[0] == 'FOUND':
            virus_name = status[1]
            logger.warning(
                f"Virus rilevato in upload: {virus_name}, file: {file.name}"
            )
            raise ValidationError(
                _('File infetto rilevato: %(virus)s. Upload bloccato per motivi di sicurezza.'),
                params={'virus': virus_name},
                code='virus_detected'
            )
        
        elif status and status[0] == 'ERROR':
            error_msg = status[1]
            logger.error(f"Errore scansione ClamAV: {error_msg}")
            if getattr(settings, 'ANTIVIRUS_REQUIRED', False):
                raise ValidationError(
                    _('Errore durante la scansione antivirus. Riprovare.'),
                    code='antivirus_error'
                )
        
        # Se OK, passa
        logger.info(f"File {file.name} scansionato: pulito")
        
    except clamd.ClamdError as e:
        logger.error(f"Errore ClamAV: {e}")
        if getattr(settings, 'ANTIVIRUS_REQUIRED', False):
            raise ValidationError(
                _('Errore durante la scansione antivirus.'),
                code='antivirus_error'
            )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Errore generico scansione antivirus: {e}")
        if getattr(settings, 'ANTIVIRUS_REQUIRED', False):
            raise ValidationError(
                _('Errore durante la scansione antivirus.'),
                code='antivirus_error'
            )


# Aggiornare il validator combinato
def validate_file_content(file):
    """
    Validatore combinato che esegue tutti i controlli.
    """
    validate_file_size(file)
    validate_file_extension(file)
    validate_file_mime_type(file)
    validate_antivirus(file)  # <-- AGGIUNGERE
```

**4. Configurare settings.py**:

```python
# mygest/settings.py

# ====================================
# Antivirus - ClamAV
# ====================================

# Abilita/disabilita scansione antivirus
ANTIVIRUS_ENABLED = os.getenv('ANTIVIRUS_ENABLED', 'true').lower() == 'true'

# Se True, blocca l'upload se ClamAV non è disponibile
# Se False, logga warning ma permette upload se ClamAV down
ANTIVIRUS_REQUIRED = os.getenv('ANTIVIRUS_REQUIRED', 'false').lower() == 'true'

# Socket Unix (default per Debian/Ubuntu)
CLAMAV_SOCKET = os.getenv('CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')

# In alternativa, connessione TCP (se socket non disponibile)
CLAMAV_HOST = os.getenv('CLAMAV_HOST', 'localhost')
CLAMAV_PORT = int(os.getenv('CLAMAV_PORT', '3310'))
```

**5. Testing**:

```python
# documenti/tests/test_antivirus.py
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from documenti.validators import validate_antivirus
from django.core.exceptions import ValidationError


class AntivirusValidatorTest(TestCase):
    def test_clean_file(self):
        """Test file pulito passa la validazione"""
        file_content = b"PDF file content here"
        file = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        
        # Non dovrebbe sollevare eccezioni
        validate_antivirus(file)
    
    def test_eicar_virus(self):
        """Test file di test EICAR viene rilevato"""
        # EICAR test string (NON è un virus reale, solo per test antivirus)
        eicar = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
        file = SimpleUploadedFile("virus.txt", eicar, content_type="text/plain")
        
        with self.assertRaises(ValidationError) as cm:
            validate_antivirus(file)
        
        self.assertIn('virus_detected', cm.exception.code)
```

**Approccio B: Quarantena e scansione asincrona**

Per file molto grandi o per non bloccare l'utente:

```python
# documenti/tasks.py (usa Celery)
from celery import shared_task
from .validators import get_clamd_client
from .models import Documento
import logging

logger = logging.getLogger(__name__)


@shared_task
def scan_documento_async(documento_id):
    """
    Scansione asincrona di un documento appena caricato.
    Se il virus viene trovato, marca il documento come infetto.
    """
    try:
        doc = Documento.objects.get(pk=documento_id)
        
        if not doc.file:
            return
        
        cd = get_clamd_client()
        if not cd:
            logger.warning(f"ClamAV non disponibile per documento {documento_id}")
            return
        
        # Scansiona
        with doc.file.open('rb') as f:
            result = cd.instream(f.read())
        
        status = result.get('stream')
        
        if status and status[0] == 'FOUND':
            virus_name = status[1]
            logger.critical(
                f"VIRUS TROVATO nel documento {documento_id}: {virus_name}"
            )
            
            # Marca il documento come infetto
            doc.tags = f"VIRUS:{virus_name}"
            doc.note = f"[AUTOMATICO] File infetto rilevato: {virus_name}. Upload bloccato."
            doc.save(update_fields=['tags', 'note'])
            
            # Opzionale: elimina il file
            # doc.file.delete(save=False)
            
            # Notifica admin
            from django.core.mail import mail_admins
            mail_admins(
                subject=f"VIRUS RILEVATO - Documento {doc.codice}",
                message=f"Virus trovato nel documento {doc.codice} (ID: {doc.pk}):\n"
                        f"Virus: {virus_name}\n"
                        f"File: {doc.file.name}\n"
                        f"Cliente: {doc.cliente}\n"
                        f"Azione: File marcato come infetto."
            )
        else:
            logger.info(f"Documento {documento_id} scansionato: pulito")
            # Opzionale: marca come scansionato
            # doc.tags = "scanned:ok"
            # doc.save(update_fields=['tags'])
    
    except Documento.DoesNotExist:
        logger.error(f"Documento {documento_id} non trovato per scansione")
    except Exception as e:
        logger.error(f"Errore scansione asincrona documento {documento_id}: {e}")


# Nel signal o nella view dopo il save:
from .tasks import scan_documento_async

@receiver(post_save, sender=Documento)
def schedule_antivirus_scan(sender, instance, created, **kwargs):
    """Schedula scansione antivirus asincrona dopo upload"""
    if created and instance.file:
        scan_documento_async.delay(instance.pk)
```

---

## Implementazione Completa

### File da creare

1. **`documenti/validators.py`** (NUOVO)
   - Validatori dimensione, estensione, MIME, antivirus

2. **`documenti/management/commands/cleanup_tmp.py`** (NUOVO)
   - Comando pulizia file temporanei

3. **`documenti/signals.py`** (NUOVO o aggiornare esistente)
   - Signal per cleanup automatico

4. **`documenti/tasks.py`** (NUOVO, opzionale con Celery)
   - Task asincroni per scansione antivirus

### File da modificare

1. **`mygest/settings.py`**
   - Aggiungere configurazioni path, dimensioni, antivirus

2. **`documenti/models.py`**
   - Aggiornare `documento_upload_to()` per usare `UPLOAD_TEMP_DIR`
   - Aggiungere validators a campo `file`

3. **`archivio_fisico/models.py`**
   - Aggiungere validators a campo `verbale_scan`

4. **`requirements.txt`**
   - Aggiungere `python-magic`, `clamd`

### Dipendenze da installare

```bash
pip install python-magic clamd
```

Per Ubuntu/Debian:
```bash
sudo apt-get install libmagic1 python3-magic
```

### File .env da aggiornare

```bash
# File Storage
ARCHIVIO_BASE_PATH=/mnt/archivio
UPLOAD_TEMP_DIR=tmp
IMPORTAZIONI_SOURCE_DIRS=/home/utente/documenti:/mnt/archivio/importazioni

# Upload Limits
FILE_UPLOAD_MAX_MEMORY_SIZE=52428800  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE=104857600  # 100 MB

# Antivirus
ANTIVIRUS_ENABLED=true
ANTIVIRUS_REQUIRED=false
CLAMAV_SOCKET=/var/run/clamav/clamd.ctl
```

---

## Priorità Implementazione

### Priorità ALTA (implementare subito)
1. ✅ **Path configurabili** - Risolve problemi di portabilità
2. ✅ **Validazione dimensione file** - Previene DoS e problemi memoria
3. ✅ **Validazione estensioni/MIME** - Primo livello sicurezza

### Priorità MEDIA (entro 1-2 settimane)
4. ✅ **Pulizia automatica tmp/** - Previene accumulo spazio disco
5. ✅ **Controlli antivirus** - Sicurezza critica per documenti

### Priorità BASSA (opzionale/futuro)
6. Scansione asincrona con Celery
7. Quarantena file sospetti
8. Dashboard monitoring upload/virus

---

## Test da Eseguire

### Test 1: Dimensione file
```bash
# Creare file test di 60MB
dd if=/dev/urandom of=test_60mb.pdf bs=1M count=60

# Tentare upload - dovrebbe fallire con errore dimensione
```

### Test 2: Estensione proibita
```bash
# Tentare upload di file .exe - dovrebbe fallire
```

### Test 3: MIME spoofing
```bash
# Rinominare un .exe in .pdf - dovrebbe fallire su MIME check
mv malware.exe malware.pdf
```

### Test 4: Antivirus
```bash
# Test con EICAR (stringa test standard antivirus)
echo 'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*' > eicar.txt
# Upload dovrebbe essere bloccato da ClamAV
```

### Test 5: Pulizia tmp
```bash
# Creare file vecchi in tmp
touch -d "10 days ago" media/tmp/2024/TEST/old_file.pdf

# Eseguire comando cleanup
python manage.py cleanup_tmp --days=7

# Verificare che il file sia stato eliminato
```

---

## Monitoraggio e Logging

### Metriche da monitorare

1. **Spazio disco tmp/**
   ```bash
   du -sh media/tmp/
   ```

2. **File rifiutati per dimensione**
   ```bash
   grep "file_too_large" logs/django.log | wc -l
   ```

3. **Virus rilevati**
   ```bash
   grep "VIRUS TROVATO" logs/django.log
   ```

4. **Pulizia tmp eseguita**
   ```bash
   grep "cleanup_tmp" logs/cron.log
   ```

### Alert da configurare

1. Alert se `tmp/` supera 1GB
2. Alert se virus rilevato
3. Alert se ClamAV down per > 1 ora
4. Alert se rate upload anomalo (possibile DoS)

---

## Conformità GDPR

Le soluzioni proposte migliorano la conformità GDPR:

- ✅ **Art. 32**: Sicurezza del trattamento (antivirus, validazioni)
- ✅ **Art. 25**: Privacy by design (validazioni preventive)
- ✅ **Art. 5**: Limitazione della conservazione (pulizia tmp/)
- ✅ **Art. 32**: Integrità e riservatezza (protezione da malware)

---

## Conclusioni

Le modifiche proposte risolvono completamente i 4 problemi identificati:

1. ✅ **tmp/ non pulita** → Comando cleanup + signal automatico
2. ✅ **Path hardcoded** → Variabili ambiente + .env configurabile
3. ✅ **No validazione dimensione** → Settings + validators multi-livello
4. ✅ **No antivirus** → Integrazione ClamAV + scansione asincrona

**Benefici**:
- Sicurezza migliorata significativamente
- Codice portabile e configurabile
- Prevenzione DoS e malware
- Gestione automatica spazio disco
- Conformità normativa migliorata

**Effort stimato**: 1-2 giorni sviluppo + 1 giorno testing
