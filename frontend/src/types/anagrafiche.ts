/**
 * Types per modulo Anagrafiche
 */

export type TipoSoggetto = 'PF' | 'PG'; // Persona Fisica | Persona Giuridica

export interface Indirizzo {
  id: number;
  tipo_indirizzo: string;
  tipo_indirizzo_display?: string;
  toponimo: string;
  indirizzo: string;
  numero_civico: string;
  frazione: string;
  cap: string;
  comune: string;
  provincia: string;
  nazione: string;
  principale: boolean;
  note: string;
  created_at?: string;
  updated_at?: string;
}

export interface EmailContatto {
  id: number;
  nominativo: string;
  email: string;
  tipo: string;
  tipo_display?: string;
  note: string;
  is_preferito: boolean;
  attivo: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Cliente {
  id: number;
  cliente_dal: string | null;
  cliente_al: string | null;
  codice_destinatario: string;
  tipo_cliente: number | null; // FK to ClientiTipo
  tipo_cliente_display?: string; // Nome leggibile
}

export interface AnagraficaList {
  id: number;
  tipo: TipoSoggetto;
  display_name: string;
  codice_fiscale: string;
  partita_iva: string;
  email: string;
  pec: string;
  telefono: string;
  codice: string | null;
  is_cliente: boolean;
  created_at: string;
  updated_at: string;
}

export interface AnagraficaDetail {
  id: number;
  tipo: TipoSoggetto;
  display_name: string;
  ragione_sociale: string;
  nome: string;
  cognome: string;
  codice_fiscale: string;
  partita_iva: string;
  codice: string | null;
  pec: string;
  email: string;
  telefono: string;
  indirizzo: string;
  note: string;
  created_at: string;
  updated_at: string;
  cliente: Cliente | null;
  indirizzi: Indirizzo[];
  contatti_email: EmailContatto[];
}

export interface AnagraficaFormData {
  tipo: TipoSoggetto;
  ragione_sociale: string;
  nome: string;
  cognome: string;
  codice_fiscale: string;
  partita_iva: string;
  pec: string;
  email: string;
  telefono: string;
  indirizzo: string;
  note: string;
  codice: string;
  // Campi Cliente (opzionali)
  is_cliente?: boolean;
  cliente_dal?: string;
  cliente_al?: string;
  codice_destinatario?: string;
  tipo_cliente?: number | null;
}

export interface ClientiTipo {
  id: number;
  codice: string;
  descrizione: string;
  slug: string;
}

export interface AnagraficaFilters {
  search?: string;
  tipo?: TipoSoggetto | '';
  is_cliente?: boolean | '';
  tipo_cliente?: number | '';
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface AnagraficheListResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: AnagraficaList[];
}
