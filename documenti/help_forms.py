"""
Form custom per l'editing user-friendly del help_data in Django Admin.
"""
from __future__ import annotations
from typing import Dict, Any

from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import DocumentiTipo
from .help_builder import HelpDataBuilder


class HelpDataAdminForm(forms.ModelForm):
    """
    Form customizzato per DocumentiTipo che gestisce help_data
    in modo user-friendly con campi separati.
    """
    
    # ========================================================================
    # SEZIONI DISCORSIVE (user input)
    # ========================================================================
    
    # Sezione 1: Descrizione Breve
    help_descrizione_breve = forms.CharField(
        label="Descrizione Breve",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'cols': 80,
            'placeholder': 'Descrizione sintetica del tipo documento (2-3 righe)'
        }),
        required=False,
        help_text="Panoramica generale del tipo documento"
    )
    
    # Sezione 2: Quando Usare - Casi d'uso
    help_quando_usare_casi = forms.CharField(
        label="Quando Usare - Casi d'uso",
        widget=forms.Textarea(attrs={
            'rows': 5,
            'cols': 80,
            'placeholder': 'Un caso d\'uso per riga\n- Caso 1\n- Caso 2\n- Caso 3'
        }),
        required=False,
        help_text="Elenca i casi d'uso appropriati (uno per riga, opzionalmente con - iniziale)"
    )
    
    help_quando_usare_non_usare = forms.CharField(
        label="Quando NON Usare",
        widget=forms.Textarea(attrs={
            'rows': 5,
            'cols': 80,
            'placeholder': 'Una situazione da evitare per riga\n- Situazione 1\n- Situazione 2'
        }),
        required=False,
        help_text="Situazioni in cui NON si deve usare questo tipo (uno per riga)"
    )
    
    # Sezione 3: Relazione Fascicoli
    help_relazione_fascicoli_descrizione = forms.CharField(
        label="Relazione Fascicoli - Descrizione",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'cols': 80,
            'placeholder': 'Come si collegano i documenti di questo tipo ai fascicoli'
        }),
        required=False,
        help_text="Spiega la relazione con i fascicoli"
    )
    
    help_relazione_fascicoli_best_practices = forms.CharField(
        label="Best Practices Fascicoli",
        widget=forms.Textarea(attrs={
            'rows': 5,
            'cols': 80,
            'placeholder': 'Una best practice per riga\n- Pratica 1\n- Pratica 2'
        }),
        required=False,
        help_text="Suggerimenti per il collegamento ai fascicoli"
    )
    
    # Sezione 4: Workflow
    help_workflow_stati = forms.CharField(
        label="Stati Workflow",
        widget=forms.Textarea(attrs={
            'rows': 3,
            'cols': 80,
            'placeholder': 'Bozza\nProtocollato\nArchiviato'
        }),
        required=False,
        help_text="Stati possibili del documento (uno per riga)"
    )
    
    help_workflow_stato_iniziale = forms.CharField(
        label="Stato Iniziale",
        max_length=50,
        required=False,
        help_text="Stato di default alla creazione (es. Bozza)"
    )
    
    # Sezione 5: Note Speciali
    help_note_attenzioni = forms.CharField(
        label="Attenzioni Importanti",
        widget=forms.Textarea(attrs={
            'rows': 5,
            'cols': 80,
            'placeholder': 'Una attenzione per riga\n- Attenzione 1\n- Attenzione 2'
        }),
        required=False,
        help_text="Attenzioni importanti da tenere a mente"
    )
    
    help_note_suggerimenti = forms.CharField(
        label="Suggerimenti Operativi",
        widget=forms.Textarea(attrs={
            'rows': 5,
            'cols': 80,
            'placeholder': 'Un suggerimento per riga\n- Suggerimento 1\n- Suggerimento 2'
        }),
        required=False,
        help_text="Suggerimenti per un uso ottimale"
    )
    
    help_note_vincoli = forms.CharField(
        label="Vincoli di Business",
        widget=forms.Textarea(attrs={
            'rows': 5,
            'cols': 80,
            'placeholder': 'Un vincolo per riga\n- Vincolo 1\n- Vincolo 2'
        }),
        required=False,
        help_text="Regole di business da rispettare"
    )
    
    # ========================================================================
    # GESTIONE FAQ (via widget JSON semplificato)
    # ========================================================================
    
    help_faq_json = forms.JSONField(
        label="FAQ (JSON)",
        widget=forms.Textarea(attrs={
            'rows': 10,
            'cols': 80,
            'placeholder': '''[
  {
    "domanda": "Come faccio a...?",
    "risposta": "Devi fare così..."
  }
]'''
        }),
        required=False,
        help_text=mark_safe(
            'Lista FAQ in formato JSON. Struttura: '
            '<code>[{"domanda": "...", "risposta": "..."}]</code>'
        )
    )
    
    class Meta:
        model = DocumentiTipo
        fields = '__all__'
        widgets = {
            'help_data': forms.HiddenInput(),  # Nascosto, ricostruito dal form
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Carica help_data esistente nei campi separati
        if self.instance and self.instance.help_data:
            self._load_help_data_to_fields()
        
        # Aggiungi CSS custom
        self.fields['help_descrizione_breve'].widget.attrs['class'] = 'vLargeTextField'
    
    def _load_help_data_to_fields(self):
        """Carica i dati da help_data JSON nei campi del form."""
        hd = self.instance.help_data
        
        # Descrizione breve
        self.fields['help_descrizione_breve'].initial = hd.get('descrizione_breve', '')
        
        # Quando usare
        quando = hd.get('quando_usare', {})
        if casi := quando.get('casi_uso', []):
            self.fields['help_quando_usare_casi'].initial = '\n'.join(casi)
        if non_usare := quando.get('non_usare_per', []):
            self.fields['help_quando_usare_non_usare'].initial = '\n'.join(non_usare)
        
        # Relazione fascicoli
        rel_fasc = hd.get('relazione_fascicoli', {})
        self.fields['help_relazione_fascicoli_descrizione'].initial = rel_fasc.get('descrizione', '')
        if bp := rel_fasc.get('best_practices', []):
            self.fields['help_relazione_fascicoli_best_practices'].initial = '\n'.join(bp)
        
        # Workflow
        workflow = hd.get('workflow', {})
        if stati := workflow.get('stati_possibili', []):
            self.fields['help_workflow_stati'].initial = '\n'.join(stati)
        self.fields['help_workflow_stato_iniziale'].initial = workflow.get('stato_iniziale', '')
        
        # Note speciali
        note = hd.get('note_speciali', {})
        if att := note.get('attenzioni', []):
            self.fields['help_note_attenzioni'].initial = '\n'.join(att)
        if sug := note.get('suggerimenti', []):
            self.fields['help_note_suggerimenti'].initial = '\n'.join(sug)
        if vinc := note.get('vincoli_business', []):
            self.fields['help_note_vincoli'].initial = '\n'.join(vinc)
        
        # FAQ
        if faq := hd.get('faq', []):
            self.fields['help_faq_json'].initial = faq
    
    def clean(self):
        """Validazione custom."""
        cleaned_data = super().clean()
        
        # Valida FAQ JSON se presente
        faq_json = cleaned_data.get('help_faq_json')
        if faq_json:
            if not isinstance(faq_json, list):
                raise forms.ValidationError({
                    'help_faq_json': 'FAQ deve essere una lista di oggetti'
                })
            for item in faq_json:
                if not isinstance(item, dict) or 'domanda' not in item or 'risposta' not in item:
                    raise forms.ValidationError({
                        'help_faq_json': 'Ogni FAQ deve avere "domanda" e "risposta"'
                    })
        
        return cleaned_data
    
    def save(self, commit=True):
        """Salva ricostruendo help_data dai campi del form."""
        instance = super().save(commit=False)
        
        # Ricostruisci help_data dalle sezioni discorsive
        help_data = self._build_help_data_from_fields()
        
        # Per nuove istanze, salva prima l'oggetto base senza sezioni tecniche
        # in modo che abbia un PK per le query di AttributoDefinizione
        if not instance.pk and commit:
            instance.help_data = help_data
            instance.save()
        
        # Genera sezioni tecniche automaticamente (richiede instance.pk)
        builder = HelpDataBuilder(instance)
        technical_sections = builder.build_all_technical_sections()
        
        # Merge: discorsive (da form) + tecniche (auto-generate)
        help_data.update(technical_sections)
        
        instance.help_data = help_data
        
        if commit:
            instance.save()
        
        return instance
    
    def _build_help_data_from_fields(self) -> Dict[str, Any]:
        """Costruisce help_data dalle sezioni discorsive del form."""
        cd = self.cleaned_data
        
        help_data = {}
        
        # Descrizione breve
        if desc := cd.get('help_descrizione_breve', '').strip():
            help_data['descrizione_breve'] = desc
        
        # Quando usare
        casi_uso = self._parse_multiline(cd.get('help_quando_usare_casi', ''))
        non_usare = self._parse_multiline(cd.get('help_quando_usare_non_usare', ''))
        if casi_uso or non_usare:
            help_data['quando_usare'] = {
                'casi_uso': casi_uso,
                'non_usare_per': non_usare,
            }
        
        # Relazione fascicoli
        rel_desc = cd.get('help_relazione_fascicoli_descrizione', '').strip()
        rel_bp = self._parse_multiline(cd.get('help_relazione_fascicoli_best_practices', ''))
        if rel_desc or rel_bp:
            help_data['relazione_fascicoli'] = {
                'descrizione': rel_desc,
                'best_practices': rel_bp,
                'vantaggi_collegamento': [],
                'come_collegare': {},
                'regole_business': {},
            }
        
        # Workflow
        stati = self._parse_multiline(cd.get('help_workflow_stati', ''))
        stato_init = cd.get('help_workflow_stato_iniziale', '').strip()
        if stati or stato_init:
            help_data['workflow'] = {
                'stati_possibili': stati or ['Bozza', 'Protocollato', 'Archiviato'],
                'stato_iniziale': stato_init or (stati[0] if stati else 'Bozza'),
                'azioni_disponibili': [],
            }
        
        # Note speciali
        attenzioni = self._parse_multiline(cd.get('help_note_attenzioni', ''))
        suggerimenti = self._parse_multiline(cd.get('help_note_suggerimenti', ''))
        vincoli = self._parse_multiline(cd.get('help_note_vincoli', ''))
        if attenzioni or suggerimenti or vincoli:
            help_data['note_speciali'] = {
                'attenzioni': attenzioni,
                'suggerimenti': suggerimenti,
                'vincoli_business': vincoli,
            }
        
        # FAQ
        if faq := cd.get('help_faq_json'):
            help_data['faq'] = faq
        
        # Risorse correlate (placeholder)
        help_data['risorse_correlate'] = {
            'guide_correlate': [],
            'tipi_documento_correlati': [],
        }
        
        return help_data
    
    def _parse_multiline(self, text: str) -> list:
        """
        Converte testo multilinea in lista.
        Rimuove '- ' iniziale se presente.
        """
        if not text:
            return []
        
        lines = [line.strip() for line in text.strip().split('\n')]
        # Rimuovi '- ' iniziale
        lines = [line.lstrip('- ').strip() for line in lines if line.strip()]
        return lines


class HelpDataFieldset:
    """Helper per organizzare i fieldset nel ModelAdmin."""
    
    @staticmethod
    def get_fieldsets():
        """Restituisce i fieldset organizzati per sezioni."""
        return [
            ('Informazioni Base', {
                'fields': ('codice', 'nome', 'attivo', 'estensioni_permesse'),
            }),
            ('Pattern e Nomi File', {
                'fields': ('pattern_codice', 'nome_file_pattern'),
                'description': (
                    'Questi pattern vengono usati per generare automaticamente '
                    'le sezioni tecniche dell\'help.'
                ),
            }),
            ('Rilevamento Duplicati', {
                'fields': ('duplicate_detection_config',),
                'classes': ('collapse',),
            }),
            ('Help - Descrizione', {
                'fields': ('help_descrizione_breve',),
                'description': 'Panoramica generale del tipo documento',
            }),
            ('Help - Quando Usare', {
                'fields': ('help_quando_usare_casi', 'help_quando_usare_non_usare'),
                'description': 'Casi d\'uso appropriati e situazioni da evitare',
            }),
            ('Help - Relazione Fascicoli', {
                'fields': (
                    'help_relazione_fascicoli_descrizione',
                    'help_relazione_fascicoli_best_practices'
                ),
                'classes': ('collapse',),
            }),
            ('Help - Workflow', {
                'fields': ('help_workflow_stati', 'help_workflow_stato_iniziale'),
                'classes': ('collapse',),
            }),
            ('Help - Note Speciali', {
                'fields': (
                    'help_note_attenzioni',
                    'help_note_suggerimenti',
                    'help_note_vincoli'
                ),
                'classes': ('collapse',),
            }),
            ('Help - FAQ', {
                'fields': ('help_faq_json',),
                'classes': ('collapse',),
                'description': mark_safe(
                    'FAQ in formato JSON. '
                    'Per editing avanzato usa il '
                    '<a href="#" onclick="alert(\'Usa: python manage.py configure_help_wizard\')">wizard CLI</a>'
                ),
            }),
            ('Help - Ordine Visualizzazione', {
                'fields': ('help_ordine',),
                'classes': ('collapse',),
            }),
            ('Dati Tecnici (Non Modificare)', {
                'fields': ('help_data',),
                'classes': ('collapse',),
                'description': mark_safe(
                    '<strong>ATTENZIONE:</strong> Questo campo viene generato automaticamente. '
                    'Modificare solo se sai cosa stai facendo.<br>'
                    'Le sezioni tecniche (attributi_dinamici, pattern_codice, archiviazione, '
                    'campi_obbligatori) vengono rigenerate automaticamente al salvataggio.'
                ),
            }),
        ]
