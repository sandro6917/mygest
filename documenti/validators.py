"""
Validators per upload file - Sicurezza e validazione

Questo modulo fornisce validatori per controllare:
- Dimensione file
- Estensioni permesse/proibite
- MIME type reale (magic bytes)
- Scansione antivirus con ClamAV
- Path traversal prevention
"""

from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import os
import logging

logger = logging.getLogger(__name__)


def validate_file_size(file):
    """
    Valida che il file non superi la dimensione massima configurata.
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: Se il file supera FILE_UPLOAD_MAX_MEMORY_SIZE
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
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: Se l'estensione è proibita o non permessa
    """
    ext = os.path.splitext(file.name)[1][1:].lower()  # Rimuove il punto
    
    # Check blacklist
    forbidden = getattr(settings, 'FORBIDDEN_FILE_EXTENSIONS', [])
    if ext in forbidden:
        raise ValidationError(
            _('Tipo di file non consentito: .%(extension)s'),
            params={'extension': ext},
            code='forbidden_extension'
        )
    
    # Check whitelist
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
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: Se il MIME type non è permesso
    """
    allowed_mimes = getattr(settings, 'ALLOWED_MIME_TYPES', None)
    if not allowed_mimes:
        return  # Skip se non configurato
    
    try:
        import magic
        
        # Leggi i primi bytes per determinare il tipo
        file.seek(0)
        file_data = file.read(2048)
        file.seek(0)  # Reset position
        
        file_mime = magic.from_buffer(file_data, mime=True)
        
        if file_mime not in allowed_mimes:
            raise ValidationError(
                _('Tipo di file non consentito: %(mime_type)s'),
                params={'mime_type': file_mime},
                code='invalid_mime_type'
            )
    except ImportError:
        # python-magic non installato
        logger.warning("python-magic non disponibile, skip validazione MIME type")
    except Exception as e:
        # Errore nella validazione MIME
        logger.warning(f"Impossibile validare MIME type: {e}")


def validate_no_path_traversal(filename):
    """
    Previene path traversal attacks nel nome file.
    
    Args:
        filename: Nome del file
        
    Raises:
        ValidationError: Se il filename contiene caratteri pericolosi
    """
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValidationError(
            _('Nome file non valido. Non sono ammessi caratteri speciali di path.'),
            code='invalid_filename'
        )


def get_clamd_client():
    """
    Connessione al daemon ClamAV.
    
    Returns:
        clamd.ClamdUnixSocket o clamd.ClamdNetworkSocket o None se non disponibile
    """
    try:
        import clamd
    except ImportError:
        logger.warning("clamd non installato, skip antivirus")
        return None
    
    socket_path = getattr(settings, 'CLAMAV_SOCKET', '/var/run/clamav/clamd.ctl')
    
    try:
        if socket_path and os.path.exists(socket_path):
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
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: Se virus rilevato o se antivirus richiesto ma non disponibile
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
        
    except ImportError:
        logger.warning("clamd non installato")
        if getattr(settings, 'ANTIVIRUS_REQUIRED', False):
            raise ValidationError(
                _('Libreria antivirus non disponibile.'),
                code='antivirus_unavailable'
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


def validate_file_content(file):
    """
    Validatore combinato che esegue tutti i controlli di sicurezza.
    
    Esegue nell'ordine:
    1. Validazione dimensione file
    2. Validazione estensione (blacklist/whitelist)
    3. Validazione MIME type reale
    4. Scansione antivirus
    
    Args:
        file: UploadedFile object
        
    Raises:
        ValidationError: Se uno dei controlli fallisce
    """
    validate_file_size(file)
    validate_file_extension(file)
    validate_file_mime_type(file)
    validate_antivirus(file)


def validate_uploaded_file(
    file,
    check_size=True,
    check_extension=True,
    check_content=True,
    antivirus=True,
    max_size_mb=None,
    allowed=None,
    forbidden=None,
    allowed_mime_types=None
):
    """
    Validatore completo e configurabile per file upload.
    
    Questa è la funzione principale da usare nelle form e nelle view.
    Permette di scegliere quali validazioni eseguire.
    
    Args:
        file: UploadedFile object
        check_size: Se True, valida dimensione file (default: True)
        check_extension: Se True, valida estensione (default: True)
        check_content: Se True, valida MIME type reale (default: True)
        antivirus: Se True, esegue scansione antivirus (default: True)
        max_size_mb: Dimensione massima in MB (default: da settings)
        allowed: Lista estensioni permesse (default: da settings)
        forbidden: Lista estensioni proibite (default: da settings)
        allowed_mime_types: Lista MIME types permessi (default: da settings)
    
    Raises:
        ValidationError: Se uno dei controlli fallisce
        
    Example:
        >>> from django.core.files.uploadedfile import SimpleUploadedFile
        >>> file = SimpleUploadedFile("test.pdf", b"content")
        >>> validate_uploaded_file(file)  # Validazione completa
        >>> validate_uploaded_file(file, antivirus=False)  # Skip antivirus
        >>> validate_uploaded_file(file, check_size=True, check_extension=True)  # Solo size e estensione
    """
    # Validazione dimensione
    if check_size:
        if max_size_mb:
            # Temporaneamente sovrascrivi il setting
            original_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', None)
            settings.FILE_UPLOAD_MAX_MEMORY_SIZE = max_size_mb * 1024 * 1024
            try:
                validate_file_size(file)
            finally:
                if original_size:
                    settings.FILE_UPLOAD_MAX_MEMORY_SIZE = original_size
        else:
            validate_file_size(file)
    
    # Validazione estensione
    if check_extension:
        if allowed or forbidden:
            # Temporaneamente sovrascrivi i settings
            original_allowed = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', None)
            original_forbidden = getattr(settings, 'FORBIDDEN_FILE_EXTENSIONS', None)
            
            if allowed:
                settings.ALLOWED_FILE_EXTENSIONS = allowed
            if forbidden:
                settings.FORBIDDEN_FILE_EXTENSIONS = forbidden
            
            try:
                validate_file_extension(file)
            finally:
                if original_allowed:
                    settings.ALLOWED_FILE_EXTENSIONS = original_allowed
                if original_forbidden:
                    settings.FORBIDDEN_FILE_EXTENSIONS = original_forbidden
        else:
            validate_file_extension(file)
    
    # Validazione MIME type
    if check_content:
        if allowed_mime_types:
            # Temporaneamente sovrascrivi il setting
            original_mimes = getattr(settings, 'ALLOWED_MIME_TYPES', None)
            settings.ALLOWED_MIME_TYPES = allowed_mime_types
            try:
                validate_file_mime_type(file)
            finally:
                if original_mimes:
                    settings.ALLOWED_MIME_TYPES = original_mimes
        else:
            validate_file_mime_type(file)
    
    # Scansione antivirus
    if antivirus:
        validate_antivirus(file)
    
    # Nome file sicuro (sempre)
    # Per file già esistenti (con percorso completo), valida solo il basename
    filename_to_check = file.name
    if hasattr(file, 'name') and ('/' in file.name or '\\' in file.name):
        # È un percorso completo, estrai solo il basename
        filename_to_check = os.path.basename(file.name)
    validate_no_path_traversal(filename_to_check)
