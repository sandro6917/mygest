/**
 * Tipi TypeScript per il modulo Comunicazioni
 */

export interface EmailContatto {
  id: number;
  email: string;
  nominativo: string;
  tipo: 'email' | 'pec';
  is_preferito: boolean;
  attivo: boolean;
  anagrafica: number;
  anagrafica_display: string;
  display_name?: string;
}

export interface MailingList {
  id: number;
  nome: string;
  slug: string;
  descrizione: string;
  attiva: boolean;
  proprietario: number;
  proprietario_display: string;
  contatti_count: number;
}

export interface TemplateContextField {
  id: number;
  template: number;
  key: string;
  label: string;
  field_type: 'text' | 'textarea' | 'integer' | 'decimal' | 'date' | 'datetime' | 'boolean' | 'choice' | 'codice_tributo';
  widget?: string;  // Widget personalizzato (es: 'anagrafica', 'fk_anagrafica')
  required: boolean;
  help_text: string;
  default_value?: string;
  choices?: string;
  source_path?: string;
  ordering: number;
  active: boolean;
}

export interface TemplateComunicazione {
  id: number;
  nome: string;
  oggetto: string;
  corpo_testo: string;
  corpo_html: string;
  attivo: boolean;
  data_creazione: string;
  data_modifica: string;
  context_fields: TemplateContextField[];
}

export interface FirmaComunicazione {
  id: number;
  nome: string;
  corpo_testo: string;
  corpo_html: string;
  attivo: boolean;
  data_creazione: string;
  data_modifica: string;
}

export interface CodiceTributoF24 {
  id: number;
  codice: string;
  sezione: 'erario' | 'inps' | 'regioni' | 'imu' | 'inail' | 'accise' | 'altri';
  descrizione: string;
  causale: string;
  periodicita: string;
  attivo: boolean;
  display: string;
}

export interface AllegatoComunicazione {
  id: number;
  comunicazione: number;
  documento?: number;
  documento_display?: string;
  fascicolo?: number;
  fascicolo_display?: string;
  file?: string;
  file_url?: string;
  nome_file?: string;
  filename: string;
  tipo: 'documento' | 'fascicolo' | 'file' | 'unknown';
  note?: string;
  data_creazione: string;
}

export interface AllegatoComunicazioneFormData {
  documento?: number;
  fascicolo?: number;
  file?: File;
  nome_file?: string;
  note?: string;
}

export interface Comunicazione {
  id: number;
  tipo: 'AVVISO' | 'DOCUMENTI' | 'INFORMATIVA';
  direzione: 'IN' | 'OUT';
  oggetto: string;
  corpo: string;
  corpo_html: string;
  mittente: string;
  destinatari: string;
  destinatari_calcolati: string[];
  destinatari_con_anagrafica: Array<{
    email: string;
    codice_anagrafica: string | null;
    ragione_sociale: string | null;
  }>;
  contatti_destinatari: number[];
  liste_destinatari: number[];
  template?: number;
  template_nome?: string;
  firma?: number;
  firma_nome?: string;
  dati_template: Record<string, any>;
  stato: 'bozza' | 'inviata' | 'errore';
  log_errore: string;
  data_creazione: string;
  data_invio?: string;
  documento_protocollo?: number;
  protocollo_movimento?: number;
  protocollo_label: string;
  email_message_id: string;
  importato_il?: string;
  import_source: string;
  allegati?: AllegatoComunicazione[];
}

export interface ComunicazioneFormData {
  tipo: string;
  direzione: string;
  oggetto: string;
  corpo: string;
  corpo_html?: string;
  mittente?: string;
  destinatari?: string;  // Opzionale, può essere popolato automaticamente dai contatti
  contatti_destinatari?: number[];
  liste_destinatari?: number[];
  template?: number;
  firma?: number;
  dati_template?: Record<string, any>;
  documento_protocollo?: number;
}

export interface EmailImport {
  id: number;
  mailbox: number;
  uid: string;
  message_id: string;
  mittente: string;
  destinatari: string;
  oggetto: string;
  data_messaggio?: string;
  importato_il: string;
  comunicazione?: number;
}

export interface ComunicazioneFilters {
  direzione?: string;
  stato?: string;
  tipo?: string;
  anagrafica?: number;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export const TIPO_COMUNICAZIONE_CHOICES = [
  { value: 'AVVISO', label: 'Avviso scadenza' },
  { value: 'DOCUMENTI', label: 'Invio documenti' },
  { value: 'INFORMATIVA', label: 'Comunicazione informativa' },
];

export const DIREZIONE_CHOICES = [
  { value: 'IN', label: 'Entrata' },
  { value: 'OUT', label: 'Uscita' },
];

export const STATO_CHOICES = [
  { value: 'bozza', label: 'Bozza' },
  { value: 'inviata', label: 'Inviata' },
  { value: 'errore', label: 'Errore invio' },
];
