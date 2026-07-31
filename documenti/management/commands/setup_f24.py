"""
Management command per configurare il tipo documento F24 (Modelli F24)
e la voce di titolario F24 sotto AF-TAX (Imposte e tasse).

Idempotente: usa get_or_create per non sovrascrivere configurazioni
già personalizzate (es. scelte extra aggiunte da un amministratore).

Usage:
    python manage.py setup_f24
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from documenti.models import DocumentiTipo, AttributoDefinizione
from titolario.models import TitolarioVoce


class Command(BaseCommand):
    help = 'Configura tipo documento F24 con attributi e voce titolario F24 (sotto AF-TAX)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Setup F24 ===\n'))

        with transaction.atomic():
            # 1. Verifica/crea tipo documento F24
            tipo_f24, created = DocumentiTipo.objects.get_or_create(
                codice='F24',
                defaults={
                    'nome': 'Modello di versamento F24',
                    'estensioni_permesse': 'pdf',
                    'pattern_codice': '{CLI}_{TIPO}_{DATA}_{SEQ:03d}',
                    'nome_file_pattern': 'F24_{attr:data_scadenza:%Y%m%d}_{attr:Tipo}_{cliente.anagrafica.codice}',
                    'attivo': True,
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creato tipo documento: {tipo_f24}'))
            else:
                self.stdout.write(self.style.WARNING(f'✓ Tipo documento già esistente: {tipo_f24}'))

            # 2. Verifica/crea attributi dinamici per F24 (non sovrascrive quelli esistenti)
            attributi_config = [
                {
                    'codice': 'data_scadenza',
                    'nome': 'Data Scadenza',
                    'tipo_dato': AttributoDefinizione.TipoDato.DATE,
                    'required': False,
                    'help_text': 'Data di scadenza della rata F24 (non presente in tutti i modelli)',
                    'ordine': 1,
                },
                {
                    'codice': 'Tipo_pagamento',
                    'nome': 'Tipo pagamento',
                    'tipo_dato': AttributoDefinizione.TipoDato.CHOICE,
                    'required': False,
                    'choices': 'Telematico, Cartaceo, Homebanking',
                    'ordine': 2,
                },
                {
                    'codice': 'data_pagamento',
                    'nome': 'Data Pagamento',
                    'tipo_dato': AttributoDefinizione.TipoDato.DATE,
                    'required': False,
                    'ordine': 3,
                },
                {
                    'codice': 'Tipo',
                    'nome': 'Tipo',
                    'tipo_dato': AttributoDefinizione.TipoDato.CHOICE,
                    'required': False,
                    'choices': 'Modello, Ricevuta, Quietanza, Scarto',
                    'help_text': "Valorizzato a 'Modello' dall'importazione automatica",
                    'ordine': 4,
                },
            ]

            for attr_config in attributi_config:
                attr, attr_created = AttributoDefinizione.objects.get_or_create(
                    tipo_documento=tipo_f24,
                    codice=attr_config['codice'],
                    defaults={
                        'nome': attr_config['nome'],
                        'tipo_dato': attr_config['tipo_dato'],
                        'required': attr_config['required'],
                        'choices': attr_config.get('choices', ''),
                        'help_text': attr_config.get('help_text', ''),
                        'ordine': attr_config.get('ordine', 0),
                    }
                )

                if attr_created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Creato attributo: {attr.codice} ({attr.nome})'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ✓ Attributo già esistente: {attr.codice} ({attr.nome})'))

            # 3. Verifica/crea voce titolario F24 sotto AF > AF-TAX (Imposte e tasse)
            voce_aftax = TitolarioVoce.objects.filter(codice='AF-TAX').first()
            if voce_aftax:
                voce_f24, voce_created = TitolarioVoce.objects.get_or_create(
                    codice='F24',
                    parent=voce_aftax,
                    defaults={
                        'titolo': 'Versamenti F24',
                        'pattern_codice': '{CLI}-F24-{ANNO}-{SEQ:03d}',
                    }
                )

                if voce_created:
                    self.stdout.write(self.style.SUCCESS(f'\n✓ Creata voce titolario: {voce_aftax.codice}/{voce_f24.codice} - {voce_f24.titolo}'))
                else:
                    self.stdout.write(self.style.WARNING(f'\n✓ Voce titolario già esistente: {voce_aftax.codice}/{voce_f24.codice} - {voce_f24.titolo}'))
            else:
                self.stdout.write(self.style.WARNING(
                    '\n⚠ Voce titolario AF-TAX non trovata: la voce F24 non è stata creata, '
                    'sarà usata la voce di default (Varie) finché non viene configurata manualmente.'
                ))

        self.stdout.write(self.style.SUCCESS('\n=== Setup completato con successo! ==='))
