#!/usr/bin/env python3
"""
Script per generare un PDF con l'analisi della gestione scadenze.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from datetime import datetime

def create_pdf():
    """Genera il PDF con l'analisi."""
    
    filename = f"analisi_scadenze_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4,
                           rightMargin=2*cm, leftMargin=2*cm,
                           topMargin=2*cm, bottomMargin=2*cm)
    
    # Container per gli elementi
    story = []
    
    # Stili
    styles = getSampleStyleSheet()
    
    # Stile titolo personalizzato
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Stile sottotitolo
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Stile sezione
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    # Stile normale
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )
    
    # Titolo principale
    story.append(Paragraph("ANALISI GESTIONE SCADENZE", title_style))
    story.append(Paragraph(f"MyGest - Data: {datetime.now().strftime('%d/%m/%Y')}", 
                          ParagraphStyle('Date', parent=styles['Normal'], 
                                       fontSize=10, alignment=TA_CENTER,
                                       textColor=colors.grey)))
    story.append(Spacer(1, 0.5*cm))
    
    # Introduzione
    story.append(Paragraph("1. INTRODUZIONE", subtitle_style))
    intro_text = """
    La gestione delle scadenze rappresenta un obiettivo primario del progetto MyGest. 
    Questo documento analizza lo stato attuale dell'implementazione, confrontandola con 
    i requisiti desiderati, e propone un piano di miglioramento dettagliato.
    """
    story.append(Paragraph(intro_text, normal_style))
    story.append(Spacer(1, 0.3*cm))
    
    # Requisiti desiderati
    story.append(Paragraph("2. REQUISITI DESIDERATI", subtitle_style))
    
    story.append(Paragraph("2.1 Modello Scadenza", section_style))
    req_scadenza = """
    La scadenza è un promemoria di un flusso di lavoro con i seguenti attributi:
    """
    story.append(Paragraph(req_scadenza, normal_style))
    
    # Lista attributi Scadenza
    scadenza_attrs = [
        "titolo - identificativo della scadenza",
        "descrizione - dettagli estesi",
        "stato - stato corrente della scadenza",
        "priorità - livello di urgenza",
        "categoria - classificazione tematica",
        "note_interne - annotazioni riservate",
        "periodicità - unità di ripetizione (giornaliera, mensile, settimanale)",
        "periodicità_intervallo - numero di unità tra occorrenze (es: ogni 3 mesi)",
        "num_occorrenze - numero totale di occorrenze da generare",
        "data_scadenza - data della prima o unica occorrenza",
        "google_calendar_calendar_id - ID calendario Google per sincronizzazione",
        "Collegamenti: pratica, documento, fascicolo (opzionali)",
        "Assegnatari: uno o più utenti responsabili"
    ]
    
    story.append(ListFlowable(
        [ListItem(Paragraph(attr, normal_style)) for attr in scadenza_attrs],
        bulletType='bullet',
        leftIndent=20
    ))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("2.2 Modello Occorrenza", section_style))
    req_occ = """
    Le occorrenze sono la proiezione temporale della scadenza. Ogni scadenza ha almeno 
    1 occorrenza. Gli attributi previsti sono:
    """
    story.append(Paragraph(req_occ, normal_style))
    
    occ_attrs = [
        "titolo - può differire dalla scadenza padre",
        "descrizione - dettagli specifici dell'occorrenza",
        "data - giorno dell'occorrenza",
        "ora_inizio - orario di inizio",
        "ora_fine - orario di fine",
        "giornaliera - flag per evento all-day",
        "stato - stato specifico dell'occorrenza",
        "google_calendar_event_id - ID evento Google Calendar",
        "google_calendar_synced_at - timestamp sincronizzazione"
    ]
    
    story.append(ListFlowable(
        [ListItem(Paragraph(attr, normal_style)) for attr in occ_attrs],
        bulletType='bullet',
        leftIndent=20
    ))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("2.3 Sistema Alert", section_style))
    alert_req = """
    Ogni occorrenza deve supportare MULTIPLI alert con:
    """
    story.append(Paragraph(alert_req, normal_style))
    
    alert_attrs = [
        "metodo_alert - email, webhook o altro",
        "offset_alert_periodo - unità di tempo (minuti, ore, giorni, settimane)",
        "offset_alert - numero di unità prima dell'occorrenza",
        "alert_programmata_il - timestamp calcolato per l'invio",
        "Esempio: primo alert 1 settimana prima, secondo 1 giorno prima, terzo 1 ora prima"
    ]
    
    story.append(ListFlowable(
        [ListItem(Paragraph(attr, normal_style)) for attr in alert_attrs],
        bulletType='bullet',
        leftIndent=20
    ))
    
    story.append(PageBreak())
    
    # Stato attuale
    story.append(Paragraph("3. STATO ATTUALE IMPLEMENTAZIONE", subtitle_style))
    
    story.append(Paragraph("3.1 Aspetti Soddisfatti ✓", section_style))
    soddisfatti_text = """
    L'implementazione attuale copre correttamente molti aspetti:
    """
    story.append(Paragraph(soddisfatti_text, normal_style))
    
    # Tabella aspetti soddisfatti
    data_ok = [
        ['Componente', 'Attributi Implementati'],
        ['Scadenza', 'titolo, descrizione, stato, priorità, categoria, note_interne'],
        ['', 'periodicità, periodicità_intervallo, google_calendar_calendar_id'],
        ['', 'Collegamenti M2M: pratiche, fascicoli, documenti'],
        ['', 'Assegnatari M2M con User'],
        ['Occorrenza', 'titolo, descrizione, stato, metodo_alert'],
        ['', 'google_calendar_event_id, google_calendar_synced_at'],
        ['', 'Collegamento a Comunicazione'],
        ['Servizi', 'OccurrenceGenerator per generazione occorrenze'],
        ['', 'AlertDispatcher per invio notifiche'],
        ['', 'GoogleCalendarSync per sincronizzazione'],
    ]
    
    table_ok = Table(data_ok, colWidths=[4*cm, 11*cm])
    table_ok.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table_ok)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("3.2 Problemi e Discrepanze Critiche ✗", section_style))
    
    # Box problemi critici
    problemi = [
        "<b>1. Attributi mancanti in Scadenza:</b>",
        "   • num_occorrenze: non esiste come campo del modello",
        "   • data_scadenza: manca il campo per la data della prima occorrenza",
        "",
        "<b>2. Problemi in ScadenzaOccorrenza:</b>",
        "   • Mancano campi separati: data, ora_inizio, ora_fine",
        "   • Esiste solo 'inizio' e 'fine' come DateTimeField completi",
        "   • giornaliera: manca il flag per eventi all-day",
        "   • offset_alert_periodo: non esiste come campo",
        "   • Si usa solo offset_alert_minuti invece di unità configurabili",
        "",
        "<b>3. LIMITAZIONE CRITICA - Alert Singolo:</b>",
        "   • Ogni occorrenza supporta UN SOLO alert",
        "   • Requisito: MULTIPLI alert per occorrenza",
        "   • Impossibile configurare: 1 settimana + 1 giorno + 1 ora prima",
        "",
        "<b>4. Interfaccia utente:</b>",
        "   • Vista lista non evidenzia l'accoppiata Scadenza/Occorrenza",
        "   • Manca una vista Scadenziario dedicata",
        "   • Alert multipli non gestibili tramite form",
    ]
    
    for problema in problemi:
        story.append(Paragraph(problema, normal_style))
    
    story.append(PageBreak())
    
    # Soluzioni proposte
    story.append(Paragraph("4. SOLUZIONI PROPOSTE", subtitle_style))
    
    story.append(Paragraph("4.1 Soluzione Alert Multipli (PRIORITÀ ALTA)", section_style))
    sol1 = """
    <b>Problema:</b> Attualmente ogni occorrenza ha un solo alert.<br/>
    <b>Soluzione:</b> Creare un nuovo modello <b>ScadenzaAlert</b> con relazione 
    ForeignKey verso ScadenzaOccorrenza.
    """
    story.append(Paragraph(sol1, normal_style))
    story.append(Spacer(1, 0.2*cm))
    
    # Struttura nuovo modello
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=8,
        leftIndent=20,
        backColor=colors.HexColor('#f5f5f5'),
        borderPadding=5
    )
    
    code = """
<font face="Courier" size="8">
class ScadenzaAlert(models.Model):<br/>
    occorrenza = ForeignKey(ScadenzaOccorrenza, related_name='alerts')<br/>
    offset_alert_periodo = CharField(choices=[minuti, ore, giorni, settimane])<br/>
    offset_alert = PositiveIntegerField()  # numero di unità<br/>
    metodo_alert = CharField(choices=[EMAIL, WEBHOOK])<br/>
    alert_config = JSONField()<br/>
    alert_programmata_il = DateTimeField()  # calcolato automaticamente<br/>
    alert_inviata_il = DateTimeField(null=True)<br/>
    stato = CharField(choices=[pending, sent, failed])<br/>
</font>
    """
    story.append(Paragraph(code, code_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("Vantaggi:", normal_style))
    vantaggi = [
        "Supporto illimitato di alert per occorrenza",
        "Configurazione granulare (1 settimana, 1 giorno, 1 ora prima)",
        "Diversi metodi per diversi alert (email + webhook)",
        "Tracciabilità stato per ogni singolo alert"
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(v, normal_style)) for v in vantaggi],
        bulletType='bullet',
        leftIndent=20
    ))
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph("4.2 Campi Mancanti (PRIORITÀ ALTA)", section_style))
    
    campi_add = """
    <b>In Scadenza aggiungere:</b><br/>
    • num_occorrenze: PositiveIntegerField(null=True) - numero massimo di occorrenze<br/>
    • data_scadenza: DateField(null=True) - data prima occorrenza<br/>
    <br/>
    <b>In ScadenzaOccorrenza aggiungere:</b><br/>
    • giornaliera: BooleanField(default=False) - flag per evento all-day<br/>
    <br/>
    <b>Rimuovere da ScadenzaOccorrenza:</b><br/>
    • offset_alert_minuti, alert_config → spostati in ScadenzaAlert
    """
    story.append(Paragraph(campi_add, normal_style))
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph("4.3 Vista Scadenziario (PRIORITÀ MEDIA)", section_style))
    scad_view = """
    Creare una vista dedicata che mostri tutte le occorrenze future raggruppate per giorno,
    evidenziando l'accoppiata Scadenza/Occorrenza con:
    """
    story.append(Paragraph(scad_view, normal_style))
    
    scad_features = [
        "Filtro per range temporale (oggi, questa settimana, questo mese)",
        "Visualizzazione per giorno con tutte le occorrenze",
        "Indicazione degli alert programmati per ogni occorrenza",
        "Link rapidi a scadenza, pratica, fascicolo collegati",
        "Azioni: completa, rinvia, invia alert manualmente"
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(f, normal_style)) for f in scad_features],
        bulletType='bullet',
        leftIndent=20
    ))
    story.append(Spacer(1, 0.4*cm))
    
    story.append(Paragraph("4.4 Miglioramento Template Lista (PRIORITÀ MEDIA)", section_style))
    templ_text = """
    Modificare la home delle scadenze per evidenziare meglio:
    """
    story.append(Paragraph(templ_text, normal_style))
    
    templ_features = [
        "Colonna 'Prossima Occorrenza' con data/ora ben visibile",
        "Colonna 'Alert Programmati' con conteggio",
        "Badge colorati per priorità e stato",
        "Filtri rapidi per stato, priorità, assegnatario",
        "Indicatore visivo per scadenze senza occorrenze future"
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(f, normal_style)) for f in templ_features],
        bulletType='bullet',
        leftIndent=20
    ))
    
    story.append(PageBreak())
    
    # Piano implementazione
    story.append(Paragraph("5. PIANO DI IMPLEMENTAZIONE", subtitle_style))
    
    # Tabella piano
    piano_data = [
        ['Fase', 'Attività', 'Priorità', 'Tempo'],
        ['1', 'Creare modello ScadenzaAlert', 'ALTA', '2h'],
        ['1', 'Creare migration per nuovi campi', 'ALTA', '1h'],
        ['1', 'Migration dati esistenti (offset_alert_minuti → ScadenzaAlert)', 'ALTA', '2h'],
        ['1', 'Aggiornare forms per gestire alert multipli', 'ALTA', '3h'],
        ['1', 'Aggiornare admin per inline alerts', 'ALTA', '1h'],
        ['2', 'Modificare AlertDispatcher per gestire alert multipli', 'ALTA', '2h'],
        ['2', 'Aggiornare services OccurrenceGenerator', 'ALTA', '1h'],
        ['2', 'Test unitari nuova logica alert', 'ALTA', '2h'],
        ['3', 'Creare vista Scadenziario', 'MEDIA', '4h'],
        ['3', 'Creare template scadenziario.html', 'MEDIA', '3h'],
        ['3', 'Aggiornare template home.html', 'MEDIA', '2h'],
        ['3', 'Aggiornare template detail.html per alert multipli', 'MEDIA', '2h'],
        ['4', 'Aggiornare API serializers per ScadenzaAlert', 'MEDIA', '2h'],
        ['4', 'Aggiornare endpoints API', 'MEDIA', '2h'],
        ['4', 'Documentazione modifiche', 'MEDIA', '1h'],
        ['5', 'Test integrazione completi', 'ALTA', '3h'],
        ['5', 'Test con utenti reali', 'MEDIA', '2h'],
    ]
    
    piano_table = Table(piano_data, colWidths=[1.5*cm, 8*cm, 2.5*cm, 2.5*cm])
    piano_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(piano_table)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("Stima Totale: ~35 ore di sviluppo", 
                          ParagraphStyle('Bold', parent=normal_style, fontName='Helvetica-Bold')))
    story.append(Spacer(1, 0.5*cm))
    
    # Riepilogo priorità
    story.append(Paragraph("5.1 Riepilogo per Priorità", section_style))
    
    priorita_data = [
        ['Priorità', 'Attività', 'Motivazione'],
        ['ALTA', 'Modello ScadenzaAlert + Migration', 
         'Risolve limitazione critica degli alert singoli'],
        ['ALTA', 'Nuovi campi (num_occorrenze, data_scadenza, giornaliera)',
         'Allinea il modello ai requisiti desiderati'],
        ['ALTA', 'Aggiornamento logica alert', 
         'Necessario per supportare alert multipli'],
        ['MEDIA', 'Vista Scadenziario',
         'Migliora UX e visibilità occorrenze'],
        ['MEDIA', 'Miglioramento template',
         'Evidenzia accoppiata Scadenza/Occorrenza'],
        ['MEDIA', 'Aggiornamento API',
         'Supporto frontend per nuove funzionalità'],
        ['BASSA', 'Integrazione calendario visuale',
         'Enhancement UI opzionale'],
        ['BASSA', 'Export PDF/Excel',
         'Funzionalità extra per reporting'],
    ]
    
    priorita_table = Table(priorita_data, colWidths=[2.5*cm, 5.5*cm, 7*cm])
    priorita_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5490')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(priorita_table)
    
    story.append(PageBreak())
    
    # Conclusioni
    story.append(Paragraph("6. CONCLUSIONI", subtitle_style))
    
    conclusioni = """
    L'implementazione attuale della gestione scadenze in MyGest copre una buona parte dei 
    requisiti desiderati, ma presenta alcune <b>limitazioni critiche</b> che ne riducono 
    l'efficacia:
    <br/><br/>
    <b>Punti di forza:</b><br/>
    • Architettura solida con separazione Scadenza/Occorrenza<br/>
    • Integrazione con Google Calendar funzionante<br/>
    • Collegamenti M2M con pratiche, fascicoli, documenti<br/>
    • Sistema di logging e audit trail completo<br/>
    • Supporto periodicità multiple con generazione automatica<br/>
    <br/>
    <b>Criticità da risolvere:</b><br/>
    • <b>Alert singolo per occorrenza</b>: limita drasticamente l'utilità del sistema<br/>
    • Campi mancanti che limitano la configurazione<br/>
    • UI non ottimizzata per l'uso quotidiano (manca scadenziario)<br/>
    <br/>
    <b>Raccomandazione:</b><br/>
    Si consiglia di procedere con l'implementazione delle modifiche <b>PRIORITÀ ALTA</b> 
    nel più breve tempo possibile, in particolare la creazione del modello ScadenzaAlert 
    che risolve la limitazione più critica del sistema attuale.
    <br/><br/>
    Le modifiche di priorità MEDIA possono essere implementate in una seconda fase, ma sono
    comunque importanti per rendere il sistema realmente utilizzabile nel quotidiano.
    <br/><br/>
    Con queste implementazioni, MyGest disporrà di un sistema di gestione scadenze completo,
    flessibile e allineato ai requisiti originali del progetto.
    """
    story.append(Paragraph(conclusioni, normal_style))
    story.append(Spacer(1, 1*cm))
    
    # Footer
    footer = f"""
    <para align="center">
    <font size="8" color="grey">
    Documento generato automaticamente il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}<br/>
    MyGest - Sistema di Gestione Integrato
    </font>
    </para>
    """
    story.append(Paragraph(footer, styles['Normal']))
    
    # Genera PDF
    doc.build(story)
    print(f"✓ PDF generato: {filename}")
    return filename

if __name__ == "__main__":
    create_pdf()
