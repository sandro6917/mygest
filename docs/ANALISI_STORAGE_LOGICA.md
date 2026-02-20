# Analisi Struttura Storage - Fascicoli e Documenti

## Data Analisi: 17 Novembre 2025

---

## 🎯 Logica Attesa (Requisiti)

La struttura delle directory dovrebbe seguire questa gerarchia:

1. **Cliente** (codice CLI)
2. **Albero voce di classificazione del titolario**
3. **Periodo di riferimento** (anno)

### Comportamento Atteso:

**FASCICOLI:**
- Viene creata **solo la directory** (senza file)
- Percorso: `ARCHIVIO_BASE_PATH/CLI/voce_titolario_path/anno/`

**DOCUMENTI:**
- **CON fascicolo:** Il file viene rinominato e salvato nella directory del fascicolo
- **SENZA fascicolo:** Il file viene rinominato e salvato in: `ARCHIVIO_BASE_PATH/CLI/voce_titolario_doc/anno/`
- Rinominazione secondo il pattern configurato in `DocumentiTipo.nome_file_pattern`

---

## ✅ Analisi Codice Attuale

### 1. FASCICOLI (`fascicoli/models.py`)

#### 1.1 Funzione `build_archivio_dir_abs()` (linea ~167)

```python
def build_archivio_dir_abs(self) -> str:
    """Percorso ASSOLUTO dove vive il fascicolo sul NAS (unificato con Documento)."""
    cli_code = self._cliente_code(self.cliente)
    parts = [p.replace(os.sep, "-") for p in self._titolario_parts()]
    return ensure_archivio_path(cli_code, parts, self.anno)
```

**✅ CORRETTO:** Costruisce il percorso seguendo la logica richiesta.

#### 1.2 Funzione `_titolario_parts()` (linea ~117)

```python
def _titolario_parts(self) -> List[str]:
    return build_titolario_parts(self.titolario_voce) if self.titolario_voce_id else []
```

Utilizza la funzione utility in `fascicoli/utils.py`

#### 1.3 Salvataggio Fascicolo (metodo `save()`, linea ~170-213)

```python
def save(self, *args, **kwargs):
    # ... logica di creazione codice ...
    
    dest_dir = self.build_archivio_dir_abs()
    
    def _apply_fs():
        os.makedirs(dest_dir, exist_ok=True)  # ✅ Crea SOLO la directory
        type(self).objects.filter(pk=self.pk).update(path_archivio=dest_dir)
    transaction.on_commit(_apply_fs)
```

**✅ CORRETTO:** Crea **solo la directory** senza copiare file.

### 2. UTILITY TITOLARIO (`fascicoli/utils.py`)

#### 2.1 Funzione `ensure_archivio_path()` (linea ~6)

```python
def ensure_archivio_path(cliente_code: str, titolario_path_parts: list[str], anno: int | None = None) -> str:
    """
    Crea (se non esistono) le directory dell'archivio cliente/titolario.
    
    Esempio:
        cliente_code = "ROSSIM"
        titolario_path_parts = ["03 - Amministrazione", "03.01 - Fatturazione clienti", ...]
        anno = 2025
    Restituisce:
        /srv/archivio/ROSSIM/03 - Amministrazione/.../03.01.02 - Fatture ricevute/2025
    """
    base = getattr(settings, "ARCHIVIO_BASE_PATH", "/srv/archivio")
    parts = [base, cliente_code] + titolario_path_parts
    if anno:
        parts.append(str(anno))
    path = os.path.join(*parts)
    os.makedirs(path, exist_ok=True)
    return path
```

**✅ CORRETTO:** Implementa perfettamente la gerarchia:
- `ARCHIVIO_BASE_PATH/cliente/voce1/voce2/.../anno/`

#### 2.2 Funzione `build_titolario_parts()` (linea ~24)

```python
def build_titolario_parts(voce) -> List[str]:
    """
    Ritorna la lista delle parti di path dall'ultima voce fino alla radice.
    Formato: "<CODICE> - <TITOLO>" per ogni livello.
    """
    parts: List[str] = []
    node = voce
    while node:
        parts.insert(0, f"{node.codice} - {getattr(node, 'titolo', '')}")
        node = getattr(node, "parent", None)
    return parts
```

**✅ CORRETTO:** Costruisce l'albero completo del titolario dalla foglia alla radice.

### 3. DOCUMENTI (`documenti/models.py`)

#### 3.1 Funzione `_build_path()` (linea ~229)

```python
def _build_path(self) -> str:
    """Percorso ASSOLUTO del contenitore del documento nel NAS."""
    # 1) Path "del documento" (in base al suo titolario, se presente)
    cli_code = self._cliente_code(self.cliente)
    doc_parts = build_titolario_parts(self.titolario_voce) if self.titolario_voce_id else []
    doc_abs = ensure_archivio_path(cli_code, doc_parts, self.data_documento.year)
    
    # 2) Se legato a un fascicolo, confronta con il path del fascicolo
    if self.fascicolo_id:
        fasc_abs = (self.fascicolo.path_archivio or "").strip()
        # Usa il path fascicolo solo se esiste e coincide col path del documento
        try:
            same = bool(fasc_abs) and os.path.normpath(fasc_abs) == os.path.normpath(doc_abs)
            exists = bool(fasc_abs) and os.path.isdir(fasc_abs)
        except Exception:
            same, exists = False, False
        if same and exists:
            return fasc_abs
    # 3) Default: usa il path calcolato per il documento
    return doc_abs
```

**⚠️ PROBLEMA POTENZIALE:** 
- Il documento calcola il proprio path basandosi sul `self.titolario_voce` del documento
- Confronta con il path del fascicolo
- Usa il path del fascicolo SOLO se coincide

**Casistica problematica:**
Se `documento.titolario_voce != fascicolo.titolario_voce`, il documento viene salvato in una directory diversa da quella del fascicolo!

#### 3.2 Rinominazione File (metodo `_rename_file_if_needed()`, linea ~263)

```python
def _rename_file_if_needed(self, original_name: str, only_new: bool):
    if not self.file:
        return
    if only_new and not self._state.adding:
        return
    
    desired = build_document_filename(self, original_name)
    
    # cartella finale RELATIVA dentro ARCHIVIO_BASE_PATH
    rel_dest_dir = os.path.relpath(self.percorso_archivio, settings.ARCHIVIO_BASE_PATH)
    # ...
```

**✅ CORRETTO:** Utilizza `build_document_filename()` che applica il pattern configurato.

#### 3.3 Spostamento File (metodo `_move_file_into_archivio()`, linea ~319)

```python
def _move_file_into_archivio(self):
    """
    Sposta il file dallo tmp dello storage alla cartella finale 
    calcolata da percorso_archivio.
    """
    if not self.file:
        return
    
    storage = self.file.storage
    current_name = self.file.name
    rel_dest_dir = os.path.relpath(self.percorso_archivio, settings.ARCHIVIO_BASE_PATH).lstrip("./")
    desired_base = build_document_filename(self, os.path.basename(current_name))
    target_rel = os.path.normpath(os.path.join(rel_dest_dir, desired_base))
    # ...
    # Copia e sposta il file
```

**✅ CORRETTO:** Sposta il file nella directory calcolata da `percorso_archivio`.

#### 3.4 Salvataggio Documento (metodo `save()`, linea ~360)

```python
@transaction.atomic
def save(self, *args, **kwargs):
    is_new = self.pk is None
    original_name = None
    if self.file and hasattr(self.file, "name"):
        original_name = os.path.basename(self.file.name)
    
    if is_new and not self.codice:
        seq = self._next_seq()
        self.codice = self._generate_codice(seq)
    
    # percorso assoluto su /mnt/archivio
    self.percorso_archivio = self._build_path()
    
    super().save(*args, **kwargs)
    
    # rinomina/sposta il file
    if self.file and original_name:
        self._rename_file_if_needed(original_name, only_new=True)
    
    # Sposta sempre il file dentro percorso_archivio
    if self.file:
        self._move_file_into_archivio()
```

**✅ CORRETTO:** Esegue tutte le operazioni nell'ordine corretto.

### 4. GENERAZIONE NOME FILE (`documenti/utils.py`)

#### 4.1 Funzione `build_document_filename()` (linea ~49)

```python
def build_document_filename(doc: Any, original_name: str) -> str:
    """
    Costruisce il nome file finale in base a DocumentiTipo.nome_file_pattern.
    Token supportati:
      - {id}, {tipo.codice}
      - {data_documento:%Y%m%d}
      - {slug:descrizione}
      - {attr:<codice>} e {attr:<codice>:%Y%m%d}
      - {uattr:<codice>} -> inserisce "_<valore>" solo se esiste
      - {attrobj:<attr>:<app>:<model>:<field>}
      - {upper:TEXT} / {lower:TEXT}
    """
    base, ext = os.path.splitext(original_name or "")
    ext = ext or ".bin"
    
    pattern = (getattr(doc.tipo, "nome_file_pattern", "") or "").strip()
    if not pattern:
        return f"{(doc.codice or 'DOC')}{ext}"
    
    # ... elaborazione pattern con regex ...
    
    name = _token_rx.sub(repl, pattern).strip().strip("_- ")
    if not name:
        name = (doc.codice or "DOC")
    return f"{name}{ext}"
```

**✅ CORRETTO:** Sistema flessibile e completo di pattern per la rinominazione.

---

## 🔍 PROBLEMI IDENTIFICATI

### ⚠️ PROBLEMA 1: Documenti fascicolati con titolario diverso

**Scenario:**
1. Fascicolo ha `titolario_voce = "03.01 - Fatturazione"`
2. Documento collegato al fascicolo ha `titolario_voce = "03.02 - Contabilità"`

**Comportamento attuale:**
- Il documento calcola il proprio path basandosi sul suo `titolario_voce`
- Confronta con il path del fascicolo
- Se NON coincidono, il documento viene salvato nella sua directory, NON nella directory del fascicolo

**Path risultanti:**
```
Fascicolo:   /archivio/CLI001/03 - Amministrazione/03.01 - Fatturazione/2025/
Documento:   /archivio/CLI001/03 - Amministrazione/03.02 - Contabilità/2025/
```

**È corretto questo comportamento?**

### ⚠️ PROBLEMA 2: Documenti senza titolario proprio

**Scenario:**
- Documento collegato a fascicolo
- `documento.titolario_voce = None`

**Codice attuale (linea ~232):**
```python
doc_parts = build_titolario_parts(self.titolario_voce) if self.titolario_voce_id else []
doc_abs = ensure_archivio_path(cli_code, doc_parts, self.data_documento.year)
```

Se `titolario_voce` è `None`, `doc_parts` sarà una lista vuota `[]`.

**Path risultante:**
```
/archivio/CLI001/2025/  (senza albero del titolario)
```

Questo può essere corretto solo se il documento eredita il path del fascicolo (che avviene nel controllo successivo).

---

## ✅ ASPETTI CORRETTI

### 1. ✅ Struttura Gerarchia Directory

La struttura è implementata correttamente:
```
ARCHIVIO_BASE_PATH/
  └── CLI_CODE/
      └── TITOLARIO_PATH/
          └── ANNO/
```

### 2. ✅ Fascicoli: Solo Directory

I fascicoli creano **solo la directory**, senza file. ✅

### 3. ✅ Rinominazione File Documenti

I file dei documenti vengono rinominati secondo il pattern configurato in `nome_file_pattern`. ✅

### 4. ✅ Albero Titolario Completo

La funzione `build_titolario_parts()` costruisce correttamente l'intero albero dalla radice alla foglia. ✅

### 5. ✅ Periodo di Riferimento

L'anno viene aggiunto come ultima directory del path. ✅

---

## 📝 RACCOMANDAZIONI

### Raccomandazione 1: Chiarire Logica Titolario Documenti Fascicolati

**Opzione A (Attuale):** Il documento può avere un titolario diverso dal fascicolo e viene salvato nella sua directory.

**Opzione B (Più Rigida):** Un documento collegato a un fascicolo DEVE usare la directory del fascicolo, indipendentemente dal suo titolario.

**Suggerimento:** Se si sceglie l'Opzione B, modificare `_build_path()`:

```python
def _build_path(self) -> str:
    # Se collegato a un fascicolo, usa SEMPRE il path del fascicolo
    if self.fascicolo_id:
        fasc_abs = (self.fascicolo.path_archivio or "").strip()
        if fasc_abs and os.path.isdir(fasc_abs):
            return fasc_abs
    
    # Altrimenti calcola il path del documento
    cli_code = self._cliente_code(self.cliente)
    doc_parts = build_titolario_parts(self.titolario_voce) if self.titolario_voce_id else []
    return ensure_archivio_path(cli_code, doc_parts, self.data_documento.year)
```

### Raccomandazione 2: Gestire Documenti Senza Titolario

Se un documento non ha `titolario_voce` proprio e non è collegato a un fascicolo, attualmente viene salvato in:
```
/archivio/CLI_CODE/ANNO/
```

Valutare se:
1. ✅ Accettare questo comportamento (documenti "generici")
2. ⚠️ Rendere obbligatorio il titolario per documenti non fascicolati
3. ⚠️ Usare un titolario di default (es. "99 - Varie")

### Raccomandazione 3: Validazione Coerenza

Aggiungere un controllo in `Documento.clean()` per verificare che:
- Se il documento è collegato a un fascicolo, il suo titolario sia compatibile (stesso o discendente)
- Il cliente del documento coincida con quello del fascicolo

---

## 📊 RIEPILOGO FINALE

| Aspetto | Stato | Note |
|---------|-------|------|
| Struttura directory fascicoli | ✅ CORRETTO | Cliente → Titolario → Anno |
| Creazione solo directory fascicoli | ✅ CORRETTO | Nessun file copiato |
| Rinominazione file documenti | ✅ CORRETTO | Usa pattern configurabile |
| Albero titolario completo | ✅ CORRETTO | Dalla radice alla foglia |
| Documenti fascicolati con titolario diverso | ⚠️ DA CHIARIRE | Possono finire in directory diverse |
| Documenti senza titolario | ⚠️ DA VALUTARE | Finiscono in CLI/ANNO/ |
| Pattern nome file | ✅ CORRETTO | Sistema flessibile e potente |

---

## 🎯 CONCLUSIONE

**Il codice rispecchia sostanzialmente la logica descritta**, con alcune **sfumature da chiarire**:

1. **✅ FASCICOLI:** Implementazione perfetta
2. **⚠️ DOCUMENTI FASCICOLATI:** Possono divergere se hanno titolario diverso
3. **⚠️ DOCUMENTI SENZA TITOLARIO:** Necessita chiarimento sulla gestione

Il sistema è **ben progettato e flessibile**, ma potrebbero servire **validazioni aggiuntive** o **decisioni di business** sui casi limite.
