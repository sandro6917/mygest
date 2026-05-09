# Guida: Field Mapping con Note

## 📝 Gestione Campi Estratti

### Opzioni di Destinazione

Quando crei un mapping tra una zona del template e un campo del documento, hai diverse opzioni:

#### 1. **Campi Fissi del Documento**
Mappano direttamente a campi del modello `Documento`:
- `numero_protocollo` - Numero protocollo
- `data_documento` - Data documento
- `oggetto` - Oggetto del documento
- `note` (sovrascrive) - Sostituisce completamente il campo Note

#### 2. **Campi Cliente** (lookup automatico in Phase 5)
Mappano a campi testuali dell'anagrafica cliente:
- `cliente.anagrafica.codice_fiscale` - CF del cliente (lookup automatico)
- `cliente.anagrafica.partita_iva` - P.IVA del cliente
- `cliente.anagrafica.nome` - Denominazione cliente
- `cliente.anagrafica.email` - Email cliente

**Nota**: Non mappare mai direttamente a `cliente` (FK), usa i campi testuali!

#### 3. **Attributi Dinamici**
Mappano ad attributi specifici del tipo documento (es. UNILAV):
- `attributi.tipo` - Tipo comunicazione
- `attributi.lavoratore_cf` - Codice Fiscale lavoratore
- `attributi.data_comunicazione` - Data comunicazione
- ... tutti gli altri 40 attributi UNILAV

#### 4. **📝 Aggiungi a Note** (NUOVO!)
Campo virtuale `__note__` che **appende** il valore estratto alle Note:

**Esempio**:
```
Zona: datore_telefono
Campo Documento: 📝 Aggiungi a Note

Risultato nel documento:
note = """
... eventuali note esistenti ...

Datore - Telefono: 06-12345678
"""
```

---

## 🎯 Strategia Consigliata per UNILAV

### Mapping Essenziali (dati strutturati):
| Zona Template | Campo Documento | Motivo |
|---------------|-----------------|--------|
| `tipo_comunicazione` | `attributi.tipo` | Obbligatorio, dropdown |
| `data_comunicazione` | `attributi.data_comunicazione` | Data evento |
| `lavoratore_cf` | `attributi.lavoratore_cf` | Identificativo lavoratore |
| `lavoratore_cognome` | `attributi.lavoratore_cognome` | Anagrafica lavoratore |
| `lavoratore_nome` | `attributi.lavoratore_nome` | Anagrafica lavoratore |
| `cf_datore` | `cliente.anagrafica.codice_fiscale` | Lookup cliente automatico |

### Mapping Secondari (informazioni aggiuntive):
| Zona Template | Campo Documento | Motivo |
|---------------|-----------------|--------|
| `datore_telefono` | `📝 Aggiungi a Note` | Info utile ma non strutturata |
| `datore_email` | `📝 Aggiungi a Note` | Info utile ma non strutturata |
| `datore_indirizzo` | `📝 Aggiungi a Note` | Info utile ma non strutturata |
| `lavoratore_indirizzo` | `📝 Aggiungi a Note` | Info utile ma non strutturata |

---

## ⚙️ Comportamento in Phase 5 (Form Integration)

### Scenario: UNILAV con mapping completo

**Dati estratti dall'AI**:
```json
{
  "tipo_comunicazione": "Assunzione",
  "lavoratore_cf": "RSSMRA80A01H501Z",
  "lavoratore_cognome": "Rossi",
  "lavoratore_nome": "Mario",
  "cf_datore": "12345678901",
  "datore_telefono": "06-12345678",
  "datore_email": "info@azienda.it"
}
```

**Applicazione mapping**:
1. `attributi.tipo` = "Assunzione"
2. `attributi.lavoratore_cf` = "RSSMRA80A01H501Z"
3. `attributi.lavoratore_cognome` = "Rossi"
4. `attributi.lavoratore_nome` = "Mario"
5. **Lookup cliente** con CF "12345678901" → `cliente_id` = 42 (se trovato)
6. **Append a note**:
   ```
   Datore - Telefono: 06-12345678
   Datore - Email: info@azienda.it
   ```

**Risultato finale nel form**:
- Campo `Cliente`: pre-compilato con "Azienda XYZ S.r.l." (ID 42)
- Campo `Tipo`: pre-compilato con "Assunzione"
- Campo `Lavoratore CF`: "RSSMRA80A01H501Z"
- Campo `Lavoratore Cognome`: "Rossi"
- Campo `Lavoratore Nome`: "Mario"
- Campo `Note`:
  ```
  Datore - Telefono: 06-12345678
  Datore - Email: info@azienda.it
  ```

**Utente può**:
- ✅ Verificare i dati pre-compilati
- ✅ Correggere eventuali errori
- ✅ Completare campi mancanti
- ✅ Salvare il documento

Le correzioni vengono salvate in `ExtractionCorrection` per migliorare l'AI.

---

## 🚫 Cosa NON Fare

### ❌ Mappare FK direttamente
```
SBAGLIATO: cf_datore → cliente (FK vuole ID, non testo!)
CORRETTO:  cf_datore → cliente.anagrafica.codice_fiscale
```

### ❌ Mappare stesso campo 2 volte
```
SBAGLIATO:
  - lavoratore_cf → attributi.lavoratore_cf
  - lavoratore_cf → __note__

CORRETTO: Scegli una destinazione per campo
```

### ❌ Sovrascrivere Note accidentalmente
```
ATTENZIONE: campo "note" (sovrascrive) sostituisce tutto!
USA:        "📝 Aggiungi a Note" per appendere
```

---

## 💡 Best Practices

1. **Mappa prima i campi obbligatori** (tipo, data, CF lavoratore)
2. **Usa campi Cliente per lookup** (CF datore → cliente.anagrafica.codice_fiscale)
3. **Usa attributi dinamici** per dati strutturati specifici UNILAV
4. **Usa `__note__`** per informazioni secondarie/leggibilità umana
5. **Non mappare tutto**: solo ciò che serve davvero
6. **Testa il template** con documenti reali prima di attivarlo

---

## 🔄 Workflow Completo

```
1. TEMPLATE MANAGER (Phase 3 - ADESSO)
   ↓
   Crei zone sul canvas
   ↓
   Mappi zone a campi destinazione
   ↓
   Salvi template

2. AI IMPORT PAGE (Phase 4 - prossimo)
   ↓
   Utente carica UNILAV
   ↓
   AI estrae dati usando template
   ↓
   Mostra preview risultati

3. FORM INTEGRATION (Phase 5)
   ↓
   Pre-fill form con dati estratti
   ↓
   Lookup automatico cliente via CF
   ↓
   Append info secondarie a note
   ↓
   Utente verifica e salva
   ↓
   Salva correzioni per training AI
```

---

**Versione**: 1.0  
**Data**: 2 Marzo 2026  
**Feature**: Field Mapping con campo virtuale `__note__`
