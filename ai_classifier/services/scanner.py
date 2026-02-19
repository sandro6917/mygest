"""
Scanner per directory - scansiona ricorsivamente file in una directory
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..utils.file_handlers import FileTypeDetector, PathValidator

logger = logging.getLogger(__name__)


class DirectoryScanner:
    """
    Scanner per directory che identifica tutti i file processabili.
    Supporta directory locali, NAS, e Windows shares (SMB/UNC).
    """
    
    def __init__(
        self,
        directory_path: str,
        allowed_extensions: Optional[List[str]] = None,
        max_file_size_mb: int = 50,
        recursive: bool = True
    ):
        """
        Inizializza lo scanner.
        
        Args:
            directory_path: Path della directory da scansionare
            allowed_extensions: Lista estensioni permesse (es: ['.pdf', '.jpg'])
            max_file_size_mb: Dimensione massima file in MB
            recursive: Se True, scansiona sottocartelle ricorsivamente
        """
        self.directory_path = directory_path
        self.allowed_extensions = allowed_extensions or ['.pdf', '.txt', '.jpg', '.jpeg', '.png', '.tiff', '.docx']
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.recursive = recursive
        
        # Statistiche scansione
        self.total_files = 0
        self.valid_files = 0
        self.skipped_files = 0
        self.errors = []
    
    def validate_directory(self) -> bool:
        """
        Valida che la directory sia accessibile.
        
        Returns:
            True se directory valida e accessibile
        """
        if not PathValidator.is_valid_path(self.directory_path):
            error_msg = f"Directory non valida o inaccessibile: {self.directory_path}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
        
        # Log info su tipo di path
        if PathValidator.is_network_path(self.directory_path):
            logger.info(f"Scanning network path: {self.directory_path}")
        else:
            logger.info(f"Scanning local path: {self.directory_path}")
        
        return True
    
    def scan(self) -> List[Dict[str, Any]]:
        """
        Scansiona la directory e ritorna lista di file processabili.
        
        Returns:
            Lista di dict con informazioni su ogni file:
            {
                'file_path': str,
                'file_name': str,
                'file_size': int (bytes),
                'mime_type': str,
                'extension': str
            }
        """
        if not self.validate_directory():
            return []
        
        files = []
        
        try:
            # Usa Path.rglob per scansione ricorsiva o glob per non ricorsiva
            path_obj = Path(self.directory_path)
            
            if self.recursive:
                # Scansione ricorsiva
                pattern = '**/*'
                file_iter = path_obj.rglob('*')
            else:
                # Solo directory root
                file_iter = path_obj.glob('*')
            
            for file_path in file_iter:
                # Salta directory
                if not file_path.is_file():
                    continue
                
                self.total_files += 1
                
                # Verifica estensione
                if not FileTypeDetector.is_supported_file(str(file_path), self.allowed_extensions):
                    logger.debug(f"Skipping unsupported file: {file_path.name}")
                    self.skipped_files += 1
                    continue
                
                # Verifica dimensione
                file_size = file_path.stat().st_size
                if file_size > self.max_file_size_bytes:
                    logger.warning(
                        f"Skipping file too large ({file_size / 1024 / 1024:.2f} MB): {file_path.name}"
                    )
                    self.skipped_files += 1
                    continue
                
                # Ottieni info file
                try:
                    file_name, file_size, mime_type = FileTypeDetector.get_file_info(str(file_path))
                    
                    files.append({
                        'file_path': str(file_path),
                        'file_name': file_name,
                        'file_size': file_size,
                        'mime_type': mime_type,
                        'extension': file_path.suffix.lower()
                    })
                    
                    self.valid_files += 1
                    
                except Exception as e:
                    error_msg = f"Error reading file {file_path.name}: {str(e)}"
                    logger.error(error_msg)
                    self.errors.append(error_msg)
                    continue
        
        except Exception as e:
            error_msg = f"Error scanning directory: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
        
        logger.info(
            f"Scan complete: {self.total_files} total, "
            f"{self.valid_files} valid, {self.skipped_files} skipped"
        )
        
        return files
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Ritorna statistiche della scansione.
        
        Returns:
            Dict con statistiche
        """
        return {
            'total_files': self.total_files,
            'valid_files': self.valid_files,
            'skipped_files': self.skipped_files,
            'errors_count': len(self.errors),
            'errors': self.errors
        }


class SMBScanner(DirectoryScanner):
    """
    Scanner specializzato per Windows shares (SMB/CIFS).
    Estende DirectoryScanner con supporto specifico per SMB.
    """
    
    def __init__(
        self,
        smb_path: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """
        Inizializza scanner SMB.
        
        Args:
            smb_path: Path UNC (es: \\\\server\\share\\folder o //server/share/folder)
            username: Username per autenticazione (opzionale se già montato)
            password: Password per autenticazione (opzionale)
            **kwargs: Altri parametri per DirectoryScanner
        """
        super().__init__(smb_path, **kwargs)
        self.username = username
        self.password = password
    
    def validate_directory(self) -> bool:
        """
        Valida accesso a share SMB.
        Assume che lo share sia già montato nel filesystem.
        """
        # Per ora, delega al PathValidator standard
        # In futuro, può implementare mounting automatico con smbclient
        
        is_valid = super().validate_directory()
        
        if is_valid and PathValidator.is_network_path(self.directory_path):
            logger.info(f"SMB share accessible: {self.directory_path}")
        
        return is_valid
