import jsPDF from 'jspdf';
import type { DocumentoTipoHelpData } from '@/types/help';

/**
 * Genera e scarica un PDF con la guida completa del tipo documento
 */
export const exportHelpToPDF = (
  tipoDocumento: string,
  codice: string,
  helpData: DocumentoTipoHelpData
): void => {
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 20;
  const maxWidth = pageWidth - 2 * margin;
  let yPosition = margin;

  // Funzione per sanitizzare testo rimuovendo caratteri Unicode non supportati
  const sanitizeText = (text: string): string => {
    if (!text) return '';
    
    return text
      // Frecce Unicode
      .replace(/→|➔|⇒|⟹|⇨/g, '->')
      .replace(/←|⇐|⟸/g, '<-')
      .replace(/↔|⇔/g, '<->')
      
      // Simboli comuni
      .replace(/✓|✔|☑/g, '[OK]')
      .replace(/✗|✘|☒/g, '[NO]')
      .replace(/•|●|◦|▪|▫/g, '-')
      
      // Punteggiatura speciale
      .replace(/"|"/g, '"')
      .replace(/'|'/g, "'")
      .replace(/…/g, '...')
      .replace(/–|—/g, '-')
      
      // Emoji comuni - sostituiti con prefissi testuali
      .replace(/⚠️\s*/g, '[!] ')
      .replace(/📂\s*/g, '* ')
      .replace(/📁\s*/g, '* ')
      .replace(/📝\s*/g, '- ')
      .replace(/📌\s*/g, '> ')
      .replace(/💡\s*/g, '[TIP] ')
      .replace(/�\s*/g, '[RICERCA] ')
      .replace(/�\s*/g, '[LINK] ')
      .replace(/�\s*/g, '[INFO] ')
      .replace(/⚡|�|✨|🎯|⭐/g, '')
      
      // Altri simboli
      .replace(/©/g, '(c)')
      .replace(/®/g, '(R)')
      .replace(/™/g, '(TM)')
      .replace(/°/g, ' gradi')
      .replace(/€/g, 'EUR')
      
      .trim();
  };

  // Funzione per aggiungere nuova pagina se necessario
  const checkPageBreak = (requiredSpace: number = 10) => {
    if (yPosition + requiredSpace > pageHeight - margin) {
      doc.addPage();
      yPosition = margin;
      return true;
    }
    return false;
  };

  // Funzione per aggiungere testo con word wrap
  const addText = (
    text: string,
    fontSize: number = 10,
    style: 'normal' | 'bold' | 'italic' = 'normal',
    color: [number, number, number] = [0, 0, 0]
  ) => {
    doc.setFontSize(fontSize);
    doc.setFont('helvetica', style);
    doc.setTextColor(...color);

    const sanitizedText = sanitizeText(text);
    const lines = doc.splitTextToSize(sanitizedText, maxWidth);
    lines.forEach((line: string) => {
      checkPageBreak();
      doc.text(line, margin, yPosition);
      yPosition += fontSize * 0.6; // Aumentato da 0.5 a 0.6 per migliore leggibilità
    });
    yPosition += 4; // Aumentato da 3 a 4 per più spazio tra paragrafi
  };

  // Funzione per aggiungere titolo sezione
  const addSectionTitle = (title: string) => {
    checkPageBreak(15);
    yPosition += 5;
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(33, 150, 243); // Blu MUI
    doc.text(sanitizeText(title), margin, yPosition);
    yPosition += 8;
    
    // Linea decorativa
    doc.setDrawColor(33, 150, 243);
    doc.setLineWidth(0.5);
    doc.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 5;
  };

  // Funzione per aggiungere sottotitolo
  const addSubtitle = (subtitle: string) => {
    checkPageBreak(10);
    yPosition += 3;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(0, 0, 0);
    doc.text(sanitizeText(subtitle), margin, yPosition);
    yPosition += 7;
  };

  // Funzione per aggiungere lista puntata
  const addBulletList = (items: string[]) => {
    items.forEach((item) => {
      checkPageBreak();
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(0, 0, 0);
      
      // Bullet point
      doc.circle(margin + 2, yPosition - 1.5, 0.8, 'F');
      
      // Testo con indentazione
      const sanitizedItem = sanitizeText(item);
      const lines = doc.splitTextToSize(sanitizedItem, maxWidth - 8);
      lines.forEach((line: string, idx: number) => {
        if (idx > 0) checkPageBreak();
        doc.text(line, margin + 6, yPosition);
        yPosition += 6; // Aumentato da 5 a 6 per migliore spaziatura
      });
    });
    yPosition += 3;
  };

  // Funzione per aggiungere tabella
  const addTable = (headers: string[], rows: string[][]) => {
    const colWidth = maxWidth / headers.length;
    const rowHeight = 10; // Altezza fissa riga aumentata da 8 a 10
    
    checkPageBreak(20);
    
    // Header
    doc.setFillColor(33, 150, 243);
    doc.rect(margin, yPosition - 6, maxWidth, rowHeight, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(9);
    doc.setFont('helvetica', 'bold');
    
    headers.forEach((header, idx) => {
      doc.text(sanitizeText(header), margin + idx * colWidth + 2, yPosition);
    });
    yPosition += rowHeight;

    // Righe
    doc.setTextColor(0, 0, 0);
    doc.setFont('helvetica', 'normal');
    
    rows.forEach((row, rowIdx) => {
      checkPageBreak(rowHeight + 2);
      
      // Sfondo alternato
      if (rowIdx % 2 === 0) {
        doc.setFillColor(245, 245, 245);
        doc.rect(margin, yPosition - 6, maxWidth, rowHeight, 'F');
      }
      
      row.forEach((cell, colIdx) => {
        const sanitizedCell = sanitizeText(cell);
        const cellText = doc.splitTextToSize(sanitizedCell, colWidth - 4);
        doc.text(cellText[0] || '', margin + colIdx * colWidth + 2, yPosition);
      });
      yPosition += rowHeight;
    });
    
    yPosition += 5;
  };

  // === INTESTAZIONE DOCUMENTO ===
  doc.setFillColor(33, 150, 243);
  doc.rect(0, 0, pageWidth, 40, 'F');
  
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(20);
  doc.setFont('helvetica', 'bold');
  doc.text('Guida al Documento', margin, 20);
  
  doc.setFontSize(14);
  doc.setFont('helvetica', 'normal');
  doc.text(sanitizeText(`${tipoDocumento} (${codice})`), margin, 32);
  
  yPosition = 50;

  // === DESCRIZIONE BREVE ===
  if (helpData.descrizione_breve) {
    addText(helpData.descrizione_breve, 11, 'italic', [60, 60, 60]);
    yPosition += 5;
  }

  // === QUANDO USARE ===
  if (helpData.quando_usare) {
    addSectionTitle('Quando Usare');
    
    if (helpData.quando_usare.casi_uso && helpData.quando_usare.casi_uso.length > 0) {
      addSubtitle('Casi d\'uso appropriati:');
      addBulletList(helpData.quando_usare.casi_uso);
    }
    
    if (helpData.quando_usare.non_usare_per && helpData.quando_usare.non_usare_per.length > 0) {
      addSubtitle('NON usare per:');
      addBulletList(helpData.quando_usare.non_usare_per);
    }
  }

  // === CAMPI OBBLIGATORI ===
  if (helpData.campi_obbligatori) {
    addSectionTitle('Campi Obbligatori');
    
    if (helpData.campi_obbligatori.sempre && helpData.campi_obbligatori.sempre.length > 0) {
      addSubtitle('Sempre obbligatori:');
      addBulletList(helpData.campi_obbligatori.sempre);
    }
    
    if (helpData.campi_obbligatori.condizionali && Object.keys(helpData.campi_obbligatori.condizionali).length > 0) {
      addSubtitle('Condizionali:');
      Object.entries(helpData.campi_obbligatori.condizionali).forEach(([campo, quando]) => {
        addText(`${campo}:`, 10, 'bold');
        addText(`Quando: ${quando}`, 9, 'italic', [100, 100, 100]);
      });
    }
  }

  // === GUIDA COMPILAZIONE ===
  if (helpData.guida_compilazione?.step && helpData.guida_compilazione.step.length > 0) {
    addSectionTitle('Guida alla Compilazione');
    
    helpData.guida_compilazione.step.forEach((step, idx) => {
      addSubtitle(`${idx + 1}. ${step.titolo}`);
      addText(step.descrizione);
      
      if (step.campo) {
        addText(`Campo: ${step.campo}`, 9, 'italic', [100, 100, 100]);
      }
      
      if (step.attenzione) {
        addText(`ATTENZIONE: ${step.attenzione}`, 9, 'bold', [255, 152, 0]);
      }
    });
  }

  // === ATTRIBUTI DINAMICI ===
  if (helpData.attributi_dinamici?.disponibili && helpData.attributi_dinamici.disponibili.length > 0) {
    addSectionTitle('Attributi Dinamici');
    
    helpData.attributi_dinamici.disponibili.forEach(attr => {
      addSubtitle(attr.nome);
      addText(attr.descrizione);
      addText(`Tipo: ${attr.tipo}`, 9, 'italic', [100, 100, 100]);
      
      if (attr.obbligatorio) {
        addText('Campo obbligatorio', 9, 'bold', [211, 47, 47]);
      }
      
      if (attr.choices && attr.choices.length > 0) {
        addText(`Valori ammessi: ${attr.choices.join(', ')}`, 9);
      }
    });
  }

  // === PATTERN CODICE ===
  if (helpData.pattern_codice) {
    addSectionTitle('Pattern Codice Documento');
    
    addText(`Pattern: ${helpData.pattern_codice.default}`, 11, 'bold');
    addText(helpData.pattern_codice.spiegazione);
    
    if (helpData.pattern_codice.esempi && helpData.pattern_codice.esempi.length > 0) {
      addSubtitle('Esempi:');
      helpData.pattern_codice.esempi.forEach(esempio => {
        addText(`Input: ${JSON.stringify(esempio.input)}`, 9, 'normal', [100, 100, 100]);
        addText(`Output: ${esempio.output}`, 10, 'bold', [33, 150, 243]);
        if (esempio.descrizione) {
          addText(esempio.descrizione, 9, 'italic');
        }
        yPosition += 2;
      });
    }
    
    if (helpData.pattern_codice.placeholder_disponibili) {
      addSubtitle('Placeholder Disponibili:');
      const headers = ['Placeholder', 'Descrizione'];
      const rows = Object.entries(helpData.pattern_codice.placeholder_disponibili).map(([key, value]) => [
        key,
        value
      ]);
      addTable(headers, rows);
    }
  }

  // === ARCHIVIAZIONE ===
  if (helpData.archiviazione) {
    addSectionTitle('Archiviazione');
    
    if (helpData.archiviazione.percorso_tipo) {
      addSubtitle('Struttura Percorso:');
      addText(helpData.archiviazione.percorso_tipo, 9, 'normal', [100, 100, 100]);
    }
    
    if (helpData.archiviazione.esempio_completo) {
      addSubtitle('Esempio Completo:');
      addText(helpData.archiviazione.esempio_completo, 9, 'bold', [76, 175, 80]);
    }
    
    if (helpData.archiviazione.nome_file_pattern) {
      addSubtitle('Pattern Nome File:');
      addText(helpData.archiviazione.nome_file_pattern, 9);
    }
    
    if (helpData.archiviazione.note && helpData.archiviazione.note.length > 0) {
      addSubtitle('Note Importanti:');
      addBulletList(helpData.archiviazione.note);
    }
  }

  // === RELAZIONE FASCICOLI ===
  if (helpData.relazione_fascicoli) {
    addSectionTitle('Relazione con i Fascicoli');
    
    if (helpData.relazione_fascicoli.descrizione) {
      addText(helpData.relazione_fascicoli.descrizione);
    }
    
    if (helpData.relazione_fascicoli.come_collegare) {
      addSubtitle('Come Collegare:');
      const metodi = helpData.relazione_fascicoli.come_collegare;
      
      if (metodi.metodo_1) {
        addText(`1. ${metodi.metodo_1.titolo}`, 10, 'bold');
        addText(metodi.metodo_1.descrizione);
        if (metodi.metodo_1.passaggi) addBulletList(metodi.metodo_1.passaggi);
      }
      
      if (metodi.metodo_2) {
        addText(`2. ${metodi.metodo_2.titolo}`, 10, 'bold');
        addText(metodi.metodo_2.descrizione);
        if (metodi.metodo_2.passaggi) addBulletList(metodi.metodo_2.passaggi);
      }
      
      if (metodi.metodo_3) {
        addText(`3. ${metodi.metodo_3.titolo}`, 10, 'bold');
        addText(metodi.metodo_3.descrizione);
        if (metodi.metodo_3.passaggi) addBulletList(metodi.metodo_3.passaggi);
      }
    }
    
    if (helpData.relazione_fascicoli.regole_business?.regole && helpData.relazione_fascicoli.regole_business.regole.length > 0) {
      addSubtitle('Regole di Business:');
      addBulletList(helpData.relazione_fascicoli.regole_business.regole.map(r => r.spiegazione));
    }
  }

  // === WORKFLOW ===
  if (helpData.workflow) {
    addSectionTitle('Workflow');
    
    if (helpData.workflow.stati_possibili && helpData.workflow.stati_possibili.length > 0) {
      addSubtitle('Stati Possibili:');
      addText(helpData.workflow.stati_possibili.join(' → '), 10);
      
      if (helpData.workflow.stato_iniziale) {
        addText(`Stato iniziale: ${helpData.workflow.stato_iniziale}`, 9, 'italic', [33, 150, 243]);
      }
    }
    
    if (helpData.workflow.azioni_disponibili && helpData.workflow.azioni_disponibili.length > 0) {
      addSubtitle('Azioni Disponibili:');
      const headers = ['Azione', 'Quando', 'Effetto'];
      const rows = helpData.workflow.azioni_disponibili.map(a => [
        a.azione,
        a.quando,
        a.effetto
      ]);
      addTable(headers, rows);
    }
  }

  // === PROTOCOLLAZIONE ===
  if (helpData.protocollazione) {
    addSectionTitle('Protocollazione');
    
    if (helpData.protocollazione.descrizione) {
      addText(helpData.protocollazione.descrizione, 10);
    }
    
    if (helpData.protocollazione.quando_protocollare && helpData.protocollazione.quando_protocollare.length > 0) {
      addSubtitle('Quando Protocollare:');
      addBulletList(helpData.protocollazione.quando_protocollare);
    }
    
    if (helpData.protocollazione.processo?.step && helpData.protocollazione.processo.step.length > 0) {
      addSubtitle('Processo di Protocollazione:');
      addBulletList(helpData.protocollazione.processo.step);
    }
    
    if (helpData.protocollazione.numero_protocollo) {
      addSubtitle('Numero di Protocollo:');
      const np = helpData.protocollazione.numero_protocollo;
      addText(`Formato: ${np.formato}`, 10, 'bold');
      addText(`Esempio: ${np.esempio}`, 10, 'italic', [33, 150, 243]);
      addText(np.spiegazione, 9);
    }
    
    if (helpData.protocollazione.registro) {
      addSubtitle('Registro di Protocollo:');
      addText(helpData.protocollazione.registro.descrizione, 10);
      if (helpData.protocollazione.registro.informazioni_registrate && helpData.protocollazione.registro.informazioni_registrate.length > 0) {
        addText('Informazioni registrate:', 9, 'bold');
        addBulletList(helpData.protocollazione.registro.informazioni_registrate);
      }
    }
    
    if (helpData.protocollazione.vincoli && helpData.protocollazione.vincoli.length > 0) {
      addSubtitle('Vincoli:');
      addBulletList(helpData.protocollazione.vincoli);
    }
    
    if (helpData.protocollazione.note && helpData.protocollazione.note.length > 0) {
      addSubtitle('Note Importanti:');
      addBulletList(helpData.protocollazione.note);
    }
  }

  // === TRACCIABILITA ===
  if (helpData.tracciabilita) {
    addSectionTitle('Tracciabilita');
    
    if (helpData.tracciabilita.descrizione) {
      addText(helpData.tracciabilita.descrizione, 10);
    }
    
    if (helpData.tracciabilita.cosa_viene_tracciato && helpData.tracciabilita.cosa_viene_tracciato.length > 0) {
      addSubtitle('Cosa Viene Tracciato:');
      addBulletList(helpData.tracciabilita.cosa_viene_tracciato);
    }
    
    if (helpData.tracciabilita.eventi_tracciati && helpData.tracciabilita.eventi_tracciati.length > 0) {
      addSubtitle('Eventi Tracciati:');
      const headers = ['Evento', 'Descrizione', 'Informazioni Registrate'];
      const rows = helpData.tracciabilita.eventi_tracciati.map(e => [
        e.evento,
        e.descrizione,
        e.informazioni_registrate.join(', ')
      ]);
      addTable(headers, rows);
    }
    
    if (helpData.tracciabilita.consultazione_storico) {
      addSubtitle('Consultazione Storico:');
      const cs = helpData.tracciabilita.consultazione_storico;
      addText(`Dove: ${cs.dove}`, 10, 'bold');
      addText(`Come: ${cs.come}`, 10);
      if (cs.informazioni_visualizzate && cs.informazioni_visualizzate.length > 0) {
        addText('Informazioni visualizzate:', 9, 'bold');
        addBulletList(cs.informazioni_visualizzate);
      }
    }
    
    if (helpData.tracciabilita.utilita && helpData.tracciabilita.utilita.length > 0) {
      addSubtitle('Utilita:');
      addBulletList(helpData.tracciabilita.utilita);
    }
    
    if (helpData.tracciabilita.vincoli && helpData.tracciabilita.vincoli.length > 0) {
      addSubtitle('Vincoli:');
      addBulletList(helpData.tracciabilita.vincoli);
    }
  }

  // === NOTE SPECIALI ===
  if (helpData.note_speciali) {
    addSectionTitle('Note Speciali');
    
    if (helpData.note_speciali.attenzioni && helpData.note_speciali.attenzioni.length > 0) {
      addSubtitle('Attenzioni:');
      addBulletList(helpData.note_speciali.attenzioni);
    }
    
    if (helpData.note_speciali.suggerimenti && helpData.note_speciali.suggerimenti.length > 0) {
      addSubtitle('Suggerimenti:');
      addBulletList(helpData.note_speciali.suggerimenti);
    }
    
    if (helpData.note_speciali.vincoli_business && helpData.note_speciali.vincoli_business.length > 0) {
      addSubtitle('Vincoli di Business:');
      addBulletList(helpData.note_speciali.vincoli_business);
    }
  }

  // === FAQ ===
  if (helpData.faq && helpData.faq.length > 0) {
    addSectionTitle('Domande Frequenti');
    
    helpData.faq.forEach((faq, idx) => {
      addText(`Q${idx + 1}: ${faq.domanda}`, 10, 'bold');
      addText(`R: ${faq.risposta}`, 10);
      yPosition += 5; // Aumentato da 2 a 5 per più spazio tra FAQ
    });
  }

  // === FOOTER SU OGNI PAGINA ===
  const totalPages = doc.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(150, 150, 150);
    doc.setFont('helvetica', 'normal');
    
    const footerText = sanitizeText(`MyGest - Guida Tipo Documento ${codice}`);
    const pageText = `Pagina ${i} di ${totalPages}`;
    
    doc.text(footerText, margin, pageHeight - 10);
    doc.text(pageText, pageWidth - margin - 30, pageHeight - 10);
    
    // Data generazione
    const today = new Date().toLocaleDateString('it-IT');
    doc.text(`Generato il: ${today}`, pageWidth / 2 - 20, pageHeight - 10);
  }

  // === DOWNLOAD ===
  const fileName = sanitizeText(`guida_${codice}_${tipoDocumento.toLowerCase().replace(/\s+/g, '_')}.pdf`);
  doc.save(fileName);
};
