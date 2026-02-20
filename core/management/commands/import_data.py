"""
Management command per importare dati con merge intelligente.
Supporta INSERT di nuovi record e UPDATE di record esistenti.
"""
from django.core.management.base import BaseCommand
from django.core import serializers
from django.apps import apps
from django.db import transaction
from django.db.models import Q
import json
import os
from datetime import datetime
from collections import defaultdict


class Command(BaseCommand):
    help = 'Importa dati nel database con merge intelligente (insert + update)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            default='fixtures/sync/export.json',
            help='File di input con dati da importare'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula import senza applicare modifiche'
        )
        parser.add_argument(
            '--full-replace',
            action='store_true',
            help='Elimina tutti i record esistenti prima di importare'
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            default=True,
            help='Crea backup prima di importare (default: True)'
        )

    def handle(self, *args, **options):
        input_file = options['input']
        dry_run = options['dry_run']
        full_replace = options['full_replace']
        do_backup = options['backup']
        
        if not os.path.exists(input_file):
            self.stdout.write(
                self.style.ERROR(f'❌ File non trovato: {input_file}')
            )
            return
        
        self.stdout.write(self.style.SUCCESS('🔍 Inizio import dati...'))
        self.stdout.write(f'📂 Input: {input_file}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  Modalità DRY-RUN: nessuna modifica sarà applicata'))
        
        if full_replace:
            self.stdout.write(self.style.WARNING('⚠️  Modalità FULL-REPLACE: record esistenti saranno eliminati'))
        
        # Leggi dati
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.stdout.write(f'📦 Caricati {len(data)} record dal file')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Errore lettura file: {e}'))
            return
        
        # Statistiche
        stats = {
            'created': defaultdict(int),
            'updated': defaultdict(int),
            'deleted': defaultdict(int),
            'skipped': defaultdict(int),
            'errors': defaultdict(list),
        }
        
        try:
            with transaction.atomic():
                # Fase 1: Full replace se richiesto
                if full_replace:
                    self.stdout.write('\n🗑️  Fase 1: Eliminazione record esistenti...')
                    deleted_stats = self._delete_all_data(dry_run)
                    stats['deleted'] = deleted_stats
                
                # Fase 2: Import con merge
                self.stdout.write('\n📥 Fase 2: Import e merge record...')
                
                # Usa deserializer Django per gestire correttamente le FK
                for deserialized_obj in serializers.deserialize('json', json.dumps(data)):
                    obj = deserialized_obj.object
                    model_name = f"{obj._meta.app_label}.{obj._meta.model_name}"
                    
                    try:
                        # Cerca record esistente
                        try:
                            existing = obj._meta.model.objects.get(pk=obj.pk)
                            
                            # Update record esistente (copia tutti i field tranne pk)
                            if not dry_run:
                                for field in obj._meta.fields:
                                    if not field.primary_key:  # Skip PK
                                        setattr(existing, field.name, getattr(obj, field.name))
                                
                                # Gestisci M2M separatamente
                                existing.save()
                                for m2m_field in obj._meta.many_to_many:
                                    m2m_value = getattr(obj, m2m_field.name).all()
                                    getattr(existing, m2m_field.name).set(m2m_value)
                            
                            stats['updated'][model_name] += 1
                            
                        except obj._meta.model.DoesNotExist:
                            # Crea nuovo record
                            if not dry_run:
                                obj.save()
                                # Gestisci M2M per nuovi oggetti
                                for m2m_field in obj._meta.many_to_many:
                                    m2m_value = deserialized_obj.m2m_data.get(m2m_field.name, [])
                                    getattr(obj, m2m_field.name).set(m2m_value)
                            
                            stats['created'][model_name] += 1
                    
                    except Exception as e:
                        error_msg = f'Record {model_name}#{obj.pk}: {str(e)}'
                        stats['errors'][model_name].append(error_msg)
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ {error_msg}')
                        )
                
                # Rollback se dry-run
                if dry_run:
                    self.stdout.write(self.style.WARNING('\n🔙 Rollback modifiche (dry-run)'))
                    raise Exception("Dry run - rollback")
        
        except Exception as e:
            if not dry_run:
                self.stdout.write(self.style.ERROR(f'\n❌ Errore import: {e}'))
                raise
        
        # Report finale
        self._print_report(stats, dry_run)

    def _delete_all_data(self, dry_run):
        """Elimina tutti i record delle tabelle target"""
        from core.management.commands.export_data import Command as ExportCommand
        
        deleted_stats = defaultdict(int)
        
        # Elimina in ordine inverso per rispettare FK
        for model_path in reversed(ExportCommand.EXPORT_MODELS):
            try:
                app_label, model_name = model_path.split('.')
                Model = apps.get_model(app_label, model_name)
                
                count = Model.objects.count()
                
                if count > 0:
                    if not dry_run:
                        Model.objects.all().delete()
                    
                    deleted_stats[model_path] = count
                    self.stdout.write(f'  🗑️  {model_path}: {count} record eliminati')
            
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Errore eliminazione {model_path}: {e}')
                )
        
        return deleted_stats

    def _print_report(self, stats, dry_run):
        """Stampa report finale"""
        self.stdout.write(self.style.SUCCESS('\n\n' + '='*60))
        
        if dry_run:
            self.stdout.write(self.style.SUCCESS('📊 ANTEPRIMA MODIFICHE (dry-run)'))
        else:
            self.stdout.write(self.style.SUCCESS('✅ IMPORT COMPLETATO'))
        
        self.stdout.write('='*60)
        
        # Record creati
        if stats['created']:
            self.stdout.write(self.style.SUCCESS('\n➕ Record CREATI:'))
            for model, count in stats['created'].items():
                self.stdout.write(f'   • {model}: {count}')
            self.stdout.write(f'   TOTALE: {sum(stats["created"].values())}')
        
        # Record aggiornati
        if stats['updated']:
            self.stdout.write(self.style.SUCCESS('\n🔄 Record AGGIORNATI:'))
            for model, count in stats['updated'].items():
                self.stdout.write(f'   • {model}: {count}')
            self.stdout.write(f'   TOTALE: {sum(stats["updated"].values())}')
        
        # Record eliminati
        if stats['deleted']:
            self.stdout.write(self.style.WARNING('\n🗑️  Record ELIMINATI:'))
            for model, count in stats['deleted'].items():
                self.stdout.write(f'   • {model}: {count}')
            self.stdout.write(f'   TOTALE: {sum(stats["deleted"].values())}')
        
        # Errori
        if stats['errors']:
            self.stdout.write(self.style.ERROR('\n❌ ERRORI:'))
            for model, errors in stats['errors'].items():
                self.stdout.write(f'   {model}: {len(errors)} errori')
                for error in errors[:5]:  # Mostra primi 5
                    self.stdout.write(f'      - {error}')
                if len(errors) > 5:
                    self.stdout.write(f'      ... e altri {len(errors) - 5} errori')
        
        self.stdout.write('\n' + '='*60 + '\n')
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS('💡 Per applicare le modifiche, esegui senza --dry-run')
            )
