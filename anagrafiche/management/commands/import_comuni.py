"""
Management command per importare i comuni italiani da file JSON.
Uso: python manage.py import_comuni [path_to_json]
"""
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from anagrafiche.models_comuni import ComuneItaliano


class Command(BaseCommand):
    help = 'Importa comuni italiani da file JSON (formato gi_comuni_cap.json)'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            nargs='?',
            default='gi_comuni_cap.json',
            help='Path al file JSON dei comuni (default: gi_comuni_cap.json nella root del progetto)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina tutti i comuni esistenti prima dell\'import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula l\'import senza salvare nel database'
        )

    def handle(self, *args, **options):
        json_file = options['json_file']
        clear = options['clear']
        dry_run = options['dry_run']

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'File non trovato: {json_file}')
        except json.JSONDecodeError as e:
            raise CommandError(f'Errore parsing JSON: {e}')

        if not isinstance(data, list):
            raise CommandError('Il file JSON deve contenere un array di comuni')

        self.stdout.write(f'Trovati {len(data)} record nel file JSON')

        if dry_run:
            self.stdout.write(self.style.WARNING('Modalità DRY-RUN: nessuna modifica verrà salvata'))

        if clear and not dry_run:
            count = ComuneItaliano.objects.count()
            ComuneItaliano.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Eliminati {count} comuni esistenti'))

        # Raggruppa per codice_istat per gestire comuni con più CAP
        comuni_dict = {}
        for record in data:
            codice = record.get('codice_istat')
            if not codice:
                continue
            
            # Primo record per questo comune o CAP minore
            if codice not in comuni_dict:
                comuni_dict[codice] = record
            # Nota: alcuni comuni hanno più CAP, prendiamo il primo

        self.stdout.write(f'Comuni unici da importare: {len(comuni_dict)}')

        created = 0
        updated = 0
        skipped = 0

        with transaction.atomic():
            for codice_istat, record in comuni_dict.items():
                try:
                    # Parsing coordinate
                    lat = None
                    lon = None
                    try:
                        lat = float(record.get('lat', 0))
                        lon = float(record.get('lon', 0))
                    except (ValueError, TypeError):
                        pass

                    comune_data = {
                        'codice_belfiore': record.get('codice_belfiore', ''),
                        'nome': record.get('denominazione_ita', ''),
                        'nome_alternativo': record.get('denominazione_ita_altra', ''),
                        'provincia': record.get('sigla_provincia', ''),
                        'nome_provincia': record.get('denominazione_provincia', ''),
                        'cap': record.get('cap', ''),
                        'regione': record.get('denominazione_regione', ''),
                        'codice_regione': record.get('codice_regione', ''),
                        'flag_capoluogo': record.get('flag_capoluogo', 'NO'),
                        'latitudine': lat,
                        'longitudine': lon,
                        'attivo': True,
                    }

                    if dry_run:
                        # Solo simulazione
                        exists = ComuneItaliano.objects.filter(codice_istat=codice_istat).exists()
                        if exists:
                            updated += 1
                        else:
                            created += 1
                    else:
                        # Import reale
                        comune, was_created = ComuneItaliano.objects.update_or_create(
                            codice_istat=codice_istat,
                            defaults=comune_data
                        )
                        if was_created:
                            created += 1
                        else:
                            updated += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Errore importando comune {codice_istat}: {e}')
                    )
                    skipped += 1
                    continue

            if dry_run:
                # Rollback transazione in dry-run
                transaction.set_rollback(True)

        # Report finale
        self.stdout.write(self.style.SUCCESS(f'\n{"=" * 60}'))
        self.stdout.write(self.style.SUCCESS(f'Import completato!'))
        self.stdout.write(self.style.SUCCESS(f'{"=" * 60}'))
        self.stdout.write(f'Comuni creati:    {created}')
        self.stdout.write(f'Comuni aggiornati: {updated}')
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'Comuni saltati:    {skipped}'))
        self.stdout.write(self.style.SUCCESS(f'Totale elaborati:  {created + updated}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY-RUN: nessuna modifica salvata nel database'))
