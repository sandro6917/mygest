"""
Classe base per importatori di documenti.
Definisce l'interfaccia che tutti gli importatori devono implementare.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
import logging

if TYPE_CHECKING:
    from documenti.models import ImportSession
    from django.contrib.auth.models import User
    from documenti.models import Documento

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Risultato del parsing di un singolo documento"""
    success: bool
    parsed_data: Dict[str, Any]
    anagrafiche_reperite: List[Dict[str, Any]]
    valori_editabili: Dict[str, Any]
    mappatura_db: Dict[str, Any]
    error_message: str = ""
    error_traceback: str = ""


class BaseImporter(ABC):
    """
    Classe base astratta per tutti gli importatori di documenti.
    
    Ogni importatore deve:
    1. Estendere questa classe
    2. Implementare i metodi astratti
    3. Registrarsi con @ImporterRegistry.register
    
    Esempio:
        @ImporterRegistry.register
        class MioImporter(BaseImporter):
            tipo = 'mio_tipo'
            display_name = 'Mio Tipo Documento'
            ...
    """
    
    # Metadata (da sovrascrivere nelle sottoclassi)
    tipo: Optional[str] = None  # 'cedolini', 'unilav', etc.
    display_name: Optional[str] = None
    supported_extensions: List[str] = []  # ['.pdf', '.zip']
    max_file_size_mb: int = 500
    batch_mode: bool = True  # Se supporta multi-documento (ZIP)
    
    def __init__(self, session: 'ImportSession'):
        """
        Inizializza l'importatore con una sessione.
        
        Args:
            session: Sessione di importazione attiva
        """
        self.session = session
    
    @abstractmethod
    def extract_documents(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Estrae lista documenti dal file caricato.
        
        Per file ZIP: estrae tutti i file supportati
        Per file singolo: ritorna lista con un elemento
        
        Args:
            file_path: Path al file originale caricato
            
        Returns:
            List di dict con:
            {
                'filename': str,          # Nome file estratto
                'file_path': str,         # Path completo file estratto
                'file_size': int,         # Dimensione in bytes
                'ordine': int,            # Posizione nella lista (opzionale)
            }
            
        Raises:
            ValueError: Se il file non è valido
        """
        pass
    
    @abstractmethod
    def parse_document(self, file_path: str, filename: str) -> ParseResult:
        """
        Parserizza singolo documento ed estrae dati strutturati.
        
        Args:
            file_path: Path completo al file da parsare
            filename: Nome originale del file
            
        Returns:
            ParseResult con:
            - success: True se parsing ok, False se errore
            - parsed_data: Dati estratti (struttura dipende dal tipo)
            - anagrafiche_reperite: Lista anagrafiche matchate nel DB
            - valori_editabili: Campi modificabili dall'utente
            - mappatura_db: Preview campi che andranno nel DB
            - error_message: Messaggio errore (se success=False)
            - error_traceback: Traceback completo (se success=False)
        """
        pass
    
    @abstractmethod
    def create_documento(
        self, 
        parsed_data: Dict[str, Any],
        valori_editati: Dict[str, Any],
        user: 'User',
        **kwargs
    ) -> 'Documento':
        """
        Crea documento nel DB dai dati parsati + valori editati dall'utente.
        
        Args:
            parsed_data: Dati estratti dal parser (da ImportSessionDocument.parsed_data)
            valori_editati: Valori modificati dall'utente (merge con parsed_data)
            user: Utente che sta eseguendo l'importazione
            **kwargs: Parametri aggiuntivi (es. fascicolo_id, cliente_id)
            
        Returns:
            Documento creato e salvato nel DB
            
        Raises:
            ValidationError: Se i dati non sono validi
            IntegrityError: Se violazione vincoli DB
        """
        pass
    
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """
        Validazione file uploadato (estensione, dimensione, formato).
        
        Implementazione di default: controlla estensione e dimensione.
        Può essere sovrascritto per validazioni custom.
        
        Args:
            file_path: Path al file da validare
            
        Returns:
            Tuple (is_valid, error_message)
            - is_valid: True se valido, False altrimenti
            - error_message: Descrizione errore (vuoto se valido)
        """
        import os
        
        if not os.path.exists(file_path):
            return False, "File non trovato"
        
        # Controlla dimensione
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > self.max_file_size_mb:
            return False, f"File troppo grande: {file_size_mb:.1f}MB (max {self.max_file_size_mb}MB)"
        
        # Controlla estensione
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_extensions:
            return False, f"Estensione {ext} non supportata. Estensioni valide: {', '.join(self.supported_extensions)}"
        
        return True, ""
    
    def match_anagrafica(self, codice_fiscale: str) -> Optional[Dict[str, Any]]:
        """
        Helper per match anagrafica da codice fiscale.
        
        Riutilizzabile da tutti gli importatori.
        
        Args:
            codice_fiscale: CF da cercare (case-insensitive)
            
        Returns:
            Dict con info anagrafica se trovata:
            {
                'id': int,
                'codice_fiscale': str,
                'nome': str,
                'match_type': 'exact' | 'multiple',
                'cliente_id': int | None,
            }
            None se non trovata
        """
        from anagrafiche.models import Anagrafica
        
        try:
            anagrafica = Anagrafica.objects.get(codice_fiscale__iexact=codice_fiscale)
            return {
                'id': anagrafica.id,
                'codice_fiscale': anagrafica.codice_fiscale,
                'nome': str(anagrafica),
                'match_type': 'exact',
                'cliente_id': getattr(anagrafica.cliente, 'id', None) if hasattr(anagrafica, 'cliente') else None,
            }
        except Anagrafica.DoesNotExist:
            logger.debug(f"Anagrafica con CF {codice_fiscale} non trovata")
            return None
        except Anagrafica.MultipleObjectsReturned:
            # Prendi il primo (potrebbe servire logica più sofisticata)
            anagrafica = Anagrafica.objects.filter(codice_fiscale__iexact=codice_fiscale).first()
            logger.warning(f"Trovate multiple anagrafiche con CF {codice_fiscale}, uso la prima: {anagrafica.id}")
            return {
                'id': anagrafica.id,
                'codice_fiscale': anagrafica.codice_fiscale,
                'nome': str(anagrafica),
                'match_type': 'multiple',
                'cliente_id': getattr(anagrafica.cliente, 'id', None) if hasattr(anagrafica, 'cliente') else None,
            }


class ImporterRegistry:
    """
    Registry pattern per gestire tutti gli importatori.
    
    Uso:
        # Registrare un importatore
        @ImporterRegistry.register
        class MioImporter(BaseImporter):
            ...
        
        # Recuperare un importatore
        importer_class = ImporterRegistry.get_importer('cedolini')
        importer = importer_class(session)
        
        # Lista tipi disponibili
        tipi = ImporterRegistry.get_all_types()
    """
    
    _importers: Dict[str, type[BaseImporter]] = {}
    
    @classmethod
    def register(cls, importer_class: type[BaseImporter]):
        """
        Decorator per registrare un importatore.
        
        Args:
            importer_class: Classe che estende BaseImporter
            
        Returns:
            La classe stessa (per permettere uso come decorator)
            
        Raises:
            ValueError: Se la classe non ha 'tipo' definito
        """
        if not importer_class.tipo:
            raise ValueError(
                f"Importatore {importer_class.__name__} deve avere attributo 'tipo' definito"
            )
        
        if importer_class.tipo in cls._importers:
            logger.warning(
                f"Importatore '{importer_class.tipo}' già registrato, "
                f"sovrascrittura da {cls._importers[importer_class.tipo].__name__} "
                f"a {importer_class.__name__}"
            )
        
        cls._importers[importer_class.tipo] = importer_class
        logger.info(f"Registrato importatore: {importer_class.tipo} ({importer_class.__name__})")
        
        return importer_class
    
    @classmethod
    def get_importer(cls, tipo: str) -> type[BaseImporter]:
        """
        Recupera classe importatore per tipo.
        
        Args:
            tipo: Tipo importazione (es. 'cedolini', 'unilav')
            
        Returns:
            Classe importatore
            
        Raises:
            ValueError: Se tipo non registrato
        """
        if tipo not in cls._importers:
            available = ', '.join(cls._importers.keys())
            raise ValueError(
                f"Importatore '{tipo}' non registrato. "
                f"Disponibili: {available}"
            )
        return cls._importers[tipo]
    
    @classmethod
    def get_all_types(cls) -> List[Dict[str, Any]]:
        """
        Lista tipi importazione disponibili.
        
        Returns:
            Lista di dict con info su ogni tipo:
            [
                {
                    'tipo': str,
                    'display_name': str,
                    'supported_extensions': List[str],
                    'batch_mode': bool,
                    'max_file_size_mb': int,
                },
                ...
            ]
        """
        return [
            {
                'tipo': tipo,
                'display_name': imp.display_name,
                'supported_extensions': imp.supported_extensions,
                'batch_mode': imp.batch_mode,
                'max_file_size_mb': imp.max_file_size_mb,
            }
            for tipo, imp in sorted(cls._importers.items())
        ]
    
    @classmethod
    def is_registered(cls, tipo: str) -> bool:
        """
        Verifica se un tipo è registrato.
        
        Args:
            tipo: Tipo da verificare
            
        Returns:
            True se registrato, False altrimenti
        """
        return tipo in cls._importers
