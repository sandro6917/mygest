"""
Management command per inviare gli alert programmati.
Può essere eseguito via cron ogni 5-15 minuti.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from scadenze.models import ScadenzaAlert
from scadenze.services import AlertDispatcher


class Command(BaseCommand):
    help = "Invia gli alert programmati che sono pronti per essere inviati"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra gli alert da inviare senza effettivamente inviarli',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Trova tutti gli alert pronti
        alerts_da_inviare = ScadenzaAlert.objects.filter(
            stato=ScadenzaAlert.Stato.PENDENTE,
            alert_programmata_il__lte=now
        ).select_related(
            'occorrenza__scadenza'
        ).order_by('alert_programmata_il')
        
        count = alerts_da_inviare.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Nessun alert da inviare al momento.')
            )
            return
        
        self.stdout.write(
            self.style.WARNING(f'Trovati {count} alert da inviare...')
        )
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('Modalità DRY RUN - nessun alert verrà inviato'))
            for alert in alerts_da_inviare:
                self.stdout.write(
                    f'  - {alert.occorrenza.scadenza.titolo} / {alert.occorrenza}'
                    f' ({alert.offset_alert} {alert.get_offset_alert_periodo_display()} prima)'
                    f' → {alert.get_metodo_alert_display()}'
                )
            return
        
        dispatcher = AlertDispatcher()
        inviati = 0
        falliti = 0
        
        for alert in alerts_da_inviare:
            try:
                dispatcher.dispatch_alert(alert)
                inviati += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Alert inviato: {alert.occorrenza.scadenza.titolo} '
                        f'({alert.get_metodo_alert_display()})'
                    )
                )
            except Exception as exc:
                falliti += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Errore invio alert {alert.pk}: {exc}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Completato: {inviati} inviati, {falliti} falliti'
            )
        )
