# Feature: Importa ZIP come Libro Unico

## 📋 Descrizione

Nuova funzionalità che permette di importare un file ZIP contenente cedolini come **singolo documento LIBUNI** invece che come documenti BPAG individuali.

## 🎯 Requisiti Implementati

### Workflow
1. **Upload ZIP**: L'utente carica un file ZIP contenente cedolini
2. **Parsing automatico**: Il sistema parsa il primo PDF per estrarre:
   - CF azienda → cerca/crea cliente datore di lavoro
   - Periodo retribuzione (es: "Aprile 2025")
   - Data documento (primo giorno del mese)
3. **Scansione dipendenti**: Analizza tutti i PDF per estrarre lista dipendenti
4. **Controllo duplicati**: Verifica se esiste già LIBUNI per stesso cliente + periodo + tipo
   - Se duplicato: chiede azione (Sostituisci | Duplica | Skip)
5. **Creazione documento**:
   - **Tipo**: LIBUNI
   - **Cliente**: Datore di lavoro (azienda)
   - **Titolo**: "Libro Unico {mese} {anno} - {ragione_sociale}"
   - **Data documento**: Primo giorno del mese di riferimento
   - **Titolario**: HR-PAY/PAG
   - **Fascicolo**: None
   - **File allegato**: ZIP intero
   - **Note**: 
     ```
     Contiene {n} cedolini
     
     Dipendenti:
     - Nome Cognome 1
     - Nome Cognome 2
     ...
     ```

## 🛠️ Implementazione

### Backend

#### 1. **Serializer** (`api/v1/documenti/serializers.py`)
```python
class ImportaZipLibroUnicoSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    azione_duplicati = serializers.ChoiceField(
        choices=['sostituisci', 'duplica', 'skip'],
        default='duplica'
    )
```

#### 2. **Utility** (`api/v1/documenti/importa_libro_unico.py`)
Funzione principale: `importa_zip_come_libro_unico()`
- Estrae PDF dallo ZIP
- Parsa primo PDF per metadati
- Cerca/crea cliente datore
- Scansiona tutti i PDF per elenco dipendenti
- Controlla duplicati
- Crea/sostituisce documento LIBUNI

#### 3. **Endpoint API** (`api/v1/documenti/views.py`)
```python
@action(detail=False, methods=['post'], url_path='importa-zip-libro-unico')
def importa_zip_libro_unico(self, request):
    # POST /api/v1/documenti/importa-zip-libro-unico/
```

**Request:**
```json
{
  "file": <ZIP file>,
  "azione_duplicati": "sostituisci" | "duplica" | "skip"
}
```

**Response Success:**
```json
{
  "success": true,
  "documento_id": 123,
  "duplicato": false,
  "azione": "creato",
  "metadati": {
    "titolo": "Libro Unico Aprile 2025 - ARKLABS SRL",
    "periodo": "Aprile 2025",
    "anno": 2025,
    "mese": 4,
    "cliente": "ARKLABS SRL",
    "num_cedolini": 15,
    "dipendenti": ["Mario Rossi", "Luca Bianchi", ...]
  },
  "errori": []
}
```

**Response Error:**
```json
{
  "success": false,
  "errori": [
    "Impossibile identificare il datore di lavoro (CF mancante)",
    "..."
  ]
}
```

### Frontend

#### 1. **API Client** (`frontend/src/api/documenti.ts`)
```typescript
async importaZipLibroUnico(
  file: File,
  azioneDuplicati: 'sostituisci' | 'duplica' | 'skip' = 'duplica'
): Promise<{...}>
```

#### 2. **UI Component** (`frontend/src/pages/ImportaCedoliniPage.tsx`)
- **Pulsante**: "📚 Importa ZIP come Libro Unico"
  - Visibile solo se il file selezionato è un ZIP
  - Posizionato sotto il pulsante "Analizza file"
- **Handler**: `handleImportaLibroUnico()`
  - Chiede conferma all'utente
  - Esegue importazione con `azione_duplicati='duplica'`
  - Mostra risultato in Alert con metadati
  - Reset automatico dopo 3 secondi se successo

#### 3. **UI Feedback**
- Loading state durante importazione
- Alert con risultato:
  - ✅ Successo: Mostra titolo, periodo, cliente, num cedolini, dipendenti
  - ⚠️ Duplicato: Avvisa dell'ID duplicato e azione eseguita
  - ❌ Errore: Lista errori

## 📊 Logica Duplicati

**Criterio duplicato**: 
```python
Documento.objects.filter(
    cliente=cliente_datore,
    tipo=tipo_libuni,
    data_documento__year=anno,
    data_documento__month=mese
).first()
```

**Azioni disponibili**:
1. **sostituisci**: Elimina file vecchio e aggiorna documento esistente
2. **duplica**: Crea nuovo documento (permette duplicati)
3. **skip**: Non crea nulla, restituisce info duplicato

## 🔒 Validazioni

### Backend
- ✅ File deve essere ZIP
- ✅ Dimensione massima: 100MB
- ✅ ZIP deve contenere almeno 1 PDF
- ✅ Primo PDF deve essere parsabile
- ✅ CF azienda deve essere presente
- ✅ Datore di lavoro deve esistere in anagrafica
- ✅ Tipo documento LIBUNI deve esistere
- ✅ Titolario HR-PAY deve esistere

### Frontend
- ✅ File deve essere ZIP (per importazione libro unico)
- ✅ Conferma utente prima dell'importazione

## 📝 Note Tecniche

### Dipendenze
- **Parser cedolini**: Usa `documenti/parsers/cedolino_parser.py`
  - Estrae: CF azienda, ragione sociale, periodo, anno, mese
  - Estrae: nome/cognome dipendenti
- **Titolario**: Cerca `HR-PAY` o varianti
- **Storage**: ZIP salvato su NAS come file documento

### File Creati/Modificati

**Backend:**
- ✅ `api/v1/documenti/serializers.py` - Aggiunto `ImportaZipLibroUnicoSerializer`
- ✅ `api/v1/documenti/importa_libro_unico.py` - Nuovo file utility
- ✅ `api/v1/documenti/views.py` - Aggiunto endpoint `importa_zip_libro_unico`

**Frontend:**
- ✅ `frontend/src/api/documenti.ts` - Aggiunto `importaZipLibroUnico()`
- ✅ `frontend/src/pages/ImportaCedoliniPage.tsx` - Aggiunto pulsante e handler

## 🧪 Test Suggeriti

### Caso 1: ZIP Nuovo
1. Upload ZIP con 10 cedolini
2. Verifica creazione documento LIBUNI
3. Verifica metadati: titolo, periodo, cliente, note con lista dipendenti

### Caso 2: ZIP Duplicato (duplica)
1. Upload stesso ZIP due volte con azione='duplica'
2. Verifica creazione di 2 documenti LIBUNI distinti

### Caso 3: ZIP Duplicato (sostituisci)
1. Crea documento LIBUNI
2. Upload nuovo ZIP stesso periodo con azione='sostituisci'
3. Verifica sostituzione file e metadati

### Caso 4: ZIP Duplicato (skip)
1. Crea documento LIBUNI
2. Upload nuovo ZIP stesso periodo con azione='skip'
3. Verifica che non venga creato nuovo documento

### Caso 5: Errori
1. ZIP vuoto → Errore "Lo ZIP non contiene file PDF"
2. PDF non parsabile → Errore "Impossibile estrarre dati dal primo PDF"
3. CF azienda mancante → Errore "Datore di lavoro con CF ... non trovato"
4. Tipo LIBUNI mancante → Errore "Tipo documento LIBUNI non configurato"
5. Titolario HR-PAY mancante → Errore "Titolario HR-PAY non trovato"

## 🚀 Deploy

### 1. Backend
```bash
cd /home/sandro/mygest
git add .
git commit -m "feat: importazione ZIP come documento Libro Unico"
./scripts/deploy.sh
```

### 2. Frontend
```bash
cd /home/sandro/mygest/frontend
npm run build
```

### 3. Restart Services
```bash
sudo systemctl restart mygest
sudo systemctl restart nginx
```

## 📚 Riferimenti

- **Parser cedolini**: `documenti/parsers/cedolino_parser.py`
- **Importazione cedolini esistente**: `api/v1/documenti/views.py` - `importa_cedolini_preview/confirm`
- **Tipo documento LIBUNI**: Deve esistere nel database
- **Titolario HR-PAY**: `titolario/migrations/0002_titolario_privato.py`

---

**Data implementazione**: 6 Febbraio 2026  
**Versione**: 1.0  
**Autore**: Sandro Chimenti (con assistenza GitHub Copilot)
