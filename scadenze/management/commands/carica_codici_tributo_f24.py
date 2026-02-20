"""
Management command per caricare o aggiornare i codici tributo F24.

Uso:
    python manage.py carica_codici_tributo_f24 <file.csv|file.json>
    
Il file CSV deve avere le colonne:
    codice,sezione,descrizione,causale,periodicita,note,attivo,data_inizio_validita,data_fine_validita

Il file JSON deve avere la struttura:
    [
        {
            "codice": "1001",
            "sezione": "erario",
            "descrizione": "...",
            "causale": "...",
            "periodicita": "mensile",
            "note": "...",
            "attivo": true,
            "data_inizio_validita": "2020-01-01",
            "data_fine_validita": null
        },
        ...
    ]
"""

import csv
import json
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from scadenze.models import CodiceTributoF24


class Command(BaseCommand):
    help = "Carica o aggiorna i codici tributo F24 da file CSV o JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=str,
            help='Percorso del file CSV o JSON con i codici tributo'
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Aggiorna i codici esistenti invece di saltarli'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina tutti i codici esistenti prima di caricare i nuovi'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file'])
        
        if not file_path.exists():
            raise CommandError(f"File non trovato: {file_path}")
        
        # Determina il formato dal tipo di file
        if file_path.suffix.lower() == '.csv':
            codici = self._load_from_csv(file_path)
        elif file_path.suffix.lower() == '.json':
            codici = self._load_from_json(file_path)
        else:
            raise CommandError("Formato file non supportato. Usa .csv o .json")
        
        # Elimina i codici esistenti se richiesto
        if options['clear']:
            deleted_count = CodiceTributoF24.objects.all().count()
            CodiceTributoF24.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Eliminati {deleted_count} codici tributo esistenti")
            )
        
        # Carica i codici
        created = 0
        updated = 0
        skipped = 0
        errors = 0
        
        with transaction.atomic():
            for codice_data in codici:
                try:
                    codice = codice_data['codice']
                    
                    # Converti le date da stringa a oggetto date
                    if codice_data.get('data_inizio_validita'):
                        codice_data['data_inizio_validita'] = datetime.strptime(
                            codice_data['data_inizio_validita'], '%Y-%m-%d'
                        ).date()
                    if codice_data.get('data_fine_validita'):
                        codice_data['data_fine_validita'] = datetime.strptime(
                            codice_data['data_fine_validita'], '%Y-%m-%d'
                        ).date()
                    
                    # Cerca se esiste già
                    obj, is_created = CodiceTributoF24.objects.get_or_create(
                        codice=codice,
                        defaults=codice_data
                    )
                    
                    if is_created:
                        created += 1
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Creato: {codice} - {codice_data['descrizione'][:50]}")
                        )
                    elif options['update']:
                        # Aggiorna i campi
                        for field, value in codice_data.items():
                            setattr(obj, field, value)
                        obj.save()
                        updated += 1
                        self.stdout.write(
                            self.style.WARNING(f"↻ Aggiornato: {codice} - {codice_data['descrizione'][:50]}")
                        )
                    else:
                        skipped += 1
                        self.stdout.write(
                            f"⊘ Saltato (già esistente): {codice}"
                        )
                
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ Errore con codice {codice_data.get('codice', '???')}: {e}")
                    )
        
        # Riepilogo
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"Codici creati: {created}"))
        if updated > 0:
            self.stdout.write(self.style.WARNING(f"Codici aggiornati: {updated}"))
        if skipped > 0:
            self.stdout.write(f"Codici saltati: {skipped}")
        if errors > 0:
            self.stdout.write(self.style.ERROR(f"Errori: {errors}"))
        self.stdout.write("="*60)

    def _load_from_csv(self, file_path: Path) -> list[dict]:
        """Carica i codici tributo da un file CSV."""
        codici = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Converti il campo attivo da stringa a booleano
                row['attivo'] = row.get('attivo', 'true').lower() in ('true', '1', 'si', 'yes')
                
                # Gestisci valori vuoti per le date
                if not row.get('data_inizio_validita'):
                    row['data_inizio_validita'] = None
                if not row.get('data_fine_validita'):
                    row['data_fine_validita'] = None
                
                codici.append(row)
        
        self.stdout.write(f"Caricati {len(codici)} codici dal CSV")
        return codici

    def _load_from_json(self, file_path: Path) -> list[dict]:
        """Carica i codici tributo da un file JSON."""
        with open(file_path, 'r', encoding='utf-8') as f:
            codici = json.load(f)
        
        self.stdout.write(f"Caricati {len(codici)} codici dal JSON")
        return codici
