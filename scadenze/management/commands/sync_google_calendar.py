"""
Management command per sincronizzare manualmente le occorrenze con Google Calendar.
Utile per:
- Sincronizzare occorrenze esistenti che non sono ancora state sincronizzate
- Ri-sincronizzare occorrenze dopo modifiche manuali
- Risolvere eventuali problemi di sincronizzazione

Uso:
    python manage.py sync_google_calendar
    python manage.py sync_google_calendar --all
    python manage.py sync_google_calendar --non-synced
    python manage.py sync_google_calendar --dry-run
    python manage.py sync_google_calendar --occorrenza-id 123
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from scadenze.models import ScadenzaOccorrenza
from scadenze.services import GoogleCalendarSync


class Command(BaseCommand):
    help = "Sincronizza le occorrenze con Google Calendar"

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sincronizza tutte le occorrenze (incluse quelle già sincronizzate)',
        )
        parser.add_argument(
            '--non-synced',
            action='store_true',
            help='Sincronizza solo le occorrenze mai sincronizzate',
        )
        parser.add_argument(
            '--from-date',
            type=str,
            help='Sincronizza occorrenze a partire da questa data (formato: YYYY-MM-DD)',
        )
        parser.add_argument(
            '--occorrenza-id',
            type=int,
            help='Sincronizza una specifica occorrenza tramite ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra le occorrenze da sincronizzare senza effettivamente sincronizzarle',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forza la ri-sincronizzazione anche di occorrenze annullate (sconsigliato)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        occorrenza_id = options.get('occorrenza_id')
        
        # Inizializza il servizio di sincronizzazione
        try:
            sync = GoogleCalendarSync()
        except Exception as e:
            raise CommandError(f'Errore nell\'inizializzazione di Google Calendar: {e}')
        
        # Determina quali occorrenze sincronizzare
        if occorrenza_id:
            # Sincronizza una singola occorrenza
            try:
                occorrenze = ScadenzaOccorrenza.objects.filter(id=occorrenza_id)
                if not occorrenze.exists():
                    raise CommandError(f'Occorrenza con ID {occorrenza_id} non trovata')
            except ValueError:
                raise CommandError('ID occorrenza non valido')
        else:
            # Costruisci la query
            occorrenze = ScadenzaOccorrenza.objects.select_related('scadenza')
            
            # Filtra per stato (esclude annullate a meno che --force)
            if not force:
                occorrenze = occorrenze.exclude(stato=ScadenzaOccorrenza.Stato.ANNULLATA)
            
            # Filtra per data
            if options.get('from_date'):
                try:
                    from datetime import datetime
                    from_date = datetime.strptime(options['from_date'], '%Y-%m-%d')
                    occorrenze = occorrenze.filter(inizio__gte=from_date)
                except ValueError:
                    raise CommandError('Formato data non valido. Usa YYYY-MM-DD')
            
            # Filtra per stato di sincronizzazione
            if options['non_synced']:
                occorrenze = occorrenze.filter(google_calendar_event_id='')
            elif not options['all']:
                # Di default, sincronizza solo future e non ancora sincronizzate
                now = timezone.now()
                occorrenze = occorrenze.filter(
                    inizio__gte=now
                ).filter(
                    google_calendar_event_id=''
                )
        
        # Ordina per data di inizio
        occorrenze = occorrenze.order_by('inizio')
        count = occorrenze.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Nessuna occorrenza da sincronizzare.')
            )
            return
        
        # Mostra il riepilogo
        self.stdout.write(
            self.style.WARNING(f'\nTrovate {count} occorrenze da sincronizzare...\n')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.NOTICE('Modalità DRY RUN - nessuna sincronizzazione effettiva\n')
            )
            for occ in occorrenze[:20]:  # Mostra solo le prime 20
                sync_status = '✓ Già sincronizzata' if occ.google_calendar_event_id else '✗ Non sincronizzata'
                self.stdout.write(
                    f'  [{sync_status}] {occ.scadenza.titolo} - {occ.inizio:%Y-%m-%d %H:%M}'
                )
            if count > 20:
                self.stdout.write(f'\n  ... e altre {count - 20} occorrenze')
            return
        
        # Conferma prima di procedere
        if count > 10 and not options['all'] and not occorrenza_id:
            confirm = input(
                f'\nStai per sincronizzare {count} occorrenze. Continuare? [s/N]: '
            )
            if confirm.lower() not in ['s', 'si', 'sì', 'y', 'yes']:
                self.stdout.write(self.style.WARNING('Operazione annullata.'))
                return
        
        # Esegui la sincronizzazione
        successi = 0
        errori = 0
        
        self.stdout.write('')  # Riga vuota
        for i, occ in enumerate(occorrenze, 1):
            try:
                # Mostra progresso
                if count > 10 and i % 10 == 0:
                    self.stdout.write(f'Progresso: {i}/{count}...')
                
                sync.upsert_occurrence(occ)
                successi += 1
                
                if count <= 20:  # Mostra dettagli solo se poche occorrenze
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {occ.scadenza.titolo} - {occ.inizio:%Y-%m-%d %H:%M}'
                        )
                    )
            except Exception as e:
                errori += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Errore per {occ.scadenza.titolo}: {str(e)}'
                    )
                )
        
        # Riepilogo finale
        self.stdout.write('')  # Riga vuota
        self.stdout.write(
            self.style.SUCCESS(f'Sincronizzazione completata!')
        )
        self.stdout.write(f'  Successi: {successi}')
        if errori > 0:
            self.stdout.write(
                self.style.ERROR(f'  Errori: {errori}')
            )
        
        # Suggerimenti
        if errori > 0:
            self.stdout.write(
                self.style.WARNING(
                    '\nSuggerimento: controlla i log per maggiori dettagli sugli errori.'
                )
            )
