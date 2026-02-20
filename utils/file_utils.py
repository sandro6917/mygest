"""
File Utilities - Funzioni per la gestione di file e storage
"""
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def get_unique_filename(storage, destination_path):
    """
    Genera un nome file unico aggiungendo un suffisso numerico progressivo se necessario.
    
    Args:
        storage: Django storage instance
        destination_path: Percorso di destinazione desiderato
    
    Returns:
        str: Percorso unico (originale o con suffisso numerico)
    
    Example:
        documento.pdf -> documento_1.pdf -> documento_2.pdf
    """
    if not storage.exists(destination_path):
        return destination_path
    
    base_dir = os.path.dirname(destination_path)
    filename = os.path.basename(destination_path)
    name, ext = os.path.splitext(filename)
    
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        new_path = os.path.join(base_dir, new_filename) if base_dir else new_filename
        if not storage.exists(new_path):
            return new_path
        counter += 1


def ensure_directory(path):
    """
    Crea una directory se non esiste.
    
    Args:
        path: Percorso della directory da creare
    
    Returns:
        bool: True se creata o già esistente, False in caso di errore
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Errore nella creazione della directory {path}: {str(e)}")
        return False


def move_to_orphaned(storage, source_path, orphaned_dir="FileNonAssociati"):
    """
    Sposta un file in una cartella di file orfani/non associati.
    Non sovrascrive file esistenti, aggiunge un suffisso numerico.
    
    Args:
        storage: Django storage instance
        source_path: Percorso del file sorgente
        orphaned_dir: Nome della cartella di destinazione (default: "FileNonAssociati")
    
    Returns:
        str: Percorso di destinazione finale, o None in caso di errore
    """
    if not storage.exists(source_path):
        logger.warning(f"File sorgente {source_path} non trovato")
        return None
    
    try:
        # Prepara percorso di destinazione
        filename = os.path.basename(source_path)
        destination_path = os.path.join(orphaned_dir, filename)
        
        # Ottieni un nome file unico se esiste già
        unique_destination = get_unique_filename(storage, destination_path)
        
        # Crea la directory se non esiste
        dest_dir_path = os.path.join(settings.ARCHIVIO_BASE_PATH, orphaned_dir)
        ensure_directory(dest_dir_path)
        
        # Sposta il file (copia + cancella originale)
        with storage.open(source_path, 'rb') as source_file:
            storage.save(unique_destination, source_file)
        
        storage.delete(source_path)
        
        logger.info(f"File spostato: {source_path} -> {unique_destination}")
        return unique_destination
        
    except Exception as e:
        logger.error(f"Errore nello spostamento del file {source_path}: {str(e)}")
        return None


def get_file_extension(filename):
    """
    Estrae l'estensione da un nome file.
    
    Args:
        filename: Nome del file
    
    Returns:
        str: Estensione (senza punto) in minuscolo, o stringa vuota
    """
    if not filename:
        return ""
    _, ext = os.path.splitext(filename)
    return ext.lstrip('.').lower()


def format_file_size(size_bytes):
    """
    Formatta una dimensione in bytes in formato leggibile (KB, MB, GB).
    
    Args:
        size_bytes: Dimensione in bytes
    
    Returns:
        str: Dimensione formattata (es: "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
