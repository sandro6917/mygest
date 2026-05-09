/**
 * Types per AI-Assisted Document Import
 */

// ==================== TEMPLATE MODELS ====================

export interface ExtractionTemplateZone {
  id: number;
  nome_campo: string;
  etichetta: string;
  x_percent: number;
  y_percent: number;
  width_percent: number;
  height_percent: number;
  absolute_coordinates: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  tipo_dato: 'text' | 'codice_fiscale' | 'partita_iva' | 'date' | 'decimal' | 'integer' | 'email' | 'phone' | 'currency';
  obbligatorio: boolean;
  pattern_validazione?: string;
  ordine: number;
}

export interface ExtractionTemplatePage {
  id: number;
  numero_pagina: number;
  immagine_template: string;
  immagine_url: string;
  larghezza: number;
  altezza: number;
  zone: ExtractionTemplateZone[];
}

export interface ExtractionFieldMapping {
  id: number;
  nome_campo_template: string;
  tipo_campo_destinazione: 'field' | 'attribute' | 'note' | 'metadata';
  nome_campo_destinazione: string;
  funzione_trasformazione?: string;
  formato_input?: string;
  valore_default?: string;
}

export interface DocumentExtractionTemplate {
  id: number;
  tipo_documento: number;
  tipo_documento_id: number;
  tipo_documento_codice: string;
  tipo_documento_descrizione: string;
  nome: string;
  descrizione: string;
  numero_pagine: number;
  attivo: boolean;
  priorita: number;
  creato_il: string;
  aggiornato_il: string;
  creato_da?: number;
  creato_da_username?: string;
  pagine: ExtractionTemplatePage[];
  mapping_campi: ExtractionFieldMapping[];
}

export interface ExtractionCorrection {
  id: number;
  nome_campo: string;
  valore_estratto: string;
  valore_corretto: string;
  confidence_estrazione?: number;
  data_correzione: string;
}

export interface AIPredictionFeedback {
  id: number;
  documento: number;
  documento_codice: string;
  tipo_predetto: number;
  tipo_predetto_codice: string;
  confidence_predizione: number;
  top_3_predizioni: Array<{
    tipo_id: number;
    codice: string;
    confidence: number;
  }>;
  tipo_confermato: number;
  tipo_confermato_codice: string;
  predizione_corretta: boolean;
  dati_estratti_ai: Record<string, any>;
  utente?: number;
  utente_username?: string;
  data_predizione: string;
  usato_per_training: boolean;
  training_job?: number;
  correzioni: ExtractionCorrection[];
}

// ==================== REQUEST/RESPONSE TYPES ====================

export interface UploadDocumentRequest {
  file: File;
  filename?: string;
}

export interface UploadDocumentResponse {
  temp_file_path: string;
  ocr_text: string;
  page_count: number;
  ocr_method: string;
}

export interface PredictTypeRequest {
  temp_file_path?: string;
  ocr_text?: string;
  filename?: string;
}

export interface PredictionResult {
  tipo_documento_id: number;
  tipo_documento_codice: string;
  tipo_documento_descrizione: string;
  confidence: number;
  has_template: boolean;
}

export interface PredictTypeResponse {
  predictions: PredictionResult[];
  model_version: string;
  total_types: number;
}

export interface ExtractDataRequest {
  temp_file_path: string;
  tipo_documento_id: number;
  template_id?: number;
}

export interface ExtractedField {
  nome_campo: string;
  etichetta: string;
  valore: string | null;
  tipo_dato: string;
  confidence?: number;
  mapping: {
    tipo_campo_destinazione: string;
    nome_campo_destinazione: string;
    funzione_trasformazione?: string;
    formato_input?: string;
  };
  validazione_ok: boolean;
  errore_validazione?: string;
}

export interface ExtractDataResponse {
  template_id: number;
  template_nome: string;
  campi_estratti: ExtractedField[];
  note_generate: string;
  estrazione_completa: boolean;
}

export interface ConfirmPredictionRequest {
  documento_id: number;
  tipo_predetto_id: number;
  tipo_confermato_id: number;
  confidence_predizione: number;
  top_3_predizioni: Array<{
    tipo_id: number;
    codice: string;
    confidence: number;
  }>;
  dati_estratti_ai?: Record<string, any>;
}

export interface ConfirmPredictionResponse {
  feedback_id: number;
  predizione_corretta: boolean;
}

export interface SaveFeedbackRequest {
  feedback_id: number;
  correzioni: Array<{
    nome_campo: string;
    valore_estratto: string;
    valore_corretto: string;
    confidence_estrazione?: number;
  }>;
}

export interface SaveFeedbackResponse {
  correzioni_salvate: number;
}

// ==================== TEMPLATE MANAGEMENT ====================

export interface CreateTemplateRequest {
  tipo_documento: number;
  nome: string;
  descrizione?: string;
  numero_pagine?: number;
  attivo?: boolean;
  priorita?: number;
}

export interface CreateTemplatePageRequest {
  template_id: number;
  numero_pagina: number;
  immagine: File;
  larghezza: number;
  altezza: number;
}

export interface CreateTemplateZoneRequest {
  pagina_id: number;
  nome_campo: string;
  etichetta: string;
  x_percent: number;
  y_percent: number;
  width_percent: number;
  height_percent: number;
  tipo_dato: string;
  obbligatorio?: boolean;
  pattern_validazione?: string;
  ordine?: number;
}

export interface UpdateTemplateZoneRequest {
  nome_campo?: string;
  etichetta?: string;
  x_percent?: number;
  y_percent?: number;
  width_percent?: number;
  height_percent?: number;
  tipo_dato?: string;
  obbligatorio?: boolean;
  pattern_validazione?: string;
  ordine?: number;
}

export interface CreateFieldMappingRequest {
  template_id: number;
  nome_campo_template: string;
  tipo_campo_destinazione: 'field' | 'attribute' | 'note' | 'metadata';
  nome_campo_destinazione: string;
  funzione_trasformazione?: string;
  formato_input?: string;
  valore_default?: string;
}

// ==================== PAGINATED RESPONSE ====================

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
