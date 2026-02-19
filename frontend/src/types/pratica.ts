/**
 * Type definitions for Pratiche module
 */

export interface PraticheTipo {
  id: number;
  codice: string;
  nome: string;
  prefisso_codice: string;
  pattern_codice: string;
}

export interface Cliente {
  id: number;
  anagrafica: number;
  anagrafica_display?: string;
  codice_fiscale: string;
  partita_iva: string;
}

export interface FascicoloSimple {
  id: number;
  codice: string;
  titolo: string;
  stato: string;
  stato_display: string;
}

export interface ScadenzaSimple {
  id: number;
  titolo: string;
  descrizione: string;
  stato: string;
  stato_display: string;
  priorita: string;
  priorita_display: string;
  data_scadenza: string | null;
  categoria: string;
}

export interface PraticaListItem {
  id: number;
  codice: string;
  tipo: number;
  tipo_detail: PraticheTipo;
  cliente: number;
  cliente_detail: Cliente;
  oggetto: string;
  stato: 'aperta' | 'lavorazione' | 'attesa' | 'chiusa';
  stato_display: string;
  responsabile: number | null;
  responsabile_nome: string;
  data_apertura: string;
  data_chiusura: string | null;
  periodo_riferimento: 'anno' | 'annomese' | 'annomesegiorno';
  data_riferimento: string;
  num_note: number;
  ultima_nota: string | null;
}

export interface Pratica extends PraticaListItem {
  periodo_riferimento_display: string;
  periodo_key: string;
  progressivo: number;
  note: string;
  tag: string;
  tipo_detail: PraticheTipo;
  cliente_detail: Cliente;
  note_collegate: PraticaNota[];
  fascicoli: FascicoloSimple[];
  scadenze: ScadenzaSimple[];
}

export interface PraticaNota {
  id: number;
  tipo: 'memo' | 'comunicazione' | 'chiusura' | 'altro';
  tipo_display: string;
  testo: string;
  data: string;
  stato: 'aperta' | 'chiusa';
  stato_display: string;
}

export interface PraticaNotaFormData {
  pratica: number;
  tipo: string;
  testo: string;
  data: string;
  stato: string;
}

export interface PraticaFormData {
  tipo: number | null;
  cliente: number | null;
  oggetto: string;
  stato: string;
  responsabile: number | null;
  periodo_riferimento: string;
  data_riferimento: string;
  data_chiusura: string | null;
  note: string;
  tag: string;
}

export interface PraticaListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PraticaListItem[];
}

export interface PraticaFilters {
  page?: number;
  page_size?: number;
  search?: string;
  tipo?: number;
  cliente?: number;
  stato?: string;
  responsabile?: number;
  periodo_riferimento?: string;
  data_apertura_da?: string;
  data_apertura_a?: string;
  ordering?: string;
}
