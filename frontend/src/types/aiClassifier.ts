/**
 * Types per AI Classifier Module
 */

export type JobStatus = 'pending' | 'running' | 'completed' | 'failed';
export type ConfidenceLevel = 'low' | 'medium' | 'high';
export type ClassificationMethod = 'rule_only' | 'llm' | 'hybrid';

export interface ClassificationJob {
  id: number;
  directory_path: string;
  status: JobStatus;
  status_display: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  total_files: number;
  processed_files: number;
  successful_files: number;
  failed_files: number;
  progress_percentage: number;
  errors: string[];
  use_llm: boolean;
  llm_provider: string;
  created_by: number;
  created_by_username: string;
}

export interface ClassificationResult {
  id: number;
  job: number;
  file_path: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  predicted_type: string;
  predicted_type_display: string;
  confidence_level: ConfidenceLevel;
  confidence_level_display: string;
  confidence_score: number;
  classification_method: ClassificationMethod;
  extracted_text: string;
  extracted_metadata: Record<string, any>;
  suggested_cliente: number | null;
  suggested_cliente_nome: string | null;
  suggested_fascicolo: number | null;
  suggested_fascicolo_nome: string | null;
  suggested_titolario: number | null;
  imported: boolean;
  documento: number | null;
  documento_codice: string | null;
  imported_at: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface ClassifierConfig {
  id: number;
  allowed_extensions: string[];
  max_file_size_mb: number;
  confidence_threshold: number;
  llm_model: string;
  openai_api_key: string;
  filename_patterns: Record<string, string[]>;
  content_patterns: Record<string, string[]>;
}

export interface CreateJobRequest {
  directory_path: string;
  use_llm: boolean;
  recursive?: boolean;
}

export interface ImportDocumentsRequest {
  result_ids: number[];
}

export interface ImportDocumentsResponse {
  success: boolean;
  imported_count: number;
  documents: Array<{
    id: number;
    codice: string;
    descrizione: string;
  }>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface JobStats {
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_files_processed: number;
  total_documents_imported: number;
}

// Tipi per ML Prediction API

export interface ParsedFields {
  parser_type: string;
  parsed_successfully: boolean;
  attributi: Record<string, any>;
  anagrafiche?: {
    datore?: {
      codice_fiscale: string;
      tipo: 'PF' | 'PG';
      denominazione: string;
    };
    lavoratore?: {
      codice_fiscale: string;
      tipo: 'PF';
      denominazione: string;
    };
  };
  descrizione_suggerita?: string;
}

export interface PredictResponse {
  success: boolean;
  predictions: {
    tipo: {
      top_prediction: string;
      confidence: number;
      all_predictions: Array<[string, number]>;
      meets_threshold: boolean;
    };
  };
  metadata: {
    extracted_features: {
      codici_fiscali: string[];
      partite_iva: string[];
      importi: string[];
      date: string[];
      entities_persone: number;
      entities_org: number;
      word_count: number;
    };
    ocr_method: string;
    ocr_pages: number;
    text_length: number;
    filename: string;
    parsed_fields?: ParsedFields;  // Campi specifici estratti (UNILAV, etc.)
  };
  model_info: {
    version: string;
    accuracy: number;
    trained_at: string;
  };
  error?: string;
  prediction_id?: number;
}
