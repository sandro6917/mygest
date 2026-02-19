"""
Utility per gestione e rilevamento tipi di file
"""
import os
import magic
from typing import Optional, Tuple
from pathlib import Path


class FileTypeDetector:
    """Rilevatore tipo di file basato su MIME type e estensione"""
    
    # Mapping MIME types supportati
    SUPPORTED_MIME_TYPES = {
        'application/pdf': '.pdf',
        'text/plain': '.txt',
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/tiff': '.tiff',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    }
    
    @staticmethod
    def detect_mime_type(file_path: str) -> Optional[str]:
        """
        Rileva il MIME type di un file usando python-magic.
        
        Args:
            file_path: Percorso del file
            
        Returns:
            MIME type string o None se non rilevabile
        """
        try:
            mime = magic.Magic(mime=True)
            return mime.from_file(file_path)
        except Exception as e:
            # Fallback: prova con estensione
            ext = Path(file_path).suffix.lower()
            for mime_type, extension in FileTypeDetector.SUPPORTED_MIME_TYPES.items():
                if ext == extension:
                    return mime_type
            return None
    
    @staticmethod
    def is_supported_file(file_path: str, allowed_extensions: list = None) -> bool:
        """
        Verifica se un file è supportato per l'elaborazione.
        
        Args:
            file_path: Percorso del file
            allowed_extensions: Lista estensioni permesse (es: ['.pdf', '.jpg'])
            
        Returns:
            True se file supportato, False altrimenti
        """
        ext = Path(file_path).suffix.lower()
        
        if allowed_extensions:
            return ext in allowed_extensions
        
        # Default: usa estensioni da SUPPORTED_MIME_TYPES
        return ext in FileTypeDetector.SUPPORTED_MIME_TYPES.values()
    
    @staticmethod
    def get_file_info(file_path: str) -> Tuple[str, int, str]:
        """
        Ottiene informazioni base su un file.
        
        Args:
            file_path: Percorso del file
            
        Returns:
            Tupla (file_name, file_size_bytes, mime_type)
        """
        path = Path(file_path)
        file_name = path.name
        file_size = path.stat().st_size if path.exists() else 0
        mime_type = FileTypeDetector.detect_mime_type(file_path) or 'application/octet-stream'
        
        return file_name, file_size, mime_type


class PathValidator:
    """Validatore e normalizzatore percorsi directory"""
    
    @staticmethod
    def is_valid_path(path: str) -> bool:
        """
        Verifica se un path è valido e accessibile.
        Supporta path locali, UNC Windows (\\\\server\\share), e mounted shares.
        
        Args:
            path: Percorso da validare
            
        Returns:
            True se path valido e accessibile
        """
        if not path:
            return False
        
        try:
            # Converti a Path object
            p = Path(path)
            
            # Verifica esistenza
            return p.exists() and p.is_dir()
        except Exception:
            return False
    
    @staticmethod
    def normalize_path(path: str) -> str:
        """
        Normalizza un percorso (risolve .., ., espande ~, etc.)
        
        Args:
            path: Percorso da normalizzare
            
        Returns:
            Percorso normalizzato
        """
        try:
            return str(Path(path).resolve())
        except Exception:
            return path
    
    @staticmethod
    def is_network_path(path: str) -> bool:
        """
        Verifica se un path è un percorso di rete (UNC Windows o mount).
        
        Args:
            path: Percorso da verificare
            
        Returns:
            True se percorso di rete
        """
        # Windows UNC path: \\server\share
        if path.startswith('\\\\') or path.startswith('//'):
            return True
        
        # Linux mount point: controlla se mounted
        try:
            p = Path(path)
            # Se il path è in /mnt/ o /media/, probabilmente è un mount
            if any(parent.name in ['mnt', 'media'] for parent in p.parents):
                return True
        except Exception:
            pass
        
        return False
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """
        Sanitizza un path per prevenire directory traversal attacks.
        
        Args:
            path: Percorso da sanitizzare
            
        Returns:
            Percorso sicuro
        """
        # Rimuovi sequenze pericolose
        dangerous_patterns = ['..', '~', '$']
        sanitized = path
        
        for pattern in dangerous_patterns:
            sanitized = sanitized.replace(pattern, '')
        
        return sanitized
