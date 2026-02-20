# Implementazione Voci Titolario Intestate ad Anagrafiche

## 📋 Riepilogo Implementazione

**Data**: 21 Gennaio 2026  
**Feature**: Voci titolario intestate ad anagrafiche (es. dossier dipendenti)  
**Scope**: Backend completo con API REST

---

## ✅ Cosa è stato implementato

### 1. **Estensione Modello `TitolarioVoce`**

**Nuovi campi**:

```python
class TitolarioVoce(models.Model):
    # ... campi esistenti ...
    
    consente_intestazione = models.BooleanField(
        default=False,
        verbose_name="Consente intestazione",
        help_text="Se True, consente di creare sotto-voci intestate ad anagrafiche"
    )
    
    anagrafica = models.ForeignKey(
        'anagrafiche.Anagrafica',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='voci_titolario',
        verbose_name="Anagrafica intestataria",
        help_text="Anagrafica a cui è intestata questa voce (opzionale)"
    )
```

**Nuovi metodi**:
- `is_voce_intestata()`: Verifica se voce è intestata
- `get_anagrafiche_disponibili()`: Anagrafiche non ancora usate
- `clean()`: Validazione business rules completa

---

### 2. **Validazioni Business Rules**

✅ **REGOLA 1**: Voce intestata DEVE avere parent con `consente_intestazione=True`  
✅ **REGOLA 2**: Voce NON può contemporaneamente consentire intestazione ed essere intestata  
✅ **REGOLA 3**: Prevenzione loop circolari nella gerarchia  
✅ **REGOLA 4**: Limite profondità massima (6 livelli)  
✅ **REGOLA 5**: Unicità anagrafica per parent (no duplicati)  
✅ **REGOLA 6**: `on_delete=PROTECT` su anagrafica (non cancellabile se ha voci)

---

### 3. **Migration & Data Migration**

**File**: `titolario/migrations/0003_titolariovoce_anagrafica_and_more.py`

**Azioni**:
- Aggiunge campo `consente_intestazione` (default=False)
- Aggiunge campo `anagrafica` (ForeignKey PROTECT)
- Aggiorna `pattern_codice` help_text (include `{ANA}`)
- **Data migration**: Abilita `consente_intestazione=True` su:
  - `HR-PERS` (Dossier personale)
  - `SALES-LEAD` (Lead e opportunità)
  - `LEG-CONT` (Contenzioso)

---

### 4. **Admin Django Migliorato**

**File**: `titolario/admin.py`

**Features**:
- Fieldset separato per "Intestazione Anagrafica"
- Badge colorato per flag `consente_intestazione`
- Display formattato per anagrafica intestataria
- Autocomplete per selezione anagrafica
- Filtri per `consente_intestazione` e `parent`
- Ricerca per nome/cognome anagrafica

---

### 5. **API REST Completa**

**Endpoint principale**: `/api/v1/fascicoli/titolario-voci/`

**ViewSet**: `TitolarioVoceViewSet`

**Actions standard**:
- `GET /titolario-voci/` - Lista voci
- `GET /titolario-voci/{id}/` - Dettaglio
- `POST /titolario-voci/` - Crea nuova voce
- `PATCH /titolario-voci/{id}/` - Modifica
- `DELETE /titolario-voci/{id}/` - Elimina

**Actions custom**:
- `GET /titolario-voci/voci_radice/` - Voci di primo livello
- `GET /titolario-voci/{id}/figli/` - Figli di una voce
- `GET /titolario-voci/{id}/anagrafiche_disponibili/` - Anagrafiche disponibili per intestazione
- `POST /titolario-voci/{id}/crea_voce_intestata/` - Helper creazione voce intestata

**Filtri disponibili**:
- `?parent=<id>` - Filtra per parent
- `?consente_intestazione=true` - Solo voci che consentono intestazione
- `?anagrafica=<id>` - Voci intestate a specifica anagrafica
- `?search=<term>` - Ricerca su codice, titolo, nome anagrafica

---

### 6. **Serializer Esteso**

**File**: `api/v1/fascicoli/serializers.py`

```python
class TitolarioVoceSerializer(serializers.ModelSerializer):
    anagrafica_nome = serializers.CharField(source='anagrafica.nome', read_only=True)
    is_voce_intestata = serializers.BooleanField(read_only=True)
    codice_gerarchico = serializers.CharField(read_only=True)
    
    class Meta:
        fields = [
            'id', 'codice', 'titolo', 'pattern_codice', 'parent',
            'consente_intestazione', 'anagrafica', 'anagrafica_nome',
            'is_voce_intestata', 'codice_gerarchico'
        ]
```

**Response esempio**:
```json
{
  "id": 42,
  "codice": "ROSMAR01",
  "titolo": "Mario Rossi",
  "pattern_codice": "{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}",
  "parent": 15,
  "consente_intestazione": false,
  "anagrafica": 123,
  "anagrafica_nome": "Mario Rossi",
  "is_voce_intestata": true,
  "codice_gerarchico": "HR-PERS/ROSMAR01"
}
```

---

### 7. **Test Suite Completa**

**File**: `titolario/tests_voci_intestate.py`

**10 test coprono**:
✅ Creazione voce base con flag  
✅ Creazione voce intestata  
✅ Validazione parent deve consentire intestazione  
✅ Validazione voce intestata senza parent  
✅ Validazione conflitto flag + anagrafica  
✅ Validazione unicità anagrafica per parent  
✅ Metodo `get_anagrafiche_disponibili()`  
✅ Codice gerarchico con voce intestata  
✅ PROTECT su cancellazione anagrafica  
✅ Pattern codice con placeholder `{ANA}`

**Coverage**: 77% su `titolario/models.py`

---

## 🎯 Caso d'Uso Principale: Dossier Dipendenti

### Struttura Esempio

```
HR (Risorse Umane)
└─ HR-PERS (Dossier personale) [consente_intestazione=True]
    ├─ ROSMAR01 (Mario Rossi) [anagrafica=Mario Rossi]
    │   ├─ BUSTE-PAGA
    │   ├─ CONTRATTI
    │   ├─ CU
    │   └─ FORMAZIONE
    ├─ VERAL01 (Alice Verdi) [anagrafica=Alice Verdi]
    │   ├─ BUSTE-PAGA
    │   └─ CONTRATTI
    └─ BIALGI02 (Luigi Bianchi) [anagrafica=Luigi Bianchi]
        └─ BUSTE-PAGA
```

### Workflow Creazione

#### 1. Via Admin Django

1. Vai su **Admin → Titolario → Voci di titolario**
2. Clicca su voce `HR-PERS`
3. Verifica che `Consente intestazione` = ✓ Sì
4. Clicca "Aggiungi voce di titolario"
5. Compila:
   - **Codice**: `ROSMAR01` (codice anagrafica)
   - **Titolo**: `Mario Rossi` (o custom)
   - **Parent**: `HR-PERS - Dossier personale`
   - **Anagrafica**: Cerca e seleziona "Mario Rossi"
   - **Pattern codice**: `{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}`
6. Salva

#### 2. Via API REST

**Request**:
```http
POST /api/v1/fascicoli/titolario-voci/15/crea_voce_intestata/
Content-Type: application/json
Authorization: Bearer <token>

{
  "anagrafica_id": 123,
  "titolo": "Mario Rossi",
  "pattern_codice": "{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}"
}
```

**Response**:
```json
{
  "id": 42,
  "codice": "ROSMAR01",
  "titolo": "Mario Rossi",
  "parent": 15,
  "anagrafica": 123,
  "anagrafica_nome": "Mario Rossi",
  "is_voce_intestata": true,
  "consente_intestazione": false,
  "pattern_codice": "{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}",
  "codice_gerarchico": "HR-PERS/ROSMAR01"
}
```

#### 3. Creazione sotto-voci (Buste Paga, Contratti, etc.)

Dopo aver creato la voce intestata, puoi creare sotto-voci standard:

```http
POST /api/v1/fascicoli/titolario-voci/
Content-Type: application/json
Authorization: Bearer <token>

{
  "codice": "BUSTE-PAGA",
  "titolo": "Buste Paga",
  "parent": 42,
  "pattern_codice": "{CLI}-{ANA}-BUSTE-{ANNO}-{SEQ:03d}"
}
```

---

## 📊 Pattern Codice con `{ANA}`

### Placeholder Disponibili

| Placeholder | Descrizione | Esempio |
|------------|-------------|---------|
| `{CLI}` | Codice cliente | `ROSSIM` |
| `{TIT}` | Codice titolario | `HR-PERS` |
| `{ANNO}` | Anno fascicolo | `2025` |
| `{SEQ:03d}` | Progressivo con zero-padding | `001`, `042` |
| `{ANA}` | **NUOVO**: Codice anagrafica intestataria | `ROSMAR01` |

### Esempi Pattern

```python
# Pattern standard per dossier dipendente
"{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}"
→ "AZIENDA-ROSMAR01-BUSTE-2025-001"

# Pattern semplificato
"{ANA}-{TIT}-{SEQ:04d}"
→ "ROSMAR01-CONTRATTI-0001"

# Pattern con separatore diverso
"{ANNO}_{ANA}_{TIT}_{SEQ:03d}"
→ "2025_ROSMAR01_CU_001"
```

**Nota**: Il pattern verrà utilizzato quando si creeranno **fascicoli** collegati alle voci titolario intestate.

---

## 🔒 Sicurezza e Vincoli

### Protezione Anagrafica

```python
# PROTECT: Impedisce cancellazione anagrafica se ha voci titolario
anagrafica = models.ForeignKey(..., on_delete=models.PROTECT)
```

**Comportamento**:
- Tentativo di cancellare anagrafica con voci → `ProtectedError`
- Bisogna prima eliminare/riassegnare tutte le voci intestate
- Garantisce integrità referenziale

### Validazione Integrità

```python
# Esempio: impedisce duplicati
if TitolarioVoce.objects.filter(
    parent=parent, 
    anagrafica=anagrafica
).exists():
    raise ValidationError("Voce già esistente per questa anagrafica")
```

### Limitazioni

- Max 6 livelli di profondità gerarchia
- Unicità (parent, codice) mantenuta
- Voce intestata NON può a sua volta consentire intestazione
- Voce radice (parent=null) NON può essere intestata

---

## 🚀 Endpoint API Dettagliati

### 1. Lista Voci Titolario

```http
GET /api/v1/fascicoli/titolario-voci/
```

**Query params**:
- `?search=mario` - Ricerca
- `?parent=15` - Filtra per parent
- `?consente_intestazione=true` - Solo voci abilitate
- `?anagrafica=123` - Voci di specifica anagrafica

### 2. Voci Radice

```http
GET /api/v1/fascicoli/titolario-voci/voci_radice/
```

Ritorna solo voci di primo livello (parent=null).

### 3. Figli di una Voce

```http
GET /api/v1/fascicoli/titolario-voci/{id}/figli/
```

Ritorna tutte le sotto-voci dirette.

**Esempio**:
```http
GET /api/v1/fascicoli/titolario-voci/15/figli/
```
→ Ritorna: ROSMAR01, VERAL01, BIALGI02 (se sotto HR-PERS)

### 4. Anagrafiche Disponibili

```http
GET /api/v1/fascicoli/titolario-voci/{id}/anagrafiche_disponibili/
```

Ritorna anagrafiche che possono essere intestate (non ancora usate).

**Condizioni**:
- La voce deve avere `consente_intestazione=True`
- Esclude anagrafiche già intestate sotto questa voce

### 5. Crea Voce Intestata (Helper)

```http
POST /api/v1/fascicoli/titolario-voci/{id}/crea_voce_intestata/
```

**Body**:
```json
{
  "anagrafica_id": 123,
  "titolo": "Mario Rossi",  // opzionale, default: nome anagrafica
  "pattern_codice": "{CLI}-{ANA}-{TIT}-{ANNO}-{SEQ:03d}"  // opzionale
}
```

**Validazioni automatiche**:
- Parent deve consentire intestazione
- Anagrafica deve esistere
- No duplicati (stessa anagrafica sotto stesso parent)

---

## 📈 Statistiche Test

```
10 test eseguiti: 10 passed ✅
Coverage titolario/models.py: 77.27%
Tempo esecuzione: 5.61s
```

**Test critici**:
- ✅ Business rules validation
- ✅ Database constraints (PROTECT, UNIQUE)
- ✅ API methods (get_anagrafiche_disponibili)
- ✅ Gerarchie complesse

---

## 🎨 Prossimi Passi (Frontend - Fase 2)

Per completare la feature lato frontend:

1. **Component React**: `TitolarioTree` con supporto voci intestate
2. **Form creazione**: Interfaccia user-friendly per creare voci intestate
3. **Autocomplete anagrafiche**: Integrato con API `anagrafiche_disponibili`
4. **Visualizzazione badge**: Indica voci intestate con icona utente
5. **Filtri avanzati**: Per voce consente_intestazione e anagrafica

---

## 📝 Note Implementative

### Codice Anagrafica vs Titolo

**Best Practice**:
- `codice` = codice anagrafica (es. `ROSMAR01`)
- `titolo` = nome completo (es. `Mario Rossi`)

**Esempio**:
```python
anagrafica = Anagrafica.objects.get(id=123)
voce = TitolarioVoce.objects.create(
    codice=anagrafica.codice,      # ROSMAR01
    titolo=anagrafica.nome,        # Mario Rossi
    parent=hr_pers,
    anagrafica=anagrafica
)
```

### Pattern Codice Ereditato

Le sotto-voci (es. BUSTE-PAGA) possono:
- Ereditare pattern del parent
- Avere pattern custom
- Usare `{ANA}` nel pattern anche se non intestate direttamente

### Performance Considerations

- Usa `select_related('anagrafica')` in query
- Cache voci titolario in frontend (cambiano raramente)
- Indici database automatici su ForeignKey

---

## ✅ Checklist Completamento Backend

- [x] Modello esteso con nuovi campi
- [x] Migration creata e applicata
- [x] Data migration per voci iniziali
- [x] Validazioni business rules complete
- [x] Admin Django configurato
- [x] API ViewSet con actions custom
- [x] Serializer esteso
- [x] Test suite completa (10 test)
- [x] Documentazione tecnica
- [ ] Frontend implementation (Fase 2)

---

**Status**: ✅ **Backend completo e funzionante**  
**Pronto per**: Integrazione frontend e testing utente
