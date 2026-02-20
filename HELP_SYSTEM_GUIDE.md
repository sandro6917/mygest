# Sistema Help Documenti - Guida Implementazione

## 📚 Panoramica

Sistema completo di documentazione integrata per i tipi di documento in MyGest. Permette di creare guide interattive consultabili direttamente dal frontend.

## 🎯 Features Implementate

### Backend (Django)
- ✅ Campi `help_data` (JSONField) e `help_ordine` (Integer) nel modello `DocumentiTipo`
- ✅ Migration `0009_add_help_fields.py` applicata
- ✅ Serializer aggiornato per includere campi help
- ✅ Fixture completa per tipo "CED - Cedolino Paga" con documentazione estensiva

### Frontend (React + TypeScript)
- ✅ Types TypeScript completi per struttura help (`types/help.ts`)
- ✅ Componenti riutilizzabili:
  - `HelpCard`: Card per lista tipi documento
  - `HelpDrawer`: Drawer laterale per help contestuale
  - `HelpIconWithPopover`: Icona help con popover esplicativo
- ✅ Pagine:
  - `/help/documenti`: Lista tipi documento con ricerca
  - `/help/documenti/:codice`: Dettaglio help con tabs
- ✅ Routes configurate
- ✅ Link "Help" aggiunto nella navbar

## 📂 Struttura Files

```
Backend:
├── documenti/models.py                   # Modello DocumentiTipo esteso
├── documenti/migrations/0009_add_help_fields.py
├── documenti/fixtures/help_cedolini.json # Fixture esempio CED
└── api/v1/documenti/serializers.py       # Serializer con help_data

Frontend:
├── src/types/
│   ├── help.ts                          # TypeScript interfaces
│   └── documento.ts                     # DocumentiTipo esteso
├── src/components/help/
│   ├── HelpCard.tsx
│   ├── HelpDrawer.tsx
│   ├── HelpIconWithPopover.tsx
│   └── index.ts
├── src/pages/help/
│   ├── HelpDocumentiPage.tsx
│   ├── HelpDocumentoTipoDetailPage.tsx
│   └── index.ts
└── src/routes/index.tsx                 # Routes /help/*
```

## 🔧 Come Aggiungere Help per un Nuovo Tipo

### 1. Metodo Django Admin (Semplice)

1. Vai su `http://localhost:8000/admin/documenti/documentitipo/`
2. Seleziona il tipo documento
3. Compila il campo `help_data` con JSON seguendo la struttura

### 2. Metodo Fixture (Raccomandato)

Crea un file `documenti/fixtures/help_<codice>.json`:

```json
[
  {
    "model": "documenti.documentitipo",
    "pk": null,
    "fields": {
      "codice": "FATT",
      "nome": "Fattura Attiva",
      "help_ordine": 20,
      "help_data": {
        "descrizione_breve": "...",
        "quando_usare": {
          "casi_uso": ["..."],
          "non_usare_per": ["..."]
        },
        "campi_obbligatori": {
          "sempre": ["cliente", "data_documento"],
          "condizionali": {}
        },
        "attributi_dinamici": {
          "disponibili": [],
          "pattern_code_examples": []
        },
        "guida_compilazione": {
          "step": []
        },
        "pattern_codice": {
          "default": "...",
          "spiegazione": "..."
        },
        "archiviazione": {
          "percorso_tipo": "...",
          "esempio_completo": "..."
        },
        "workflow": {
          "stati_possibili": [],
          "azioni_disponibili": []
        },
        "note_speciali": {
          "attenzioni": [],
          "suggerimenti": [],
          "vincoli_business": []
        },
        "faq": [],
        "risorse_correlate": {
          "guide_correlate": [],
          "tipi_documento_correlati": []
        }
      }
    }
  }
]
```

Carica con:
```bash
python manage.py loaddata documenti/fixtures/help_<codice>.json
```

### 3. Metodo Programmatico

```python
from documenti.models import DocumentiTipo

tipo = DocumentiTipo.objects.get(codice='FATT')
tipo.help_data = {
    "descrizione_breve": "...",
    # ... struttura completa
}
tipo.help_ordine = 20
tipo.save()
```

## 📖 Struttura Dati Help

### Campi Principali

```typescript
interface DocumentoTipoHelpData {
  descrizione_breve: string;           // Descrizione 1-2 righe
  quando_usare: CasoUso;               // Quando usare/non usare
  campi_obbligatori: CampiObbligatori; // Campi richiesti
  attributi_dinamici: AttributiDinamici; // Attributi del tipo
  guida_compilazione: GuidaCompilazione; // Step-by-step
  pattern_codice: PatternCodice;       // Spiegazione pattern
  archiviazione: Archiviazione;        // Dove vengono salvati i file
  relazione_fascicoli?: RelazioneFascicoli; // Come collegare a fascicoli
  workflow: Workflow;                  // Stati e azioni
  note_speciali: NoteSpeciali;         // Attenzioni/suggerimenti
  faq: FAQ[];                          // Domande frequenti
  risorse_correlate: RisorseCorrelate; // Link correlati
  changelog?: ChangelogEntry[];        // Storia modifiche
}
```

### Esempio Minimo

```json
{
  "descrizione_breve": "Breve descrizione del tipo documento",
  "quando_usare": {
    "casi_uso": ["Caso 1", "Caso 2"],
    "non_usare_per": ["Caso A"]
  },
  "campi_obbligatori": {
    "sempre": ["cliente", "data_documento"],
    "condizionali": {}
  },
  "attributi_dinamici": {
    "disponibili": [],
    "pattern_code_examples": []
  },
  "guida_compilazione": {
    "step": [
      {
        "numero": 1,
        "titolo": "Primo passo",
        "descrizione": "Descrizione dettagliata",
        "campo": "cliente",
        "esempio": "Es. Rossi SRL"
      }
    ]
  },
  "pattern_codice": {
    "default": "{CLI}-{TIT}-{ANNO}-{SEQ:03d}",
    "spiegazione": "Spiegazione pattern",
    "esempi": [],
    "placeholder_disponibili": {}
  },
  "archiviazione": {
    "percorso_tipo": "/archivio/{CLI}/{TIT}/{ANNO}/",
    "esempio": "/srv/archivio/ROSSI01/FATT/2025/",
    "esempio_completo": "/srv/archivio/ROSSI01/FATT/2025/FATT-ROSSI01-2025-001.pdf",
    "note": []
  },
  "workflow": {
    "stati_possibili": ["Bozza", "Protocollato"],
    "azioni_disponibili": []
  },
  "note_speciali": {
    "attenzioni": [],
    "suggerimenti": [],
    "vincoli_business": []
  },
  "faq": [],
  "risorse_correlate": {
    "guide_correlate": [],
    "tipi_documento_correlati": []
  }
}
```

## 🎨 Personalizzazione UI

### Ordine Visualizzazione

Usa il campo `help_ordine` per controllare l'ordine nella pagina Help:
- `help_ordine = 0`: Appare per primo
- `help_ordine = 10`: Cedolini (come da fixture)
- `help_ordine = 100`: Appare per ultimo

### Nascondere Tipo dalla Sezione Help

Imposta `help_data = {}` oppure lascia il campo vuoto. Il tipo non apparirà nella lista help.

## 🔍 Testing

### Backend
```bash
# Verifica tipo caricato
python manage.py shell -c "from documenti.models import DocumentiTipo; print(DocumentiTipo.objects.get(codice='CED').help_data)"

# Verifica API
curl http://localhost:8000/api/v1/documenti/tipi/ | jq '.[] | select(.codice=="CED") | .help_data'
```

### Frontend
1. Vai su `http://localhost:5173/help/documenti`
2. Verifica card tipo CED
3. Clicca "Leggi Guida"
4. Naviga tra i tab (Panoramica, Guida, Attributi, FAQ)

## 📝 Esempio Completo: Tipo Cedolino

Vedi file: `documenti/fixtures/help_cedolini.json`

Include:
- Descrizione completa e casi d'uso
- 7 step dettagliati per compilazione
- 3 attributi dinamici (dipendente, mese, mensilità)
- Esempi pattern codice
- Spiegazione archiviazione
- 8 FAQ complete
- Note privacy e GDPR
- Link risorse correlate

## 🚀 Prossimi Sviluppi

### Fase 3: Contenuti (da fare)
- [ ] Scrivere help per tipo FATT (Fatture)
- [ ] Scrivere help per tipo CONTR (Contratti)
- [ ] Scrivere help per tipo CUD
- [ ] Aggiungere screenshot step compilazione
- [ ] Registrare video tutorial
- [ ] Traduzione in inglese

### Features Future
- [ ] Help contestuale inline nei form (tooltip automatici)
- [ ] Sistema di ricerca full-text nella documentazione
- [ ] Feedback utenti sulle guide (utile/non utile)
- [ ] Analytics su guide più consultate
- [ ] Export PDF delle guide
- [ ] Versioning guide con changelog
- [ ] Help basato su AI (chatbot)

## 🎯 Best Practices

1. **Scrivi per utenti non tecnici**: Evita jargon, spiega passo-passo
2. **Usa esempi concreti**: Meglio "ROSMAR01-2025-001" che "codice generato"
3. **Screenshot quando possibile**: Immagini valgono 1000 parole
4. **Testa con utenti reali**: Fai leggere le guide e raccogli feedback
5. **Mantieni aggiornato**: Quando cambia il tipo, aggiorna la guida
6. **Versioning**: Usa campo changelog per tracciare modifiche

## 📞 Support

Per domande o problemi:
- GitHub Issues: https://github.com/sandro6917/mygest/issues
- Email: admin@mygest.it

---

**Versione**: 1.0.0  
**Data**: 29 Gennaio 2026  
**Autore**: Sandro Chimenti
