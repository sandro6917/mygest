/**
 * Servizio API per Archivio Fisico
 */
import apiClient from './client';
import type {
  UnitaFisica,
  UnitaFisicaDetail,
  UnitaFisicaTreeNode,
  UnitaFisicaFilters,
  OperazioneArchivio,
  OperazioneArchivioFormData,
  OperazioneArchivioFilters,
  RigaOperazioneArchivio,
  RigaOperazioneFormData,
  CollocazioneFisica,
  VerbaleConsegnaTemplate,
  DocumentoTracciabile,
  FascicoloTracciabile,
  MovimentoProtocollo,
} from '../types/archivioFisico';

const BASE_URL = '/archivio-fisico';

// ============ Unità Fisiche ============

export const getUnitaFisiche = async (filters?: UnitaFisicaFilters) => {
  const params = new URLSearchParams();
  
  if (filters?.tipo) params.append('tipo', filters.tipo);
  if (filters?.attivo !== undefined) params.append('attivo', String(filters.attivo));
  if (filters?.archivio_fisso !== undefined) params.append('archivio_fisso', String(filters.archivio_fisso));
  if (filters?.parent) params.append('parent', String(filters.parent));
  if (filters?.search) params.append('search', filters.search);
  
  const response = await apiClient.get<UnitaFisica[]>(`${BASE_URL}/unita/?${params.toString()}`);
  return response.data;
};

export const getUnitaFisica = async (id: number) => {
  const response = await apiClient.get<UnitaFisicaDetail>(`${BASE_URL}/unita/${id}/`);
  return response.data;
};

export const getUnitaFisicheTree = async () => {
  const response = await apiClient.get<UnitaFisicaTreeNode[]>(`${BASE_URL}/unita/tree/`);
  return response.data;
};

export const getUnitaFisicaChildren = async (id: number) => {
  const response = await apiClient.get<UnitaFisica[]>(`${BASE_URL}/unita/${id}/children/`);
  return response.data;
};

export const getUnitaFisicaAncestors = async (id: number) => {
  const response = await apiClient.get<UnitaFisica[]>(`${BASE_URL}/unita/${id}/ancestors/`);
  return response.data;
};

export const getUnitaFisicheRadici = async () => {
  const response = await apiClient.get<UnitaFisica[]>(`${BASE_URL}/unita/radici/`);
  return response.data;
};

export const createUnitaFisica = async (data: Partial<UnitaFisica>) => {
  const response = await apiClient.post<UnitaFisica>(`${BASE_URL}/unita/`, data);
  return response.data;
};

export const updateUnitaFisica = async (id: number, data: Partial<UnitaFisica>) => {
  const response = await apiClient.patch<UnitaFisica>(`${BASE_URL}/unita/${id}/`, data);
  return response.data;
};

export const deleteUnitaFisica = async (id: number) => {
  await apiClient.delete(`${BASE_URL}/unita/${id}/`);
};

// ============ Operazioni Archivio ============

export const getOperazioniArchivio = async (filters?: OperazioneArchivioFilters, page = 1, pageSize = 20) => {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('page_size', String(pageSize));
  
  if (filters?.tipo_operazione) params.append('tipo_operazione', filters.tipo_operazione);
  if (filters?.referente_interno) params.append('referente_interno', String(filters.referente_interno));
  if (filters?.referente_esterno) params.append('referente_esterno', String(filters.referente_esterno));
  if (filters?.data_dal) params.append('data_dal', filters.data_dal);
  if (filters?.data_al) params.append('data_al', filters.data_al);
  if (filters?.search) params.append('search', filters.search);
  
  const response = await apiClient.get<{
    count: number;
    next: string | null;
    previous: string | null;
    results: OperazioneArchivio[];
  }>(`${BASE_URL}/operazioni/?${params.toString()}`);
  return response.data;
};

export const getOperazioneArchivio = async (id: number) => {
  const response = await apiClient.get<OperazioneArchivio>(`${BASE_URL}/operazioni/${id}/`);
  return response.data;
};

export const createOperazioneArchivio = async (data: OperazioneArchivioFormData) => {
  // Se c'è un file, usa FormData, altrimenti usa JSON
  if (data.verbale_scan) {
    const formData = new FormData();
    
    formData.append('tipo_operazione', data.tipo_operazione);
    formData.append('referente_interno', String(data.referente_interno));
    
    if (data.referente_esterno) {
      formData.append('referente_esterno', String(data.referente_esterno));
    }
    
    if (data.note) {
      formData.append('note', data.note);
    }
    
    formData.append('verbale_scan', data.verbale_scan);
    
    // Aggiungi le righe come JSON
    if (data.righe && data.righe.length > 0) {
      formData.append('righe', JSON.stringify(data.righe));
    }
    
    const response = await apiClient.post<OperazioneArchivio>(
      `${BASE_URL}/operazioni/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } else {
    // Nessun file: usa JSON normale
    const response = await apiClient.post<OperazioneArchivio>(
      `${BASE_URL}/operazioni/`,
      data
    );
    return response.data;
  }
};

export const updateOperazioneArchivio = async (id: number, data: Partial<OperazioneArchivioFormData>) => {
  // Se c'è un file, usa FormData, altrimenti usa JSON
  if (data.verbale_scan) {
    const formData = new FormData();
    
    if (data.tipo_operazione) {
      formData.append('tipo_operazione', data.tipo_operazione);
    }
    
    if (data.referente_interno) {
      formData.append('referente_interno', String(data.referente_interno));
    }
    
    if (data.referente_esterno !== undefined) {
      if (data.referente_esterno) {
        formData.append('referente_esterno', String(data.referente_esterno));
      }
    }
    
    if (data.note !== undefined) {
      formData.append('note', data.note || '');
    }
    
    formData.append('verbale_scan', data.verbale_scan);
    
    if (data.righe) {
      formData.append('righe', JSON.stringify(data.righe));
    }
    
    const response = await apiClient.patch<OperazioneArchivio>(
      `${BASE_URL}/operazioni/${id}/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } else {
    // Nessun file: usa JSON normale
    const response = await apiClient.patch<OperazioneArchivio>(
      `${BASE_URL}/operazioni/${id}/`,
      data
    );
    return response.data;
  }
};

export const deleteOperazioneArchivio = async (id: number) => {
  await apiClient.delete(`${BASE_URL}/operazioni/${id}/`);
};

export const processOperazioneArchivio = async (id: number) => {
  const response = await apiClient.post<{ status: string; message: string }>(
    `${BASE_URL}/operazioni/${id}/process/`
  );
  return response.data;
};

export const downloadVerbaleConsegna = async (operazioneId: number, templateSlug?: string) => {
  const url = templateSlug 
    ? `${BASE_URL}/operazioni/${operazioneId}/verbale/?template=${templateSlug}`
    : `${BASE_URL}/operazioni/${operazioneId}/verbale/`;
  
  const response = await apiClient.get(url, {
    responseType: 'blob',
  });
  
  // Crea un link per il download
  const blob = new Blob([response.data], {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  });
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = `verbale_consegna_${operazioneId}_${new Date().getTime()}.docx`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
};

export const getVerbaleTemplates = async () => {
  const response = await apiClient.get<VerbaleConsegnaTemplate[]>(
    `${BASE_URL}/operazioni/templates/`
  );
  return response.data;
};

// ============ Righe Operazioni ============

export const getRigheOperazione = async (operazioneId: number) => {
  const response = await apiClient.get<RigaOperazioneArchivio[]>(
    `${BASE_URL}/righe/?operazione=${operazioneId}`
  );
  return response.data;
};

export const createRigaOperazione = async (data: RigaOperazioneFormData) => {
  const response = await apiClient.post<RigaOperazioneArchivio>(`${BASE_URL}/righe/`, data);
  return response.data;
};

export const updateRigaOperazione = async (id: number, data: Partial<RigaOperazioneFormData>) => {
  const response = await apiClient.patch<RigaOperazioneArchivio>(`${BASE_URL}/righe/${id}/`, data);
  return response.data;
};

export const deleteRigaOperazione = async (id: number) => {
  await apiClient.delete(`${BASE_URL}/righe/${id}/`);
};

// ============ Collocazioni Fisiche ============

export const getCollocazioniFisiche = async (filters?: { unita?: number; documento?: number; solo_attive?: boolean }) => {
  const params = new URLSearchParams();
  
  if (filters?.unita) params.append('unita', String(filters.unita));
  if (filters?.documento) params.append('documento', String(filters.documento));
  if (filters?.solo_attive !== undefined) params.append('solo_attive', String(filters.solo_attive));
  
  const response = await apiClient.get<CollocazioneFisica[]>(`${BASE_URL}/collocazioni/?${params.toString()}`);
  return response.data;
};

// ============ Documenti e Fascicoli Tracciabili ============

export const getDocumentiTracciabili = async (
  search?: string,
  referenteEsterno?: number,
  statoOperazione?: 'latenti' | 'in_giacenza' | 'scaricati'
) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (referenteEsterno) params.append('referente_esterno', String(referenteEsterno));
  if (statoOperazione) params.append('stato_operazione', statoOperazione);
  
  const response = await apiClient.get<DocumentoTracciabile[]>(
    `${BASE_URL}/documenti-tracciabili/?${params.toString()}`
  );
  return response.data;
};

export const getFascicoliTracciabili = async (
  search?: string,
  referenteEsterno?: number,
  statoOperazione?: 'latenti' | 'in_giacenza' | 'scaricati'
) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (referenteEsterno) params.append('referente_esterno', String(referenteEsterno));
  if (statoOperazione) params.append('stato_operazione', statoOperazione);
  
  const response = await apiClient.get<FascicoloTracciabile[]>(
    `${BASE_URL}/fascicoli-tracciabili/?${params.toString()}`
  );
  return response.data;
};

export const getMovimentiProtocollo = async (filters?: {
  search?: string;
  documento_id?: number;
  fascicolo_id?: number;
}) => {
  const params = new URLSearchParams();
  
  if (filters?.search) params.append('search', filters.search);
  if (filters?.documento_id) params.append('documento_id', String(filters.documento_id));
  if (filters?.fascicolo_id) params.append('fascicolo_id', String(filters.fascicolo_id));
  
  const response = await apiClient.get<MovimentoProtocollo[]>(
    `${BASE_URL}/movimenti-protocollo/?${params.toString()}`
  );
  return response.data;
};

// ============ Utenti ============

export const getUtenti = async () => {
  const response = await apiClient.get(`${BASE_URL}/operazioni/utenti/`);
  return response.data;
};

// ============ Anagrafiche ============

export const searchAnagrafiche = async (search?: string) => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  
  const response = await apiClient.get(`/anagrafiche/?${params.toString()}`);
  return response.data.results || response.data;
};

export default {
  // Unità Fisiche
  getUnitaFisiche,
  getUnitaFisica,
  getUnitaFisicheTree,
  getUnitaFisicaChildren,
  getUnitaFisicaAncestors,
  getUnitaFisicheRadici,
  createUnitaFisica,
  updateUnitaFisica,
  deleteUnitaFisica,
  
  // Operazioni
  getOperazioniArchivio,
  getOperazioneArchivio,
  createOperazioneArchivio,
  updateOperazioneArchivio,
  deleteOperazioneArchivio,
  processOperazioneArchivio,
  downloadVerbaleConsegna,
  getVerbaleTemplates,
  
  // Righe
  getRigheOperazione,
  createRigaOperazione,
  updateRigaOperazione,
  deleteRigaOperazione,
  
  // Collocazioni
  getCollocazioniFisiche,
  
  // Ricerca
  getDocumentiTracciabili,
  getFascicoliTracciabili,
  getMovimentiProtocollo,
  
  // Utenti e Anagrafiche
  getUtenti,
  searchAnagrafiche,
};
