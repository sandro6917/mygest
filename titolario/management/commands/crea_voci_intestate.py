"""
Management command per creazione bulk di voci titolario intestate ad anagrafiche.

Uso:
    # Crea voci per tutte le anagrafiche disponibili sotto HR-PERS
    python manage.py crea_voci_intestate HR-PERS
    
    # Crea voci per anagrafiche specifiche
    python manage.py crea_voci_intestate HR-PERS --anagrafiche ROSMAR01 BIAGIO01
    
    # Modalità dry-run (senza salvare)
    python manage.py crea_voci_intestate HR-PERS --dry-run
    
    # Crea anche sotto-voci standard (Buste Paga, Contratti, etc.)
    python manage.py crea_voci_intestate HR-PERS --crea-sottovoci
"""

from __future__ import annotations
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from titolario.models import TitolarioVoce
from anagrafiche.models import Anagrafica


class Command(BaseCommand):
    help = 'Crea voci titolario intestate ad anagrafiche in modalità bulk'

    def add_arguments(self, parser):
        parser.add_argument(
            'voce_parent_codice',
            type=str,
            help='Codice della voce parent (es. HR-PERS)'
        )
        parser.add_argument(
            '--anagrafiche',
            nargs='+',
            type=str,
            help='Codici anagrafiche specifiche (opzionale, default: tutte disponibili)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Modalità dry-run: mostra cosa verrebbe creato senza salvare'
        )
        parser.add_argument(
            '--crea-sottovoci',
            action='store_true',
            help='Crea anche sotto-voci standard (Buste Paga, Contratti, CU, Documenti)'
        )

    def handle(self, *args, **options):
        codice_parent = options['voce_parent_codice']
        codici_anagrafiche = options.get('anagrafiche')
        dry_run = options.get('dry_run', False)
        crea_sottovoci = options.get('crea_sottovoci', False)

        # Trova voce parent
        try:
            voce_parent = TitolarioVoce.objects.get(codice=codice_parent)
        except TitolarioVoce.DoesNotExist:
            raise CommandError(f'Voce titolario "{codice_parent}" non trovata')

        # Verifica che consenta intestazione
        if not voce_parent.consente_intestazione:
            raise CommandError(
                f'La voce "{codice_parent}" non consente intestazione ad anagrafiche'
            )

        # Ottieni anagrafiche disponibili
        if codici_anagrafiche:
            # Anagrafiche specifiche
            anagrafiche = Anagrafica.objects.filter(codice__in=codici_anagrafiche)
            if anagrafiche.count() != len(codici_anagrafiche):
                codici_trovati = set(anagrafiche.values_list('codice', flat=True))
                codici_mancanti = set(codici_anagrafiche) - codici_trovati
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Anagrafiche non trovate: {", ".join(codici_mancanti)}'
                    )
                )
        else:
            # Tutte le anagrafiche disponibili
            anagrafiche = voce_parent.get_anagrafiche_disponibili()

        # Filtra solo con codice valido
        anagrafiche = anagrafiche.exclude(codice__isnull=True).exclude(codice='')

        if not anagrafiche.exists():
            self.stdout.write(
                self.style.WARNING('ℹ️  Nessuna anagrafica disponibile per intestazione.')
            )
            return

        self.stdout.write(f'\n📋 Voce parent: {voce_parent.codice} - {voce_parent.titolo}')
        self.stdout.write(f'👥 Anagrafiche da processare: {anagrafiche.count()}')
        if crea_sottovoci:
            self.stdout.write(f'📁 Sotto-voci standard: SÌ')
        self.stdout.write('')

        totale_create = 0
        totale_gia_esistenti = 0
        totale_sottovoci = 0
        errori = []

        # Template sotto-voci standard
        SOTTO_VOCI_TEMPLATE = [
            ('BP', 'Buste Paga', '{CLI}-{ANA}-BP-{ANNO}-{SEQ:03d}'),
            ('CONTR', 'Contratti', '{CLI}-{ANA}-CONTR-{ANNO}-{SEQ:03d}'),
            ('CU', 'Certificazione Unica', '{CLI}-{ANA}-CU-{ANNO}-{SEQ:03d}'),
            ('DOC', 'Documenti Vari', '{CLI}-{ANA}-DOC-{ANNO}-{SEQ:03d}'),
        ]

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 MODALITÀ DRY-RUN (nessuna modifica sarà salvata)\n'))

        for anagrafica in anagrafiche:
            # Verifica se esiste già (FUORI dalla transazione)
            if TitolarioVoce.objects.filter(parent=voce_parent, anagrafica=anagrafica).exists():
                totale_gia_esistenti += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⏭️  {anagrafica.codice} - {anagrafica.display_name()} (già esistente)'
                    )
                )
                continue

            try:
                with transaction.atomic():
                    # Crea voce intestata
                    if not dry_run:
                        nuova_voce = TitolarioVoce.objects.create(
                            codice=anagrafica.codice,
                            titolo=f"Dossier {anagrafica.display_name()}",
                            parent=voce_parent,
                            anagrafica=anagrafica,
                            pattern_codice='{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}',
                            consente_intestazione=False
                        )
                    else:
                        nuova_voce = None  # dry-run

                    totale_create += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {anagrafica.codice} - Dossier {anagrafica.display_name()}'
                        )
                    )

                    # Crea sotto-voci se richiesto
                    if crea_sottovoci and not dry_run and nuova_voce:
                        for sv_codice, sv_titolo, sv_pattern in SOTTO_VOCI_TEMPLATE:
                            try:
                                TitolarioVoce.objects.create(
                                    codice=sv_codice,
                                    titolo=sv_titolo,
                                    parent=nuova_voce,
                                    pattern_codice=sv_pattern,
                                    consente_intestazione=False
                                )
                                totale_sottovoci += 1
                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f'      ↳ {sv_codice} - {sv_titolo}'
                                    )
                                )
                            except Exception as e:
                                errori.append(f"{anagrafica.display_name()} → {sv_titolo}: {str(e)}")

                    elif crea_sottovoci and dry_run:
                        # In dry-run mostra cosa verrebbe creato
                        for sv_codice, sv_titolo, sv_pattern in SOTTO_VOCI_TEMPLATE:
                            totale_sottovoci += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'      ↳ {sv_codice} - {sv_titolo} (dry-run)'
                                )
                            )
                    
                    # Se dry-run, rollback questa singola transazione
                    if dry_run:
                        transaction.set_rollback(True)

            except Exception as e:
                errori.append(f"{anagrafica.display_name()}: {str(e)}")
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ {anagrafica.codice} - {anagrafica.display_name()}: {str(e)}'
                    )
                )

        # Riepilogo finale
        self.stdout.write('')
        self.stdout.write('─' * 60)
        self.stdout.write(self.style.SUCCESS(f'✓ Voci create: {totale_create}'))
        if crea_sottovoci:
            self.stdout.write(self.style.SUCCESS(f'✓ Sotto-voci create: {totale_sottovoci}'))
        if totale_gia_esistenti > 0:
            self.stdout.write(self.style.WARNING(f'ℹ️  Già esistenti: {totale_gia_esistenti}'))
        if errori:
            self.stdout.write(self.style.ERROR(f'✗ Errori: {len(errori)}'))
            for errore in errori[:10]:  # Max 10 errori mostrati
                self.stdout.write(self.style.ERROR(f'  - {errore}'))

        if dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    '🔍 DRY-RUN completato: nessuna modifica salvata nel database'
                )
            )
