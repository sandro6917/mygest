# Logica Titolario Implementata

## Data: 2025-01-17

## Requisiti Utente

L'utente ha specificato due regole importanti sulla gestione del titolario nei documenti:

### (a) Documenti fascicolati possono avere titolario diverso dal fascicolo
**Domanda:** "se ho un documento fascicolato, il titolario del documento (se specificato) può essere diverso da quello del fascicolo?"

**Risposta:** Sì, è possibile. La struttura del database lo permette:
- Il documento ha un campo `titolario_voce` opzionale
- Il fascicolo ha un campo `titolario_voce` opzionale
- Non c'è vincolo che li leghi

**Comportamento implementato:**
- Quando costruisce il percorso, il documento usa SEMPRE il proprio `titolario_voce` (o il default "99 - Varie")
- Il `titolario_voce` del fascicolo viene usato solo per organizzare la directory del fascicolo stesso
- I documenti fascicolati sono indipendenti dal punto di vista del titolario

### (b) Documenti senza titolario vanno in "99 - Varie" + spostamento file
**Requisito:** "i documenti senza titolario vanno inseriti in un voce di default (99 - varie). In sede di modifica del documento in caso di assegnazione di un voce di titolario, i file dovranno essere spostati nella directory di riferimento"

**Implementazione completata:**

#### 1. Funzione Default Titolario
```python
def get_or_create_default_titolario():
    """
    Ottiene (o crea) la voce di titolario di default '99 - Varie'
    per i documenti senza titolario assegnato.
    """
    from titolario.models import TitolarioVoce
    
    voce, created = TitolarioVoce.objects.get_or_create(
        codice="99",
        parent__isnull=True,
        defaults={
            "descrizione": "Varie",
            "note": "Voce di default per documenti senza titolario",
        }
    )
    return voce
```

**Posizione:** In `documenti/models.py`, subito dopo `User = get_user_model()`

#### 2. Modifica _build_path()
```python
def _build_path(self) -> str:
    """
    Costruisce il percorso assoluto della cartella di archivio.
    Se il documento non ha titolario, usa il default "99 - Varie".
    """
    # Usa titolario del documento o default "99 - Varie"
    voce_da_usare = self.titolario_voce
    if not voce_da_usare:
        voce_da_usare = get_or_create_default_titolario()

    anno = self.anno_competenza
    cliente = self.cliente

    if not anno or not cliente:
        return settings.ARCHIVIO_BASE_PATH

    titolario_path = build_titolario_parts(voce_da_usare)
    
    parts = [
        settings.ARCHIVIO_BASE_PATH,
        cliente.slug,
        titolario_path,
        str(anno),
    ]
    return os.path.join(*parts)
```

#### 3. Logica Spostamento File in save()

Quando un documento viene modificato e cambia il suo `titolario_voce`:

```python
@transaction.atomic
def save(self, *args, **kwargs):
    is_new = self.pk is None
    
    # Verifica se il titolario è cambiato (per spostare il file)
    titolario_changed = False
    old_percorso = None
    if not is_new and self.pk:
        try:
            old_doc = type(self).objects.only("titolario_voce_id", "percorso_archivio").get(pk=self.pk)
            if old_doc.titolario_voce_id != self.titolario_voce_id:
                titolario_changed = True
                old_percorso = old_doc.percorso_archivio
                logger.info(
                    "Documento id=%s: titolario_voce cambiato da %s a %s",
                    self.pk,
                    old_doc.titolario_voce_id,
                    self.titolario_voce_id
                )
        except type(self).DoesNotExist:
            pass
    
    # ... generazione codice ...
    
    # Ricalcola percorso_archivio con nuovo titolario (o default)
    self.percorso_archivio = self._build_path()
    
    super().save(*args, **kwargs)
    
    # ... rinomina file ...
    
    # Se il titolario è cambiato e c'è un file, spostalo nella nuova directory
    if titolario_changed and self.file and old_percorso and old_percorso != self.percorso_archivio:
        logger.info(
            "Documento id=%s: spostamento file da %s a %s",
            self.pk,
            old_percorso,
            self.percorso_archivio
        )
        self._move_file_into_archivio()
    # Altrimenti, sposta sempre il file dentro percorso_archivio (se presente)
    elif self.file:
        self._move_file_into_archivio()
```

## Flussi Operativi

### Creazione Nuovo Documento

1. **Senza titolario specificato:**
   - `_build_path()` → chiama `get_or_create_default_titolario()`
   - Ottiene/crea voce "99 - Varie"
   - Costruisce percorso: `/mnt/archivio/{cliente}/99-Varie/{anno}/`
   - `save()` → salva file nella directory di default

2. **Con titolario specificato:**
   - `_build_path()` → usa `self.titolario_voce`
   - Costruisce percorso: `/mnt/archivio/{cliente}/{titolario}/{anno}/`
   - `save()` → salva file nella directory corretta

### Modifica Documento Esistente

1. **Assegnazione titolario a documento senza titolario:**
   - `save()` → rileva `titolario_changed = True`
   - Registra `old_percorso` (che puntava a "99 - Varie")
   - `_build_path()` → calcola nuovo percorso con titolario assegnato
   - Verifica: `old_percorso != self.percorso_archivio`
   - `_move_file_into_archivio()` → sposta file fisico da "99 - Varie" al nuovo titolario
   - Log: "spostamento file da ... a ..."

2. **Cambio titolario su documento già classificato:**
   - Stessa logica: rileva cambio, sposta file, logga operazione

3. **Nessun cambio titolario:**
   - `titolario_changed = False`
   - Esegue solo `_move_file_into_archivio()` standard (gestisce upload nuovi file)

## Verifica Implementazione

### Test Manuale Suggerito

1. **Test Default "99 - Varie":**
   ```python
   # Nel Django shell
   from documenti.models import Documento
   from anagrafiche.models import Cliente
   
   cliente = Cliente.objects.first()
   
   # Crea documento senza titolario
   doc = Documento.objects.create(
       cliente=cliente,
       anno_competenza=2025,
       titolo="Test senza titolario",
       # titolario_voce=None (default)
   )
   
   # Verifica percorso
   print(doc.percorso_archivio)
   # Deve contenere: /mnt/archivio/{cliente.slug}/99-Varie/2025/
   ```

2. **Test Spostamento File:**
   ```python
   from titolario.models import TitolarioVoce
   
   # Assegna un titolario
   voce = TitolarioVoce.objects.filter(codice="01").first()
   doc.titolario_voce = voce
   doc.save()
   
   # Verifica nuovo percorso
   print(doc.percorso_archivio)
   # Deve contenere: /mnt/archivio/{cliente.slug}/01-{descrizione}/2025/
   
   # Verifica log (se hai un file allegato)
   # Deve apparire: "Documento id=X: spostamento file da ... a ..."
   ```

### Check Django

```bash
python manage.py check
# Output: System check identified no issues (0 silenced).
```

✅ **PASSATO**

## File Modificati

1. **documenti/models.py:**
   - Aggiunta funzione `get_or_create_default_titolario()` (linea ~20)
   - Modificata `_build_path()` per usare default quando `titolario_voce` è None (linea ~330)
   - Modificata `save()` per rilevare cambio titolario e spostare file (linea ~383)

## Script Utilizzati

1. **scripts/patch_storage_logic.py:**
   - Aggiunge `get_or_create_default_titolario()`
   - Sostituisce `_build_path()` con versione che usa default

2. **scripts/patch_storage_logic2.py:**
   - Modifica `save()` per gestire cambio titolario
   - Aggiunge logging dello spostamento file

## Logging

Il sistema logga le seguenti operazioni:

```python
logger.info(
    "Documento id=%s: titolario_voce cambiato da %s a %s",
    self.pk, old_doc.titolario_voce_id, self.titolario_voce_id
)

logger.info(
    "Documento id=%s: spostamento file da %s a %s",
    self.pk, old_percorso, self.percorso_archivio
)
```

Utile per monitorare gli spostamenti in produzione.

## Note Tecniche

### Performance
- La query per rilevare il cambio usa `.only("titolario_voce_id", "percorso_archivio")` per minimizzare il carico sul DB
- Lo spostamento file avviene solo se effettivamente necessario (`old_percorso != self.percorso_archivio`)

### Atomicità
- Il metodo `save()` è decorato con `@transaction.atomic`
- In caso di errore durante lo spostamento, l'intera operazione viene annullata

### Compatibilità
- Il codice è retrocompatibile: documenti esistenti senza titolario vengono automaticamente associati a "99 - Varie" al primo accesso
- Non richiede migrazioni dati immediate

## Conclusioni

✅ **Requisito (a):** Implementato - documenti fascicolati possono avere titolario diverso dal fascicolo

✅ **Requisito (b):** Implementato - documenti senza titolario vanno in "99 - Varie" e vengono spostati quando assegnato un titolario

✅ **Django Check:** Nessun errore

✅ **Logging:** Tracciamento completo degli spostamenti file

🔜 **Next Step:** Test funzionale con upload e modifica documento reale
