# Analisi Estrazione Certificazioni Uniche (CU) con Template AI

**Data**: 16 Marzo 2026  
**Versione**: 1.0  
**Obiettivo**: Verificare e migliorare l'estrazione dati CU usando il template AI configurato

---

## 📊 Situazione Attuale

### Template AI Configurato

**Nome**: `CU Dipendenti/Pensionati`  
**Tipo Documento**: CU (Certificazione Unica)  
**Stato**: Attivo ✓  
**Priorità**: 0

#### Zone Definite (9/9)

| # | Nome Campo | Etichetta | Tipo Dato | Obbligatorio | Mapping |
|---|-----------|-----------|-----------|--------------|----------|
| 1 | `anno_presentazione` | Anno presentazione | int | ✓ | ❌ NO |
| 2 | `anno_imposta` | Anno di imposta | int | ✓ | ❌ NO |
| 3 | `codice_fiscale_datore` | Codice fiscale datore di lavoro | text | ✓ | ✓ SI |
| 4 | `denominazione_datore` | Denominazione datore | text | - | ❌ NO |
| 5 | `nome_datore` | Nome Datore di lavoro | text | - | ❌ NO |
| 6 | `codice_fiscale_lavoratore` | Codice fiscale Lavoratore | text | ✓ | ✓ SI |
| 7 | `cognome_lavoratore` | Cognome Lavoratore | text | - | ❌ NO |
| 8 | `nome_lavoratore` | Nome Lavoratore | text | - | ❌ NO |
| 9 | `data_comunicazione` | Data Comunicazione | date | - | ✓ SI |

**Copertura Mapping**: **3/9 campi** (33%)

#### Mapping Configurati (3)

```
✓ codice_fiscale_datore
  → field: cliente.anagrafica.codice_fiscale

✓ codice_fiscale_lavoratore  
  → attribute: attributi.dipendente

✓ data_comunicazione
  → field: data_documento
```

#### Zone SENZA Mapping (6)

⚠️ **Campi estratti ma non salvati**:
- `anno_imposta` (obbligatorio!)
- `anno_presentazione` (obbligatorio!)
- `denominazione_datore`
- `nome_datore`
- `cognome_lavoratore`
- `nome_lavoratore`

---

## 🧪 Test Estrazione Attuale

### Parser CU Manuale (cu_parser.py)

**File Test**: `MRVLSN65P17E875J - 2025 - MORVIDUCCI ALESSANDRO.pdf`

**Risultato**:

```
=== SOSTITUTO (Datore di Lavoro) ===
CF: 01713960530 ✓
Denominazione: (non trovata) ❌
P.IVA: 01713960530 ✓
Sede: Grosseto GR ✓

=== PERCIPIENTE (Lavoratore) ===
CF: MRVLSN65P17E875J ✓
Nome:  Datasdisnascita Datasassunzione Datascessazione ❌ (parsing errato)
Nato il: 29-01-2009 ❌ (dato errato)

=== DATI FISCALI CU ===
Anno riferimento: 2025 ✓
Tipo certificazione: (non trovata) ❌
Ritenute IRPEF: 34,44 ✓
```

**Campi Estratti Correttamente (6/12)**: 50% di successo

---

## ❌ Problemi Rilevati

### 1. Template AI Incompleto

**Problema**: Solo **3 campi su 9** hanno mapping configurato

**Impatto**:  
- 6 campi vengono estratti dalle zone ma **non salvati** nel database
- `anno_imposta` è obbligatorio ma non viene mappato → **dato critico perso**
- Nome/cognome lavoratore non vengono salvati → perde informazioni anagrafiche

**Esempio Concreto**:
```
Template estrae:
  - anno_imposta: 2025 ✓
  - cognome_lavoratore: "MORVIDUCCI" ✓
  - nome_lavoratore: "ALESSANDRO" ✓

Importer salva:
  - anno_imposta: ❌ NON SALVATO (no mapping)
  - cognome_lavoratore: ❌ NON SALVATO (no mapping)  
  - nome_lavoratore: ❌ NON SALVATO (no mapping)
```

### 2. Mapping CF Lavoratore Errato

**Configurazione Attuale**:
```
codice_fiscale_lavoratore → attribute: attributi.dipendente
```

**Problema**:  
Salva **solo il CF come attributo**, non crea l'anagrafica del lavoratore

**Comportamento Corretto Richiesto**:
```python
1. Cerca Anagrafica con CF lavoratore
2. Se NON esiste:
   - Crea Anagrafica PF con:
     * codice_fiscale = "MRVLSN65P17E875J"
     * cognome = da zona "cognome_lavoratore"
     * nome = da zona "nome_lavoratore"
     * tipo = "PF"
3. Salva riferimento Anagrafica nel documento (NON come attributo)
```

### 3. Mapping CF Datore Incompleto

**Configurazione Attuale**:
```
codice_fiscale_datore → field: cliente.anagrafica.codice_fiscale
```

**Problema**:  
Presume che il **Cliente esista già**. Se non esiste → errore importazione

**Comportamento Corretto Richiesto**:
```python
1. Determina tipo CF datore:
   - 16 caratteri → Persona Fisica (PF)
   - 11 cifre → Persona Giuridica (PG)

2. Cerca Cliente con:
   - anagrafica.codice_fiscale = CF_datore

3. Se NON esiste:
   a) Crea Anagrafica (PF o PG):
      * codice_fiscale = CF_datore
      * denominazione/ragione_sociale = da zona "denominazione_datore" (se PG)
      * nome + cognome = da zone "nome_datore" (se PF)
      * tipo = "PF" o "PG"
   
   b) Crea Cliente:
      * anagrafica = anagrafica appena creata
      * codice_cliente = generato automaticamente
      * attivo = True

4. Usa Cliente nel documento
```

### 4. Parser Manuale Impreciso

**Problemi Rilevati**:
- Denominazione datore non estratta
- Nome percipiente estratto in modo confuso (pattern regex sbagliati)
- Data nascita errata (parsing posizionale)
- Tipo certificazione non trovato

**Causa**:  
Il parser `cu_parser.py` usa **regex e pattern posizionali** che funzionano solo con formati CU molto specifici.

**Template AI Vantaggio**:  
Le **zone con coordinate** estraggono dati da posizioni precise nel PDF → più affidabile

---

## ✅ Soluzione Proposta

### FASE 1: Completare Mapping Template AI

Aggiungere mapping per i **6 campi mancanti**:

```python
# Da configurare in Django Admin (/admin/ai_classifier/extractionfieldmapping/)

# 1. Anno imposta → Attributo
ExtractionFieldMapping.objects.create(
    template=template_cu,
    nome_campo_template='anno_imposta',
    tipo_campo_destinazione='attribute',
    nome_campo_destinazione='attributi.anno_riferimento'
)

# 2. Anno presentazione → Attributo
ExtractionFieldMapping.objects.create(
    template=template_cu,
    nome_campo_template='anno_presentazione',
    tipo_campo_destinazione='attribute',
    nome_campo_destinazione='attributi.anno_presentazione'
)

# 3. Denominazione datore → Campo Anagrafica
ExtractionFieldMapping.objects.create(
    template=template_cu,
    nome_campo_template='denominazione_datore',
    tipo_campo_destinazione='field',
    nome_campo_destinazione='cliente.anagrafica.denominazione'
)

# 4. Nome datore → Campo Anagrafica (PF)
ExtractionFieldMapping.objects.create(
    template=template_cu,
    nome_campo_template='nome_datore',
    tipo_campo_destinazione='field',
    nome_campo_destinazione='cliente.anagrafica.nome'
)

# 5. Cognome lavoratore → Attributo (per creazione anagrafica)
ExtractionFieldMapping.objects.create(
    template=template_cu,
    nome_campo_template='cognome_lavoratore',
    tipo_campo_destinazione='attribute',
    nome_campo_destinazione='attributi.dipendente_cognome'
)

# 6. Nome lavoratore → Attributo (per creazione anagrafica)
ExtractionFieldMapping.objects.create(
    template=template_cu,
    nome_campo_template='nome_lavoratore',
    tipo_campo_destinazione='attribute',
    nome_campo_destinazione='attributi.dipendente_nome'
)
```

### FASE 2: Modificare CertificazioniUnicheImporter

**File**: `/home/sandro/mygest/documenti/importers/certificazioni_uniche.py`

#### 2.1 Integrare DataExtractionService

```python
from api.v1.ai_classifier.views_ai_import import DataExtractionService

class CertificazioniUnicheImporter(BaseImporter):
    
    def parse_document(self, file_path: str, file_info: Dict[str, Any]) -> ParseResult:
        """
        Parsing usando template AI invece di cu_parser.py
        """
        try:
            # 1. Carica template AI
            template = DocumentExtractionTemplate.objects.get(
                tipo_documento__codice='CU',
                attivo=True
            )
            
            # 2. Estrai dati con servizio AI
            service = DataExtractionService()
            extraction_result = service.extract_from_template(
                file_path=file_path,
                template=template
            )
            
            if not extraction_result['estrazione_completa']:
                return ParseResult(
                    success=False,
                    error_message="Estrazione incompleta: campi obbligatori mancanti",
                    parsed_data={},
                    anagrafiche_reperite=[],
                    valori_editabili={},
                    mappatura_db={}
                )
            
            # 3. Converti campi estratti in dizionario
            dati = {}
            for campo in extraction_result['campi_estratti']:
                dati[campo['nome_campo']] = campo['valore']
            
            # 4. Gestisci DATORE DI LAVORO (Cliente)
            cf_datore = dati['codice_fiscale_datore']
            cliente = self._crea_o_trova_cliente_datore(dati)
            
            # 5. Gestisci LAVORATORE (Anagrafica)
            anagrafica_dipendente = self._crea_o_trova_anagrafica_lavoratore(dati)
            
            # 6. Prepara dati documento
            parsed_data = {
                'cliente_id': cliente.id,
                'anagrafica_dipendente_id': anagrafica_dipendente.id,
                'anno_riferimento': dati['anno_imposta'],
                'data_documento': dati.get('data_comunicazione'),
            }
            
            # 7. Prepara attributi dinamici
            attributi = {
                'anno_riferimento': dati['anno_imposta'],
                'anno_presentazione': dati.get('anno_presentazione'),
                'dipendente_cf': dati['codice_fiscale_lavoratore'],
                'dipendente_cognome': dati.get('cognome_lavoratore'),
                'dipendente_nome': dati.get('nome_lavoratore'),
            }
            
            return ParseResult(
                success=True,
                parsed_data=parsed_data,
                anagrafiche_reperite=[cliente.anagrafica, anagrafica_dipendente],
                valori_editabili={
                    'titolo': f"CU {dati['anno_imposta']} - {dati['cognome_lavoratore']} {dati['nome_lavoratore']}",
                    'note': f"Anno imposta: {dati['anno_imposta']}"
                },
                mappatura_db={
                    'tipo': 'CU',
                    'attributi': attributi,
                    'note_preview': f"CU anno {dati['anno_imposta']}"
                },
                error_message="",
                error_traceback=""
            )
            
        except Exception as e:
            logger.error(f"Errore parsing CU con template AI: {e}")
            return ParseResult(
                success=False,
                error_message=str(e),
                error_traceback=traceback.format_exc(),
                parsed_data={},
                anagrafiche_reperite=[],
                valori_editabili={},
                mappatura_db={}
            )
```

#### 2.2 Metodo Creazione Cliente Datore

```python
def _crea_o_trova_cliente_datore(self, dati: Dict[str, Any]) -> Cliente:
    """
    Trova o crea Cliente per datore di lavoro.
    
    Regole:
    - CF 16 caratteri → PF (usa nome_datore)
    - CF 11 cifre → PG (usa denominazione_datore)
    """
    from anagrafiche.models import Anagrafica, Cliente
    
    cf_datore = dati['codice_fiscale_datore']
    
    # 1. Cerca cliente esistente
    try:
        cliente = Cliente.objects.get(anagrafica__codice_fiscale=cf_datore)
        logger.info(f"Cliente datore trovato: {cliente}")
        return cliente
    except Cliente.DoesNotExist:
        pass
    
    # 2. Determina tipo anagrafica
    if len(cf_datore) == 16:
        tipo = 'PF'
        nome = dati.get('nome_datore', '')
        cognome = ''  # Separare da nome se necessario
        denominazione = None
    elif len(cf_datore) == 11:
        tipo = 'PG'
        nome = None
        cognome = None
        denominazione = dati.get('denominazione_datore') or 'DATORE DI LAVORO (da verificare)'
    else:
        raise ValueError(f"CF datore non valido: {cf_datore}")
    
    # 3. Crea Anagrafica
    anagrafica = Anagrafica.objects.create(
        codice_fiscale=cf_datore,
        tipo=tipo,
        nome=nome,
        cognome=cognome,
        denominazione=denominazione
    )
    logger.info(f"Anagrafica datore creata: {anagrafica}")
    
    # 4. Crea Cliente
    from anagrafiche.utils import genera_codice_cliente
    
    cliente = Cliente.objects.create(
        anagrafica=anagrafica,
        codice_cliente=genera_codice_cliente(anagrafica),
        attivo=True
    )
    logger.info(f"Cliente datore creato: {cliente}")
    
    return cliente


def _crea_o_trova_anagrafica_lavoratore(self, dati: Dict[str, Any]) -> Anagrafica:
    """
    Trova o crea Anagrafica PF per lavoratore dipendente.
    """
    from anagrafiche.models import Anagrafica
    
    cf_lavoratore = dati['codice_fiscale_lavoratore']
    
    # 1. Cerca anagrafica esistente
    try:
        anagrafica = Anagrafica.objects.get(codice_fiscale=cf_lavoratore)
        logger.info(f"Anagrafica lavoratore trovata: {anagrafica}")
        return anagrafica
    except Anagrafica.DoesNotExist:
        pass
    
    # 2. Crea nuova anagrafica PF
    anagrafica = Anagrafica.objects.create(
        codice_fiscale=cf_lavoratore,
        tipo='PF',
        cognome=dati.get('cognome_lavoratore', 'COGNOME_DA_VERIFICARE'),
        nome=dati.get('nome_lavoratore', 'NOME_DA_VERIFICARE')
    )
    logger.info(f"Anagrafica lavoratore creata: {anagrafica}")
    
    return anagrafica
```

### FASE 3: Aggiornare Attributi CU

**File**: Management command esistente o nuovo script

```python
# Assicurati che esistano questi AttributoDefinizione per tipo CU

AttributoDefinizione.objects.get_or_create(
    tipo_documento=tipo_cu,
    codice='anno_riferimento',
    defaults={
        'nome': 'Anno di Imposta',
        'tipo_dato': 'int',
        'obbligatorio': True,
        'ordine': 1
    }
)

AttributoDefinizione.objects.get_or_create(
    tipo_documento=tipo_cu,
    codice='anno_presentazione',
    defaults={
        'nome': 'Anno di Presentazione',
        'tipo_dato': 'int',
        'obbligatorio': False,
        'ordine': 2
    }
)

AttributoDefinizione.objects.get_or_create(
    tipo_documento=tipo_cu,
    codice='dipendente_cf',
    defaults={
        'nome': 'Codice Fiscale Dipendente',
        'tipo_dato': 'text',
        'obbligatorio': True,
        'ordine': 3
    }
)

AttributoDefinizione.objects.get_or_create(
    tipo_documento=tipo_cu,
    codice='dipendente_cognome',
    defaults={
        'nome': 'Cognome Dipendente',
        'tipo_dato': 'text',
        'obbligatorio': False,
        'ordine': 4
    }
)

AttributoDefinizione.objects.get_or_create(
    tipo_documento=tipo_cu,
    codice='dipendente_nome',
    defaults={
        'nome': 'Nome Dipendente',
        'tipo_dato': 'text',
        'obbligatorio': False,
        'ordine': 5
    }
)
```

---

## 📋 Piano di Implementazione

### Step 1: Configurazione Template (10 min)
- [ ] Accedere a `/admin/ai_classifier/extractionfieldmapping/`
- [ ] Aggiungere 6 mapping mancanti (vedi FASE 1)
- [ ] Verificare che tutti i 9 campi abbiano mapping

### Step 2: Modificare Importer (30 min)
- [ ] Backup file `certificazioni_uniche.py`
- [ ] Integrare `DataExtractionService` nel metodo `parse_document()`
- [ ] Implementare `_crea_o_trova_cliente_datore()`
- [ ] Implementare `_crea_o_trova_anagrafica_lavoratore()`
- [ ] Testare con file CU di esempio

### Step 3: Aggiornare Attributi (5 min)
- [ ] Eseguire script aggiornamento AttributoDefinizione
- [ ] Verificare attributi disponibili per tipo CU

### Step 4: Test E2E (15 min)
- [ ] Caricare ZIP con 3-5 CU di test
- [ ] Verificare preview dati estratti
- [ ] Confermare importazione
- [ ] Verificare:
  - ✓ Anagrafica datore creata (se non esisteva)
  - ✓ Cliente datore creato (se non esisteva)
  - ✓ Anagrafica lavoratore creata (se non esisteva)
  - ✓ Documento CU creato con 9 attributi
  - ✓ Relazioni corrette (cliente, dipendente)

### Step 5: Validazione Produzione (10 min)
- [ ] Importare ZIP CU reale (es. 28 CU dipendenti)
- [ ] Verificare duplicati gestiti correttamente
- [ ] Verificare performance (< 30 sec per 28 CU)

**Tempo Totale Stimato**: ~70 minuti

---

## 🎯 Risultati Attesi

### Prima (Situazione Attuale)
```
Estrazione:
  - Parser regex manuale
  - Dati estratti: 50% corretti
  - Campo anno_imposta: NON SALVATO
  - CF datore → DEVE esistere Cliente (errore se non esiste)
  - CF lavoratore → SOLO come attributo (no anagrafica)
```

### Dopo (Con Soluzione Proposta)
```
Estrazione:
  - Template AI con zone coordinate
  - Dati estratti: 90%+ corretti
  - Campo anno_imposta: SALVATO come attributo ✓
  - CF datore → Crea Anagrafica + Cliente se non esiste ✓
  - CF lavoratore → Crea Anagrafica PF se non esiste ✓
  - Tutti i 9 campi mappati e salvati ✓
```

### Benefici
1. **Maggiore affidabilità**: Zone con coordinate > regex posizionali
2. **Completezza dati**: 9/9 campi salvati (vs 3/9 attuale)
3. **Autonomia**: Crea anagrafiche mancanti automaticamente
4. **Tracciabilità**: Ogni CU ha riferimenti a Cliente + Dipendente
5. **Manutenibilità**: Mapping configurabile da UI (no codice)

---

## 📌 Note Implementative

### Validazione Codici Fiscali

Il sistema DEVE validare CF prima di creare anagrafiche:

```python
from anagrafiche.utils import validazione_cf

# Per CF datore
cf_valido, tipo_cf = validazione_cf(cf_datore)
if not cf_valido:
    raise ValueError(f"CF datore non valido: {cf_datore}")

# tipo_cf restituisce 'PF' o 'PG'
```

### Gestione Duplicati

```python
# Verificare duplicati CU per stesso dipendente + anno
duplicati = Documento.objects.filter(
    tipo__codice='CU',
    cliente=cliente,
    attributi__codice='dipendente_cf',
    attributi__valore=cf_lavoratore,
    attributi__codice='anno_riferimento',
    attributi__valore=anno_imposta
)

if duplicati.exists():
    # Gestisci duplicato: salta, sovrascrivi, avvisa utente
    pass
```

### Performance

Per importazioni massive (> 50 CU):
- Usare `bulk_create()` per AttributoValore
- Cache query Anagrafica/Cliente per CF
- Disabilitare temporaneamente signal Django

```python
# Cache CF → Anagrafica
cf_cache = {}

def _get_anagrafica_cached(cf):
    if cf not in cf_cache:
        cf_cache[cf] = Anagrafica.objects.get(codice_fiscale=cf)
    return cf_cache[cf]
```

---

## 🔗 Riferimenti

- **Template AI**: `/admin/ai_classifier/documentextractiontemplate/`
- **Mapping Campi**: `/admin/ai_classifier/extractionfieldmapping/`
- **Importer CU**: `/home/sandro/mygest/documenti/importers/certificazioni_uniche.py`
- **Parser Attuale**: `/home/sandro/mygest/documenti/parsers/cu_parser.py`
- **Data Extraction Service**: `/home/sandro/mygest/api/v1/ai_classifier/views_ai_import.py`

---

## ✅ Checklist Verifica

Prima di considerare completato:

- [ ] Template AI ha mapping per tutti i 9 campi
- [ ] Importer usa `DataExtractionService` invece di `cu_parser`
- [ ] CF datore → crea Anagrafica (PF/PG) + Cliente se non esiste
- [ ] CF lavoratore → crea Anagrafica PF se non esiste
- [ ] Tutti gli attributi CU salvati correttamente
- [ ] Test E2E passa con file CU reale
- [ ] Duplicati gestiti (skip o warning)
- [ ] Performance accettabile (< 30 sec per 28 CU)
- [ ] Documentazione aggiornata (PRD_ASIS.md)

---

**Fine Analisi** - Pronto per implementazione
