"""
Management command per configurare l'help_data di un tipo documento
tramite wizard interattivo.

Usage:
    python manage.py configure_help_wizard [--tipo CODICE]
    python manage.py configure_help_wizard --tipo CED
"""
from __future__ import annotations
import json
from typing import Dict, List, Any, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from documenti.models import DocumentiTipo
from documenti.help_builder import HelpDataBuilder


class Command(BaseCommand):
    help = 'Wizard interattivo per configurare help_data tipo documento'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tipo',
            type=str,
            help='Codice tipo documento da configurare'
        )
        parser.add_argument(
            '--rebuild-technical',
            action='store_true',
            help='Rigenera solo le sezioni tecniche automatiche'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*70
        ))
        self.stdout.write(self.style.SUCCESS(
            '  WIZARD CONFIGURAZIONE HELP TIPO DOCUMENTO'
        ))
        self.stdout.write(self.style.SUCCESS(
            '='*70 + '\n'
        ))
        
        # Seleziona tipo documento
        if options['tipo']:
            try:
                tipo = DocumentiTipo.objects.get(codice=options['tipo'])
            except DocumentiTipo.DoesNotExist:
                raise CommandError(f"Tipo documento '{options['tipo']}' non trovato")
        else:
            tipo = self._select_tipo_documento()
        
        self.stdout.write(
            f"\n{self.style.WARNING('Tipo selezionato:')} "
            f"{self.style.SUCCESS(tipo.codice + ' - ' + tipo.nome)}\n"
        )
        
        # Modalità rebuild-technical
        if options['rebuild_technical']:
            self._rebuild_technical_only(tipo)
            return
        
        # Wizard completo
        self._run_wizard(tipo)
    
    def _select_tipo_documento(self) -> DocumentiTipo:
        """Permette di selezionare un tipo documento."""
        tipi = DocumentiTipo.objects.all().order_by('codice')
        
        self.stdout.write(self.style.WARNING('Tipi documento disponibili:\n'))
        for i, tipo in enumerate(tipi, 1):
            has_help = '✓' if tipo.help_data else '✗'
            self.stdout.write(f"  {i}. [{has_help}] {tipo.codice} - {tipo.nome}")
        
        while True:
            scelta = input(f"\nSeleziona numero (1-{tipi.count()}): ").strip()
            try:
                idx = int(scelta) - 1
                if 0 <= idx < tipi.count():
                    return tipi[idx]
            except ValueError:
                pass
            self.stdout.write(self.style.ERROR("Scelta non valida!"))
    
    def _rebuild_technical_only(self, tipo: DocumentiTipo):
        """Rigenera solo le sezioni tecniche."""
        self.stdout.write(self.style.WARNING(
            '\n=== RIGENERAZIONE SEZIONI TECNICHE ===\n'
        ))
        
        builder = HelpDataBuilder(tipo)
        tipo.help_data = builder.merge_with_existing(tipo.help_data)
        tipo.save()
        
        self.stdout.write(self.style.SUCCESS(
            '\n✓ Sezioni tecniche rigenerate con successo!\n'
        ))
        self.stdout.write('Sezioni aggiornate:')
        self.stdout.write('  - attributi_dinamici')
        self.stdout.write('  - pattern_codice')
        self.stdout.write('  - archiviazione')
        self.stdout.write('  - campi_obbligatori\n')
    
    def _run_wizard(self, tipo: DocumentiTipo):
        """Esegue il wizard completo."""
        help_data = tipo.help_data or {}
        
        # Banner informativo
        self.stdout.write(self.style.WARNING(
            '\nLe sezioni TECNICHE verranno generate automaticamente.\n'
            'Compilerai solo le sezioni DISCORSIVE.\n'
        ))
        
        # Sezioni discorsive da compilare
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  SEZIONE 1: DESCRIZIONE BREVE'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        help_data['descrizione_breve'] = self._input_descrizione_breve(
            help_data.get('descrizione_breve', '')
        )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  SEZIONE 2: QUANDO USARE'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        help_data['quando_usare'] = self._input_quando_usare(
            help_data.get('quando_usare', {})
        )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  SEZIONE 3: GUIDA COMPILAZIONE'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        help_data['guida_compilazione'] = self._input_guida_compilazione(
            help_data.get('guida_compilazione', {})
        )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  SEZIONE 4: RELAZIONE FASCICOLI'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        help_data['relazione_fascicoli'] = self._input_relazione_fascicoli(
            help_data.get('relazione_fascicoli', {})
        )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  SEZIONE 5: WORKFLOW'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        help_data['workflow'] = self._input_workflow(
            help_data.get('workflow', {})
        )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  SEZIONE 6: NOTE SPECIALI'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        help_data['note_speciali'] = self._input_note_speciali(
            help_data.get('note_speciali', {})
        )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  SEZIONE 7: FAQ'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        help_data['faq'] = self._input_faq(
            help_data.get('faq', [])
        )
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('  SEZIONE 8: RISORSE CORRELATE'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        help_data['risorse_correlate'] = self._input_risorse_correlate(
            help_data.get('risorse_correlate', {})
        )
        
        # Genera sezioni tecniche automaticamente
        self.stdout.write(self.style.WARNING(
            '\n\n🤖 Generazione automatica sezioni tecniche...\n'
        ))
        builder = HelpDataBuilder(tipo)
        help_data.update(builder.build_all_technical_sections())
        
        # Salva
        with transaction.atomic():
            tipo.help_data = help_data
            tipo.save()
        
        self.stdout.write(self.style.SUCCESS(
            '\n' + '='*70
        ))
        self.stdout.write(self.style.SUCCESS(
            '  ✓ CONFIGURAZIONE COMPLETATA CON SUCCESSO!'
        ))
        self.stdout.write(self.style.SUCCESS(
            '='*70 + '\n'
        ))
        
        # Riepilogo
        self._print_summary(tipo)
    
    # ========================================================================
    # INPUT METHODS per ogni sezione
    # ========================================================================
    
    def _input_descrizione_breve(self, current: str) -> str:
        """Input descrizione breve."""
        if current:
            self.stdout.write(f"Attuale: {self.style.WARNING(current)}\n")
        
        self.stdout.write("Inserisci una descrizione breve del tipo documento")
        self.stdout.write("(max 2-3 righe, panoramica generale)\n")
        
        lines = []
        self.stdout.write("Scrivi la descrizione (riga vuota per terminare):")
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        
        return ' '.join(lines) if lines else current
    
    def _input_quando_usare(self, current: Dict) -> Dict:
        """Input casi d'uso."""
        risultato = {
            'casi_uso': [],
            'non_usare_per': [],
        }
        
        # Casi d'uso
        self.stdout.write("\n📌 Quando usare questo tipo documento?")
        self.stdout.write("Elenca i casi d'uso appropriati (vuoto per finire):\n")
        
        i = 1
        while True:
            caso = input(f"  {i}. ").strip()
            if not caso:
                break
            risultato['casi_uso'].append(caso)
            i += 1
        
        if not risultato['casi_uso'] and current.get('casi_uso'):
            risultato['casi_uso'] = current['casi_uso']
        
        # Non usare per
        self.stdout.write("\n🚫 Quando NON usare (situazioni da evitare):")
        self.stdout.write("(vuoto per finire)\n")
        
        i = 1
        while True:
            caso = input(f"  {i}. ").strip()
            if not caso:
                break
            risultato['non_usare_per'].append(caso)
            i += 1
        
        if not risultato['non_usare_per'] and current.get('non_usare_per'):
            risultato['non_usare_per'] = current['non_usare_per']
        
        return risultato
    
    def _input_guida_compilazione(self, current: Dict) -> Dict:
        """Input guida compilazione step-by-step."""
        self.stdout.write("\n📝 Guida compilazione passo-passo")
        self.stdout.write("Vuoi creare una guida dettagliata? (s/n): ")
        
        if input().lower() != 's':
            return current or {'step': []}
        
        step = []
        self.stdout.write("\nInserisci gli step di compilazione:\n")
        
        i = 1
        while True:
            self.stdout.write(f"\n--- STEP {i} ---")
            
            titolo = input("Titolo step (vuoto per finire): ").strip()
            if not titolo:
                break
            
            descrizione = input("Descrizione: ").strip()
            campo = input("Campo interessato: ").strip()
            esempio = input("Esempio: ").strip()
            attenzione = input("Attenzione (opzionale): ").strip()
            
            step.append({
                'numero': i,
                'titolo': titolo,
                'descrizione': descrizione,
                'campo': campo,
                'esempio': esempio,
                'attenzione': attenzione if attenzione else None,
            })
            i += 1
        
        return {'step': step} if step else current
    
    def _input_relazione_fascicoli(self, current: Dict) -> Dict:
        """Input relazione con fascicoli."""
        self.stdout.write("\n📁 Relazione con i fascicoli")
        
        descrizione = input(
            "Descrizione relazione (come si collegano i fascicoli): "
        ).strip()
        
        if not descrizione:
            return current or {}
        
        # Best practices
        self.stdout.write("\n💡 Best practices (vuoto per finire):")
        best_practices = []
        i = 1
        while True:
            bp = input(f"  {i}. ").strip()
            if not bp:
                break
            best_practices.append(bp)
            i += 1
        
        return {
            'descrizione': descrizione,
            'best_practices': best_practices,
            'vantaggi_collegamento': current.get('vantaggi_collegamento', []),
            'come_collegare': current.get('come_collegare', {}),
            'regole_business': current.get('regole_business', {}),
        }
    
    def _input_workflow(self, current: Dict) -> Dict:
        """Input workflow stati e azioni."""
        self.stdout.write("\n🔄 Workflow documento")
        
        # Stati
        self.stdout.write("\nStati possibili (vuoto per finire):")
        stati = []
        i = 1
        while True:
            stato = input(f"  {i}. ").strip()
            if not stato:
                break
            stati.append(stato)
            i += 1
        
        if not stati:
            stati = current.get('stati_possibili', ['Bozza', 'Protocollato', 'Archiviato'])
        
        # Stato iniziale
        stato_iniziale = input(f"\nStato iniziale (default: {stati[0]}): ").strip()
        if not stato_iniziale:
            stato_iniziale = stati[0]
        
        return {
            'stati_possibili': stati,
            'stato_iniziale': stato_iniziale,
            'azioni_disponibili': current.get('azioni_disponibili', []),
        }
    
    def _input_note_speciali(self, current: Dict) -> Dict:
        """Input note speciali."""
        risultato = {
            'attenzioni': [],
            'suggerimenti': [],
            'vincoli_business': [],
        }
        
        # Attenzioni
        self.stdout.write("\n⚠️  Attenzioni importanti (vuoto per finire):")
        i = 1
        while True:
            att = input(f"  {i}. ").strip()
            if not att:
                break
            risultato['attenzioni'].append(att)
            i += 1
        
        # Suggerimenti
        self.stdout.write("\n💡 Suggerimenti operativi (vuoto per finire):")
        i = 1
        while True:
            sug = input(f"  {i}. ").strip()
            if not sug:
                break
            risultato['suggerimenti'].append(sug)
            i += 1
        
        # Vincoli business
        self.stdout.write("\n🔒 Vincoli di business (vuoto per finire):")
        i = 1
        while True:
            vinc = input(f"  {i}. ").strip()
            if not vinc:
                break
            risultato['vincoli_business'].append(vinc)
            i += 1
        
        # Mantieni esistenti se vuoti
        for key in risultato:
            if not risultato[key] and current.get(key):
                risultato[key] = current[key]
        
        return risultato
    
    def _input_faq(self, current: List) -> List:
        """Input FAQ."""
        self.stdout.write("\n❓ FAQ - Domande Frequenti")
        self.stdout.write("Vuoi aggiungere FAQ? (s/n): ")
        
        if input().lower() != 's':
            return current or []
        
        faq = []
        i = 1
        while True:
            self.stdout.write(f"\n--- FAQ {i} ---")
            domanda = input("Domanda (vuoto per finire): ").strip()
            if not domanda:
                break
            
            risposta = input("Risposta: ").strip()
            
            faq.append({
                'domanda': domanda,
                'risposta': risposta,
            })
            i += 1
        
        return faq if faq else current
    
    def _input_risorse_correlate(self, current: Dict) -> Dict:
        """Input risorse correlate."""
        self.stdout.write("\n🔗 Risorse correlate")
        self.stdout.write("Vuoi aggiungere risorse? (s/n): ")
        
        if input().lower() != 's':
            return current or {
                'guide_correlate': [],
                'tipi_documento_correlati': [],
            }
        
        return {
            'guide_correlate': current.get('guide_correlate', []),
            'tipi_documento_correlati': current.get('tipi_documento_correlati', []),
            'link_esterni': current.get('link_esterni', []),
        }
    
    def _print_summary(self, tipo: DocumentiTipo):
        """Stampa riepilogo configurazione."""
        self.stdout.write("\n📊 RIEPILOGO CONFIGURAZIONE\n")
        self.stdout.write(f"Tipo: {tipo.codice} - {tipo.nome}")
        
        if tipo.help_data:
            self.stdout.write(f"\nSezioni configurate:")
            for key in sorted(tipo.help_data.keys()):
                icon = '🤖' if key in [
                    'attributi_dinamici',
                    'pattern_codice',
                    'archiviazione',
                    'campi_obbligatori'
                ] else '📝'
                self.stdout.write(f"  {icon} {key}")
        
        self.stdout.write(f"\n\nPer visualizzare l'help:")
        self.stdout.write(f"  Frontend: /help/documenti/{tipo.codice}")
        self.stdout.write(f"  Admin: /admin/documenti/documentitipo/{tipo.pk}/change/")
        
        self.stdout.write(f"\n\nPer rigenerare solo le sezioni tecniche:")
        self.stdout.write(
            f"  python manage.py configure_help_wizard "
            f"--tipo {tipo.codice} --rebuild-technical\n"
        )
