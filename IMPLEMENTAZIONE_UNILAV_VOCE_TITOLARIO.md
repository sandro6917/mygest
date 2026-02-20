# Modifiche Implementate: UNILAV - Voce Titolario e Attributo SELECT

**Data**: 3 Febbraio 2026  
**Feature**: Importazione UNILAV  
**Ticket**: Requisiti utente per gestione corretta documenti UNILAV

---

## 📋 Modifiche Richieste

1. ✅ **Ubicazione documento deve rimanere vuota**
2. ✅ **Voce di Titolario intestata al dipendente sotto "Dossier personale"**
3. ✅ **Attributo dinamico `tipo` deve essere una SELECT con valori impostati**

---

## 🔧 Implementazione

### 1. Ubicazione = None (Documenti Digitali)

**File**: `api/v1/documenti/views.py`

```python
documento = Documento.objects.create(
    tipo=tipo_unilav,
    cliente=cliente_datore,
    titolario_voce=voce_dipendente,
    descrizione=descrizione,
    data_documento=documento_data['data_comunicazione'],
    digitale=True,
    tracciabile=True,
    stato='definitivo',
    ubicazione=None,  # ← ESPLICITO: documenti digitali non hanno ubicazione fisica
)
```

**Nota**: Già implementato correttamente per documenti digitali, ora esplicitato nel codice.

---

### 2. Voce Titolario Intestata al Dipendente

**File**: `api/v1/documenti/views.py`

**Logica implementata**:

```python
# 3.bis Crea/Trova voce titolario intestata al dipendente
# Parent: HR-PERS (Dossier personale)
# Sottovoce: Codice anagrafica dipendente (es. CONSLI01)
# Titolo: "Dossier {Cognome} {Nome}"
voce_dipendente = None
try:
    voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
    
    # Cerca voce intestata al dipendente
    voce_dipendente = TitolarioVoce.objects.filter(
        parent=voce_hr_pers,
        anagrafica=anagrafica_lavoratore
    ).first()
    
    if not voce_dipendente:
        # Crea nuova voce intestata
        # IMPORTANTE: L'anagrafica deve avere un codice valido
        if not anagrafica_lavoratore.codice:
            # Genera codice anagrafica se non presente
            from anagrafiche.utils import get_or_generate_cli
            get_or_generate_cli(anagrafica_lavoratore)
            anagrafica_lavoratore.refresh_from_db()
        
        voce_dipendente = TitolarioVoce.objects.create(
            codice=anagrafica_lavoratore.codice,
            titolo=f"Dossier {anagrafica_lavoratore.display_name()}",
            parent=voce_hr_pers,
            anagrafica=anagrafica_lavoratore,
            pattern_codice='{CLI}-{ANA}-UNILAV-{ANNO}-{SEQ:03d}',
            consente_intestazione=False
        )
        logger.info(f"Creata voce titolario per dipendente: {voce_dipendente.codice} - {voce_dipendente.titolo}")
    else:
        logger.info(f"Trovata voce titolario esistente per dipendente: {voce_dipendente.codice}")
        
except TitolarioVoce.DoesNotExist:
    logger.warning("Voce titolario HR-PERS non trovata. Documento verrà creato senza voce titolario.")
    voce_dipendente = None
```

**Caratteristiche**:
- **Parent**: `HR-PERS` (Dossier personale)
- **Codice**: Codice anagrafica dipendente (es. `CONSLI01`)
- **Titolo**: `"Dossier {Cognome} {Nome}"` (es. "Dossier CONSORTI LISA")
- **Pattern codice documento**: `{CLI}-{ANA}-UNILAV-{ANNO}-{SEQ:03d}`
  - Esempio: `CLI001-CONSLI01-UNILAV-2026-001`
- **Riutilizzo**: Se la voce esiste già, viene riutilizzata
- **Generazione codice**: Se l'anagrafica non ha codice, viene generato automaticamente

**Import aggiunti**:
```python
from titolario.models import TitolarioVoce
import logging

logger = logging.getLogger(__name__)
```

---

### 3. Attributo `tipo` come SELECT

**Database**: Già configurato correttamente

Verifica configurazione:
```bash
python manage.py shell -c "
from documenti.models import DocumentiTipo, AttributoDefinizione
tipo = DocumentiTipo.objects.get(codice='UNILAV')
attr = AttributoDefinizione.objects.get(tipo_documento=tipo, codice='tipo')
print(f'Tipo dato: {attr.tipo_dato}')
print(f'Scelte: {attr.choices}')
"
```

Output:
```
Tipo dato: choice
Scelte: Assunzione, Proroga, Trasformazione, Cessazione
```

**Frontend**: Modificato da TextField a Select

**File**: `frontend/src/pages/ImportaUnilavPage.tsx`

**Import aggiunti**:
```typescript
import {
  // ...esistenti
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
```

**Campo modificato**:
```tsx
// PRIMA (TextField):
<TextField
  label="Tipologia Contrattuale"
  value={editedData.documento.tipo || ''}
  onChange={(e) => updateUnilav('tipo', e.target.value)}
  fullWidth
/>

// DOPO (Select):
<FormControl fullWidth>
  <InputLabel>Tipologia Comunicazione *</InputLabel>
  <Select
    value={editedData.documento.tipo || ''}
    onChange={(e) => updateUnilav('tipo', e.target.value)}
    label="Tipologia Comunicazione *"
    required
  >
    <MenuItem value="">
      <em>Seleziona tipologia</em>
    </MenuItem>
    <MenuItem value="Assunzione">Assunzione</MenuItem>
    <MenuItem value="Proroga">Proroga</MenuItem>
    <MenuItem value="Trasformazione">Trasformazione</MenuItem>
    <MenuItem value="Cessazione">Cessazione</MenuItem>
  </Select>
</FormControl>
```

**Valori disponibili**:
1. **Assunzione** - Prima comunicazione per nuovo rapporto di lavoro
2. **Proroga** - Estensione contratto a tempo determinato
3. **Trasformazione** - Modifica tipologia contrattuale (es. da determinato a indeterminato)
4. **Cessazione** - Fine rapporto di lavoro

---

## 📊 Struttura Finale Documento UNILAV

```
Documento UNILAV
├── tipo: UNILAV (DocumentiTipo)
├── cliente: Cliente (Datore di Lavoro)
├── titolario_voce: TitolarioVoce (Intestata al dipendente)
│   ├── Codice: CONSLI01 (codice anagrafica lavoratore)
│   ├── Titolo: "Dossier CONSORTI LISA"
│   ├── Parent: HR-PERS (Dossier personale)
│   └── Pattern: {CLI}-{ANA}-UNILAV-{ANNO}-{SEQ:03d}
├── descrizione: "UNILAV 1700026200007595 - CONSORTI LISA"
├── data_documento: 2026-01-03 (data comunicazione)
├── digitale: True
├── tracciabile: True
├── stato: definitivo
├── ubicazione: None ← SEMPRE None per documenti digitali
├── file: PDF UNILAV allegato
│
├── Attributi Dinamici:
│   ├── dipendente: 124 (ID anagrafica lavoratore)
│   ├── tipo: "Assunzione" ← SELECT con 4 scelte
│   ├── data_comunicazione: 2026-01-03
│   ├── data_da: 2026-01-03 (inizio rapporto)
│   └── data_a: 2026-12-31 (fine rapporto)
│
└── Note:
    ├── Qualifica: Operaio
    ├── CCNL: CCNL Commercio
    ├── Livello: 3° livello
    ├── Retribuzione: 1.500,00 EUR
    ├── Ore settimanali: 40
    └── Tipo orario: Tempo pieno
```

---

## 🧪 Test Eseguito

**File**: `test_unilav_updates.py`

```bash
cd /home/sandro/mygest
source venv/bin/activate
python manage.py shell < test_unilav_updates.py
```

**Risultati**:
```
✅ Tipo UNILAV trovato: UNILAV (ID: 34)
✅ Attributo 'tipo' configurato come SELECT (tipo_dato='choice')
   Scelte disponibili: Assunzione, Proroga, Trasformazione, Cessazione
✅ Voce HR-PERS trovata: Dossier personale (ID: 20)
   Voci intestate a dipendenti: 6
✅ Simulazione creazione voce intestata OK
```

---

## 📝 File Modificati

### Backend
1. **`api/v1/documenti/views.py`**
   - Aggiunto import `TitolarioVoce` e `logging`
   - Aggiunta logica creazione/recupero voce titolario intestata
   - Esplicitato `ubicazione=None` nella creazione documento

### Frontend
2. **`frontend/src/pages/ImportaUnilavPage.tsx`**
   - Aggiunto import `MenuItem`, `FormControl`, `InputLabel`, `Select`
   - Modificato campo "Tipologia Contrattuale" da TextField a Select
   - Aggiunte 4 opzioni: Assunzione, Proroga, Trasformazione, Cessazione

### Documentazione
3. **`FEATURE_UNILAV_CAMPI_DOCUMENTO.md`**
   - Aggiornata sezione campi base con `titolario_voce` e `ubicazione=None`
   - Aggiornata sezione attributi con info SELECT per `tipo`

4. **`test_unilav_updates.py`** (nuovo)
   - Script di test per verificare configurazione

---

## ✅ Checklist Completamento

- [x] Ubicazione esplicitamente `None` per documenti digitali
- [x] Voce titolario intestata al dipendente sotto HR-PERS
  - [x] Codice = codice anagrafica lavoratore
  - [x] Titolo = "Dossier {Cognome} {Nome}"
  - [x] Pattern = `{CLI}-{ANA}-UNILAV-{ANNO}-{SEQ:03d}`
  - [x] Riutilizzo voce esistente se già presente
  - [x] Generazione automatica codice anagrafica se mancante
- [x] Attributo `tipo` come SELECT
  - [x] Database configurato con `tipo_dato='choice'`
  - [x] Frontend usa `<Select>` invece di `<TextField>`
  - [x] 4 scelte disponibili
- [x] Test eseguiti con successo
- [x] Documentazione aggiornata

---

## 🚀 Prossimi Passi

1. **Test end-to-end manuale**:
   - Caricare PDF UNILAV di test
   - Verificare preview mostra SELECT per tipo
   - Confermare importazione
   - Verificare documento creato:
     - ✅ Voce titolario intestata al dipendente
     - ✅ Codice documento generato correttamente
     - ✅ Ubicazione = None
     - ✅ Attributo tipo salvato correttamente

2. **Verifiche database**:
   ```sql
   -- Documento creato
   SELECT * FROM documenti_documento WHERE tipo_id = 34 ORDER BY id DESC LIMIT 1;
   
   -- Voce titolario dipendente
   SELECT * FROM titolario_titolarovoce 
   WHERE parent_id = 20 AND anagrafica_id = <ID_LAVORATORE>;
   
   -- Attributi dinamici
   SELECT av.*, ad.codice, av.valore 
   FROM documenti_attributovalore av
   JOIN documenti_attributodefinizione ad ON av.definizione_id = ad.id
   WHERE av.documento_id = <ID_DOCUMENTO>;
   ```

3. **Test casi edge**:
   - Dipendente senza codice anagrafica (deve generarlo automaticamente)
   - Dipendente con voce titolario già esistente (deve riutilizzarla)
   - HR-PERS mancante (deve loggare warning ma continuare)
   - Tipo comunicazione non selezionato (validazione required)

---

**Implementato da**: GitHub Copilot  
**Revisione**: In attesa di test utente
