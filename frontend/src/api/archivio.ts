/**
 * API service for Archivio Fisico (Unità Fisiche)
 */
import { apiClient } from './client';

export interface UnitaFisica {
  id: number;
  codice: string;
  nome: string;
  tipo: string;
  tipo_display: string;
  attivo: boolean;
  archivio_fisso: boolean;
  full_path: string;
  parent: number | null;
  ordine: number;
  created_at: string;
  updated_at: string;
}

export interface UnitaFisicaTreeNode {
  id: number;
  codice: string;
  nome: string;
  tipo: string;
  tipo_display: string;
  attivo: boolean;
  archivio_fisso: boolean;
  full_path: string;
  children: UnitaFisicaTreeNode[];
}

const BASE_URL = '/archivio-fisico/unita';

export const archivioApi = {
  /**
   * Ottieni tutte le unità fisiche (senza paginazione)
   */
  async list(): Promise<UnitaFisica[]> {
    const { data } = await apiClient.get<UnitaFisica[]>(`${BASE_URL}/`);
    return data;
  },

  /**
   * Ottieni una singola unità fisica
   */
  async get(id: number): Promise<UnitaFisica> {
    const { data } = await apiClient.get<UnitaFisica>(`${BASE_URL}/${id}/`);
    return data;
  },

  /**
   * Ottieni la struttura ad albero delle unità fisiche
   */
  async getTree(): Promise<UnitaFisicaTreeNode[]> {
    const { data } = await apiClient.get<UnitaFisicaTreeNode[]>(`${BASE_URL}/tree/`);
    return data;
  },

  /**
   * Ottieni i figli diretti di un'unità fisica
   */
  async getChildren(id: number): Promise<UnitaFisica[]> {
    const { data } = await apiClient.get<UnitaFisica[]>(`${BASE_URL}/${id}/children/`);
    return data;
  },

  /**
   * Ottieni gli antenati di un'unità fisica
   */
  async getAncestors(id: number): Promise<UnitaFisica[]> {
    const { data } = await apiClient.get<UnitaFisica[]>(`${BASE_URL}/${id}/ancestors/`);
    return data;
  },

  /**
   * Ottieni solo le unità radice (senza parent)
   */
  async getRoots(): Promise<UnitaFisica[]> {
    const { data } = await apiClient.get<UnitaFisica[]>(`${BASE_URL}/radici/`);
    return data;
  },

  /**
   * Stampa l'etichetta dell'unità fisica
   * Configurazione completa dal database (StampaModulo/StampaCampo)
   * @param id - ID dell'unità fisica
   */
  async stampaEtichetta(id: number): Promise<Blob> {
    const response = await apiClient.get(`${BASE_URL}/${id}/stampa_etichetta/`, {
      responseType: 'blob',
    });
    
    return response.data;
  },

  /**
   * Stampa la lista degli oggetti contenuti nell'unità fisica
   * Utilizza StampaLista configurato come "archivio_fisico.archiviofisicolistastampa"
   * @param id - ID dell'unità fisica
   * @param listaSlug - Slug della lista di stampa (default: "archiviofisicolistastampa")
   */
  async stampaListaContenuti(id: number, listaSlug?: string): Promise<Blob> {
    const params = new URLSearchParams();
    if (listaSlug) {
      params.append('lista', listaSlug);
    }
    
    const response = await apiClient.get(`${BASE_URL}/${id}/stampa_lista_contenuti/`, {
      responseType: 'blob',
      params,
    });
    
    return response.data;
  },

  /**
   * Stampa la copertina A4 dell'unità fisica
   * @param id - ID dell'unità fisica
   */
  async stampaCopertina(id: number): Promise<Blob> {
    const response = await apiClient.get(`${BASE_URL}/${id}/stampa_copertina/`, {
      responseType: 'blob',
    });
    
    return response.data;
  },

  /**
   * Stampa la copertina A3 orizzontale dell'unità fisica
   * @param id - ID dell'unità fisica
   */
  async stampaCopertinaA3(id: number): Promise<Blob> {
    const response = await apiClient.get(`${BASE_URL}/${id}/stampa_copertina_a3/`, {
      responseType: 'blob',
    });
    
    return response.data;
  },

  /**
   * Stampa l'elenco combinato di fascicoli e documenti dell'unità fisica
   * @param id - ID dell'unità fisica
   */
  async stampaFascicoliDocumenti(id: number): Promise<Blob> {
    const response = await apiClient.get(`${BASE_URL}/${id}/stampa_fascicoli_documenti/`, {
      responseType: 'blob',
    });
    
    return response.data;
  },
};

/**
 * Utility per aprire l'anteprima del PDF dell'etichetta in una nuova scheda
 */
export const previewEtichettaPDF = async (id: number) => {
  const blob = await archivioApi.stampaEtichetta(id);
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
 * Utility per scaricare il PDF dell'etichetta
 */
export const downloadEtichettaPDF = async (id: number, nomeFile?: string) => {
  const blob = await archivioApi.stampaEtichetta(id);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nomeFile || `etichetta_unita_${id}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Utility per aprire l'anteprima del PDF della copertina in una nuova scheda
 */
export const previewCopertinaPDF = async (id: number) => {
  const blob = await archivioApi.stampaCopertina(id);
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
 * Utility per scaricare il PDF della copertina
 */
export const downloadCopertinaPDF = async (id: number, nomeFile?: string) => {
  const blob = await archivioApi.stampaCopertina(id);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nomeFile || `copertina_unita_${id}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Utility per aprire l'anteprima del PDF della copertina A3 in una nuova scheda
 */
export const previewCopertinaA3PDF = async (id: number) => {
  const blob = await archivioApi.stampaCopertinaA3(id);
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
 * Utility per scaricare il PDF della copertina A3
 */
export const downloadCopertinaA3PDF = async (id: number, nomeFile?: string) => {
  const blob = await archivioApi.stampaCopertinaA3(id);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nomeFile || `copertina_a3_unita_${id}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Utility per aprire l'anteprima del PDF della lista contenuti in una nuova scheda
 */
export const previewListaContenutiPDF = async (id: number, listaSlug?: string) => {
  const blob = await archivioApi.stampaListaContenuti(id, listaSlug);
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
 * Utility per scaricare il PDF della lista contenuti
 */
export const downloadListaContenutiPDF = async (id: number, nomeFile?: string, listaSlug?: string) => {
  const blob = await archivioApi.stampaListaContenuti(id, listaSlug);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nomeFile || `lista_contenuti_unita_${id}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Utility per aprire l'anteprima del PDF combinato fascicoli+documenti
 */
export const previewFascicoliDocumentiPDF = async (id: number) => {
  try {
    const blob = await archivioApi.stampaFascicoliDocumenti(id);
    
    // Verifica se è un JSON (risposta vuota) invece di un PDF
    if (blob.type === 'application/json') {
      const text = await blob.text();
      const json = JSON.parse(text);
      alert(json.message || 'Nessun fascicolo o documento trovato');
      return null;
    }
    
    const url = window.URL.createObjectURL(blob);
    
    // Apri in una nuova scheda
    const newWindow = window.open(url, '_blank');
    
    if (!newWindow) {
      // Se il popup è bloccato, prova a scaricare
      console.warn('Popup bloccato, scarico il PDF');
      await downloadFascicoliDocumentiPDF(id);
    }
    
    // Pulisci l'URL dopo un breve ritardo per permettere l'apertura
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
    }, 1000);
    
    return newWindow;
  } catch (error) {
    console.error('Errore preview PDF fascicoli/documenti:', error);
    throw error;
  }
};

/**
 * Utility per scaricare il PDF combinato fascicoli+documenti
 */
export const downloadFascicoliDocumentiPDF = async (id: number, nomeFile?: string) => {
  const blob = await archivioApi.stampaFascicoliDocumenti(id);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = nomeFile || `fascicoli_documenti_unita_${id}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
