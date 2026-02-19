/**
 * API Client per Scadenze
 */
import apiClient from './client';
import type {
  Scadenza,
  ScadenzaListItem,
  ScadenzaFormData,
  ScadenzaFilters,
  ScadenzaOccorrenza,
  OccorrenzaFilters,
  PaginatedResponse,
} from '@/types/scadenza';

const BASE_URL = '/scadenze';

export const scadenzeApi = {
  // ========== SCADENZE ==========

  // Lista scadenze
  async list(filters?: ScadenzaFilters): Promise<PaginatedResponse<ScadenzaListItem>> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, String(value));
        }
      });
    }
    const response = await apiClient.get<PaginatedResponse<ScadenzaListItem>>(
      `${BASE_URL}/?${params.toString()}`
    );
    return response.data;
  },

  // Dettaglio scadenza
  async get(id: number): Promise<Scadenza> {
    const response = await apiClient.get<Scadenza>(`${BASE_URL}/${id}/`);
    return response.data;
  },

  // Crea scadenza
  async create(data: ScadenzaFormData): Promise<Scadenza> {
    const response = await apiClient.post<Scadenza>(`${BASE_URL}/`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  },

  // Aggiorna scadenza
  async update(id: number, data: Partial<ScadenzaFormData>): Promise<Scadenza> {
    const response = await apiClient.patch<Scadenza>(`${BASE_URL}/${id}/`, data, {
      headers: {
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  },

  // Elimina scadenza
  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${id}/`);
  },

  // Genera occorrenze
  async generaOccorrenze(
    id: number,
    params: { start?: string; end?: string; count?: number }
  ): Promise<{ occorrenze: ScadenzaOccorrenza[]; totale: number; messaggio: string } | ScadenzaOccorrenza[]> {
    const response = await apiClient.post<{ occorrenze: ScadenzaOccorrenza[]; totale: number; messaggio: string } | ScadenzaOccorrenza[]>(
      `${BASE_URL}/${id}/genera_occorrenze/`,
      params
    );
    return response.data;
  },

  // ========== OCCORRENZE ==========

  // Lista occorrenze
  async listOccorrenze(filters?: OccorrenzaFilters): Promise<PaginatedResponse<ScadenzaOccorrenza>> {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, String(value));
        }
      });
    }
    const response = await apiClient.get<PaginatedResponse<ScadenzaOccorrenza>>(
      `${BASE_URL}/occorrenze/?${params.toString()}`
    );
    return response.data;
  },

  // Dettaglio occorrenza
  async getOccorrenza(id: number): Promise<ScadenzaOccorrenza> {
    const response = await apiClient.get<ScadenzaOccorrenza>(`${BASE_URL}/occorrenze/${id}/`);
    return response.data;
  },

  // Crea occorrenza
  async createOccorrenza(data: Partial<ScadenzaOccorrenza>): Promise<ScadenzaOccorrenza> {
    const response = await apiClient.post<ScadenzaOccorrenza>(`${BASE_URL}/occorrenze/`, data);
    return response.data;
  },

  // Aggiorna occorrenza
  async updateOccorrenza(id: number, data: Partial<ScadenzaOccorrenza>): Promise<ScadenzaOccorrenza> {
    const response = await apiClient.patch<ScadenzaOccorrenza>(
      `${BASE_URL}/occorrenze/${id}/`,
      data
    );
    return response.data;
  },

  // Elimina occorrenza
  async deleteOccorrenza(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/occorrenze/${id}/`);
  },

  // Completa occorrenza
  async completaOccorrenza(id: number): Promise<ScadenzaOccorrenza> {
    const response = await apiClient.post<ScadenzaOccorrenza>(
      `${BASE_URL}/occorrenze/${id}/completa/`
    );
    return response.data;
  },

  // Annulla occorrenza
  async annullaOccorrenza(id: number): Promise<ScadenzaOccorrenza> {
    const response = await apiClient.post<ScadenzaOccorrenza>(
      `${BASE_URL}/occorrenze/${id}/annulla/`
    );
    return response.data;
  },
};
