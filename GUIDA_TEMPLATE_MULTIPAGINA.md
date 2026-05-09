# 📄 Guida Template Multi-Pagina e Documenti Variabili

## 🎯 Problema

Come gestire documenti con **numero variabile di pagine** dove solo alcune contengono dati da estrarre?

**Esempi tipici**:
- Contratti di lavoro (20-50 pagine, dati su pag 1, 3, ultima)
- UNILAV con frontespizio (2-4 pagine, dati sempre sulla seconda)
- Cedolini con allegati (pagine variabili, dati solo sulla prima)
- Documenti scannerizzati con copertine (numero copertine varia)

---

## ✅ Soluzione 1: Template Multi-Pagina a Posizioni Fisse

### Quando usare
✅ Le pagine con dati hanno **posizione fissa** nel documento  
✅ Struttura documento **prevedibile** (es. UNILAV sempre 2 pagine)  
✅ Non serve elaborazione dinamica  

### Come configurare

#### 1. Crea il template normalmente
```
Tipo Documento: CONTRATTO_LAVORO
Nome Template: "Contratto standard CCNL Commercio"
```

#### 2. Aggiungi SOLO le pagine con dati
```
Pagina 1 (numero_pagina=1):
  - Immagine di riferimento: pagina 1 del contratto tipo
  - Zone: dati anagrafici lavoratore

Pagina 3 (numero_pagina=3):
  - Immagine di riferimento: pagina 3 del contratto tipo
  - Zone: qualifica, livello, retribuzione

Pagina 15 (numero_pagina=15):
  - Immagine di riferimento: ultima pagina del contratto tipo
  - Zone: firme, date
```

⚠️ **Importante**: Non serve creare pagine 2, 4-14, ecc. se non contengono zone da estrarre!

#### 3. Disegna zone normalmente su ogni pagina
```
Pagina 1:
  Zona "nome_cognome" → attributi.nome_lavoratore
  Zona "cf_lavoratore" → attributi.cf_lavoratore + normalize_codice_fiscale
  Zona "data_nascita" → attributi.data_nascita + normalize_date_italian

Pagina 3:
  Zona "qualifica" → attributi.qualifica
  Zona "livello" → attributi.livello_ccnl

Pagina 15:
  Zona "data_firma" → data_documento + normalize_date_italian
```

### Comportamento in fase di import (Phase 5)

```python
# ExtractionService già implementato
# Quando l'utente carica un PDF di 20 pagine:

1. AI classifica → tipo documento "CONTRATTO_LAVORO"
2. Carica template associato (ha pagine 1, 3, 15)
3. Estrae OCR da TUTTE le 20 pagine
4. MA estrae dati SOLO da pagine 1, 3, 15 usando le zone configurate
5. Ignora pagine 2, 4-14, 16-20 (non hanno zone)
6. Restituisce dati estratti per pre-compilare il form
```

**Vantaggi**:
- ✅ Configurazione semplice
- ✅ UI attuale già supporta
- ✅ Nessun codice custom necessario
- ✅ Performance ottima

**Svantaggi**:
- ❌ Serve che le pagine siano sempre nelle stesse posizioni
- ❌ Non gestisce documenti con struttura variabile

---

## ✅ Soluzione 2: Template con Pattern Detection

### Quando usare
✅ La pagina con dati **cambia posizione** nel documento  
✅ Documenti con **frontespizi variabili** (1-3 pagine di copertina)  
✅ Serve **flessibilità** nella struttura  

### Come configurare

#### 1. Crea template con pagina "tipo" (numero_pagina=1)
```
Tipo Documento: UNILAV
Nome Template: "UNILAV standard"

Pagina 1 (numero_pagina=1):
  - Immagine: prima pagina DOPO frontespizio
  - Zone: tutti i campi UNILAV standard
```

#### 2. Definisci pattern di identificazione

Nel database, aggiungi metadati al template (field JSON futuro o note):

```json
{
  "page_detection": {
    "strategy": "pattern_match",
    "patterns": [
      "COMUNICAZIONE OBBLIGATORIA",
      "CODICE FISCALE LAVORATORE",
      "TIPO COMUNICAZIONE"
    ],
    "min_matches": 2,
    "search_first_n_pages": 5
  }
}
```

#### 3. Enhancement ExtractionService (Phase 5)

```python
# In api/v1/ai_classifier/views_ai_import.py
# Enhancement da fare in Phase 5

class ExtractionService:
    
    def extract_with_variable_pages(self, pdf_file, template):
        """
        Estrae dati da documenti con pagine variabili
        usando pattern detection
        """
        # 1. Estrai OCR da tutte le pagine
        all_pages_text = self.extract_all_pages(pdf_file)
        
        # 2. Per ogni TemplatePage con strategia pattern
        for template_page in template.pagine.all():
            
            # Se numero_pagina > 0: usa posizione fissa (Soluzione 1)
            if template_page.numero_pagina > 0:
                target_page = template_page.numero_pagina - 1
                extracted = self.extract_zones_from_page(
                    all_pages_text[target_page], 
                    template_page
                )
                continue
            
            # Se numero_pagina == 0: usa pattern detection (Soluzione 2)
            if template_page.numero_pagina == 0:
                patterns = self._get_page_patterns(template_page)
                target_page = self._find_page_by_patterns(
                    all_pages_text, 
                    patterns
                )
                extracted = self.extract_zones_from_page(
                    all_pages_text[target_page], 
                    template_page
                )
        
        return extracted
    
    def _find_page_by_patterns(self, pages, patterns):
        """
        Trova la pagina che matcha i pattern configurati
        """
        for page_num, page_text in enumerate(pages):
            matches = sum(
                1 for pattern in patterns['keywords']
                if pattern.upper() in page_text.upper()
            )
            
            if matches >= patterns['min_matches']:
                return page_num
        
        raise ValueError(
            f"Nessuna pagina trovata con almeno "
            f"{patterns['min_matches']} pattern su {len(patterns['keywords'])}"
        )
```

### UI Enhancement per Pattern Detection

```typescript
// In TemplateEditorPage.tsx - Enhancement futuro
// Quando numero_pagina === 0, mostra sezione "Pattern Detection"

{selectedPage?.numero_pagina === 0 && (
  <Card sx={{ mb: 2 }}>
    <CardContent>
      <Typography variant="h6" gutterBottom>
        🔍 Rilevamento Pagina Dinamico
      </Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        Questa pagina usa pattern detection. Il sistema cercherà 
        automaticamente la pagina contenente questi pattern.
      </Alert>
      
      <TextField
        label="Pattern Keywords (uno per riga)"
        multiline
        rows={4}
        fullWidth
        value={pagePatterns}
        onChange={(e) => setPagePatterns(e.target.value)}
        helperText="Es: COMUNICAZIONE OBBLIGATORIA, CODICE FISCALE, ecc."
      />
      
      <TextField
        label="Minimo Match Richiesti"
        type="number"
        value={minMatches}
        onChange={(e) => setMinMatches(e.target.value)}
        helperText="Quanti pattern devono essere presenti nella pagina"
      />
    </CardContent>
  </Card>
)}
```

**Vantaggi**:
- ✅ Gestisce strutture variabili
- ✅ Adattabile a documenti non standard
- ✅ Più robusto per documenti scannerizzati

**Svantaggi**:
- ❌ Richiede enhancement UI (futuro)
- ❌ Richiede enhancement ExtractionService (Phase 5)
- ❌ Più lento (deve scansionare per trovare pagina)
- ❌ Rischio falsi positivi se pattern troppo generici

---

## 🎯 Casi d'Uso Pratici

### Caso 1: UNILAV (Comunicazioni Obbligatorie)

**Caratteristiche**:
- Struttura FISSA: sempre 1-2 pagine
- Dati sempre sulla pagina 1 (o 2 se c'è frontespizio)
- Frontespizio opzionale ma prevedibile

**Soluzione**: **Template Multi-Pagina Fissa**

```
Template UNILAV:
  Pagina 1 (numero_pagina=1):
    - Zone: tipo, cf_lavoratore, data_comunicazione, ecc.
  
  (Non serve pagina 2 se è solo frontespizio senza dati)
```

**Workflow**:
1. Upload UNILAV di 2 pagine
2. AI classifica → UNILAV
3. Estrae OCR da entrambe le pagine
4. Applica zone SOLO a pagina 1
5. Dati estratti → form pre-compilato

---

### Caso 2: Cedolini Paga

**Caratteristiche**:
- Pagina 1: dati lavoratore + retribuzione (SEMPRE)
- Pagine 2-N: dettagli ore, ferie, TFR (OPZIONALI)
- Numero pagine varia: 1-5 pagine

**Soluzione**: **Template Multi-Pagina Fissa**

```
Template CEDOLINO:
  Pagina 1 (numero_pagina=1):
    - Zone: cf_dipendente, periodo (mese/anno), retribuzione_lorda
  
  Pagina 2 (numero_pagina=2) [OPZIONALE]:
    - Zone: ore_ordinarie, ore_straordinario
  
  (Pagine 3-N ignorate se non hanno zone)
```

**Comportamento**:
- Cedolino 1 pag → estrae solo da pag 1
- Cedolino 3 pag → estrae da pag 1 e 2, ignora pag 3
- Cedolino 5 pag → estrae da pag 1 e 2, ignora pag 3-5

---

### Caso 3: Contratti Lavoro (20-50 pagine)

**Caratteristiche**:
- Pagina 1: dati anagrafici
- Pagina 3-5: qualifica e retribuzione (posizione VARIA)
- Ultima pagina: firme (posizione VARIABILE)

**Soluzione**: **Ibrida** (Fissa + Pattern per ultima pagina)

```
Template CONTRATTO:
  Pagina 1 (numero_pagina=1):
    - Zone: nome, cf, residenza
  
  Pagina 3 (numero_pagina=3):
    - Zone: qualifica, ccnl, livello
  
  Pagina 0 (numero_pagina=0, pattern_detection=true):
    - Patterns: ["FIRMA DATORE", "FIRMA LAVORATORE", "DATA __/__/____"]
    - Zone: data_firma, luogo_firma
```

**Comportamento**:
- Estrae da pagina 1 (fissa)
- Estrae da pagina 3 (fissa)
- CERCA l'ultima pagina con pattern firme
- Estrae da pagina trovata

---

## 📊 Confronto Soluzioni per Tipo Documento

| Tipo Documento | Pagine | Struttura | Soluzione Consigliata |
|----------------|--------|-----------|----------------------|
| **UNILAV** | 1-2 | Fissa | Multi-Pagina Fissa (pag 1) |
| **Cedolino** | 1-5 | Semi-fissa | Multi-Pagina Fissa (pag 1-2) |
| **Contratto Standard** | 15-20 | Fissa | Multi-Pagina Fissa (pag 1, 3, 15) |
| **Contratto Variabile** | 10-50 | Variabile | Ibrida (fisse + pattern) |
| **Documenti Scannerizzati** | 5-100 | Molto variabile | Pattern Detection |
| **Libro Unico** | 10-200 | Sezioni fisse | Multi-Pagina Fissa (pag specifiche) |

---

## 🛠️ Implementazione Immediata vs Futura

### ✅ Disponibile ORA (Phase 3 completata)

**Multi-Pagina a Posizioni Fisse**:
- [x] UI supporta creazione pagine multiple
- [x] Ogni pagina ha numero_pagina configurabile
- [x] Zone disegnabili su ogni pagina
- [x] Field mapping funzionante
- [x] Nessun codice aggiuntivo richiesto

**Come usare**:
1. Apri template editor
2. Clicca "Aggiungi Pagina"
3. Imposta numero_pagina = 1 (o 3, 15, ecc.)
4. Carica immagine di riferimento
5. Disegna zone
6. Crea field mapping
7. ✅ Fatto!

### ⏳ Richiede Enhancement (Phase 5)

**Pattern Detection per Pagine Variabili**:
- [ ] UI: campo pattern keywords
- [ ] UI: campo min_matches
- [ ] Backend: logica _find_page_by_patterns
- [ ] Backend: metadata JSON in TemplatePage
- [ ] Test con documenti variabili

**Quando implementare**: Durante Phase 5 se emerge necessità

---

## 💡 Raccomandazioni

### Per la maggior parte dei documenti (90% casi):

**USA Soluzione 1: Multi-Pagina Fissa**

Motivi:
- ✅ Già funzionante
- ✅ Semplice da configurare
- ✅ Affidabile
- ✅ Performante
- ✅ Sufficiente per documenti standardizzati (UNILAV, Cedolini, Contratti tipo)

### Solo se necessario (10% casi complessi):

**USA Soluzione 2: Pattern Detection**

Motivi:
- ⚠️ Richiede development aggiuntivo
- ⚠️ Più complesso da configurare
- ⚠️ Più lento in esecuzione
- ✅ Ma necessario per documenti molto variabili

---

## 🚀 Quick Start: Configura il tuo primo template multi-pagina

### Esempio: UNILAV con 1 pagina dati

1. **Crea template**:
   - Vai a `/admin/templates`
   - Nuovo template per tipo "UNILAV"
   - Nome: "UNILAV Standard 2024"

2. **Aggiungi pagina 1**:
   - Clicca "Aggiungi Pagina"
   - numero_pagina = 1
   - Upload immagine UNILAV tipo
   - Salva

3. **Disegna zone sulla pagina 1**:
   - tipo_comunicazione (in alto)
   - cf_lavoratore (centro)
   - data_comunicazione (basso)
   - ecc.

4. **Crea field mappings**:
   - tipo_comunicazione → attributi.tipo + normalize_choice_from_db
   - cf_lavoratore → attributi.lavoratore_cf + normalize_codice_fiscale
   - data_comunicazione → attributi.data_comunicazione + normalize_date_italian

5. **✅ Template pronto!**

Quando un utente caricherà un UNILAV di 2 pagine:
- AI estrae OCR da entrambe
- Applica zone solo a pagina 1
- Ignora pagina 2 (frontespizio)
- Dati estratti → form pre-compilato

---

## 📚 Riferimenti

- **Phase 3**: Template Manager UI (COMPLETATO)
- **Phase 5**: Extraction Service enhancement (FUTURO)
- **GUIDA_FIELD_MAPPING_NOTE.md**: Campo virtuale __note__
- **GUIDA_TRASFORMAZIONI_CHOICE_FIELDS.md**: Sistema trasformazioni
- **attributi_choice_report.pdf**: 62 attributi choice documentati

---

## ❓ FAQ

**Q: Devo creare una pagina per ogni pagina del PDF?**  
A: ❌ NO! Crea pagine SOLO per quelle con zone da estrarre.

**Q: Se il PDF ha 20 pagine ma dati solo su pag 1 e 3?**  
A: Crea solo 2 pagine template (pag 1 e pag 3). Le altre 18 vengono ignorate.

**Q: Il PDF può avere meno pagine del template?**  
A: ⚠️ SI, ma riceverai errore se tenti di estrarre da pagina inesistente. Es: template con pag 15, ma PDF ha solo 10 pagine → errore. Usa pattern detection se struttura varia.

**Q: Posso mischiare pagine fisse e pattern detection?**  
A: ✅ SI (futuro Phase 5). Pagine con numero_pagina > 0 = fisse, numero_pagina = 0 = pattern.

**Q: E se la pagina con dati cambia sempre posizione?**  
A: Usa Soluzione 2 (Pattern Detection) - richiede enhancement Phase 5.

**Q: Quanto tempo serve per configurare un template multi-pagina?**  
A: ~10-15 min per template a 3 pagine con 20 zone totali.

---

**Versione**: 1.0  
**Data**: 2 Marzo 2026  
**Stato**: Soluzione 1 già implementata ✅ | Soluzione 2 richiede Phase 5 ⏳
