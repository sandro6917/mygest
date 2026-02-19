"""
Management command per importare esempi di training da una directory.
"""
import os
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from ai_classifier.models import TrainingExample
from ai_classifier.services.extractors.pdf_extractor import PDFExtractor
from ai_classifier.services.extractors.metadata_extractor import MetadataExtractor

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Importa esempi di training da una directory organizzata per tipo'

    def add_arguments(self, parser):
        parser.add_argument(
            'base_directory',
            type=str,
            help='Directory base contenente sottocartelle per tipo (es. /training_data)'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username dell\'utente creatore (default: admin)'
        )
        parser.add_argument(
            '--priority',
            type=int,
            default=5,
            help='Priorità degli esempi importati (default: 5)'
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Sovrascrivi esempi esistenti con stesso file_name'
        )

    def handle(self, *args, **options):
        base_dir = options['base_directory']
        username = options['user']
        priority = options['priority']
        overwrite = options['overwrite']

        # Verifica directory
        if not os.path.exists(base_dir) or not os.path.isdir(base_dir):
            raise CommandError(f'Directory non valida: {base_dir}')

        # Trova utente
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Utente non trovato: {username}')

        # Inizializza extractors
        pdf_extractor = PDFExtractor(max_pages=5)
        metadata_extractor = MetadataExtractor()

        self.stdout.write(f'\n📚 Importazione Esempi di Training')
        self.stdout.write(f'Directory: {base_dir}')
        self.stdout.write(f'Utente: {username}')
        self.stdout.write('=' * 60)

        total_imported = 0
        total_skipped = 0
        total_errors = 0

        # Scansiona sottodirectory (ciascuna rappresenta un tipo documento)
        for entry in os.scandir(base_dir):
            if not entry.is_dir():
                continue

            document_type = entry.name.upper()
            type_dir = entry.path

            self.stdout.write(f'\n📁 Processing type: {document_type}')

            # Scansiona file nella directory del tipo
            for file_entry in os.scandir(type_dir):
                if not file_entry.is_file():
                    continue

                file_name = file_entry.name
                file_path = file_entry.path
                file_ext = os.path.splitext(file_name)[1].lower()

                # Supporta solo PDF per ora
                if file_ext != '.pdf':
                    self.stdout.write(f'  ⏭️  Skip {file_name} (formato non supportato)')
                    total_skipped += 1
                    continue

                # Verifica se esiste già
                if not overwrite and TrainingExample.objects.filter(file_name=file_name).exists():
                    self.stdout.write(f'  ⏭️  Skip {file_name} (già esistente)')
                    total_skipped += 1
                    continue

                try:
                    # Estrai testo
                    extracted_text = pdf_extractor.extract_text(file_path)

                    # Estrai metadata
                    metadata = metadata_extractor.extract_from_text(extracted_text)

                    # Crea o aggiorna esempio
                    example, created = TrainingExample.objects.update_or_create(
                        file_name=file_name,
                        defaults={
                            'file_path': file_path,
                            'document_type': document_type,
                            'extracted_text': extracted_text,
                            'extracted_metadata': metadata,
                            'is_active': True,
                            'priority': priority,
                            'created_by': user,
                        }
                    )

                    action = '✅ Importato' if created else '🔄 Aggiornato'
                    self.stdout.write(f'  {action}: {file_name} ({len(extracted_text)} chars)')
                    total_imported += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Errore {file_name}: {e}')
                    )
                    total_errors += 1

        # Riepilogo
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'\n✅ Importati: {total_imported}'))
        self.stdout.write(f'⏭️  Saltati: {total_skipped}')
        if total_errors > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errori: {total_errors}'))

        self.stdout.write('\n💡 Tip: Gli esempi sono ora disponibili per il Few-Shot Learning!')
        self.stdout.write('   Riavvia i job di classificazione per usare i nuovi esempi.\n')
