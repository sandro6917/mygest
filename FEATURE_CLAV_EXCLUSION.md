# Esclusione CLAV (Carte di Lavoro) da AI Classifier

**Data**: 25 Febbraio 2026  
**Issue**: CLAV è un tipo documento residuale/generico troppo variegato per ML  
**Soluzione**: Escluso da training e predizioni

---

## 🎯 Motivo Esclusione

CLAV (Carte di lavoro) comprende una **grande varietà di documenti** senza pattern comuni:
- Documenti temporanei
- Bozze
- Appunti
- File generici
- Materiale di lavoro non categorizzato

Questi documenti:
- ❌ Non hanno caratteristiche distintive per ML
- ❌ Non hanno rilevanza per archiviazione documentale strutturata
- ✅ Devono essere inseriti **manualmente** dagli utenti

---

## 📊 Impatto

Prima dell'esclusione:
- **Documenti totali con file**: 445
- **Documenti CLAV**: 83 (18.7%)
- **Altri tipi**: 362

Dopo l'esclusione:
- **Documenti per training**: 362 (↓ 83 docs)
- **Tipi documento ML**: 14 (↓ 1 tipo)
- **Accuracy prevista**: Potenzialmente più alta (meno rumore)

---

## 🔧 Implementazione

### 1. Model Trainer - Esclusione da Training

**File**: `ai_classifier/services/ml/model_trainer.py`

**Metodo**: `_extract_features_from_documents()`

```python
# ESCLUDI documenti CLAV (Carte di lavoro)
# Tipo generico/residuale da inserire manualmente
if doc.tipo and doc.tipo.codice == 'CLAV':
    excluded_count += 1
    continue
```

**Risultato**:
- ✅ 83 documenti CLAV esclusi dal dataset di training
- ✅ Log informativo: `ℹ️  Esclusi N documenti CLAV (Carte di lavoro)`
- ✅ Modello addestrato solo su tipi con pattern riconoscibili

### 2. Predictor - Filtr dall'Output

**File**: `ai_classifier/services/ml/predictor.py`

**Metodo**: `_get_top_predictions()`

```python
def _get_top_predictions(
    self,
    probabilities: np.ndarray,
    label_encoder,
    top_n: int = 3,
    exclude_types: List[str] = None,
) -> List[Tuple[str, float]]:
    """
    Ottiene le top N predizioni con confidence.
    
    Esclude automaticamente CLAV (Carte di lavoro) che è un tipo
    documento residuale/generico da inserire manualmente.
    """
    if exclude_types is None:
        exclude_types = ['CLAV']  # Default: escludi Carte di lavoro
    
    # Filtra tipi esclusi durante iterazione
    for idx in sorted_indices:
        label = label_encoder.inverse_transform([idx])[0]
        
        # Salta tipi esclusi (CLAV)
        if label in exclude_types:
            continue
        
        # ...
```

**Risultato**:
- ✅ CLAV **mai mostrato** tra i suggerimenti AI
- ✅ Filtro automatico applicato di default
- ✅ Top-N predictions saltano CLAV anche se ha confidence alta

---

## 🧪 Test Validazione

**File**: `test_clav_filter.py`

**Scenario test**:
```
Probabilità simulate:
  BIL   : 5%
  BPAG  : 10%
  CLAV  : 40%  ⚠️ DOVREBBE ESSERE ESCLUSO
  F24   : 30%
  FAT   : 15%
```

**Risultato atteso**: Top 3 = F24, FAT, BPAG (saltando CLAV)

**Output test**:
```
🎯 Top 3 Predizioni (con filtro CLAV):
   ✅ 1. F24: 30%
   ✅ 2. FAT: 15%
   ✅ 3. BPAG: 10%

✅ SUCCESS: CLAV correttamente escluso!
   Top 3 risultanti: F24, FAT, BPAG
```

✅ **Test PASSED**: CLAV correttamente filtrato dalle predizioni

---

## 📝 Comportamento Sistema

### Training (`python manage.py train_model`)
```bash
📖 Step 1/5: Estrazione features...
   Elaborando documento 50/445...
   ℹ️  Esclusi 83 documenti CLAV (Carte di lavoro)
   ✅ Features estratte: 362 documenti
```

### Predizione API (`POST /api/v1/ai-classifier/predict/`)
```json
{
  "predictions": {
    "tipo": {
      "all_predictions": [
        ["F24", 0.30],
        ["FAT", 0.15],
        ["BPAG", 0.10]
      ]
    }
  }
}
```
**Nota**: CLAV **non appare** anche se modello lo predice internamente

### Frontend (DocumentoFormPage)
```tsx
// Suggerimenti AI mostrati
🤖 Suggerimenti AI basati sul contenuto:
  • F24 (30%) 🔴
  • FAT (15%) 🔴
  • BPAG (10%) 🔴
```
**Nota**: CLAV **non viene mai suggerito** agli utenti

---

## 🎓 Estensibilità

Il parametro `exclude_types` consente di escludere altri tipi in futuro:

```python
# Esempio: escludere anche altri tipi generici
predictions = self._get_top_predictions(
    proba,
    label_encoder,
    top_n=5,
    exclude_types=['CLAV', 'VARI', 'TEMP']  # Custom list
)
```

---

## 🔄 Re-training con Esclusione CLAV

Quando si esegue re-training:

```bash
cd /home/sandro/mygest
source venv/bin/activate
python manage.py shell

>>> from ai_classifier.services.ml.model_trainer import ModelTrainer
>>> from documenti.models import Documento
>>> 
>>> docs = Documento.objects.filter(file__isnull=False).exclude(file='')
>>> trainer = ModelTrainer()
>>> model = trainer.train_initial_model(docs, version='v1.2.0_no_clav')
```

**Output**:
```
📊 Documenti totali da elaborare: 445
   ℹ️  Esclusi 83 documenti CLAV (Carte di lavoro)
   ✅ Features estratte: 362 documenti
   
📊 Modello: v1.2.0_no_clav
   Accuracy: 93.XX% (potenzialmente più alta!)
   Samples: 362
```

---

## ✅ Checklist Implementazione

- [x] Filtro CLAV nel `ModelTrainer._extract_features_from_documents()`
- [x] Log informativo numero documenti CLAV esclusi
- [x] Filtro CLAV nel `Predictor._get_top_predictions()`
- [x] Default `exclude_types=['CLAV']` nel metodo
- [x] Test unit del filtro CLAV
- [x] Documentazione modifiche

---

## 📚 File Modificati

```
ai_classifier/services/ml/
├── model_trainer.py    [MODIFIED] +filtro CLAV nel training
└── predictor.py        [MODIFIED] +filtro CLAV nelle predizioni

test_clav_filter.py     [CREATED] Test unit filtro
FEATURE_CLAV_EXCLUSION.md [CREATED] Questa documentazione
```

---

## 🎯 Conclusioni

✅ **CLAV (Carte di lavoro) escluso con successo**  
✅ **83 documenti generici non inquinano più il training**  
✅ **Predizioni più accurate su tipi strutturati**  
✅ **Frontend non suggerisce mai CLAV agli utenti**  
✅ **Sistema manterrà questa esclusione nei futuri re-training**

---

**Versione**: 1.0  
**Status**: ✅ Completato  
**Autore**: Sandro Chimenti
