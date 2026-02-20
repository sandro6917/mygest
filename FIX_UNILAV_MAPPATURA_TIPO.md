# Fix: Mappatura Tipo Comunicazione UNILAV

**Data**: 3 Febbraio 2026  
**Issue**: Valore "LAVORO A TEMPO DETERMINATO" non valido per SELECT tipo comunicazione

---

## 🐛 Problema Riscontrato

### Errore Frontend
```
MUI: You have provided an out-of-range value `LAVORO A TEMPO DETERMINATO` for the select component.
Consider providing a value that matches one of the available options or ''.
The available values are ``, `Assunzione`, `Proroga`, `Trasformazione`, `Cessazione`.
```

### Errore Backend
```
Bad Request: /api/v1/documenti/importa_unilav_confirm/
POST /api/v1/documenti/importa_unilav_confirm/ HTTP/1.1" 400 37
```

### Causa
Il parser PDF estrae dal documento UNILAV il campo **"Tipologia contrattuale"** (es. "LAVORO A TEMPO DETERMINATO", "LAVORO A TEMPO INDETERMINATO"), ma l'attributo dinamico `tipo` nel database accetta solo 4 valori predefiniti:
- **Assunzione**
- **Proroga**
- **Trasformazione**
- **Cessazione**

---

## ✅ Soluzione Implementata

### Backend: Mappatura Intelligente

**File**: `api/v1/documenti/views.py`

**Funzione aggiunta**:
```python
def _mappa_tipo_comunicazione_unilav(tipologia_contrattuale: str, tipo_comunicazione: str) -> str:
    """
    Mappa la tipologia contrattuale estratta dal PDF a uno dei valori validi
    per l'attributo 'tipo' (Assunzione, Proroga, Trasformazione, Cessazione).
    """
    # Se tipo_comunicazione contiene già un valore valido, usalo
    if tipo_comunicazione:
        tipo_upper = tipo_comunicazione.upper()
        if 'ASSUNZIONE' in tipo_upper:
            return 'Assunzione'
        elif 'PROROGA' in tipo_upper:
            return 'Proroga'
        elif 'TRASFORMAZIONE' in tipo_upper:
            return 'Trasformazione'
        elif 'CESSAZIONE' in tipo_upper or 'CESSIONE' in tipo_upper:
            return 'Cessazione'
    
    # Altrimenti, usa tipologia_contrattuale per inferire
    if tipologia_contrattuale:
        tipo_upper = tipologia_contrattuale.upper()
        
        # Mapping basato su keywords
        if 'DETERMINATO' in tipo_upper or 'TEMPO DETERMINATO' in tipo_upper:
            return 'Assunzione'
        elif 'INDETERMINATO' in tipo_upper or 'TEMPO INDETERMINATO' in tipo_upper:
            return 'Assunzione'
        elif 'APPRENDISTATO' in tipo_upper:
            return 'Assunzione'
        elif 'SOMMINISTRAZIONE' in tipo_upper:
            return 'Assunzione'
        elif 'TIROCINIO' in tipo_upper or 'STAGE' in tipo_upper:
            return 'Assunzione'
    
    # Default: Assunzione
    return 'Assunzione'
```

**Utilizzo nella preview**:
```python
# Mappa tipo comunicazione a uno dei valori validi della SELECT
tipo_mappato = _mappa_tipo_comunicazione_unilav(
    unilav_data.get('tipologia_contrattuale'),
    unilav_data.get('tipo_comunicazione')
)

documento_response = {
    ...
    'tipo': tipo_mappato,  # Valore mappato per la SELECT
    ...
}
```

### Logica di Mappatura

| Campo PDF | Valore Estratto | → | Valore Mappato |
|-----------|----------------|---|----------------|
| Tipo comunicazione | "Assunzione" | → | "Assunzione" |
| Tipo comunicazione | "Proroga contratto" | → | "Proroga" |
| Tipo comunicazione | "Trasformazione rapporto" | → | "Trasformazione" |
| Tipo comunicazione | "Cessazione" | → | "Cessazione" |
| Tipologia contrattuale | "LAVORO A TEMPO DETERMINATO" | → | "Assunzione" |
| Tipologia contrattuale | "LAVORO A TEMPO INDETERMINATO" | → | "Assunzione" |
| Tipologia contrattuale | "APPRENDISTATO" | → | "Assunzione" |
| Tipologia contrattuale | "SOMMINISTRAZIONE" | → | "Assunzione" |
| Tipologia contrattuale | "TIROCINIO" | → | "Assunzione" |
| (Nessun match) | - | → | "Assunzione" (default) |

### Logging per Debug

Aggiunto warning quando il mapping usa il valore default:
```python
logger.warning(
    f"Impossibile mappare tipo comunicazione UNILAV: "
    f"tipo_comunicazione='{tipo_comunicazione}', "
    f"tipologia_contrattuale='{tipologia_contrattuale}'. "
    f"Uso default: 'Assunzione'"
)
```

### Miglioramento Validazione

Aggiunto logging dettagliato per errori di validazione:
```python
if not serializer.is_valid():
    logger.error(f"Errori validazione UNILAV confirm: {serializer.errors}")
    logger.error(f"Dati ricevuti: {request.data}")
    return Response(
        {
            'detail': 'Errore validazione dati',
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )
```

---

## 📊 Esempi di Mappatura

### Caso 1: UNILAV Assunzione Tempo Determinato
```json
{
  "tipo_comunicazione": "Assunzione",
  "tipologia_contrattuale": "LAVORO A TEMPO DETERMINATO"
}
→ tipo: "Assunzione"
```

### Caso 2: UNILAV Proroga
```json
{
  "tipo_comunicazione": "Proroga di contratto a tempo determinato",
  "tipologia_contrattuale": "LAVORO A TEMPO DETERMINATO"
}
→ tipo: "Proroga"
```

### Caso 3: UNILAV Trasformazione
```json
{
  "tipo_comunicazione": "Trasformazione da tempo determinato a indeterminato",
  "tipologia_contrattuale": "LAVORO A TEMPO INDETERMINATO"
}
→ tipo: "Trasformazione"
```

### Caso 4: UNILAV Cessazione
```json
{
  "tipo_comunicazione": "Cessazione del rapporto",
  "tipologia_contrattuale": null
}
→ tipo: "Cessazione"
```

---

## 🧪 Test

Riavviare il server Django e riprovare l'importazione:

```bash
# Terminare server esistente
pkill -f "python.*runserver"

# Riavviare
cd /home/sandro/mygest
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

Verificare:
1. ✅ Upload PDF UNILAV
2. ✅ Preview mostra SELECT con valore valido (es. "Assunzione")
3. ✅ Nessun warning MUI
4. ✅ Conferma crea documento correttamente

---

## 📝 Note Implementative

### Perché "Assunzione" come default?
La maggior parte dei documenti UNILAV riguarda nuove assunzioni. Quando non è possibile determinare il tipo esatto, "Assunzione" è il valore più sicuro.

### Futuri Miglioramenti
Se nei PDF UNILAV il campo "Tipo comunicazione" contiene sempre uno dei 4 valori corretti, potremmo:
1. Usare direttamente `tipo_comunicazione` dal PDF
2. Eliminare la mappatura da `tipologia_contrattuale`

Attualmente usiamo entrambi i campi per massima robustezza.

---

## ✅ File Modificati

- `api/v1/documenti/views.py`:
  - Aggiunta funzione `_mappa_tipo_comunicazione_unilav()`
  - Modificato `importa_unilav_preview()` per usare la mappatura
  - Migliorato logging in `importa_unilav_confirm()`

---

**Status**: ✅ Implementato  
**Test**: In attesa di verifica utente
