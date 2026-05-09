/**
 * API Service per AI-Assisted Document Import
 */
import { apiClient } from './client';
import type {
  DocumentExtractionTemplate,
  ExtractionTemplatePage,
  ExtractionTemplateZone,
  ExtractionFieldMapping,
  AIPredictionFeedback,
  UploadDocumentRequest,
  UploadDocumentResponse,
  PredictTypeRequest,
  PredictTypeResponse,
  ExtractDataRequest,
  ExtractDataResponse,
  ConfirmPredictionRequest,
  ConfirmPredictionResponse,
  SaveFeedbackRequest,
  SaveFeedbackResponse,
  CreateTemplateRequest,
  CreateTemplatePageRequest,
  CreateTemplateZoneRequest,
  UpdateTemplateZoneRequest,
  CreateFieldMappingRequest,
  PaginatedResponse,
} from '@/types/aiImport';

const BASE_URL = '/ai-classifier';

export const aiImportApi = {
  // ==================== AI IMPORT WORKFLOW ====================
  
  /**
   * Upload documento e estrazione OCR
   */
  upload: async (request: UploadDocumentRequest): Promise<UploadDocumentResponse> => {
    const formData = new FormData();
    formData.append('file', request.file);
    if (request.filename) {
      formData.append('filename', request.filename);
    }
    
    const { data } = await apiClient.post<UploadDocumentResponse>(
      `${BASE_URL}/ai-import/upload/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return data;
  },

  /**
   * Predizione tipo documento (top 3)
   */
  predict: async (request: PredictTypeRequest): Promise<PredictTypeResponse> => {
    const { data } = await apiClient.post<PredictTypeResponse>(
      `${BASE_URL}/ai-import/predict/`,
      request
    );
    return data;
  },

  /**
   * Estrazione dati da template
   */
  extract: async (request: ExtractDataRequest): Promise<ExtractDataResponse> => {
    const { data } = await apiClient.post<ExtractDataResponse>(
      `${BASE_URL}/ai-import/extract/`,
      request
    );
    return data;
  },

  /**
   * Conferma predizione utente
   */
  confirmPrediction: async (request: ConfirmPredictionRequest): Promise<ConfirmPredictionResponse> => {
    const { data } = await apiClient.post<ConfirmPredictionResponse>(
      `${BASE_URL}/ai-import/confirm-prediction/`,
      request
    );
    return data;
  },

  /**
   * Salva feedback correzioni
   */
  saveFeedback: async (request: SaveFeedbackRequest): Promise<SaveFeedbackResponse> => {
    const { data } = await apiClient.post<SaveFeedbackResponse>(
      `${BASE_URL}/ai-import/save-feedback/`,
      request
    );
    return data;
  },

  // ==================== TEMPLATE MANAGEMENT ====================

  /**
   * Lista template di estrazione
   */
  listTemplates: async (params?: Record<string, any>): Promise<PaginatedResponse<DocumentExtractionTemplate>> => {
    const { data } = await apiClient.get<PaginatedResponse<DocumentExtractionTemplate>>(
      `${BASE_URL}/templates/`,
      { params }
    );
    return data;
  },

  /**
   * Dettaglio template
   */
  getTemplate: async (id: number): Promise<DocumentExtractionTemplate> => {
    const { data } = await apiClient.get<DocumentExtractionTemplate>(
      `${BASE_URL}/templates/${id}/`
    );
    return data;
  },

  /**
   * Crea template
   */
  createTemplate: async (request: CreateTemplateRequest): Promise<DocumentExtractionTemplate> => {
    const { data } = await apiClient.post<DocumentExtractionTemplate>(
      `${BASE_URL}/templates/`,
      request
    );
    return data;
  },

  /**
   * Aggiorna template
   */
  updateTemplate: async (id: number, request: Partial<CreateTemplateRequest>): Promise<DocumentExtractionTemplate> => {
    const { data } = await apiClient.patch<DocumentExtractionTemplate>(
      `${BASE_URL}/templates/${id}/`,
      request
    );
    return data;
  },

  /**
   * Elimina template
   */
  deleteTemplate: async (id: number): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/templates/${id}/`);
  },

  /**
   * Aggiungi pagina a template
   */
  addTemplatePage: async (templateId: number, request: CreateTemplatePageRequest): Promise<ExtractionTemplatePage> => {
    const formData = new FormData();
    formData.append('template_id', templateId.toString());
    formData.append('numero_pagina', request.numero_pagina.toString());
    formData.append('immagine', request.immagine);
    formData.append('larghezza', request.larghezza.toString());
    formData.append('altezza', request.altezza.toString());
    
    const { data } = await apiClient.post<ExtractionTemplatePage>(
      `${BASE_URL}/templates/${templateId}/add_page/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return data;
  },

  /**
   * Aggiungi zona estrazione
   */
  addTemplateZone: async (request: CreateTemplateZoneRequest): Promise<ExtractionTemplateZone> => {
    const { data } = await apiClient.post<ExtractionTemplateZone>(
      `${BASE_URL}/templates/add_zone/`,
      request
    );
    return data;
  },

  /**
   * Aggiorna zona estrazione
   */
  updateTemplateZone: async (zoneId: number, request: UpdateTemplateZoneRequest): Promise<ExtractionTemplateZone> => {
    const { data } = await apiClient.patch<ExtractionTemplateZone>(
      `${BASE_URL}/templates/zones/${zoneId}/`,
      request
    );
    return data;
  },

  /**
   * Elimina zona estrazione
   */
  deleteTemplateZone: async (zoneId: number): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/templates/zones/${zoneId}/`);
  },

  /**
   * Ottieni campi disponibili per tipo documento
   */
  getAvailableFields: async (tipoDocumentoId: number): Promise<{
    tipo_documento: { id: number; codice: string; descrizione: string };
    campi: Array<{ value: string; label: string; type: string }>;
  }> => {
    const { data } = await apiClient.get(
      `${BASE_URL}/templates/available-fields/${tipoDocumentoId}/`
    );
    return data;
  },

  /**
   * Ottieni trasformazioni disponibili
   */
  getAvailableTransformations: async (): Promise<{
    transformations: Array<{ value: string; label: string; category: string }>;
    count: number;
  }> => {
    const { data } = await apiClient.get(
      `${BASE_URL}/templates/available-transformations/`
    );
    return data;
  },

  /**
   * Aggiungi mapping campo
   */
  addFieldMapping: async (request: CreateFieldMappingRequest): Promise<ExtractionFieldMapping> => {
    const { data } = await apiClient.post<ExtractionFieldMapping>(
      `${BASE_URL}/templates/field-mappings/`,
      request
    );
    return data;
  },

  /**
   * Elimina mapping campo
   */
  deleteFieldMapping: async (mappingId: number): Promise<void> => {
    await apiClient.delete(`${BASE_URL}/templates/field-mappings/${mappingId}/`);
  },

  // ==================== FEEDBACK ====================

  /**
   * Lista feedback predizioni
   */
  listFeedback: async (params?: Record<string, any>): Promise<PaginatedResponse<AIPredictionFeedback>> => {
    const { data } = await apiClient.get<PaginatedResponse<AIPredictionFeedback>>(
      `${BASE_URL}/feedback/`,
      { params }
    );
    return data;
  },

  /**
   * Dettaglio feedback
   */
  getFeedback: async (id: number): Promise<AIPredictionFeedback> => {
    const { data } = await apiClient.get<AIPredictionFeedback>(
      `${BASE_URL}/feedback/${id}/`
    );
    return data;
  },

  /**
   * Statistiche feedback (per dashboard)
   */
  getFeedbackStats: async (): Promise<{
    total_feedback: number;
    predizioni_corrette: number;
    accuracy_rate: number;
    feedback_non_usati_training: number;
  }> => {
    const { data } = await apiClient.get(
      `${BASE_URL}/feedback/stats/`
    );
    return data;
  },
};
