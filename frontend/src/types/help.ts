/**
 * TypeScript types per sistema Help documentazione tipi documento
 */

export interface CasoUso {
  casi_uso: string[];
  non_usare_per: string[];
}

export interface CampiObbligatori {
  sempre: string[];
  condizionali: Record<string, string>;
}

export interface AttributoDinamico {
  codice: string;
  nome: string;
  tipo: string;
  modello?: string;
  descrizione: string;
  obbligatorio: boolean;
  validazione?: string;
  choices?: string[];
  default?: string;
  esempio: string;
}

export interface PatternCodeExample {
  pattern: string;
  risultato: string;
  spiegazione: string;
}

export interface AttributiDinamici {
  disponibili: AttributoDinamico[];
  pattern_code_examples: PatternCodeExample[];
}

export interface StepCompilazione {
  numero: number;
  titolo: string;
  descrizione: string;
  campo: string;
  tipo?: string;
  screenshot?: string;
  attenzione?: string;
  validazione?: string;
  suggerimento?: string;
  esempio: string;
  default?: string;
  choices?: string[];
  formati_accettati?: string[];
  dimensione_max?: string;
}

export interface Shortcut {
  titolo: string;
  descrizione: string;
  link: string;
  vantaggi?: string[];
}

export interface GuidaCompilazione {
  step: StepCompilazione[];
  shortcut?: Shortcut;
}

export interface EsempioPatternCodice {
  input: {
    dipendente?: string;
    anno?: number;
    sequenza?: number;
    [key: string]: any;
  };
  output: string;
  descrizione?: string;
}

export interface PatternCodice {
  default: string;
  spiegazione: string;
  esempi: EsempioPatternCodice[];
  placeholder_disponibili: Record<string, string>;
  personalizzazione?: string;
}

export interface Archiviazione {
  percorso_tipo: string;
  esempio: string;
  nome_file_pattern?: string;
  esempio_file?: string;
  esempio_completo: string;
  note: string[];
  organizzazione?: string;
}

export interface MetodoCollegamentoFascicolo {
  titolo: string;
  descrizione: string;
  passaggi: string[];
  benefici?: string[];
  attenzioni?: string[];
  limitazioni?: string[];
}

export interface RegolaBusinessFascicolo {
  regola: string;
  spiegazione: string;
  esempio_ok?: string;
  esempio_ko?: string;
  comportamento?: string;
  warning?: string;
  esempio?: string;
  importante?: string;
}

export interface CasoUsoFascicolo {
  scenario: string;
  descrizione: string;
  vantaggi?: string;
  esempio_struttura?: string;
  attenzione?: string;
  quando_usare?: string;
  limitazione?: string;
}

export interface RelazioneFascicoli {
  descrizione: string;
  vantaggi_collegamento: string[];
  come_collegare: {
    metodo_1?: MetodoCollegamentoFascicolo;
    metodo_2?: MetodoCollegamentoFascicolo;
    metodo_3?: MetodoCollegamentoFascicolo;
  };
  regole_business: {
    titolo: string;
    regole: RegolaBusinessFascicolo[];
  };
  casi_uso_tipici: {
    caso_1?: CasoUsoFascicolo;
    caso_2?: CasoUsoFascicolo;
    caso_3?: CasoUsoFascicolo;
  };
  domande_frequenti: FAQ[];
  best_practices: string[];
}

export interface AzioneWorkflow {
  azione: string;
  quando: string;
  effetto: string;
  permessi?: string;
  requisiti?: string[];
  attenzione?: string;
}

export interface Workflow {
  stati_possibili: string[];
  stato_iniziale?: string;
  azioni_disponibili: AzioneWorkflow[];
  transizioni?: Record<string, string>;
}

export interface Protocollazione {
  descrizione: string;
  quando_protocollare: string[];
  processo: {
    step: string[];
  };
  numero_protocollo: {
    formato: string;
    esempio: string;
    spiegazione: string;
  };
  registro: {
    descrizione: string;
    informazioni_registrate: string[];
  };
  vincoli: string[];
  note: string[];
}

export interface Tracciabilita {
  descrizione: string;
  cosa_viene_tracciato: string[];
  eventi_tracciati: {
    evento: string;
    descrizione: string;
    informazioni_registrate: string[];
  }[];
  consultazione_storico: {
    dove: string;
    come: string;
    informazioni_visualizzate: string[];
  };
  utilita: string[];
  vincoli: string[];
}

export interface NoteSpeciali {
  attenzioni: string[];
  suggerimenti: string[];
  vincoli_business: string[];
  privacy?: string[];
}

export interface FAQ {
  domanda: string;
  risposta: string;
}

export interface GuidaCorrelata {
  titolo: string;
  url: string;
  descrizione: string;
}

export interface TipoDocumentoCorrelato {
  codice: string;
  nome: string;
  descrizione: string;
}

export interface LinkEsterno {
  titolo: string;
  url: string;
  descrizione: string;
}

export interface RisorseCorrelate {
  guide_correlate: GuidaCorrelata[];
  tipi_documento_correlati: TipoDocumentoCorrelato[];
  link_esterni?: LinkEsterno[];
}

export interface ChangelogEntry {
  versione: string;
  data: string;
  modifiche: string[];
}

/**
 * Struttura completa dati Help per tipo documento
 */
export interface DocumentoTipoHelpData {
  descrizione_breve: string;
  quando_usare: CasoUso;
  campi_obbligatori: CampiObbligatori;
  attributi_dinamici: AttributiDinamici;
  guida_compilazione: GuidaCompilazione;
  pattern_codice: PatternCodice;
  archiviazione: Archiviazione;
  relazione_fascicoli?: RelazioneFascicoli;
  protocollazione?: Protocollazione;
  tracciabilita?: Tracciabilita;
  workflow: Workflow;
  note_speciali: NoteSpeciali;
  faq: FAQ[];
  risorse_correlate: RisorseCorrelate;
  changelog?: ChangelogEntry[];
}
