"""
Signals per AI Classifier - Feedback Loop Automatico

Gestisce:
- Auto-predizione su salvataggio documento con file
- Confronto predizione vs tipo reale
- Auto-aggiunta a TrainingQueue se diversi
"""
import hashlib
import logging
import threading
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from documenti.models import Documento
from ai_classifier.models import DocumentPrediction, TrainingQueue

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Documento)
def auto_predict_on_documento_save(sender, instance, created, **kwargs):
    # Solo se documento ha file e tipo
    if not instance.file or not instance.tipo:
        return

    # Skip se tipo è CLAV (escluso da AI)
    if instance.tipo.codice == 'CLAV':
        return

    # Cattura valori scalari prima che la transazione si chiuda
    doc_id = instance.id
    tipo_codice = instance.tipo.codice
    try:
        file_path = instance.file.path
    except Exception:
        return
    file_name = instance.file.name

    def _run_prediction():
        try:
            import os
            # Import qui per evitare circular imports
            from django.db import connection as _db_connection
            from ai_classifier.services.ml.predictor import Predictor
            from documenti.models import DocumentiTipo
            # Ricarica il documento per ottenere il path file aggiornato
            # (il file può essere spostato tra il save e l'on_commit)
            doc_instance = Documento.objects.filter(pk=doc_id).first()
            if not doc_instance or not doc_instance.file:
                return

            current_file_path = doc_instance.file.path
            current_file_name = doc_instance.file.name

            if not os.path.exists(current_file_path):
                logger.warning(f"⚠️  File non trovato per Doc #{doc_id}: {current_file_path}, skip auto-predizione")
                return

            logger.info(f"🤖 Auto-predizione per Documento #{doc_id} (tipo: {tipo_codice})")

            predictor = Predictor()
            if not predictor.ml_model:
                logger.warning("⚠️  Nessun modello ML attivo, skip auto-predizione")
                return

            result = predictor.predict(
                file_path=current_file_path,
                filename=current_file_name,
                return_top_n=3,
                min_confidence=0.0,
            )

            if not result['success']:
                logger.error(f"❌ Predizione fallita: {result.get('error')}")
                return

            tipo_pred = result['predictions']['tipo']
            top_tipo = tipo_pred['top_prediction']
            top_confidence = tipo_pred['confidence']

            logger.info(f"   Predetto: {top_tipo} (confidence: {top_confidence:.1%})")
            logger.info(f"   Reale: {tipo_codice}")

            try:
                predicted_type_obj = DocumentiTipo.objects.get(codice=top_tipo)
            except DocumentiTipo.DoesNotExist:
                logger.warning(f"   ⚠️  Tipo predetto '{top_tipo}' non trovato nel DB, skip DocumentPrediction")
                return

            file_hash = ''
            try:
                with open(current_file_path, 'rb') as fh:
                    file_hash = hashlib.sha256(fh.read()).hexdigest()
            except Exception:
                pass

            doc_pred, pred_created = DocumentPrediction.objects.update_or_create(
                documento=doc_instance,
                defaults={
                    'ml_model': predictor.ml_model,
                    'original_filename': current_file_name,
                    'file_hash': file_hash,
                    'predicted_type': predicted_type_obj,
                    'type_confidence': top_confidence,
                    'user_corrected': (top_tipo != tipo_codice),
                    'predicted_metadata': {
                        'all_predictions': tipo_pred['all_predictions'],
                        'ocr_method': result['metadata'].get('ocr_method'),
                        'text_length': result['metadata'].get('text_length'),
                    },
                    'extracted_features': result['metadata'].get('extracted_features') or {},
                }
            )

            action = "creata" if pred_created else "aggiornata"
            logger.info(f"   ✅ DocumentPrediction {action} (ID: {doc_pred.id})")

            if top_tipo != tipo_codice:
                if not TrainingQueue.objects.filter(prediction=doc_pred).exists():
                    TrainingQueue.objects.create(prediction=doc_pred)
                    logger.info(f"   📥 Aggiunto a TrainingQueue (predizione errata)")
                else:
                    logger.debug(f"   ℹ️  Già in TrainingQueue")
            else:
                logger.info(f"   ✅ Predizione corretta!")

        except Exception as e:
            logger.error(f"❌ Errore durante auto-predizione Doc #{doc_id}: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Chiudi la connessione DB del thread background per evitare leak
            try:
                from django.db import connection as _db_conn
                _db_conn.close()
            except Exception:
                pass

    def _start_prediction_thread():
        # on_commit non deve mai propagare eccezioni (documento già committato,
        # un'eccezione qui causerebbe HTTP 500 con documento già creato nel DB)
        try:
            t = threading.Thread(target=_run_prediction, daemon=True, name=f"ai-predict-doc-{doc_id}")
            t.start()
        except Exception as e:
            logger.warning(f"⚠️  Impossibile avviare thread predizione Doc #{doc_id}: {e}")

    transaction.on_commit(_start_prediction_thread)
