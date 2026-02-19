import type { MovimentoProtocollo } from '@/types/protocollo';
/**
 * Type definitions for Fascicoli module
 */

export interface TitolarioVoce {
  id: number;
  codice: string;
  titolo: string;
  pattern_codice: string;
  parent?: number | null;
  consente_intestazione?: boolean;
  anagrafica?: number | null;
  anagrafica_nome?: string;
  is_voce_intestata?: boolean;
  codice_gerarchico?: string;
}

export interface UnitaFisica {
  id: number;
  tipo: string;
  codice: string;
  nome: string;
  full_path: string;
}

export interface FascicoloListItem {
  id: number;
  codice: string;
  titolo: string;
  anno: number;
  stato: 'corrente' | 'storico' | 'chiuso' | 'deposito' | 'archivio_deposito' | 'scaricato';
  stato_display: string;
  cliente: number | null;
  cliente_display?: string;
  titolario_voce: number;
  titolario_voce_detail?: TitolarioVoce;
  parent: number | null;
  parent_display?: string;
  progressivo: number;
  sub_progressivo: number;
  ubicazione: number | null;
  ubicazione_full_path?: string;
  retention_anni: number;
  created_at: string;
  updated_at: string;
  num_pratiche?: number;
  num_sottofascicoli?: number;
  num_fascicoli_collegati?: number;
}

export interface Fascicolo extends FascicoloListItem {
  note: string;
  path_archivio: string;
  pratica_id: number | null;
  pratica_display?: string;
  pratiche_details?: Array<{
    id: number;
    codice: string;
    oggetto: string;
  }>;
  sottofascicoli?: FascicoloListItem[];
  fascicoli_collegati_details?: FascicoloListItem[];
  ubicazione_detail?: UnitaFisica;
  movimenti_protocollo?: MovimentoProtocollo[];
  protocollo_attivo?: {
    id: number;
    protocollo_label: string;
    direzione: 'IN' | 'OUT';
    data: string;
    chiuso: boolean;
  };
}

export interface FascicoloFormData {
  titolo: string;
  anno: number;
  cliente: number | null;
  titolario_voce: number;
  parent?: number | null;
  stato?: 'corrente' | 'storico' | 'chiuso' | 'deposito' | 'archivio_deposito' | 'scaricato';
  note?: string;
  ubicazione?: number | null;
  retention_anni?: number;
  pratiche?: number[];
  fascicoli_collegati?: number[];
}

export interface FascicoloFilters {
  page?: number;
  page_size?: number;
  search?: string;
  cliente?: number;
  titolario_voce?: number;
  anno?: number;
  stato?: string;
  ubicazione?: number;
  parent?: number | string; // 'null' per fascicoli radice
  ordering?: string;
  con_file?: string; // 'true' per fascicoli con documenti con file
}

export interface FascicoloListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: FascicoloListItem[];
}

export interface MovimentoFormData {
  tipo: 'entrata' | 'uscita';
  quando?: string;
  da_chi?: string;
  a_chi?: string;
  causale: string;
  note?: string;
  data_rientro_prevista?: string;
  ubicazione?: number | null;
}

export interface FascicoliStats {
  total: number;
  by_stato: Record<string, number>;
  by_anno: Record<string, number>;
}
