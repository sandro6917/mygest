/**
 * API service for Fascicoli
 */
import axios from 'axios';
import { apiClient } from './client';
import type {
  Fascicolo,
  FascicoloListItem,
  FascicoloListResponse,
  FascicoloFormData,
  FascicoloFilters,
  FascicoliStats,
  MovimentoFormData,
  TitolarioVoce,
  UnitaFisica,
} from '@/types/fascicolo';
import type { MovimentoProtocollo } from '@/types/protocollo';

const BASE_URL = '/fascicoli';

// Helper per pulire i dati del form
const cleanFormData = <T extends FascicoloFormData | Partial<FascicoloFormData>>(data: T): T => {
  const cleaned: Record<string, unknown> = { ...data };
  
  // Converti stringhe vuote in null per i campi opzionali
  if ('cliente' in cleaned && cleaned.cliente === '') {
    cleaned.cliente = null;
  }
  
  if ('parent' in cleaned && cleaned.parent === '') {
    cleaned.parent = null;
  }
  
  if ('ubicazione' in cleaned && cleaned.ubicazione === '') {
    cleaned.ubicazione = null;
  }
  
  return cleaned as T;
};

export const fascicoliApi = {
  // Lista fascicoli con filtri
  async list(filters?: FascicoloFilters): Promise<FascicoloListResponse> {
    const params = new URLSearchParams();

    if (filters) {
      if (filters.page) params.append('page', filters.page.toString());
      if (filters.page_size) params.append('page_size', filters.page_size.toString());
      if (filters.search) params.append('search', filters.search);
      if (filters.cliente) params.append('cliente', filters.cliente.toString());
      if (filters.titolario_voce) params.append('titolario_voce', filters.titolario_voce.toString());
      if (filters.anno) params.append('anno', filters.anno.toString());
      if (filters.stato) params.append('stato', filters.stato);
      if (filters.ubicazione) params.append('ubicazione', filters.ubicazione.toString());
      if (filters.parent !== undefined) {
        params.append('parent', filters.parent === 'null' ? 'null' : filters.parent.toString());
      }
      if (filters.ordering) params.append('ordering', filters.ordering);
    }

    const queryString = params.toString();
    const url = queryString ? `${BASE_URL}/fascicoli/?${queryString}` : `${BASE_URL}/fascicoli/`;
    
    const response = await apiClient.get<FascicoloListResponse>(url);
    return response.data;
  },

  // Dettaglio fascicolo
  async get(id: number): Promise<Fascicolo> {
    const response = await apiClient.get<Fascicolo>(`${BASE_URL}/fascicoli/${id}/`);
    return response.data;
  },

  // Crea nuovo fascicolo
  async create(data: FascicoloFormData): Promise<Fascicolo> {
    const cleanedData = cleanFormData(data);
    const response = await apiClient.post<Fascicolo>(`${BASE_URL}/fascicoli/`, cleanedData);
    return response.data;
  },

  // Aggiorna fascicolo
  async update(id: number, data: Partial<FascicoloFormData>): Promise<Fascicolo> {
    const cleanedData = cleanFormData(data);
    const response = await apiClient.patch<Fascicolo>(`${BASE_URL}/fascicoli/${id}/`, cleanedData);
    return response.data;
  },

  // Elimina fascicolo
  async delete(id: number): Promise<void> {
    await apiClient.delete(`${BASE_URL}/fascicoli/${id}/`);
  },

  // Lista sottofascicoli di un fascicolo
  async listSottofascicoli(parentId: number): Promise<FascicoloListItem[]> {
    const response = await apiClient.get<FascicoloListItem[]>(`${BASE_URL}/fascicoli/${parentId}/sottofascicoli/`);
    return response.data;
  },

  // Movimenti protocollo
  async listMovimenti(fascicoloId: number): Promise<MovimentoProtocollo[]> {
    const response = await apiClient.get<MovimentoProtocollo[]>(`${BASE_URL}/fascicoli/${fascicoloId}/movimenti/`);
    return response.data;
  },

  // Registra entrata
  async registraEntrata(fascicoloId: number, data: MovimentoFormData): Promise<MovimentoProtocollo> {
    const response = await apiClient.post<MovimentoProtocollo>(
      `${BASE_URL}/fascicoli/${fascicoloId}/registra_entrata/`,
      data
    );
    return response.data;
  },

  // Registra uscita
  async registraUscita(fascicoloId: number, data: MovimentoFormData): Promise<MovimentoProtocollo> {
    const response = await apiClient.post<MovimentoProtocollo>(
      `${BASE_URL}/fascicoli/${fascicoloId}/registra_uscita/`,
      data
    );
    return response.data;
  },

  // Ottieni lista voci titolario (per select/autocomplete)
  async listTitolarioVoci(search?: string): Promise<TitolarioVoce[]> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    
    const queryString = params.toString();
    const url = queryString 
      ? `${BASE_URL}/titolario-voci/?${queryString}` 
      : `${BASE_URL}/titolario-voci/`;
    
    const response = await apiClient.get<TitolarioVoce[]>(url);
    // L'API ora restituisce direttamente un array (paginazione disabilitata)
    return Array.isArray(response.data) ? response.data : [];
  },

  // Ottieni lista unità fisiche (per select)
  async listUnitaFisiche(search?: string): Promise<UnitaFisica[]> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    
    const queryString = params.toString();
    const url = queryString 
      ? `${BASE_URL}/archivio-fisico/unita/?${queryString}` 
      : `${BASE_URL}/archivio-fisico/unita/`;
    
    const response = await apiClient.get<{ results?: UnitaFisica[] } | UnitaFisica[]>(url);
    if (Array.isArray(response.data)) {
      return response.data;
    }
    return response.data.results || [];
  },

  // Statistiche fascicoli
  async getStats(): Promise<FascicoliStats> {
    const response = await apiClient.get<FascicoliStats>(`${BASE_URL}/fascicoli/stats/`);
    return response.data;
  },

  // Collega fascicolo esistente come sottofascicolo
  async collegaSottofascicolo(parentId: number, targetId: number): Promise<void> {
    const formData = new FormData();
    formData.append('target_id', targetId.toString());
    
    await apiClient.post(`/fascicoli/${parentId}/collega/`, formData);
  },

  // Ottieni fascicoli collegabili come sottofascicoli (stesso cliente, titolario, anno)
  async getSottofascicoliCollegabili(fascicoloId: number): Promise<FascicoloListItem[]> {
    const response = await apiClient.get<FascicoloListItem[]>(
      `${BASE_URL}/fascicoli/${fascicoloId}/sottofascicoli_collegabili/`
    );
    return response.data;
  },

  // Ottieni fascicoli collegabili (M2M - esclusi self, sottofascicoli, già collegati)
  async getFascicoliCollegabili(fascicoloId: number, filters?: {
    search?: string;
    anno?: number;
    cliente?: number;
    titolario?: number;
  }): Promise<FascicoloListItem[]> {
    const params = new URLSearchParams();
    if (filters?.search) params.append('search', filters.search);
    if (filters?.anno) params.append('anno', filters.anno.toString());
    if (filters?.cliente) params.append('cliente', filters.cliente.toString());
    if (filters?.titolario) params.append('titolario', filters.titolario.toString());
    
    const queryString = params.toString();
    const url = queryString 
      ? `${BASE_URL}/fascicoli/${fascicoloId}/fascicoli_collegabili/?${queryString}`
      : `${BASE_URL}/fascicoli/${fascicoloId}/fascicoli_collegabili/`;
    
    const response = await apiClient.get<FascicoloListItem[]>(url);
    return response.data;
  },

  // Collega un fascicolo (relazione M2M)
  async collegaFascicolo(fascicoloId: number, fascicoloDaCollegareId: number): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      `${BASE_URL}/fascicoli/${fascicoloId}/collega_fascicolo/`,
      { fascicolo_id: fascicoloDaCollegareId }
    );
    return response.data;
  },

  // Scollega un fascicolo (relazione M2M)
  async scollegaFascicolo(fascicoloId: number, fascicoloDaScollegareId: number): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      `${BASE_URL}/fascicoli/${fascicoloId}/scollega_fascicolo/`,
      { fascicolo_id: fascicoloDaScollegareId }
    );
    return response.data;
  },

  // Stampa etichetta fascicolo
  async stampaEtichetta(id: number, moduloSlug: string = 'ET_FASCICOLO'): Promise<Blob> {
    // Usa axios.create per creare un client con gli interceptor di apiClient
    // ma con baseURL vuoto (per usare URL assoluti come /etichette/)
    const token = localStorage.getItem('access_token');
    if (!token) {
      throw new Error('Token di autenticazione non trovato. Effettua nuovamente il login.');
    }
    
    try {
      const response = await axios.get(`/etichette/fascicoli/fascicolo/${id}/`, {
        params: { modulo: moduloSlug },
        responseType: 'blob',
        headers: { Authorization: `Bearer ${token}` },
      });
      return response.data;
    } catch (error) {
      // Se riceve 401, il token è scaduto
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        // Tenta il refresh del token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          try {
            const refreshResponse = await axios.post('/api/v1/auth/refresh/', {
              refresh: refreshToken,
            });
            const { access } = refreshResponse.data;
            localStorage.setItem('access_token', access);
            
            // Riprova la richiesta con il nuovo token
            const retryResponse = await axios.get(`/etichette/fascicoli/fascicolo/${id}/`, {
              params: { modulo: moduloSlug },
              responseType: 'blob',
              headers: { Authorization: `Bearer ${access}` },
            });
            return retryResponse.data;
          } catch (refreshError) {
            // Refresh fallito, logout
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            throw new Error('Sessione scaduta. Effettua nuovamente il login.');
          }
        }
      }
      throw error;
    }
  },
};

/**
 * Utility per aprire l'anteprima del PDF dell'etichetta fascicolo in una nuova scheda
 */
export const previewEtichettaFascicoloPDF = async (id: number) => {
  const blob = await fascicoliApi.stampaEtichetta(id);
  const url = window.URL.createObjectURL(blob);
  
  // Apri in una nuova scheda
  const newWindow = window.open(url, '_blank');
  
  // Pulisci l'URL dopo un breve ritardo per permettere l'apertura
  setTimeout(() => {
    window.URL.revokeObjectURL(url);
  }, 100);
  
  return newWindow;
};

/**
 * Utility per aprire l'anteprima del PDF della copertina fascicolo in una nuova scheda
 */
export const previewCopertinaFascicoloPDF = async (id: number) => {
  const blob = await fascicoliApi.stampaEtichetta(id, 'CopFas');
  const url = window.URL.createObjectURL(blob);
  
  // Apri in una nuova scheda
  const newWindow = window.open(url, '_blank');
  
  // Pulisci l'URL dopo un breve ritardo per permettere l'apertura
  setTimeout(() => {
    window.URL.revokeObjectURL(url);
  }, 100);
  
  return newWindow;
};
