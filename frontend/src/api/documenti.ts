import { apiClient } from './client';
import type {
  Documento,
  DocumentoListResponse,
  DocumentoFormData,
  DocumentoJsonPayload,
  DocumentoFilters,
  DocumentiTipo,
  AttributoDefinizione,
  ProtocollazioneData,
} from '@/types/documento';

const BASE_URL = '/documenti';

export const documentiApi = {
  // Lista documenti con paginazione e filtri
  async list(filters?: DocumentoFilters, page = 1, pageSize = 20): Promise<DocumentoListResponse> {
    const params = new URLSearchParams();
    
    if (page) params.append('page', page.toString());
    if (pageSize) params.append('page_size', pageSize.toString());
    
    if (filters) {
      if (filters.search) params.append('search', filters.search);
      if (filters.tipo) params.append('tipo', filters.tipo.toString());
      if (filters.cliente) params.append('cliente', filters.cliente.toString());
      if (filters.fascicolo) params.append('fascicolo', filters.fascicolo.toString());
      if (filters.fascicolo__isnull !== undefined) params.append('fascicolo__isnull', filters.fascicolo__isnull.toString());
      if (filters.ubicazione) params.append('ubicazione', filters.ubicazione.toString());
      if (filters.stato) params.append('stato', filters.stato);
      if (filters.data_da) params.append('data_da', filters.data_da);
      if (filters.data_a) params.append('data_a', filters.data_a);
      if (filters.digitale !== undefined) params.append('digitale', filters.digitale.toString());
      if (filters.tracciabile !== undefined) params.append('tracciabile', filters.tracciabile.toString());
      if (filters.ordering) params.append('ordering', filters.ordering);
    }

    const response = await apiClient.get<DocumentoListResponse>(
      `${BASE_URL}/?${params.toString()}`
    );
    return response.data;
  },

  // Dettaglio documento
  async get(id: number): Promise<Documento> {
    const response = await apiClient.get<Documento>(`${BASE_URL}/${id}/`);
    return response.data;
  },

  // Crea nuovo documento
  async create(data: DocumentoFormData | DocumentoJsonPayload | FormData): Promise<Documento> {
    // Se data è già FormData, usalo direttamente
    if (data instanceof FormData) {
      const response = await apiClient.post<Documento>(
        `${BASE_URL}/`,
        data
      );
      return response.data;
    }

    // Se c'è un file, usa FormData
    const maybeFilePayload = data as DocumentoFormData;
    if (maybeFilePayload.file) {
      const formData = new FormData();
      
      // Campi base
      Object.entries(maybeFilePayload).forEach(([key, value]) => {
        if (value !== undefined && value !== null && key !== 'file') {
          if (typeof value === 'boolean') {
            formData.append(key, value ? 'true' : 'false');
          } else if (value instanceof File) {
            formData.append(key, value);
          } else {
            formData.append(key, value.toString());
          }
        }
      });

      // File
      formData.append('file', maybeFilePayload.file);

      const response = await apiClient.post<Documento>(
        `${BASE_URL}/`,
        formData
      );
      return response.data;
    }

    // Altrimenti usa JSON
    const response = await apiClient.post<Documento>(`${BASE_URL}/`, data);
    return response.data;
  },

  // Aggiorna documento
  async update(id: number, data: DocumentoJsonPayload | FormData): Promise<Documento> {
    // Se data è già FormData, usalo direttamente
    if (data instanceof FormData) {
      const response = await apiClient.patch<Documento>(
        `${BASE_URL}/${id}/`,
        data
      );
      return response.data;
    }
    
    // Altrimenti è un oggetto JSON, invialo come JSON
    const response = await apiClient.patch<Documento>(
      `${BASE_URL}/${id}/`,
      data,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  },

  // Elimina documento
  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${id}/`);
  },

  // Download file documento
  async downloadFile(id: number): Promise<Blob> {
    const response = await apiClient.get<Blob>(
      `${BASE_URL}/${id}/download/`,
      {
        responseType: 'blob',
      }
    );
    return response.data;
  },

  // Protocollazione documento
  async protocolla(id: number, data: ProtocollazioneData): Promise<Documento> {
    const response = await apiClient.post<Documento>(
      `${BASE_URL}/${id}/protocolla/`,
      data
    );
    return response.data;
  },

  // Lista tipi documento
  async listTipi(): Promise<DocumentiTipo[]> {
    const response = await apiClient.get<DocumentiTipo[]>(`${BASE_URL}/tipi/`);
    return response.data;
  },

  // Dettaglio tipo documento con attributi
  async getTipo(id: number): Promise<{
    tipo: DocumentiTipo;
    attributi: AttributoDefinizione[];
  }> {
    const response = await apiClient.get<{
      tipo: DocumentiTipo;
      attributi: AttributoDefinizione[];
    }>(`${BASE_URL}/tipi/${id}/`);
    return response.data;
  },

  // Cerca documenti per codice/descrizione
  async search(query: string): Promise<Documento[]> {
    const response = await apiClient.get<Documento[]>(
      `${BASE_URL}/search/?q=${encodeURIComponent(query)}`
    );
    return response.data;
  },

  // Importa cedolini paga da file ZIP (DEPRECATED - usare importaCedoliniPreview + importaCedoliniConfirm)
  async importaCedolini(
    zipFile: File, 
    duplicatePolicy: 'skip' | 'replace' | 'add' = 'skip'
  ): Promise<{
    created: number;
    replaced?: number;
    skipped?: number;
    errors: string[];
    warnings: string[];
    documenti: Array<{
      id: number;
      codice: string;
      descrizione: string;
      filename: string;
      action?: string;
    }>;
  }> {
    const formData = new FormData();
    formData.append('file', zipFile);
    formData.append('duplicate_policy', duplicatePolicy);

    const response = await apiClient.post(
      `${BASE_URL}/importa_cedolini/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Importa cedolini - Step 1: Preview (analizza ZIP/PDF)
  async importaCedoliniPreview(file: File): Promise<{
    temp_dir: string;
    totale: number;
    validi: Array<{
      filename: string;
      pdf_path: string;
      datore: {
        codice_fiscale: string;
        ragione_sociale: string | null;
        indirizzo: string | null;
        esistente: boolean;
        anagrafica_id: number | null;
      };
      lavoratore: {
        codice_fiscale: string;
        cognome: string;
        nome: string;
        matricola: string | null;
        esistente: boolean;
        anagrafica_id: number | null;
      };
      cedolino: {
        anno: number;
        mese: number;
        mensilita: number;
        periodo: string;
        livello: string | null;
        data_documento: string;
      };
      duplicato: boolean;
      documento_duplicato_id: number | null;
      attributi_db: {
        tipo: string;
        anno_riferimento: number;
        mese_riferimento: number;
        mensilita: number;
        dipendente: string;
      };
      dati_note: {
        matricola?: string | null;
        matricola_inps?: string | null;
        data_nascita?: string | null;
        data_assunzione?: string | null;
        data_cessazione?: string | null;
        livello?: string | null;
        netto?: string | null;
        numero_cedolino?: string | null;
        data_ora_cedolino?: string | null;
      };
    }>;
    duplicati: Array<any>;  // Stesso tipo di validi
    errori: Array<{
      filename: string;
      error: string;
    }>;
    statistiche: {
      nuovi_datori: number;
      nuovi_dipendenti: number;
      totale_validi: number;
      totale_duplicati: number;
      totale_errori: number;
    };
  }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post(
      `${BASE_URL}/importa_cedolini_preview/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Importa cedolini - Step 2: Confirm (importa da preview)
  async importaCedoliniConfirm(payload: {
    temp_dir: string;
    cedolini: Array<any>;
    fascicolo?: number | null;
    duplicate_policy?: 'skip' | 'replace' | 'add';
  }): Promise<{
    created: number;
    replaced: number;
    skipped: number;
    errors: Array<{
      filename: string;
      error: string;
    }>;
    documenti: Array<{
      id: number;
      codice: string;
      descrizione: string;
      filename: string;
      action: string;
    }>;
  }> {
    const response = await apiClient.post(
      `${BASE_URL}/importa_cedolini_confirm/`,
      payload
    );
    return response.data;
  },

  // Importa UNILAV - Preview
  async importaUnilavPreview(
    pdfFile: File
  ): Promise<{
    datore: {
      codice_fiscale: string;
      tipo: 'PF' | 'PG';
      // PG
      ragione_sociale?: string;
      // PF
      cognome?: string;
      nome?: string;
      // Common
      settore?: string;
      comune?: string;
      cap?: string;
      indirizzo?: string;
      telefono?: string;
      email?: string;
      // Flags
      esiste?: boolean;
      anagrafica_id?: number;
      cliente_id?: number;
      crea_se_non_esiste?: boolean;
      crea_cliente?: boolean;
    };
    lavoratore: {
      codice_fiscale: string;
      tipo: 'PF';
      cognome: string;
      nome: string;
      sesso?: string;
      data_nascita?: string;
      comune_nascita?: string;
      cittadinanza?: string;
      comune?: string;
      cap?: string;
      indirizzo?: string;
      livello_istruzione?: string;
      // Flags
      esiste?: boolean;
      anagrafica_id?: number;
      crea_se_non_esiste?: boolean;
    };
    documento: {
      codice_comunicazione: string;
      tipo_comunicazione?: string;
      data_comunicazione?: string;
      dipendente?: number;
      tipo?: string;
      data_da?: string;
      data_a?: string;
      qualifica?: string;
      contratto_collettivo?: string;
      livello?: string;
      retribuzione?: string;
      ore_settimanali?: string;
      tipo_orario?: string;
    };
    file_temp_path: string;
  }> {
    const formData = new FormData();
    formData.append('file', pdfFile);

    const response = await apiClient.post(
      `${BASE_URL}/importa_unilav_preview/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  // Importa UNILAV - Confirm
  async importaUnilavConfirm(data: {
    datore: any;
    lavoratore: any;
    documento: any;
    file_temp_path: string;
  }): Promise<{
    success: boolean;
    message: string;
    anagrafica_datore_id?: number;
    cliente_id?: number;
    anagrafica_lavoratore_id?: number;
    documento_id?: number;
  }> {
    const response = await apiClient.post(
      `${BASE_URL}/importa_unilav_confirm/`,
      data
    );
    return response.data;
  },
  
  // Importa ZIP come Libro Unico
  async importaZipLibroUnico(
    file: File,
    azioneDuplicati: 'sostituisci' | 'duplica' | 'skip' = 'duplica'
  ): Promise<{
    success: boolean;
    documento_id?: number;
    duplicato: boolean;
    duplicato_id?: number;
    azione: string;
    metadati: {
      titolo: string;
      periodo: string;
      anno: number;
      mese: number;
      cliente: string;
      num_cedolini: number;
      dipendenti: string[];
    };
    errori: string[];
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('azione_duplicati', azioneDuplicati);

    const response = await apiClient.post(
      `${BASE_URL}/importa-zip-libro-unico/`,
      formData
    );
    return response.data;
  },
};

