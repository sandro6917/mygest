"""
OpenAI Client per classificazione documenti con GPT-4o-mini
"""
import os
import logging
import json
from typing import Dict, Any, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


class OpenAIClassifier:
    """
    Classificatore di documenti basato su OpenAI GPT.
    Usa GPT-4o-mini per classificazione efficiente e low-cost.
    Supporta Few-Shot Learning con esempi di training.
    """
    
    # System prompt BASE per classificazione
    BASE_SYSTEM_PROMPT = """Sei un esperto classificatore di documenti italiani.
Dato il testo estratto da un documento, devi classificarlo in una delle seguenti categorie:

{categories}

Rispondi SOLO con un oggetto JSON nel seguente formato:
{{
    "type": "CODICE_CATEGORIA",
    "confidence": NUMERO_DA_0_A_1,
    "reasoning": "Breve spiegazione della classificazione"
}}

{examples_section}
"""

    # Categorie di default
    DEFAULT_CATEGORIES = """- CED (Cedolino): Busta paga, prospetto retribuzione
- UNI (Unilav): Comunicazione obbligatoria lavoro, CO
- DIC (Dichiarazione Fiscale): Modello 730, Modello Redditi, Unico
- BIL (Bilancio): Bilancio di esercizio, stato patrimoniale, conto economico
- F24 (F24): Modello F24, delega di pagamento tributi
- EST (Estratto Conto): Estratto conto bancario, movimenti
- FAT (Fattura): Fattura attiva/passiva
- CON (Contratto): Contratto di lavoro, affitto, etc.
- COR (Corrispondenza): Lettere, comunicazioni generiche
- PRO (Protocollo): Documenti protocollati
- ALT (Altro): Documenti non classificabili nelle categorie precedenti"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_tokens: int = 500,
        use_examples: bool = True
    ):
        """
        Inizializza il client OpenAI.
        
        Args:
            api_key: OpenAI API key (se None, usa variabile ambiente OPENAI_API_KEY)
            model: Modello OpenAI da usare
            temperature: Temperature per sampling (0.0 = deterministico)
            max_tokens: Massimo numero di token per risposta
        """
        if OpenAI is None:
            raise ImportError("OpenAI library non installata. Installa con: pip install openai")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key non fornita. "
                "Passa api_key al costruttore o imposta variabile ambiente OPENAI_API_KEY"
            )
        
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_tokens: int = 500,
        use_examples: bool = True
    ):
        """
        Inizializza il client OpenAI.
        
        Args:
            api_key: OpenAI API key (se None, usa variabile ambiente OPENAI_API_KEY)
            model: Modello OpenAI da usare
            temperature: Temperature per sampling (0.0 = deterministico)
            max_tokens: Massimo numero di token per risposta
            use_examples: Se True, carica esempi di training per Few-Shot Learning
        """
        if OpenAI is None:
            raise ImportError("OpenAI library non installata. Installa con: pip install openai")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key non fornita. "
                "Passa api_key al costruttore o imposta variabile ambiente OPENAI_API_KEY"
            )
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_examples = use_examples
        
        # Inizializza client
        self.client = OpenAI(api_key=self.api_key)
        
        # Carica esempi di training se richiesto
        self.training_examples = {}
        if self.use_examples:
            self._load_training_examples()
        
        # Genera system prompt (con o senza esempi)
        self.system_prompt = self._build_system_prompt()
        
        logger.info(f"✅ LLM classifier enabled with model {self.model}")
        if self.training_examples:
            total_examples = sum(len(examples) for examples in self.training_examples.values())
            logger.info(f"📚 Loaded {total_examples} training examples for {len(self.training_examples)} types")
    
    def _load_training_examples(self):
        """Carica esempi di training dal database"""
        try:
            # Import qui per evitare circular dependency
            from ai_classifier.models import TrainingExample
            
            self.training_examples = TrainingExample.get_all_active_examples(max_per_type=2)
        except Exception as e:
            logger.warning(f"Could not load training examples: {e}")
            self.training_examples = {}
    
    def _build_system_prompt(self) -> str:
        """
        Costruisce il system prompt con eventuali esempi di training.
        
        Returns:
            System prompt completo
        """
        categories = self.DEFAULT_CATEGORIES
        
        # Aggiungi sezione esempi se disponibili
        if self.training_examples:
            examples_text = "\n\n**ESEMPI DI RIFERIMENTO:**\n"
            for doc_type, examples in self.training_examples.items():
                examples_text += f"\n**Tipo {doc_type}:**\n"
                for i, ex in enumerate(examples, 1):
                    examples_text += f"{i}. File: {ex['file_name']}\n"
                    if ex.get('description'):
                        examples_text += f"   Caratteristiche: {ex['description']}\n"
                    if ex.get('text'):
                        examples_text += f"   Estratto: {ex['text'][:200]}...\n"
            
            examples_section = examples_text
        else:
            examples_section = ""
        
        return self.BASE_SYSTEM_PROMPT.format(
            categories=categories,
            examples_section=examples_section
        )
    
    def reload_examples(self):
        """Ricarica gli esempi di training dal database"""
        self._load_training_examples()
        self.system_prompt = self._build_system_prompt()
        logger.info("Training examples reloaded")
    
    def classify(
        self,
        text: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Classifica un documento usando OpenAI GPT.
        
        Args:
            text: Testo estratto dal documento
            filename: Nome file (opzionale, usato come context addizionale)
            metadata: Metadata estratti (opzionale)
            
        Returns:
            Dict con risultato classificazione:
            {
                'type': str,
                'confidence': float,
                'reasoning': str,
                'raw_response': str
            }
        """
        # Prepara il prompt user
        user_prompt = self._build_user_prompt(text, filename, metadata)
        
        try:
            # Chiamata API OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}  # Forza risposta JSON
            )
            
            # Estrai risposta
            raw_response = response.choices[0].message.content
            logger.debug(f"OpenAI response: {raw_response}")
            
            # Parsa JSON
            result = json.loads(raw_response)
            
            # Valida risposta
            if 'type' not in result or 'confidence' not in result:
                raise ValueError(f"Risposta OpenAI incompleta: {raw_response}")
            
            # Normalizza confidence (assicura range 0-1)
            confidence = float(result['confidence'])
            if confidence > 1.0:
                confidence = confidence / 100.0  # Converti da percentuale
            
            return {
                'type': result['type'],
                'confidence': confidence,
                'reasoning': result.get('reasoning', ''),
                'raw_response': raw_response
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"Errore parsing risposta OpenAI: {e}")
            raise ValueError(f"OpenAI non ha ritornato JSON valido: {e}")
        
        except Exception as e:
            logger.error(f"Errore chiamata OpenAI: {e}")
            raise
    
    def _build_user_prompt(
        self,
        text: str,
        filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Costruisce il prompt user con context aggiuntivo"""
        prompt_parts = []
        
        # Filename come hint
        if filename:
            prompt_parts.append(f"Nome file: {filename}")
        
        # Metadata estratti
        if metadata:
            metadata_str = json.dumps(metadata, ensure_ascii=False, indent=2)
            prompt_parts.append(f"Metadata estratti:\n{metadata_str}")
        
        # Testo documento (limita lunghezza per non eccedere token limit)
        max_text_length = 3000  # ~750 token
        truncated_text = text[:max_text_length]
        if len(text) > max_text_length:
            truncated_text += "\n\n[... testo troncato ...]"
        
        prompt_parts.append(f"Testo documento:\n{truncated_text}")
        
        return "\n\n".join(prompt_parts)
    
    def batch_classify(self, documents: list) -> list:
        """
        Classifica multipli documenti in batch.
        
        Args:
            documents: Lista di dict {'text': str, 'filename': str, 'metadata': dict}
            
        Returns:
            Lista di risultati classificazione
        """
        results = []
        
        for doc in documents:
            try:
                result = self.classify(
                    text=doc.get('text', ''),
                    filename=doc.get('filename'),
                    metadata=doc.get('metadata')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Errore classificazione {doc.get('filename', 'unknown')}: {e}")
                results.append({
                    'type': 'ALT',
                    'confidence': 0.0,
                    'reasoning': f'Errore: {str(e)}',
                    'error': str(e)
                })
        
        return results
