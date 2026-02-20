# Modifica al File Storage - Copia o Sposta File

## Descrizione
Implementata la funzionalità che permette all'utente di scegliere se **copiare** o **spostare** un file quando viene associato ad un documento nel gestionale.

## Modifiche Effettuate

### 1. Forms (`documenti/forms.py`)

#### `DocumentoDinamicoForm`
- **Aggiunto campo `file_operation`**: Campo radio che permette di scegliere tra:
  - `copy`: Copia il file mantenendo l'originale
  - `move`: Sposta il file eliminando l'originale dalla directory di origine
- **Valore predefinito**: `copy` (per retrocompatibilità)
- **Widget**: `RadioSelect` per una scelta chiara e visibile
- **Modificato metodo `save()`**: Passa l'operazione scelta al modello tramite l'attributo `_file_operation`

#### `DocumentoForm`
- Applicate le stesse modifiche per mantenere coerenza in tutte le interfacce

### 2. Models (`documenti/models.py`)

#### Metodo `_move_file_into_archivio()`
- **Modificato comportamento**: Ora gestisce sia la copia che lo spostamento del file
- **Implementazione**:
  - Legge l'attributo `_file_operation` dall'istanza (default: `copy`)
  - Copia sempre il file nella destinazione finale
  - **Se `file_operation == 'move'`**: Elimina il file originale dopo la copia
  - **Se `file_operation == 'copy'`**: Mantiene il file originale
- **Logging migliorato**: Log differenziati per operazioni di copia e spostamento

### 3. Templates

#### `documenti/templates/documenti/nuovo_dinamico.html`
- Il campo `file_operation` viene visualizzato subito dopo il campo `file`
- Stile con background grigio per evidenziare l'opzione
- Help text descrittivo per guidare l'utente

#### `documenti/templates/documenti/modifica_dinamico.html`
- Applicate le stesse modifiche del template `nuovo_dinamico.html`

## Comportamento

### Scenario 1: Copia (default)
1. L'utente carica un file tramite il form
2. Seleziona "Copia il file (mantieni l'originale)"
3. Il sistema copia il file nella directory del gestionale
4. Il file originale **rimane** nella sua posizione originale

### Scenario 2: Sposta
1. L'utente carica un file tramite il form
2. Seleziona "Sposta il file (elimina l'originale)"
3. Il sistema copia il file nella directory del gestionale
4. Il file originale **viene eliminato** dalla sua posizione originale

## Retrocompatibilità
- Il valore predefinito è `copy`, garantendo che il comportamento esistente non venga alterato
- Se il campo `file_operation` non viene specificato, il sistema utilizza automaticamente la modalità copia
- I documenti esistenti non sono influenzati dalle modifiche

## Note Tecniche
- L'operazione viene passata tramite un attributo temporaneo `_file_operation` sull'istanza del modello
- Il metodo `_move_file_into_archivio()` gestisce entrambe le operazioni in modo sicuro con logging appropriato
- Gestione errori: se l'eliminazione del file originale fallisce (in modalità move), viene registrato un warning nel log ma il salvataggio del documento prosegue

## Test
Per testare la funzionalità:
1. Accedere alla sezione "Documenti > Nuovo"
2. Selezionare un tipo di documento
3. Caricare un file
4. Scegliere l'operazione desiderata (Copia/Sposta)
5. Salvare il documento
6. Verificare che il file sia stato copiato/spostato come richiesto

## File Modificati
- `documenti/forms.py`
- `documenti/models.py`
- `documenti/templates/documenti/nuovo_dinamico.html`
- `documenti/templates/documenti/modifica_dinamico.html`
