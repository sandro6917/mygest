# Guida: Trasformazioni per Campi Choice

## 🎯 Quando Usare Quale Trasformazione

### **Funzione Generica: `normalize_choice_from_db`** ⭐

**Usa SEMPRE questa per campi choice**, salvo casi eccezionali.

#### Come Funziona
1. Legge le scelte configurate in `AttributoDefinizione.choices`
2. Cerca match automatico: valore esatto, label, contenuto parziale
3. Ritorna il valore corretto dalla configurazione

#### Vantaggi
- ✅ **Zero codice**: non serve creare funzioni custom
- ✅ **Configurabile**: modifichi scelte in Django Admin, funziona subito
- ✅ **Scalabile**: funziona per tutti i tipi documento
- ✅ **Intelligente**: match flessibile (case-insensitive, parziale)

#### Esempio Pratico

**Configurazione in Django Admin**:
```
Tipo Documento: UNILAV (ID=34)
Attributo: tipo
Tipo Dato: choice
Scelte: "ASS|Assunzione,PRO|Proroga,TRA|Trasformazione,CES|Cessazione"
```

**Mapping nel Template**:
```
Zona: tipo_comunicazione
Campo: attributi.tipo
Trasformazione: 🔄 Normalizza da Scelte DB (Auto)
```

**Cosa succede in Phase 5**:
```python
AI estrae: "Assunzione"
↓
apply_transformation(
    value="Assunzione",
    transformation_name="normalize_choice_from_db",
    campo_codice="tipo",           # estratto dal mapping
    tipo_documento_id=34            # UNILAV
)
↓
Funzione legge AttributoDefinizione.choices
↓
Match trovato: "Assunzione" → "ASS"
↓
Salva: attributi.tipo = "ASS"
```

**Altri esempi di match**:
```python
"ASS" → "ASS" (match esatto valore)
"Assunzione" → "ASS" (match esatto label)
"assunzione" → "ASS" (case-insensitive)
"ASSUNZIONE A TEMPO INDETERMINATO" → "ASS" (match parziale)
"Nuova Assunzione" → "ASS" (contiene label)
"PRO" → "PRO" (già corretto)
"proroga contratto" → "PRO" (match parziale)
```

---

## 📋 Quando Usare Funzioni Specifiche

### Usa funzione specifica SOLO se:

1. **Logica complessa non coperta da match automatico**
   ```python
   # Esempio: sinonimi molto specifici del dominio
   "Licenziamento per giusta causa" → "CES"
   "Dimissioni volontarie" → "CES"
   "Risoluzione consensuale" → "CES"
   ```

2. **Trasformazione dipende da altri campi**
   ```python
   # Esempio: tipo dipende da combinazione di valori
   if tipo_rapporto == "subordinato" and durata == "determinato":
       return "TD"
   elif tipo_rapporto == "subordinato" and durata == "indeterminato":
       return "TI"
   ```

3. **Necessaria validazione aggiuntiva**
   ```python
   # Esempio: normalizza E valida formato
   def normalize_mese_anno(value):
       # "03/2024" o "Marzo 2024" → "2024-03"
       # + validazione mese 1-12, anno 2000-2100
       ...
   ```

---

## 🎨 Strategia Consigliata per Tipo Documento

### UNILAV (esempio completo)

| Attributo | Tipo | Trasformazione Consigliata | Motivo |
|-----------|------|----------------------------|---------|
| `tipo` | choice | `normalize_choice_from_db` | Scelte semplici da config |
| `modello` | choice | `normalize_choice_from_db` | Scelte semplici da config |
| `lavoratore_sesso` | choice | `normalize_sesso` | Funzione generica M/F riutilizzabile |
| `lavoratore_cf` | string | `normalize_codice_fiscale` | Non è choice, serve validazione |
| `data_comunicazione` | date | `normalize_date_italian` | Non è choice, serve conversione |
| `datore_cf` | string | `normalize_codice_fiscale` | Non è choice, serve validazione |

### CEDOLINO (ipotetico)

| Attributo | Tipo | Trasformazione Consigliata | Motivo |
|-----------|------|----------------------------|---------|
| `mese` | choice | `normalize_choice_from_db` | Scelte 01-12 da config |
| `anno` | int | `extract_numbers` | Non è choice, estrae anno |
| `dipendente` | int (FK) | Nessuna* | Campo FK, lookup in Phase 5 |

*Per FK: mappa a campo helper testuale (es. `dipendente_cf`), poi lookup in Phase 5

---

## 💡 Best Practices

### ✅ DO

1. **Configura scelte in Django Admin**
   ```
   Attributo: stato_pratica
   Scelte: "BOZZA|Bozza,INVIATA|Inviata,APPROVATA|Approvata,RIFIUTATA|Rifiutata"
   ```

2. **Usa `normalize_choice_from_db` di default**
   - Funziona per 90% dei casi
   - Zero manutenzione codice

3. **Testa i match**
   - In Django shell:
   ```python
   from api.v1.ai_classifier.transformations import normalize_choice_from_db
   
   result = normalize_choice_from_db(
       value="Bozza",
       campo_codice="stato_pratica",
       tipo_documento_id=42
   )
   print(result)  # "BOZZA"
   ```

### ❌ DON'T

1. **Non creare funzione specifica per scelte semplici**
   ```python
   # ❌ SBAGLIATO - spreco di codice
   def normalize_mese_cedolino(value):
       mapping = {'gennaio': '01', 'febbraio': '02', ...}
       return mapping.get(value.lower(), value)
   
   # ✅ CORRETTO - usa funzione generica
   # (le scelte sono già in AttributoDefinizione.choices)
   ```

2. **Non hardcodare scelte nel codice**
   ```python
   # ❌ SBAGLIATO
   STATI_PRATICA = {'bozza': 'BOZZA', 'inviata': 'INVIATA'}
   
   # ✅ CORRETTO - scelte in DB
   # AttributoDefinizione.choices = "BOZZA|Bozza,INVIATA|Inviata"
   ```

3. **Non usare trasformazioni per campi non-choice**
   ```python
   # ❌ SBAGLIATO
   Campo: codice_fiscale (string)
   Trasformazione: normalize_choice_from_db
   
   # ✅ CORRETTO
   Campo: codice_fiscale (string)
   Trasformazione: normalize_codice_fiscale
   ```

---

## 🔧 Aggiungere Nuova Scelta

**Scenario**: UNILAV ha nuovo tipo comunicazione "Distacco"

### Soluzione con `normalize_choice_from_db`:

1. **Django Admin** → Documenti → Attributi Definizioni
2. Trova attributo `tipo` del tipo UNILAV
3. Modifica campo `Scelte`:
   ```
   Prima: "ASS|Assunzione,PRO|Proroga,TRA|Trasformazione,CES|Cessazione"
   Dopo:  "ASS|Assunzione,PRO|Proroga,TRA|Trasformazione,CES|Cessazione,DIS|Distacco"
   ```
4. Salva

**Fatto!** La funzione `normalize_choice_from_db` riconoscerà automaticamente:
- "DIS" → "DIS"
- "Distacco" → "DIS"
- "distacco" → "DIS"
- "Distacco lavoratore" → "DIS"

**Nessuna modifica al codice necessaria!**

---

## 🚀 Riepilogo Decisione

```
Devo mappare attributo choice?
  ↓
  Si → Uso normalize_choice_from_db (99% dei casi)
  No → È un altro tipo di campo?
      ↓
      CF/PIVA → normalize_codice_fiscale / normalize_partita_iva
      Date → normalize_date_italian
      Email → normalize_email
      Testo → uppercase / lowercase / title_case
      Altro → Nessuna trasformazione o funzione custom
```

---

**Versione**: 1.0  
**Data**: 2 Marzo 2026  
**Feature**: Trasformazioni Choice Fields con `normalize_choice_from_db`
