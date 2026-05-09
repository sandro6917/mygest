# Fase 2: API Endpoints - COMPLETATA ✅

## 📋 Endpoint Creati

### 🚀 AI Import Workflow

Base URL: `/api/v1/ai-classifier/ai-import/`

#### 1. Upload Documento + OCR
```http
POST /api/v1/ai-classifier/ai-import/upload/
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Request:**
```json
{
  "file": <file_binary>,
  "filename": "documento.pdf" (opzionale)
}
```

**Response:**
```json
{
  "temp_file_path": "/tmp/ai_import_20260227_102030_documento.pdf",
  "ocr_text": "Testo estratto dal documento...",
  "page_count": 2,
  "ocr_method": "native"
}
```

---

#### 2. Predizione Tipo Documento (Top 3)
```http
POST /api/v1/ai-classifier/ai-import/predict/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request:**
```json
{
  "temp_file_path": "/tmp/ai_import_...",
  "ocr_text": "..." (alternativa a temp_file_path),
  "filename": "documento.pdf" (opzionale)
}
```

**Response:**
```json
{
  "predictions": [
    {
      "tipo_documento_id": 15,
      "tipo_documento_codice": "UNILAV",
      "tipo_documento_descrizione": "Comunicazione Obbligatoria Unilav",
      "confidence": 0.9234,
      "has_template": true
    },
    {
      "tipo_documento_id": 22,
      "tipo_documento_codice": "CEDOL",
      "tipo_documento_descrizione": "Cedolino Paga",
      "confidence": 0.0512,
      "has_template": true
    },
    {
      "tipo_documento_id": 8,
      "tipo_documento_codice": "FAT",
      "tipo_documento_descrizione": "Fattura",
      "confidence": 0.0123,
      "has_template": false
    }
  ],
  "model_version": "v1.2.3",
  "total_types": 51
}
```

---

#### 3. Estrazione Dati da Template
```http
POST /api/v1/ai-classifier/ai-import/extract/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request:**
```json
{
  "temp_file_path": "/tmp/ai_import_...",
  "tipo_documento_id": 15,
  "template_id": 5 (opzionale, usa priorità massima se omesso)
}
```

**Response:**
```json
{
  "template_id": 5,
  "template_nome": "UNILAV Standard 2026",
  "campi_estratti": [
    {
      "nome_campo": "codice_fiscale_datore",
      "etichetta": "Codice Fiscale Datore di Lavoro",
      "valore": "RSSMRA80A01H501X",
      "tipo_dato": "codice_fiscale",
      "confidence": 0.95,
      "mapping": {
        "tipo_campo_destinazione": "attribute",
        "nome_campo_destinazione": "attributo:cf_datore",
        "funzione_trasformazione": "normalize_cf",
        "formato_input": ""
      },
      "validazione_ok": true,
      "errore_validazione": null
    },
    {
      "nome_campo": "data_assunzione",
      "etichetta": "Data Assunzione",
      "valore": "15/01/2026",
      "tipo_dato": "date",
      "confidence": 0.88,
      "mapping": {
        "tipo_campo_destinazione": "field",
        "nome_campo_destinazione": "data_documento",
        "funzione_trasformazione": "parse_date_it",
        "formato_input": "DD/MM/YYYY"
      },
      "validazione_ok": true,
      "errore_validazione": null
    }
  ],
  "note_generate": "=== DATI ESTRATTI AI (UNILAV) ===\n\nCodice Fiscale Datore di Lavoro: RSSMRA80A01H501X\nData Assunzione: 15/01/2026\n\n[Auto-generato il 2026-02-27 10:25]",
  "estrazione_completa": true
}
```

---

#### 4. Conferma Predizione
```http
POST /api/v1/ai-classifier/ai-import/confirm-prediction/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request:**
```json
{
  "documento_id": 1234,
  "tipo_predetto_id": 15,
  "tipo_confermato_id": 15,
  "confidence_predizione": 0.9234,
  "top_3_predizioni": [
    {"tipo_id": 15, "codice": "UNILAV", "confidence": 0.9234},
    {"tipo_id": 22, "codice": "CEDOL", "confidence": 0.0512},
    {"tipo_id": 8, "codice": "FAT", "confidence": 0.0123}
  ],
  "dati_estratti_ai": {
    "codice_fiscale_datore": "RSSMRA80A01H501X",
    "data_assunzione": "15/01/2026"
  }
}
```

**Response:**
```json
{
  "feedback_id": 567,
  "predizione_corretta": true
}
```

---

#### 5. Salva Feedback Correzioni
```http
POST /api/v1/ai-classifier/ai-import/save-feedback/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request:**
```json
{
  "feedback_id": 567,
  "correzioni": [
    {
      "nome_campo": "data_assunzione",
      "valore_estratto": "15/01/2026",
      "valore_corretto": "16/01/2026",
      "confidence_estrazione": 0.88
    }
  ]
}
```

**Response:**
```json
{
  "correzioni_salvate": 1
}
```

---

### 🎨 Template Management

Base URL: `/api/v1/ai-classifier/templates/`

#### 1. Lista Template
```http
GET /api/v1/ai-classifier/templates/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "tipo_documento": 15,
      "tipo_documento_codice": "UNILAV",
      "tipo_documento_descrizione": "Comunicazione Obbligatoria Unilav",
      "nome": "UNILAV Standard 2026",
      "descrizione": "Template per UNILAV aggiornato 2026",
      "numero_pagine": 2,
      "attivo": true,
      "priorita": 10,
      "creato_il": "2026-02-20T14:30:00Z",
      "aggiornato_il": "2026-02-27T09:15:00Z",
      "creato_da": 1,
      "creato_da_username": "admin",
      "pagine": [...],
      "mapping_campi": [...]
    }
  ]
}
```

#### 2. Dettaglio Template
```http
GET /api/v1/ai-classifier/templates/{id}/
Authorization: Bearer <token>
```

#### 3. Crea Template
```http
POST /api/v1/ai-classifier/templates/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request:**
```json
{
  "tipo_documento": 15,
  "nome": "UNILAV Standard 2026",
  "descrizione": "Template per UNILAV...",
  "numero_pagine": 2,
  "attivo": true,
  "priorita": 10
}
```

#### 4. Aggiungi Pagina a Template
```http
POST /api/v1/ai-classifier/templates/{id}/add_page/
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Request:**
```json
{
  "template_id": 5,
  "numero_pagina": 1,
  "immagine": <file_binary>,
  "larghezza": 1920,
  "altezza": 2480
}
```

**Response:**
```json
{
  "id": 10,
  "numero_pagina": 1,
  "immagine_template": "/media/extraction_templates/2026/02/pagina1.png",
  "immagine_url": "http://example.com/media/extraction_templates/2026/02/pagina1.png",
  "larghezza": 1920,
  "altezza": 2480,
  "zone": []
}
```

#### 5. Aggiungi Zona Estrazione
```http
POST /api/v1/ai-classifier/templates/add_zone/
Content-Type: application/json
Authorization: Bearer <token>
```

**Request:**
```json
{
  "pagina_id": 10,
  "nome_campo": "codice_fiscale_datore",
  "etichetta": "Codice Fiscale Datore di Lavoro",
  "x_percent": 15.5,
  "y_percent": 22.3,
  "width_percent": 25.0,
  "height_percent": 3.5,
  "tipo_dato": "codice_fiscale",
  "obbligatorio": true,
  "pattern_validazione": "^[A-Z]{6}\\d{2}[A-Z]\\d{2}[A-Z]\\d{3}[A-Z]$",
  "ordine": 1
}
```

**Response:**
```json
{
  "id": 25,
  "nome_campo": "codice_fiscale_datore",
  "etichetta": "Codice Fiscale Datore di Lavoro",
  "x_percent": 15.5,
  "y_percent": 22.3,
  "width_percent": 25.0,
  "height_percent": 3.5,
  "absolute_coordinates": {
    "x": 297,
    "y": 553,
    "width": 480,
    "height": 87
  },
  "tipo_dato": "codice_fiscale",
  "obbligatorio": true,
  "pattern_validazione": "^[A-Z]{6}\\d{2}[A-Z]\\d{2}[A-Z]\\d{3}[A-Z]$",
  "ordine": 1
}
```

---

## 📁 File Creati

### Backend

1. **`/api/v1/ai_classifier/serializers_ai_import.py`** (450 righe)
   - Serializers per tutti i modelli AI import
   - Serializers request/response per endpoint workflow
   - Serializers per template management

2. **`/api/v1/ai_classifier/views_ai_import.py`** (740 righe)
   - `AIImportViewSet`: 6 endpoint workflow
     - `upload()` - Upload + OCR
     - `predict()` - Predizione top 3
     - `extract()` - Estrazione dati da template
     - `confirm_prediction()` - Salva conferma
     - `save_feedback()` - Salva correzioni
   - `TemplateManagementViewSet`: CRUD template
     - `list()`, `retrieve()`, `create()`, `update()`, `destroy()`
     - `add_page()` - Aggiungi pagina
     - `add_zone()` - Aggiungi zona
   - `ExtractionService`: Logica estrazione OCR da zone

3. **`/api/v1/ai_classifier/urls.py`** (modificato)
   - Aggiunto routing per `ai-import` e `templates`

---

## 🔧 Servizi Implementati

### ExtractionService

Classe helper per estrazione dati da template:

```python
class ExtractionService:
    def extract_from_template(file_path, template):
        """Estrae dati da tutte le zone del template"""
        
    def _extract_zone_value(file_path, pagina, zona):
        """Estrae valore da zona specifica (coordinate)"""
        
    def _search_pattern_in_text(text, zona):
        """Cerca pattern nel testo (CF, P.IVA, date, email, etc.)"""
        
    def _validate_field(valore, zona):
        """Valida campo estratto (obbligatorio, pattern)"""
```

**Note**: Implementazione attuale semplificata:
- Estrae tutto il testo OCR (non solo zona specifica)
- Cerca pattern regex nel testo completo
- **TODO**: Implementare OCR di zona specifica usando coordinate

---

## 🧪 Test degli Endpoint

### Test Workflow Completo

```bash
# 1. Upload
curl -X POST http://localhost:8000/api/v1/ai-classifier/ai-import/upload/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/documento.pdf"

# 2. Predict
curl -X POST http://localhost:8000/api/v1/ai-classifier/ai-import/predict/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"temp_file_path": "/tmp/ai_import_...", "filename": "documento.pdf"}'

# 3. Extract
curl -X POST http://localhost:8000/api/v1/ai-classifier/ai-import/extract/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"temp_file_path": "/tmp/ai_import_...", "tipo_documento_id": 15}'

# 4. Confirm
curl -X POST http://localhost:8000/api/v1/ai-classifier/ai-import/confirm-prediction/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"documento_id": 1234, "tipo_predetto_id": 15, "tipo_confermato_id": 15, ...}'

# 5. Feedback
curl -X POST http://localhost:8000/api/v1/ai-classifier/ai-import/save-feedback/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"feedback_id": 567, "correzioni": [...]}'
```

---

## ✅ Stato Implementazione

### Completato
- ✅ 6 endpoint workflow AI import
- ✅ CRUD template management
- ✅ Serializers completi per request/response
- ✅ ExtractionService per OCR + pattern matching
- ✅ Validazione campi (obbligatori, pattern regex)
- ✅ Auto-generazione note da dati estratti
- ✅ Tracking feedback e correzioni
- ✅ URL routing configurato
- ✅ Django check passed (no errors)

### TODO (Ottimizzazioni Future)
- ⏳ OCR di zona specifica usando coordinate (attualmente estrae tutto)
- ⏳ Confidence OCR per singola zona
- ⏳ Funzioni trasformazione dati (parse_date_it, normalize_cf, etc.)
- ⏳ Batch processing template (multiple documents)
- ⏳ Template versioning
- ⏳ Performance optimization (caching, async OCR)

---

## 🎯 Prossimi Passi - Fase 3

Fase 3: **Admin Template Manager (Frontend)**

Obiettivo: Creare interfaccia React per:
1. Upload template image per tipo documento
2. Visual zone drawing tool (canvas-based)
3. Definizione mapping campi
4. Test estrazione su documenti reali

Tecnologie proposte:
- **react-konva** o **fabric.js** per disegno zone
- **Canvas API** per rendering immagine template
- **Material-UI** per UI components
- **React Query** per data fetching

Vuoi procedere con la Fase 3? 🚀
