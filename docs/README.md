# Guide Documentation - MyGest

Questa directory contiene la documentazione operativa di MyGest in formato Markdown, HTML e PDF.

## 📚 Guide Disponibili

### Guida Deployment e Sincronizzazione

**File**: `GUIDA_DEPLOYMENT_SYNC.md`

Guida completa per:
- Deployment applicazione (automatico GitHub Actions + manuale SSH)
- Sincronizzazione database dev↔prod
- Gestione archivio documentale su NAS
- Backup cloud con rclone
- Troubleshooting e FAQ

**Formati disponibili**:
- **Markdown sorgente**: `GUIDA_DEPLOYMENT_SYNC.md` (106 KB)
- **HTML responsivo**: `GUIDA_DEPLOYMENT_SYNC.html` (generato automaticamente)
- **PDF stampa**: `GUIDA_DEPLOYMENT_SYNC.pdf` (160 KB, generato automaticamente)

**Accesso online**:
- HTML: `https://mygest.sandro.cloud/guide/deployment.html`
- PDF: `https://mygest.sandro.cloud/guide/deployment.pdf`
- Help integrato: `https://mygest.sandro.cloud/help/guida-deployment/`

## 🔄 Rigenerare HTML e PDF

Quando modifichi il file Markdown sorgente, rigenera HTML e PDF:

```bash
# Attiva virtualenv
cd /home/sandro/mygest
source venv/bin/activate

# Rigenera guida
python docs/generate_guide.py
```

**Output**:
```
============================================================
  MyGest - Guida Deployment Generator
============================================================

📖 Reading GUIDA_DEPLOYMENT_SYNC.md...
🔄 Converting Markdown to HTML...
💾 Saving HTML to GUIDA_DEPLOYMENT_SYNC.html...
✅ HTML saved: /home/sandro/mygest/docs/GUIDA_DEPLOYMENT_SYNC.html
📄 Generating PDF...
✅ PDF saved: /home/sandro/mygest/docs/GUIDA_DEPLOYMENT_SYNC.pdf
📊 PDF size: 0.16 MB

============================================================
✅ Generation completed successfully!
============================================================
```

## 🛠️ Dipendenze

Per generare HTML e PDF servono:

```bash
pip install markdown weasyprint pygments
```

**Già incluse in**: `requirements.txt`

## 📝 Workflow Modifica Guide

1. **Modifica Markdown**:
   ```bash
   nano docs/GUIDA_DEPLOYMENT_SYNC.md
   # Oppure usa editor preferito
   ```

2. **Rigenera formati**:
   ```bash
   python docs/generate_guide.py
   ```

3. **Verifica locale**:
   ```bash
   # Apri HTML in browser
   xdg-open docs/GUIDA_DEPLOYMENT_SYNC.html
   
   # Oppure server dev
   python manage.py runserver
   # Vai su http://localhost:8000/guide/deployment.html
   ```

4. **Commit e deploy**:
   ```bash
   git add docs/
   git commit -m "docs: aggiorna guida deployment"
   git push origin main
   ```

## 🎨 Personalizzazione Stile

### HTML

Modifica CSS in `docs/generate_guide.py`:
- Cerca sezione `css = """...."""`
- Personalizza colori, font, layout
- Rigenera con `python docs/generate_guide.py`

### PDF

Modifica CSS PDF in `docs/generate_guide.py`:
- Cerca sezione `pdf_css = CSS(string='''...''')`
- Personalizza header/footer, margini, page breaks
- Rigenera

## 📐 Struttura Markdown

La guida usa **Markdown esteso** con:

- ✅ **Tables**: `| Col1 | Col2 |`
- ✅ **Code blocks**: ` ```bash ... ``` `
- ✅ **Syntax highlighting**: Pygments
- ✅ **Auto-TOC**: Generato automaticamente
- ✅ **Links**: Interni `[testo](#sezione)` ed esterni
- ✅ **Emoji**: 📝 🚀 ✅ ❌ ⚠️

## 🚀 Creare Nuove Guide

### 1. Crea Markdown

```bash
nano docs/NUOVA_GUIDA.md
```

### 2. Aggiorna generator script

Modifica `docs/generate_guide.py`:

```python
# Aggiungi file input/output
MD_FILE = DOCS_DIR / "NUOVA_GUIDA.md"
HTML_FILE = DOCS_DIR / "NUOVA_GUIDA.html"
PDF_FILE = DOCS_DIR / "NUOVA_GUIDA.pdf"
```

### 3. Crea view Django

In `mygest/views.py`:

```python
def serve_nuova_guida_html(request):
    html_path = os.path.join(settings.BASE_DIR, 'docs', 'NUOVA_GUIDA.html')
    if not os.path.exists(html_path):
        raise Http404("Guida non trovata")
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/html')
```

### 4. Aggiungi URL

In `mygest/urls.py`:

```python
path("guide/nuova-guida.html", serve_nuova_guida_html, name="guide-nuova"),
```

### 5. Aggiungi al Help

In `mygest/views.py` → `HELP_TOPICS`:

```python
"nuova-guida": {
    "name": "Nuova Guida",
    "summary": "Descrizione breve",
    "template": "help/nuova_guida.html",
    "order": 3,
},
```

Crea template `templates/help/nuova_guida.html` (usa `guida_deployment.html` come base).

## 📊 Statistiche Guida Deployment

- **Markdown sorgente**: ~106 KB, 1100+ righe
- **HTML generato**: ~200 KB (con CSS inline)
- **PDF generato**: ~160 KB, 35 pagine A4
- **Sezioni principali**: 7 (intro, deploy, sync, NAS, troubleshooting, FAQ, ref)
- **Comandi esempio**: 80+ snippet bash/Python
- **Tabelle**: 5 (caratteristiche, errori comuni, etc.)

## 🔗 Link Utili

- **Django Templates**: `templates/help/*.html`
- **URL routing**: `mygest/urls.py`
- **View help**: `mygest/views.py` (funzioni `help_*` e `serve_*_guide_*`)
- **Markdown extensions**: https://python-markdown.github.io/extensions/
- **WeasyPrint docs**: https://doc.courtbouillon.org/weasyprint/

## 📞 Supporto

Per problemi con generazione guide:

1. Verificare dipendenze: `pip list | grep -E "markdown|weasyprint|pygments"`
2. Test generazione: `python docs/generate_guide.py`
3. Log errori: Salvare output script
4. Issue GitHub: https://github.com/sandro6917/mygest/issues

---

**MyGest Development Team** - Febbraio 2026
