import type { MovimentoProtocollo } from '@/types/protocollo';
import type { UnitaFisica } from '@/types/fascicolo';
import type { DocumentoTipoHelpData } from '@/types/help';

export interface DocumentiTipo {
  id: number;
  codice: string;
  nome: string;
  estensioni_permesse: string;
  pattern_codice: string;
  nome_file_pattern: string;
  attivo: boolean;
  help_data?: DocumentoTipoHelpData;
  help_ordine?: number;
  help_status?: 'completo' | 'parziale' | 'da_completare' | 'vuoto' | 'non_disponibile';
  help_visibile_pubblico?: boolean;
}

export interface TitolarioVoce {
  id: number;
  codice: string;
  titolo: string;
  parent?: number | null;
  pattern_codice: string;
  path_display?: string;
  consente_intestazione?: boolean;
  anagrafica?: number | null;
  anagrafica_nome?: string;
  is_voce_intestata?: boolean;
  codice_gerarchico?: string;
}

export interface AttributoDefinizione {
  id: number;
  tipo_documento: number;
  codice: string;
  nome: string;
  tipo_dato: 'string' | 'int' | 'decimal' | 'date' | 'datetime' | 'bool' | 'choice';
  widget?: string;
  scelte?: string;
  obbligatorio: boolean;
  ordine: number;
  help_text: string;
}

export interface AttributoValore {
  id: number;
  documento: number;
  definizione: number;
  definizione_detail?: AttributoDefinizione;
  valore: string;
}

export interface Fascicolo {
  id: number;
  codice: string;
  titolo: string;
  cliente: number;
  cliente_display?: string;
  titolario_voce?: number;
  titolario_voce_display?: string;
}

export interface Cliente {
  id: number;
  anagrafica: number;
  anagrafica_display?: string;
  codice_fiscale?: string;
  partita_iva?: string;
}

export interface DocumentoMovimento {
  id: number;
  documento: number;
  direzione: 'IN' | 'OUT';
  data_movimento: string;
  destinatario?: string;
  note: string;
  chiuso: boolean;
  chiuso_il?: string;
  chiuso_da?: number;
}

export interface Documento {
  id: number;
  codice: string;
  tipo: number;
  tipo_detail?: DocumentiTipo;
  fascicolo?: number | null;
  fascicolo_detail?: Fascicolo;
  cliente: number;
  cliente_detail?: Cliente;
  titolario_voce?: number;
  titolario_voce_detail?: TitolarioVoce;
  ubicazione?: number | null;
  ubicazione_detail?: UnitaFisica | null;
  descrizione: string;
  data_documento: string;
  stato: 'bozza' | 'definitivo' | 'archiviato' | 'uscito' | 'consegnato' | 'scaricato';
  digitale: boolean;
  tracciabile: boolean;
  file?: string;
  percorso_archivio: string;
  tags: string;
  note: string;
  creato_il: string;
  aggiornato_il: string;
  out_aperto: boolean;
  attributi?: AttributoValore[];
  movimenti?: DocumentoMovimento[];
  movimenti_protocollo?: MovimentoProtocollo[];
  protocollo_attivo?: {
    id: number;
    protocollo_label: string;
    direzione: 'IN' | 'OUT';
    data: string;
    chiuso: boolean;
  };
  protocollo_numero?: number;
  protocollo_anno?: number;
  protocollo_direzione?: 'IN' | 'OUT';
  protocollo_data?: string;
  file_url?: string;
  file_name?: string;
}

export interface DocumentoFormData {
  tipo: number;
  cliente?: number | null;
  fascicolo?: number | null;
  titolario_voce?: number | null;
  ubicazione?: number | null;
  descrizione: string;
  data_documento: string;
  stato: string;
  digitale: boolean;
  tracciabile: boolean;
  file?: File;
  file_operation?: 'copy' | 'move';
  tags?: string;
  note?: string;
  [key: string]: string | number | boolean | File | null | undefined; // per attributi dinamici attr_*
}

export type AttributiPayload = Record<string, string | number | boolean>;

export interface DocumentoJsonPayload {
  tipo?: number;
  cliente?: number | null;
  fascicolo?: number | null;
  titolario_voce?: number | null;
  ubicazione?: number | null;
  descrizione?: string;
  data_documento?: string;
  stato?: string;
  digitale?: boolean;
  tracciabile?: boolean;
  file_operation?: 'copy' | 'move';
  tags?: string;
  note?: string;
  file?: null;
  attributi?: AttributiPayload;
  delete_source_file?: boolean;
  source_file_path?: string;
}

export interface DocumentoFilters {
  search?: string;
  tipo?: number;
  cliente?: number;
  fascicolo?: number;
  fascicolo__isnull?: boolean; // Filtro per documenti non fascicolati
  stato?: string;
  data_da?: string;
  data_a?: string;
  digitale?: boolean;
  tracciabile?: boolean;
  ubicazione?: number;
  ordering?: string;
}

export interface ProtocollazioneData {
  direzione: 'IN' | 'OUT';
  destinatario?: string;
  note?: string;
}

export interface DocumentoListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Documento[];
}
