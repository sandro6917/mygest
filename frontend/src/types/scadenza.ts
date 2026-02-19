/**
 * Types per Scadenze
 */

export interface UserSimple {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface PraticaSimple {
  id: number;
  numero: string;
  oggetto: string;
}

export interface FascicoloSimple {
  id: number;
  numero: string;
  oggetto: string;
}

export interface DocumentoSimple {
  id: number;
  numero_protocollo: string;
  oggetto: string;
}

export interface ScadenzaListItem {
  id: number;
  titolo: string;
  descrizione: string;
  stato: 'bozza' | 'attiva' | 'completata' | 'archiviata' | 'in_scadenza' | 'scaduta';
  stato_display: string;
  priorita: 'low' | 'medium' | 'high' | 'critical';
  priorita_display: string;
  categoria: string;
  data_scadenza: string | null;
  periodicita: 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'custom';
  periodicita_display: string;
  periodicita_intervallo: number;
  creato_da: number | null;
  creato_da_nome: string;
  num_assegnatari: number;
  num_occorrenze: number;
  prossima_occorrenza: string | null;
  creato_il: string;
  aggiornato_il: string;
}

export interface Scadenza {
  id: number;
  titolo: string;
  descrizione: string;
  stato: 'bozza' | 'attiva' | 'completata' | 'archiviata' | 'in_scadenza' | 'scaduta';
  stato_display: string;
  priorita: 'low' | 'medium' | 'high' | 'critical';
  priorita_display: string;
  categoria: string;
  note_interne: string;
  data_scadenza: string | null;
  creato_da: number | null;
  creato_da_detail: UserSimple | null;
  assegnatari: number[];
  assegnatari_detail: UserSimple[];
  pratiche: number[];
  pratiche_detail: PraticaSimple[];
  fascicoli: number[];
  fascicoli_detail: FascicoloSimple[];
  documenti: number[];
  documenti_detail: DocumentoSimple[];
  comunicazione_destinatari: string;
  comunicazione_modello: string;
  periodicita: 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'custom';
  periodicita_display: string;
  periodicita_intervallo: number;
  periodicita_config: Record<string, unknown>;
  google_calendar_calendar_id: string;
  google_calendar_synced_at: string | null;
  creato_il: string;
  aggiornato_il: string;
}

export interface ScadenzaFormData {
  titolo: string;
  descrizione: string;
  stato: 'bozza' | 'attiva' | 'completata' | 'archiviata' | 'in_scadenza' | 'scaduta';
  priorita: 'low' | 'medium' | 'high' | 'critical';
  categoria: string;
  note_interne: string;
  data_scadenza: string | null;
  assegnatari: number[];
  pratiche: number[];
  fascicoli: number[];
  documenti: number[];
  comunicazione_destinatari: string;
  comunicazione_modello: string;
  periodicita: 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly' | 'custom';
  periodicita_intervallo: number;
  periodicita_config: Record<string, unknown>;
  google_calendar_calendar_id: string;
}

export interface ScadenzaAlertConfig {
  // Email settings
  destinatari?: string;  // Email comma-separated (sovrascrive scadenza.comunicazione_destinatari)
  oggetto_custom?: string;  // Oggetto email personalizzato
  corpo_custom?: string;  // Corpo email personalizzato
  
  // Webhook settings
  url?: string;  // Webhook URL
  payload?: Record<string, unknown>;  // Custom payload completo
  timeout?: number;  // Timeout in secondi (default 10)
  
  [key: string]: unknown;
}

export interface ScadenzaAlert {
  id: number;
  occorrenza: number;
  offset_alert: number;
  offset_alert_periodo: 'minutes' | 'hours' | 'days' | 'weeks';
  offset_alert_periodo_display: string;
  metodo_alert: 'email' | 'webhook';
  metodo_alert_display: string;
  alert_config: ScadenzaAlertConfig;
  alert_programmata_il: string | null;
  alert_inviata_il: string | null;
  stato: 'pending' | 'scheduled' | 'sent' | 'failed';
  stato_display: string;
  creato_il: string;
  aggiornato_il: string;
}

export interface ScadenzaOccorrenzaAlertConfig {
  // Email settings
  destinatari?: string;  // Email comma-separated (sovrascrive scadenza.comunicazione_destinatari)
  oggetto_custom?: string;  // Oggetto email personalizzato
  corpo_custom?: string;  // Corpo email personalizzato (supporta template)
  
  // Webhook settings
  url?: string;  // Webhook URL
  payload?: Record<string, unknown>;  // Custom payload (sovrascrive default)
  timeout?: number;  // Timeout in secondi (default 10)
  
  [key: string]: unknown;
}

export interface ScadenzaOccorrenza {
  id: number;
  scadenza: number;  // ID della scadenza (per write)
  scadenza_dettaglio?: {  // Dettagli nested (read-only)
    id: number;
    titolo: string;
    descrizione: string;
    priorita: string;
    categoria: string;
    periodicita: string;
    stato: string;
  };
  scadenza_titolo: string;
  titolo: string;
  descrizione: string;
  inizio: string;
  fine: string | null;
  giornaliera: boolean;
  metodo_alert: 'email' | 'webhook';
  metodo_alert_display: string;
  offset_alert_minuti: number;
  alert_config: ScadenzaOccorrenzaAlertConfig;
  alert_programmata_il: string | null;
  alert_inviata_il: string | null;
  stato: 'pending' | 'scheduled' | 'alerted' | 'completed' | 'cancelled';
  stato_display: string;
  alerts?: ScadenzaAlert[];
  num_alerts?: number;
  google_calendar_event_id: string;
  google_calendar_synced_at: string | null;
  creato_il: string;
  aggiornato_il: string;
}

export interface ScadenzaFilters {
  page?: number;
  page_size?: number;
  search?: string;
  stato?: string;
  priorita?: string;
  categoria?: string;
  periodicita?: string;
  creato_da?: number;
  assegnatario?: number;
  ordering?: string;
}

export interface OccorrenzaFilters {
  page?: number;
  page_size?: number;
  scadenza?: number;
  stato?: string;
  metodo_alert?: string;
  inizio_da?: string;
  inizio_a?: string;
  ordering?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
