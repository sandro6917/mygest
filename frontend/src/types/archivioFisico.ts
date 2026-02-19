/**
 * Tipi TypeScript per Archivio Fisico
 */

export type TipoUnitaFisica = 
  | 'ufficio'
  | 'stanza'
  | 'scaffale'
  | 'mobile'
  | 'anta'
  | 'ripiano'
  | 'contenitore'
  | 'cartellina';

export type TipoOperazioneArchivio = 'entrata' | 'uscita' | 'interna';

export interface UnitaFisica {
  id: number;
  codice: string;
  nome: string;
  tipo: TipoUnitaFisica;
  tipo_display: string;
  parent?: number | null;
  parent_nome?: string | null;
  full_path: string;
  attivo: boolean;
  archivio_fisso: boolean;
  ordine?: number;
  note?: string;
  prefisso_codice?: string;
  progressivo_codice?: number;
  progressivo?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UnitaFisicaDetail extends UnitaFisica {
  parent_detail?: UnitaFisica | null;
  ancestors: Array<{
    id: number;
    codice: string;
    nome: string;
    tipo: string;
  }>;
  figli_count: number;
}

export interface UnitaFisicaTreeNode extends UnitaFisica {
  children: UnitaFisicaTreeNode[];
}

export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  display_name: string;
}

export interface Anagrafica {
  id: number;
  codice: string;
  cognome?: string;
  nome?: string;
  ragione_sociale?: string;
  display_name: string;
}

export interface DocumentoTracciabile {
  id: number;
  codice: string;
  tipo: number;
  tipo_nome: string;
  descrizione: string;
  data_documento: string;
  stato: string;
  stato_display: string;
  digitale: boolean;
  tracciabile: boolean;
  ubicazione?: number | null;
  ubicazione_nome?: string | null;
}

export interface FascicoloTracciabile {
  id: number;
  codice: string;
  titolo: string;
  anno: number;
  numero: string;
  stato: string;
  stato_display: string;
  cliente?: number | null;
  cliente_nome?: string | null;
  ubicazione?: number | null;
  ubicazione_nome?: string | null;
}

export interface MovimentoProtocollo {
  id: number;
  numero: string;
  anno: number;
  direzione: string;
  direzione_display: string;
  data: string;
  documento?: number | null;
  fascicolo?: number | null;
}

export interface RigaOperazioneArchivio {
  id?: number;
  operazione?: number;
  fascicolo?: number | null;
  fascicolo_detail?: FascicoloTracciabile | null;
  documento?: number | null;
  documento_detail?: DocumentoTracciabile | null;
  movimento_protocollo?: number | null;
  movimento_protocollo_detail?: MovimentoProtocollo | null;
  unita_fisica_sorgente?: number | null;
  unita_fisica_sorgente_detail?: UnitaFisica | null;
  unita_fisica_destinazione?: number | null;
  unita_fisica_destinazione_detail?: UnitaFisica | null;
  stato_precedente?: string;
  stato_successivo?: string;
  note?: string;
  oggetto_display?: string;
}

export interface OperazioneArchivio {
  id?: number;
  tipo_operazione: TipoOperazioneArchivio;
  tipo_operazione_display?: string;
  data_ora?: string;
  referente_interno: number;
  referente_interno_detail?: User;
  referente_esterno?: number | null;
  referente_esterno_detail?: Anagrafica | null;
  note?: string;
  verbale_scan?: string | null;
  verbale_scan_url?: string | null;
  righe?: RigaOperazioneArchivio[];
  righe_count?: number;
}

export interface VerbaleConsegnaTemplate {
  id: number;
  nome: string;
  slug: string;
  descrizione?: string;
  file_template: string;
  filename_pattern: string;
  attivo: boolean;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface CollocazioneFisica {
  id: number;
  content_type: number;
  object_id: number;
  documento?: number | null;
  documento_detail?: DocumentoTracciabile | null;
  unita: number;
  unita_detail: UnitaFisica;
  attiva: boolean;
  dal: string;
  al?: string | null;
  note?: string;
  created_at: string;
  updated_at: string;
}

// Form types
export interface OperazioneArchivioFormData {
  tipo_operazione: TipoOperazioneArchivio;
  referente_interno: number;
  referente_esterno?: number | null;
  note?: string;
  verbale_scan?: File | null;
  righe: RigaOperazioneFormData[];
}

export interface RigaOperazioneFormData {
  id?: number;
  fascicolo?: number | null;
  documento?: number | null;
  movimento_protocollo?: number | null;
  unita_fisica_sorgente?: number | null;
  unita_fisica_destinazione?: number | null;
  stato_precedente?: string;
  stato_successivo?: string;
  note?: string;
}

// Filter types
export interface OperazioneArchivioFilters {
  tipo_operazione?: TipoOperazioneArchivio;
  referente_interno?: number;
  referente_esterno?: number;
  data_dal?: string;
  data_al?: string;
  search?: string;
}

export interface UnitaFisicaFilters {
  tipo?: TipoUnitaFisica;
  attivo?: boolean;
  archivio_fisso?: boolean;
  parent?: number;
  search?: string;
}
