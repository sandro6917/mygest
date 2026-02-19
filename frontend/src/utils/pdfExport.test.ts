/**
 * Test manuale per export PDF help documenti
 * 
 * Eseguire questi test in browser dopo aver avviato il dev server:
 * 1. npm run dev
 * 2. Navigare su http://localhost:5173/help/documenti/CED
 * 3. Seguire gli step di test
 */

export const MANUAL_PDF_TESTS = [
  {
    id: 1,
    nome: 'Download PDF Base',
    steps: [
      'Navigare su /help/documenti/CED',
      'Verificare presenza pulsante "Scarica PDF" (rosso, outlined)',
      'Click su "Scarica PDF"',
      'Verificare download file: guida_CED_cedolino_paga.pdf',
      'Aprire PDF e verificare leggibilità',
    ],
    expectedResult: 'PDF scaricato e visualizzabile correttamente',
  },
  {
    id: 2,
    nome: 'Contenuto PDF Completo',
    steps: [
      'Aprire PDF scaricato dal test 1',
      'Verificare intestazione blu con titolo "Guida al Documento"',
      'Scorrere tutte le pagine e verificare presenza sezioni:',
      '  - Quando Usare',
      '  - Campi Obbligatori',
      '  - Guida alla Compilazione',
      '  - Attributi Dinamici',
      '  - Pattern Codice Documento (con tabella placeholder)',
      '  - Archiviazione',
      '  - Relazione con i Fascicoli',
      '  - Workflow (con tabelle azioni)',
      '  - Note Speciali',
      '  - FAQ',
    ],
    expectedResult: 'Tutte le 10+ sezioni presenti e formattate correttamente',
  },
  {
    id: 3,
    nome: 'Formattazione Tabelle',
    steps: [
      'Nel PDF, cercare sezione "Pattern Codice Documento"',
      'Verificare tabella "Placeholder Disponibili":',
      '  - Header blu con testo bianco',
      '  - Righe alternate grigio/bianco',
      '  - 2 colonne: Placeholder | Descrizione',
      '  - 8 righe di placeholder ({CLI}, {COGNOME}, etc.)',
      'Cercare sezione "Workflow"',
      'Verificare tabella "Azioni Disponibili":',
      '  - 3 colonne: Azione | Quando | Effetto',
      '  - Formattazione corretta',
    ],
    expectedResult: 'Tabelle ben formattate con header colorati',
  },
  {
    id: 4,
    nome: 'Paginazione e Footer',
    steps: [
      'Verificare numero pagine in PDF (dovrebbe essere 5-7 pagine per CED)',
      'Su ogni pagina verificare footer:',
      '  - Sinistra: "MyGest - Guida Tipo Documento CED"',
      '  - Centro: "Generato il: [data odierna]"',
      '  - Destra: "Pagina X di Y"',
      'Verificare che numerazione sia corretta (es. "Pagina 1 di 5")',
    ],
    expectedResult: 'Footer presente su tutte le pagine con info corrette',
  },
  {
    id: 5,
    nome: 'Page Break Corretto',
    steps: [
      'Scorrere PDF e verificare che:',
      '  - Titoli sezione non siano "orfani" (senza contenuto nella stessa pagina)',
      '  - Tabelle non siano spezzate a metà (se possibile)',
      '  - Liste puntate siano leggibili anche se vanno a capo pagina',
    ],
    expectedResult: 'Layout professionale senza interruzioni brusche',
  },
  {
    id: 6,
    nome: 'Testo e Font',
    steps: [
      'Selezionare testo nel PDF (dovrebbe essere selezionabile, non immagine)',
      'Verificare leggibilità font (Helvetica standard)',
      'Cercare caratteri speciali (accenti, apostrofi):',
      '  - "à", "è", "ì", "ò", "ù"',
      '  - Apostrofi in "d\'uso"',
      'Verificare che siano renderizzati correttamente',
    ],
    expectedResult: 'Testo selezionabile e caratteri speciali corretti',
  },
  {
    id: 7,
    nome: 'Liste Puntate',
    steps: [
      'Cercare sezione "Quando Usare" → "Casi d\'uso appropriati"',
      'Verificare lista puntata:',
      '  - Bullet point (pallino nero) visibile',
      '  - Indentazione corretta',
      '  - Testo allineato dopo bullet',
      '  - Word wrap corretto per elementi lunghi',
    ],
    expectedResult: 'Liste puntate ben formattate e leggibili',
  },
  {
    id: 8,
    nome: 'Esempi Pattern Codice',
    steps: [
      'Cercare sezione "Pattern Codice Documento" → "Esempi"',
      'Verificare box esempio:',
      '  - Box grigio con "Input: {...}"',
      '  - Output in blu con font monospace',
      '  - Descrizione sotto output',
      'Verificare presenza almeno 2 esempi',
    ],
    expectedResult: 'Esempi formattati in box colorati con chiarezza',
  },
  {
    id: 9,
    nome: 'Edge Case - Tipo Senza Help',
    steps: [
      'Navigare su /help/documenti',
      'Se esiste tipo senza help_data, click su di esso',
      'Verificare che pulsante "Scarica PDF" sia:',
      '  - Nascosto, oppure',
      '  - Disabilitato, oppure',
      '  - Non causi errore se cliccato',
    ],
    expectedResult: 'Gestione corretta assenza help_data',
  },
  {
    id: 10,
    nome: 'Performance - Tempo Download',
    steps: [
      'Navigare su /help/documenti/CED',
      'Click "Scarica PDF"',
      'Misurare tempo tra click e apertura dialog download',
      '  - Dovrebbe essere < 1-2 secondi',
      'Verificare che browser non si blocchi durante generazione',
    ],
    expectedResult: 'Download rapido senza freeze interfaccia',
  },
];

/**
 * Checklist validazione PDF generato
 */
export const PDF_VALIDATION_CHECKLIST = {
  struttura: [
    'Intestazione blu con titolo e sottotitolo',
    'Descrizione breve in corsivo',
    'Almeno 8 sezioni principali',
    'Footer su ogni pagina',
  ],
  contenuto: [
    'Quando Usare: casi_uso e non_usare_per',
    'Campi Obbligatori: sempre e condizionali',
    'Guida Compilazione: step numerati',
    'Attributi Dinamici: lista con dettagli',
    'Pattern Codice: pattern + tabella placeholder',
    'Archiviazione: percorsi + note',
    'Fascicoli: metodi collegamento + regole',
    'Workflow: stati + tabella azioni',
    'Note Speciali: attenzioni + suggerimenti',
    'FAQ: domande e risposte',
  ],
  formattazione: [
    'Titoli sezioni in blu con linea decorativa',
    'Sottotitoli in grassetto nero',
    'Liste puntate con bullet point',
    'Tabelle con header blu',
    'Righe tabella alternate grigio/bianco',
    'Font monospace per codici/percorsi',
    'Colori warning (arancione) per attenzioni',
  ],
  qualita: [
    'Testo selezionabile (non immagine)',
    'Caratteri speciali corretti (accenti)',
    'Word wrap appropriato',
    'Page break non spezza sezioni critiche',
    'Numerazione pagine corretta',
    'Data generazione presente in footer',
  ],
  file: [
    'Nome file pattern: guida_{CODICE}_{nome}.pdf',
    'Dimensione file ragionevole (100-300 KB)',
    'Apribile in tutti i PDF reader comuni',
    'Stampabile senza problemi',
  ],
};

/**
 * Note per sviluppatori
 */
export const DEVELOPER_NOTES = {
  jsPDF: {
    version: '2.5+',
    docs: 'https://github.com/parallax/jsPDF',
    limitazioni: [
      'Solo font standard PDF (Helvetica, Times, Courier)',
      'No supporto nativo SVG/immagini complesse',
      'Colori solo RGB (no CMYK)',
      'Performance degrada con PDF >50 pagine',
    ],
  },
  
  estensioni_future: [
    'Embed logo aziendale nell\'intestazione',
    'Supporto immagini Base64 per screenshot',
    'Generazione server-side con puppeteer',
    'Export batch multipli tipi documento',
    'Temi colore personalizzabili',
    'Link cliccabili a risorse esterne',
  ],
  
  debugging: {
    console_log: 'Decommentare console.log in pdfExport.ts per debug',
    test_local: 'Testare sempre in ambiente dev prima di committare',
    browser_support: 'Verificare Chrome, Firefox, Safari, Edge',
  },
};

/**
 * Comandi utili per testing
 */
export const USEFUL_COMMANDS = {
  dev: 'npm run dev',
  build: 'npm run build',
  typecheck: 'npx tsc --noEmit',
  lint: 'npm run lint',
  
  test_sequence: [
    'cd /home/sandro/mygest/frontend',
    'npm run dev',
    '// Aprire browser su http://localhost:5173',
    '// Navigare su /help/documenti/CED',
    '// Click "Scarica PDF"',
    '// Verificare PDF scaricato',
  ],
};
