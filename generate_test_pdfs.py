#!/usr/bin/env python
"""
Script per generare PDF di test realistici per il sistema di classificazione AI
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

OUTPUT_DIR = "/tmp/test_docs_pdf"

def create_cedolino_pdf():
    """Crea un PDF che simula un cedolino paga"""
    filepath = os.path.join(OUTPUT_DIR, "cedolino_rossi_mario_202401.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Intestazione
    title = Paragraph("<b>CEDOLINO PAGA - GENNAIO 2024</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # Dati dipendente
    story.append(Paragraph("<b>AZIENDA:</b> Studio Associato Rossi & Partners", styles['Normal']))
    story.append(Paragraph("<b>Dipendente:</b> Rossi Mario", styles['Normal']))
    story.append(Paragraph("<b>Codice Fiscale:</b> RSSMRA80A01H501U", styles['Normal']))
    story.append(Paragraph("<b>Matricola:</b> 12345", styles['Normal']))
    story.append(Paragraph("<b>Periodo:</b> Gennaio 2024", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Tabella retribuzione
    data = [
        ['DESCRIZIONE', 'IMPORTO'],
        ['Retribuzione Base', '€ 1.800,00'],
        ['Superminimo', '€ 300,00'],
        ['Scatti Anzianità', '€ 200,00'],
        ['Premio Produttività', '€ 200,00'],
        ['TOTALE RETRIBUZIONE LORDA', '€ 2.500,00'],
        ['', ''],
        ['TRATTENUTE', ''],
        ['Contributi INPS (9,19%)', '€ 229,75'],
        ['Contributi INPS (0,30%)', '€ 7,50'],
        ['INAIL', '€ 5,00'],
        ['IRPEF', '€ 400,00'],
        ['Addizionale Regionale', '€ 25,00'],
        ['Addizionale Comunale', '€ 15,00'],
        ['TOTALE TRATTENUTE', '€ 682,25'],
        ['', ''],
        ['<b>NETTO DA PAGARE</b>', '<b>€ 1.817,75</b>'],
    ]
    
    table = Table(data, colWidths=[12*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    print(f"✓ Creato: {filepath}")


def create_f24_pdf():
    """Crea un PDF che simula un modello F24"""
    filepath = os.path.join(OUTPUT_DIR, "F24_202401_rossi_mario.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Intestazione
    title = Paragraph("<b>MODELLO F24 - AGENZIA DELLE ENTRATE</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("<b>Data compilazione:</b> 16/01/2024", styles['Normal']))
    story.append(Paragraph("<b>Codice Fiscale:</b> RSSMRA80A01H501U", styles['Normal']))
    story.append(Paragraph("<b>Contribuente:</b> ROSSI MARIO", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Sezione Erario
    story.append(Paragraph("<b>SEZIONE ERARIO</b>", styles['Heading2']))
    data_erario = [
        ['CODICE TRIBUTO', 'ANNO RIF.', 'IMPORTO A DEBITO', 'IMPORTO A CREDITO'],
        ['1001 - IRPEF', '2023', '€ 1.500,00', ''],
        ['1040 - IRAP', '2023', '€ 350,00', ''],
        ['3800 - IVA mensile', '12/2023', '€ 800,00', ''],
    ]
    
    table_erario = Table(data_erario, colWidths=[5*cm, 3*cm, 4*cm, 4*cm])
    table_erario.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table_erario)
    story.append(Spacer(1, 0.5*cm))
    
    # Sezione INPS
    story.append(Paragraph("<b>SEZIONE INPS</b>", styles['Heading2']))
    data_inps = [
        ['CODICE SEDE', 'CAUSALE', 'MATRICOLA', 'PERIODO DAL', 'AL', 'IMPORTO'],
        ['0100', 'DM10', '1234567890', '01/12/2023', '31/12/2023', '€ 650,00'],
    ]
    
    table_inps = Table(data_inps, colWidths=[2.5*cm, 2.5*cm, 3*cm, 3*cm, 3*cm, 3*cm])
    table_inps.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table_inps)
    story.append(Spacer(1, 0.5*cm))
    
    # Totale
    story.append(Paragraph("<b>TOTALE F24: € 3.300,00</b>", styles['Heading2']))
    
    doc.build(story)
    print(f"✓ Creato: {filepath}")


def create_fattura_pdf():
    """Crea un PDF che simula una fattura"""
    filepath = os.path.join(OUTPUT_DIR, "fattura_2024_00123.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Intestazione
    title = Paragraph("<b>FATTURA N. 2024/00123</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    # Dati emittente
    story.append(Paragraph("<b>STUDIO ASSOCIATO ROSSI & PARTNERS</b>", styles['Heading2']))
    story.append(Paragraph("Via Roma, 123 - 00100 Roma (RM)", styles['Normal']))
    story.append(Paragraph("P.IVA: 12345678901", styles['Normal']))
    story.append(Paragraph("Codice Fiscale: 12345678901", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Dati cliente
    story.append(Paragraph("<b>CLIENTE:</b>", styles['Heading3']))
    story.append(Paragraph("Acme S.r.l.", styles['Normal']))
    story.append(Paragraph("Via Milano, 456 - 20100 Milano (MI)", styles['Normal']))
    story.append(Paragraph("P.IVA: 09876543210", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Dati fattura
    story.append(Paragraph("<b>Data:</b> 15/01/2024", styles['Normal']))
    story.append(Paragraph("<b>Scadenza:</b> 14/02/2024", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Righe fattura
    story.append(Paragraph("<b>DETTAGLIO PRESTAZIONI</b>", styles['Heading3']))
    data = [
        ['DESCRIZIONE', 'Q.TÀ', 'PREZZO UNIT.', 'IMPORTO'],
        ['Consulenza fiscale periodo Dicembre 2023', '1', '€ 500,00', '€ 500,00'],
        ['Elaborazione dichiarazioni IVA', '1', '€ 300,00', '€ 300,00'],
        ['Consulenza straordinaria riorganizzazione', '4h', '€ 75,00', '€ 300,00'],
        ['', '', '<b>IMPONIBILE</b>', '<b>€ 1.100,00</b>'],
        ['', '', 'IVA 22%', '€ 242,00'],
        ['', '', '<b>TOTALE FATTURA</b>', '<b>€ 1.342,00</b>'],
    ]
    
    table = Table(data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, 3), 1, colors.black),
        ('LINEABOVE', (0, -2), (-1, -2), 2, colors.black),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("<i>Pagamento: Bonifico bancario entro 30gg data fattura</i>", styles['Normal']))
    story.append(Paragraph("<i>IBAN: IT60X0542811101000000123456</i>", styles['Normal']))
    
    doc.build(story)
    print(f"✓ Creato: {filepath}")


def create_bilancio_pdf():
    """Crea un PDF che simula un bilancio aziendale"""
    filepath = os.path.join(OUTPUT_DIR, "bilancio_acme_srl_2023.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Intestazione
    title = Paragraph("<b>BILANCIO D'ESERCIZIO 2023</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("<b>ACME S.R.L.</b>", styles['Heading2']))
    story.append(Paragraph("Capitale sociale: € 10.000,00 i.v.", styles['Normal']))
    story.append(Paragraph("Sede legale: Via Milano, 456 - 20100 Milano (MI)", styles['Normal']))
    story.append(Paragraph("P.IVA e Codice Fiscale: 09876543210", styles['Normal']))
    story.append(Paragraph("Registro Imprese Milano n. 09876543210", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Stato Patrimoniale
    story.append(Paragraph("<b>STATO PATRIMONIALE AL 31/12/2023</b>", styles['Heading2']))
    story.append(Spacer(1, 0.3*cm))
    
    data_attivo = [
        ['ATTIVO', '31/12/2023', '31/12/2022'],
        ['<b>A) CREDITI VERSO SOCI</b>', '0', '0'],
        ['<b>B) IMMOBILIZZAZIONI</b>', '', ''],
        ['I - Immobilizzazioni immateriali', '15.000', '20.000'],
        ['II - Immobilizzazioni materiali', '85.000', '95.000'],
        ['<b>Totale immobilizzazioni (B)</b>', '<b>100.000</b>', '<b>115.000</b>'],
        ['<b>C) ATTIVO CIRCOLANTE</b>', '', ''],
        ['I - Rimanenze', '45.000', '40.000'],
        ['II - Crediti', '120.000', '110.000'],
        ['IV - Disponibilità liquide', '35.000', '25.000'],
        ['<b>Totale attivo circolante (C)</b>', '<b>200.000</b>', '<b>175.000</b>'],
        ['<b>D) RATEI E RISCONTI</b>', '5.000', '3.000'],
        ['', '', ''],
        ['<b>TOTALE ATTIVO</b>', '<b>€ 305.000</b>', '<b>€ 293.000</b>'],
    ]
    
    table_attivo = Table(data_attivo, colWidths=[10*cm, 3*cm, 3*cm])
    table_attivo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
    ]))
    
    story.append(table_attivo)
    
    doc.build(story)
    print(f"✓ Creato: {filepath}")


def create_dichiarazione_pdf():
    """Crea un PDF che simula una dichiarazione dei redditi"""
    filepath = os.path.join(OUTPUT_DIR, "dichiarazione_redditi_2023_rossi_mario.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Intestazione
    title = Paragraph("<b>MODELLO 730/2024</b>", styles['Title'])
    story.append(title)
    story.append(Paragraph("<b>DICHIARAZIONE DEI REDDITI - ANNO 2023</b>", styles['Heading2']))
    story.append(Spacer(1, 0.5*cm))
    
    # Dati contribuente
    story.append(Paragraph("<b>DATI ANAGRAFICI</b>", styles['Heading3']))
    story.append(Paragraph("Cognome e Nome: ROSSI MARIO", styles['Normal']))
    story.append(Paragraph("Codice Fiscale: RSSMRA80A01H501U", styles['Normal']))
    story.append(Paragraph("Data di nascita: 01/01/1980", styles['Normal']))
    story.append(Paragraph("Comune di nascita: Roma (RM)", styles['Normal']))
    story.append(Paragraph("Residenza: Via Roma, 123 - 00100 Roma (RM)", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Redditi
    story.append(Paragraph("<b>QUADRO C - REDDITI DI LAVORO DIPENDENTE</b>", styles['Heading3']))
    data_redditi = [
        ['DESCRIZIONE', 'IMPORTO'],
        ['Reddito da lavoro dipendente', '€ 35.000,00'],
        ['Ritenute IRPEF', '€ 8.500,00'],
        ['Contributi previdenziali', '€ 3.200,00'],
    ]
    
    table = Table(data_redditi, colWidths=[10*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))
    
    # Detrazioni
    story.append(Paragraph("<b>ONERI DEDUCIBILI E DETRAIBILI</b>", styles['Heading3']))
    data_oneri = [
        ['TIPOLOGIA', 'IMPORTO'],
        ['Spese sanitarie', '€ 1.200,00'],
        ['Interessi mutuo prima casa', '€ 2.500,00'],
        ['Contributi previdenziali', '€ 800,00'],
        ['Spese istruzione', '€ 600,00'],
    ]
    
    table2 = Table(data_oneri, colWidths=[10*cm, 4*cm])
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table2)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("<b>RISULTATO DELLA DICHIARAZIONE</b>", styles['Heading3']))
    story.append(Paragraph("<b>Imposta lorda: € 8.500,00</b>", styles['Normal']))
    story.append(Paragraph("<b>Detrazioni: € 1.200,00</b>", styles['Normal']))
    story.append(Paragraph("<b>Imposta netta: € 7.300,00</b>", styles['Normal']))
    story.append(Paragraph("<b style='color: green'>A CREDITO: € 1.200,00</b>", styles['Normal']))
    
    doc.build(story)
    print(f"✓ Creato: {filepath}")


if __name__ == '__main__':
    # Crea directory output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Creazione PDF di test in: {OUTPUT_DIR}\n")
    
    # Genera tutti i PDF
    create_cedolino_pdf()
    create_f24_pdf()
    create_fattura_pdf()
    create_bilancio_pdf()
    create_dichiarazione_pdf()
    
    print(f"\n✅ Creati 5 PDF di test in {OUTPUT_DIR}")
    print("\nElenco file:")
    for f in os.listdir(OUTPUT_DIR):
        if f.endswith('.pdf'):
            size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
            print(f"  - {f} ({size} bytes)")
