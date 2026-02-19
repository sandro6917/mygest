"""
Validatori per risultati classificazione e configurazione
"""
from typing import Dict, Any, Optional


class ClassificationValidator:
    """Validatore per risultati di classificazione"""
    
    # Tipologie documenti valide
    VALID_TYPES = ['CED', 'UNI', 'DIC', 'BIL', 'F24', 'EST', 'FAT', 'CON', 'COR', 'PRO', 'ALT']
    
    # Livelli confidenza validi
    VALID_CONFIDENCE_LEVELS = ['high', 'medium', 'low']
    
    @staticmethod
    def validate_classification_result(
        predicted_type: str,
        confidence_score: float,
        confidence_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Valida un risultato di classificazione.
        
        Args:
            predicted_type: Tipo documento predetto
            confidence_score: Score di confidenza (0.0 - 1.0)
            confidence_level: Livello confidenza (opzionale, calcolato se assente)
            
        Returns:
            Dict con risultato validato e eventuali errori
            
        Raises:
            ValueError se validazione fallisce
        """
        errors = []
        
        # Valida tipo
        if predicted_type not in ClassificationValidator.VALID_TYPES:
            errors.append(f"Tipo '{predicted_type}' non valido. Validi: {ClassificationValidator.VALID_TYPES}")
        
        # Valida score
        if not (0.0 <= confidence_score <= 1.0):
            errors.append(f"Confidence score {confidence_score} fuori range [0.0, 1.0]")
        
        # Calcola livello se non fornito
        if confidence_level is None:
            confidence_level = ClassificationValidator.calculate_confidence_level(confidence_score)
        elif confidence_level not in ClassificationValidator.VALID_CONFIDENCE_LEVELS:
            errors.append(
                f"Confidence level '{confidence_level}' non valido. "
                f"Validi: {ClassificationValidator.VALID_CONFIDENCE_LEVELS}"
            )
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return {
            'predicted_type': predicted_type,
            'confidence_score': confidence_score,
            'confidence_level': confidence_level,
            'valid': True
        }
    
    @staticmethod
    def calculate_confidence_level(score: float) -> str:
        """
        Calcola il livello di confidenza da uno score numerico.
        
        Args:
            score: Score 0.0 - 1.0
            
        Returns:
            'high', 'medium', o 'low'
        """
        if score >= 0.8:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> bool:
        """
        Valida metadata estratti da un documento.
        
        Args:
            metadata: Dizionario metadata
            
        Returns:
            True se metadata validi
        """
        # Validazione base: deve essere un dizionario
        if not isinstance(metadata, dict):
            return False
        
        # Campi opzionali supportati
        optional_fields = [
            'data_documento',
            'importo',
            'codice_fiscale',
            'partita_iva',
            'nominativo',
            'periodo_riferimento',
            'anno',
            'numero_documento',
        ]
        
        # Verifica che non ci siano chiavi inattese (warning, non errore)
        # Per ora accetta qualsiasi chiave
        return True


class ConfigValidator:
    """Validatore per configurazione classificatore"""
    
    @staticmethod
    def validate_llm_config(
        provider: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """
        Valida configurazione LLM.
        
        Args:
            provider: Provider LLM (openai, anthropic, local)
            model: Nome modello
            temperature: Temperatura (0.0 - 2.0)
            max_tokens: Massimo numero di token
            
        Returns:
            Dict con configurazione validata
            
        Raises:
            ValueError se validazione fallisce
        """
        errors = []
        
        # Valida provider
        valid_providers = ['openai', 'anthropic', 'local']
        if provider not in valid_providers:
            errors.append(f"Provider '{provider}' non valido. Validi: {valid_providers}")
        
        # Valida temperature
        if not (0.0 <= temperature <= 2.0):
            errors.append(f"Temperature {temperature} fuori range [0.0, 2.0]")
        
        # Valida max_tokens
        if max_tokens < 1 or max_tokens > 4000:
            errors.append(f"Max tokens {max_tokens} fuori range [1, 4000]")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return {
            'provider': provider,
            'model': model,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'valid': True
        }
    
    @staticmethod
    def validate_patterns(patterns: Dict[str, list]) -> bool:
        """
        Valida pattern per rule-based classification.
        
        Args:
            patterns: Dict {tipo: [pattern1, pattern2, ...]}
            
        Returns:
            True se patterns validi
        """
        if not isinstance(patterns, dict):
            return False
        
        # Ogni chiave deve essere un tipo valido
        # Ogni valore deve essere una lista di stringhe
        for doc_type, pattern_list in patterns.items():
            if doc_type not in ClassificationValidator.VALID_TYPES:
                return False
            if not isinstance(pattern_list, list):
                return False
            if not all(isinstance(p, str) for p in pattern_list):
                return False
        
        return True
