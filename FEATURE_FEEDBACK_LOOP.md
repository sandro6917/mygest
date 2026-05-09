# Feedback Loop - Sistema di Apprendimento Continuo

**Data implementazione**: 25 Febbraio 2026  
**Status**: ✅ Completato  
**Versione**: 1.0

---

## 🎯 Obiettivo

Implementare un sistema di **continuous learning** che:
1. ✅ Monitora automaticamente le predizioni del modello ML
2. ✅ Confronta predizioni con valori reali inseriti dagli utenti
3. ✅ Raccoglie documenti con predizioni errate in una coda
4. ✅ Re-addestra periodicamente il modello con le correzioni
5. ✅ Migliora progressivamente l'accuracy del sistema

---

## 📊 Architettura Feedback Loop

```
┌─────────────────────────────────────────────────────────┐
│                   UTENTE                                │
│   Carica documento → Sistema predice tipo              │
│   Utente conferma o corregge tipo manualmente          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│         DJANGO SIGNAL (post_save Documento)            │
│                                                         │
│  1. Esegue predizione automatica su file               │
│  2. Crea DocumentPrediction (predetto vs reale)       │
│  3. Se diversi → aggiunge a TrainingQueue              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│            TRAINING QUEUE                               │
│  Accumula documenti con:                               │
│  - Predizioni errate (alta priorità)                   │
│  - Feedback manuale utenti                             │
│  - Nuovi tipi documento                                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼ (Cron: ogni notte 02:00)
┌─────────────────────────────────────────────────────────┐
│      MANAGEMENT COMMAND: retrain_ml_model              │
│                                                         │
│  1. Verifica documenti in coda (min 20)               │
│  2. Combina vecchi + nuovi documenti                   │
│  3. Re-training modello ML                             │
│  4. Confronta accuracy nuovo vs vecchio                │
│  5. Auto-attiva se migliora ≥2%                        │
│  6. Svuota TrainingQueue                               │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Componenti Implementati

### 1. Django Signal - Auto-Predizione

**File**: `ai_classifier/signals.py`

**Trigger**: `post_save` sul modello `Documento`

**Logica**:
```python
@receiver(post_save, sender=Documento)
def auto_predict_on_documento_save(sender, instance, created, **kwargs):
    # 1. Skip se documento senza file o tipo CLAV
    if not instance.file or not instance.tipo:
        return
    if instance.tipo.codice == 'CLAV':
        return
    
    # 2. Esegui predizione
    predictor = Predictor()
    result = predictor.predict(instance.file.path)
    
    # 3. Crea/aggiorna DocumentPrediction
    DocumentPrediction.objects.update_or_create(
        documento=instance,
        defaults={
            'predicted_tipo': result['tipo'],
            'confidence': result['confidence'],
            'actual_tipo': instance.tipo.codice,
            'is_correct': (predicted == actual),
            'user_corrected': (predicted != actual),
        }
    )
    
    # 4. Se errato → aggiungi a TrainingQueue
    if predicted != actual:
        TrainingQueue.objects.create(
            documento=instance,
            priority=2 if confidence > 0.5 else 1,  # Alta priority se era sicuro ma sbagliato
        )
```

**Attivazione**: Automatico tramite `ai_classifier/apps.py`

**Logging**: 
```
🤖 Auto-predizione per Documento #123 (tipo: FAT)
   Predetto: BPAG (confidence: 85%)
   Reale: FAT
   ✅ DocumentPrediction creata (ID: 456)
   📥 Aggiunto a TrainingQueue (predizione errata)
```

---

### 2. Management Command - Re-training

**File**: `ai_classifier/management/commands/retrain_ml_model.py`

**Usage**:
```bash
python manage.py retrain_ml_model [OPTIONS]
```

**Opzioni**:
- `--min-samples N`: Minimo documenti in coda (default: 20)
- `--auto-activate`: Attiva automaticamente nuovo modello se migliora
- `--improvement-threshold P`: Soglia miglioramento (default: 0.02 = 2%)
- `--dry-run`: Simula senza salvare (per test)

**Workflow**:
```
1. Verifica documenti in TrainingQueue
   └─ Se < min-samples → esci
   
2. Carica modello attivo corrente
   └─ Ottieni metriche baseline
   
3. Prepara dataset training
   ├─ Vecchi documenti (tutti con file, escluso CLAV)
   └─ Nuovi documenti (dalla coda, escluso CLAV)
   
4. Crea TrainingJob (status: running)

5. Esegui re-training
   ├─ Combina vecchi + nuovi
   ├─ Estrai features (esclude CLAV)
   ├─ Train RandomForest
   └─ Salva nuovo modello (v1.X.0)
   
6. Confronta metriche
   ├─ Accuracy improvement = nuovo - vecchio
   └─ Decision: attivare nuovo modello?
   
7. Attivazione condizionale
   ├─ Se improvement ≥ threshold → attiva
   ├─ Se auto-activate && improvement > 0 → attiva
   └─ Altrimenti → mantieni vecchio
   
8. Aggiorna TrainingJob (status: completed/failed)

9. Svuota TrainingQueue
   └─ Marca documenti come processed
```

**Output**:
```
======================================================================
🔄 RE-TRAINING MODELLO ML
======================================================================

📊 Documenti in TrainingQueue: 25

📦 Modello attivo corrente:
   Versione: v1.0.0_20260225_162701
   Accuracy: 92.96%
   Samples: 386

📚 Dataset training:
   Documenti esistenti: 362
   Nuovi documenti: 25
   Totale: 387

🚀 TrainingJob #5 avviato...
🤖 Training in corso su 387 documenti...
[... training logs ...]

======================================================================
✅ RE-TRAINING COMPLETATO
======================================================================

📊 Confronto Modelli:

   PRECEDENTE (v1.0.0_20260225_162701):
      Accuracy:  92.96%
      Samples:   386

   NUOVO (v1.1.0_20260225_230000):
      Accuracy:  94.15%
      Samples:   387

   📈 Miglioramento: +1.19%

🎯 Decisione attivazione:
   Accuracy migliorata di 1.19% (soglia: 2%)
   ⚠️  Nuovo modello NON attivato (mantieni v1.0.0)

✅ 25 documenti rimossi dalla TrainingQueue
```

---

### 3. Cron Job - Scheduling Automatico

**File**: `scripts/cron_retrain_ml.sh`

**Installazione**:
```bash
# 1. Rendi eseguibile
chmod +x /srv/mygest/app/scripts/cron_retrain_ml.sh

# 2. Aggiungi a crontab
crontab -e

# 3. Aggiungi questa riga (esegue ogni notte alle 02:00)
0 2 * * * /srv/mygest/app/scripts/cron_retrain_ml.sh >> /srv/mygest/logs/cron_retrain.log 2>&1
```

**Script**:
```bash
#!/bin/bash
PROJECT_DIR="/srv/mygest/app"
VENV_DIR="$PROJECT_DIR/venv"

cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"

python manage.py retrain_ml_model \
    --min-samples 20 \
    --auto-activate \
    --improvement-threshold 0.02
```

**Log file**: `/srv/mygest/logs/cron_retrain.log`

---

### 4. Frontend - Suggerimenti AI (già implementato)

**File**: `frontend/src/pages/DocumentoFormPage.tsx`

**UI Features**:
- ✅ Auto-predizione su file upload
- ✅ Spinner loading durante analisi
- ✅ Box suggerimenti con top 3 predictions
- ✅ Badges colorati per confidence
- ✅ Click su suggerimento per auto-selezione tipo

**Feedback implicito**:
- Quando utente seleziona tipo diverso da predizione → Django signal rileva differenza
- DocumentPrediction salvato con `user_corrected=True`
- Documento aggiunto automaticamente a TrainingQueue

---

## 📈 Metriche e Monitoring

### DocumentPrediction - Storico Predizioni

```sql
SELECT 
    COUNT(*) as total_predictions,
    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct,
    AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) * 100 as accuracy,
    AVG(confidence) * 100 as avg_confidence
FROM ai_classifier_documentprediction;
```

### TrainingQueue - Documenti in Attesa

```sql
SELECT COUNT(*) as pending_documents
FROM ai_classifier_trainingqueue
WHERE processed = FALSE;
```

### TrainingJob - Storico Re-training

```sql
SELECT 
    id,
    status,
    started_at,
    completed_at,
    accuracy_improvement,
    activated
FROM ai_classifier_trainingjob
ORDER BY started_at DESC
LIMIT 10;
```

---

## 🧪 Testing

### Test 1: Signal Auto-Predizione

```python
from documenti.models import Documento, DocumentiTipo
from ai_classifier.models import DocumentPrediction, TrainingQueue

# Crea documento con file
doc = Documento.objects.create(
    tipo=DocumentiTipo.objects.get(codice='FAT'),
    file='/path/to/fattura.pdf',
    # ... altri campi
)

# Verifica DocumentPrediction creato
assert DocumentPrediction.objects.filter(documento=doc).exists()

# Se predizione errata, verifica in TrainingQueue
pred = DocumentPrediction.objects.get(documento=doc)
if not pred.is_correct:
    assert TrainingQueue.objects.filter(documento=doc).exists()
```

### Test 2: Management Command Dry-Run

```bash
python manage.py retrain_ml_model --dry-run --min-samples 5
```

**Output atteso**:
```
⚠️  Modalità DRY-RUN: nessuna modifica sarà salvata
📊 Documenti in TrainingQueue: 0
⚠️  Documenti insufficienti per re-training (minimo: 5)
```

### Test 3: Re-training Reale (manuale)

```bash
# 1. Aggiungi documenti alla coda manualmente (per test)
python manage.py shell
>>> from documenti.models import Documento
>>> from ai_classifier.models import TrainingQueue
>>> docs = Documento.objects.filter(file__isnull=False)[:25]
>>> for doc in docs:
...     TrainingQueue.objects.get_or_create(documento=doc, priority=1)

# 2. Esegui re-training
python manage.py retrain_ml_model --min-samples 20 --auto-activate

# 3. Verifica nuovo modello
>>> from ai_classifier.models import MLModel
>>> MLModel.objects.filter(is_active=True).first()
<MLModel: v1.1.0_...>
```

---

## 🎓 Best Practices

### Frequency Re-training
- **Daily** (raccomandato): Cron alle 02:00, min 20 documenti
- **Weekly**: Cron domenica notte, min 50 documenti
- **On-demand**: Manuale quando necessario

### Soglie Attivazione
- **Conservative** (default): ≥2% improvement
- **Aggressive**: ≥1% improvement o `--auto-activate`
- **Manual**: No auto-attivazione, review manuale

### Priority TrainingQueue
- **Priority 3**: Nuovi tipi documento (massima)
- **Priority 2**: Predizioni errate con alta confidence
- **Priority 1**: Predizioni errate con bassa confidence

### Esclusioni
- ✅ CLAV sempre escluso (tipo generico)
- ✅ Documenti senza file esclusi
- ✅ Documenti con errori OCR loggati ma non bloccanti

---

## 🔍 Troubleshooting

### Signal non si attiva
**Sintomo**: Documenti salvati ma nessuna predizione automatica

**Verifica**:
```python
# Check signal registrato
from django.db.models import signals
print(signals.post_save._live_receivers(Documento))  # Deve contenere auto_predict_on_documento_save
```

**Soluzione**: Verifica `ai_classifier/apps.py` importa signals in `ready()`

### Re-training fallisce
**Sintomo**: TrainingJob status='failed'

**Verifica log**:
```python
from ai_classifier.models import TrainingJob
job = TrainingJob.objects.latest('started_at')
print(job.error_message)
```

**Cause comuni**:
- Modello ML attivo non trovato
- File documento corrotto/mancante
- Memoria insufficiente per training
- Errore OCR su alcuni documenti

### Accuracy non migliora
**Sintomo**: Re-training completato ma accuracy stessa o peggiore

**Possibili cause**:
- Documenti in coda troppo simili a esistenti
- Dataset sbilanciato (SMOTE non sufficiente)
- Nuovi documenti con qualità OCR scarsa
- Iperparametri modello da ottimizzare

**Soluzione**: Review manuale documenti in coda, verifica qualità OCR

---

## 📚 File Creati/Modificati

```
ai_classifier/
├── signals.py                              [CREATED] 130 lines
├── apps.py                                 [MODIFIED] +import signals
├── management/
│   ├── __init__.py                         [CREATED]
│   └── commands/
│       ├── __init__.py                     [CREATED]
│       └── retrain_ml_model.py             [CREATED] 290 lines

scripts/
└── cron_retrain_ml.sh                      [CREATED] Cron job script

FEATURE_FEEDBACK_LOOP.md                    [CREATED] Questa documentazione
```

---

## ✅ Checklist Implementazione

- [x] Django signal `post_save` per auto-predizione
- [x] Creazione `DocumentPrediction` su ogni salvataggio
- [x] Auto-aggiunta a `TrainingQueue` se predizione errata
- [x] Management command `retrain_ml_model`
- [x] Opzioni: `--min-samples`, `--auto-activate`, `--dry-run`
- [x] Confronto metriche vecchio vs nuovo modello
- [x] Attivazione condizionale basata su threshold
- [x] Logging dettagliato con output colorato
- [x] Script Cron job per scheduling notturno
- [x] Documentazione completa
- [x] Frontend già implementato (suggerimenti AI)

---

## 🎯 Risultati Attesi

### Scenario Tipico

**Mese 1**:
- Modello iniziale: 92.96% accuracy (386 samples)
- Utenti caricano 50 documenti/settimana
- ~10 predizioni errate/settimana
- Re-training settimanale: +1-2% accuracy

**Mese 3**:
- Modello v1.5.0: 95-96% accuracy (600+ samples)
- Predizioni errate: ~5/settimana
- Re-training: +0.5-1% accuracy

**Mese 6**:
- Modello v2.0.0: 97-98% accuracy (800+ samples)
- Sistema stabile, re-training meno frequente
- Focus su nuovi tipi documento

---

## 🚀 Prossimi Miglioramenti

### Fase 2 (Futuro)
- [ ] Dashboard web per monitoring metriche
- [ ] Alert email su accuracy drop
- [ ] A/B testing tra modelli diversi
- [ ] Feedback manuale esplicito (pulsante "Segnala errore")
- [ ] Export/import modelli per backup
- [ ] Multi-model ensemble (RandomForest + SVM + NN)

---

**Versione**: 1.0  
**Status**: ✅ Completato  
**Autore**: Sandro Chimenti  
**Data**: 25 Febbraio 2026
