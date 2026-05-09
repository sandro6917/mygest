"""
Management command per configurare il tipo documento CU (Certificazioni Uniche)
e la voce di titolario relativa.

Usage:
    python manage.py setup_cu
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from documenti.models import DocumentiTipo, AttributoDefinizione
from titolario.models import TitolarioVoce


class Command(BaseCommand):
    help = 'Configura tipo documento CU (Certificazioni Uniche) con attributi e voce titolario'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Setup Certificazioni Uniche ===\n'))
        
        with transaction.atomic():
            # 1. Verifica/crea tipo documento CU
            tipo_cu, created = DocumentiTipo.objects.get_or_create(
                codice='CU',
                defaults={
                    'nome': 'Certificazione Unica',
                    'estensioni_permesse': 'pdf',
                    'pattern_codice': '{CLI}-CU-{ANNO}-{SEQ:03d}',
                    'nome_file_pattern': '{attr:dipendente.codice}_CU_{attr:anno_riferimento}.pdf',
                    'attivo': True,
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creato tipo documento: {tipo_cu}'))
            else:
                self.stdout.write(self.style.WARNING(f'✓ Tipo documento già esistente: {tipo_cu}'))
            
            # 2. Crea attributi dinamici per CU
            attributi_config = [
                {
                    'codice': 'anno_riferimento',
                    'nome': 'Anno Riferimento',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': True,
                    'help_text': 'Anno fiscale di riferimento (es. 2024)',
                    'ordine': 1,
                },
                {
                    'codice': 'dipendente',
                    'nome': 'Dipendente',
                    'tipo_dato': AttributoDefinizione.TipoDato.INT,
                    'required': True,
                    'widget': 'anagrafica',
                    'help_text': 'Anagrafica del percipiente (dipendente)',
                    'ordine': 2,
                },
                {
                    'codice': 'tipo_certificazione',
                    'nome': 'Tipo Certificazione',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Tipologia di certificazione (es. Ordinaria, Soggetto estero)',
                    'ordine': 3,
                },
                {
                    'codice': 'redditi_lavoro_dipendente',
                    'nome': 'Redditi Lavoro Dipendente',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Punto 1 - Redditi da lavoro dipendente (formato: 1.234,56)',
                    'ordine': 4,
                },
                {
                    'codice': 'ritenute_irpef',
                    'nome': 'Ritenute IRPEF',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Punto 4 - Ritenute IRPEF (formato: 1.234,56)',
                    'ordine': 5,
                },
                {
                    'codice': 'addizionale_regionale',
                    'nome': 'Addizionale Regionale',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Punto 5 - Addizionale regionale IRPEF (formato: 1.234,56)',
                    'ordine': 6,
                },
                {
                    'codice': 'addizionale_comunale',
                    'nome': 'Addizionale Comunale',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Punto 6 - Addizionale comunale IRPEF (formato: 1.234,56)',
                    'ordine': 7,
                },
                {
                    'codice': 'contributi_previdenziali',
                    'nome': 'Contributi Previdenziali',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Contributi previdenziali a carico del dipendente (formato: 1.234,56)',
                    'ordine': 8,
                },
                {
                    'codice': 'bonus_renzi',
                    'nome': 'Bonus/Trattamento Integrativo',
                    'tipo_dato': AttributoDefinizione.TipoDato.STRING,
                    'required': False,
                    'help_text': 'Eventuale bonus Renzi o trattamento integrativo (formato: 1.234,56)',
                    'ordine': 9,
                },
            ]
            
            for attr_config in attributi_config:
                attr, attr_created = AttributoDefinizione.objects.update_or_create(
                    tipo_documento=tipo_cu,
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
            
            # 3. Verifica/crea voce titolario HR-CU (Certificazioni Uniche)
            # Parent: HR - Human Resources
            try:
                voce_hr = TitolarioVoce.objects.get(codice='HR')
            except TitolarioVoce.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR('⚠ Voce titolario HR non trovata. Crearla manualmente o eseguire setup titolario.')
                )
                return
            
            voce_cu, voce_created = TitolarioVoce.objects.get_or_create(
                codice='HR-CU',
                defaults={
                    'titolo': 'Certificazioni Uniche',
                    'parent': voce_hr,
                    'pattern_codice': '{CLI}-CU-{ANNO}-{SEQ:03d}',
                    'consente_intestazione': True,
                }
            )
            
            if voce_created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creata voce titolario: {voce_cu.codice} - {voce_cu.titolo}'))
            else:
                self.stdout.write(self.style.WARNING(f'✓ Voce titolario già esistente: {voce_cu.codice}'))
            
            self.stdout.write(self.style.SUCCESS('\n✅ Setup Certificazioni Uniche completato con successo!'))
            self.stdout.write(
                '\nNOTA: Le Certificazioni Uniche saranno importate sotto la voce titolario HR-CU, '
                'con possibilità di intestazione al singolo dipendente (voci HR-PERS/{codice_dipendente}).'
            )
