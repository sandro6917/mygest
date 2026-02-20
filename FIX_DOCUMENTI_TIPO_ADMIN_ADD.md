# Fix: ValueError su creazione DocumentiTipo in Admin

## 🐛 Problema

Quando si tentava di creare un nuovo `DocumentiTipo` dall'admin Django, si verificava l'errore:

```
ValueError: Model instances passed to related filters must be saved.
```

**URL**: `http://localhost:8000/admin/documenti/documentitipo/add/`  
**Django Version**: 5.2.8  
**Exception Location**: `django/db/models/fields/related_lookups.py`, line 20

## 🔍 Causa

Il problema si verificava nel flusso di salvataggio dell'admin:

1. `HelpDataAdminForm.save()` chiamava `HelpDataBuilder` **PRIMA** di salvare l'istanza
2. `HelpDataBuilder` tentava di fare query su `AttributoDefinizione.objects.filter(tipo_documento=self.tipo)`
3. Poiché `self.tipo` non aveva ancora un `pk`, Django sollevava l'errore

### Stack trace del problema

```python
# documenti/help_forms.py (PRIMA della fix)
def save(self, commit=True):
    instance = super().save(commit=False)
    help_data = self._build_help_data_from_fields()
    
    # ❌ ERRORE: instance non ha ancora pk!
    builder = HelpDataBuilder(instance)
    technical_sections = builder.build_all_technical_sections()
    
    help_data.update(technical_sections)
    instance.help_data = help_data
    
    if commit:
        instance.save()  # Troppo tardi!
```

## ✅ Soluzione

### 1. Fix nel `HelpDataAdminForm.save()`

**File**: `documenti/help_forms.py`

Modificato il metodo `save()` per salvare l'istanza **PRIMA** di generare le sezioni tecniche:

```python
def save(self, commit=True):
    """Salva ricostruendo help_data dai campi del form."""
    instance = super().save(commit=False)
    
    # Ricostruisci help_data dalle sezioni discorsive
    help_data = self._build_help_data_from_fields()
    
    # ✅ Per nuove istanze, salva prima l'oggetto base
    if not instance.pk and commit:
        instance.help_data = help_data
        instance.save()
    
    # Ora possiamo generare le sezioni tecniche (richiede instance.pk)
    builder = HelpDataBuilder(instance)
    technical_sections = builder.build_all_technical_sections()
    
    # Merge: discorsive + tecniche
    help_data.update(technical_sections)
    instance.help_data = help_data
    
    if commit:
        instance.save()  # Aggiorna con sezioni tecniche
    
    return instance
```

### 2. Protezione nel `HelpDataBuilder`

**File**: `documenti/help_builder.py`

Aggiunta protezione in tutti i metodi che fanno query su `AttributoDefinizione`:

#### `build_attributi_dinamici()`
```python
def build_attributi_dinamici(self) -> Dict[str, Any]:
    from documenti.models import AttributoDefinizione
    
    # ✅ Se l'istanza non è salvata, ritorna struttura vuota
    if not self.tipo.pk:
        return {
            'disponibili': [],
            'pattern_code_examples': [],
        }
    
    attributi = AttributoDefinizione.objects.filter(
        tipo_documento=self.tipo
    ).order_by('ordine', 'codice')
    # ...
```

#### `build_pattern_codice()`
```python
# Aggiungi placeholder da attributi dinamici
from documenti.models import AttributoDefinizione

# ✅ Solo se l'istanza è salvata
if self.tipo.pk:
    attributi = AttributoDefinizione.objects.filter(tipo_documento=self.tipo)
    for attr in attributi:
        placeholder_map[f'{{attr:{attr.codice}}}'] = (
            f'Valore attributo "{attr.nome}"'
        )
        # ...
```

#### `build_campi_obbligatori()`
```python
# Aggiungi attributi required (solo se istanza salvata)
if self.tipo.pk:
    attributi_req = AttributoDefinizione.objects.filter(
        tipo_documento=self.tipo,
        required=True
    )
    sempre.extend([attr.nome for attr in attributi_req])
```

## 🧪 Testing

Per testare la fix:

1. Vai su `http://localhost:8000/admin/documenti/documentitipo/add/`
2. Compila i campi obbligatori:
   - Codice: `TEST`
   - Nome: `Test Documento`
3. Clicca "Salva"
4. ✅ Il tipo documento viene creato correttamente
5. ✅ Le sezioni tecniche di `help_data` vengono generate automaticamente

### Comportamento atteso

1. **Primo save**: Salva l'istanza con solo i dati discorsivi (descrizione, quando_usare, ecc.)
2. **Generazione tecnica**: Genera le sezioni tecniche accedendo agli attributi correlati
3. **Secondo save**: Aggiorna l'istanza con le sezioni tecniche complete

## 📝 Note Tecniche

### Perché serve salvare due volte?

Quando si crea un nuovo `DocumentiTipo`:
1. Gli `AttributoDefinizione` inline possono essere aggiunti contemporaneamente
2. Ma Django li salva **DOPO** il modello principale
3. Quindi al primo save non ci sono ancora attributi da leggere
4. Al secondo save, gli attributi sono già salvati e possono essere inclusi

### Pattern generale

Questo pattern è utile ogni volta che si ha:
- Un form che genera dati basati su relazioni
- Inline che vengono salvati dopo il modello principale
- Necessità di popolare campi calcolati che dipendono da oggetti correlati

## 🎯 Impatto

- ✅ Risolve il bug di creazione `DocumentiTipo` in admin
- ✅ Mantiene la generazione automatica delle sezioni tecniche
- ✅ Nessun impatto su modifiche di tipi esistenti (hanno già `pk`)
- ✅ Protegge il builder da istanze non salvate

## 🔄 Commit

```bash
git add documenti/help_forms.py documenti/help_builder.py
git commit -m "fix(documenti): risolve ValueError su creazione DocumentiTipo in admin

- Salva istanza prima di generare sezioni tecniche in HelpDataAdminForm
- Aggiunge protezioni pk in HelpDataBuilder per evitare query su istanze non salvate
- Risolve: ValueError 'Model instances passed to related filters must be saved'
"
```

## 📚 Riferimenti

- Django Model Forms: https://docs.djangoproject.com/en/5.2/topics/forms/modelforms/
- Admin Inlines: https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.InlineModelAdmin
- Related Lookups: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#field-lookups

---

**Fix applicata**: 17 Febbraio 2026  
**Versione Django**: 5.2.8  
**By**: Sandro Chimenti
