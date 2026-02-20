"""
Management command per eliminare occorrenze in eccesso
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from scadenze.models import Scadenza, ScadenzaOccorrenza


class Command(BaseCommand):
    help = 'Elimina occorrenze in eccesso dalle scadenze, mantenendo solo le ultime N'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scadenza-id',
            type=int,
            help='ID della scadenza da cui eliminare occorrenze (opzionale, altrimenti tutte)'
        )
        parser.add_argument(
            '--keep',
            type=int,
            default=100,
            help='Numero massimo di occorrenze da mantenere per scadenza (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe eliminato senza eliminare realmente'
        )

    def handle(self, *args, **options):
        scadenza_id = options.get('scadenza_id')
        keep = options['keep']
        dry_run = options['dry_run']

        # Filtra scadenze
        if scadenza_id:
            scadenze = Scadenza.objects.filter(id=scadenza_id)
            if not scadenze.exists():
                self.stdout.write(self.style.ERROR(f'Scadenza con ID {scadenza_id} non trovata'))
                return
        else:
            # Trova scadenze con troppe occorrenze
            scadenze = Scadenza.objects.annotate(
                num_occ=Count('occorrenze')
            ).filter(num_occ__gt=keep)

        if not scadenze.exists():
            self.stdout.write(self.style.SUCCESS('Nessuna scadenza con occorrenze in eccesso'))
            return

        total_deleted = 0
        
        for scadenza in scadenze:
            num_occorrenze = scadenza.occorrenze.count()
            
            if num_occorrenze <= keep:
                continue
            
            to_delete = num_occorrenze - keep
            
            # Ottieni le occorrenze più vecchie da eliminare (ordinate per data inizio)
            occorrenze_to_delete = scadenza.occorrenze.order_by('inizio')[:to_delete]
            ids_to_delete = list(occorrenze_to_delete.values_list('id', flat=True))
            
            self.stdout.write(
                f'\nScadenza: "{scadenza.titolo}" (ID: {scadenza.id})'
            )
            self.stdout.write(
                f'  Occorrenze totali: {num_occorrenze}'
            )
            self.stdout.write(
                f'  Da eliminare: {to_delete} (più vecchie)'
            )
            self.stdout.write(
                f'  Da mantenere: {keep} (più recenti)'
            )
            
            if not dry_run:
                # Elimina in batch per evitare problemi di memoria
                deleted_count = ScadenzaOccorrenza.objects.filter(id__in=ids_to_delete).delete()[0]
                total_deleted += deleted_count
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Eliminate {deleted_count} occorrenze')
                )
            else:
                total_deleted += to_delete
                self.stdout.write(
                    self.style.WARNING(f'  [DRY RUN] Verrebbero eliminate {to_delete} occorrenze')
                )
        
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'[DRY RUN] Verrebbero eliminate in totale {total_deleted} occorrenze')
            )
            self.stdout.write(
                self.style.WARNING('Esegui senza --dry-run per eliminare realmente')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Eliminate in totale {total_deleted} occorrenze')
            )
