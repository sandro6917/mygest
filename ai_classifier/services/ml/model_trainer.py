"""
Model Trainer - Training e re-training modelli ML

Gestisce:
- Initial training su documenti esistenti
- Re-training periodico con nuovi esempi
- Versionamento modelli
- Salvataggio su NAS
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE

from django.conf import settings
from django.db import transaction

from ai_classifier.models import MLModel, TrainingJob
from .feature_extractor import FeatureExtractor
from .ocr_service import OCRService

logger = logging.getLogger(__name__)


class ModelTrainer:
    """
    Trainer per modelli ML di classificazione documenti.
    """
    
    def __init__(
        self,
        model_save_dir: str = None,
        model_type: str = 'random_forest',
        test_size: float = 0.2,
        random_state: int = 42,
        use_smote: bool = True,
    ):
        """
        Inizializza Model Trainer.
        
        Args:
            model_save_dir: Directory dove salvare modelli (default: NAS)
            model_type: Tipo modello ('random_forest', 'logistic_regression', 'svm')
            test_size: Percentuale test set
            random_state: Seed per riproducibilità
            use_smote: Se True, usa SMOTE per bilanciare classi sbilanciate
        """
        # Directory salvataggio modelli
        if model_save_dir is None:
            # Default: NAS se disponibile, altrimenti locale
            nas_path = getattr(settings, 'NAS_ML_MODELS_PATH', None)
            if nas_path and os.path.exists(nas_path):
                self.model_save_dir = nas_path
            else:
                # Fallback locale
                self.model_save_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        else:
            self.model_save_dir = model_save_dir
        
        # Crea directory se non esiste
        os.makedirs(self.model_save_dir, exist_ok=True)
        logger.info(f"📁 Model save directory: {self.model_save_dir}")
        
        self.model_type = model_type
        self.test_size = test_size
        self.random_state = random_state
        self.use_smote = use_smote
        
        # Inizializza services
        self.feature_extractor = FeatureExtractor()
        self.ocr_service = OCRService()
        
        # Label encoders (per tipo, cliente, titolario)
        self.label_encoders = {
            'tipo': LabelEncoder(),
            'cliente': LabelEncoder(),
            'titolario': LabelEncoder(),
        }
    
    def train_initial_model(
        self,
        documents: List[Any],  # QuerySet di Documento
        version: str = None,
    ) -> MLModel:
        """
        Training iniziale su documenti esistenti.
        
        Args:
            documents: QuerySet di documenti con file
            version: Versione modello (default: v1.0.0)
            
        Returns:
            MLModel salvato
        """
        if version is None:
            version = f"v1.0.0_{datetime.now():%Y%m%d_%H%M%S}"
        
        logger.info(f"🚀 INITIAL TRAINING - Versione: {version}")
        logger.info(f"   Documenti: {len(documents)}")
        
        # Step 1: Estrai features da tutti i documenti
        logger.info("📖 Step 1/5: Estrazione features...")
        features_list, labels = self._extract_features_from_documents(documents)
        
        if not features_list:
            raise ValueError("Nessuna feature estratta. Verifica i documenti.")
        
        logger.info(f"   ✅ Features estratte: {len(features_list)} documenti")
        
        # Step 2: Fit TF-IDF vectorizer
        logger.info("📚 Step 2/5: Training TF-IDF vectorizer...")
        texts = [f['raw_text'] for f in features_list if f.get('raw_text')]
        self.feature_extractor.fit_vectorizer(texts)
        
        # Step 3: Crea feature vectors
        logger.info("🔢 Step 3/5: Creazione feature vectors...")
        X, y = self._prepare_training_data(features_list, labels)
        
        logger.info(f"   ✅ Feature matrix: {X.shape}")
        logger.info(f"   ✅ Labels: {len(y)}")
        
        # Step 4: Train modello
        logger.info("🤖 Step 4/5: Training modello ML...")
        model, metrics = self._train_model(X, y, labels)
        
        # Step 5: Salva modello
        logger.info("💾 Step 5/5: Salvataggio modello...")
        ml_model = self._save_model(
            model=model,
            version=version,
            metrics=metrics,
            training_samples=len(documents),
        )
        
        logger.info("=" * 60)
        logger.info("✅ TRAINING COMPLETATO")
        logger.info(f"   Versione: {ml_model.version}")
        logger.info(f"   Accuracy: {ml_model.accuracy:.2%}")
        logger.info(f"   F1-Score: {ml_model.f1_score:.2%}")
        logger.info("=" * 60)
        
        return ml_model
    
    def retrain_model(
        self,
        training_job: TrainingJob,
        old_documents: List[Any],
        new_documents: List[Any],
    ) -> Optional[MLModel]:
        """
        Re-training con nuovi documenti dalla coda.
        
        Args:
            training_job: TrainingJob in corso
            old_documents: Documenti usati nel training precedente
            new_documents: Nuovi documenti dalla TrainingQueue
            
        Returns:
            Nuovo MLModel se training riuscito, None altrimenti
        """
        logger.info(f"🔄 RE-TRAINING - Job #{training_job.id}")
        logger.info(f"   Vecchi documenti: {len(old_documents)}")
        logger.info(f"   Nuovi documenti: {len(new_documents)}")
        
        # Combina documenti
        all_documents = list(old_documents) + list(new_documents)
        
        # Genera nuova versione
        previous_model = MLModel.get_active_model()
        if previous_model:
            # Incrementa versione minor
            prev_version = previous_model.version
            major, minor, patch = prev_version.lstrip('v').split('_')[0].split('.')
            new_version = f"v{major}.{int(minor)+1}.{patch}_{datetime.now():%Y%m%d_%H%M%S}"
        else:
            new_version = f"v1.0.0_{datetime.now():%Y%m%d_%H%M%S}"
        
        # Training
        try:
            new_model = self.train_initial_model(
                documents=all_documents,
                version=new_version,
            )
            
            # Calcola miglioramento
            if previous_model:
                accuracy_improvement = new_model.accuracy - previous_model.accuracy
                training_job.previous_model = previous_model
            else:
                accuracy_improvement = new_model.accuracy
            
            # Aggiorna job
            training_job.new_samples_count = len(new_documents)
            training_job.training_samples_count = len(all_documents)
            training_job.complete(new_model, accuracy_improvement)
            
            # Attiva nuovo modello se miglioramento > 2% o primo modello
            if accuracy_improvement > 0.02 or not previous_model:
                new_model.activate()
                logger.info(f"✅ Nuovo modello attivato (improvement: {accuracy_improvement:+.2%})")
            else:
                logger.warning(f"⚠️  Nuovo modello NON attivato (improvement troppo basso: {accuracy_improvement:+.2%})")
            
            return new_model
        
        except Exception as e:
            logger.error(f"❌ Errore re-training: {e}", exc_info=True)
            training_job.fail(str(e))
            return None
    
    def _extract_features_from_documents(
        self,
        documents: List[Any],
    ) -> Tuple[List[Dict], Dict[str, List]]:
        """
        Estrae features da lista di documenti.
        
        Esclude documenti CLAV (Carte di lavoro) che sono considerati
        documenti residuali/generici da inserire manualmente.
        
        Returns:
            (features_list, labels_dict)
        """
        features_list = []
        labels = {
            'tipo': [],
            'cliente': [],
            'titolario': [],
        }
        
        excluded_count = 0
        
        for i, doc in enumerate(documents, 1):
            if i % 50 == 0:
                logger.info(f"   Elaborando documento {i}/{len(documents)}...")
            
            try:
                # ESCLUDI documenti CLAV (Carte di lavoro)
                # Tipo generico/residuale da inserire manualmente
                if doc.tipo and doc.tipo.codice == 'CLAV':
                    excluded_count += 1
                    continue
                
                # Verifica che il documento abbia un file
                if not doc.file or not os.path.exists(doc.file.path):
                    logger.warning(f"   ⚠️  Doc #{doc.id}: file non trovato, skip")
                    continue
                
                # Estrai testo con OCR
                ocr_result = self.ocr_service.extract_text_from_file(
                    file_path=doc.file.path,
                )
                
                text = ocr_result.get('text', '')
                if not text or len(text) < 50:
                    logger.warning(f"   ⚠️  Doc #{doc.id}: testo troppo corto, skip")
                    continue
                
                # Estrai features
                features = self.feature_extractor.extract_features(
                    text=text,
                    filename=os.path.basename(doc.file.name),
                    metadata=ocr_result.get('metadata', {}),
                )
                
                features_list.append(features)
                
                # Labels
                labels['tipo'].append(doc.tipo.codice if doc.tipo else 'UNK')
                labels['cliente'].append(doc.cliente_id if doc.cliente_id else 0)
                labels['titolario'].append(doc.titolario_voce_id if hasattr(doc, 'titolario_voce_id') and doc.titolario_voce_id else 0)
            
            except Exception as e:
                logger.error(f"   ❌ Errore elaborazione Doc #{doc.id}: {e}")
                continue
        
        if excluded_count > 0:
            logger.info(f"   ℹ️  Esclusi {excluded_count} documenti CLAV (Carte di lavoro)")
        
        return features_list, labels
    
    def _prepare_training_data(
        self,
        features_list: List[Dict],
        labels: Dict[str, List],
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Prepara feature matrix e label arrays per training.
        """
        # Ri-estrai TF-IDF ora che il vectorizer è fitted
        X_vectors = []
        for features in features_list:
            # Ri-esegui extract_text_features ora che vectorizer è fitted
            text = features.get('raw_text', '')
            if text:
                features['text_features'] = self.feature_extractor._extract_text_features(text)
            
            # Converti a numpy vector
            vector = self.feature_extractor.get_feature_vector(features)
            X_vectors.append(vector)
        
        X = np.vstack(X_vectors)
        
        # Encode labels
        y_encoded = {}
        for label_name, label_values in labels.items():
            # Fit label encoder
            self.label_encoders[label_name].fit(label_values)
            # Transform
            y_encoded[label_name] = self.label_encoders[label_name].transform(label_values)
        
        return X, y_encoded
    
    def _train_model(
        self,
        X: np.ndarray,
        y: Dict[str, np.ndarray],
        labels_raw: Dict[str, List],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Training del modello ML.
        
        Per ora usiamo solo classificazione 'tipo' (single-output).
        In futuro possiamo estendere a multi-output (tipo + cliente + titolario).
        """
        # Per ora solo 'tipo' documento
        y_tipo = y['tipo']
        
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_tipo,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y_tipo if len(np.unique(y_tipo)) > 1 else None,
        )
        
        logger.info(f"   Train set: {X_train.shape[0]} samples")
        logger.info(f"   Test set: {X_test.shape[0]} samples")
        
        # Bilanciamento con SMOTE (se abilitato e necessario)
        if self.use_smote and len(np.unique(y_train)) > 1:
            try:
                logger.info("   ⚖️  Applicando SMOTE per bilanciamento classi...")
                smote = SMOTE(random_state=self.random_state)
                X_train, y_train = smote.fit_resample(X_train, y_train)
                logger.info(f"   ✅ Train set dopo SMOTE: {X_train.shape[0]} samples")
            except Exception as e:
                logger.warning(f"   ⚠️  SMOTE fallito: {e}, procedo senza")
        
        # Inizializza modello
        if self.model_type == 'random_forest':
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=self.random_state,
                n_jobs=-1,  # Usa tutti i core
                class_weight='balanced',  # Gestione classi sbilanciate
            )
        else:
            raise ValueError(f"Model type non supportato: {self.model_type}")
        
        # Train
        logger.info(f"   🏋️  Training {self.model_type}...")
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        
        # Metriche
        accuracy = accuracy_score(y_test, y_pred)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_test, y_pred, average='weighted', zero_division=0
        )
        
        logger.info(f"   ✅ Accuracy: {accuracy:.2%}")
        logger.info(f"   ✅ Precision: {precision:.2%}")
        logger.info(f"   ✅ Recall: {recall:.2%}")
        logger.info(f"   ✅ F1-Score: {f1:.2%}")
        
        # Classification report dettagliato
        tipo_labels = self.label_encoders['tipo'].classes_
        report = classification_report(
            y_test, y_pred,
            target_names=tipo_labels,
            zero_division=0,
        )
        logger.info("\n📊 CLASSIFICATION REPORT:\n" + report)
        
        # Metriche da salvare
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'test_samples': len(y_test),
            'classification_report': report,
        }
        
        # Feature importance (se RandomForest)
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            top_features = np.argsort(importances)[-20:][::-1]  # Top 20
            metrics['feature_importances'] = {
                'top_20_indices': top_features.tolist(),
                'top_20_scores': importances[top_features].tolist(),
            }
        
        return {'model': model}, metrics
    
    def _save_model(
        self,
        model: Dict[str, Any],
        version: str,
        metrics: Dict[str, Any],
        training_samples: int,
    ) -> MLModel:
        """
        Salva modello su filesystem e crea record MLModel.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Path files
        model_filename = f"model_{version}_{timestamp}.pkl"
        vectorizer_filename = f"vectorizer_{version}_{timestamp}.pkl"
        encoders_filename = f"encoders_{version}_{timestamp}.pkl"
        
        model_path = os.path.join(self.model_save_dir, model_filename)
        vectorizer_path = os.path.join(self.model_save_dir, vectorizer_filename)
        encoders_path = os.path.join(self.model_save_dir, encoders_filename)
        
        # Salva files
        logger.info(f"   💾 Salvataggio modello: {model_path}")
        joblib.dump(model['model'], model_path)
        
        logger.info(f"   💾 Salvataggio vectorizer: {vectorizer_path}")
        joblib.dump(self.feature_extractor.vectorizer, vectorizer_path)
        
        logger.info(f"   💾 Salvataggio label encoders: {encoders_path}")
        joblib.dump(self.label_encoders, encoders_path)
        
        # Crea record MLModel
        with transaction.atomic():
            ml_model = MLModel.objects.create(
                version=version,
                model_type=self.model_type,
                model_file_path=model_path,
                vectorizer_file_path=vectorizer_path,
                label_encoder_file_path=encoders_path,
                accuracy=metrics['accuracy'],
                precision=metrics['precision'],
                recall=metrics['recall'],
                f1_score=metrics['f1_score'],
                training_samples=training_samples,
                training_stats={
                    'test_samples': metrics['test_samples'],
                    'feature_importances': metrics.get('feature_importances', {}),
                    'classification_report': metrics['classification_report'],
                },
                is_active=False,  # Non attivare automaticamente
            )
        
        logger.info(f"   ✅ MLModel salvato: ID={ml_model.id}")
        
        return ml_model
