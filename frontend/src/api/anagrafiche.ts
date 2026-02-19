/**
 * API service for Anagrafiche/Clienti
 */
import { apiClient } from './client';
import type { Cliente, AnagraficaDetail } from '@/types/anagrafiche';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ClientiFilters {
  page?: number;
  page_size?: number;
  search?: string;
  tipo?: 'PF' | 'PG';
  codice_fiscale?: string;
}

export const anagraficheApi = {
  /**
   * Lista clienti con paginazione e filtri
   */
  async listClienti(filters?: ClientiFilters): Promise<PaginatedResponse<Cliente>> {
    const params = new URLSearchParams();

    if (filters) {
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.page_size) params.append('page_size', filters.page_size.toString());
      if (filters.search) params.append('search', filters.search);
      if (filters.tipo) params.append('tipo', filters.tipo);
      if (filters.codice_fiscale) params.append('codice_fiscale', filters.codice_fiscale);
    }

    const queryString = params.toString();
    const url = queryString ? `/clienti/?${queryString}` : '/clienti/';

    const { data } = await apiClient.get<PaginatedResponse<Cliente>>(url);
    return data;
  },

  /**
   * Recupera un singolo cliente
   */
  async getCliente(id: number): Promise<Cliente> {
    const { data } = await apiClient.get<Cliente>(`/clienti/${id}/`);
    return data;
  },

  /**
   * Autocomplete anagrafiche per codice fiscale
   */
  async autocompleteAnagrafiche(query: string): Promise<AnagraficaDetail[]> {
    const params = new URLSearchParams({ search: query });
    const { data } = await apiClient.get<PaginatedResponse<AnagraficaDetail>>(
      `/anagrafiche/autocomplete/?${params.toString()}`
    );
    return data.results;
  },
};
