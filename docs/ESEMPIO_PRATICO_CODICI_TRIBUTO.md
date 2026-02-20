# Esempio Pratico - Utilizzo Codici Tributo F24

## Scenario: Studio Commercialista invia comunicazione F24 ai clienti

### Step 1: Creare il Template (Django Admin)

**Admin** → **Comunicazioni** → **Template Comunicazione** → **Aggiungi**

```
Nome: Scadenza F24 Mensile
Categoria: Comunicazioni Fiscali
Attivo: ✓

Oggetto:
Promemoria F24 - {mese} {anno} - Codice {codice_tributo}

Corpo:
Gentile {nome_cliente},

Le ricordiamo la scadenza per il versamento F24 relativo a {mese} {anno}.

DETTAGLI VERSAMENTO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Codice Tributo: {codice_tributo}
Sezione:        F24
Importo:        € {importo}
Scadenza:       {data_scadenza}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODALITÀ DI PAGAMENTO:
- Online tramite home banking
- Presso sportello bancario o postale
- Tramite servizi telematici dell'Agenzia delle Entrate

Per ulteriori informazioni o assistenza, non esiti a contattarci.

Cordiali saluti,
Studio Commercialista Rossi & Associati
```

**Campi Dinamici da creare:**

1. **nome_cliente**
   - Label: Nome Cliente
   - Tipo: Text
   - Required: ✓
   - Help Text: Nome e cognome o ragione sociale

2. **codice_tributo**
   - Label: Codice Tributo F24
   - Tipo: **Codice Tributo F24** ← NUOVO TIPO
   - Required: ✓
   - Help Text: Seleziona il codice tributo appropriato

3. **importo**
   - Label: Importo da versare
   - Tipo: Decimal
   - Required: ✓
   - Help Text: Importo in euro (es: 1234.56)

4. **mese**
   - Label: Mese di riferimento
   - Tipo: Choice
   - Choices: Gennaio,Febbraio,Marzo,Aprile,Maggio,Giugno,Luglio,Agosto,Settembre,Ottobre,Novembre,Dicembre
   - Required: ✓

5. **anno**
   - Label: Anno
   - Tipo: Integer
   - Default: 2024
   - Required: ✓

6. **data_scadenza**
   - Label: Data Scadenza
   - Tipo: Date
   - Required: ✓
   - Help Text: Formato: GG/MM/AAAA

**Salva il template** ✅

---

### Step 2: Creare la Comunicazione (Frontend React)

**Frontend** → **Comunicazioni** → **+ Nuova Comunicazione**

#### A. Informazioni Principali

```
Tipo:       [INFORMATIVA ▼]
Direzione:  [OUT ▼]
Template:   [Scadenza F24 Mensile ▼]  ← Seleziona il template
Firma:      [Studio Commercialista Rossi ▼]
```

#### B. Campi Template (Appaiono automaticamente)

**Nome Cliente:**
```
┌─────────────────────────────────────────┐
│ Mario Rossi S.r.l.                      │
└─────────────────────────────────────────┘
```

**Codice Tributo F24:** ← AUTOCOMPLETE
```
┌─────────────────────────────────────────┐
│ ritenute                          ✕  🔄 │  ← Inizia a digitare
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐  ← Dropdown appare
│ 1001   [ERARIO]                         │
│ Ritenute su redditi da lavoro           │  ← Clicca per selezionare
│ dipendente e assimilati                 │
│ Causale: Ritenute lavoro dipendente    │
├─────────────────────────────────────────┤
│ 1002   [ERARIO]                         │
│ Ritenute su redditi di lavoro           │
│ autonomo                                │
│ Causale: Compensi professionisti       │
├─────────────────────────────────────────┤
│ ... altri 6 risultati ...              │
└─────────────────────────────────────────┘
```

**Dopo la selezione:**
```
┌─────────────────────────────────────────┐
│ 1001 - Ritenute su redditi da     ✕    │  ← Mostra display completo
└─────────────────────────────────────────┘
```

**Importo:**
```
┌─────────────────────────────────────────┐
│ 2850.75                                  │
└─────────────────────────────────────────┘
```

**Mese:**
```
┌─────────────────────────────────────────┐
│ Dicembre                            ▼   │
└─────────────────────────────────────────┘
```

**Anno:**
```
┌─────────────────────────────────────────┐
│ 2024                                     │
└─────────────────────────────────────────┘
```

**Data Scadenza:**
```
┌─────────────────────────────────────────┐
│ 2024-01-16                              │
└─────────────────────────────────────────┘
```

#### C. Preview del Messaggio (Appare automaticamente)

```
┌─────────────────────────────────────────────────────────────┐
│ 📄 PREVIEW MESSAGGIO                                        │
│                                                             │
│ Oggetto:                                                    │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Promemoria F24 - Dicembre 2024 - Codice 1001 - Ritenute││
│ │ su redditi da lavoro dipendente e assimilati            ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Corpo:                                                      │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Gentile Mario Rossi S.r.l.,                             ││
│ │                                                          ││
│ │ Le ricordiamo la scadenza per il versamento F24 relativo││
│ │ a Dicembre 2024.                                         ││
│ │                                                          ││
│ │ DETTAGLI VERSAMENTO:                                     ││
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │ Codice Tributo: 1001 - Ritenute su redditi da lavoro   ││
│ │                 dipendente e assimilati                 ││
│ │ Sezione:        F24                                     ││
│ │ Importo:        € 2850.75                               ││
│ │ Scadenza:       16/01/2024                              ││
│ │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ││
│ │                                                          ││
│ │ MODALITÀ DI PAGAMENTO:                                   ││
│ │ - Online tramite home banking                           ││
│ │ - Presso sportello bancario o postale                   ││
│ │ - Tramite servizi telematici dell'Agenzia delle Entrate ││
│ │                                                          ││
│ │ Per ulteriori informazioni o assistenza, non esiti a    ││
│ │ contattarci.                                             ││
│ │                                                          ││
│ │ Cordiali saluti,                                         ││
│ │ Studio Commercialista Rossi & Associati                 ││
│ └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

#### D. Destinatari

```
Destinatari (Email):
┌─────────────────────────────────────────┐
│ mario.rossi@email.it                     │
└─────────────────────────────────────────┘

O seleziona da Liste:
┌─────────────────────────────────────────┐
│ Clienti Mensile                      ▼  │
└─────────────────────────────────────────┘
```

#### E. Salva e Invia

```
[Annulla]  [Salva come Bozza]  [Salva e Invia]
```

---

### Step 3: Risultato Finale

**Email inviata a: mario.rossi@email.it**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Da: studio@rossiassociati.it
A: mario.rossi@email.it
Oggetto: Promemoria F24 - Dicembre 2024 - Codice 1001 - Ritenute 
         su redditi da lavoro dipendente e assimilati
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gentile Mario Rossi S.r.l.,

Le ricordiamo la scadenza per il versamento F24 relativo a 
Dicembre 2024.

DETTAGLI VERSAMENTO:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Codice Tributo: 1001 - Ritenute su redditi da lavoro dipendente 
                e assimilati
Sezione:        F24
Importo:        € 2850.75
Scadenza:       16/01/2024
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MODALITÀ DI PAGAMENTO:
- Online tramite home banking
- Presso sportello bancario o postale
- Tramite servizi telematici dell'Agenzia delle Entrate

Per ulteriori informazioni o assistenza, non esiti a contattarci.

Cordiali saluti,
Studio Commercialista Rossi & Associati

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Studio Commercialista Rossi & Associati
Via Roma 123, 00100 Roma
Tel: 06 1234567 | Email: studio@rossiassociati.it
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Altri Esempi di Utilizzo

### Esempio 2: Comunicazione IMU

**Template:** Promemoria IMU
**Codice Tributo selezionato:** `3800` - IMU - Imposta municipale propria su abitazione principale

### Esempio 3: Comunicazione INPS

**Template:** Versamento Contributi INPS
**Codice Tributo selezionato:** `PXX` - Contributi gestione separata INPS

### Esempio 4: Comunicazione IVA

**Template:** Versamento IVA Trimestrale
**Codice Tributo selezionato:** `6099` - IVA - Versamenti trimestrali

---

## Tips & Tricks

### 🔍 Ricerca Efficace

**Per Codice:**
- Digita `1001` → Trova esattamente il codice 1001

**Per Descrizione:**
- Digita `ritenute` → Trova tutti i codici con "ritenute" nella descrizione
- Digita `imu` → Trova tutti i codici IMU

**Per Causale:**
- Digita `lavoro dipendente` → Trova codici relativi al lavoro dipendente

### 🏷️ Filtro per Sezione

Cerca codici solo in una sezione specifica:
- ERARIO: Ritenute, imposte dirette, IVA
- INPS: Contributi previdenziali
- REGIONI: IRAP, addizionali regionali
- IMU: Tributi comunali
- INAIL: Premi assicurativi
- ACCISE: Tributi energetici

### ⚠️ Codici Obsoleti

Il sistema mostra un warning per codici non più attivi:
- Esempio: `TASI` - Tassa sui Servizi Indivisibili (abolita dal 2020)

### 📋 Template Riutilizzabili

Crea template generici e riutilizzali:
1. Template "Generico F24" con placeholder `{tipo_tributo}`
2. Seleziona codice tributo diverso per ogni comunicazione
3. Risparmia tempo nella creazione

---

## Vantaggi del Sistema

✅ **Accuratezza**: Codici ufficiali dall'Agenzia delle Entrate
✅ **Velocità**: Autocomplete riduce errori di digitazione
✅ **Professionalità**: Display formattato automaticamente
✅ **Flessibilità**: Riutilizza template per codici diversi
✅ **Aggiornabilità**: Scraper per aggiornare i codici
✅ **Tracciabilità**: Storico comunicazioni con codici tributo

---

## Troubleshooting

**Q: Non trovo il codice che cerco**
A: Prova con sinonimi o cerca per numero se lo conosci

**Q: Il codice è marcato come obsoleto**
A: Verifica con l'Agenzia delle Entrate se è ancora valido

**Q: Come aggiorno i codici tributo?**
A: Usa `python scripts/scraper_codici_tributo.py`

**Q: Posso aggiungere codici personalizzati?**
A: Sì, tramite Django Admin → Scadenze → Codici Tributo F24

---

## Conclusione

Il sistema di codici tributo F24 rende la creazione di comunicazioni fiscali **rapida**, **accurata** e **professionale**. 

🎉 **Pronto all'uso!**
