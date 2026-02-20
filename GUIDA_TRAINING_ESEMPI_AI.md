# 📚 Guida: Istruire il Sistema AI con Esempi

Il sistema AI Classifier può essere "addestrato" fornendo esempi di documenti già classificati. Questo migliora significativamente l'accuratezza della classificazione automatica usando la tecnica del **Few-Shot Learning**.

## 🎯 Come Funziona

Quando crei esempi di training:
1. **Il sistema estrae** testo e metadata dal documento
2. **L'AI impara** le caratteristiche distintive di quel tipo
3. **Nelle classificazioni future**, l'AI usa gli esempi come riferimento

Esempio: Se fornisci 2-3 cedolini veri, l'AI capirà meglio come riconoscere cedolini simili.

---

## 📁 Metodo 1: Organizza Directory

### Struttura Directory

Crea una directory con sottocartelle per tipo documento:

```
/path/to/training_data/
├── CED/
│   ├── cedolino_gennaio_2024.pdf
│   ├── cedolino_febbraio_2024.pdf
│   └── cedolino_marzo_2024.pdf
├── DIC/
│   ├── 730_2024_rossi.pdf
│   ├── unico_2023_bianchi.pdf
│   └── redditi_pf_2024.pdf
├── F24/
│   ├── f24_gen_2024.pdf
│   └── f24_feb_2024.pdf
└── UNI/
    ├── unilav_assunzione.pdf
    └── unilav_trasformazione.pdf
```

### Importazione Automatica

```bash
# Import dalla directory
python manage.py import_training_examples /path/to/training_data/ --user admin

# Con priorità alta (esempi più importanti)
python manage.py import_training_examples /path/to/training_data/ --priority 10

# Sovrascrivi esempi esistenti
python manage.py import_training_examples /path/to/training_data/ --overwrite
```

**Output**:
```
📚 Importazione Esempi di Training
Directory: /path/to/training_data/
Utente: admin
============================================================

📁 Processing type: CED
  ✅ Importato: cedolino_gennaio_2024.pdf (2345 chars)
  ✅ Importato: cedolino_febbraio_2024.pdf (2298 chars)

📁 Processing type: DIC
  ✅ Importato: 730_2024_rossi.pdf (5678 chars)

...

============================================================
✅ Importati: 8
⏭️  Saltati: 0
❌ Errori: 0

💡 Tip: Gli esempi sono ora disponibili per il Few-Shot Learning!
```

---

## 🖥️ Metodo 2: Django Admin

### Accedi all'Admin

1. Vai su: `http://yourserver/admin/`
2. Login con credenziali admin
3. Naviga a: **AI Classifier** → **Training Examples**

### Crea Esempio Manualmente

1. Click **"Add Training Example"**
2. Compila i campi:
   - **File name**: Nome del file esempio (es. `cedolino_gennaio_2024.pdf`)
   - **File path**: Path completo (opzionale, utile per riferimento)
   - **Document type**: Codice tipo (es. `CED`, `DIC`, `F24`)
   - **Description**: Descrizione caratteristiche distintive
   - **Extracted text**: Testo estratto dal documento (può essere copiato/incollato)
   - **Extracted metadata**: JSON con metadata estratti (opzionale)
   - **Is active**: ✅ (attivo per usarlo nel training)
   - **Priority**: Numero (più alto = più importante)

3. Click **"Save"**

### Gestione Esempi

- ✅ **Attiva/Disattiva**: Seleziona esempi → Actions → "Attiva/Disattiva esempi selezionati"
- 🔝 **Priorità Alta**: Seleziona esempi → Actions → "Imposta priorità alta (10)"
- 📋 **Filtra**: Usa filtri laterali per tipo, stato, priorità
- 🔍 **Cerca**: Campo ricerca per nome file o descrizione

---

## 🎓 Best Practices

### Quanti Esempi?

- **Minimo**: 1-2 esempi per tipo
- **Ottimale**: 2-3 esempi per tipo
- **Massimo**: 5 esempi per tipo (oltre non migliora molto)

Il sistema carica automaticamente **max 2 esempi per tipo** (configurabile).

### Quali Documenti Scegliere?

✅ **Buoni esempi**:
- Documenti **tipici** e rappresentativi
- Con **testo chiaro** e leggibile
- Diversi tra loro (es. cedolini di mesi diversi)

❌ **Evita**:
- Documenti corrotti o illeggibili
- Duplicati identici
- Documenti troppo specifici/anomali

### Priorità

- **10**: Esempi eccellenti, molto rappresentativi
- **5**: Esempi standard (default)
- **0-3**: Esempi meno rilevanti

Gli esempi con priorità alta vengono mostrati per primi all'AI.

---

## 🔍 Verifica Funzionamento

### Dopo Importazione

1. **Controlla Admin**:
   - Vai su **Training Examples**
   - Verifica che gli esempi siano **attivi** (✅)
   - Controlla che **extracted_text** contenga testo

2. **Crea Nuovo Job**:
   - Vai su `/ai-classifier/jobs`
   - Crea nuovo job con **"Usa AI"** attivo
   - Avvia classificazione

3. **Verifica Log**:
   ```
   ✅ LLM classifier enabled with model gpt-4o-mini
   📚 Loaded 8 training examples for 4 types
   ```

4. **Controlla Risultati**:
   - I documenti simili agli esempi dovrebbero avere **confidence > 0.90**
   - Il campo **reasoning** dovrebbe menzionare caratteristiche degli esempi

---

## 📊 Esempio Completo

### Directory Training Data

```bash
mkdir -p /tmp/training_examples/{CED,DIC,F24,UNI}

# Copia documenti esempio (assicurati di avere PDF veri)
cp /path/to/cedolino1.pdf /tmp/training_examples/CED/
cp /path/to/cedolino2.pdf /tmp/training_examples/CED/
cp /path/to/730.pdf /tmp/training_examples/DIC/
cp /path/to/unico.pdf /tmp/training_examples/DIC/
```

### Import

```bash
python manage.py import_training_examples /tmp/training_examples/ --user admin --priority 10
```

### Verifica

```python
# Shell Django
from ai_classifier.models import TrainingExample

# Conta esempi
print(f"Total examples: {TrainingExample.objects.filter(is_active=True).count()}")

# Per tipo
for doc_type in ['CED', 'DIC', 'F24', 'UNI']:
    count = TrainingExample.objects.filter(document_type=doc_type, is_active=True).count()
    print(f"{doc_type}: {count} examples")

# Esempi caricati per LLM
examples = TrainingExample.get_all_active_examples(max_per_type=2)
for doc_type, exs in examples.items():
    print(f"{doc_type}: {len(exs)} examples loaded for LLM")
```

---

## 🚀 Ricarica Esempi (Advanced)

Se aggiungi nuovi esempi mentre un job è in esecuzione, puoi ricaricare dinamicamente:

```python
# In Django shell
from ai_classifier.services.llm.openai_client import OpenAIClassifier

# Crea nuovo classifier con esempi aggiornati
classifier = OpenAIClassifier(
    api_key="your-key",
    use_examples=True
)

# Oppure ricarica su classifier esistente
classifier.reload_examples()
```

---

## ❓ FAQ

**Q: Gli esempi vengono usati sempre?**  
A: Sì, se `use_examples=True` (default) e ci sono esempi attivi nel database.

**Q: Quanto costa?**  
A: Gli esempi aumentano leggermente il costo (~+10-20% token), ma migliorano molto l'accuratezza.

**Q: Devo riavviare Django?**  
A: No, gli esempi sono caricati dal database a runtime.

**Q: Posso disattivare il Few-Shot Learning?**  
A: Sì, imposta `use_examples=False` nell'inizializzazione di OpenAIClassifier.

---

## 📝 Riepilogo Comandi

```bash
# Import da directory organizzata
python manage.py import_training_examples /path/to/training_data/

# Con opzioni
python manage.py import_training_examples /path/to/training_data/ \
    --user admin \
    --priority 10 \
    --overwrite

# Verifica esempi
python manage.py shell -c "
from ai_classifier.models import TrainingExample
print(f'Active examples: {TrainingExample.objects.filter(is_active=True).count()}')
"
```

---

🎯 **Risultato**: Il sistema AI impara dai tuoi documenti reali e migliora progressivamente! 🚀
