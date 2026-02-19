# AI Classifier - Sistema di Classificazione Automatica Documenti

## 📋 Panoramica

**AI Classifier** è un'app Django per la classificazione automatica di documenti usando un approccio hybrid:
1. **Rule-based classification**: Pattern matching veloce su filename e contenuto
2. **LLM fallback**: OpenAI GPT-4o-mini per casi ambigui

### Tipologie Documenti Supportate
- **CED** - Cedolino
- **UNI** - Unilav
- **DIC** - Dichiarazione Fiscale
- **BIL** - Bilancio
- **F24** - F24
- **EST** - Estratto Conto
- **FAT** - Fattura
- **CON** - Contratto
- **COR** - Corrispondenza
- **PRO** - Protocollo
- **ALT** - Altro

---

## 🚀 Quick Start

### 1. Installazione Dipendenze

```bash
# Attiva virtual environment
source venv/bin/activate

# Installa dipendenze Python
pip install PyPDF2 pdfplumber pillow openai python-magic

# Su Linux, installa anche libmagic
sudo apt-get install libmagic1  # Debian/Ubuntu
```

### 2. Configurazione OpenAI API Key

```bash
# Aggiungi al file .env
echo "OPENAI_API_KEY=sk-your-api-key-here" >> .env

# Oppure esporta variabile ambiente
export OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Migrazioni Database

```bash
python manage.py migrate ai_classifier
```

### 4. Configurazione Iniziale

Accedi al Django Admin e vai su **AI Classifier > Configurazione Classificatore**:
- Verifica pattern di default (filename_patterns, content_patterns)
- Imposta threshold confidenza (default: 0.7)
- Configura estensioni permesse

---

## 📡 API Endpoints

### Base URL
```
/api/v1/ai-classifier/
```

### Jobs

#### Crea nuovo job
```http
POST /api/v1/ai-classifier/jobs/
Content-Type: application/json
Authorization: Bearer <token>

{
  "directory_path": "/path/to/documents",
  "use_llm": true,
  "llm_provider": "openai"
}
```

#### Avvia job
```http
POST /api/v1/ai-classifier/jobs/{id}/start/
Authorization: Bearer <token>
```

#### Lista jobs
```http
GET /api/v1/ai-classifier/jobs/
Authorization: Bearer <token>

# Filtri opzionali
?status=completed
?created_by=1
```

#### Dettaglio job
```http
GET /api/v1/ai-classifier/jobs/{id}/
Authorization: Bearer <token>
```

### Results

#### Lista risultati
```http
GET /api/v1/ai-classifier/results/
Authorization: Bearer <token>

# Filtri opzionali
?job=1
?predicted_type=CED
?confidence_level=high
?imported=false
?suggested_cliente=5
```

#### Dettaglio risultato
```http
GET /api/v1/ai-classifier/results/{id}/
Authorization: Bearer <token>
```

#### Aggiorna classificazione (manuale)
```http
PATCH /api/v1/ai-classifier/results/{id}/
Content-Type: application/json
Authorization: Bearer <token>

{
  "predicted_type": "UNI",
  "confidence_score": 0.95,
  "suggested_cliente": 10,
  "notes": "Corretto manualmente"
}
```

### Import

#### Importa batch documenti
```http
POST /api/v1/ai-classifier/import/documents/
Content-Type: application/json
Authorization: Bearer <token>

{
  "result_ids": [1, 2, 3, 4],
  "copy_files": true,
  "delete_source": false
}
```

**Response:**
```json
{
  "success": true,
  "imported_count": 4,
  "documents": [
    {"id": 101, "codice": "CLI001-TIT01-2024-001"},
    {"id": 102, "codice": "CLI002-TIT02-2024-005"}
  ]
}
```

### Config

#### Leggi configurazione
```http
GET /api/v1/ai-classifier/config/
Authorization: Bearer <token>
```

#### Aggiorna configurazione
```http
PUT /api/v1/ai-classifier/config/1/
Content-Type: application/json
Authorization: Bearer <token>

{
  "llm_model": "gpt-4o-mini",
  "llm_temperature": 0.1,
  "confidence_threshold": 0.75,
  "filename_patterns": {
    "CED": ["cedolino", "payslip", "busta paga"],
    "UNI": ["unilav", "comunicazione obbligatoria"]
  }
}
```

---

## 🔧 Workflow Completo

### 1. Crea Job
```bash
curl -X POST http://localhost:8000/api/v1/ai-classifier/jobs/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "directory_path": "/mnt/nas/documenti_da_importare",
    "use_llm": true
  }'
```

**Response:**
```json
{
  "id": 1,
  "directory_path": "/mnt/nas/documenti_da_importare",
  "status": "pending",
  "created_by": 1,
  "use_llm": true
}
```

### 2. Avvia Job
```bash
curl -X POST http://localhost:8000/api/v1/ai-classifier/jobs/1/start/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Il job processa **sincronamente**:
1. Scansiona directory (ricorsivamente)
2. Filtra file per estensione e dimensione
3. Estrae testo da PDF
4. Applica rule-based classification
5. Se confidenza < threshold, usa LLM
6. Salva risultati in ClassificationResult

### 3. Verifica Risultati
```bash
curl http://localhost:8000/api/v1/ai-classifier/results/?job=1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "file_name": "cedolino_gennaio_2024.pdf",
      "predicted_type": "CED",
      "predicted_type_display": "Cedolino",
      "confidence_score": 0.92,
      "confidence_level": "high",
      "classification_method": "rule",
      "suggested_cliente": null,
      "imported": false
    },
    {
      "id": 2,
      "file_name": "unilav_123456.pdf",
      "predicted_type": "UNI",
      "confidence_score": 0.65,
      "confidence_level": "medium",
      "classification_method": "llm",
      "imported": false
    }
  ]
}
```

### 4. (Opzionale) Correzioni Manuali
```bash
curl -X PATCH http://localhost:8000/api/v1/ai-classifier/results/2/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "predicted_type": "DIC",
    "confidence_score": 1.0,
    "suggested_cliente": 5,
    "notes": "Corretto: era dichiarazione, non unilav"
  }'
```

### 5. Importa in App Documenti
```bash
curl -X POST http://localhost:8000/api/v1/ai-classifier/import/documents/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "result_ids": [1, 2, 3],
    "copy_files": true,
    "delete_source": false
  }'
```

**Cosa succede:**
1. Per ogni result_id:
   - Crea `Documento` con tipo, cliente, titolario suggeriti
   - Copia file in NAS (percorso automatico)
   - Estrae metadata (data, importo, CF, etc.)
   - Genera titolo intelligente
   - Marca result come `imported=True`
2. Ritorna lista documenti creati

---

## 🎯 Logica di Classificazione

### Rule-Based
1. **Filename matching**: Controlla se filename contiene pattern specifici
   - Es: `cedolino_*.pdf` → CED
   - Es: `unilav_*.pdf` → UNI
   - Es: `*_F24.pdf` → F24

2. **Content matching**: Analizza testo estratto per keyword
   - Es: "cedolino paga" → CED
   - Es: "modello f24" → F24
   - Es: "bilancio di esercizio" → BIL

3. **Score calculation**:
   ```
   final_score = (filename_score * 0.5) + (content_score * 0.5)
   ```

4. **Confidence level**:
   - `high`: score >= 0.8
   - `medium`: 0.5 <= score < 0.8
   - `low`: score < 0.5

### LLM Fallback
Se `confidence_score < threshold` (default 0.7):
1. Invia a GPT-4o-mini:
   - Filename
   - Testo estratto (max 3000 chars)
   - Metadata estratti
2. Riceve JSON:
   ```json
   {
     "type": "CED",
     "confidence": 0.95,
     "reasoning": "Il documento contiene 'cedolino paga' e 'retribuzione lorda'"
   }
   ```

---

## 📊 Metadata Estratti

Il `MetadataExtractor` cerca automaticamente:
- **codice_fiscale**: Pattern CF italiano (16 caratteri)
- **partita_iva**: 11 cifre
- **data_documento**: Date in vari formati (DD/MM/YYYY, YYYY-MM-DD)
- **importo**: Importi in euro (€ 1.234,56)
- **anno**: Anno (2020-2030)
- **periodo_riferimento**: Es: "Gennaio 2024"

Metadata specifici per tipo:
- **CED**: `periodo_paga`, `retribuzione_lorda`
- **F24**: `codici_tributo`
- **UNI**: `tipo_comunicazione`

---

## 🔐 Sicurezza

### API Keys
- **Produzione**: Usa variabile ambiente `OPENAI_API_KEY`
- **Mai committare** API key nel codice
- In `ClassifierConfig`, il campo `openai_api_key` è `write_only` (non esposto in GET)

### Path Validation
- `PathValidator.sanitize_path()` previene directory traversal
- Solo directory esistenti e accessibili sono accettate
- Windows UNC paths supportati: `\\server\share`

### Permissions
- Tutti gli endpoint richiedono `IsAuthenticated`
- Users vedono solo i propri jobs (staff vede tutti)

---

## 🧪 Testing

```bash
# Run tutti i test
pytest ai_classifier/tests/

# Test specifici
pytest ai_classifier/tests/test_models.py
pytest ai_classifier/tests/test_utils.py

# Con coverage
pytest ai_classifier/tests/ --cov=ai_classifier --cov-report=html
```

---

## 📝 Esempi File Pattern

### Cedolini
```
cedolino_gennaio_2024.pdf
ROSSI_MARIO_CED_012024.pdf
payslip_2024_01.pdf
```

### Unilav
```
unilav_1234567890.pdf
CO_assunzione_ROSSI.pdf
comunicazione_obbligatoria.pdf
```

### Dichiarazioni
```
730_2023_ROSSI_MARIO.pdf
modello_redditi_2023.pdf
dichiarazione_XXXXXX.pdf
```

### F24
```
F24_gennaio_2024.pdf
delega_tributi_012024.pdf
modello_f24_XXXXXX.pdf
```

---

## 🚧 Troubleshooting

### Errore: "OpenAI API key non fornita"
```bash
# Verifica variabile ambiente
echo $OPENAI_API_KEY

# Se vuota, esportala
export OPENAI_API_KEY=sk-your-key
```

### Errore: "Directory non valida o inaccessibile"
```bash
# Verifica permessi
ls -la /path/to/directory

# Per Windows share, verifica mount
df -h | grep cifs
```

### Errore: "PyPDF2 non trovato"
```bash
pip install PyPDF2 pdfplumber pillow
```

### Errore: "python-magic: failed to find libmagic"
```bash
# Linux
sudo apt-get install libmagic1

# macOS
brew install libmagic

# Windows
# Usa installazione binaria: python-magic-bin
pip install python-magic-bin
```

### Performance: Job troppo lento
- **Riduci `max_pages`** in PDFExtractor (default 10)
- **Disabilita LLM** per batch grandi (`use_llm=false`)
- **Filtra directory** prima della scansione (solo file recenti)
- **Futura implementazione**: Celery per processing asincrono

---

## 🔄 Future Enhancements

### MVP (Fase 1) - ✅ COMPLETATO
- [x] Scanner directory (locale + NAS + SMB)
- [x] Estrazione testo PDF
- [x] Rule-based classification
- [x] LLM fallback (OpenAI)
- [x] API REST completa
- [x] Import in app documenti

### Fase 2 - Roadmap
- [ ] OCR per immagini (Tesseract)
- [ ] Estrazione metadata avanzata (NER con spaCy)
- [ ] Suggerimento automatico cliente (da CF/PIVA)
- [ ] Suggerimento fascicolo (da cliente + tipo)
- [ ] Processing asincrono (Celery)
- [ ] UI React (frontend)
- [ ] Batch import con preview
- [ ] Export statistiche classificazione

### Fase 3 - Ottimizzazioni
- [ ] LLM locali (Ollama + LLaMA)
- [ ] ML classifier training (scikit-learn)
- [ ] Cache risultati classificazione
- [ ] Webhook notifications
- [ ] Multi-language support

---

## 📚 Riferimenti

- **OpenAI GPT-4o-mini**: https://platform.openai.com/docs/models/gpt-4o-mini
- **PyPDF2**: https://pypdf2.readthedocs.io/
- **pdfplumber**: https://github.com/jsvine/pdfplumber
- **python-magic**: https://github.com/ahupp/python-magic

---

## 👨‍💻 Supporto

Per domande o problemi:
1. Controlla questa documentazione
2. Verifica logs: `logs/django.log`
3. Testa con esempi forniti in `ai_classifier/tests/`

---

**Versione**: 1.0.0 (MVP)  
**Data**: Febbraio 2025  
**Autore**: AI Classifier Team
