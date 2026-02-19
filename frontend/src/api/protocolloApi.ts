/**
 * API per gestione protocollo
 */
import { apiClient } from './client';
import type { MovimentoProtocollo } from '@/types/protocollo';

export interface ProtocollazioneInput {
  direzione: 'IN' | 'OUT';
  quando?: string;
  da_chi?: string;
  da_chi_anagrafica?: number;
  a_chi?: string;
  a_chi_anagrafica?: number;
  data_rientro_prevista?: string;
  ubicazione_id?: number;
  causale?: string;
  note?: string;
  target_type?: string;
  target_id?: string | number;
}

export interface ProtocollazioneResponse {
  success: boolean;
  message: string;
  movimento?: MovimentoProtocollo;
  error?: string;
}

/**
 * Ottiene lista movimenti protocollo con filtri
 */
export const getMovimentiProtocollo = async (params?: {
  documento?: number;
  fascicolo?: number;
  direzione?: 'IN' | 'OUT';
  anno?: number;
  cliente?: number;
  chiuso?: boolean;
}): Promise<MovimentoProtocollo[]> => {
  const response = await apiClient.get('/protocollo/movimenti/', { params });
  return response.data.results || response.data;
};

/**
 * Ottiene dettaglio movimento protocollo
 */
export const getMovimentoProtocollo = async (id: number): Promise<MovimentoProtocollo> => {
  const response = await apiClient.get(`/protocollo/movimenti/${id}/`);
  return response.data;
};

/**
 * Protocolla un documento
 */
export const protocollaDocumento = async (
  documentoId: number,
  data: ProtocollazioneInput
): Promise<ProtocollazioneResponse> => {
  const response = await apiClient.post(
    `/protocollo/movimenti/protocolla-documento/${documentoId}/`,
    data
  );
  return response.data;
};

/**
 * Protocolla un fascicolo
 */
export const protocollaFascicolo = async (
  fascicoloId: number,
  data: ProtocollazioneInput
): Promise<ProtocollazioneResponse> => {
  const response = await apiClient.post(
    `/protocollo/movimenti/protocolla-fascicolo/${fascicoloId}/`,
    data
  );
  return response.data;
};

export const protocollaTarget = async (
  data: ProtocollazioneInput
): Promise<ProtocollazioneResponse> => {
  const response = await apiClient.post(`/protocollo/movimenti/protocolla-target/`, data);
  return response.data;
};

export default {
  getMovimentiProtocollo,
  getMovimentoProtocollo,
  protocollaDocumento,
  protocollaFascicolo,
  protocollaTarget,
};
