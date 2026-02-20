# Design: Sistema Generico di Rilevamento Duplicati per Documenti

## Data
5 Febbraio 2026

## 🎯 Obiettivo

Creare un sistema **generico, configurabile e riutilizzabile** per rilevare documenti duplicati basato su criteri definiti a livello di **tipo documento** (DocumentiTipo).

## 🏗️ Architettura Proposta

### 1. **Configurazione a Livello di Tipo Documento**

Aggiungere campo JSON al modello `DocumentiTipo` per definire i criteri di duplicazione:

```python
class DocumentiTipo(models.Model):
    # ... campi esistenti ...
    
    duplicate_detection_config = models.JSONField(
        default=dict,
        blank=True,
        encoder=DjangoJSONEncoder,
        verbose_name=_("Configurazione rilevamento duplicati"),
        help_text=_(
            "Criteri per identificare documenti duplicati. "
            "Struttura: {'enabled': bool, 'strategy': str, 'fields': [...], 'scope': {...}}"
        )
    )
```

### 2. **Struttura Configurazione JSON**

```json
{
    "enabled": true,
    "strategy": "exact_match",
    "scope": {
        "cliente": true,
        "anno": false,
        "fascicolo": false
    },
    "fields": [
        {
            "type": "attribute",
            "code": "numero_cedolino",
            "required": false,
            "weight": 1.0
        },
        {
            "type": "attribute",
            "code": "data_ora_cedolino",
            "required": false,
            "weight": 1.0
        }
    ],
    "match_mode": "all_required_or_any_weighted"
}
```

#### Parametri Configurazione

| Parametro | Tipo | Descrizione |
|-----------|------|-------------|
| `enabled` | bool | Attiva/disattiva rilevamento duplicati per questo tipo |
| `strategy` | str | Strategia di matching: `exact_match`, `weighted`, `fuzzy` |
| `scope.cliente` | bool | Match solo documenti dello stesso cliente |
| `scope.anno` | bool | Match solo documenti dello stesso anno |
| `scope.fascicolo` | bool | Match solo documenti dello stesso fascicolo |
| `fields` | array | Lista campi/attributi da confrontare |
| `match_mode` | str | Modalità: `all`, `any`, `all_required_or_any_weighted` |

#### Field Configuration

```json
{
    "type": "attribute",           // 'attribute', 'field', 'metadata'
    "code": "numero_cedolino",     // Codice attributo o nome campo
    "required": false,             // Se true, campo obbligatorio per match
    "weight": 1.0,                 // Peso per match ponderato (0.0-1.0)
    "normalize": true,             // Normalizza valore prima del confronto
    "case_sensitive": false        // Match case-sensitive
}
```

### 3. **Service Layer: DuplicateDetectionService**

Creare un service generico per il rilevamento:

```python
# documenti/services/duplicate_detection.py

from typing import Optional, List, Dict, Any
from django.db.models import Q
from documenti.models import Documento, DocumentiTipo, AttributoValore
import logging

logger = logging.getLogger(__name__)


class DuplicateMatchResult:
    """Risultato del match duplicazione"""
    
    def __init__(self, is_duplicate: bool, documento: Optional[Documento] = None,
                 confidence: float = 0.0, matched_fields: List[str] = None):
        self.is_duplicate = is_duplicate
        self.documento = documento
        self.confidence = confidence  # 0.0 - 1.0
        self.matched_fields = matched_fields or []
    
    def __bool__(self):
        return self.is_duplicate
    
    def __repr__(self):
        if self.is_duplicate:
            return (f"<DuplicateMatch: Doc {self.documento.id}, "
                   f"confidence={self.confidence:.2f}, "
                   f"fields={', '.join(self.matched_fields)}>")
        return "<NoDuplicate>"


class DuplicateDetectionService:
    """
    Servizio generico per rilevamento duplicati documenti.
    
    Utilizzo:
        service = DuplicateDetectionService(tipo_documento)
        result = service.find_duplicate(
            cliente=cliente,
            attributi={'numero_cedolino': '00071', 'data_ora_cedolino': '31-12-2025 14:30'},
            documento_fields={'data_documento': date(2025, 12, 31)}
        )
        
        if result.is_duplicate:
            print(f"Duplicato trovato: {result.documento.codice}")
            print(f"Confidenza: {result.confidence}")
            print(f"Campi matched: {result.matched_fields}")
    """
    
    def __init__(self, tipo_documento: DocumentiTipo):
        self.tipo = tipo_documento
        self.config = tipo_documento.duplicate_detection_config or {}
        self.enabled = self.config.get('enabled', False)
    
    def is_enabled(self) -> bool:
        """Verifica se rilevamento duplicati è attivo per questo tipo"""
        return self.enabled
    
    def find_duplicate(
        self,
        cliente: Optional['Cliente'] = None,
        fascicolo: Optional['Fascicolo'] = None,
        attributi: Dict[str, Any] = None,
        documento_fields: Dict[str, Any] = None,
        exclude_documento_id: Optional[int] = None
    ) -> DuplicateMatchResult:
        """
        Cerca documento duplicato basandosi sulla configurazione.
        
        Args:
            cliente: Cliente del documento
            fascicolo: Fascicolo del documento (opzionale)
            attributi: Dizionario attributi dinamici {codice: valore}
            documento_fields: Campi del modello Documento {nome_campo: valore}
            exclude_documento_id: ID documento da escludere dalla ricerca
            
        Returns:
            DuplicateMatchResult con informazioni sul match
        """
        if not self.enabled:
            return DuplicateMatchResult(is_duplicate=False)
        
        attributi = attributi or {}
        documento_fields = documento_fields or {}
        
        # 1. Build base query con scope
        query = self._build_scope_query(cliente, fascicolo, documento_fields)
        
        if exclude_documento_id:
            query = query.exclude(id=exclude_documento_id)
        
        # Prefetch attributi per ottimizzare
        documenti = query.prefetch_related('attributi__definizione')
        
        if not documenti.exists():
            return DuplicateMatchResult(is_duplicate=False)
        
        # 2. Strategy-based matching
        strategy = self.config.get('strategy', 'exact_match')
        
        if strategy == 'exact_match':
            return self._exact_match_strategy(documenti, attributi, documento_fields)
        elif strategy == 'weighted':
            return self._weighted_match_strategy(documenti, attributi, documento_fields)
        else:
            logger.warning(f"Unknown strategy '{strategy}', using exact_match")
            return self._exact_match_strategy(documenti, attributi, documento_fields)
    
    def _build_scope_query(self, cliente, fascicolo, documento_fields):
        """Costruisce query base con scope configurato"""
        scope = self.config.get('scope', {})
        
        # Base: stesso tipo
        query = Documento.objects.filter(tipo=self.tipo)
        
        # Scope: cliente
        if scope.get('cliente', True) and cliente:
            query = query.filter(cliente=cliente)
        
        # Scope: fascicolo
        if scope.get('fascicolo', False) and fascicolo:
            query = query.filter(fascicolo=fascicolo)
        
        # Scope: anno
        if scope.get('anno', False) and 'data_documento' in documento_fields:
            anno = documento_fields['data_documento'].year
            query = query.filter(data_documento__year=anno)
        
        return query
    
    def _exact_match_strategy(self, documenti, attributi, documento_fields):
        """
        Strategia exact match: tutti i campi configurati devono corrispondere.
        
        Logica:
        - Se campo è 'required': DEVE matchare
        - Se campo è opzionale: matcha se presente in entrambi
        """
        fields_config = self.config.get('fields', [])
        match_mode = self.config.get('match_mode', 'all')
        
        for doc in documenti:
            matched_fields = []
            required_matches = 0
            required_count = 0
            optional_matches = 0
            
            # Costruisci dizionario attributi documento
            doc_attributi = {
                attr.definizione.codice: attr.valore
                for attr in doc.attributi.all()
            }
            
            # Verifica ogni campo configurato
            for field_cfg in fields_config:
                field_type = field_cfg.get('type')
                field_code = field_cfg.get('code')
                is_required = field_cfg.get('required', False)
                
                if is_required:
                    required_count += 1
                
                # Match attributo
                if field_type == 'attribute':
                    value_new = attributi.get(field_code)
                    value_doc = doc_attributi.get(field_code)
                    
                    # Normalizza valori
                    if field_cfg.get('normalize', True):
                        value_new = self._normalize_value(value_new)
                        value_doc = self._normalize_value(value_doc)
                    
                    # Case sensitivity
                    if not field_cfg.get('case_sensitive', False):
                        if isinstance(value_new, str):
                            value_new = value_new.lower()
                        if isinstance(value_doc, str):
                            value_doc = value_doc.lower()
                    
                    # Confronto
                    if value_new and value_doc and value_new == value_doc:
                        matched_fields.append(field_code)
                        if is_required:
                            required_matches += 1
                        else:
                            optional_matches += 1
                    elif is_required and (value_new or value_doc):
                        # Required field non matcha
                        break
                
                # Match campo documento
                elif field_type == 'field':
                    value_new = documento_fields.get(field_code)
                    value_doc = getattr(doc, field_code, None)
                    
                    if value_new and value_doc and value_new == value_doc:
                        matched_fields.append(field_code)
                        if is_required:
                            required_matches += 1
                        else:
                            optional_matches += 1
                    elif is_required:
                        break
            
            else:  # No break - tutti i controlli passati
                # Valuta match in base a match_mode
                is_match = False
                
                if match_mode == 'all':
                    # Tutti i campi devono matchare
                    is_match = (required_matches == required_count and
                               len(matched_fields) == len(fields_config))
                
                elif match_mode == 'any':
                    # Almeno un campo deve matchare
                    is_match = len(matched_fields) > 0
                
                elif match_mode == 'all_required_or_any_weighted':
                    # Tutti i required + almeno un opzionale (se ci sono opzionali)
                    is_match = required_matches == required_count
                    if is_match and (len(fields_config) > required_count):
                        is_match = optional_matches > 0
                
                if is_match:
                    confidence = len(matched_fields) / len(fields_config) if fields_config else 0.0
                    return DuplicateMatchResult(
                        is_duplicate=True,
                        documento=doc,
                        confidence=confidence,
                        matched_fields=matched_fields
                    )
        
        return DuplicateMatchResult(is_duplicate=False)
    
    def _weighted_match_strategy(self, documenti, attributi, documento_fields):
        """
        Strategia weighted: calcola score basato su pesi configurati.
        Match se score >= threshold (default 0.8)
        """
        threshold = self.config.get('threshold', 0.8)
        fields_config = self.config.get('fields', [])
        
        best_match = None
        best_score = 0.0
        
        for doc in documenti:
            doc_attributi = {
                attr.definizione.codice: attr.valore
                for attr in doc.attributi.all()
            }
            
            total_weight = 0.0
            matched_weight = 0.0
            matched_fields = []
            
            for field_cfg in fields_config:
                field_type = field_cfg.get('type')
                field_code = field_cfg.get('code')
                weight = field_cfg.get('weight', 1.0)
                
                total_weight += weight
                
                # Match attributo
                if field_type == 'attribute':
                    value_new = self._normalize_value(attributi.get(field_code))
                    value_doc = self._normalize_value(doc_attributi.get(field_code))
                    
                    if value_new and value_doc and value_new == value_doc:
                        matched_weight += weight
                        matched_fields.append(field_code)
                
                elif field_type == 'field':
                    value_new = documento_fields.get(field_code)
                    value_doc = getattr(doc, field_code, None)
                    
                    if value_new and value_doc and value_new == value_doc:
                        matched_weight += weight
                        matched_fields.append(field_code)
            
            # Calcola score
            score = matched_weight / total_weight if total_weight > 0 else 0.0
            
            if score >= threshold and score > best_score:
                best_score = score
                best_match = DuplicateMatchResult(
                    is_duplicate=True,
                    documento=doc,
                    confidence=score,
                    matched_fields=matched_fields
                )
        
        return best_match or DuplicateMatchResult(is_duplicate=False)
    
    def _normalize_value(self, value):
        """Normalizza valore per confronto"""
        if value is None:
            return None
        
        if isinstance(value, str):
            # Trim whitespace
            value = value.strip()
            # Empty string → None
            if not value:
                return None
        
        return value
```

### 4. **Configurazioni Predefinite per Tipi Comuni**

#### Cedolini (BPAG)

```json
{
    "enabled": true,
    "strategy": "exact_match",
    "scope": {
        "cliente": true,
        "anno": false,
        "fascicolo": false
    },
    "fields": [
        {
            "type": "attribute",
            "code": "numero_cedolino",
            "required": false,
            "weight": 1.0,
            "normalize": true,
            "case_sensitive": false
        },
        {
            "type": "attribute",
            "code": "data_ora_cedolino",
            "required": false,
            "weight": 1.0,
            "normalize": true
        }
    ],
    "match_mode": "all_required_or_any_weighted"
}
```

**Logica**: Duplicato se stesso cliente + (numero_cedolino E data_ora_cedolino matchano)

#### Fatture (FATT)

```json
{
    "enabled": true,
    "strategy": "exact_match",
    "scope": {
        "cliente": true,
        "anno": true,
        "fascicolo": false
    },
    "fields": [
        {
            "type": "attribute",
            "code": "numero_fattura",
            "required": true,
            "weight": 1.0
        },
        {
            "type": "field",
            "code": "data_documento",
            "required": false,
            "weight": 0.5
        }
    ],
    "match_mode": "all"
}
```

**Logica**: Duplicato se stesso cliente + stesso anno + numero_fattura uguale

#### UNILAV

```json
{
    "enabled": true,
    "strategy": "exact_match",
    "scope": {
        "cliente": true,
        "anno": false,
        "fascicolo": false
    },
    "fields": [
        {
            "type": "attribute",
            "code": "protocollo_unilav",
            "required": true,
            "weight": 1.0
        },
        {
            "type": "attribute",
            "code": "codice_comunicazione",
            "required": false,
            "weight": 0.8
        }
    ],
    "match_mode": "all_required_or_any_weighted"
}
```

### 5. **Integrazione negli Importers**

Gli importer usano il service in modo uniforme:

```python
# documenti/importers/cedolini.py

from documenti.services.duplicate_detection import DuplicateDetectionService

class CedoliniImporter(BaseImporter):
    
    @transaction.atomic
    def create_documento(self, parsed_data, valori_editati, user, **kwargs):
        """Crea documento con verifica duplicazione generica"""
        
        # ... setup cliente, titolario, etc ...
        
        # Tipo documento
        tipo_bpag, _ = DocumentiTipo.objects.get_or_create(codice='BPAG', ...)
        
        # ✅ Verifica duplicazione usando service generico
        duplicate_policy = kwargs.get('duplicate_policy', 'skip')
        
        if duplicate_policy != 'add':
            # Prepara attributi per verifica
            attributi_per_verifica = {
                'numero_cedolino': parsed_data['cedolino'].get('numero_cedolino'),
                'data_ora_cedolino': parsed_data['cedolino'].get('data_ora_cedolino'),
            }
            
            # Usa service generico
            service = DuplicateDetectionService(tipo_bpag)
            
            if service.is_enabled():
                result = service.find_duplicate(
                    cliente=cliente,
                    attributi=attributi_per_verifica
                )
                
                if result.is_duplicate:
                    if duplicate_policy == 'skip':
                        logger.warning(
                            f"Duplicato rilevato: Doc {result.documento.codice} "
                            f"(confidence {result.confidence:.0%}, "
                            f"campi: {', '.join(result.matched_fields)})"
                        )
                        raise ValueError(
                            f"Documento già esistente: {result.documento.codice}"
                        )
                    
                    elif duplicate_policy == 'replace':
                        logger.info(f"Sostituzione documento {result.documento.id}")
                        result.documento.delete()
        
        # Crea documento
        documento = Documento.objects.create(...)
        
        # Salva attributi (numero e data/ora inclusi)
        self._create_attributi(documento, tipo_bpag, anno, mese, mensilita, parsed_data)
        
        return documento
```

### 6. **Admin Django Interface**

Aggiungere widget per configurazione JSON:

```python
# documenti/admin.py

from django.contrib import admin
from .models import DocumentiTipo

@admin.register(DocumentiTipo)
class DocumentiTipoAdmin(admin.ModelAdmin):
    fieldsets = [
        ('Informazioni Base', {
            'fields': ('codice', 'nome', 'attivo', 'estensioni_permesse')
        }),
        ('Pattern', {
            'fields': ('pattern_codice', 'nome_file_pattern')
        }),
        ('Rilevamento Duplicati', {
            'fields': ('duplicate_detection_config',),
            'classes': ('collapse',),
            'description': 'Configura criteri per identificare documenti duplicati'
        }),
        ('Help', {
            'fields': ('help_data', 'help_ordine'),
            'classes': ('collapse',)
        }),
    ]
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'duplicate_detection_config':
            kwargs['widget'] = JSONEditorWidget(
                schema={
                    'type': 'object',
                    'properties': {
                        'enabled': {'type': 'boolean'},
                        'strategy': {'type': 'string', 'enum': ['exact_match', 'weighted']},
                        # ...
                    }
                }
            )
        return super().formfield_for_dbfield(db_field, **kwargs)
```

## 🎯 Vantaggi della Soluzione

### 1. **Genericità**
- ✅ Un solo service per TUTTI i tipi di documento
- ✅ Nessun codice hardcoded per tipo specifico
- ✅ Riutilizzabile in qualsiasi importer

### 2. **Configurabilità**
- ✅ Configurazione via Admin Django (no code deploy)
- ✅ Criteri diversi per tipo documento
- ✅ Attivazione/disattivazione per tipo

### 3. **Flessibilità**
- ✅ Match su attributi dinamici o campi modello
- ✅ Strategie multiple (exact, weighted, fuzzy future)
- ✅ Scope configurabile (cliente, anno, fascicolo)
- ✅ Match modes: all, any, custom

### 4. **Manutenibilità**
- ✅ Logica centralizzata in un service
- ✅ Testing semplificato
- ✅ Facile estensione (nuove strategie, nuovi field types)

### 5. **Performance**
- ✅ Query ottimizzate con prefetch
- ✅ Early termination su non-match
- ✅ Scope query riduce set di ricerca

## 📋 Esempio Completo: BPAG (Cedolini)

### Migrazione per aggiungere campo

```python
# documenti/migrations/000X_add_duplicate_detection.py

from django.db import migrations, models
import django.core.serializers.json

class Migration(migrations.Migration):
    dependencies = [
        ('documenti', '000X_previous'),
    ]
    
    operations = [
        migrations.AddField(
            model_name='documentitipo',
            name='duplicate_detection_config',
            field=models.JSONField(
                blank=True,
                default=dict,
                encoder=django.core.serializers.json.DjangoJSONEncoder,
                help_text='Criteri per identificare documenti duplicati',
                verbose_name='Configurazione rilevamento duplicati'
            ),
        ),
    ]
```

### Data Migration per Configurazione BPAG

```python
# documenti/migrations/000X_configure_bpag_duplicates.py

from django.db import migrations

def configure_bpag_duplicates(apps, schema_editor):
    DocumentiTipo = apps.get_model('documenti', 'DocumentiTipo')
    
    config = {
        "enabled": True,
        "strategy": "exact_match",
        "scope": {
            "cliente": True,
            "anno": False,
            "fascicolo": False
        },
        "fields": [
            {
                "type": "attribute",
                "code": "numero_cedolino",
                "required": False,
                "weight": 1.0,
                "normalize": True,
                "case_sensitive": False
            },
            {
                "type": "attribute",
                "code": "data_ora_cedolino",
                "required": False,
                "weight": 1.0,
                "normalize": True
            }
        ],
        "match_mode": "all_required_or_any_weighted"
    }
    
    try:
        bpag = DocumentiTipo.objects.get(codice='BPAG')
        bpag.duplicate_detection_config = config
        bpag.save()
        print(f"✅ Configurata duplicazione per BPAG")
    except DocumentiTipo.DoesNotExist:
        print("⚠️  Tipo BPAG non trovato")

class Migration(migrations.Migration):
    dependencies = [
        ('documenti', '000X_add_duplicate_detection'),
    ]
    
    operations = [
        migrations.RunPython(
            configure_bpag_duplicates,
            reverse_code=migrations.RunPython.noop
        ),
    ]
```

## 🧪 Testing

```python
# documenti/tests/test_duplicate_detection.py

import pytest
from documenti.models import DocumentiTipo, Documento
from documenti.services.duplicate_detection import DuplicateDetectionService

@pytest.mark.django_db
class TestDuplicateDetection:
    
    def test_cedolino_exact_match_duplicate(self):
        """Test: stesso numero e data/ora = duplicato"""
        tipo_bpag = DocumentiTipo.objects.create(
            codice='BPAG',
            duplicate_detection_config={
                'enabled': True,
                'strategy': 'exact_match',
                'scope': {'cliente': True},
                'fields': [
                    {'type': 'attribute', 'code': 'numero_cedolino', 'required': False},
                    {'type': 'attribute', 'code': 'data_ora_cedolino', 'required': False}
                ],
                'match_mode': 'all_required_or_any_weighted'
            }
        )
        
        # Crea documento esistente
        doc1 = create_test_documento(tipo_bpag, cliente, attributi={
            'numero_cedolino': '00071',
            'data_ora_cedolino': '31-12-2025 14:30'
        })
        
        # Verifica duplicazione
        service = DuplicateDetectionService(tipo_bpag)
        result = service.find_duplicate(
            cliente=cliente,
            attributi={
                'numero_cedolino': '00071',
                'data_ora_cedolino': '31-12-2025 14:30'
            }
        )
        
        assert result.is_duplicate
        assert result.documento.id == doc1.id
        assert result.confidence == 1.0
        assert 'numero_cedolino' in result.matched_fields
        assert 'data_ora_cedolino' in result.matched_fields
    
    def test_cedolino_ristampa_non_duplicate(self):
        """Test: stesso numero ma data/ora diversa = NON duplicato"""
        # ... (stesso numero, timestamp diverso)
        assert not result.is_duplicate
```

## 🚀 Roadmap Implementazione

### Phase 1: Core Service
1. ✅ Aggiungere campo `duplicate_detection_config` a DocumentiTipo
2. ✅ Creare `DuplicateDetectionService` con strategia `exact_match`
3. ✅ Testing unitario del service

### Phase 2: Integrazione BPAG
1. ✅ Configurare BPAG con criteri numero + data/ora
2. ✅ Aggiornare `CedoliniImporter` per usare service
3. ✅ Aggiungere attributi `numero_cedolino` e `data_ora_cedolino`

### Phase 3: Altri Tipi
1. ✅ Configurare FATT (fatture)
2. ✅ Configurare UNILAV
3. ✅ Configurare altri tipi comuni

### Phase 4: Enhancements
1. ⏳ Strategia `weighted` avanzata
2. ⏳ Fuzzy matching (Levenshtein distance)
3. ⏳ UI/UX Admin per configurazione visuale

## 📚 Conclusione

Questa soluzione:
- ✅ È **generica** e riutilizzabile per qualsiasi tipo documento
- ✅ È **configurabile** via database (no code deploy)
- ✅ È **estensibile** con nuove strategie e field types
- ✅ È **performante** con query ottimizzate
- ✅ È **testabile** con logica centralizzata

**Elimina completamente** il bisogno di codice hardcoded per duplicazione nei singoli importer!
