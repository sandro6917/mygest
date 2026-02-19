/**
 * API Client per Import Sessions
 * Gestione workflow importazione documenti unificato
 */

import { apiClient } from './client';

// ============================================
// Types
// ============================================

export type TipoImportazione = 'cedolini' | 'unilav' | 'f24' | 'dichiarazioni_fiscali' | 'contratti' | 'fatture';

export type StatoSession = 'active' | 'completed' | 'expired';

export type StatoDocumento = 'pending' | 'imported' | 'skipped' | 'error';

export interface ImporterType {
  tipo: TipoImportazione;
  display_name: string;
  supported_extensions: string[];
  batch_mode: boolean;
  max_file_size_mb: number;
}

export interface AnagraficaReperita {
  id: number | null;
  codice_fiscale: string;
  nome: string;
  match_type: 'exact' | 'multiple' | 'not_found';
  ruolo: string;
  cliente_id: number | null;
  dati?: Record<string, any>;
}

export interface AttributoMappatura {
  codice: string;
  nome: string;
  valore: string;
}

export interface MappaturaDatabaseDocument {
  tipo: string;
  attributi: AttributoMappatura[];
  note_preview: string;
}

export interface DuplicateCheckInfo {
  id: number;
  codice: string;
  numero_cedolino?: string;
  data_ora_cedolino?: string;
  confidence: number;
  matched_fields: string[];
}

export interface DuplicateCheckResult {
  is_duplicate: boolean;
  duplicate_info: DuplicateCheckInfo | null;
  error?: string;
}

export interface BatchDuplicatesResponse {
  duplicates: Record<string, DuplicateCheckResult>;
}

export interface ImportSessionDocument {
  uuid: string;
  session: string;
  filename: string;
  file_path: string;
  file_url: string | null;
  file_size: number;
  parsed_data: Record<string, any>;
  anagrafiche_reperite: AnagraficaReperita[];
  valori_editabili: Record<string, any>;
  mappatura_db: MappaturaDatabaseDocument;
  stato: StatoDocumento;
  stato_display: string;
  ordine: number;
  documento_creato: number | null;
  documento_creato_detail: {
    id: number;
    codice: string;
    titolo: string;
    tipo: string | null;
  } | null;
  error_message: string;
  error_traceback: string;
  parsed_at: string | null;
  imported_at: string | null;
}

export interface ImportSessionList {
  uuid: string;
  tipo_importazione: TipoImportazione;
  tipo_importazione_display: string;
  file_originale_nome: string;
  num_documenti_totali: number;
  num_documenti_importati: number;
  num_documenti_saltati: number;
  num_documenti_errore: number;
  stato: StatoSession;
  stato_display: string;
  utente: number;
  utente_nome: string;
  created_at: string;
  updated_at: string;
  expires_at: string;
  completed_at: string | null;
  is_active: boolean;
  progress_percentage: number;
}

export interface ImportSessionDetail extends ImportSessionList {
  file_originale: string;
  temp_dir: string;
  documents: ImportSessionDocument[];
}

export interface CreateSessionRequest {
  tipo_importazione: TipoImportazione;
  file: File;
}

export interface UpdateDocumentRequest {
  valori_editabili: Record<string, any>;
}

export interface CreateDocumentRequest {
  valori_editabili?: Record<string, any>;
  cliente_id?: number;
  fascicolo_id?: number;
}

export interface CreateDocumentResponse {
  success: boolean;
  documento: {
    id: number;
    codice: string;
    titolo: string;
    tipo: string | null;
  };
  session_document: ImportSessionDocument;
}

// ============================================
// API Functions
// ============================================

export const importApi = {
  /**
   * GET /api/v1/documenti/import-sessions/types/
   * Ottiene lista tipi importazione disponibili
   */
  getTypes: async (): Promise<ImporterType[]> => {
    const { data } = await apiClient.get<ImporterType[]>('/documenti/import-sessions/types/');
    return data;
  },

  /**
   * GET /api/v1/documenti/import-sessions/
   * Lista sessioni di importazione dell'utente
   */
  listSessions: async (params?: {
    stato?: StatoSession;
    tipo_importazione?: TipoImportazione;
  }): Promise<ImportSessionList[]> => {
    const { data } = await apiClient.get<ImportSessionList[]>('/documenti/import-sessions/', { params });
    return data;
  },

  /**
   * POST /api/v1/documenti/import-sessions/
   * Crea nuova sessione di importazione (upload file + parsing)
   */
  createSession: async (request: CreateSessionRequest): Promise<ImportSessionDetail> => {
    const formData = new FormData();
    formData.append('tipo_importazione', request.tipo_importazione);
    formData.append('file', request.file);

    const { data } = await apiClient.post<ImportSessionDetail>(
      '/documenti/import-sessions/',
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
   * GET /api/v1/documenti/import-sessions/{uuid}/
   * Dettaglio sessione con lista documenti
   */
  getSession: async (uuid: string): Promise<ImportSessionDetail> => {
    const { data } = await apiClient.get<ImportSessionDetail>(`/documenti/import-sessions/${uuid}/`);
    return data;
  },

  /**
   * DELETE /api/v1/documenti/import-sessions/{uuid}/
   * Elimina sessione e cleanup file temporanei
   */
  deleteSession: async (uuid: string): Promise<void> => {
    await apiClient.delete(`/documenti/import-sessions/${uuid}/`);
  },

  /**
   * GET /api/v1/documenti/import-sessions/{uuid}/documents/
   * Lista documenti della sessione (con filtro stato opzionale)
   */
  listDocuments: async (
    sessionUuid: string,
    params?: { stato?: StatoDocumento }
  ): Promise<ImportSessionDocument[]> => {
    const { data } = await apiClient.get<ImportSessionDocument[]>(
      `/documenti/import-sessions/${sessionUuid}/documents/`,
      { params }
    );
    return data;
  },

  /**
   * GET /api/v1/documenti/import-sessions/{uuid}/documents/{doc_uuid}/
   * Dettaglio singolo documento
   */
  getDocument: async (sessionUuid: string, docUuid: string): Promise<ImportSessionDocument> => {
    const { data } = await apiClient.get<ImportSessionDocument>(
      `/documenti/import-sessions/${sessionUuid}/documents/${docUuid}/`
    );
    return data;
  },

  /**
   * PATCH /api/v1/documenti/import-sessions/{uuid}/documents/{doc_uuid}/
   * Aggiorna valori editabili del documento
   */
  updateDocument: async (
    sessionUuid: string,
    docUuid: string,
    request: UpdateDocumentRequest
  ): Promise<ImportSessionDocument> => {
    const { data } = await apiClient.patch<ImportSessionDocument>(
      `/documenti/import-sessions/${sessionUuid}/documents/${docUuid}/`,
      request
    );
    return data;
  },

  /**
   * POST /api/v1/documenti/import-sessions/{uuid}/documents/{doc_uuid}/create/
   * Crea documento nel DB dal documento parsato
   */
  createDocument: async (
    sessionUuid: string,
    docUuid: string,
    request?: CreateDocumentRequest
  ): Promise<CreateDocumentResponse> => {
    const { data } = await apiClient.post<CreateDocumentResponse>(
      `/documenti/import-sessions/${sessionUuid}/documents/${docUuid}/create/`,
      request || {}
    );
    return data;
  },

  /**
   * POST /api/v1/documenti/import-sessions/{uuid}/documents/{doc_uuid}/skip/
   * Salta importazione del documento
   */
  skipDocument: async (sessionUuid: string, docUuid: string): Promise<ImportSessionDocument> => {
    const { data} = await apiClient.post<ImportSessionDocument>(
      `/documenti/import-sessions/${sessionUuid}/documents/${docUuid}/skip/`
    );
    return data;
  },

  /**
   * GET /api/v1/documenti/import-sessions/{uuid}/check-duplicates/
   * Verifica duplicati per tutti i documenti pending della sessione
   */
  checkDuplicates: async (sessionUuid: string): Promise<BatchDuplicatesResponse> => {
    const { data } = await apiClient.get<BatchDuplicatesResponse>(
      `/documenti/import-sessions/${sessionUuid}/check-duplicates/`
    );
    return data;
  },
};
