"""
Management command per configurare il tipo documento CU-ZIP (Archivio Certificazioni Uniche)
e i relativi attributi dinamici.

Usage:
    python manage.py setup_cu_zip
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from documenti.models import DocumentiTipo, AttributoDefinizione
from titolario.models import TitolarioVoce


class Command(BaseCommand):
    help = 'Configura tipo documento CU-ZIP (Archivio Certificazioni Uniche) con attributi dinamici'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Setup Archivio Certificazioni Uniche (CU-ZIP) ===\n'))
        
        with transaction.atomic():
            # 1. Verifica/crea tipo documento CU-ZIP
            tipo_cu_zip, created = DocumentiTipo.objects.get_or_create(
                codice='CU-ZIP',
                defaults={
                    'nome': 'Archivio Certificazioni Uniche',
                    'estensioni_permesse': 'zip',
                    'pattern_codice': '{CLI}-CUZIP-{ANNO}-{SEQ:03d}',
                    'nome_file_pattern': 'Archivio_CU_{attr:anno_imposta}_{cliente.codice}.zip',
                    'attivo': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creato tipo documento: {tipo_cu_zip}'))
            else:
                self.stdout.write(self.style.WARNING(f'✓ Tipo documento già esistente: {tipo_cu_zip}'))
            
            # 2. Crea attributi dinamici per CU-ZIP
            attributi_config = [
                {
                    'codice': 'anno_imposta',
                    'nome': 'Anno Imposta',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': True,
                    'help_text': 'Anno fiscale di riferimento delle certificazioni (es. 2024)',
                    'ordine': 1,
                },
                {
                    'codice': 'datore',
                    'nome': 'Datore di Lavoro',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': False,
                    'widget': 'cliente',
                    'help_text': 'Cliente datore di lavoro (FK a Cliente)',
                    'ordine': 2,
                },
                {
                    'codice': 'datore_cf',
                    'nome': 'Codice Fiscale Datore',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Codice Fiscale o Partita IVA del datore di lavoro',
                    'ordine': 3,
                },
                {
                    'codice': 'datore_denominazione',
                    'nome': 'Denominazione Datore',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Ragione sociale del datore di lavoro',
                    'ordine': 4,
                },
                {
                    'codice': 'num_certificazioni',
                    'nome': 'Numero Certificazioni',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': False,
                    'help_text': 'Numero totale di certificazioni contenute nell\'archivio',
                    'ordine': 5,
                },
                {
                    'codice': 'dipendenti_lista',
                    'nome': 'Elenco Dipendenti',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Lista dipendenti (uno per riga, formato: COGNOME NOME)',
                    'ordine': 6,
                },
            ]
            
            for attr_config in attributi_config:
                attr, attr_created = AttributoDefinizione.objects.update_or_create(
                    tipo_documento=tipo_cu_zip,
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
            
            # 3. Verifica voce titolario HR-CU (Certificazioni Uniche)
            voce_cu = TitolarioVoce.objects.filter(codice='HR-CU').first()
            
            if not voce_cu:
                self.stdout.write(
                    self.style.ERROR('⚠ Voce titolario HR-CU non trovata. Eseguire prima "python manage.py setup_cu".')
                )
                return
            
            self.stdout.write(self.style.SUCCESS(f'✓ Voce titolario HR-CU validata: {voce_cu.codice} - {voce_cu.titolo}'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ Setup Archivio Certificazioni Uniche (CU-ZIP) completato con successo!'))
            self.stdout.write(
                '\nNOTA: Gli archivi ZIP CU saranno importati sotto la voce titolario HR-CU come documenti contenitori.'
            )
