"""
Extractor per metadata da documenti (date, CF, PIVA, importi, etc.)
"""
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Estrattore di metadata da testo di documenti.
    Identifica pattern comuni: codice fiscale, P.IVA, date, importi, etc.
    """
    
    # Regex patterns per metadata comuni
    PATTERNS = {
        # Codice Fiscale italiano (16 caratteri alfanumerici)
        'codice_fiscale': r'\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b',
        
        # Partita IVA italiana (11 cifre)
        'partita_iva': r'\b\d{11}\b',
        
        # Date (vari formati)
        'date': [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD/MM/YYYY, DD-MM-YY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY-MM-DD
        ],
        
        # Importi euro (es: 1.234,56 €, EUR 1234.56)
        'importo': [
            r'€\s*[\d.,]+',
            r'EUR\s*[\d.,]+',
            r'[\d.,]+\s*€',
            r'[\d.,]+\s*EUR',
        ],
        
        # Periodo/Anno (es: 2024, Anno 2023, gennaio 2024)
        'anno': r'\b(19|20)\d{2}\b',
        
        # Mese/Anno (es: 01/2024, Gennaio 2024)
        'periodo': r'\b(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+\d{4}\b',
    }
    
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Estrae metadata da testo.
        
        Args:
            text: Testo da analizzare
            
        Returns:
            Dict con metadata estratti
        """
        metadata = {}
        
        if not text:
            return metadata
        
        # Codice Fiscale
        cf_matches = self._extract_pattern(text, self.PATTERNS['codice_fiscale'])
        if cf_matches:
            metadata['codice_fiscale'] = cf_matches[0]  # Prende il primo match
        
        # Partita IVA
        piva_matches = self._extract_pattern(text, self.PATTERNS['partita_iva'])
        if piva_matches:
            # Filtra possibili false positive (es: date, telefoni)
            valid_piva = [p for p in piva_matches if self._is_valid_piva_format(p)]
            if valid_piva:
                metadata['partita_iva'] = valid_piva[0]
        
        # Date
        date_matches = []
        for pattern in self.PATTERNS['date']:
            date_matches.extend(self._extract_pattern(text, pattern))
        if date_matches:
            # Prova a parsare la prima data valida
            parsed_date = self._parse_date(date_matches[0])
            if parsed_date:
                metadata['data_documento'] = parsed_date.isoformat()
        
        # Importi
        importo_matches = []
        for pattern in self.PATTERNS['importo']:
            importo_matches.extend(self._extract_pattern(text, pattern))
        if importo_matches:
            # Estrai valore numerico dal primo match
            importo = self._parse_amount(importo_matches[0])
            if importo is not None:
                metadata['importo'] = importo
        
        # Anno
        anno_matches = self._extract_pattern(text, self.PATTERNS['anno'])
        if anno_matches:
            # Filtra anni validi (es: 2000-2030)
            valid_anni = [int(a) for a in anno_matches if 2000 <= int(a) <= 2030]
            if valid_anni:
                metadata['anno'] = valid_anni[0]
        
        # Periodo (mese/anno)
        periodo_matches = self._extract_pattern(text, self.PATTERNS['periodo'], re.IGNORECASE)
        if periodo_matches:
            metadata['periodo_riferimento'] = periodo_matches[0]
        
        return metadata
    
    def _extract_pattern(self, text: str, pattern: str, flags: int = 0) -> List[str]:
        """Estrae tutti i match di un pattern regex"""
        try:
            return re.findall(pattern, text, flags)
        except Exception as e:
            logger.warning(f"Regex error: {e}")
            return []
    
    def _is_valid_piva_format(self, piva: str) -> bool:
        """Verifica se una stringa ha formato P.IVA valido"""
        # Semplice check: 11 cifre, non tutte uguali
        if len(piva) != 11 or not piva.isdigit():
            return False
        if len(set(piva)) == 1:  # Tutte cifre uguali
            return False
        return True
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Prova a parsare una data da string"""
        date_formats = [
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d/%m/%y',
            '%d-%m-%y',
            '%Y-%m-%d',
            '%Y/%m/%d',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Estrae valore numerico da stringa importo"""
        try:
            # Rimuovi simboli valuta
            cleaned = amount_str.replace('€', '').replace('EUR', '').strip()
            
            # Gestisci formato italiano (1.234,56) vs internazionale (1,234.56)
            if ',' in cleaned and '.' in cleaned:
                # Determina quale è il separatore decimale
                if cleaned.rfind(',') > cleaned.rfind('.'):
                    # Formato italiano
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    # Formato internazionale
                    cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                # Solo virgola: assume formato italiano
                cleaned = cleaned.replace(',', '.')
            
            return float(cleaned)
        except Exception as e:
            logger.debug(f"Cannot parse amount '{amount_str}': {e}")
            return None
    
    def extract_specific_patterns(self, text: str, doc_type: str) -> Dict[str, Any]:
        """
        Estrae pattern specifici per tipo di documento.
        
        Args:
            text: Testo da analizzare
            doc_type: Tipo documento (CED, UNI, F24, etc.)
            
        Returns:
            Dict con metadata specifici del tipo
        """
        specific_metadata = {}
        
        if doc_type == 'CED':  # Cedolino
            # Cerca "Periodo di paga", "Retribuzione lorda", etc.
            periodo_match = re.search(r'Periodo\s+(?:di\s+)?paga:?\s*([^\n]+)', text, re.IGNORECASE)
            if periodo_match:
                specific_metadata['periodo_paga'] = periodo_match.group(1).strip()
            
            retribuzione_match = re.search(r'Retribuzione\s+lorda:?\s*€?\s*([\d.,]+)', text, re.IGNORECASE)
            if retribuzione_match:
                specific_metadata['retribuzione_lorda'] = self._parse_amount(retribuzione_match.group(1))
        
        elif doc_type == 'F24':  # F24
            # Cerca "Codice tributo"
            tributo_matches = re.findall(r'Codice\s+tributo:?\s*(\d{4})', text, re.IGNORECASE)
            if tributo_matches:
                specific_metadata['codici_tributo'] = tributo_matches
        
        elif doc_type == 'UNI':  # Unilav
            # Cerca "Tipo comunicazione"
            tipo_com_match = re.search(r'Tipo\s+comunicazione:?\s*([^\n]+)', text, re.IGNORECASE)
            if tipo_com_match:
                specific_metadata['tipo_comunicazione'] = tipo_com_match.group(1).strip()
        
        return specific_metadata
