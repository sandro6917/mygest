# Implementazione Titolario UNILAV - HR-PERS/DIPENDENTE/CONTRATTI

## 🎯 Obiettivo Implementato

Aggiunta gestione **titolario gerarchico automatico** per documenti UNILAV seguendo il pattern dei Cedolini.

---

## 🏗️ Struttura Titolario UNILAV

### Schema Gerarchico
```
HR-PERS (Personale - Voce Radice)
  └── {CODICE_ANAGRAFICA} (es. ROSMAR01 - Voce Dipendente)
        └── CONTRATTI (Contratti di lavoro - Voce Finale)
```

### Esempio Pratico
```
HR-PERS
  ├── ROSMAR01 (Rossi Mario)
  │     └── CONTRATTI → QUI vanno i documenti UNILAV di Rossi Mario
  ├── BNCGVN02 (Bianchi Giovanni)
  │     └── CONTRATTI → QUI vanno i documenti UNILAV di Bianchi Giovanni
  └── ...
```

---

## 📝 Modifiche Implementate

### File: `documenti/importers/unilav.py`

#### 1. **Nuovo Metodo `_get_or_create_titolario_dipendente()`**

**Posizione**: Righe 297-358 (dopo `parse_document`, prima di `_mappa_tipo_comunicazione`)

**Codice**:
```python
def _get_or_create_titolario_dipendente(self, anagrafica_dipendente: Anagrafica) -> TitolarioVoce:
    """
    Ottiene o crea la voce titolario CONTRATTI per il dipendente.
    
    Struttura: HR-PERS/{CODICE_ANAGRAFICA}/CONTRATTI
    Esempio: HR-PERS/ROSMAR01/CONTRATTI
    
    Args:
        anagrafica_dipendente: Anagrafica del lavoratore
        
    Returns:
        TitolarioVoce CONTRATTI per il dipendente
    """
    from anagrafiche.utils import get_or_generate_cli
    
    # 1. Verifica/crea voce radice HR-PERS
    try:
        voce_hr_pers = TitolarioVoce.objects.get(codice='HR-PERS')
    except TitolarioVoce.DoesNotExist:
        logger.error("Voce titolario HR-PERS non trovata! Crearla manualmente.")
        # Fallback: usa voce di default
        from documenti.models import get_or_create_default_titolario
        return get_or_create_default_titolario()
    
    # 2. Ottieni codice anagrafica dipendente (es. ROSMAR01)
    codice_dipendente = get_or_generate_cli(anagrafica_dipendente)
    
    # 3. Verifica/crea sottovoce per il dipendente (HR-PERS/ROSMAR01)
    voce_dipendente, created = TitolarioVoce.objects.get_or_create(
        codice=codice_dipendente,
        parent=voce_hr_pers,
        defaults={
            'titolo': f"{anagrafica_dipendente.cognome} {anagrafica_dipendente.nome}",
            'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
        }
    )
    
    if created:
        logger.info(f"Creata voce titolario dipendente: {voce_dipendente.codice} - {voce_dipendente.titolo}")
    
    # 4. Verifica/crea sottovoce CONTRATTI (HR-PERS/ROSMAR01/CONTRATTI)
    voce_contratti, created = TitolarioVoce.objects.get_or_create(
        codice='CONTRATTI',
        parent=voce_dipendente,
        defaults={
            'titolo': 'Contratti di lavoro',
            'pattern_codice': '{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
        }
    )
    
    if created:
        logger.info(
            f"Creata voce titolario CONTRATTI per {codice_dipendente}: "
            f"{voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_contratti.codice}"
        )
    
    logger.debug(
        f"Titolario UNILAV: {voce_hr_pers.codice}/{voce_dipendente.codice}/{voce_contratti.codice}"
    )
    
    return voce_contratti
```

**Funzionamento**:

##### Step 1: Verifica HR-PERS
- ✅ Cerca voce radice `HR-PERS`
- ❌ Se non esiste → **FALLBACK** a `99 - Varie` (safety net)
- ⚠️ Log ERROR per avvisare che HR-PERS deve essere creato

##### Step 2: Genera Codice Dipendente
- Usa utility `get_or_generate_cli(anagrafica_dipendente)`
- Algoritmo: `COGNOME[0:6]NOME[0:2]`
- Esempio: `Rossi Mario` → `ROSMAR01`

##### Step 3: Crea Voce Dipendente
- `get_or_create`: `HR-PERS/ROSMAR01`
- Titolo: `"Rossi Mario"`
- **Idempotente**: se esiste già, la recupera

##### Step 4: Crea Voce CONTRATTI
- `get_or_create`: `HR-PERS/ROSMAR01/CONTRATTI`
- Titolo: `"Contratti di lavoro"`
- **Idempotente**: se esiste già, la recupera

##### Step 5: Return
- Restituisce voce finale `CONTRATTI` da assegnare al documento

---

#### 2. **Modifica `create_documento()` - Aggiunta Chiamata Titolario**

**Posizione**: Righe 463-465

**PRIMA**:
```python
# 3. Recupera/Crea Tipo UNILAV
tipo_unilav, _ = DocumentiTipo.objects.get_or_create(
    codice='UNILAV',
    defaults={'descrizione': 'Comunicazione UNILAV'}
)

# 4. Crea Fascicolo (se necessario)
fascicolo = None
```

**DOPO**:
```python
# 3. Recupera/Crea Tipo UNILAV
tipo_unilav, _ = DocumentiTipo.objects.get_or_create(
    codice='UNILAV',
    defaults={'descrizione': 'Comunicazione UNILAV'}
)

# 4. Titolario: Gerarchia HR-PERS/{CODICE_DIPENDENTE}/CONTRATTI
# Esempio: HR-PERS/ROSMAR01/CONTRATTI
titolario = self._get_or_create_titolario_dipendente(anagrafica_lavoratore)

# 5. Crea Fascicolo (se necessario)
fascicolo = None
```

**Cambiamenti**:
- ✅ Aggiunto Step 4: creazione titolario
- ✅ Rinumerati step successivi (5, 6, 7, 8, 9)
- ✅ Variabile `titolario` ora disponibile per assegnazione documento

---

#### 3. **Modifica `Documento.objects.create()` - Assegnazione Titolario**

**Posizione**: Riga 499

**PRIMA**:
```python
documento = Documento.objects.create(
    tipo=tipo_unilav,
    cliente=cliente_datore,
    fascicolo=fascicolo,
    descrizione=descrizione,
    data_documento=valori_editati['data_comunicazione'],
    # ... resto campi
)
```

**DOPO**:
```python
documento = Documento.objects.create(
    tipo=tipo_unilav,
    cliente=cliente_datore,
    fascicolo=fascicolo,
    titolario_voce=titolario,  # ← AGGIUNTO
    descrizione=descrizione,
    data_documento=valori_editati['data_comunicazione'],
    # ... resto campi
)
```

**Cambiamento**:
- ✅ Aggiunto campo `titolario_voce=titolario`
- ✅ Assegna voce `HR-PERS/DIPENDENTE/CONTRATTI` al documento

---

## 🔄 Flusso Completo End-to-End

### Input
```python
parsed_data = {
    'lavoratore': {
        'codice_fiscale': 'RSSMRA80A01H501X',
        'cognome': 'ROSSI',
        'nome': 'MARIO',
    },
    'unilav': {
        'codice_comunicazione': '12345678',
        'data_comunicazione': '2024-01-15',
        # ...
    }
}
```

### Esecuzione
```python
importer = UNILAVImporter(session)

# create_documento() viene chiamato
documento = importer.create_documento(
    parsed_data=parsed_data,
    valori_editati=valori_editabili,
    user=user,
    file_path='/path/to/unilav.pdf'
)
```

### Step Interni
```
1. Crea anagrafica_datore (ACME SRL - CF: 12345678901)
   └─> Cliente creato

2. Crea anagrafica_lavoratore (Rossi Mario - CF: RSSMRA80A01H501X)
   └─> Codice auto-generato: ROSMAR01

3. Recupera tipo_unilav (UNILAV)

4. _get_or_create_titolario_dipendente(anagrafica_lavoratore)
   ├─> Verifica HR-PERS → esiste
   ├─> Genera codice: ROSMAR01
   ├─> get_or_create HR-PERS/ROSMAR01
   │   └─> Creata (prima volta) o recuperata (successive)
   ├─> get_or_create HR-PERS/ROSMAR01/CONTRATTI
   │   └─> Creata (prima volta) o recuperata (successive)
   └─> Return: TitolarioVoce(codice='CONTRATTI', parent__codice='ROSMAR01')

5. Crea fascicolo (opzionale)

6. Documento.objects.create(
     titolario_voce=voce_contratti,  ← HR-PERS/ROSMAR01/CONTRATTI
     # ... altri campi
   )
```

### Output Database
```
Tabella: titolario_titolariovoce
┌────┬───────────┬───────────┬──────────────────────┬─────────────────┐
│ id │ codice    │ parent_id │ titolo               │ pattern_codice  │
├────┼───────────┼───────────┼──────────────────────┼─────────────────┤
│ 1  │ HR-PERS   │ NULL      │ Personale            │ {CLI}-{TIT}-... │
│ 2  │ ROSMAR01  │ 1         │ Rossi Mario          │ {CLI}-{TIT}-... │
│ 3  │ CONTRATTI │ 2         │ Contratti di lavoro  │ {CLI}-{TIT}-... │
└────┴───────────┴───────────┴──────────────────────┴─────────────────┘

Tabella: documenti_documento
┌────┬──────────────┬───────────────────┬────────────────────┬─────────────┐
│ id │ codice       │ titolario_voce_id │ descrizione        │ cliente_id  │
├────┼──────────────┼───────────────────┼────────────────────┼─────────────┤
│ 10 │ CLI-CONT-... │ 3                 │ UNILAV Assunzione..│ 5 (ACME)    │
└────┴──────────────┴───────────────────┴────────────────────┴─────────────┘
```

---

## ✅ Caratteristiche Implementate

| Caratteristica | Implementazione | Note |
|----------------|----------------|------|
| **Auto-creazione gerarchia** | ✅ Sì | HR-PERS → DIPENDENTE → CONTRATTI |
| **Idempotenza** | ✅ Sì | `get_or_create` per tutte le voci |
| **Personalizzazione** | ✅ Sì | Ogni lavoratore ha propria sottovoce |
| **Fallback robusto** | ✅ Sì | Se HR-PERS manca → usa "99 - Varie" |
| **Logging completo** | ✅ Sì | Traccia creazioni e recuperi |
| **Transaction safety** | ✅ Sì | `@transaction.atomic` in create_documento |
| **Codice univoco** | ✅ Sì | `get_or_generate_cli()` garantisce unicità |

---

## 🆚 Confronto con Cedolini

| Aspetto | Cedolini | UNILAV |
|---------|----------|--------|
| **Struttura** | HR-PERS/DIPENDENTE/PAG | HR-PERS/DIPENDENTE/CONTRATTI |
| **Voce finale** | `PAG` (Paghe) | `CONTRATTI` (Contratti di lavoro) |
| **Titolo voce** | "Paghe" | "Contratti di lavoro" |
| **Metodo** | `_get_or_create_titolario_dipendente()` | `_get_or_create_titolario_dipendente()` |
| **Pattern** | Identico | Identico |
| **Fallback** | 99 - Varie | 99 - Varie |

**Differenza principale**: Solo il nome della voce finale (`PAG` vs `CONTRATTI`).

---

## 🛡️ Prerequisiti

### Obbligatori
1. **Voce Titolario `HR-PERS`** deve esistere:
   ```python
   TitolarioVoce.objects.create(
       codice='HR-PERS',
       parent=None,
       titolo='Personale',
       descrizione='Gestione risorse umane e personale',
       pattern_codice='{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
   )
   ```

### Opzionali (Fallback Automatico)
- Se `HR-PERS` manca → usa `99 - Varie` (creato automaticamente)
- ⚠️ LOG ERROR avvisa dell'assenza

---

## 📊 Mappatura Campi - Aggiornamento

### Campo Titolario Voce

| Campo | Stato PRIMA | Stato DOPO |
|-------|-------------|------------|
| **Titolario voce** | ❌ `None` (non mappato) | ✅ `HR-PERS/DIPENDENTE/CONTRATTI` |

### Score Aggiornato

| Categoria | PRIMA | DOPO |
|-----------|-------|------|
| **Campi Base** | 10/13 (77%) | **11/13 (85%)** ✅ |
| **Attributi Dinamici** | 7/7 (100%) | 7/7 (100%) ✅ |
| **Score Totale** | 24/28 (85%) | **25/28 (89%)** ✅ |

**Miglioramento**: +4% copertura complessiva

---

## 🧪 Test Consigliati

### Test Unitario
```python
@pytest.mark.django_db
def test_unilav_titolario_gerarchia(sample_unilav_pdf, user):
    """Verifica creazione gerarchia titolario completa"""
    # Setup: crea HR-PERS
    voce_hr_pers = TitolarioVoce.objects.create(
        codice='HR-PERS',
        parent=None,
        titolo='Personale',
        pattern_codice='{CLI}-{TIT}-{ANNO}-{SEQ:03d}',
    )
    
    # Import UNILAV
    importer = UNILAVImporter(session)
    result = importer.parse_document(sample_unilav_pdf, 'test.pdf')
    
    documento = importer.create_documento(
        parsed_data=result.parsed_data,
        valori_editati=result.valori_editabili,
        user=user,
        file_path=sample_unilav_pdf
    )
    
    # Verifiche
    assert documento.titolario_voce is not None
    assert documento.titolario_voce.codice == 'CONTRATTI'
    assert documento.titolario_voce.parent is not None
    assert documento.titolario_voce.parent.parent is not None
    assert documento.titolario_voce.parent.parent.codice == 'HR-PERS'
    
    # Verifica path completo
    path = []
    voce = documento.titolario_voce
    while voce:
        path.insert(0, voce.codice)
        voce = voce.parent
    
    assert len(path) == 3
    assert path[0] == 'HR-PERS'
    assert path[1].startswith('ROSMAR')  # o altro codice dipendente
    assert path[2] == 'CONTRATTI'
```

### Test Idempotenza
```python
@pytest.mark.django_db
def test_unilav_titolario_idempotenza(sample_unilav_pdf, user):
    """Verifica idempotenza creazione titolario"""
    # Setup HR-PERS
    TitolarioVoce.objects.create(codice='HR-PERS', parent=None, titolo='Personale')
    
    importer = UNILAVImporter(session)
    result = importer.parse_document(sample_unilav_pdf, 'test.pdf')
    
    # Prima importazione
    doc1 = importer.create_documento(
        parsed_data=result.parsed_data,
        valori_editati=result.valori_editabili,
        user=user,
        file_path=sample_unilav_pdf
    )
    
    # Seconda importazione stesso lavoratore
    doc2 = importer.create_documento(
        parsed_data=result.parsed_data,
        valori_editati=result.valori_editabili,
        user=user,
        file_path=sample_unilav_pdf
    )
    
    # Devono avere STESSA voce titolario (non duplicata)
    assert doc1.titolario_voce.id == doc2.titolario_voce.id
    
    # Conta voci create
    count_dipendente = TitolarioVoce.objects.filter(
        parent__codice='HR-PERS'
    ).count()
    assert count_dipendente == 1  # Solo UNA voce dipendente
    
    count_contratti = TitolarioVoce.objects.filter(
        codice='CONTRATTI',
        parent__parent__codice='HR-PERS'
    ).count()
    assert count_contratti == 1  # Solo UNA voce CONTRATTI per dipendente
```

---

## 📝 Conclusioni

### ✅ Implementazione Completa
- ✅ Metodo `_get_or_create_titolario_dipendente()` aggiunto
- ✅ Chiamata inserita in `create_documento()`
- ✅ Campo `titolario_voce` ora mappato correttamente
- ✅ Pattern identico a Cedolini (riutilizzo best practice)

### 🎯 Obiettivi Raggiunti
1. ✅ Gerarchia automatica `HR-PERS/DIPENDENTE/CONTRATTI`
2. ✅ Idempotenza garantita (`get_or_create`)
3. ✅ Fallback robusto (voce `99 - Varie`)
4. ✅ Logging completo
5. ✅ Copertura mappatura: 85% → **89%**

### 🚀 Prossimi Passi
1. ✅ **COMPLETATO**: Implementazione titolario
2. ⏭️ Popolare campo `tags` (MEDIA priorità)
3. ⏭️ Test unitari e integrazione
4. ⏭️ Verificare prerequisito HR-PERS in produzione
5. ⏭️ Deploy e test con file reali

---

**File Modificato**: `documenti/importers/unilav.py`  
**Righe Aggiunte**: ~65 (nuovo metodo + modifiche)  
**Stato**: ✅ Nessun errore di sintassi  
**Versione**: 1.0  
**Data**: 6 Febbraio 2026
