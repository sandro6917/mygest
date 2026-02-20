# Fix Widget Autocomplete Anagrafica - Frontend React

## Problema
Nel frontend React, quando si crea o modifica un documento con attributi dinamici configurati come widget anagrafica, veniva mostrato un semplice input numerico invece di un componente autocomplete per la selezione delle anagrafiche.

## Soluzione Implementata

### 1. **Aggiornamento Tipo TypeScript** (`frontend/src/types/documento.ts`)

Aggiunto il campo `widget` all'interfaccia `AttributoDefinizione`:

```typescript
export interface AttributoDefinizione {
  id: number;
  tipo_documento: number;
  codice: string;
  nome: string;
  tipo_dato: 'string' | 'int' | 'decimal' | 'date' | 'datetime' | 'bool' | 'choice';
  widget?: string;  // ← NUOVO CAMPO
  scelte?: string;
  obbligatorio: boolean;
  ordine: number;
  help_text: string;
}
```

### 2. **Modifica Componente Form** (`frontend/src/pages/DocumentoFormPage.tsx`)

#### Import del componente AnagraficaAutocomplete:
```typescript
import { AnagraficaAutocomplete, type AnagraficaOption } from '@/components/AnagraficaAutocomplete';
```

#### Nuovo stato per le anagrafiche selezionate:
```typescript
const [anagraficheAttributi, setAnagraficheAttributi] = useState<Record<string, AnagraficaOption | null>>({});
```

#### Rendering condizionale degli attributi:
```typescript
{attr.tipo_dato === 'int' && 
 attr.widget && ['anagrafica', 'fk_anagrafica', 'anag'].includes(attr.widget.toLowerCase()) ? (
  <AnagraficaAutocomplete
    value={anagraficheAttributi[attr.codice] || null}
    onChange={(anagrafica) => {
      setAnagraficheAttributi(prev => ({
        ...prev,
        [attr.codice]: anagrafica
      }));
      setFormData((prev) => ({
        ...prev,
        [`attr_${attr.codice}`]: anagrafica?.id || '',
      }));
    }}
    required={attr.obbligatorio}
    placeholder={`Seleziona ${attr.nome.toLowerCase()}...`}
  />
) : /* ...altri tipi di input... */}
```

#### Caricamento anagrafiche in modalità edit:
Quando si modifica un documento esistente, le anagrafiche vengono caricate dall'API:
```typescript
// Carica l'anagrafica dal server
apiClient.get(`/anagrafiche/${anagraficaId}/`)
  .then(response => {
    setAnagraficheAttributi(prev => ({
      ...prev,
      [codice]: response.data
    }));
  })
```

### 3. **Aggiornamento Serializer API** (`api/v1/documenti/serializers.py`)

Aggiunto il campo `widget` al serializer:

```python
class AttributoDefinizioneSerializer(serializers.ModelSerializer):
    obbligatorio = serializers.BooleanField(source='required', read_only=True)
    scelte = serializers.CharField(source='choices', read_only=True)
    
    class Meta:
        model = AttributoDefinizione
        fields = [
            'id', 'tipo_documento', 'codice', 'nome', 'tipo_dato',
            'widget',  # ← NUOVO CAMPO
            'scelte', 'obbligatorio', 'ordine', 'help_text'
        ]
```

## Risultato

Ora quando si crea o modifica un documento con attributi configurati come widget anagrafica:

✅ Viene mostrato il componente `AnagraficaAutocomplete` con funzionalità di ricerca
✅ L'utente può cercare anagrafiche per nome, codice fiscale o partita IVA
✅ Vengono mostrate informazioni aggiuntive (tipo, contatti) nell'autocomplete
✅ Il valore selezionato viene salvato correttamente come ID dell'anagrafica
✅ In modalità edit, l'anagrafica esistente viene caricata e visualizzata correttamente

## File Modificati

- `frontend/src/types/documento.ts`: Aggiunto campo `widget`
- `frontend/src/pages/DocumentoFormPage.tsx`: Implementato rendering condizionale con AnagraficaAutocomplete
- `api/v1/documenti/serializers.py`: Aggiunto campo `widget` al serializer

## Test

Per testare, creare un documento di tipo:
- **Contratto di Lavoro** (CT_LAV) - campo "Dipendente"
- **Fattura di acquisto** (FA) - campo "Fornitore"
- **Atto Notarile** (ATTNOT) - campi "Notaio", "Parte", "Controparte"
- **Contratto di locazione** (LOC) - campi "Parte", "Controparte"

In tutti questi casi, i campi anagrafica mostreranno l'autocomplete invece di un input numerico.
