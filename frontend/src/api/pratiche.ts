/**
 * API service for Pratiche
 */
import { apiClient } from './client';
import type {
  Pratica,
  PraticaListResponse,
  PraticaFormData,
  PraticaFilters,
  PraticheTipo,
  PraticaNota,
  PraticaNotaFormData,
} from '@/types/pratica';

const BASE_URL = '/pratiche';

// Helper per pulire i dati del form
const cleanFormData = <T extends PraticaFormData | Partial<PraticaFormData>>(data: T): T => {
  const cleaned: Record<string, unknown> = { ...data };
  
  // Converti stringhe vuote in null per i campi data
  if ('data_chiusura' in cleaned && cleaned.data_chiusura === '') {
    cleaned.data_chiusura = null;
  }
  
  // Converti stringhe vuote in null per altri campi opzionali
  if ('responsabile' in cleaned && cleaned.responsabile === '') {
    cleaned.responsabile = null;
  }
  
  return cleaned as T;
};

export const praticheApi = {
  // Lista pratiche con filtri
  async list(filters?: PraticaFilters): Promise<PraticaListResponse> {
    const params = new URLSearchParams();

    if (filters) {
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.page_size) params.append('page_size', filters.page_size.toString());
      if (filters.search) params.append('search', filters.search);
      if (filters.tipo) params.append('tipo', filters.tipo.toString());
      if (filters.cliente) params.append('cliente', filters.cliente.toString());
      if (filters.stato) params.append('stato', filters.stato);
      if (filters.responsabile) params.append('responsabile', filters.responsabile.toString());
      if (filters.periodo_riferimento) params.append('periodo_riferimento', filters.periodo_riferimento);
      if (filters.data_apertura_da) params.append('data_apertura_da', filters.data_apertura_da);
      if (filters.data_apertura_a) params.append('data_apertura_a', filters.data_apertura_a);
      if (filters.ordering) params.append('ordering', filters.ordering);
    }

    const response = await apiClient.get<PraticaListResponse>(
      `${BASE_URL}/?${params.toString()}`
    );
    return response.data;
  },

  // Dettaglio pratica
  async get(id: number): Promise<Pratica> {
    const response = await apiClient.get<Pratica>(`${BASE_URL}/${id}/`);
    return response.data;
  },

  // Crea nuova pratica
  async create(data: PraticaFormData): Promise<Pratica> {
    const cleanedData = cleanFormData(data);
    const response = await apiClient.post<Pratica>(`${BASE_URL}/`, cleanedData, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  },

  // Aggiorna pratica
  async update(id: number, data: Partial<PraticaFormData>): Promise<Pratica> {
    const cleanedData = cleanFormData(data);
    const response = await apiClient.patch<Pratica>(`${BASE_URL}/${id}/`, cleanedData, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  },

  // Elimina pratica
  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${id}/`);
  },

  // Ricerca pratiche
  async search(query: string): Promise<Pratica[]> {
    const response = await apiClient.get<Pratica[]>(`${BASE_URL}/search/?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // Lista tipi pratica
  async listTipi(): Promise<PraticheTipo[]> {
    const response = await apiClient.get<PraticheTipo[]>(`${BASE_URL}/tipi/`);
    return response.data;
  },

  // Dettaglio tipo pratica
  async getTipo(id: number): Promise<PraticheTipo> {
    const response = await apiClient.get<PraticheTipo>(`${BASE_URL}/tipi/${id}/`);
    return response.data;
  },

  // ========== NOTE ==========
  
  // Lista note di una pratica
  async listNote(praticaId: number): Promise<PraticaNota[]> {
    const response = await apiClient.get<PraticaNota[] | { results: PraticaNota[] }>(
      `${BASE_URL}/note/?pratica=${praticaId}`
    );
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data.results;
  },

  // Dettaglio nota
  async getNota(id: number): Promise<PraticaNota> {
    const response = await apiClient.get<PraticaNota>(`${BASE_URL}/note/${id}/`);
    return response.data;
  },

  // Crea nuova nota
  async createNota(data: PraticaNotaFormData): Promise<PraticaNota> {
    const response = await apiClient.post<PraticaNota>(`${BASE_URL}/note/`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  },

  // Aggiorna nota
  async updateNota(id: number, data: Partial<PraticaNotaFormData>): Promise<PraticaNota> {
    const response = await apiClient.patch<PraticaNota>(`${BASE_URL}/note/${id}/`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  },

  // Elimina nota
  async deleteNota(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/note/${id}/`);
  },
};
