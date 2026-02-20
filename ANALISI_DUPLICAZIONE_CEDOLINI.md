# Analisi: Duplicazione Cedolini basata su Numero e Data/Ora

## Data Analisi
5 Febbraio 2026

## Requisito
Verificare se un cedolino è già presente nel database usando:
1. **Numero cedolino** (`numero_cedolino`)
2. **Data/Ora cedolino** (`data_ora_cedolino`)

## 📊 Dati Estratti dal Parser

### Campi Estratti dal PDF

Il parser `cedolino_parser.py` estrae già questi campi:

```python
class CedolinoData(TypedDict):
    numero_cedolino: Optional[str]      # Es. "00071"
    data_ora_cedolino: Optional[str]    # Es. "31-12-2025 14:30" o "31-12-2025"
```

### Pattern di Estrazione

**Numero Cedolino:**
```python
# Pattern: "Nr. 00071" oppure "Numero 00071"
numero_match = re.search(r'(?:Nr\.|Numero)\s*[:\s]*(\d+)', text, re.IGNORECASE)
if numero_match:
    data['numero_cedolino'] = numero_match.group(1)  # "00071"
```

**Data/Ora Cedolino:**
```python
# Pattern 1: Timestamp completo "DD-MM-YYYY HH:MM"
datetime_match = re.search(r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2})', text)
if datetime_match:
    data['data_ora_cedolino'] = f"{datetime_match.group(1)} {datetime_match.group(2)}"
    # Risultato: "31-12-2025 14:30"

# Pattern 2: Solo data "DD-MM-YYYY"
date_only_match = re.search(r'Prot\.\s*(\d{2}-\d{2}-\d{4})', text)
if date_only_match:
    data['data_ora_cedolino'] = date_only_match.group(1)
    # Risultato: "31-12-2025"
```

## 🔍 Stato Attuale

### Attributi Salvati nel DB

Attualmente l'importer salva solo questi attributi:

```python
attributi_config = [
    ('anno_riferimento', 'Anno riferimento', 'int', anno),
    ('mese_riferimento', 'Mese riferimento', 'int', mese),
    ('mensilita', 'Mensilità', 'str', mensilita),
    ('dipendente', 'Dipendente', 'str', f"{cognome} {nome}"),
]
```

**❌ Problema**: `numero_cedolino` e `data_ora_cedolino` **NON** vengono salvati come attributi!

### Logica Duplicazione Documentata (FEATURE_CEDOLINI_DUPLICATI_E_PATTERN_ATTRIBUTI.md)

La documentazione descrive un sistema basato su:
- Stesso tipo (BPAG)
- Stesso cliente
- Stesso anno
- Stesso dipendente
- Stesso mese
- Stessa mensilità

**❌ Non corrisponde al requisito**: mancano numero e data/ora cedolino

## ✅ Soluzione Proposta

### 1. Aggiungere Attributi Mancanti

Modificare `_create_attributi()` in `documenti/importers/cedolini.py`:

```python
def _create_attributi(self, documento, tipo_bpag, anno, mese, mensilita, parsed_data):
    """Crea AttributoValore per il documento"""
    
    # Estrai numero e data/ora dal parsed_data
    numero_cedolino = parsed_data['cedolino'].get('numero_cedolino')
    data_ora_cedolino = parsed_data['cedolino'].get('data_ora_cedolino')
    
    attributi_config = [
        ('anno_riferimento', 'Anno riferimento', 'int', anno),
        ('mese_riferimento', 'Mese riferimento', 'int', mese),
        ('mensilita', 'Mensilità', 'str', mensilita),
        ('dipendente', 'Dipendente', 'str', 
         f"{parsed_data['lavoratore']['cognome']} {parsed_data['lavoratore']['nome']}"),
        
        # ✅ NUOVI ATTRIBUTI per duplicazione
        ('numero_cedolino', 'Numero cedolino', 'str', numero_cedolino),
        ('data_ora_cedolino', 'Data/Ora cedolino', 'str', data_ora_cedolino),
    ]
    
    for codice, nome, tipo_campo, valore in attributi_config:
        # Salta se valore è None (attributi opzionali)
        if valore is None:
            continue
            
        definizione, _ = AttributoDefinizione.objects.get_or_create(
            tipo_documento=tipo_bpag,
            codice=codice,
            defaults={'nome': nome, 'tipo': tipo_campo, 'obbligatorio': False}
        )
        
        AttributoValore.objects.create(
            documento=documento,
            definizione=definizione,
            valore=str(valore)
        )
```

### 2. Implementare `_trova_documento_esistente()`

Aggiungere metodo nell'importer:

```python
def _trova_documento_esistente(
    self, 
    cliente: Cliente, 
    numero_cedolino: Optional[str],
    data_ora_cedolino: Optional[str]
) -> Optional[Documento]:
    """
    Cerca documento cedolino esistente basato su numero e data/ora.
    
    Criteri di duplicazione:
    1. PRIORITÀ ALTA: numero_cedolino E data_ora_cedolino (se entrambi presenti)
    2. FALLBACK: solo numero_cedolino (se data/ora mancante)
    
    Args:
        cliente: Cliente (datore di lavoro)
        numero_cedolino: Numero del cedolino (es. "00071")
        data_ora_cedolino: Data/Ora cedolino (es. "31-12-2025 14:30")
        
    Returns:
        Documento esistente o None
    """
    if not numero_cedolino and not data_ora_cedolino:
        # Nessun criterio di ricerca disponibile
        return None
    
    # Query base: tipo BPAG + cliente
    documenti = Documento.objects.filter(
        tipo__codice='BPAG',
        cliente=cliente
    ).prefetch_related('attributi__definizione')
    
    # Cerca nei documenti esistenti
    for doc in documenti:
        # Costruisci dizionario attributi
        attributi = {
            attr.definizione.codice: attr.valore 
            for attr in doc.attributi.all()
        }
        
        doc_numero = attributi.get('numero_cedolino')
        doc_data_ora = attributi.get('data_ora_cedolino')
        
        # CASO 1: Entrambi i campi presenti → match esatto
        if numero_cedolino and data_ora_cedolino:
            if doc_numero == numero_cedolino and doc_data_ora == data_ora_cedolino:
                logger.info(
                    f"Duplicato trovato: Doc {doc.id} - "
                    f"Nr. {numero_cedolino}, Data/Ora {data_ora_cedolino}"
                )
                return doc
        
        # CASO 2: Solo numero presente → match su numero
        elif numero_cedolino and not data_ora_cedolino:
            if doc_numero == numero_cedolino:
                logger.info(
                    f"Duplicato trovato (solo numero): Doc {doc.id} - Nr. {numero_cedolino}"
                )
                return doc
        
        # CASO 3: Solo data/ora presente → match su data/ora
        elif data_ora_cedolino and not numero_cedolino:
            if doc_data_ora == data_ora_cedolino:
                logger.info(
                    f"Duplicato trovato (solo data/ora): Doc {doc.id} - {data_ora_cedolino}"
                )
                return doc
    
    return None
```

### 3. Integrare nel Flusso di Creazione

Modificare `create_documento()`:

```python
@transaction.atomic
def create_documento(self, parsed_data, valori_editati, user, **kwargs):
    """Crea documento cedolino con verifica duplicazione"""
    
    # ... codice esistente per cliente, anagrafica, titolario ...
    
    # ✅ Estrai campi per duplicazione
    numero_cedolino = parsed_data['cedolino'].get('numero_cedolino')
    data_ora_cedolino = parsed_data['cedolino'].get('data_ora_cedolino')
    
    # ✅ Verifica duplicazione
    duplicate_policy = kwargs.get('duplicate_policy', 'skip')
    
    if duplicate_policy != 'add':  # Se policy NON è "aggiungi comunque"
        doc_esistente = self._trova_documento_esistente(
            cliente=cliente,
            numero_cedolino=numero_cedolino,
            data_ora_cedolino=data_ora_cedolino
        )
        
        if doc_esistente:
            if duplicate_policy == 'skip':
                logger.warning(
                    f"Cedolino duplicato (Nr. {numero_cedolino}, "
                    f"Data/Ora {data_ora_cedolino}). Saltato."
                )
                raise ValueError(
                    f"Documento già esistente: {doc_esistente.codice}. "
                    f"Nr. cedolino: {numero_cedolino}"
                )
            
            elif duplicate_policy == 'replace':
                logger.info(
                    f"Sostituzione documento {doc_esistente.id} - "
                    f"Nr. {numero_cedolino}"
                )
                doc_esistente.delete()
    
    # Crea nuovo documento
    documento = Documento.objects.create(...)
    
    # ✅ Salva attributi includendo numero e data/ora
    self._create_attributi(documento, tipo_bpag, anno, mese, mensilita, parsed_data)
    
    return documento
```

### 4. Aggiornare Valori Editabili

Nel metodo `parse_document()`, includere nei valori editabili:

```python
valori_editabili = {
    'periodo': parsed['cedolino']['periodo'],
    'anno': parsed['cedolino']['anno'],
    'mese': parsed['cedolino']['mese'],
    'mensilita': parsed['cedolino']['mensilita'],
    'netto': str(parsed['cedolino']['netto']) if parsed['cedolino']['netto'] else None,
    
    # ✅ NUOVO: Permetti modifica numero e data/ora prima di conferma
    'numero_cedolino': parsed['cedolino'].get('numero_cedolino'),
    'data_ora_cedolino': parsed['cedolino'].get('data_ora_cedolino'),
}
```

## 🎯 Vantaggi della Soluzione

### 1. **Precisione Massima**
- Match su **numero cedolino** univoco
- Timestamp preciso per distinguere ristampe/versioni

### 2. **Flessibilità**
- Funziona anche se solo uno dei due campi è presente
- Fallback intelligente: numero → data/ora → skip

### 3. **Retrocompatibilità**
- Nuovi attributi opzionali (non obbligatori)
- Documenti esistenti non vengono invalidati

### 4. **UI User-Friendly**
- Numero e data/ora visibili nella preview
- Modificabili prima della conferma import
- Messaggi chiari su documenti duplicati

## 📋 Casistiche Gestite

| Caso | Numero | Data/Ora | Comportamento |
|------|--------|----------|---------------|
| 1 | ✅ | ✅ | Match esatto su entrambi (MIGLIORE) |
| 2 | ✅ | ❌ | Match solo su numero |
| 3 | ❌ | ✅ | Match solo su data/ora |
| 4 | ❌ | ❌ | Nessuna verifica duplicati (richiede policy 'add') |
| 5 | ✅ | ✅ (diverso) | NON duplicato (numero uguale ma timestamp diverso = ristampa) |

## ⚠️ Edge Cases

### Caso 1: Ristampa Cedolino
```
Cedolino A: Nr. 00071, Data/Ora 31-12-2025 14:30
Cedolino B: Nr. 00071, Data/Ora 31-12-2025 16:45
```
**Risultato**: NON duplicato (timestamp diverso)

### Caso 2: PDF Senza Numero
```
Cedolino A: Nr. NULL, Data/Ora 31-12-2025 14:30
Cedolino B: Nr. NULL, Data/Ora 31-12-2025 14:30
```
**Risultato**: Duplicato (match su data/ora)

### Caso 3: PDF Senza Data/Ora
```
Cedolino A: Nr. 00071, Data/Ora NULL
Cedolino B: Nr. 00071, Data/Ora NULL
```
**Risultato**: Duplicato (match su numero)

## 🔄 Migrazione Dati Esistenti

Per documenti già importati senza numero/data_ora:

```python
# Script migrazione (opzionale)
from documenti.models import Documento
from documenti.parsers.cedolino_parser import parse_cedolino_pdf

for doc in Documento.objects.filter(tipo__codice='BPAG'):
    if doc.file and not doc.attributi.filter(definizione__codice='numero_cedolino').exists():
        try:
            # Re-parse PDF per estrarre numero/data_ora
            parsed = parse_cedolino_pdf(doc.file.path)
            
            numero = parsed['cedolino'].get('numero_cedolino')
            data_ora = parsed['cedolino'].get('data_ora_cedolino')
            
            # Crea attributi mancanti
            # ... (codice creazione attributi)
            
        except Exception as e:
            logger.warning(f"Skip doc {doc.id}: {e}")
```

## 📝 Modifiche Necessarie

### File da Modificare

1. **`documenti/importers/cedolini.py`**
   - ✅ Aggiungere attributi `numero_cedolino` e `data_ora_cedolino` in `_create_attributi()`
   - ✅ Implementare `_trova_documento_esistente()`
   - ✅ Integrare verifica in `create_documento()`
   - ✅ Aggiornare `valori_editabili` in `parse_document()`

2. **`api/v1/documenti/serializers.py`** (se esistente)
   - Aggiungere campi `numero_cedolino` e `data_ora_cedolino` in `valori_editabili`

3. **Frontend React** (opzionale ma consigliato)
   - Mostrare numero e data/ora nella preview
   - Permettere modifica prima della conferma

### Testing

```python
# Test case 1: Duplicato esatto
doc1 = create_cedolino(nr="00071", dt="31-12-2025 14:30")
doc2_attempt = create_cedolino(nr="00071", dt="31-12-2025 14:30")
# Expected: ValueError (duplicato)

# Test case 2: Ristampa (numero uguale, data/ora diversa)
doc1 = create_cedolino(nr="00071", dt="31-12-2025 14:30")
doc2 = create_cedolino(nr="00071", dt="31-12-2025 16:45")
# Expected: OK (non duplicato)

# Test case 3: Solo numero match
doc1 = create_cedolino(nr="00071", dt=None)
doc2_attempt = create_cedolino(nr="00071", dt=None)
# Expected: ValueError (duplicato)
```

## 🎯 Conclusione

La soluzione proposta:
- ✅ Implementa il criterio richiesto (numero + data/ora)
- ✅ Gestisce tutti i casi edge
- ✅ Mantiene flessibilità con 3 policy
- ✅ Retrocompatibile con dati esistenti
- ✅ Estensibile per futuri requisiti

**Prossimo step**: Implementare le modifiche nel codice
