# Fix: UNILAV file_path vs file_temp_path Mismatch

**Data**: 3 Febbraio 2026  
**Issue**: 400 Bad Request - Campo 'file_path' obbligatorio mancante

---

## 🐛 Problema Riscontrato

### Errore Log Backend
```
Errori validazione UNILAV confirm: {'file_path': [ErrorDetail(string='Campo obbligatorio.', code='required')]}
Dati ricevuti: {
  ...
  'file_temp_path': '/tmp/tmpaqx1qlpi/UNILAV_1700026200007595.pdf'
}
Bad Request: /api/v1/documenti/importa_unilav_confirm/
```

### Causa
- **Frontend**: Invia `file_temp_path` nel payload JSON
- **Backend**: Serializer si aspetta `file_path` (campo required=True)
- **Mismatch**: Nome campo diverso → validazione fallisce con 400 Bad Request

---

## ✅ Soluzione Implementata

### Modifica al Serializer

**File**: `api/v1/documenti/serializers.py`

**Prima** (rigido, solo file_path):
```python
class UnilavImportConfirmSerializer(serializers.Serializer):
    datore = UnilavAnagraficaSerializer(required=True)
    lavoratore = UnilavAnagraficaSerializer(required=True)
    documento = UnilavDocumentoSerializer(required=True)
    
    # Solo file_path accettato
    file_path = serializers.CharField(max_length=500, required=True,
                                      help_text="Percorso temporaneo del file PDF caricato")
    
    def validate(self, attrs):
        if datore.get('codice_fiscale') == lavoratore.get('codice_fiscale'):
            raise serializers.ValidationError(...)
        return attrs
```

**Dopo** (flessibile, accetta entrambi):
```python
class UnilavImportConfirmSerializer(serializers.Serializer):
    datore = UnilavAnagraficaSerializer(required=True)
    lavoratore = UnilavAnagraficaSerializer(required=True)
    documento = UnilavDocumentoSerializer(required=True)
    
    # Accetta sia file_path che file_temp_path
    file_path = serializers.CharField(max_length=500, required=False,
                                      help_text="Percorso temporaneo del file PDF caricato")
    file_temp_path = serializers.CharField(max_length=500, required=False,
                                           help_text="Percorso temporaneo del file PDF caricato (alternativo)")
    
    def validate(self, attrs):
        datore = attrs.get('datore', {})
        lavoratore = attrs.get('lavoratore', {})
        
        if datore.get('codice_fiscale') == lavoratore.get('codice_fiscale'):
            raise serializers.ValidationError(...)
        
        # NUOVO: Verifica che almeno uno dei due campi sia presente
        if not attrs.get('file_path') and not attrs.get('file_temp_path'):
            raise serializers.ValidationError({
                'file_path': 'Specificare file_path o file_temp_path'
            })
        
        # NUOVO: Normalizza - usa file_temp_path se presente, altrimenti file_path
        if attrs.get('file_temp_path'):
            attrs['file_path'] = attrs['file_temp_path']
        
        return attrs
```

### Logica di Normalizzazione

Il metodo `validate()` ora:

1. **Verifica**: Almeno uno dei due campi (`file_path` o `file_temp_path`) deve essere presente
2. **Normalizza**: Se presente `file_temp_path`, lo copia in `file_path`
3. **Garantisce**: La view `importa_unilav_confirm()` riceve sempre `validated_data['file_path']`

### Benefici

- ✅ **Retrocompatibilità**: Se il frontend invia `file_path`, funziona come prima
- ✅ **Compatibilità attuale**: Se il frontend invia `file_temp_path`, viene normalizzato
- ✅ **Validazione**: Almeno uno dei due campi deve essere presente
- ✅ **Pulizia**: La view continua a usare `file_path` senza modifiche

---

## 🧪 Test

### Payload Frontend (attuale)
```json
{
  "datore": { ... },
  "lavoratore": { ... },
  "documento": { ... },
  "file_temp_path": "/tmp/tmpaqx1qlpi/UNILAV_1700026200007595.pdf"
}
```

### Serializer Processing
1. `file_temp_path` presente → ✅ passa validazione
2. Normalizzazione: `attrs['file_path'] = attrs['file_temp_path']`
3. View riceve: `validated_data['file_path'] = '/tmp/tmpaqx1qlpi/UNILAV_1700026200007595.pdf'`

### Risultato Atteso
✅ Nessun errore 400 Bad Request  
✅ Documento creato con file PDF allegato  
✅ Voce titolario intestata al dipendente  
✅ Attributi dinamici salvati correttamente  

---

## 📝 Note

### Perché il mismatch?
Il frontend (React) probabilmente usa il nome `file_temp_path` per chiarezza semantica (indica che è un path temporaneo), mentre il backend originale usava `file_path` generico.

### Alternativa (non implementata)
Modificare il frontend per inviare `file_path` invece di `file_temp_path`. 

**Pro**: Backend semplice, nessuna normalizzazione  
**Contro**: Richiede modifica frontend + rischio regressioni  

### Scelta
Modificare il serializer per accettare entrambi → soluzione più robusta e senza modifiche frontend.

---

## ✅ File Modificati

- `api/v1/documenti/serializers.py`:
  - Reso `file_path` required=False
  - Aggiunto `file_temp_path` required=False  
  - Aggiunta validazione in `validate()` per verificare almeno uno presente
  - Aggiunta normalizzazione: `file_temp_path` → `file_path`

---

**Status**: ✅ Implementato  
**Test**: In attesa di verifica utente (riavvio server richiesto)
