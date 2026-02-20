"""
Utility per costruire automaticamente le sezioni tecniche del help_data
a partire dai dati del modello DocumentiTipo e AttributoDefinizione.
"""
from __future__ import annotations
from typing import Dict, List, Any, Optional
from django.db.models import Model


class HelpDataBuilder:
    """
    Costruisce automaticamente le sezioni tecniche del help_data
    per un tipo documento.
    """
    
    def __init__(self, tipo_documento):
        """
        Args:
            tipo_documento: Istanza di DocumentiTipo
        """
        self.tipo = tipo_documento
    
    def build_attributi_dinamici(self) -> Dict[str, Any]:
        """
        Genera automaticamente la sezione attributi_dinamici
        a partire da AttributoDefinizione.
        
        Returns:
            Dict con chiavi 'disponibili' e 'pattern_code_examples'
        """
        from documenti.models import AttributoDefinizione
        
        # Se l'istanza non è ancora salvata, ritorna struttura vuota
        if not self.tipo.pk:
            return {
                'disponibili': [],
                'pattern_code_examples': [],
            }
        
        attributi = AttributoDefinizione.objects.filter(
            tipo_documento=self.tipo
        ).order_by('ordine', 'codice')
        
        disponibili = []
        for attr in attributi:
            # Mappa tipo_dato Django → tipo visualizzato
            tipo_map = {
                'str': 'CharField',
                'int': 'IntegerField',
                'float': 'DecimalField',
                'date': 'DateField',
                'datetime': 'DateTimeField',
                'bool': 'BooleanField',
                'choice': 'ChoiceField',
            }
            
            attr_dict = {
                'codice': attr.codice,
                'nome': attr.nome,
                'tipo': tipo_map.get(attr.tipo_dato, attr.tipo_dato),
                'descrizione': attr.help_text or f"Campo {attr.nome}",
                'obbligatorio': attr.required,
                'esempio': self._generate_example(attr),
            }
            
            # Widget anagrafica → ForeignKey
            if attr.widget and 'anag' in attr.widget.lower():
                attr_dict['tipo'] = 'ForeignKey'
                attr_dict['modello'] = 'anagrafiche.Anagrafica'
            
            # Choices
            if attr.choices:
                choices_list = [
                    c.strip() 
                    for c in attr.choices.split(',')
                ]
                attr_dict['choices'] = choices_list
            
            # Validazione regex
            if attr.regex:
                attr_dict['validazione'] = f"Pattern: {attr.regex}"
            
            disponibili.append(attr_dict)
        
        # Esempi pattern codice
        pattern_examples = self._build_pattern_code_examples()
        
        return {
            'disponibili': disponibili,
            'pattern_code_examples': pattern_examples,
        }
    
    def build_pattern_codice(self) -> Dict[str, Any]:
        """
        Genera automaticamente la sezione pattern_codice.
        
        Returns:
            Dict con pattern, spiegazione, esempi, placeholder
        """
        pattern = self.tipo.pattern_codice or "{CLI}_{TIPO}_{DATA}_{SEQ:03d}"
        
        # Placeholder disponibili (standard)
        placeholder_map = {
            '{CLI}': 'Codice cliente (8 caratteri: 6 cifre + 2 lettere check)',
            '{TIPO}': f'Codice tipo documento ({self.tipo.codice})',
            '{DATA}': 'Data documento (formato YYYYMMDD)',
            '{ANNO}': 'Anno documento (YYYY)',
            '{MESE}': 'Mese documento (MM)',
            '{SEQ}': 'Sequenziale progressivo',
            '{SEQ:03d}': 'Sequenziale con padding (es. 001, 002, ...)',
            '{TIT}': 'Codice voce titolario',
        }
        
        # Aggiungi placeholder da attributi dinamici
        from documenti.models import AttributoDefinizione
        
        # Solo se l'istanza è salvata, altrimenti skip attributi dinamici
        if self.tipo.pk:
            attributi = AttributoDefinizione.objects.filter(tipo_documento=self.tipo)
            for attr in attributi:
                placeholder_map[f'{{attr:{attr.codice}}}'] = (
                    f'Valore attributo "{attr.nome}"'
                )
                if attr.widget and 'anag' in attr.widget.lower():
                    placeholder_map[f'{{attr:{attr.codice}.codice}}'] = (
                        f'Codice anagrafica da "{attr.nome}"'
                    )
        
        # Esempi
        esempi = self._build_pattern_examples()
        
        return {
            'default': pattern,
            'spiegazione': self._explain_pattern(pattern),
            'esempi': esempi,
            'placeholder_disponibili': placeholder_map,
            'personalizzazione': (
                'Il pattern può essere modificato nell\'admin di Django, '
                'sezione "Pattern codice" del tipo documento.'
            ),
        }
    
    def build_archiviazione(self) -> Dict[str, Any]:
        """
        Genera automaticamente la sezione archiviazione.
        
        Returns:
            Dict con percorso, pattern file, esempi
        """
        # Pattern nome file
        nome_file_pattern = self.tipo.nome_file_pattern or '{tipo.codice}_{id}.pdf'
        
        # Percorso base (da titolario)
        percorso_base = '/NAS/{CLI}/{TIT}/'
        
        return {
            'percorso_tipo': percorso_base,
            'esempio': f'/NAS/123456AB/PAG/',
            'nome_file_pattern': nome_file_pattern,
            'esempio_file': self._build_filename_example(),
            'esempio_completo': (
                f'/NAS/123456AB/PAG/{self._build_filename_example()}'
            ),
            'note': [
                'I documenti vengono archiviati automaticamente nel NAS',
                'La struttura delle cartelle segue il titolario',
                'Il nome del file viene generato automaticamente dal pattern',
                'I documenti digitali non hanno ubicazione fisica',
            ],
            'organizzazione': (
                'La struttura delle cartelle è: /NAS/<Codice Cliente>/<Codice Titolario>/'
            ),
        }
    
    def build_campi_obbligatori(self) -> Dict[str, Any]:
        """
        Genera automaticamente la sezione campi_obbligatori.
        
        Returns:
            Dict con 'sempre' e 'condizionali'
        """
        from documenti.models import AttributoDefinizione
        
        # Campi sempre obbligatori (base Documento)
        sempre = [
            'Cliente',
            'Data documento',
            'Titolario',
        ]
        
        # Aggiungi attributi required (solo se istanza salvata)
        if self.tipo.pk:
            attributi_req = AttributoDefinizione.objects.filter(
                tipo_documento=self.tipo,
                required=True
            )
            sempre.extend([attr.nome for attr in attributi_req])
        
        # Campi condizionali (logiche business)
        condizionali = {}
        
        # Se documento non digitale → ubicazione obbligatoria
        condizionali['Ubicazione fisica'] = (
            'Obbligatorio solo per documenti cartacei non fascicolati'
        )
        
        # Se documento fascicolato → fascicolo obbligatorio
        condizionali['Fascicolo'] = (
            'Obbligatorio se si vuole collegare il documento a un fascicolo'
        )
        
        return {
            'sempre': sempre,
            'condizionali': condizionali,
        }
    
    def _generate_example(self, attr) -> str:
        """Genera un esempio per un attributo."""
        if attr.choices:
            first_choice = attr.choices.split(',')[0].strip()
            if '|' in first_choice:
                return first_choice.split('|')[0]
            return first_choice
        
        tipo_examples = {
            'str': 'Testo esempio',
            'int': '123',
            'float': '123.45',
            'date': '2026-02-11',
            'datetime': '2026-02-11 14:30:00',
            'bool': 'True',
        }
        return tipo_examples.get(attr.tipo_dato, 'Valore esempio')
    
    def _build_pattern_code_examples(self) -> List[Dict[str, str]]:
        """Genera esempi per pattern code."""
        return [
            {
                'pattern': '{CLI}-{TIPO}-{ANNO}-{SEQ:03d}',
                'risultato': '123456AB-CED-2026-001',
                'spiegazione': 'Cliente 123456AB, tipo CED, anno 2026, sequenziale 1',
            },
        ]
    
    def _build_pattern_examples(self) -> List[Dict[str, Any]]:
        """Genera esempi di pattern codice documento."""
        return [
            {
                'input': {
                    'cliente': '123456AB',
                    'anno': 2026,
                    'sequenza': 1,
                },
                'output': f'123456AB-{self.tipo.codice}-2026-001',
                'descrizione': 'Primo documento del 2026 per cliente 123456AB',
            },
        ]
    
    def _explain_pattern(self, pattern: str) -> str:
        """Spiega un pattern in linguaggio naturale."""
        parts = []
        if '{CLI}' in pattern:
            parts.append('codice cliente')
        if '{TIPO}' in pattern:
            parts.append('codice tipo documento')
        if '{ANNO}' in pattern:
            parts.append('anno')
        if '{SEQ' in pattern:
            parts.append('sequenziale progressivo')
        
        return f"Il codice è composto da: {', '.join(parts)}"
    
    def _build_filename_example(self) -> str:
        """Genera un esempio di nome file."""
        pattern = self.tipo.nome_file_pattern or '{tipo.codice}_{id}.pdf'
        # Sostituzione semplice per esempio
        example = pattern.replace('{tipo.codice}', self.tipo.codice)
        example = example.replace('{id}', '123')
        example = example.replace('{data_documento:%Y%m%d}', '20260211')
        return example
    
    def build_all_technical_sections(self) -> Dict[str, Any]:
        """
        Genera TUTTE le sezioni tecniche automaticamente.
        
        Returns:
            Dict con tutte le sezioni tecniche popolate
        """
        return {
            'attributi_dinamici': self.build_attributi_dinamici(),
            'pattern_codice': self.build_pattern_codice(),
            'archiviazione': self.build_archiviazione(),
            'campi_obbligatori': self.build_campi_obbligatori(),
        }
    
    def merge_with_existing(self, existing_help_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggiorna le sezioni tecniche mantenendo quelle discorsive esistenti.
        
        Args:
            existing_help_data: help_data esistente
            
        Returns:
            help_data aggiornato con sezioni tecniche rigenerate
        """
        technical = self.build_all_technical_sections()
        
        # Copia help_data esistente
        updated = dict(existing_help_data or {})
        
        # Sovrascrivi solo sezioni tecniche
        updated.update(technical)
        
        return updated


def rebuild_help_technical_sections(tipo_documento) -> Dict[str, Any]:
    """
    Funzione helper per rigenerare le sezioni tecniche di un tipo documento.
    
    Args:
        tipo_documento: Istanza di DocumentiTipo
        
    Returns:
        help_data aggiornato
    """
    builder = HelpDataBuilder(tipo_documento)
    return builder.merge_with_existing(tipo_documento.help_data)


def get_help_status(help_data: Dict[str, Any]) -> str:
    """
    Determina lo stato di completamento di un help_data.
    
    Args:
        help_data: Dizionario help_data da analizzare
        
    Returns:
        Stato: 'completo', 'da_completare', 'parziale', 'vuoto'
    """
    if not help_data or len(help_data) == 0:
        return 'vuoto'
    
    # Controlla meta status se presente
    meta = help_data.get('_meta', {})
    if meta.get('stato') == 'da_completare':
        return 'da_completare'
    
    # Sezioni richieste per considerare help completo
    required_sections = [
        'descrizione_breve',
        'quando_usare',
        'attributi_dinamici',
        'pattern_codice',
        'archiviazione',
        'campi_obbligatori',
        'workflow',
        'note_speciali',
    ]
    
    # Conta sezioni presenti e non-placeholder
    present_count = 0
    for section in required_sections:
        if section in help_data:
            data = help_data[section]
            # Verifica che non sia placeholder "Da definire"
            if isinstance(data, dict):
                str_data = str(data)
                if 'Da definire' not in str_data and 'da completare' not in str_data.lower():
                    present_count += 1
            elif isinstance(data, str):
                if 'Da definire' not in data and 'da completare' not in data.lower():
                    present_count += 1
            else:
                present_count += 1
    
    # Determina stato in base a percentuale completamento
    completion_rate = present_count / len(required_sections)
    
    if completion_rate >= 0.8:
        return 'completo'
    elif completion_rate >= 0.4:
        return 'parziale'
    else:
        return 'da_completare'


def is_help_complete(tipo_documento) -> bool:
    """
    Verifica se l'help di un tipo documento è completo.
    
    Args:
        tipo_documento: Istanza di DocumentiTipo
        
    Returns:
        True se completo, False altrimenti
    """
    if not tipo_documento.help_data:
        return False
    
    status = get_help_status(tipo_documento.help_data)
    return status == 'completo'


def is_help_visible_to_public(help_data: Dict[str, Any]) -> bool:
    """
    Verifica se un help deve essere visibile al pubblico (non admin).
    
    Args:
        help_data: Dizionario help_data
        
    Returns:
        True se visibile pubblicamente, False se solo admin
    """
    if not help_data:
        return False
    
    # Controlla flag meta
    meta = help_data.get('_meta', {})
    
    # Se esplicitamente marcato come non visibile
    if 'visibile_pubblico' in meta:
        return meta['visibile_pubblico']
    
    # Altrimenti basati sullo stato
    status = get_help_status(help_data)
    
    # Solo help completi o parziali visibili al pubblico
    return status in ['completo', 'parziale']
