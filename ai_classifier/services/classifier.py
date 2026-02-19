"""
Classificatore Hybrid - Rule-based + LLM fallback
"""
import logging
import re
from typing import Dict, Any, Optional, Tuple

from .extractors.pdf_extractor import PDFExtractor
from .extractors.metadata_extractor import MetadataExtractor
from .llm.openai_client import OpenAIClassifier
from ..utils.validators import ClassificationValidator

logger = logging.getLogger(__name__)


class HybridClassifier:
    """
    Classificatore hybrid che combina:
    1. Rule-based classification (pattern matching veloce)
    2. LLM classification (OpenAI GPT per casi ambigui)
    
    Pipeline:
    - Estrae testo da PDF
    - Applica regole pattern matching su filename e contenuto
    - Se confidenza bassa o nessun match, usa LLM
    """
    
    def __init__(
        self,
        filename_patterns: Dict[str, list],
        content_patterns: Dict[str, list],
        use_llm: bool = True,
        llm_api_key: Optional[str] = None,
        llm_model: str = "gpt-4o-mini",
        confidence_threshold: float = 0.7
    ):
        """
        Inizializza il classificatore.
        
        Args:
            filename_patterns: Dict {tipo: [pattern1, pattern2]} per filename matching
            content_patterns: Dict {tipo: [keyword1, keyword2]} per content matching
            use_llm: Se True, usa LLM per fallback
            llm_api_key: OpenAI API key
            llm_model: Modello OpenAI
            confidence_threshold: Soglia confidenza per rule-based
        """
        self.filename_patterns = filename_patterns
        self.content_patterns = content_patterns
        self.use_llm = use_llm
        self.confidence_threshold = confidence_threshold
        
        # Inizializza extractors
        self.pdf_extractor = PDFExtractor(max_pages=10)
        self.metadata_extractor = MetadataExtractor()
        
        # Inizializza LLM classifier se abilitato
        self.llm_classifier = None
        if self.use_llm:
            try:
                self.llm_classifier = OpenAIClassifier(
                    api_key=llm_api_key,
                    model=llm_model
                )
                logger.info(f"✅ LLM classifier enabled with model {llm_model}")
            except Exception as e:
                logger.warning(f"⚠️ LLM classifier initialization failed: {e}. Falling back to rule-based only.")
                logger.debug(f"LLM init error details:", exc_info=True)
                self.use_llm = False
    
    def classify_file(
        self,
        file_path: str,
        file_name: str,
        mime_type: str
    ) -> Dict[str, Any]:
        """
        Classifica un file.
        
        Args:
            file_path: Path assoluto del file
            file_name: Nome del file
            mime_type: MIME type
            
        Returns:
            Dict con risultato classificazione:
            {
                'predicted_type': str,
                'confidence_score': float,
                'confidence_level': str,
                'classification_method': str ('rule' o 'llm'),
                'extracted_text': str,
                'extracted_metadata': dict,
                'reasoning': str
            }
        """
        logger.info(f"Classificazione file: {file_name}")
        
        # Step 1: Estrazione testo
        extracted_text = ""
        if mime_type == 'application/pdf':
            try:
                extracted_text = self.pdf_extractor.extract_text_sample(file_path, max_chars=3000)
                logger.debug(f"Estratto testo PDF ({len(extracted_text)} chars)")
            except Exception as e:
                logger.warning(f"Errore estrazione testo da {file_name}: {e}")
        elif mime_type == 'text/plain' or file_path.endswith('.txt'):
            # Gestione file TXT
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    extracted_text = f.read(3000)  # Leggi max 3000 caratteri
                logger.debug(f"Estratto testo TXT ({len(extracted_text)} chars)")
            except Exception as e:
                logger.warning(f"Errore lettura file TXT {file_name}: {e}")
        
        # Step 2: Estrazione metadata
        extracted_metadata = {}
        if extracted_text:
            try:
                extracted_metadata = self.metadata_extractor.extract_metadata(extracted_text)
                logger.debug(f"Estratti metadata: {list(extracted_metadata.keys())}")
            except Exception as e:
                logger.warning(f"Errore estrazione metadata: {e}")
        
        # Step 3: Rule-based classification
        rule_result = self._classify_with_rules(file_name, extracted_text)
        
        # Step 4: Se confidenza alta, usa rule-based
        if rule_result['confidence_score'] >= self.confidence_threshold:
            logger.info(
                f"Rule-based classification: {rule_result['predicted_type']} "
                f"(confidence: {rule_result['confidence_score']:.2%})"
            )
            result = rule_result
            result['classification_method'] = 'rule'
        
        # Step 5: Altrimenti, usa LLM fallback
        elif self.use_llm and self.llm_classifier and extracted_text:
            logger.info("Rule-based confidenza bassa, usando LLM fallback...")
            try:
                llm_result = self._classify_with_llm(
                    extracted_text,
                    file_name,
                    extracted_metadata
                )
                result = llm_result
                result['classification_method'] = 'llm'
            except Exception as e:
                logger.error(f"Errore LLM classification: {e}")
                # Fallback a rule-based anche se low confidence
                result = rule_result
                result['classification_method'] = 'rule_fallback'
        
        else:
            # Usa rule-based anche se low confidence (no LLM disponibile)
            if rule_result['confidence_score'] < self.confidence_threshold:
                logger.info(
                    f"📊 Low confidence ({rule_result['confidence_score']:.2f}) but LLM disabled - "
                    f"using rule-based classification: {rule_result['predicted_type']}"
                )
            result = rule_result
            result['classification_method'] = 'rule_only'
        
        # Aggiungi testo e metadata al risultato
        result['extracted_text'] = extracted_text
        result['extracted_metadata'] = extracted_metadata
        
        # Calcola confidence_level
        result['confidence_level'] = ClassificationValidator.calculate_confidence_level(
            result['confidence_score']
        )
        
        return result
    
    def _classify_with_rules(
        self,
        file_name: str,
        text: str
    ) -> Dict[str, Any]:
        """
        Classificazione rule-based usando pattern matching.
        
        Returns:
            Dict con predicted_type, confidence_score, reasoning
        """
        scores = {}  # {tipo: score}
        
        # Matching filename patterns
        for doc_type, patterns in self.filename_patterns.items():
            filename_score = self._match_patterns(file_name.lower(), patterns)
            if filename_score > 0:
                scores[doc_type] = scores.get(doc_type, 0) + filename_score * 0.5  # Peso 50%
        
        # Matching content patterns (se c'è testo)
        if text:
            for doc_type, keywords in self.content_patterns.items():
                content_score = self._match_patterns(text.lower(), keywords)
                if content_score > 0:
                    scores[doc_type] = scores.get(doc_type, 0) + content_score * 0.5  # Peso 50%
        
        # Trova tipo con score massimo
        if scores:
            predicted_type = max(scores, key=scores.get)
            confidence = min(scores[predicted_type], 1.0)  # Cap a 1.0
            
            matched_patterns = []
            if predicted_type in self.filename_patterns:
                matched_patterns.extend(self.filename_patterns[predicted_type])
            
            reasoning = f"Pattern matching: {', '.join(matched_patterns[:3])}"
        else:
            # Nessun match: default a ALT con bassa confidenza
            predicted_type = 'ALT'
            confidence = 0.2
            reasoning = "Nessun pattern matched"
        
        return {
            'predicted_type': predicted_type,
            'confidence_score': confidence,
            'reasoning': reasoning
        }
    
    def _match_patterns(self, text: str, patterns: list) -> float:
        """
        Calcola score di match per una lista di pattern.
        
        Args:
            text: Testo in cui cercare
            patterns: Lista di pattern/keyword da cercare
            
        Returns:
            Score 0.0 - 1.0 (numero di pattern trovati / totale pattern)
        """
        if not patterns:
            return 0.0
        
        matches = 0
        for pattern in patterns:
            # Usa regex case-insensitive
            if re.search(re.escape(pattern), text, re.IGNORECASE):
                matches += 1
        
        return matches / len(patterns)
    
    def _classify_with_llm(
        self,
        text: str,
        filename: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classificazione con LLM (OpenAI GPT).
        
        Returns:
            Dict con predicted_type, confidence_score, reasoning
        """
        llm_result = self.llm_classifier.classify(
            text=text,
            filename=filename,
            metadata=metadata
        )
        
        return {
            'predicted_type': llm_result['type'],
            'confidence_score': llm_result['confidence'],
            'reasoning': llm_result.get('reasoning', 'LLM classification')
        }
    
    def classify_batch(
        self,
        files: list
    ) -> list:
        """
        Classifica batch di file.
        
        Args:
            files: Lista di dict con file info (file_path, file_name, mime_type)
            
        Returns:
            Lista di risultati classificazione
        """
        results = []
        
        for file_info in files:
            try:
                result = self.classify_file(
                    file_path=file_info['file_path'],
                    file_name=file_info['file_name'],
                    mime_type=file_info['mime_type']
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Errore classificazione {file_info['file_name']}: {e}")
                # Aggiungi risultato di errore
                results.append({
                    'predicted_type': 'ALT',
                    'confidence_score': 0.0,
                    'confidence_level': 'low',
                    'classification_method': 'error',
                    'extracted_text': '',
                    'extracted_metadata': {},
                    'reasoning': f'Errore: {str(e)}'
                })
        
        return results
