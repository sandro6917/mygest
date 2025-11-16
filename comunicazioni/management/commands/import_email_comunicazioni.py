from django.core.management.base import BaseCommand

from comunicazioni.tasks import sincronizza_tutte_mailbox


class Command(BaseCommand):
    help = "Importa le comunicazioni in entrata dalle caselle IMAP configurate."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Numero massimo di messaggi da importare per casella (default: tutti).",
        )

    def handle(self, *args, **options):
        limite = options.get("limit")
        count = sincronizza_tutte_mailbox(limite=limite)
        if count == 0:
            self.stdout.write(self.style.WARNING("Nessuna nuova comunicazione importata."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Importate {count} comunicazioni."))
