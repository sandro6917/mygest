export interface MovimentoProtocollo {
  id: number;
  documento?: number;
  documento_display?: string;
  fascicolo?: number;
  fascicolo_display?: string;
  target_tipo?: string;
  target_type?: string | null;
  target_label?: string;
  target_object_id?: string;
  cliente: number;
  cliente_display?: string;
  direzione: 'IN' | 'OUT';
  direzione_display: string;
  data: string;
  anno: number;
  numero: number;
  protocollo_label: string;
  operatore?: number;
  operatore_display?: string;
  destinatario: string;
  destinatario_anagrafica?: number | null;
  destinatario_anagrafica_display?: string;
  destinatario_anagrafica_detail?: {
    id: number;
    display_name: string;
    tipo: 'PF' | 'PG';
    codice_fiscale?: string | null;
    partita_iva?: string | null;
  } | null;
  ubicazione?: number;
  ubicazione_full_path?: string;
  ubicazione_detail?: {
    id: number;
    codice: string;
    nome?: string;
    tipo?: string;
    tipo_display?: string;
    full_path?: string;
  } | null;
  chiuso: boolean;
  rientro_di?: number;
  data_rientro_prevista?: string;
  causale: string;
  note: string;
}
