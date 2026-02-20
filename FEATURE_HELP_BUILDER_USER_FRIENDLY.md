# 📚 Sistema Help Documenti - Gestione User-Friendly

## 🎯 Panoramica

Sistema combinato per la gestione dell'help dei tipi documento che bilancia:
- **Auto-generazione** per sezioni tecniche (zero manutenzione)
- **User-friendly editing** per sezioni discorsive (Django Admin + CLI Wizard)
- **Validazione automatica** della struttura JSON

---

## 🏗️ Architettura

### Componenti

```
documenti/
├── help_builder.py          # 🤖 Generatore automatico sezioni tecniche
├── help_forms.py            # 📝 Form Django Admin user-friendly
├── signals.py               # ⚡ Auto-aggiornamento help_data
└── management/commands/
    └── configure_help_wizard.py  # 🧙‍♂️ Wizard CLI interattivo
```

### Sezioni Help_Data

#### ✅ **Sezioni AUTO-GENERATE** (da sistema)
Queste sezioni vengono **generate automaticamente** e **non devono essere modificate manualmente**:

1. **`attributi_dinamici`**
   - Fonte: `AttributoDefinizione` model
   - Aggiornamento: Automatico quando aggiungi/modifichi/elimini attributi
   - Contiene: lista attributi con tipo, descrizione, obbligatorietà, esempi

2. **`pattern_codice`**
   - Fonte: `DocumentiTipo.pattern_codice`
   - Contiene: pattern, spiegazione, esempi, placeholder disponibili

3. **`archiviazione`**
   - Fonte: `DocumentiTipo.nome_file_pattern` + logica NAS
   - Contiene: percorso tipo, pattern nome file, esempi completi

4. **`campi_obbligatori`**
   - Fonte: `AttributoDefinizione.required` + campi base Documento
   - Contiene: campi sempre obbligatori e condizionali

#### 📝 **Sezioni MANUALI** (da utente)
Queste sezioni richiedono input manuale via Admin o Wizard:

5. **`descrizione_breve`** - Panoramica tipo documento
6. **`quando_usare`** - Casi d'uso e situazioni da evitare
7. **`guida_compilazione`** - Step-by-step compilazione
8. **`relazione_fascicoli`** - Come collegare i fascicoli
9. **`workflow`** - Stati e azioni documento
10. **`note_speciali`** - Attenzioni, suggerimenti, vincoli
11. **`faq`** - Domande frequenti
12. **`risorse_correlate`** - Link e documenti correlati

---

## 🛠️ Utilizzo

### Metodo 1: Django Admin (Raccomandato per utenti non tecnici)

#### Accesso
1. Vai su: `/admin/documenti/documentitipo/`
2. Seleziona un tipo documento esistente o creane uno nuovo
3. Clicca su "Modifica"

#### Interfaccia
Il form è organizzato in **fieldset collassabili** con colori distintivi:

- **🔵 Help - Descrizione** (blu)
- **🟣 Help - Quando Usare** (viola)
- **🟢 Help - Relazione Fascicoli** (verde)
- **🟠 Help - Workflow** (arancione)
- **🔴 Help - Note Speciali** (rosa)
- **🟣 Help - FAQ** (viola scuro)

#### Compilazione Campi

**Campi Textarea multilinea**:
```
Campo: "Quando Usare - Casi d'uso"
---
Gestione cedolini mensili dipendenti
Archiviazione buste paga
Adempimenti fiscali mensili
```

**Campo FAQ (JSON)**:
```json
[
  {
    "domanda": "Come faccio a caricare più cedolini insieme?",
    "risposta": "Usa la funzione 'Importa ZIP' dal menu Documenti"
  },
  {
    "domanda": "Posso modificare il dipendente dopo il salvataggio?",
    "risposta": "Sì, ma solo prima della protocollazione"
  }
]
```

#### Validazione Real-Time
- ✅ Il campo FAQ JSON viene validato automaticamente
- ✅ Se la struttura è errata, appare un alert
- ✅ Badge colorati indicano sezioni auto/manuali

#### Salvataggio
Al salvataggio:
1. **Sezioni discorsive** → Salvate dal form
2. **Sezioni tecniche** → Rigenerate automaticamente
3. **Validazione** → Controllo struttura JSON
4. **Messaggio conferma** → "Help salvato con successo. Sezioni tecniche rigenerate."

---

### Metodo 2: Wizard CLI (Raccomandato per setup iniziale)

#### Comando Base
```bash
# Setup completo interattivo
python manage.py configure_help_wizard

# Setup per tipo specifico
python manage.py configure_help_wizard --tipo CED

# Solo rigenerazione sezioni tecniche
python manage.py configure_help_wizard --tipo CED --rebuild-technical
```

#### Flusso Wizard

**1. Selezione Tipo**
```
Tipi documento disponibili:

  1. [✓] CED - Cedolini
  2. [✗] FAT - Fatture
  3. [✗] CNT - Contratti

Seleziona numero (1-3): 1
```

**2. Sezione Descrizione**
```
=== SEZIONE 1: DESCRIZIONE BREVE ===

Inserisci una descrizione breve del tipo documento
(max 2-3 righe, panoramica generale)

Scrivi la descrizione (riga vuota per terminare):
I cedolini sono documenti mensili che attestano...
il pagamento delle retribuzioni ai dipendenti.
<INVIO>
```

**3. Sezione Quando Usare**
```
=== SEZIONE 2: QUANDO USARE ===

📌 Quando usare questo tipo documento?
Elenca i casi d'uso appropriati (vuoto per finire):

  1. Gestione buste paga mensili
  2. Archiviazione cedolini dipendenti
  3. <INVIO>

🚫 Quando NON usare (situazioni da evitare):

  1. Per documenti diversi dalle buste paga
  2. Per contratti di assunzione
  3. <INVIO>
```

**4. Altre Sezioni**
- Guida compilazione (opzionale)
- Relazione fascicoli
- Workflow
- Note speciali
- FAQ
- Risorse correlate

**5. Auto-generazione**
```
🤖 Generazione automatica sezioni tecniche...

✓ CONFIGURAZIONE COMPLETATA CON SUCCESSO!

📊 RIEPILOGO CONFIGURAZIONE

Sezioni configurate:
  📝 descrizione_breve
  📝 quando_usare
  📝 workflow
  🤖 attributi_dinamici
  🤖 pattern_codice
  🤖 archiviazione
  🤖 campi_obbligatori
```

---

### Metodo 3: Rigenerazione Automatica

Le sezioni tecniche vengono rigenerate **automaticamente** quando:

#### Trigger Automatici

**1. Creazione nuovo DocumentiTipo**
```python
tipo = DocumentiTipo.objects.create(
    codice='FAT',
    nome='Fatture',
    pattern_codice='{CLI}-FAT-{ANNO}-{SEQ:03d}'
)
# → help_data inizializzato automaticamente con sezioni tecniche
```

**2. Modifica AttributoDefinizione**
```python
# Aggiungi nuovo attributo
AttributoDefinizione.objects.create(
    tipo_documento=tipo_ced,
    codice='matricola',
    nome='Matricola Dipendente',
    tipo_dato='str',
    required=True
)
# → attributi_dinamici in help_data rigenerato automaticamente
```

**3. Eliminazione AttributoDefinizione**
```python
attr.delete()
# → attributi_dinamici in help_data rigenerato automaticamente
```

**4. Salvataggio da Admin Form**
```python
# Ogni salvataggio da Django Admin rigenera sezioni tecniche
```

#### Rigenerazione Manuale
```bash
# Solo sezioni tecniche (preserva quelle discorsive)
python manage.py configure_help_wizard --tipo CED --rebuild-technical
```

---

## 🎨 Personalizzazione UI Admin

### File Statici Inclusi

**CSS** (`static/admin/css/help_admin.css`):
- Colori distintivi per ogni sezione
- Textarea monospace per JSON
- Badge "🤖 AUTO" e "📝 MANUALE"
- Warning box per help_data raw

**JavaScript** (`static/admin/js/help_admin.js`):
- Validazione FAQ JSON real-time
- Badge automatici su fieldset
- Helper per liste multilinea
- Link wizard CLI con copia comando

### Estensione Admin Media
```python
class DocumentiTipoAdmin(admin.ModelAdmin):
    class Media:
        css = {'all': ('admin/css/help_admin.css',)}
        js = ('admin/js/help_admin.js',)
```

---

## 🔍 Validazione JSON

### JSON Schema
File: `static/schemas/help_data_schema.json`

Definisce la struttura valida per `help_data`:
- Tipi di dato richiesti
- Campi obbligatori/opzionali
- Formato array/object
- Validazione nested structures

### Validazione Form
```python
# In HelpDataAdminForm.clean()
if faq_json:
    if not isinstance(faq_json, list):
        raise ValidationError("FAQ deve essere una lista")
    
    for item in faq_json:
        if 'domanda' not in item or 'risposta' not in item:
            raise ValidationError("Ogni FAQ deve avere domanda e risposta")
```

---

## 🚀 Esempi Pratici

### Esempio 1: Setup Nuovo Tipo Documento

**Scenario**: Creare tipo "Contratti" con help completo

**Via Admin**:
1. `/admin/documenti/documentitipo/add/`
2. Codice: `CNT`, Nome: `Contratti`
3. Pattern codice: `{CLI}-CNT-{ANNO}-{SEQ:03d}`
4. Aggiungi attributi (es. `tipo_contratto`, `scadenza`)
5. Compila sezioni help discorsive
6. Salva → sezioni tecniche generate automaticamente

**Via Wizard**:
```bash
python manage.py configure_help_wizard --tipo CNT
```

### Esempio 2: Aggiungere Attributo a Tipo Esistente

**Scenario**: Aggiungere campo "matricola" ai cedolini

**Passo 1 - Aggiungi AttributoDefinizione**:
```python
# Via Admin o shell
AttributoDefinizione.objects.create(
    tipo_documento=tipo_ced,
    codice='matricola',
    nome='Matricola Dipendente',
    tipo_dato='str',
    required=False,
    help_text='Matricola aziendale del dipendente',
    ordine=6
)
```

**Passo 2 - Verifica Auto-Aggiornamento**:
```bash
# L'attributo appare automaticamente in:
# - help_data['attributi_dinamici']['disponibili']
# - Frontend /help/documenti/CED
# - Export PDF help
```

### Esempio 3: Modificare Solo Sezioni Discorsive

**Scenario**: Aggiornare FAQ senza toccare sezioni tecniche

**Via Admin**:
1. Vai su tipo documento
2. Scroll a "Help - FAQ"
3. Modifica JSON FAQ
4. Salva → sezioni tecniche preservate, FAQ aggiornate

**Via Wizard**:
```bash
python manage.py configure_help_wizard --tipo CED
# Naviga fino a FAQ, aggiorna, le altre rimangono invariate
```

### Esempio 4: Rigenerare Solo Sezioni Tecniche

**Scenario**: Hai modificato il pattern_codice e vuoi aggiornare l'help

```bash
python manage.py configure_help_wizard --tipo CED --rebuild-technical

# Output:
# === RIGENERAZIONE SEZIONI TECNICHE ===
# ✓ Sezioni tecniche rigenerate con successo!
# Sezioni aggiornate:
#   - attributi_dinamici
#   - pattern_codice
#   - archiviazione
#   - campi_obbligatori
```

---

## 📊 Monitoraggio e Debug

### Log Django
I signal loggano tutte le operazioni:

```python
logger.info("Help_data rigenerato automaticamente per CED dopo modifica attributo matricola")
logger.info("Help_data inizializzato automaticamente per nuovo tipo FAT")
```

### Verifica Admin
Nella list view dei tipi documento:
- Colonna **"Help configurato"** (✓/✗)
- Indica se help_data è presente e popolato

### Ispezione Help_Data
```bash
python manage.py shell
```

```python
from documenti.models import DocumentiTipo
import json

tipo = DocumentiTipo.objects.get(codice='CED')

# Vedi tutte le sezioni
print(json.dumps(list(tipo.help_data.keys()), indent=2))

# Vedi sezione specifica
print(json.dumps(tipo.help_data['attributi_dinamici'], indent=2))
```

---

## 🔧 Troubleshooting

### Problema: "Sezioni tecniche non si aggiornano"

**Soluzione**:
```bash
# Forza rigenerazione
python manage.py configure_help_wizard --tipo <CODICE> --rebuild-technical
```

### Problema: "FAQ JSON non valido"

**Sintomo**: Alert "JSON non valido" al blur del campo

**Soluzione**:
1. Verifica sintassi JSON (virgole, apici)
2. Usa un validatore online (jsonlint.com)
3. Struttura corretta:
```json
[
  {
    "domanda": "Testo domanda",
    "risposta": "Testo risposta"
  }
]
```

### Problema: "Attributi non appaiono in help_data"

**Causa**: Signal non attivato o errore

**Soluzione**:
1. Controlla log Django
2. Verifica che `documenti/apps.py` carichi i signal:
```python
def ready(self):
    import documenti.signals
```
3. Forza rigenerazione manuale

### Problema: "Help_data vuoto per nuovo tipo"

**Causa**: Signal `post_save` non eseguito

**Soluzione**:
```python
from documenti.models import DocumentiTipo
from documenti.help_builder import HelpDataBuilder

tipo = DocumentiTipo.objects.get(codice='FAT')
builder = HelpDataBuilder(tipo)
tipo.help_data = builder.build_all_technical_sections()
tipo.save()
```

---

## 🎓 Best Practices

### ✅ DO (Fai)

1. **Usa Admin per modifiche rapide**
   - Ideale per aggiornare descrizioni, FAQ, note

2. **Usa Wizard per setup iniziale**
   - Più veloce per configurare tutto da zero

3. **Lascia sezioni tecniche al sistema**
   - Non modificare manualmente `attributi_dinamici`, `pattern_codice`, etc.

4. **Valida sempre il JSON**
   - Usa il validatore real-time nel form

5. **Documenta workflow completo**
   - Stati, azioni, transizioni

### ❌ DON'T (Non fare)

1. **Non modificare help_data raw**
   - Usa i campi del form o il wizard

2. **Non duplicare informazioni**
   - Le sezioni tecniche sono auto-generate

3. **Non usare JSON complesso per FAQ**
   - Mantieni struttura semplice domanda/risposta

4. **Non bypassare il form**
   - Sempre salvare tramite Admin o wizard

---

## 📚 Riferimenti

### File Chiave
- `documenti/help_builder.py` - Logica auto-generazione
- `documenti/help_forms.py` - Form Admin
- `documenti/signals.py` - Auto-aggiornamento
- `documenti/management/commands/configure_help_wizard.py` - Wizard CLI

### TypeScript Types (Frontend)
- `frontend/src/types/help.ts` - Interfacce TypeScript
- `frontend/src/utils/pdfExport.ts` - Export PDF

### Documentazione Correlata
- `FEATURE_EXPORT_HELP_PDF.md` - Export help in PDF
- `.github/copilot-instructions.md` - Convenzioni progetto

---

## 🔄 Upgrade da Vecchio Sistema

Se hai già tipi documento con `help_data` manuale:

### Migrazione Automatica
```bash
# Per ogni tipo documento
python manage.py shell
```

```python
from documenti.models import DocumentiTipo
from documenti.help_builder import rebuild_help_technical_sections

for tipo in DocumentiTipo.objects.all():
    if tipo.help_data:
        # Preserva sezioni discorsive, rigenera tecniche
        tipo.help_data = rebuild_help_technical_sections(tipo)
        tipo.save()
        print(f"✓ {tipo.codice} aggiornato")
```

### Verifica Post-Migrazione
```bash
# Controlla che tutte le sezioni siano presenti
python manage.py shell
```

```python
from documenti.models import DocumentiTipo

required_keys = [
    'attributi_dinamici', 'pattern_codice', 
    'archiviazione', 'campi_obbligatori'
]

for tipo in DocumentiTipo.objects.filter(help_data__isnull=False):
    missing = [k for k in required_keys if k not in tipo.help_data]
    if missing:
        print(f"❌ {tipo.codice}: mancano {missing}")
    else:
        print(f"✓ {tipo.codice}: completo")
```

---

## 📞 Supporto

Per domande o problemi:
1. Consulta questa guida
2. Controlla i log Django
3. Usa il wizard CLI in modalità verbose
4. Verifica la struttura JSON con lo schema

---

**Versione**: 1.0  
**Data**: Febbraio 2026  
**Autore**: Sistema MyGest
