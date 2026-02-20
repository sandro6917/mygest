"""
Management command per aggiornare i codici tributo F24
dal sito dell'Agenzia delle Entrate.

Uso:
    python manage.py aggiorna_codici_tributo [opzioni]
    
Opzioni:
    --dry-run       Simula l'aggiornamento senza modificare il DB
    --force         Forza il download anche se aggiornato di recente
    --export        Esporta anche CSV/JSON
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import sys
import os

# Aggiungi il path degli scripts
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'scripts'))

from parse_codici_tributo_excel import ParserCodiciTributo
from scadenze.models import CodiceTributoF24


class Command(BaseCommand):
    help = 'Aggiorna i codici tributo F24 dal sito dell\'Agenzia delle Entrate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula l\'aggiornamento senza modificare il database',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forza il download anche se aggiornato di recente',
        )
        parser.add_argument(
            '--export',
            action='store_true',
            help='Esporta anche in formato CSV/JSON',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Output dettagliato',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('🔄 AGGIORNAMENTO CODICI TRIBUTO F24'))
        self.stdout.write(self.style.SUCCESS('='*60 + '\n'))

        # Verifica ultimo aggiornamento
        ultimo_aggiornamento = self.get_ultimo_aggiornamento()
        
        if ultimo_aggiornamento and not options['force']:
            giorni = (timezone.now() - ultimo_aggiornamento).days
            if giorni < 7:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Ultimo aggiornamento: {giorni} giorni fa\n'
                        f'   Usa --force per forzare il download'
                    )
                )
                return
        
        # Crea parser locale
        parser = ParserCodiciTributo(verbose=options['verbose'])
        
        # Parse file Excel locali
        try:
            parser.parse_all()
        except Exception as e:
            raise CommandError(f'Errore durante il parsing: {e}')
        
        if not parser.codici:
            self.stdout.write(self.style.ERROR('❌ Nessun codice trovato'))
            self.stdout.write(self.style.WARNING('   Verifica che i file Excel siano in scripts/excel_ade/'))
            return
        
        # Dry run
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN - Nessuna modifica al database'))
            self.stdout.write(f'   Codici che verrebbero importati: {len(parser.codici)}')
            
            # Mostra statistiche
            sezioni = {}
            for codice in parser.codici:
                sezione = codice['sezione']
                sezioni[sezione] = sezioni.get(sezione, 0) + 1
            
            for sezione, count in sorted(sezioni.items()):
                self.stdout.write(f'     - {sezione.upper()}: {count}')
            
            return
        
        # Aggiorna database usando il metodo del parser
        self.stdout.write('\n💾 Aggiornamento database...')
        
        try:
            parser.update_database()
            
            # Risultati
            self.stdout.write(self.style.SUCCESS('\n✅ Aggiornamento completato!'))
            self.stdout.write(f'   📈 Totale nel database: {CodiceTributoF24.objects.count()}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Errore aggiornamento: {e}'))
            if options['verbose']:
                import traceback
                traceback.print_exc()
            raise CommandError(f'Aggiornamento fallito: {e}')
        
        # Export
        if options['export']:
            self.stdout.write('\n📤 Export files...')
            parser.export_csv()
            parser.export_json()
        
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Operazione completata!'))

    def get_ultimo_aggiornamento(self):
        """Restituisce la data dell'ultimo aggiornamento."""
        ultimo_codice = CodiceTributoF24.objects.order_by('-data_modifica').first()
        if ultimo_codice:
            return ultimo_codice.data_modifica
        return None
