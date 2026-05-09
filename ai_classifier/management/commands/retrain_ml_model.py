"""
Management command: retrain_ml_model

Esegue re-training del modello ML usando documenti dalla TrainingQueue.

Usage:
    python manage.py retrain_ml_model [--min-samples N] [--auto-activate] [--dry-run]
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ai_classifier.models import MLModel, TrainingQueue, TrainingJob
from ai_classifier.services.ml.model_trainer import ModelTrainer
from documenti.models import Documento

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Re-training modello ML con documenti dalla TrainingQueue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-samples',
            type=int,
            default=20,
            help='Numero minimo documenti in coda per procedere con re-training (default: 20)',
        )
        parser.add_argument(
            '--auto-activate',
            action='store_true',
            help='Attiva automaticamente nuovo modello se accuracy migliora ≥2%%',
        )
        parser.add_argument(
            '--improvement-threshold',
            type=float,
            default=0.02,
            help='Soglia miglioramento accuracy per auto-attivazione (default: 0.02 = 2%%)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula re-training senza salvare (per test)',
        )

    def handle(self, *args, **options):
        min_samples = options['min_samples']
        auto_activate = options['auto_activate']
        improvement_threshold = options['improvement_threshold']
        dry_run = options['dry_run']
        
        self.stdout.write('=' * 70)
        self.stdout.write(self.style.SUCCESS('🔄 RE-TRAINING MODELLO ML'))
        self.stdout.write('=' * 70)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  Modalità DRY-RUN: nessuna modifica sarà salvata'))
        
        # 1. Verifica documenti in coda
        queue_items = TrainingQueue.objects.filter(processed=False).select_related('documento', 'documento__tipo')
        queue_count = queue_items.count()
        
        self.stdout.write(f'\n📊 Documenti in TrainingQueue: {queue_count}')
        
        if queue_count < min_samples:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Documenti insufficienti per re-training (minimo: {min_samples})'
                )
            )
            self.stdout.write(f'   Attendi altri {min_samples - queue_count} documenti')
            return
        
        # 2. Ottieni modello attivo corrente
        active_model = MLModel.objects.filter(is_active=True).first()
        if not active_model:
            raise CommandError('❌ Nessun modello attivo trovato. Esegui prima il training iniziale.')
        
        self.stdout.write(f'\n📦 Modello attivo corrente:')
        self.stdout.write(f'   Versione: {active_model.version}')
        self.stdout.write(f'   Accuracy: {active_model.accuracy:.2%}')
        self.stdout.write(f'   Samples: {active_model.training_samples}')
        
        # 3. Prepara documenti per training
        # Documenti usati nel training precedente (tutti i documenti con file, escluso CLAV)
        old_documents = Documento.objects.filter(
            file__isnull=False
        ).exclude(
            file=''
        ).exclude(
            tipo__codice='CLAV'  # Escludi CLAV
        ).select_related('tipo', 'cliente', 'titolario_voce')
        
        # Documenti dalla coda (nuovi o corretti)
        new_document_ids = [item.documento_id for item in queue_items]
        new_documents = Documento.objects.filter(
            id__in=new_document_ids,
            file__isnull=False
        ).exclude(
            file=''
        ).exclude(
            tipo__codice='CLAV'  # Escludi CLAV
        ).select_related('tipo', 'cliente', 'titolario_voce')
        
        self.stdout.write(f'\n📚 Dataset training:')
        self.stdout.write(f'   Documenti esistenti: {old_documents.count()}')
        self.stdout.write(f'   Nuovi documenti: {new_documents.count()}')
        self.stdout.write(f'   Totale: {old_documents.count() + new_documents.count()}')
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ DRY-RUN completato'))
            return
        
        # 4. Crea TrainingJob
        with transaction.atomic():
            training_job = TrainingJob.objects.create(
                previous_model=active_model,
                status='running',
                started_at=timezone.now(),
            )
        
        self.stdout.write(f'\n🚀 TrainingJob #{training_job.id} avviato...')
        
        try:
            # 5. Esegui re-training
            trainer = ModelTrainer()
            
            # Combina vecchi e nuovi documenti
            all_documents = list(set(list(old_documents) + list(new_documents)))
            
            self.stdout.write(f'\n🤖 Training in corso su {len(all_documents)} documenti...')
            
            # Genera nuova versione
            from datetime import datetime
            major, minor, patch = active_model.version.lstrip('v').split('_')[0].split('.')
            new_version = f"v{major}.{int(minor)+1}.{patch}_{datetime.now():%Y%m%d_%H%M%S}"
            
            new_model = trainer.train_initial_model(
                documents=all_documents,
                version=new_version,
            )
            
            # 6. Confronta metriche
            accuracy_improvement = new_model.accuracy - active_model.accuracy
            
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(self.style.SUCCESS('✅ RE-TRAINING COMPLETATO'))
            self.stdout.write('=' * 70)
            self.stdout.write(f'\n📊 Confronto Modelli:')
            self.stdout.write(f'\n   PRECEDENTE ({active_model.version}):')
            self.stdout.write(f'      Accuracy:  {active_model.accuracy:.2%}')
            self.stdout.write(f'      Samples:   {active_model.training_samples}')
            self.stdout.write(f'\n   NUOVO ({new_model.version}):')
            self.stdout.write(f'      Accuracy:  {new_model.accuracy:.2%}')
            self.stdout.write(f'      Samples:   {new_model.training_samples}')
            self.stdout.write(f'\n   📈 Miglioramento: {accuracy_improvement:+.2%}')
            
            # 7. Decidi se attivare nuovo modello
            should_activate = False
            
            if accuracy_improvement >= improvement_threshold:
                should_activate = True
                reason = f'Accuracy migliorata di {accuracy_improvement:.2%} (soglia: {improvement_threshold:.0%})'
            elif auto_activate and accuracy_improvement > 0:
                should_activate = True
                reason = f'Auto-attivazione abilitata e accuracy migliorata di {accuracy_improvement:.2%}'
            else:
                reason = f'Miglioramento {accuracy_improvement:.2%} < soglia {improvement_threshold:.0%}'
            
            self.stdout.write(f'\n🎯 Decisione attivazione:')
            self.stdout.write(f'   {reason}')
            
            if should_activate:
                # Disattiva vecchio modello
                active_model.is_active = False
                active_model.save()
                
                # Attiva nuovo modello
                new_model.is_active = True
                new_model.save()
                
                self.stdout.write(self.style.SUCCESS(f'\n   ✅ Nuovo modello ATTIVATO: {new_model.version}'))
            else:
                self.stdout.write(self.style.WARNING(f'\n   ⚠️  Nuovo modello NON attivato (mantieni {active_model.version})'))
            
            # 8. Aggiorna TrainingJob
            training_job.new_model = new_model
            training_job.status = 'completed'
            training_job.completed_at = timezone.now()
            training_job.accuracy_improvement = accuracy_improvement
            training_job.activated = should_activate
            training_job.save()
            
            # 9. Marca documenti in coda come processati
            queue_items.update(processed=True, processed_at=timezone.now())
            
            self.stdout.write(f'\n✅ {queue_count} documenti rimossi dalla TrainingQueue')
            self.stdout.write('\n' + '=' * 70)
            
        except Exception as e:
            # Errore durante training
            training_job.status = 'failed'
            training_job.error_message = str(e)
            training_job.completed_at = timezone.now()
            training_job.save()
            
            self.stdout.write(self.style.ERROR(f'\n❌ ERRORE durante re-training: {e}'))
            import traceback
            traceback.print_exc()
            raise CommandError(f'Re-training fallito: {e}')
