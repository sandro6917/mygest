"""
Predictor Service - Inference con modelli ML addestrati

Carica il modello attivo e fa predizioni su nuovi documenti.
"""
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import joblib
import numpy as np

from django.conf import settings

from ai_classifier.models import MLModel, DocumentPrediction
from ai_classifier.services.ml.ocr_service import OCRService
from ai_classifier.services.ml.feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


def _parse_document_specific_fields(file_path: str, predicted_tipo: str) -> Optional[Dict[str, Any]]:
    """
    Estrae campi specifici per tipi di documento che hanno parser dedicati.
    
    Args:
        file_path: Path al file
        predicted_tipo: Tipo documento predetto dal ML
        
    Returns:
        Dict con campi estratti o None se non c'è parser specifico
    """
    try:
        # UNILAV: usa parser esistente
        if predicted_tipo == 'UNILAV':
            from documenti.parsers.unilav_parser import parse_unilav_pdf
            
            logger.info(f"  🔍 Parsing campi specifici UNILAV...")
            parsed = parse_unilav_pdf(file_path)
            
            # Estrai dati strutturati
            datore = parsed['datore']
            lavoratore = parsed['lavoratore']
            unilav = parsed['unilav']
            
            # Determina tipo comunicazione mappato
            tipo_com = unilav.get('tipo_comunicazione', '')
            modello = unilav.get('modello', '')
            tipologia = unilav.get('tipologia_contrattuale', '')
            
            tipo_mappato = 'Assunzione'  # Default
            if 'PROROGA' in tipo_com.upper() or 'PROROGA' in modello.upper():
                tipo_mappato = 'Proroga'
            elif 'TRASFORMAZIONE' in tipo_com.upper() or 'TRASFORMAZIONE' in modello.upper():
                tipo_mappato = 'Trasformazione'
            elif 'CESSAZIONE' in tipo_com.upper() or 'CESSAZIONE' in modello.upper():
                tipo_mappato = 'Cessazione'
            elif 'DETERMINATO' in tipologia.upper():
                tipo_mappato = 'Assunzione a termine'
            elif 'INDETERMINATO' in tipologia.upper():
                tipo_mappato = 'Assunzione a tempo indeterminato'
            
            # Costruisci response strutturata
            fields = {
                'parser_type': 'unilav',
                'parsed_successfully': True,
                
                # Attributi per il form
                'attributi': {
                    'codice_comunicazione': unilav['codice_comunicazione'],
                    'tipo': tipo_mappato,
                    'modello': unilav.get('modello'),
                    'data_comunicazione': unilav['data_comunicazione'],
                    
                    # Datore
                    'datore_cf': datore['codice_fiscale'],
                    'datore_denominazione': datore['denominazione'],
                    'datore_email': datore.get('email'),
                    'datore_telefono': datore.get('telefono'),
                    'datore_comune': datore.get('comune_sede_legale'),
                    'datore_cap': datore.get('cap_sede_legale'),
                    'datore_indirizzo': datore.get('indirizzo_sede_legale'),
                    
                    # Lavoratore
                    'lavoratore_cf': lavoratore['codice_fiscale'],
                    'lavoratore_cognome': lavoratore['cognome'],
                    'lavoratore_nome': lavoratore['nome'],
                    'lavoratore_sesso': lavoratore.get('sesso'),
                    'lavoratore_data_nascita': lavoratore.get('data_nascita'),
                    'lavoratore_comune_nascita': lavoratore.get('comune_nascita'),
                    'lavoratore_comune': lavoratore.get('comune_domicilio'),
                    'lavoratore_cap': lavoratore.get('cap_domicilio'),
                    'lavoratore_indirizzo': lavoratore.get('indirizzo_domicilio'),
                    
                    # Rapporto
                    'data_inizio_rapporto': unilav.get('data_inizio_rapporto'),
                    'data_fine_rapporto': unilav.get('data_fine_rapporto'),
                    'data_proroga': unilav.get('data_proroga'),
                    'data_trasformazione': unilav.get('data_trasformazione'),
                    'causa_trasformazione': unilav.get('causa_trasformazione'),
                    'centro_impiego': unilav.get('centro_impiego'),
                    'provincia_impiego': unilav.get('provincia_impiego'),
                    'ente_previdenziale': unilav.get('ente_previdenziale'),
                    'codice_ente_previdenziale': unilav.get('codice_ente_previdenziale'),
                    'pat_inail': unilav.get('pat_inail'),
                    'tipologia_contrattuale': unilav.get('tipologia_contrattuale'),
                    'tipo_orario': unilav.get('tipo_orario'),
                    'ore_settimanali': unilav.get('ore_settimanali'),
                    'qualifica': unilav.get('qualifica_professionale'),
                    'contratto_collettivo': unilav.get('contratto_collettivo'),
                    'livello': unilav.get('livello_inquadramento'),
                    'retribuzione': unilav.get('retribuzione'),
                },
                
                # Anagrafiche reperite (per match automatico)
                'anagrafiche': {
                    'datore': {
                        'codice_fiscale': datore['codice_fiscale'],
                        'tipo': 'PF' if len(datore['codice_fiscale']) == 16 else 'PG',
                        'denominazione': datore['denominazione'],
                    },
                    'lavoratore': {
                        'codice_fiscale': lavoratore['codice_fiscale'],
                        'tipo': 'PF',
                        'denominazione': f"{lavoratore['cognome']} {lavoratore['nome']}",
                    },
                },
                
                # Descrizione suggerita
                'descrizione_suggerita': f"UNILAV {tipo_mappato} {unilav['codice_comunicazione']} - {lavoratore['cognome']} {lavoratore['nome']}",
            }
            
            logger.info(f"  ✅ Campi UNILAV estratti: {len(fields['attributi'])} attributi")
            return fields
        
        # Altri parser specifici possono essere aggiunti qui
        # elif predicted_tipo == 'CEDOL':
        #     from documenti.parsers.cedolino_parser import parse_cedolino_pdf
        #     ...
        
        return None
        
    except Exception as e:
        logger.warning(f"  ⚠️ Errore parsing campi specifici {predicted_tipo}: {e}")
        import traceback
        traceback.print_exc()
        return None


class Predictor:
    """
    Servizio per predizioni ML su nuovi documenti.
    
    Carica modello attivo, vectorizer e encoders dal database,
    estrae features da file e ritorna predizioni con confidence.
    """
    
    def __init__(self):
        """
        Inizializza Predictor caricando modello attivo.
        """
        self.ml_model = None
        self.sklearn_model = None
        self.vectorizer = None
        self.label_encoder_tipo = None
        self.label_encoder_cliente = None
        self.label_encoder_titolario = None
        
        self.ocr_service = OCRService()
        self.feature_extractor = FeatureExtractor()
        
        # Carica modello attivo
        self._load_active_model()
    
    def _load_active_model(self):
        """
        Carica il modello ML attivo dal database.
        """
        try:
            # Trova modello attivo
            self.ml_model = MLModel.objects.filter(is_active=True).first()
            
            if not self.ml_model:
                logger.warning("⚠️ Nessun modello ML attivo trovato")
                return
            
            logger.info(f"📦 Caricamento modello: {self.ml_model.version}")
            
            # Carica file modello
            if not os.path.exists(self.ml_model.model_file_path):
                raise FileNotFoundError(f"File modello non trovato: {self.ml_model.model_file_path}")
            
            self.sklearn_model = joblib.load(self.ml_model.model_file_path)
            logger.info(f"  ✅ Modello caricato")
            
            # Carica vectorizer
            if not os.path.exists(self.ml_model.vectorizer_file_path):
                raise FileNotFoundError(f"File vectorizer non trovato: {self.ml_model.vectorizer_file_path}")
            
            self.vectorizer = joblib.load(self.ml_model.vectorizer_file_path)
            logger.info(f"  ✅ Vectorizer caricato")
            
            # Carica label encoders
            if not os.path.exists(self.ml_model.label_encoder_file_path):
                raise FileNotFoundError(f"File encoders non trovato: {self.ml_model.label_encoder_file_path}")
            
            encoders = joblib.load(self.ml_model.label_encoder_file_path)
            self.label_encoder_tipo = encoders.get('tipo')
            self.label_encoder_cliente = encoders.get('cliente')
            self.label_encoder_titolario = encoders.get('titolario')
            logger.info(f"  ✅ Label encoders caricati")
            
            logger.info(f"✅ Modello {self.ml_model.version} pronto per inference")
            logger.info(f"   Accuracy: {self.ml_model.accuracy:.2%}")
        
        except Exception as e:
            logger.error(f"❌ Errore caricamento modello: {e}")
            self.ml_model = None
            raise
    
    def predict(
        self,
        file_path: str,
        filename: Optional[str] = None,
        return_top_n: int = 3,
        min_confidence: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Predice tipo documento e metadata da file.
        
        Args:
            file_path: Path al file da classificare
            filename: Nome file originale (opzionale)
            return_top_n: Numero top predizioni da ritornare
            min_confidence: Confidence minima per considerare predizione valida
            
        Returns:
            Dict con:
            {
                'success': bool,
                'predictions': {
                    'tipo': {
                        'top_prediction': str,
                        'confidence': float,
                        'all_predictions': List[Tuple[str, float]],
                    },
                    'cliente': {...},  # Se disponibile
                    'titolario': {...},  # Se disponibile
                },
                'metadata': {
                    'extracted_features': dict,
                    'ocr_method': str,
                    'text_length': int,
                },
                'model_info': {
                    'version': str,
                    'accuracy': float,
                },
                'error': Optional[str],
            }
        """
        if not self.ml_model or not self.sklearn_model:
            return {
                'success': False,
                'error': 'Nessun modello ML attivo disponibile',
                'predictions': None,
                'metadata': None,
                'model_info': None,
            }
        
        try:
            logger.info(f"🔍 Predizione per file: {file_path}")
            
            # 1. Estrai testo con OCR
            ocr_result = self.ocr_service.extract_text_from_file(file_path)
            text = ocr_result.get('text', '')
            
            if not text or len(text) < 50:
                return {
                    'success': False,
                    'error': f'Testo insufficiente estratto ({len(text)} caratteri)',
                    'predictions': None,
                    'metadata': {
                        'ocr_method': ocr_result.get('method'),
                        'text_length': len(text),
                    },
                    'model_info': None,
                }
            
            logger.info(f"  ✅ Testo estratto: {len(text)} caratteri (metodo: {ocr_result.get('method')})")
            
            # 2. Estrai features
            if not filename:
                filename = os.path.basename(file_path)
            
            features = self.feature_extractor.extract_features(text, filename)
            logger.info(f"  ✅ Features estratte: {len(features)} dimensioni")
            
            # 3. Trasforma testo con vectorizer TF-IDF caricato
            # Il vectorizer è già fitted durante il training
            tfidf_vector = self.vectorizer.transform([text])
            
            # Ottieni feature names dal vectorizer
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Crea dict TF-IDF
            tfidf_array = tfidf_vector.toarray()[0]
            tfidf_dict = {fname: float(val) for fname, val in zip(feature_names, tfidf_array) if val > 0}
            
            # Aggiungi TF-IDF features al dict features
            if 'text_features' not in features:
                features['text_features'] = {}
            features['text_features']['tfidf_vector'] = tfidf_dict
            
            # Imposta feature_names nel feature_extractor
            self.feature_extractor.feature_names = list(feature_names)
            
            # 4. Vectorizza features per predizione
            feature_vector = self.feature_extractor.get_feature_vector(features)
            
            # 5. Predici con modello
            # Predici probabilità per tutte le classi
            proba = self.sklearn_model.predict_proba(feature_vector.reshape(1, -1))[0]
            
            # 6. Decodifica predizioni tipo documento
            tipo_predictions = self._get_top_predictions(
                proba,
                self.label_encoder_tipo,
                top_n=return_top_n
            )
            
            top_tipo, top_confidence = tipo_predictions[0]
            
            logger.info(f"  ✅ Predizione: {top_tipo} (confidence: {top_confidence:.1%})")
            
            # 7. Estrai campi specifici se disponibile parser dedicato
            parsed_fields = None
            if top_confidence >= 0.5:  # Solo se confidence ragionevole
                parsed_fields = _parse_document_specific_fields(file_path, top_tipo)
            
            # 8. Prepara risultato
            result = {
                'success': True,
                'predictions': {
                    'tipo': {
                        'top_prediction': top_tipo,
                        'confidence': top_confidence,
                        'all_predictions': tipo_predictions,
                        'meets_threshold': top_confidence >= min_confidence,
                    },
                },
                'metadata': {
                    'extracted_features': {
                        'codici_fiscali': features.get('codici_fiscali', []),
                        'partite_iva': features.get('partite_iva', []),
                        'importi': features.get('importi', []),
                        'date': features.get('date', []),
                        'entities_persone': features.get('entities_persone', 0),
                        'entities_org': features.get('entities_org', 0),
                        'word_count': features.get('word_count', 0),
                    },
                    'ocr_method': ocr_result.get('method'),
                    'ocr_pages': ocr_result.get('pages', 1),
                    'text_length': len(text),
                    'filename': filename,
                    'parsed_fields': parsed_fields,  # Campi specifici estratti
                },
                'model_info': {
                    'version': self.ml_model.version,
                    'accuracy': self.ml_model.accuracy,
                    'trained_at': self.ml_model.trained_at.isoformat(),
                },
                'error': None,
            }
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Errore durante predizione: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e),
                'predictions': None,
                'metadata': None,
                'model_info': None,
            }
    
    def _get_top_predictions(
        self,
        probabilities: np.ndarray,
        label_encoder,
        top_n: int = 3,
        exclude_types: List[str] = None,
    ) -> List[Tuple[str, float]]:
        """
        Ottiene le top N predizioni con confidence.
        
        Esclude automaticamente CLAV (Carte di lavoro) che è un tipo
        documento residuale/generico da inserire manualmente.
        
        Args:
            probabilities: Array di probabilità dal modello
            label_encoder: Label encoder per decodificare classi
            top_n: Numero predizioni da ritornare
            exclude_types: Lista tipi da escludere (default: ['CLAV'])
            
        Returns:
            Lista di tuple (label, confidence) ordinate per confidence
        """
        if exclude_types is None:
            exclude_types = ['CLAV']  # Default: escludi Carte di lavoro
        
        # Ottieni indici ordinati per probabilità decrescente
        sorted_indices = np.argsort(probabilities)[::-1]
        
        # Decodifica labels e filtra tipi esclusi
        predictions = []
        for idx in sorted_indices:
            label = label_encoder.inverse_transform([idx])[0]
            
            # Salta tipi esclusi (CLAV)
            if label in exclude_types:
                continue
            
            confidence = probabilities[idx]
            predictions.append((label, float(confidence)))
            
            # Stop quando abbiamo top_n predizioni
            if len(predictions) >= top_n:
                break
        
        return predictions
    
    def predict_and_save(
        self,
        file_path: str,
        documento_id: Optional[int] = None,
        filename: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Optional[DocumentPrediction]]:
        """
        Fa predizione e salva risultato nel database.
        
        Args:
            file_path: Path al file
            documento_id: ID documento associato (opzionale)
            filename: Nome file (opzionale)
            
        Returns:
            Tuple (prediction_result, document_prediction_object)
        """
        # Fa predizione
        result = self.predict(file_path, filename)
        
        if not result['success']:
            return result, None
        
        # Salva in database
        try:
            tipo_pred = result['predictions']['tipo']
            
            prediction = DocumentPrediction.objects.create(
                documento_id=documento_id,
                ml_model=self.ml_model,
                predicted_type=tipo_pred['top_prediction'],
                confidence_tipo=tipo_pred['confidence'],
                confidence_scores={
                    'all_predictions': tipo_pred['all_predictions'],
                },
                extracted_features=result['metadata']['extracted_features'],
            )
            
            logger.info(f"  💾 Predizione salvata: DocumentPrediction #{prediction.id}")
            
            return result, prediction
        
        except Exception as e:
            logger.error(f"❌ Errore salvataggio predizione: {e}")
            return result, None
    
    def batch_predict(
        self,
        file_paths: List[str],
        filenames: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Predizioni batch su lista di file.
        
        Args:
            file_paths: Lista path ai file
            filenames: Lista nomi file (opzionale)
            
        Returns:
            Lista di risultati predizioni
        """
        results = []
        
        if filenames is None:
            filenames = [None] * len(file_paths)
        
        for file_path, filename in zip(file_paths, filenames):
            result = self.predict(file_path, filename)
            results.append(result)
        
        return results
    
    def reload_model(self):
        """
        Ricarica il modello attivo (utile dopo re-training).
        """
        logger.info("🔄 Ricaricamento modello...")
        self._load_active_model()
