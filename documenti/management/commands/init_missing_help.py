"""
Management command per inizializzare automaticamente gli help_data mancanti
per tutti i tipi documento che non hanno ancora un help configurato.

Usage:
    python manage.py init_missing_help
    python manage.py init_missing_help --dry-run
    python manage.py init_missing_help --tipo CED
"""
from __future__ import annotations
from typing import List

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from documenti.models import DocumentiTipo
from documenti.help_builder import HelpDataBuilder


class Command(BaseCommand):
    help = 'Inizializza help_data per tipi documento senza help configurato'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe fatto senza salvare',
        )
        parser.add_argument(
            '--tipo',
            type=str,
            help='Inizializza solo un tipo specifico',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        tipo_codice = options.get('tipo')
        
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*70
        ))
        self.stdout.write(self.style.SUCCESS(
            '  INIZIALIZZAZIONE HELP MANCANTI'
        ))
        self.stdout.write(self.style.SUCCESS(
            '='*70 + '\n'
        ))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                '⚠️  MODALITÀ DRY-RUN - Nessuna modifica verrà salvata\n'
            ))
        
        # Query tipi documento senza help
        query = DocumentiTipo.objects.all()
        
        if tipo_codice:
            query = query.filter(codice=tipo_codice)
        
        # Tipi senza help o con help vuoto
        tipi_senza_help = []
        for tipo in query:
            if not tipo.help_data or len(tipo.help_data) == 0:
                tipi_senza_help.append(tipo)
        
        if not tipi_senza_help:
            self.stdout.write(self.style.SUCCESS(
                '✓ Tutti i tipi documento hanno già un help configurato!\n'
            ))
            return
        
        self.stdout.write(
            f"Trovati {len(tipi_senza_help)} tipi senza help:\n"
        )
        for tipo in tipi_senza_help:
            self.stdout.write(f"  - {tipo.codice}: {tipo.nome}")
        
        self.stdout.write('\n')
        
        # Inizializza help per ogni tipo
        inizializzati = []
        errori = []
        
        for tipo in tipi_senza_help:
            try:
                if not dry_run:
                    self._init_help_for_tipo(tipo)
                
                inizializzati.append(tipo)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ {tipo.codice} - Help inizializzato")
                )
            except Exception as e:
                errori.append((tipo, str(e)))
                self.stdout.write(
                    self.style.ERROR(f"✗ {tipo.codice} - Errore: {e}")
                )
        
        # Riepilogo
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(
            f'  RIEPILOGO'
        ))
        self.stdout.write('='*70 + '\n')
        
        self.stdout.write(f"✓ Inizializzati: {len(inizializzati)}")
        self.stdout.write(f"✗ Errori: {len(errori)}\n")
        
        if errori:
            self.stdout.write(self.style.ERROR('\nErrori dettagliati:'))
            for tipo, err in errori:
                self.stdout.write(f"  - {tipo.codice}: {err}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  DRY-RUN: Nessuna modifica salvata nel database'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                '\n✓ Modifiche salvate nel database'
            ))
        
        self.stdout.write('\n')
    
    def _init_help_for_tipo(self, tipo: DocumentiTipo):
        """
        Inizializza help_data per un tipo documento con:
        - Sezioni tecniche auto-generate
        - Placeholder per sezioni discorsive
        - Stato "da_completare"
        """
        builder = HelpDataBuilder(tipo)
        
        # Genera sezioni tecniche
        help_data = builder.build_all_technical_sections()
        
        # Aggiungi placeholder per sezioni discorsive
        help_data.update({
            '_meta': {
                'stato': 'da_completare',
                'data_creazione': timezone.now().isoformat(),
                'completato': False,
                'visibile_pubblico': False,  # Visibile solo admin
            },
            'descrizione_breve': f'Tipo documento {tipo.nome} - Help da completare',
            'quando_usare': {
                'casi_uso': ['Da definire'],
                'non_usare_per': ['Da definire'],
            },
            'guida_compilazione': {
                'step': [
                    {
                        'numero': 1,
                        'titolo': 'Compilazione base',
                        'descrizione': 'Compila i campi richiesti',
                        'campo': 'generale',
                        'esempio': 'Da definire',
                    }
                ],
            },
            'relazione_fascicoli': {
                'descrizione': 'Da definire',
                'vantaggi_collegamento': ['Da definire'],
                'come_collegare': {},
                'regole_business': {
                    'titolo': 'Regole',
                    'regole': [],
                },
                'best_practices': ['Da definire'],
            },
            'workflow': {
                'stati_possibili': ['Bozza', 'Protocollato', 'Archiviato'],
                'stato_iniziale': 'Bozza',
                'azioni_disponibili': [
                    {
                        'azione': 'Protocolla',
                        'quando': 'Da bozza a protocollato',
                        'effetto': 'Assegna numero protocollo',
                    }
                ],
            },
            'note_speciali': {
                'attenzioni': ['Help in fase di completamento'],
                'suggerimenti': ['Contatta l\'amministratore per maggiori informazioni'],
                'vincoli_business': [],
            },
            'faq': [
                {
                    'domanda': 'Quando sarà disponibile la guida completa?',
                    'risposta': 'La guida è in fase di completamento da parte degli amministratori.',
                }
            ],
            'risorse_correlate': {
                'guide_correlate': [],
                'tipi_documento_correlati': [],
                'link_esterni': [],
            },
        })
        
        # Salva
        with transaction.atomic():
            tipo.help_data = help_data
            tipo.save(update_fields=['help_data'])
