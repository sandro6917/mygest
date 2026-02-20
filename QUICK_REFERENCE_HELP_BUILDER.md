# 🚀 QUICK REFERENCE - Sistema Help Builder

## Comandi Rapidi

### Wizard CLI
```bash
# Setup completo interattivo
python manage.py configure_help_wizard

# Setup tipo specifico
python manage.py configure_help_wizard --tipo CED

# Solo sezioni tecniche (veloce!)
python manage.py configure_help_wizard --tipo CED --rebuild-technical

# Help comando
python manage.py configure_help_wizard --help
```

### Django Admin
```
URL: /admin/documenti/documentitipo/

Sezioni form:
├─ 🔵 Help - Descrizione
├─ 🟣 Help - Quando Usare  
├─ 🟢 Help - Relazione Fascicoli
├─ 🟠 Help - Workflow
├─ 🔴 Help - Note Speciali
└─ 🟣 Help - FAQ (JSON)

Badge:
🤖 AUTO = Generato automaticamente
📝 MANUALE = Richiede input utente
```

## Sezioni Help_Data

### ✅ AUTO-GENERATE (Non toccare!)
- `attributi_dinamici` → da AttributoDefinizione
- `pattern_codice` → da pattern_codice field
- `archiviazione` → da nome_file_pattern + NAS
- `campi_obbligatori` → da required fields

### 📝 MANUALE (Compila tu!)
- `descrizione_breve` → Textarea
- `quando_usare` → 2 textarea (casi + non usare)
- `guida_compilazione` → Wizard step
- `relazione_fascicoli` → Descrizione + best practices
- `workflow` → Stati + azioni
- `note_speciali` → 3 textarea (attenzioni + suggerimenti + vincoli)
- `faq` → JSON array
- `risorse_correlate` → Collegamenti

## Esempi FAQ JSON

### Formato Corretto
```json
[
  {
    "domanda": "Come faccio a...?",
    "risposta": "Devi fare così..."
  },
  {
    "domanda": "Posso modificare...?",
    "risposta": "Sì, ma solo se..."
  }
]
```

### ❌ Errori Comuni
```json
// SBAGLIATO - Non è un array
{
  "domanda": "...",
  "risposta": "..."
}

// SBAGLIATO - Campi mancanti
[
  {
    "domanda": "Solo domanda"
  }
]

// SBAGLIATO - Virgola finale
[
  {"domanda": "...", "risposta": "..."},
]
```

## Workflow Tipico

### Nuovo Tipo Documento
```
1. Admin → Crea DocumentiTipo
2. Aggiungi AttributoDefinizione (inline)
3. Compila sezioni Help discorsive
4. Salva
→ Help completo generato automaticamente
```

### Modifica Tipo Esistente
```
1. Admin → Modifica DocumentiTipo
2. Aggiorna sezioni discorsive (descrizione, FAQ, ecc.)
3. Salva
→ Sezioni tecniche rigenerate automaticamente
```

### Aggiungi Attributo
```
1. Admin → Modifica DocumentiTipo
2. Inline → Aggiungi AttributoDefinizione
3. Salva
→ attributi_dinamici aggiornato automaticamente
```

### Rigenera Solo Tecniche
```bash
python manage.py configure_help_wizard --tipo CED --rebuild-technical
```

## Trigger Auto-Aggiornamento

### Signal POST_SAVE AttributoDefinizione
- Modifica attributo → Rigenera attributi_dinamici
- Log: "Help_data rigenerato per CED dopo modifica matricola"

### Signal POST_DELETE AttributoDefinizione
- Elimina attributo → Rigenera attributi_dinamici
- Log: "Help_data rigenerato per CED dopo eliminazione matricola"

### Signal POST_SAVE DocumentiTipo
- Nuovo tipo → Inizializza help_data con placeholder
- Log: "Help_data inizializzato per nuovo tipo FAT"

### Form Admin SAVE
- Sempre → Rigenera tutte le sezioni tecniche
- Preserva → Sezioni discorsive dal form

## File Chiave

```
documenti/
├─ help_builder.py          # Generatore sezioni tecniche
├─ help_forms.py            # Form Admin user-friendly  
├─ signals.py               # Auto-aggiornamento
├─ admin.py                 # Admin customizzato
└─ management/commands/
   └─ configure_help_wizard.py  # Wizard CLI

static/
├─ admin/css/help_admin.css     # Stili UI
├─ admin/js/help_admin.js       # Validazione JS
└─ schemas/help_data_schema.json # JSON Schema
```

## Debug & Troubleshooting

### Verifica Help_Data
```python
python manage.py shell

from documenti.models import DocumentiTipo
import json

tipo = DocumentiTipo.objects.get(codice='CED')
print(json.dumps(list(tipo.help_data.keys()), indent=2))
print(json.dumps(tipo.help_data['attributi_dinamici'], indent=2))
```

### Sezioni Tecniche Non Aggiornate
```bash
# Forza rigenerazione
python manage.py configure_help_wizard --tipo CED --rebuild-technical
```

### FAQ JSON Non Valido
- Usa validatore online: jsonlint.com
- Controlla virgole, apici, parentesi
- Verifica struttura array
- Testa in browser console

### Signal Non Attivati
```python
# Verifica in documenti/apps.py
class DocumentiConfig(AppConfig):
    def ready(self):
        import documenti.signals  # ← Deve esserci!
```

## Validazione

### Real-Time (Browser)
- Blur campo FAQ → Validazione JS automatica
- Bordo verde = OK
- Bordo rosso + alert = Errore

### Save-Time (Django)
- Form.clean() → Valida struttura JSON
- Error message → Campo evidenziato in rosso

### Schema JSON
- File: `static/schemas/help_data_schema.json`
- Usa per validazione esterna se necessario

## Best Practices

### ✅ DO
- Usa Admin per modifiche rapide
- Usa Wizard per setup completo
- Lascia sezioni tecniche al sistema
- Valida sempre FAQ JSON
- Documenta workflow dettagliato
- Testa in staging prima di produzione

### ❌ DON'T
- Non modificare help_data raw (campo nascosto)
- Non duplicare info tecniche manualmente
- Non bypassare form Admin
- Non usare JSON complesso per FAQ
- Non dimenticare collectstatic dopo modifiche CSS/JS

## Migrazione Tipi Esistenti

```python
python manage.py shell

from documenti.models import DocumentiTipo
from documenti.help_builder import rebuild_help_technical_sections

# Singolo tipo
tipo = DocumentiTipo.objects.get(codice='CED')
tipo.help_data = rebuild_help_technical_sections(tipo)
tipo.save()

# Tutti i tipi
for tipo in DocumentiTipo.objects.all():
    if tipo.help_data:
        tipo.help_data = rebuild_help_technical_sections(tipo)
        tipo.save()
        print(f"✓ {tipo.codice}")
```

## Links Utili

- **Documentazione Completa**: `FEATURE_HELP_BUILDER_USER_FRIENDLY.md`
- **Riepilogo Implementazione**: `IMPLEMENTAZIONE_HELP_BUILDER_SUMMARY.md`
- **Admin Django**: `/admin/documenti/documentitipo/`
- **Frontend Help**: `/help/documenti/<CODICE>`

---

**Mantieni questo file come riferimento rapido!** 🔖
