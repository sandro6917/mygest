"""
Management command per configurare gli attributi del tipo documento BPAG (Buste Paga)
e la voce di titolario PAG - Paghe.

Usage:
    python manage.py setup_cedolini
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from documenti.models import DocumentiTipo, AttributoDefinizione
from titolario.models import TitolarioVoce


class Command(BaseCommand):
    help = 'Configura tipo documento BPAG con attributi e voce titolario PAG'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Setup Cedolini ===\n'))
        
        with transaction.atomic():
            # 1. Verifica/crea tipo documento BPAG
            tipo_bpag, created = DocumentiTipo.objects.get_or_create(
                codice='BPAG',
                defaults={
                    'nome': 'Buste paga',
                    'estensioni_permesse': 'pdf',
                    'pattern_codice': '{CLI}-BPAG-{ANNO}-{SEQ:03d}',
                    'nome_file_pattern': '{attr:dipendente.codice}_{tipo.codice}_{attr:mese_riferimento:02d}_{attr:anno_riferimento}.pdf',
                    'attivo': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creato tipo documento: {tipo_bpag}'))
            else:
                self.stdout.write(self.style.WARNING(f'✓ Tipo documento già esistente: {tipo_bpag}'))
            
            # 2. Crea attributi dinamici per BPAG
            attributi_config = [
                {
                    'codice': 'tipo',
                    'nome': 'Tipo',
                    'tipo_dato': AttributoDefinizione.TipoDato.CHOICE,
                    'required': True,
                    'choices': 'Libro Unico|Libro Unico',
                    'help_text': 'Tipo di libro (es. Libro Unico)',
                    'ordine': 1,
                },
                {
                    'codice': 'anno_riferimento',
                    'nome': 'Anno Riferimento',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': True,
                    'help_text': 'Anno di riferimento del cedolino (es. 2025)',
                    'ordine': 2,
                },
                {
                    'codice': 'mese_riferimento',
                    'nome': 'Mese Riferimento',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': True,
                    'help_text': 'Mese di riferimento (1-12)',
                    'ordine': 3,
                },
                {
                    'codice': 'mensilita',
                    'nome': 'Mensilità',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': True,
                    'help_text': 'Mensilità (1-12 ordinaria, 13 tredicesima, 14 quattordicesima)',
                    'ordine': 4,
                },
                {
                    'codice': 'dipendente',
                    'nome': 'Dipendente',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': True,
                    'widget': 'anagrafica',
                    'help_text': 'Anagrafica del dipendente collegata al cedolino',
                    'ordine': 5,
                },
            ]
            
            for attr_config in attributi_config:
                attr, attr_created = AttributoDefinizione.objects.update_or_create(
                    tipo_documento=tipo_bpag,
                    codice=attr_config['codice'],
                    defaults={
                        'nome': attr_config['nome'],
                        'tipo_dato': attr_config['tipo_dato'],
                        'required': attr_config['required'],
                        'choices': attr_config.get('choices', ''),
                        'widget': attr_config.get('widget', ''),
                        'help_text': attr_config.get('help_text', ''),
                        'ordine': attr_config.get('ordine', 0),
                    }
                )
                
                if attr_created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Creato attributo: {attr.codice} ({attr.nome})'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ✓ Aggiornato attributo: {attr.codice} ({attr.nome})'))
            
            # 3. Verifica/crea voce titolario PAG - Paghe
            voce_pag, voce_created = TitolarioVoce.objects.get_or_create(
                codice='PAG',
                parent=None,  # Voce di primo livello
                defaults={
                    'titolo': 'Paghe',
                    'pattern_codice': '{CLI}-PAG-{ANNO}-{SEQ:03d}',
                }
            )
            
            if voce_created:
                self.stdout.write(self.style.SUCCESS(f'\n✓ Creata voce titolario: {voce_pag.codice} - {voce_pag.titolo}'))
            else:
                self.stdout.write(self.style.WARNING(f'\n✓ Voce titolario già esistente: {voce_pag.codice} - {voce_pag.titolo}'))
        
        self.stdout.write(self.style.SUCCESS('\n=== Setup completato con successo! ==='))
