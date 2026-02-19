/**
 * API Client per il modulo Comunicazioni
 */

import { apiClient } from './client';
import type {
  Comunicazione,
  ComunicazioneFormData,
  ComunicazioneFilters,
  EmailContatto,
  MailingList,
  EmailImport,
  TemplateContextField,
  TemplateComunicazione,
  FirmaComunicazione,
  CodiceTributoF24,
  AllegatoComunicazione,
  AllegatoComunicazioneFormData,
} from '@/types/comunicazioni';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Base API endpoints
const COMUNICAZIONI_URL = '/comunicazioni/comunicazioni/';
const CONTATTI_URL = '/comunicazioni/contatti/';
const LISTE_URL = '/comunicazioni/liste/';
const EMAIL_IMPORT_URL = '/comunicazioni/email-import/';
const TEMPLATE_FIELDS_URL = '/comunicazioni/template-fields/';
const TEMPLATES_URL = '/comunicazioni/templates/';
const FIRME_URL = '/comunicazioni/firme/';

/**
 * Comunicazioni CRUD
 */
export const comunicazioniApi = {
  // List con filtri e paginazione
  list: async (filters?: ComunicazioneFilters): Promise<PaginatedResponse<Comunicazione>> => {
    console.log('🔍 Chiamata API comunicazioni.list con filtri:', filters);
    console.log('📡 URL:', COMUNICAZIONI_URL);
    try {
      const response = await apiClient.get<PaginatedResponse<Comunicazione>>(COMUNICAZIONI_URL, {
        params: filters,
      });
      console.log('✅ Risposta API comunicazioni:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Errore API comunicazioni:', error);
      throw error;
    }
  },

  // Get singola comunicazione
  get: async (id: number): Promise<Comunicazione> => {
    const response = await apiClient.get<Comunicazione>(`${COMUNICAZIONI_URL}${id}/`);
    return response.data;
  },

  // Create nuova comunicazione
  create: async (data: ComunicazioneFormData): Promise<Comunicazione> => {
    const response = await apiClient.post<Comunicazione>(COMUNICAZIONI_URL, data);
    return response.data;
  },

  // Update comunicazione esistente
  update: async (id: number, data: Partial<ComunicazioneFormData>): Promise<Comunicazione> => {
    const response = await apiClient.patch<Comunicazione>(`${COMUNICAZIONI_URL}${id}/`, data);
    return response.data;
  },

  // Delete comunicazione
  delete: async (id: number): Promise<void> => {
    await apiClient.delete(`${COMUNICAZIONI_URL}${id}/`);
  },

  // Invio comunicazione
  send: async (id: number): Promise<Comunicazione> => {
    const response = await apiClient.post<Comunicazione>(`${COMUNICAZIONI_URL}${id}/send/`);
    return response.data;
  },

  // Rigenera contenuto dal template
  rigenera: async (id: number): Promise<{ message: string; data: Comunicazione }> => {
    const response = await apiClient.post<{ message: string; data: Comunicazione }>(
      `${COMUNICAZIONI_URL}${id}/rigenera/`
    );
    return response.data;
  },

  // Protocollazione comunicazione
  protocolla: async (id: number, protocolloData: any): Promise<Comunicazione> => {
    const response = await apiClient.post<Comunicazione>(
      `${COMUNICAZIONI_URL}${id}/protocolla/`,
      protocolloData
    );
    return response.data;
  },

  // Get allegati di una comunicazione
  getAllegati: async (id: number): Promise<AllegatoComunicazione[]> => {
    const response = await apiClient.get<AllegatoComunicazione[]>(
      `${COMUNICAZIONI_URL}${id}/allegati/`
    );
    return response.data;
  },

  // Aggiungi allegato
  addAllegato: async (comunicazioneId: number, documentoId: number): Promise<AllegatoComunicazione> => {
    const response = await apiClient.post<AllegatoComunicazione>(
      `${COMUNICAZIONI_URL}${comunicazioneId}/allegati/`,
      { documento: documentoId }
    );
    return response.data;
  },

  // Rimuovi allegato
  removeAllegato: async (comunicazioneId: number, allegatoId: number): Promise<void> => {
    await apiClient.delete(`${COMUNICAZIONI_URL}${comunicazioneId}/allegati/${allegatoId}/`);
  },

  // Render preview del template
  previewTemplate: async (
    templateId: number,
    context: Record<string, any>
  ): Promise<{ oggetto: string; corpo: string; corpo_html: string }> => {
    const response = await apiClient.post(`${COMUNICAZIONI_URL}preview-template/`, {
      template: templateId,
      context,
    });
    return response.data;
  },
};

/**
 * Email Contatti
 */
export const emailContattiApi = {
  // List con ricerca
  list: async (params?: { search?: string; page?: number }): Promise<PaginatedResponse<EmailContatto>> => {
    const response = await apiClient.get<PaginatedResponse<EmailContatto>>(CONTATTI_URL, {
      params,
    });
    return response.data;
  },

  // Get singolo contatto
  get: async (id: number): Promise<EmailContatto> => {
    const response = await apiClient.get<EmailContatto>(`${CONTATTI_URL}${id}/`);
    return response.data;
  },

  // Autocomplete
  search: async (query: string): Promise<EmailContatto[]> => {
    console.log('🔍 emailContattiApi.search chiamata con query:', query);
    const response = await apiClient.get<PaginatedResponse<EmailContatto>>(CONTATTI_URL, {
      params: { search: query, page_size: 20 },
    });
    console.log('✅ emailContattiApi.search risposta:', response.data);
    console.log('📊 Numero risultati:', response.data.results.length);
    return response.data.results;
  },
};

/**
 * Mailing Lists
 */
export const mailingListApi = {
  // List
  list: async (params?: { search?: string; page?: number }): Promise<PaginatedResponse<MailingList>> => {
    const response = await apiClient.get<PaginatedResponse<MailingList>>(LISTE_URL, {
      params,
    });
    return response.data;
  },

  // Get singola lista
  get: async (id: number): Promise<MailingList> => {
    const response = await apiClient.get<MailingList>(`${LISTE_URL}${id}/`);
    return response.data;
  },

  // Autocomplete
  search: async (query: string): Promise<MailingList[]> => {
    const response = await apiClient.get<PaginatedResponse<MailingList>>(LISTE_URL, {
      params: { search: query, page_size: 20 },
    });
    return response.data.results;
  },
};

/**
 * Email Import
 */
export const emailImportApi = {
  // List
  list: async (params?: { search?: string; page?: number }): Promise<PaginatedResponse<EmailImport>> => {
    const response = await apiClient.get<PaginatedResponse<EmailImport>>(EMAIL_IMPORT_URL, {
      params,
    });
    return response.data;
  },

  // Get
  get: async (id: number): Promise<EmailImport> => {
    const response = await apiClient.get<EmailImport>(`${EMAIL_IMPORT_URL}${id}/`);
    return response.data;
  },
};

/**
 * Template Context Fields
 */
export const templateFieldsApi = {
  // List campi di un template
  list: async (templateId?: number): Promise<TemplateContextField[]> => {
    const response = await apiClient.get<TemplateContextField[]>(TEMPLATE_FIELDS_URL, {
      params: templateId ? { template: templateId } : undefined,
    });
    return response.data;
  },
};

/**
 * Template Comunicazioni
 */
export const templatesApi = {
  // List templates
  list: async (params?: { search?: string }): Promise<PaginatedResponse<TemplateComunicazione>> => {
    const response = await apiClient.get<PaginatedResponse<TemplateComunicazione>>(TEMPLATES_URL, {
      params,
    });
    return response.data;
  },

  // Get singolo template
  get: async (id: number): Promise<TemplateComunicazione> => {
    const response = await apiClient.get<TemplateComunicazione>(`${TEMPLATES_URL}${id}/`);
    return response.data;
  },
};

/**
 * Firme Comunicazioni
 */
export const firmeApi = {
  // List firme
  list: async (params?: { search?: string }): Promise<PaginatedResponse<FirmaComunicazione>> => {
    const response = await apiClient.get<PaginatedResponse<FirmaComunicazione>>(FIRME_URL, {
      params,
    });
    return response.data;
  },

  // Get singola firma
  get: async (id: number): Promise<FirmaComunicazione> => {
    const response = await apiClient.get<FirmaComunicazione>(`${FIRME_URL}${id}/`);
    return response.data;
  },
};

/**
 * Codici Tributo F24
 */
const CODICI_TRIBUTO_URL = '/comunicazioni/codici-tributo/';

export const codiciTributoApi = {
  // List codici tributo con ricerca
  list: async (params?: { 
    search?: string;
    sezione?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<CodiceTributoF24>> => {
    const response = await apiClient.get<PaginatedResponse<CodiceTributoF24>>(CODICI_TRIBUTO_URL, {
      params,
    });
    return response.data;
  },

  // Get singolo codice tributo
  get: async (id: number): Promise<CodiceTributoF24> => {
    const response = await apiClient.get<CodiceTributoF24>(`${CODICI_TRIBUTO_URL}${id}/`);
    return response.data;
  },

  // Search per autocomplete
  search: async (query: string, sezione?: string): Promise<CodiceTributoF24[]> => {
    const params: any = { search: query, page_size: 20 };
    if (sezione) {
      params.sezione = sezione;
    }
    const response = await apiClient.get<PaginatedResponse<CodiceTributoF24>>(CODICI_TRIBUTO_URL, {
      params,
    });
    return response.data.results;
  },
};

/**
 * Allegati Comunicazione
 */
export const allegatiComunicazioneApi = {
  // List allegati di una comunicazione
  list: async (comunicazioneId: number): Promise<AllegatoComunicazione[]> => {
    const response = await apiClient.get<{ results: AllegatoComunicazione[] }>(
      `/comunicazioni/comunicazioni/${comunicazioneId}/allegati/`
    );
    return response.data.results;
  },

  // Get singolo allegato
  get: async (comunicazioneId: number, id: number): Promise<AllegatoComunicazione> => {
    const response = await apiClient.get<AllegatoComunicazione>(
      `/comunicazioni/comunicazioni/${comunicazioneId}/allegati/${id}/`
    );
    return response.data;
  },

  // Create allegato (documento o fascicolo)
  create: async (comunicazioneId: number, data: Partial<AllegatoComunicazioneFormData>): Promise<AllegatoComunicazione> => {
    const response = await apiClient.post<AllegatoComunicazione>(
      `/comunicazioni/comunicazioni/${comunicazioneId}/allegati/`,
      data
    );
    return response.data;
  },

  // Upload file come allegato
  uploadFile: async (comunicazioneId: number, file: File, note?: string): Promise<AllegatoComunicazione> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('nome_file', file.name);
    if (note) {
      formData.append('note', note);
    }
    
    const response = await apiClient.post<AllegatoComunicazione>(
      `/comunicazioni/comunicazioni/${comunicazioneId}/allegati/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Update allegato
  update: async (comunicazioneId: number, id: number, data: Partial<AllegatoComunicazioneFormData>): Promise<AllegatoComunicazione> => {
    const response = await apiClient.patch<AllegatoComunicazione>(
      `/comunicazioni/comunicazioni/${comunicazioneId}/allegati/${id}/`,
      data
    );
    return response.data;
  },

  // Delete allegato
  delete: async (comunicazioneId: number, id: number): Promise<void> => {
    await apiClient.delete(`/comunicazioni/comunicazioni/${comunicazioneId}/allegati/${id}/`);
  },
};

