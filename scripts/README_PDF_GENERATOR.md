# Generatore PDF Documentazione UI/UX

## 📄 Descrizione

Script Python che genera automaticamente un documento PDF professionale contenente tutta la documentazione della nuova interfaccia utente di MyGest.

## 🎯 Caratteristiche

- **Copertina professionale** con logo, versione e data
- **Indice interattivo** per navigazione rapida
- **Executive Summary** con metriche chiave
- **Conversione automatica** da Markdown a PDF
- **Stili personalizzati** con colori aziendali
- **Numeri di pagina** e header automatici
- **Tabelle formattate** per dati strutturati
- **Evidenziazione codice** con sfondo grigio
- **Supporto emoji** e icone Unicode

## 📦 Dipendenze

```bash
pip install reportlab markdown beautifulsoup4
```

## 🚀 Utilizzo

### Generazione Standard

```bash
python scripts/generate_pdf_documentation.py
```

Il PDF verrà creato in: `docs/Documentazione_UI_UX_MyGest.pdf`

### Verifica Risultato

```bash
# Dimensione file
ls -lh docs/Documentazione_UI_UX_MyGest.pdf

# Apertura PDF (Linux)
xdg-open docs/Documentazione_UI_UX_MyGest.pdf

# Apertura PDF (macOS)
open docs/Documentazione_UI_UX_MyGest.pdf

# Apertura PDF (Windows)
start docs/Documentazione_UI_UX_MyGest.pdf
```

## 📋 Struttura PDF Generato

1. **Copertina**
   - Titolo e sottotitolo
   - Icone features principali
   - Tabella informazioni versione
   - Footer copyright

2. **Indice**
   - Sezioni numerate
   - Riferimenti pagine

3. **Executive Summary**
   - Panoramica generale
   - Tabella metriche chiave

4. **Sezioni Documentazione**
   - Guida Utente (da `GUIDA_UTENTE_NUOVA_UI.md`)
   - Guida Sviluppatori (da `GUIDA_NUOVE_FUNZIONALITA_UI.md`)
   - Riepilogo Tecnico (da `RIEPILOGO_IMPLEMENTAZIONE_UI.md`)
   - Proposta Strategica (da `PROPOSTA_MIGLIORAMENTO_UI_UX.md`)
   - Quick Start (da `QUICK_START_UI.md`)

## 🎨 Personalizzazione

### Modificare Colori

```python
# In _setup_styles()
textColor=HexColor('#0d47a1')  # Blu principale
textColor=HexColor('#1976d2')  # Blu secondario
backColor=HexColor('#e3f2fd')  # Sfondo chiaro
```

### Aggiungere Sezioni

```python
# In generate()
docs = [
    ('path/to/new_doc.md', 'Titolo Sezione'),
    # ... altre sezioni
]
```

### Modificare Layout

```python
# In __init__()
rightMargin=2*cm,    # Margine destro
leftMargin=2*cm,     # Margine sinistro
topMargin=2.5*cm,    # Margine superiore
bottomMargin=2*cm    # Margine inferiore
```

## 🔧 Funzioni Principali

### `PDFGenerator`

Classe principale per generazione PDF.

**Metodi:**

- `__init__(output_file)` - Inizializza generatore
- `_setup_styles()` - Configura stili personalizzati
- `add_cover_page()` - Crea copertina
- `add_table_of_contents()` - Crea indice
- `add_summary_section()` - Crea executive summary
- `markdown_to_pdf_elements(md_file)` - Converte MD in PDF
- `generate()` - Esegue generazione completa

### Helper Methods

- `_clean_text(text)` - Pulisce testo per PDF
- `_escape_xml(text)` - Escape caratteri speciali
- `_add_page_number(canvas, doc)` - Aggiunge numeri pagina

## 📊 Metriche Output

```
✅ PDF generato: docs/Documentazione_UI_UX_MyGest.pdf
📊 Dimensione: ~70 KB
📄 Pagine: ~55-60
🎨 Formato: A4 (210x297mm)
```

## 🐛 Troubleshooting

### Errore: `Style 'X' already defined`

**Soluzione:** Usa nomi univoci per stili personalizzati:

```python
self.styles.add(ParagraphStyle(name='CustomCode', ...))
```

### Errore: `Module not found: bs4`

**Soluzione:** Installa beautifulsoup4:

```bash
pip install beautifulsoup4
```

### Tabelle tagliate

**Soluzione:** Riduci `colWidths` o usa font più piccolo:

```python
Table(data, colWidths=[4*cm, 3*cm, 3*cm])
```

### Codice troppo lungo

**Soluzione:** Lo script limita automaticamente a 30 righe e 80 caratteri per riga.

## 📝 Note Tecniche

### Encoding

- UTF-8 per tutti i file Markdown
- Supporto emoji Unicode
- Escape automatico caratteri XML

### Performance

- Processamento streaming per file grandi
- Cache stili per performance
- Limite righe codice per evitare overflow

### Compatibilità

- Python 3.8+
- reportlab 3.6+
- markdown 3.3+
- beautifulsoup4 4.9+

## 🔄 Aggiornamenti Futuri

- [ ] Aggiunta immagini/screenshot
- [ ] Link cliccabili (hyperlink)
- [ ] Bookmarks PDF interattivi
- [ ] Generazione TOC automatico da H1/H2
- [ ] Supporto temi colore multipli
- [ ] Export in formato Word (.docx)

## 👤 Autore

Sviluppato con GitHub Copilot AI Assistant per il progetto MyGest.

## 📜 Licenza

© 2025 MyGest - Tutti i diritti riservati
