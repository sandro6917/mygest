# Analisi Sistema Titolario Cedolini

## 📋 Panoramica

Il sistema di importazione **Cedolini** implementa una **gestione gerarchica avanzata del titolario** con creazione automatica di voci personalizzate per ogni dipendente.

---

## 🏗️ Struttura Gerarchica Titolario Cedolini

### Schema Completo
```
HR-PERS (Personale - Voce Radice)
  └── {CODICE_ANAGRAFICA} (es. ROSMAR01 - Voce Dipendente)
        └── PAG (Paghe - Voce Finale)
```

### Esempio Pratico
```
HR-PERS
  ├── ROSMAR01 (Rossi Mario)
  │     └── PAG → QUI vanno i cedolini di Rossi Mario
  ├── BNCGVN02 (Bianchi Giovanni)
  │     └── PAG → QUI vanno i cedolini di Bianchi Giovanni
  └── ...
```

---

## 🔧 Implementazione - Metodo `_get_or_create_titolario_dipendente()`

### File
`documenti/importers/cedolini.py` - **Righe 641-702**

### Firma Metodo
```python
def _get_or_create_titolario_dipendente(
    self, 
    anagrafica_dipendente: Anagrafica
) -> TitolarioVoce:
```

### Flusso Completo

#### **Step 1: Verifica/Crea Voce Radice HR-PERS**
```python
# Riga 658-663
try:
    voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
except TitolarioVoce.DoesNotExist:
    logger.error("Voce titolario HR-PERS non trovata! Crearla manualmente.")
    # Fallback: usa voce di default
    from documenti.models import get_or_create_default_titolario
    return get_or_create_default_titolario()
```

**Logica**:
- ✅ Cerca voce `HR-PERS` (Personale) nel sistema
- ❌ Se NON esiste → **FALLBACK** a voce generica `99 - Varie`
- ⚠️ Log ERROR: deve essere creata manualmente

#### **Step 2: Genera Codice Anagrafica Dipendente**
```python
# Riga 666
from anagrafiche.utils import get_or_generate_cli
codice_dipendente = get_or_generate_cli(anagrafica_dipendente)
```

**Utility `get_or_generate_cli()`**:
- Se anagrafica ha già `codice` → lo usa
- Se NON ha codice → lo **genera automaticamente** con algoritmo:
  - **PF (Persona Fisica)**: `COGNOME[0:6]NOME[0:2]` (6+2 caratteri)
    - Esempio: `Rossi Mario` → `ROSMAR01`
  - **PG (Persona Giuridica)**: `RAGSOC[0:6]XX` (6+2 caratteri)
- Gestisce **unicità** con progressivo se codice già esistente

#### **Step 3: Crea Sottovoce Dipendente (HR-PERS/CODICE)**
```python
# Riga 669-678
voce_dipendente, created = TitolarioVoce.objects.get_or_create(
    codice=codice_dipendente,  # es. ROSMAR01
    parent=voce_hr_pers,       # Padre: HR-PERS
    defaults={
        'titolo': f"{anagrafica_dipendente.cognome} {anagrafica_dipendente.nome}",
        'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
    }
)

if created:
    logger.info(f"Creata voce titolario dipendente: {voce_dipendente.codice} - {voce_dipendente.titolo}")
```

**Campi Voce Dipendente**:
- `codice`: `ROSMAR01`
- `parent`: `HR-PERS`
- `titolo`: `"Rossi Mario"`
- `pattern_codice`: Pattern per generazione codice documento

**Comportamento**:
- ✅ Se esiste già → la recupera (idempotente)
- ✅ Se NON esiste → la crea e logga

#### **Step 4: Crea Sottovoce PAG (HR-PERS/CODICE/PAG)**
```python
# Riga 682-697
voce_pag, created = TitolarioVoce.objects.get_or_create(
    codice='PAG',              # Sempre 'PAG'
    parent=voce_dipendente,    # Padre: ROSMAR01
    defaults={
        'titolo': 'Paghe',
        'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
    }
)

if created:
    logger.info(
        f"Creata voce titolario PAG per {codice_dipendente}: "
        f"{voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_pag.codice}"
    )

logger.debug(
    f"Titolario cedolino: {voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_pag.codice}"
)
```

**Campi Voce PAG**:
- `codice`: `PAG` (fisso)
- `parent`: `voce_dipendente` (es. ROSMAR01)
- `titolo`: `"Paghe"`
- `pattern_codice`: Pattern per codice documento

**Comportamento**:
- ✅ Se esiste già → la recupera
- ✅ Se NON esiste → la crea e logga path completo

#### **Step 5: Return Voce Finale**
```python
# Riga 701
return voce_pag  # HR-PERS/ROSMAR01/PAG
```

**Voce restituita**: La foglia `PAG` che sarà assegnata al documento cedolino.

---

## 🎯 Utilizzo nel `create_documento()`

### File
`documenti/importers/cedolini.py` - **Righe 429-433**

```python
# **NUOVO: Crea automaticamente anagrafica dipendente se non esiste**
anagrafica_dipendente = self._create_or_get_dipendente_anagrafica(parsed_data['lavoratore'])

# Titolario: Gerarchia HR-PERS/{CODICE_DIPENDENTE}/PAG
# Esempio: HR-PERS/ROSMAR01/PAG
titolario = self._get_or_create_titolario_dipendente(anagrafica_dipendente)
```

### Assegnazione al Documento
```python
# Riga 497
documento = Documento.objects.create(
    tipo=tipo_bpag,
    cliente=cliente,
    fascicolo=fascicolo,
    titolario_voce=titolario,  # ← Voce PAG assegnata qui
    descrizione=f"Cedolino {cognome} {nome} - {periodo}",
    # ... altri campi
)
```

---

## 🔄 Metodo Helper `_create_or_get_dipendente_anagrafica()`

### File
`documenti/importers/cedolini.py` - **Righe 581-640**

### Flusso
```python
def _create_or_get_dipendente_anagrafica(self, lavoratore_data: Dict) -> Anagrafica:
    cf = lavoratore_data['codice_fiscale']
    
    # 1. Cerca per CF (case-insensitive)
    try:
        anagrafica = Anagrafica.objects.get(codice_fiscale__iexact=cf)
        logger.info(f"Anagrafica dipendente già esistente: {anagrafica.display_name}")
        return anagrafica
    except Anagrafica.DoesNotExist:
        pass
    except Anagrafica.MultipleObjectsReturned:
        # Se duplicati, usa il primo
        anagrafica = Anagrafica.objects.filter(codice_fiscale__iexact=cf).first()
        logger.warning(f"Trovate anagrafiche duplicate per CF {cf}, uso ID {anagrafica.id}")
        return anagrafica
    
    # 2. Crea nuova anagrafica PF
    cognome = lavoratore_data.get('cognome', '').strip().upper()
    nome = lavoratore_data.get('nome', '').strip().upper()
    
    anagrafica = Anagrafica.objects.create(
        tipo='PF',  # Persona Fisica
        codice_fiscale=cf.upper(),
        cognome=cognome,
        nome=nome,
        ragione_sociale='',  # Vuoto per PF
    )
    
    logger.info(f"Creata nuova anagrafica dipendente: {anagrafica.display_name} (CF: {cf})")
    
    return anagrafica
```

**Comportamento**:
- ✅ **Idempotente**: cerca prima, crea solo se necessario
- ✅ **Gestisce duplicati**: usa primo se multipli CF
- ✅ **Auto-creazione**: dipendente non serve pre-esistere

---

## 🛡️ Fallback - `get_or_create_default_titolario()`

### File
`documenti/models.py` - **Righe 34-48**

### Implementazione
```python
def get_or_create_default_titolario() -> TitolarioVoce:
    """
    Ottiene o crea la voce di titolario di default '99 - Varie'
    per documenti senza classificazione specifica.
    """
    default_voce, created = TitolarioVoce.objects.get_or_create(
        codice="99",
        parent=None,  # Voce radice
        defaults={
            "titolo": "Varie",
            "pattern_codice": "{CLI}-{TIT}-{ANNO}-{SEQ:03d}"
        }
    )
    if created:
        logger.info("Creata voce di titolario default: 99 - Varie")
    return default_voce
```

**Uso**:
- ⚠️ Chiamato quando `HR-PERS` NON esiste
- ✅ Crea voce generica `99 - Varie` come safety net
- ✅ Permette importazione anche senza titolario configurato

---

## 📊 Diagramma Flusso Completo

```
┌─────────────────────────────────────────┐
│ create_documento(parsed_data, ...)     │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ _create_or_get_dipendente_anagrafica()  │
│ → Cerca/Crea anagrafica lavoratore      │
│ → Return: Anagrafica                    │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│ _get_or_create_titolario_dipendente()   │
└─────────────────┬───────────────────────┘
                  │
                  ├─► 1. Verifica HR-PERS
                  │   ├─ Esiste? → Usa
                  │   └─ NON esiste? → Fallback "99 - Varie"
                  │
                  ├─► 2. Genera codice dipendente
                  │   └─ get_or_generate_cli(anagrafica)
                  │       → ROSMAR01
                  │
                  ├─► 3. get_or_create voce dipendente
                  │   └─ HR-PERS/ROSMAR01
                  │       Titolo: "Rossi Mario"
                  │
                  ├─► 4. get_or_create voce PAG
                  │   └─ HR-PERS/ROSMAR01/PAG
                  │       Titolo: "Paghe"
                  │
                  └─► 5. Return voce_pag
                  
                  ▼
┌─────────────────────────────────────────┐
│ Documento.objects.create(              │
│   titolario_voce=voce_pag,  ← Assegnato│
│   ...                                   │
│ )                                       │
└─────────────────────────────────────────┘
```

---

## 🎯 Caratteristiche Chiave

### ✅ Vantaggi
1. **Gerarchia Automatica**: Crea struttura completa senza intervento manuale
2. **Idempotente**: Chiamate multiple = stesso risultato (no duplicati)
3. **Personalizzazione**: Ogni dipendente ha la propria sottovoce
4. **Organizzazione**: Tutti i cedolini di un dipendente sotto stesso path
5. **Fallback Robusto**: Se HR-PERS manca → usa "99 - Varie"
6. **Logging Completo**: Traccia creazioni e recuperi

### ⚙️ Meccanismi
- **get_or_create**: Pattern Django per idempotenza
- **get_or_generate_cli()**: Utility per codici univoci anagrafica
- **Gerarchia Parent-Child**: TitolarioVoce.parent per albero
- **Pattern Codice**: Template dinamico per generazione codici documento

### 🔒 Safety
- ✅ Transaction atomica in `create_documento()`
- ✅ Try-catch per gestione errori
- ✅ Fallback a voce default se HR-PERS mancante
- ✅ Logging errori per debug

---

## 📦 Dipendenze

### Modelli
- `TitolarioVoce` (titolario.models)
- `Anagrafica` (anagrafiche.models)
- `Documento` (documenti.models)

### Utility
- `get_or_generate_cli()` (anagrafiche.utils)
- `get_or_create_default_titolario()` (documenti.models)

### Pattern Django
- `get_or_create()` - Idempotenza
- `get()` + try-catch - Gestione esistenza
- `objects.filter().first()` - Gestione multipli

---

## 🔑 Prerequisiti Sistema

### Obbligatori per Funzionamento Completo
1. **Voce Titolario `HR-PERS`** deve esistere nel sistema
   - Codice: `HR-PERS`
   - Titolo: `"Personale"` (o simile)
   - Parent: `None` (radice)

### Opzionali (Fallback Automatico)
- Se `HR-PERS` manca → usa `99 - Varie` (creato automaticamente)

### Script Setup Consigliato
```python
# Migration o script management command
from titolario.models import TitolarioVoce

# Crea voce radice HR-PERS se non esiste
TitolarioVoce.objects.get_or_create(
    codice='HR-PERS',
    parent=None,
    defaults={
        'titolo': 'Personale',
        'descrizione': 'Gestione risorse umane e personale',
        'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
    }
)
```

---

## 🎓 Esempio Completo End-to-End

### Input
```python
parsed_data = {
    'lavoratore': {
        'codice_fiscale': 'RSSMRA80A01H501X',
        'cognome': 'ROSSI',
        'nome': 'MARIO',
    },
    'cedolino': {
        'anno': 2024,
        'mese': 1,
        'mensilita': '1/2024',
        # ...
    }
}
```

### Esecuzione
```python
importer = CedoliniImporter(session)

# Step 1: Crea/Recupera anagrafica dipendente
anagrafica = importer._create_or_get_dipendente_anagrafica(parsed_data['lavoratore'])
# → Anagrafica(id=123, cf='RSSMRA80A01H501X', cognome='ROSSI', nome='MARIO')
# → Codice auto-generato: 'ROSMAR01'

# Step 2: Crea/Recupera titolario
titolario = importer._get_or_create_titolario_dipendente(anagrafica)
# → TitolarioVoce(codice='PAG', parent__codice='ROSMAR01', parent__parent__codice='HR-PERS')
# → Path completo: HR-PERS/ROSMAR01/PAG

# Step 3: Crea documento
documento = Documento.objects.create(
    titolario_voce=titolario,  # HR-PERS/ROSMAR01/PAG
    cliente=cliente_datore,
    descrizione="Cedolino Rossi Mario - Gennaio 2024",
    # ...
)
```

### Output Database
```
Tabella: titolario_titolarvoce
┌────┬─────────┬──────────┬──────────────┬─────────────────┐
│ id │ codice  │ parent_id│ titolo       │ pattern_codice  │
├────┼─────────┼──────────┼──────────────┼─────────────────┤
│ 1  │ HR-PERS │ NULL     │ Personale    │ {CLI}-{TIT}-... │
│ 2  │ ROSMAR01│ 1        │ Rossi Mario  │ {CLI}-{TIT}-... │
│ 3  │ PAG     │ 2        │ Paghe        │ {CLI}-{TIT}-... │
└────┴─────────┴──────────┴──────────────┴─────────────────┘

Tabella: documenti_documento
┌────┬────────────┬──────────────────┬─────────────────┬──────────────┐
│ id │ codice     │ titolario_voce_id│ descrizione     │ cliente_id   │
├────┼────────────┼──────────────────┼─────────────────┼──────────────┤
│ 10 │ CLI-PAG-...│ 3                │ Cedolino Rossi..│ 5            │
└────┴────────────┴──────────────────┴─────────────────┴──────────────┘
```

---

## 📝 Conclusioni

Il sistema Cedolini implementa una **gestione titolario gerarchica automatizzata** che:

1. ✅ **Auto-crea struttura completa** HR-PERS → Dipendente → PAG
2. ✅ **Idempotente**: safe per chiamate multiple
3. ✅ **Robusto**: fallback a "99 - Varie" se HR-PERS manca
4. ✅ **Organizzato**: ogni dipendente ha la propria classificazione
5. ✅ **Scalabile**: gestisce N dipendenti senza configurazione manuale

Questo pattern è **riutilizzabile per UNILAV** con adattamenti minimi.

---

**File Analizzati**:
- `documenti/importers/cedolini.py` (righe 429-433, 581-702)
- `documenti/models.py` (righe 34-48)
- `anagrafiche/utils.py` (get_or_generate_cli)

**Data Analisi**: 6 Febbraio 2026  
**Versione**: 1.0
