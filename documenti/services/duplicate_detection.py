"""
Servizio generico per rilevamento duplicati documenti.

Consente di verificare se un documento è duplicato basandosi su criteri
configurati a livello di tipo documento (DocumentiTipo.duplicate_detection_config).
"""
from __future__ import annotations
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from django.db.models import QuerySet
import logging

if TYPE_CHECKING:
    from documenti.models import Documento, DocumentiTipo
    from anagrafiche.models import Cliente
    from fascicoli.models import Fascicolo

logger = logging.getLogger(__name__)


class DuplicateMatchResult:
    """
    Risultato del match di duplicazione.
    
    Attributes:
        is_duplicate: True se è stato trovato un duplicato
        documento: Documento duplicato trovato (se presente)
        confidence: Score di confidenza del match (0.0 - 1.0)
        matched_fields: Lista dei codici campi/attributi che hanno matchato
    """
    
    def __init__(
        self,
        is_duplicate: bool,
        documento: Optional[Documento] = None,
        confidence: float = 0.0,
        matched_fields: List[str] = None
    ):
        self.is_duplicate = is_duplicate
        self.documento = documento
        self.confidence = confidence
        self.matched_fields = matched_fields or []
    
    def __bool__(self) -> bool:
        """Permette uso come booleano: if result: ..."""
        return self.is_duplicate
    
    def __repr__(self) -> str:
        if self.is_duplicate:
            return (
                f"<DuplicateMatch: Doc {self.documento.id}, "
                f"confidence={self.confidence:.2f}, "
                f"fields={', '.join(self.matched_fields)}>"
            )
        return "<NoDuplicate>"


class DuplicateDetectionService:
    """
    Servizio generico per rilevamento duplicati documenti.
    
    Utilizzo:
        from documenti.services.duplicate_detection import DuplicateDetectionService
        
        # Inizializza con tipo documento
        service = DuplicateDetectionService(tipo_documento)
        
        # Verifica se abilitato
        if service.is_enabled():
            # Cerca duplicato
            result = service.find_duplicate(
                cliente=cliente,
                attributi={'numero_cedolino': '00071', 'data_ora_cedolino': '31-12-2025 14:30'},
                documento_fields={'data_documento': date(2025, 12, 31)}
            )
            
            if result.is_duplicate:
                print(f"Duplicato trovato: {result.documento.codice}")
                print(f"Confidenza: {result.confidence:.0%}")
                print(f"Campi matched: {result.matched_fields}")
    
    Configurazione:
        Il tipo documento deve avere duplicate_detection_config configurato:
        
        {
            "enabled": true,
            "strategy": "exact_match",
            "scope": {
                "cliente": true,
                "anno": false,
                "fascicolo": false
            },
            "fields": [
                {
                    "type": "attribute",
                    "code": "numero_cedolino",
                    "required": false,
                    "weight": 1.0,
                    "normalize": true,
                    "case_sensitive": false
                }
            ],
            "match_mode": "all_required_or_any_weighted"
        }
    """
    
    def __init__(self, tipo_documento: DocumentiTipo):
        """
        Inizializza service con tipo documento.
        
        Args:
            tipo_documento: Tipo documento con configurazione duplicati
        """
        self.tipo = tipo_documento
        self.config = tipo_documento.duplicate_detection_config or {}
        self.enabled = self.config.get('enabled', False)
    
    def is_enabled(self) -> bool:
        """
        Verifica se rilevamento duplicati è attivo per questo tipo.
        
        Returns:
            True se abilitato, False altrimenti
        """
        return self.enabled
    
    def find_duplicate(
        self,
        cliente: Optional[Cliente] = None,
        fascicolo: Optional[Fascicolo] = None,
        attributi: Optional[Dict[str, Any]] = None,
        documento_fields: Optional[Dict[str, Any]] = None,
        exclude_documento_id: Optional[int] = None
    ) -> DuplicateMatchResult:
        """
        Cerca documento duplicato basandosi sulla configurazione.
        
        Args:
            cliente: Cliente del documento (richiesto se scope.cliente=true)
            fascicolo: Fascicolo del documento (opzionale)
            attributi: Dizionario attributi dinamici {codice: valore}
            documento_fields: Campi del modello Documento {nome_campo: valore}
            exclude_documento_id: ID documento da escludere dalla ricerca
            
        Returns:
            DuplicateMatchResult con informazioni sul match
            
        Example:
            >>> result = service.find_duplicate(
            ...     cliente=my_cliente,
            ...     attributi={'numero_cedolino': '00071'},
            ...     documento_fields={'data_documento': date(2025, 12, 31)}
            ... )
            >>> if result:
            ...     print(f"Duplicato: {result.documento.codice}")
        """
        if not self.enabled:
            return DuplicateMatchResult(is_duplicate=False)
        
        attributi = attributi or {}
        documento_fields = documento_fields or {}
        
        # 1. Build base query con scope
        query = self._build_scope_query(cliente, fascicolo, documento_fields)
        
        if exclude_documento_id:
            query = query.exclude(id=exclude_documento_id)
        
        # Prefetch attributi per ottimizzare
        documenti = query.prefetch_related('attributi_valori__definizione')
        
        if not documenti.exists():
            return DuplicateMatchResult(is_duplicate=False)
        
        # 2. Strategy-based matching
        strategy = self.config.get('strategy', 'exact_match')
        
        if strategy == 'exact_match':
            return self._exact_match_strategy(documenti, attributi, documento_fields)
        elif strategy == 'weighted':
            return self._weighted_match_strategy(documenti, attributi, documento_fields)
        else:
            logger.warning(f"Unknown strategy '{strategy}' for tipo {self.tipo.codice}, using exact_match")
            return self._exact_match_strategy(documenti, attributi, documento_fields)
    
    def _build_scope_query(
        self,
        cliente: Optional[Cliente],
        fascicolo: Optional[Fascicolo],
        documento_fields: Dict[str, Any]
    ) -> QuerySet:
        """
        Costruisce query base con scope configurato.
        
        Args:
            cliente: Cliente per filtro
            fascicolo: Fascicolo per filtro
            documento_fields: Campi documento per estrazione anno
            
        Returns:
            QuerySet filtrato per scope
        """
        from documenti.models import Documento
        
        scope = self.config.get('scope', {})
        
        # Base: stesso tipo
        query = Documento.objects.filter(tipo=self.tipo)
        
        # Scope: cliente
        if scope.get('cliente', True) and cliente:
            query = query.filter(cliente=cliente)
        
        # Scope: fascicolo
        if scope.get('fascicolo', False) and fascicolo:
            query = query.filter(fascicolo=fascicolo)
        
        # Scope: anno
        if scope.get('anno', False) and 'data_documento' in documento_fields:
            data_doc = documento_fields['data_documento']
            if hasattr(data_doc, 'year'):
                anno = data_doc.year
                query = query.filter(data_documento__year=anno)
        
        return query
    
    def _exact_match_strategy(
        self,
        documenti: QuerySet,
        attributi: Dict[str, Any],
        documento_fields: Dict[str, Any]
    ) -> DuplicateMatchResult:
        """
        Strategia exact match: tutti i campi configurati devono corrispondere.
        
        Logica:
        - Se campo è 'required': DEVE matchare
        - Se campo è opzionale: matcha se presente in entrambi
        - match_mode determina quanti campi devono matchare
        
        Args:
            documenti: QuerySet documenti candidati
            attributi: Attributi del nuovo documento
            documento_fields: Campi del nuovo documento
            
        Returns:
            DuplicateMatchResult con primo duplicato trovato
        """
        fields_config = self.config.get('fields', [])
        match_mode = self.config.get('match_mode', 'all')
        
        for doc in documenti:
            matched_fields = []
            required_matches = 0
            required_count = 0
            optional_matches = 0
            
            # Costruisci dizionario attributi documento
            doc_attributi = {
                attr.definizione.codice: attr.valore
                for attr in doc.attributi_valori.all()
            }
            
            # Verifica ogni campo configurato
            all_required_matched = True
            
            for field_cfg in fields_config:
                field_type = field_cfg.get('type')
                field_code = field_cfg.get('code')
                is_required = field_cfg.get('required', False)
                
                if is_required:
                    required_count += 1
                
                matched = False
                
                # Match attributo
                if field_type == 'attribute':
                    value_new = attributi.get(field_code)
                    value_doc = doc_attributi.get(field_code)
                    
                    # Normalizza valori
                    if field_cfg.get('normalize', True):
                        value_new = self._normalize_value(value_new)
                        value_doc = self._normalize_value(value_doc)
                    
                    # Case sensitivity
                    if not field_cfg.get('case_sensitive', False):
                        if isinstance(value_new, str):
                            value_new = value_new.lower()
                        if isinstance(value_doc, str):
                            value_doc = value_doc.lower()
                    
                    # Confronto
                    if value_new is not None and value_doc is not None and value_new == value_doc:
                        matched = True
                        matched_fields.append(field_code)
                        if is_required:
                            required_matches += 1
                        else:
                            optional_matches += 1
                    elif is_required and (value_new is not None or value_doc is not None):
                        # Required field non matcha
                        all_required_matched = False
                        break
                
                # Match campo documento
                elif field_type == 'field':
                    value_new = documento_fields.get(field_code)
                    value_doc = getattr(doc, field_code, None)
                    
                    if value_new is not None and value_doc is not None and value_new == value_doc:
                        matched = True
                        matched_fields.append(field_code)
                        if is_required:
                            required_matches += 1
                        else:
                            optional_matches += 1
                    elif is_required:
                        all_required_matched = False
                        break
            
            else:  # No break - tutti i controlli passati
                # Valuta match in base a match_mode
                is_match = False
                
                if match_mode == 'all':
                    # Tutti i campi devono matchare
                    is_match = (required_matches == required_count and
                               len(matched_fields) == len(fields_config))
                
                elif match_mode == 'any':
                    # Almeno un campo deve matchare
                    is_match = len(matched_fields) > 0
                
                elif match_mode == 'all_present':
                    # Tutti i campi PRESENTI (non-null) devono matchare
                    # Calcola quanti campi hanno valore non-null
                    present_count = 0
                    for field_cfg in fields_config:
                        field_code = field_cfg.get('code')
                        if field_cfg.get('type') == 'attribute':
                            if attributi.get(field_code) is not None:
                                present_count += 1
                        elif field_cfg.get('type') == 'field':
                            if documento_fields.get(field_code) is not None:
                                present_count += 1
                    
                    # Match se tutti i campi presenti hanno matchato
                    is_match = present_count > 0 and len(matched_fields) == present_count
                
                elif match_mode == 'all_required_or_any_weighted':
                    # Tutti i required + almeno un opzionale (se ci sono opzionali)
                    is_match = all_required_matched and required_matches == required_count
                    if is_match and (len(fields_config) > required_count):
                        # Ci sono campi opzionali, almeno uno deve matchare
                        is_match = optional_matches > 0 or required_count == len(fields_config)
                
                if is_match:
                    confidence = len(matched_fields) / len(fields_config) if fields_config else 0.0
                    logger.info(
                        f"Duplicato trovato per tipo {self.tipo.codice}: "
                        f"Doc {doc.id} ({doc.codice}), "
                        f"confidence={confidence:.0%}, "
                        f"matched_fields={matched_fields}"
                    )
                    return DuplicateMatchResult(
                        is_duplicate=True,
                        documento=doc,
                        confidence=confidence,
                        matched_fields=matched_fields
                    )
        
        return DuplicateMatchResult(is_duplicate=False)
    
    def _weighted_match_strategy(
        self,
        documenti: QuerySet,
        attributi: Dict[str, Any],
        documento_fields: Dict[str, Any]
    ) -> DuplicateMatchResult:
        """
        Strategia weighted: calcola score basato su pesi configurati.
        Match se score >= threshold (default 0.8)
        
        Args:
            documenti: QuerySet documenti candidati
            attributi: Attributi del nuovo documento
            documento_fields: Campi del nuovo documento
            
        Returns:
            DuplicateMatchResult con miglior match (se sopra threshold)
        """
        threshold = self.config.get('threshold', 0.8)
        fields_config = self.config.get('fields', [])
        
        best_match = None
        best_score = 0.0
        
        for doc in documenti:
            doc_attributi = {
                attr.definizione.codice: attr.valore
                for attr in doc.attributi_valori.all()
            }
            
            total_weight = 0.0
            matched_weight = 0.0
            matched_fields = []
            
            for field_cfg in fields_config:
                field_type = field_cfg.get('type')
                field_code = field_cfg.get('code')
                weight = field_cfg.get('weight', 1.0)
                
                total_weight += weight
                
                # Match attributo
                if field_type == 'attribute':
                    value_new = self._normalize_value(attributi.get(field_code))
                    value_doc = self._normalize_value(doc_attributi.get(field_code))
                    
                    if value_new is not None and value_doc is not None and value_new == value_doc:
                        matched_weight += weight
                        matched_fields.append(field_code)
                
                elif field_type == 'field':
                    value_new = documento_fields.get(field_code)
                    value_doc = getattr(doc, field_code, None)
                    
                    if value_new is not None and value_doc is not None and value_new == value_doc:
                        matched_weight += weight
                        matched_fields.append(field_code)
            
            # Calcola score
            score = matched_weight / total_weight if total_weight > 0 else 0.0
            
            if score >= threshold and score > best_score:
                best_score = score
                best_match = DuplicateMatchResult(
                    is_duplicate=True,
                    documento=doc,
                    confidence=score,
                    matched_fields=matched_fields
                )
        
        if best_match:
            logger.info(
                f"Duplicato trovato (weighted) per tipo {self.tipo.codice}: "
                f"Doc {best_match.documento.id} ({best_match.documento.codice}), "
                f"score={best_match.confidence:.0%}"
            )
        
        return best_match or DuplicateMatchResult(is_duplicate=False)
    
    def _normalize_value(self, value: Any) -> Optional[Any]:
        """
        Normalizza valore per confronto.
        
        Args:
            value: Valore da normalizzare
            
        Returns:
            Valore normalizzato o None
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            # Trim whitespace
            value = value.strip()
            # Empty string → None
            if not value:
                return None
        
        return value
