"""
Feature Extractor - Estrazione features da documenti per ML

Estrae:
1. TF-IDF vectors dal testo
2. Named Entities (CF, P.IVA, date, importi, nomi) con spaCy
3. Pattern matching (regex specifici per documenti italiani)
4. Metadata strutturati (file properties)

Output: feature dictionary standardizzato per training/prediction
"""
import logging
import re
import hashlib
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from collections import Counter

# NLP
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Regex patterns
from .regex_patterns import (
    CODICE_FISCALE_PATTERN,
    PARTITA_IVA_PATTERN,
    DATE_PATTERNS,
    IMPORTO_PATTERNS,
    NUMERO_DOCUMENTO_PATTERNS,
)

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Estrattore di features da documenti per training/prediction ML.
    """
    
    def __init__(
        self,
        spacy_model: str = 'it_core_news_sm',
        tfidf_max_features: int = 500,
        tfidf_ngram_range: Tuple[int, int] = (1, 2),
        tfidf_min_df: int = 2,
        tfidf_max_df: float = 0.8,
    ):
        """
        Inizializza Feature Extractor.
        
        Args:
            spacy_model: Modello spaCy da usare
            tfidf_max_features: Numero massimo features TF-IDF
            tfidf_ngram_range: Range n-gram (1,1)=unigram, (1,2)=uni+bigram
            tfidf_min_df: Minima document frequency
            tfidf_max_df: Massima document frequency (rimuove stop words)
        """
        # Carica spaCy NLP
        try:
            self.nlp = spacy.load(spacy_model)
            logger.info(f"✅ spaCy model loaded: {spacy_model}")
        except Exception as e:
            logger.error(f"❌ Errore caricamento spaCy model: {e}")
            raise
        
        # Inizializza TF-IDF vectorizer (verrà fittato durante training)
        self.vectorizer = TfidfVectorizer(
            max_features=tfidf_max_features,
            ngram_range=tfidf_ngram_range,
            min_df=tfidf_min_df,
            max_df=tfidf_max_df,
            strip_accents='unicode',
            lowercase=True,
            stop_words=self._get_italian_stopwords(),
        )
        
        self.vectorizer_fitted = False
        self.feature_names = []
    
    def extract_features(
        self,
        text: str,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Estrae tutte le features da un documento.
        
        Args:
            text: Testo del documento
            filename: Nome file originale
            metadata: Metadata opzionali (da OCR, PDF properties, etc.)
            
        Returns:
            Dict con features estratte:
            {
                'text_features': dict,      # TF-IDF vector (se fitted)
                'ner_features': dict,       # Named entities
                'pattern_features': dict,   # Pattern matched
                'filename_features': dict,  # Features dal filename
                'metadata_features': dict,  # Metadata strutturati
                'raw_text': str,           # Testo originale (per training)
            }
        """
        if not text or not text.strip():
            logger.warning(f"Testo vuoto per {filename}")
            return self._empty_features()
        
        logger.info(f"🔍 Estrazione features da: {filename} ({len(text)} caratteri)")
        
        features = {
            'filename': filename,
            'text_length': len(text),
            'raw_text': text[:5000],  # Salva primi 5000 char per training
        }
        
        # 1. Text Features (TF-IDF)
        features['text_features'] = self._extract_text_features(text)
        
        # 2. NER Features (Named Entity Recognition)
        features['ner_features'] = self._extract_ner_features(text)
        
        # 3. Pattern Features (Regex matching)
        features['pattern_features'] = self._extract_pattern_features(text)
        
        # 4. Filename Features
        features['filename_features'] = self._extract_filename_features(filename)
        
        # 5. Metadata Features
        features['metadata_features'] = self._extract_metadata_features(metadata or {})
        
        # 6. Statistical Features
        features['statistical_features'] = self._extract_statistical_features(text)
        
        logger.info(f"  ✅ Features estratte: {self._count_total_features(features)} dimensioni")
        
        return features
    
    def fit_vectorizer(self, texts: List[str]):
        """
        Fit TF-IDF vectorizer su corpus di testi (fase training).
        
        Args:
            texts: Lista di testi per training
        """
        logger.info(f"📚 Fitting TF-IDF vectorizer su {len(texts)} documenti...")
        
        # Pulisci testi
        cleaned_texts = [self._clean_text(text) for text in texts if text]
        
        # Fit
        self.vectorizer.fit(cleaned_texts)
        self.vectorizer_fitted = True
        self.feature_names = self.vectorizer.get_feature_names_out().tolist()
        
        logger.info(f"  ✅ TF-IDF fitted: {len(self.feature_names)} features")
    
    def _extract_text_features(self, text: str) -> Dict[str, Any]:
        """
        Estrae features TF-IDF dal testo.
        """
        if not self.vectorizer_fitted:
            # Se vectorizer non è fitted, ritorna features base
            return {
                'vectorizer_fitted': False,
                'text_preview': self._clean_text(text)[:500],
            }
        
        # Transform text con TF-IDF
        cleaned = self._clean_text(text)
        try:
            tfidf_vector = self.vectorizer.transform([cleaned])
            
            # Converti sparse matrix a dict (solo valori non-zero)
            tfidf_dict = {}
            nonzero_indices = tfidf_vector.nonzero()[1]
            for idx in nonzero_indices:
                feature_name = self.feature_names[idx]
                tfidf_dict[feature_name] = float(tfidf_vector[0, idx])
            
            return {
                'vectorizer_fitted': True,
                'tfidf_vector': tfidf_dict,
                'tfidf_dim': len(tfidf_dict),
                'tfidf_sparse_representation': True,
            }
        
        except Exception as e:
            logger.warning(f"Errore TF-IDF transform: {e}")
            return {'vectorizer_fitted': True, 'error': str(e)}
    
    def _extract_ner_features(self, text: str) -> Dict[str, Any]:
        """
        Estrae Named Entities con spaCy.
        """
        # Limita testo per performance (primi 10000 char)
        text_sample = text[:10000]
        
        try:
            doc = self.nlp(text_sample)
            
            entities = {
                'persons': [],       # PER - Persone
                'organizations': [], # ORG - Organizzazioni
                'locations': [],     # LOC - Luoghi
                'dates': [],         # Entità temporali
                'money': [],         # Valori monetari
                'misc': [],          # Altri
            }
            
            for ent in doc.ents:
                entity_text = ent.text.strip()
                
                if ent.label_ == 'PER':
                    entities['persons'].append(entity_text)
                elif ent.label_ == 'ORG':
                    entities['organizations'].append(entity_text)
                elif ent.label_ in ['LOC', 'GPE']:
                    entities['locations'].append(entity_text)
                elif ent.label_ in ['DATE', 'TIME']:
                    entities['dates'].append(entity_text)
                elif ent.label_ == 'MONEY':
                    entities['money'].append(entity_text)
                else:
                    entities['misc'].append(entity_text)
            
            # Conta occorrenze
            return {
                'persons_count': len(entities['persons']),
                'organizations_count': len(entities['organizations']),
                'locations_count': len(entities['locations']),
                'dates_count': len(entities['dates']),
                'money_count': len(entities['money']),
                'persons': list(set(entities['persons']))[:5],  # Top 5 unique
                'organizations': list(set(entities['organizations']))[:5],
            }
        
        except Exception as e:
            logger.warning(f"Errore NER extraction: {e}")
            return {'error': str(e)}
    
    def _extract_pattern_features(self, text: str) -> Dict[str, Any]:
        """
        Estrae pattern specifici con regex (CF, P.IVA, date, importi, etc.).
        """
        features = {}
        
        # Codici Fiscali
        cf_matches = re.findall(CODICE_FISCALE_PATTERN, text, re.IGNORECASE)
        features['codici_fiscali'] = list(set(cf_matches))
        features['codici_fiscali_count'] = len(features['codici_fiscali'])
        
        # Partite IVA
        piva_matches = re.findall(PARTITA_IVA_PATTERN, text)
        features['partite_iva'] = list(set(piva_matches))
        features['partite_iva_count'] = len(features['partite_iva'])
        
        # Date (vari formati italiani)
        date_matches = []
        for pattern in DATE_PATTERNS:
            matches = re.findall(pattern, text)
            date_matches.extend(matches)
        features['date_found'] = list(set(date_matches))[:10]  # Max 10
        features['date_count'] = len(date_matches)
        
        # Importi (€, EUR, numeri con virgola)
        importo_matches = []
        for pattern in IMPORTO_PATTERNS:
            matches = re.findall(pattern, text)
            importo_matches.extend(matches)
        features['importi_found'] = list(set(importo_matches))[:10]
        features['importi_count'] = len(importo_matches)
        
        # Numeri documento (fattura, protocollo, etc.)
        numero_doc_matches = []
        for pattern in NUMERO_DOCUMENTO_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            numero_doc_matches.extend(matches)
        features['numeri_documento'] = list(set(numero_doc_matches))[:5]
        features['numeri_documento_count'] = len(numero_doc_matches)
        
        # Keywords specifiche per tipo documento
        features['keywords_matched'] = self._match_document_keywords(text)
        
        return features
    
    def _extract_filename_features(self, filename: str) -> Dict[str, Any]:
        """
        Estrae features dal nome file.
        """
        filename_lower = filename.lower()
        
        # Parole nel filename
        words = re.findall(r'\w+', filename_lower)
        
        # Keywords nel filename (indicatori tipo documento)
        keyword_matches = []
        document_keywords = {
            'cedolino': ['cedolino', 'payslip', 'busta', 'paga', 'stipendio'],
            'fattura': ['fattura', 'invoice', 'fatt'],
            'f24': ['f24', 'f-24', 'modello f24'],
            'unilav': ['unilav', 'unificata', 'co_'],
            'dichiarazione': ['dichiarazione', '730', 'unico', 'redditi'],
            'contratto': ['contratto', 'contract'],
            'bilancio': ['bilancio', 'stato patrimoniale'],
            'estratto': ['estratto', 'conto'],
        }
        
        for doc_type, keywords in document_keywords.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    keyword_matches.append(doc_type)
        
        # Estrai date dal filename
        date_in_filename = []
        for pattern in DATE_PATTERNS[:3]:  # Solo pattern principali
            matches = re.findall(pattern, filename)
            date_in_filename.extend(matches)
        
        # Estrai anno (2020-2030)
        year_matches = re.findall(r'\b(202[0-9]|203[0-9])\b', filename)
        
        return {
            'filename': filename,
            'filename_length': len(filename),
            'words_in_filename': words[:10],  # Max 10
            'words_count': len(words),
            'keyword_matches': list(set(keyword_matches)),
            'date_in_filename': date_in_filename[:3],
            'year_in_filename': year_matches[:1],
            'extension': filename.split('.')[-1].lower() if '.' in filename else '',
        }
    
    def _extract_metadata_features(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estrae features da metadata (OCR, PDF properties, etc.).
        """
        features = {}
        
        # OCR metadata
        if 'method' in metadata:
            features['extraction_method'] = metadata['method']
        if 'confidence' in metadata:
            features['ocr_confidence'] = metadata.get('confidence', 0.0)
        if 'pages' in metadata:
            features['page_count'] = metadata.get('pages', 1)
        
        # PDF metadata
        if 'author' in metadata:
            features['pdf_author'] = metadata.get('author', '')
        if 'creator' in metadata:
            features['pdf_creator'] = metadata.get('creator', '')
        if 'title' in metadata:
            features['pdf_title'] = metadata.get('title', '')
        
        return features
    
    def _extract_statistical_features(self, text: str) -> Dict[str, Any]:
        """
        Estrae features statistiche dal testo.
        """
        # Conta caratteri, parole, linee
        char_count = len(text)
        words = text.split()
        word_count = len(words)
        line_count = text.count('\n') + 1
        
        # Parole uniche
        unique_words = len(set(w.lower() for w in words if w.isalpha()))
        
        # Densità caratteri speciali
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        
        # Densità numeri
        digit_count = sum(1 for c in text if c.isdigit())
        
        # Densità maiuscole
        upper_count = sum(1 for c in text if c.isupper())
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'line_count': line_count,
            'unique_words': unique_words,
            'avg_word_length': char_count / word_count if word_count > 0 else 0,
            'special_char_density': special_chars / char_count if char_count > 0 else 0,
            'digit_density': digit_count / char_count if char_count > 0 else 0,
            'upper_density': upper_count / char_count if char_count > 0 else 0,
        }
    
    def _match_document_keywords(self, text: str) -> Dict[str, int]:
        """
        Conta keyword specifiche per tipo documento nel testo.
        """
        text_lower = text.lower()
        
        keywords_by_type = {
            'cedolino': ['cedolino', 'busta paga', 'retribuzione', 'stipendio', 'competenze', 'contributi inps'],
            'f24': ['f24', 'codice tributo', 'ravvedimento', 'saldo', 'acconto'],
            'fattura': ['fattura', 'iva', 'imponibile', 'totale fattura', 'scadenza pagamento'],
            'unilav': ['unilav', 'comunicazione obbligatoria', 'rapporto di lavoro', 'assunzione', 'cessazione'],
            'dichiarazione': ['dichiarazione', 'redditi', 'agenzia entrate', '730', 'unico', 'irpef'],
            'contratto': ['contratto', 'parti contraenti', 'clausola', 'oggetto contratto'],
            'bilancio': ['bilancio', 'stato patrimoniale', 'conto economico', 'attivo', 'passivo'],
            'estratto_conto': ['estratto conto', 'saldo iniziale', 'saldo finale', 'movimenti'],
        }
        
        matches = {}
        for doc_type, keywords in keywords_by_type.items():
            count = sum(text_lower.count(keyword) for keyword in keywords)
            if count > 0:
                matches[doc_type] = count
        
        return matches
    
    def _clean_text(self, text: str) -> str:
        """
        Pulisce testo per TF-IDF (rimuove caratteri speciali, normalizza spazi).
        """
        # Rimuovi caratteri non alfanumerici (mantieni spazi)
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizza spazi multipli
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _get_italian_stopwords(self) -> List[str]:
        """
        Ritorna lista stopwords italiane comuni.
        """
        return [
            'di', 'a', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
            'il', 'lo', 'la', 'i', 'gli', 'le', 'un', 'uno', 'una',
            'del', 'dello', 'della', 'dei', 'degli', 'delle',
            'al', 'allo', 'alla', 'ai', 'agli', 'alle',
            'dal', 'dallo', 'dalla', 'dai', 'dagli', 'dalle',
            'nel', 'nello', 'nella', 'nei', 'negli', 'nelle',
            'sul', 'sullo', 'sulla', 'sui', 'sugli', 'sulle',
            'e', 'ed', 'o', 'od', 'ma', 'però', 'anche', 'ancora',
            'che', 'chi', 'cui', 'quale', 'quali',
            'questo', 'questa', 'questi', 'queste',
            'quello', 'quella', 'quelli', 'quelle',
            'essere', 'avere', 'fare', 'stare', 'dare',
            'è', 'sono', 'sei', 'siamo', 'siete',
            'ha', 'hanno', 'hai', 'ho', 'abbiamo', 'avete',
        ]
    
    def _count_total_features(self, features: Dict[str, Any]) -> int:
        """
        Conta totale dimensioni features (approssimativo).
        """
        count = 0
        
        # TF-IDF
        if features.get('text_features', {}).get('tfidf_vector'):
            count += len(features['text_features']['tfidf_vector'])
        
        # NER (counts)
        count += 5  # 5 campi count
        
        # Pattern features (counts)
        count += 6  # 6 campi count
        
        # Filename features
        count += 3  # 3 campi numerici
        
        # Statistical features
        count += 8  # 8 metriche
        
        return count
    
    def _empty_features(self) -> Dict[str, Any]:
        """
        Ritorna features vuote per testo mancante.
        """
        return {
            'text_features': {},
            'ner_features': {},
            'pattern_features': {},
            'filename_features': {},
            'metadata_features': {},
            'statistical_features': {},
            'raw_text': '',
        }
    
    def get_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Converte features dict a numpy array per ML.
        
        Usato durante training/prediction per creare input standardizzato.
        """
        vector = []
        
        # 1. TF-IDF vector (se disponibile)
        if features.get('text_features', {}).get('tfidf_vector'):
            tfidf_dict = features['text_features']['tfidf_vector']
            # Crea vettore ordinato per feature names
            for fname in self.feature_names:
                vector.append(tfidf_dict.get(fname, 0.0))
        else:
            # Se TF-IDF non disponibile, aggiungi zeri
            vector.extend([0.0] * len(self.feature_names))
        
        # 2. NER counts (normalizzati)
        ner = features.get('ner_features', {})
        vector.extend([
            min(ner.get('persons_count', 0) / 10.0, 1.0),  # Max 10, normalizzato
            min(ner.get('organizations_count', 0) / 10.0, 1.0),
            min(ner.get('locations_count', 0) / 5.0, 1.0),
            min(ner.get('dates_count', 0) / 20.0, 1.0),
            min(ner.get('money_count', 0) / 20.0, 1.0),
        ])
        
        # 3. Pattern counts (normalizzati)
        patterns = features.get('pattern_features', {})
        vector.extend([
            min(patterns.get('codici_fiscali_count', 0) / 5.0, 1.0),
            min(patterns.get('partite_iva_count', 0) / 5.0, 1.0),
            min(patterns.get('date_count', 0) / 20.0, 1.0),
            min(patterns.get('importi_count', 0) / 20.0, 1.0),
            min(patterns.get('numeri_documento_count', 0) / 5.0, 1.0),
        ])
        
        # 4. Filename features
        fname_feat = features.get('filename_features', {})
        vector.extend([
            min(fname_feat.get('words_count', 0) / 20.0, 1.0),
            1.0 if fname_feat.get('keyword_matches') else 0.0,
            1.0 if fname_feat.get('date_in_filename') else 0.0,
        ])
        
        # 5. Statistical features (normalizzati)
        stats = features.get('statistical_features', {})
        vector.extend([
            min(stats.get('word_count', 0) / 5000.0, 1.0),
            min(stats.get('unique_words', 0) / 2000.0, 1.0),
            stats.get('avg_word_length', 0) / 20.0,
            stats.get('special_char_density', 0),
            stats.get('digit_density', 0),
            stats.get('upper_density', 0),
        ])
        
        return np.array(vector, dtype=np.float32)
