/**
 * API Service per AI Classifier
 */
import { apiClient } from './client';
import type {
  ClassificationJob,
  ClassificationResult,
  ClassifierConfig,
  CreateJobRequest,
  ImportDocumentsRequest,
  ImportDocumentsResponse,
  PaginatedResponse,
  JobStats,
  PredictResponse,
} from '@/types/aiClassifier';

const BASE_URL = '/ai-classifier';

export const aiClassifierApi = {
  // ==================== JOBS ====================
  
  /**
   * Lista tutti i job di classificazione
   */
  listJobs: async (params?: Record<string, any>) => {
    const { data } = await apiClient.get<PaginatedResponse<ClassificationJob>>(
      `${BASE_URL}/jobs/`,
      { params }
    );
    return data;
  },

  /**
   * Recupera un job specifico
   */
  getJob: async (id: number) => {
    const { data } = await apiClient.get<ClassificationJob>(
      `${BASE_URL}/jobs/${id}/`
    );
    return data;
  },

  /**
   * Crea un nuovo job
   */
  createJob: async (jobData: CreateJobRequest) => {
    const { data } = await apiClient.post<ClassificationJob>(
      `${BASE_URL}/jobs/`,
      jobData
    );
    return data;
  },

  /**
   * Avvia un job
   */
  startJob: async (id: number) => {
    const { data } = await apiClient.post<ClassificationJob>(
      `${BASE_URL}/jobs/${id}/start/`
    );
    return data;
  },

  /**
   * Cancella un job
   */
  deleteJob: async (id: number) => {
    await apiClient.delete(`${BASE_URL}/jobs/${id}/`);
  },

  /**
   * Ottieni statistiche job
   */
  getJobStats: async () => {
    const { data } = await apiClient.get<JobStats>(
      `${BASE_URL}/jobs/stats/`
    );
    return data;
  },

  // ==================== RESULTS ====================

  /**
   * Lista risultati di classificazione
   */
  listResults: async (params?: Record<string, any>) => {
    const { data } = await apiClient.get<PaginatedResponse<ClassificationResult>>(
      `${BASE_URL}/results/`,
      { params }
    );
    return data;
  },

  /**
   * Recupera un risultato specifico
   */
  getResult: async (id: number) => {
    const { data } = await apiClient.get<ClassificationResult>(
      `${BASE_URL}/results/${id}/`
    );
    return data;
  },

  /**
   * Aggiorna un risultato (es. note, suggested_cliente)
   */
  updateResult: async (id: number, updates: Partial<ClassificationResult>) => {
    const { data } = await apiClient.patch<ClassificationResult>(
      `${BASE_URL}/results/${id}/`,
      updates
    );
    return data;
  },

  /**
   * Elimina un risultato
   */
  deleteResult: async (id: number) => {
    await apiClient.delete(`${BASE_URL}/results/${id}/`);
  },

  // ==================== CONFIG ====================

  /**
   * Recupera configurazione
   */
  getConfig: async () => {
    const { data } = await apiClient.get<ClassifierConfig>(
      `${BASE_URL}/config/`
    );
    return data;
  },

  /**
   * Aggiorna configurazione
   */
  updateConfig: async (updates: Partial<ClassifierConfig>) => {
    const { data } = await apiClient.patch<ClassifierConfig>(
      `${BASE_URL}/config/`,
      updates
    );
    return data;
  },

  // ==================== IMPORT ====================

  /**
   * Importa documenti classificati
   */
  importDocuments: async (request: ImportDocumentsRequest) => {
    const { data } = await apiClient.post<ImportDocumentsResponse>(
      `${BASE_URL}/import/documents/`,
      request
    );
    return data;
  },

  // ==================== ML PREDICTIONS ====================

  /**
   * Predice il tipo di documento da un file usando ML
   */
  predictDocumentType: async (
    file: File,
    returnTopN: number = 5,
    savePrediction: boolean = false
  ): Promise<PredictResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('return_top_n', returnTopN.toString());
    formData.append('save_prediction', savePrediction.toString());

    const { data } = await apiClient.post<PredictResponse>(
      `${BASE_URL}/predict/`,
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
   * Ottiene il modello ML attualmente attivo
   */
  getActiveModel: async () => {
    const { data } = await apiClient.get<{
      id: number;
      version: string;
      model_type: string;
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
      training_samples: number;
      is_active: boolean;
      trained_at: string;
      trained_at_formatted: string;
    }>(`${BASE_URL}/models/active/`);
    return data;
  },

  /**
   * Invia feedback su una predizione
   */
  sendPredictionFeedback: async (
    predictionId: number,
    isCorrect: boolean,
    correctValue?: string,
    comments?: string
  ) => {
    const { data } = await apiClient.post(
      `${BASE_URL}/predictions/${predictionId}/feedback/`,
      {
        is_correct: isCorrect,
        correct_value: correctValue,
        comments: comments,
      }
    );
    return data;
  },
};
