"""
Management command per esportare dati da database.
Supporta export completo o parziale di tabelle specifiche.
"""
from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
from django.db.models import Q
import json
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Esporta dati dal database per sincronizzazione dev/prod'

    # Modelli da esportare (ordine importante per FK)
    EXPORT_MODELS = [
        # Titolario (deve essere primo per FK)
        'titolario.TitolarioVoce',
        
        # Anagrafiche
        'anagrafiche.Anagrafica',
        'anagrafiche.Cliente',
        'anagrafiche.ContattoEmail',
        'anagrafiche.Indirizzo',
        
        # Archivio fisico
        'archivio_fisico.UnitaFisica',
        'archivio_fisico.CollocazioneFisica',
        
        # Documenti
        'documenti.DocumentiTipo',
        'documenti.Documento',
        'documenti.Allegato',
        
        # Fascicoli
        'fascicoli.Fascicolo',
        'fascicoli.FascicoloDocumento',
        
        # Pratiche
        'pratiche.TipoPratica',
        'pratiche.Pratica',
        'pratiche.PraticaNota',
        
        # Scadenze
        'scadenze.TipoScadenza',
        'scadenze.Scadenza',
        'scadenze.ScadenzaAlert',
        
        # Protocollo
        'protocollo.MovimentoProtocollo',
        
        # Operazioni archivio
        'archivio_fisico.OperazioneArchivio',
        'archivio_fisico.RigaOperazioneArchivio',
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='fixtures/sync/export.json',
            help='File di output per i dati esportati'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'xml', 'yaml'],
            help='Formato di export'
        )
        parser.add_argument(
            '--models',
            type=str,
            help='Modelli specifici da esportare (comma-separated, es: anagrafiche.Cliente,pratiche.Pratica)'
        )
        parser.add_argument(
            '--indent',
            type=int,
            default=2,
            help='Indentazione JSON'
        )

    def handle(self, *args, **options):
        output_file = options['output']
        format_type = options['format']
        indent = options['indent']
        
        # Crea directory se non esiste
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Determina quali modelli esportare
        if options['models']:
            models_to_export = options['models'].split(',')
        else:
            models_to_export = self.EXPORT_MODELS
        
        self.stdout.write(self.style.SUCCESS('🔍 Inizio export dati...'))
        self.stdout.write(f'📂 Output: {output_file}')
        
        all_data = []
        stats = {}
        
        for model_path in models_to_export:
            try:
                app_label, model_name = model_path.split('.')
                model = apps.get_model(app_label, model_name)
                
                # Ottieni tutti i record del modello
                queryset = model.objects.all()
                count = queryset.count()
                
                if count > 0:
                    self.stdout.write(f'  📦 {model_path}: {count} record')
                    
                    # Serializza con use_natural_foreign_keys per gestire FK
                    serialized = serializers.serialize(
                        format_type,
                        queryset,
                        use_natural_foreign_keys=True,
                        use_natural_primary_keys=False,
                        indent=indent
                    )
                    
                    # Aggiungi a collezione
                    if format_type == 'json':
                        all_data.extend(json.loads(serialized))
                    
                    stats[model_path] = count
                else:
                    self.stdout.write(f'  ⚪ {model_path}: 0 record (skip)')
                    
            except LookupError:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Modello {model_path} non trovato')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Errore export {model_path}: {e}')
                )
        
        # Scrivi file output
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if format_type == 'json':
                    json.dump(all_data, f, indent=indent, ensure_ascii=False)
                else:
                    f.write(serialized)
            
            # Statistiche finali
            file_size = os.path.getsize(output_file)
            file_size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(self.style.SUCCESS('\n✅ Export completato!'))
            self.stdout.write(f'📊 Totale record: {sum(stats.values())}')
            self.stdout.write(f'📦 Dimensione file: {file_size_mb:.2f} MB')
            self.stdout.write(f'📅 Data export: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            
            # Dettaglio per modello
            self.stdout.write('\n📋 Dettaglio:')
            for model_path, count in stats.items():
                self.stdout.write(f'   • {model_path}: {count}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Errore scrittura file: {e}')
            )
            raise
