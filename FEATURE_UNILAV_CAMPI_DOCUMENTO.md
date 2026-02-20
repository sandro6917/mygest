# Feature UNILAV: Mappatura Completa Campi Documento

## 📋 Overview

Questo documento descrive nel dettaglio tutti i campi del documento UNILAV che vengono creati durante l'importazione, specificando la loro origine, destinazione e modalità di salvataggio.

## 🗂️ Struttura Documento UNILAV

### 1. Campi Documento Base (Model `Documento`)

```python
# Recupera/crea voce titolario intestata al dipendente
voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
voce_dipendente = TitolarioVoce.objects.filter(
    parent=voce_hr_pers,
    anagrafica=anagrafica_lavoratore
).first()

if not voce_dipendente:
    # Crea voce intestata al dipendente
    voce_dipendente = TitolarioVoce.objects.create(
        codice=anagrafica_lavoratore.codice,           # Es. CONSLI01
        titolo=f"Dossier {anagrafica_lavoratore.display_name()}",  # "Dossier CONSORTI LISA"
        parent=voce_hr_pers,
        anagrafica=anagrafica_lavoratore,
        pattern_codice='{CLI}-{ANA}-UNILAV-{ANNO}-{SEQ:03d}',
        consente_intestazione=False
    )

# Crea documento
documento = Documento.objects.create(
    tipo=tipo_unilav,                              # ← DocumentiTipo 'UNILAV'
    cliente=cliente_datore,                        # ← Cliente (Datore di Lavoro)
    titolario_voce=voce_dipendente,               # ← Voce intestata al dipendente
    descrizione=descrizione,                       # ← "UNILAV {codice} - {lavoratore}"
    data_documento=documento_data['data_comunicazione'],  # ← Data comunicazione
    digitale=True,                                 # ← Sempre True (PDF)
    tracciabile=True,                              # ← Sempre True (protocollabile)
    stato='definitivo',                            # ← Sempre 'definitivo'
    ubicazione=None,                               # ← SEMPRE None (documenti digitali)
    file=<PDF_UNILAV>                             # ← File PDF allegato
)
```

#### Dettaglio Campi Base

| Campo | Valore | Tipo | Descrizione |
|-------|--------|------|-------------|
| `tipo` | `DocumentiTipo('UNILAV')` | FK | Tipo documento UNILAV (ID 34) |
| `cliente` | `Cliente` (datore) | FK | Cliente = Datore di Lavoro |
| `titolario_voce` | `TitolarioVoce` (dipendente) | FK | Voce intestata al dipendente sotto HR-PERS |
| `descrizione` | `"UNILAV {codice} - {nome lavoratore}"` | CharField | Esempio: "UNILAV 1700026200007595 - CONSORTI LISA" |
| `data_documento` | `documento_data['data_comunicazione']` | DateField | Data della comunicazione UNILAV |
| `digitale` | `True` | BooleanField | Sempre True (documento digitale PDF) |
| `tracciabile` | `True` | BooleanField | Sempre True (può essere protocollato) |
| `stato` | `'definitivo'` | CharField | Sempre 'definitivo' alla creazione |
| `ubicazione` | `None` | FK | **SEMPRE None** (documenti digitali non hanno ubicazione fisica) |
| `file` | PDF UNILAV | FileField | File PDF originale caricato |
| `note` | Dati aggiuntivi (vedi sotto) | TextField | Qualifica, CCNL, Livello, Retribuzione, etc. |

### 2. Attributi Dinamici (Model `AttributoValore`)

Gli attributi dinamici vengono salvati nella tabella `AttributoValore` collegata al documento tramite `AttributoDefinizione`.

```python
attributi_map = {
    'dipendente': anagrafica_lavoratore.id,           # ID Anagrafica lavoratore
    'tipo': documento_data.get('tipo'),               # SELECT: Assunzione|Proroga|Trasformazione|Cessazione
    'data_comunicazione': documento_data.get('data_comunicazione'),  # Data comunicazione
    'data_da': documento_data.get('data_da'),         # Data inizio rapporto
    'data_a': documento_data.get('data_a'),           # Data fine rapporto
}
```

#### Attributi Configurati

| Codice Attributo | Valore Esempio | Tipo Dato | Scelte | Descrizione |
|-----------------|---------------|-----------|--------|-------------|
| `dipendente` | `123` | `int` (FK Anagrafica) | - | ID dell'anagrafica del lavoratore |
| `tipo` | `"Assunzione"` | `choice` (SELECT) | Assunzione, Proroga, Trasformazione, Cessazione | Tipologia comunicazione UNILAV |
| `data_comunicazione` | `"2026-01-03"` | `date` | - | Data della comunicazione |
| `data_da` | `"2026-01-03"` | `date` | - | Data inizio rapporto di lavoro |
| `data_a` | `"2026-12-31"` | `date` | - | Data fine rapporto di lavoro |

**Note:**
- **`tipo` è una SELECT** con scelte predefinite (configurate in `AttributoDefinizione.choices`)
- Gli attributi sono definiti in `AttributoDefinizione` per il tipo documento UNILAV
- Se un attributo non è configurato, viene saltato (no errore)
- Gli attributi possono essere visualizzati/modificati nella UI documento

### 3. Dati Aggiuntivi (Campo `note`)

I seguenti dati vengono salvati nel campo `note` del documento (TextField):

```python
note_extra = []
if documento_data.get('qualifica'):
    note_extra.append(f"Qualifica: {documento_data['qualifica']}")
if documento_data.get('contratto_collettivo'):
    note_extra.append(f"CCNL: {documento_data['contratto_collettivo']}")
if documento_data.get('livello'):
    note_extra.append(f"Livello: {documento_data['livello']}")
if documento_data.get('retribuzione'):
    note_extra.append(f"Retribuzione: {documento_data['retribuzione']}")
if documento_data.get('ore_settimanali'):
    note_extra.append(f"Ore settimanali: {documento_data['ore_settimanali']}")
if documento_data.get('tipo_orario'):
    note_extra.append(f"Tipo orario: {documento_data['tipo_orario']}")

documento.note = '\n'.join(note_extra)
```

#### Dati nelle Note

| Campo | Valore Esempio | Formato Note |
|-------|---------------|--------------|
| `qualifica` | `"Operaio"` | `Qualifica: Operaio` |
| `contratto_collettivo` | `"CCNL Commercio"` | `CCNL: CCNL Commercio` |
| `livello` | `"3° livello"` | `Livello: 3° livello` |
| `retribuzione` | `"1.500,00 EUR"` | `Retribuzione: 1.500,00 EUR` |
| `ore_settimanali` | `"40"` | `Ore settimanali: 40` |
| `tipo_orario` | `"Tempo pieno"` | `Tipo orario: Tempo pieno` |

**Esempio campo `note` completo:**
```
Qualifica: Operaio
CCNL: CCNL Commercio
Livello: 3° livello
Retribuzione: 1.500,00 EUR
Ore settimanali: 40
Tipo orario: Tempo pieno
```

## 📊 Flusso Dati: PDF → Database

### Estrazione dal PDF (Parser)

```python
# documenti/parsers/unilav_parser.py
parsed_data = {
    'datore': {
        'codice_fiscale': 'SLMRME65H01H501A',  # ← Estratto da PDF
        'tipo': 'PF',  # ← Determinato da lunghezza CF
        'cognome': 'SALIMBENI',
        'nome': 'REMO',
        ...
    },
    'lavoratore': {
        'codice_fiscale': 'CNSLSI95E50H501X',
        'cognome': 'CONSORTI',
        'nome': 'LISA',
        ...
    },
    'unilav': {
        'codice_comunicazione': '1700026200007595',  # ← Codice UNILAV
        'data_comunicazione': '2026-01-03',
        'tipologia_contrattuale': 'A tempo determinato',
        'data_inizio_rapporto': '2026-01-03',
        'data_fine_rapporto': '2026-12-31',
        'qualifica_professionale': 'Operaio',
        'contratto_collettivo': 'CCNL Commercio',
        ...
    }
}
```

### Trasformazione Preview (API Response)

```json
{
  "datore": {
    "codice_fiscale": "SLMRME65H01H501A",
    "tipo": "PF",
    "cognome": "SALIMBENI",
    "nome": "REMO",
    "esiste": true,
    "anagrafica_id": 123,
    "cliente_id": 456
  },
  "lavoratore": {
    "codice_fiscale": "CNSLSI95E50H501X",
    "cognome": "CONSORTI",
    "nome": "LISA",
    "esiste": false
  },
  "documento": {
    "codice_comunicazione": "1700026200007595",
    "tipo_comunicazione": "UNILAV",
    "data_comunicazione": "2026-01-03",
    "dipendente": null,  // ← Sarà popolato dopo creazione lavoratore
    "tipo": "A tempo determinato",
    "data_da": "2026-01-03",        // ← data_inizio_rapporto
    "data_a": "2026-12-31",         // ← data_fine_rapporto
    "qualifica": "Operaio",         // ← qualifica_professionale
    "contratto_collettivo": "CCNL Commercio",
    "livello": null,
    "retribuzione": null,
    "ore_settimanali": null,
    "tipo_orario": null
  },
  "file_temp_path": "/tmp/unilav_xxx.pdf"
}
```

### Creazione Database (Confirm)

```
📦 TRANSAZIONE ATOMICA
│
├── 1. ANAGRAFICA DATORE
│   ├── Se esiste (CF trovato) → RIUTILIZZO (no modifiche)
│   └── Se non esiste → CREAZIONE
│       ├── codice_fiscale: "SLMRME65H01H501A"
│       ├── tipo: "PF"
│       ├── cognome: "SALIMBENI"
│       └── nome: "REMO"
│
├── 2. CLIENTE DATORE
│   ├── Se esiste → RIUTILIZZO
│   └── Se non esiste → CREAZIONE
│       └── anagrafica: <anagrafica_datore>
│
├── 3. ANAGRAFICA LAVORATORE
│   ├── Se esiste (CF trovato) → RIUTILIZZO (no modifiche)
│   └── Se non esiste → CREAZIONE
│       ├── codice_fiscale: "CNSLSI95E50H501X"
│       ├── tipo: "PF"
│       ├── cognome: "CONSORTI"
│       ├── nome: "LISA"
│       └── data_nascita: "1995-05-10"
│
├── 4. DOCUMENTO UNILAV
│   ├── tipo: DocumentiTipo('UNILAV')
│   ├── cliente: <cliente_datore>
│   ├── descrizione: "UNILAV 1700026200007595 - CONSORTI LISA"
│   ├── data_documento: "2026-01-03"
│   ├── digitale: True
│   ├── tracciabile: True
│   ├── stato: "definitivo"
│   └── file: <PDF_UNILAV>
│
├── 5. ATTRIBUTO 'dipendente'
│   ├── documento: <documento>
│   ├── definizione: AttributoDefinizione('dipendente')
│   └── valore: <anagrafica_lavoratore.id>
│
├── 6. ATTRIBUTO 'tipo'
│   ├── documento: <documento>
│   ├── definizione: AttributoDefinizione('tipo')
│   └── valore: "A tempo determinato"
│
├── 7. ATTRIBUTO 'data_comunicazione'
│   ├── documento: <documento>
│   ├── definizione: AttributoDefinizione('data_comunicazione')
│   └── valore: "2026-01-03"
│
├── 8. ATTRIBUTO 'data_da'
│   ├── documento: <documento>
│   ├── definizione: AttributoDefinizione('data_da')
│   └── valore: "2026-01-03"
│
├── 9. ATTRIBUTO 'data_a'
│   ├── documento: <documento>
│   ├── definizione: AttributoDefinizione('data_a')
│   └── valore: "2026-12-31"
│
└── 10. NOTE DOCUMENTO
    ├── Qualifica: Operaio
    ├── CCNL: CCNL Commercio
    └── [altri dati se presenti]
```

## 🎨 Visualizzazione UI - Riepilogo Documento

La UI mostra un riepilogo completo prima della conferma:

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Riepilogo Documento da Creare                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ℹ️ Verrà creato un documento UNILAV con i seguenti dati:   │
│                                                              │
│ Tipo Documento:                                             │
│ UNILAV (Comunicazione Obbligatoria)                         │
│                                                              │
│ ───────────────────────────────────────────────────────────│
│                                                              │
│ Cliente (Datore di Lavoro):                                 │
│ SALIMBENI REMO (CF: SLMRME65H01H501A)                       │
│                                                              │
│ Descrizione:                                                │
│ UNILAV 1700026200007595 - CONSORTI LISA                     │
│                                                              │
│ Data Documento:                                             │
│ 03/01/2026                                                  │
│                                                              │
│ ───────────────────────────────────────────────────────────│
│                                                              │
│ Attributi Dinamici:                                         │
│ • Dipendente: CONSORTI LISA (CF: CNSLSI95E50H501X)         │
│ • Tipo Contratto: A tempo determinato                       │
│ • Data Inizio: 03/01/2026                                   │
│ • Data Fine: 31/12/2026                                     │
│                                                              │
│ ───────────────────────────────────────────────────────────│
│                                                              │
│ Dati Aggiuntivi (salvati nelle Note):                      │
│ • Qualifica: Operaio                                        │
│ • CCNL: CCNL Commercio                                      │
│ • Livello: 3° livello                                       │
│ • Retribuzione: 1.500,00 EUR                                │
│ • Ore Settimanali: 40                                       │
│ • Tipo Orario: Tempo pieno                                  │
│                                                              │
│ ───────────────────────────────────────────────────────────│
│                                                              │
│ Caratteristiche Documento:                                  │
│ • Digitale: Sì (file PDF allegato)                         │
│ • Tracciabile: Sì (protocollabile)                         │
│ • Stato: Definitivo                                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 🔍 Query Database Risultanti

### Documento
```sql
SELECT * FROM documenti_documento WHERE id = 789;

id  | tipo_id | cliente_id | descrizione                           | data_documento | digitale | tracciabile | stato      | file
789 | 34      | 456        | UNILAV 1700026200007595 - CONSORTI... | 2026-01-03    | true     | true        | definitivo | unilav_xxx.pdf

note
---
Qualifica: Operaio
CCNL: CCNL Commercio
Livello: 3° livello
Retribuzione: 1.500,00 EUR
Ore settimanali: 40
Tipo orario: Tempo pieno
```

### Attributi Dinamici
```sql
SELECT 
    av.id,
    ad.codice AS attributo,
    av.valore
FROM documenti_attributovalore av
JOIN documenti_attributodefinizione ad ON av.definizione_id = ad.id
WHERE av.documento_id = 789;

id  | attributo          | valore
1   | dipendente         | 124
2   | tipo               | A tempo determinato
3   | data_comunicazione | 2026-01-03
4   | data_da            | 2026-01-03
5   | data_a             | 2026-12-31
```

### Join Completo
```sql
SELECT 
    d.id AS doc_id,
    d.descrizione,
    dt.nome AS tipo_documento,
    c.id AS cliente_id,
    a_datore.denominazione AS datore,
    a_datore.codice_fiscale AS datore_cf,
    -- Attributo dipendente (FK Anagrafica)
    a_lavoratore.denominazione AS lavoratore,
    a_lavoratore.codice_fiscale AS lavoratore_cf
FROM documenti_documento d
JOIN documenti_tipo dt ON d.tipo_id = dt.id
JOIN anagrafiche_cliente c ON d.cliente_id = c.id
JOIN anagrafiche_anagrafica a_datore ON c.anagrafica_id = a_datore.id
-- Join per recuperare lavoratore da attributo dinamico
LEFT JOIN documenti_attributovalore av_dip ON av_dip.documento_id = d.id 
    AND av_dip.definizione_id = (
        SELECT id FROM documenti_attributodefinizione 
        WHERE codice = 'dipendente' AND tipo_documento_id = dt.id
    )
LEFT JOIN anagrafiche_anagrafica a_lavoratore ON av_dip.valore::int = a_lavoratore.id
WHERE d.id = 789;

doc_id | descrizione                | tipo_documento | cliente_id | datore         | datore_cf        | lavoratore      | lavoratore_cf
789    | UNILAV 1700026200007595... | UNILAV         | 456        | SALIMBENI REMO | SLMRME65H01H501A | CONSORTI LISA   | CNSLSI95E50H501X
```

## 📝 Configurazione AttributoDefinizione

Per il corretto funzionamento, devono esistere le seguenti definizioni:

```sql
INSERT INTO documenti_attributodefinizione (tipo_documento_id, codice, nome, tipo_dato, obbligatorio, ordine)
VALUES 
    (34, 'dipendente', 'Dipendente', 'FK_ANAGRAFICA', true, 1),
    (34, 'tipo', 'Tipo Contratto', 'TEXT', false, 2),
    (34, 'data_comunicazione', 'Data Comunicazione', 'DATE', false, 3),
    (34, 'data_da', 'Data Inizio Rapporto', 'DATE', false, 4),
    (34, 'data_a', 'Data Fine Rapporto', 'DATE', false, 5);
```

**Note:**
- `tipo_documento_id = 34` → DocumentiTipo 'UNILAV'
- `tipo_dato = 'FK_ANAGRAFICA'` per il campo dipendente
- `tipo_dato = 'TEXT'` per campi testuali
- `tipo_dato = 'DATE'` per campi data

## ✅ Checklist Validazione

Prima di confermare l'importazione, verificare:

### Campi Obbligatori
- [x] `tipo`: DocumentiTipo 'UNILAV' esiste
- [x] `cliente`: Cliente datore esiste o viene creato
- [x] `descrizione`: Generata automaticamente
- [x] `data_documento`: Presente (data_comunicazione)
- [x] `file`: PDF caricato

### Attributi Raccomandati
- [x] `dipendente`: ID anagrafica lavoratore
- [x] `tipo`: Tipologia contrattuale
- [x] `data_da`: Data inizio rapporto
- [ ] `data_a`: Data fine rapporto (opzionale per indeterminato)

### Dati Opzionali (Note)
- [ ] `qualifica`: Qualifica professionale
- [ ] `contratto_collettivo`: CCNL
- [ ] `livello`: Livello inquadramento
- [ ] `retribuzione`: Retribuzione
- [ ] `ore_settimanali`: Ore settimanali
- [ ] `tipo_orario`: Tipo orario

## 🚀 Prossimi Sviluppi

### Attributi Aggiuntivi Configurabili
- Aggiungere `qualifica`, `ccnl`, `livello` come attributi dinamici invece che nelle note
- Permettere configurazione dinamica attributi da UI admin

### Validazioni Avanzate
- Validare coerenza date (data_da < data_a)
- Validare formati (retribuzione numerica, ore settimanali intere)
- Controllo duplicati (stesso codice_comunicazione)

### Export/Report
- Export Excel con tutti i campi (base + attributi + note)
- Report UNILAV per periodo con filtri avanzati
- Dashboard statistiche contratti (determinato/indeterminato, durata media, etc.)

---

**Versione**: 1.0  
**Data**: 3 Febbraio 2026  
**Autore**: Sistema MyGest
