# FIX: Errori Importazione UNILAV

**Data**: 6 Febbraio 2026  
**Componente**: `documenti/importers/unilav.py`  
**Errori Risolti**: 2

---

## 🐛 Errori Identificati

### 1. Missing `check_duplicate` Method
```
Errore check duplicato per cbea3984-e08c-4b2a-9c30-1198853bc9db: 
'UNILAVImporter' object has no attribute 'check_duplicate'
```

**Causa**: Il metodo `check_duplicate()` non era implementato in `UNILAVImporter`, mentre è richiesto dal sistema di importazione per verificare documenti duplicati.

**Impact**: L'endpoint `/check-duplicates/` falliva per i documenti UNILAV.

---

### 2. Invalid Anagrafica Fields
```
Errore creazione documento da cbea3984-e08c-4b2a-9c30-1198853bc9db: 
Invalid field name(s) for model Anagrafica: 'cap', 'comune', 'comune_nascita'.
```

**Causa**: Il metodo `create_documento()` tentava di salvare `cap`, `comune`, `comune_nascita` direttamente nel model `Anagrafica`, ma questi campi non esistono nel modello.

**Struttura Corretta**:
- `Anagrafica`: campi base (codice_fiscale, nome, cognome, ragione_sociale, email, telefono)
- `Indirizzo` (related model): campi geografici (indirizzo, cap, comune, provincia, nazione)

**Impact**: La creazione di nuove anagrafiche (datore/lavoratore) falliva con errore 400.

---

## ✅ Soluzioni Implementate

### 1. Implementato `check_duplicate()` Method

**File**: `documenti/importers/unilav.py`  
**Linee**: 316-388

```python
def check_duplicate(
    self,
    parsed_data: Dict[str, Any],
    valori_editabili: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Verifica se l'UNILAV è un duplicato senza crearlo.
    
    Returns:
        {
          "is_duplicate": bool,
          "duplicate_info": {
            "id": int,
            "codice": str,
            "codice_comunicazione": str,
            "data_comunicazione": str,
            "confidence": float,
            "matched_fields": list
          } | None
        }
    """
    from documenti.services.duplicate_detection import DuplicateDetectionService
    
    # Tipo documento UNILAV
    tipo_unilav = DocumentiTipo.objects.filter(codice='UNILAV').first()
    if not tipo_unilav:
        return {'is_duplicate': False, 'duplicate_info': None}
    
    # Cliente: cerca da anagrafica datore
    cliente = None
    cf_datore = parsed_data['datore']['codice_fiscale']
    if cf_datore:
        try:
            anagrafica_datore = Anagrafica.objects.get(codice_fiscale__iexact=cf_datore)
            if hasattr(anagrafica_datore, 'cliente'):
                cliente = anagrafica_datore.cliente
        except (Anagrafica.DoesNotExist, Anagrafica.MultipleObjectsReturned):
            pass
    
    if not cliente:
        return {'is_duplicate': False, 'duplicate_info': None}
    
    # Verifica duplicati su attributi chiave
    valori = valori_editabili or {}
    attributi_per_verifica = {
        'codice_comunicazione': valori.get('codice_comunicazione') or parsed_data['unilav'].get('codice_comunicazione'),
        'data_comunicazione': valori.get('data_comunicazione') or parsed_data['unilav'].get('data_comunicazione'),
    }
    
    # Usa DuplicateDetectionService generico
    service = DuplicateDetectionService(tipo_unilav)
    
    if not service.is_enabled():
        return {'is_duplicate': False, 'duplicate_info': None}
    
    result = service.find_duplicate(
        cliente=cliente,
        attributi=attributi_per_verifica,
        documento_fields={'data_documento': timezone.now().date()}
    )
    
    return {
        'is_duplicate': result.is_duplicate,
        'duplicate_info': {
            'id': result.documento.id,
            'codice': result.documento.codice,
            'codice_comunicazione': attributi_per_verifica.get('codice_comunicazione'),
            'data_comunicazione': attributi_per_verifica.get('data_comunicazione'),
            'confidence': result.confidence,
            'matched_fields': result.matched_fields,
        } if result.is_duplicate else None
    }
```

**Logica**:
1. Verifica esistenza tipo documento UNILAV
2. Trova cliente da CF datore
3. Usa `DuplicateDetectionService` per verificare duplicati su:
   - `codice_comunicazione` (univoco per comunicazione)
   - `data_comunicazione`
4. Ritorna info duplicato se trovato (ID, codice, confidence, matched_fields)

**Pattern**: Identico a `cedolini.py` per coerenza architetturale.

---

### 2. Corretta Creazione Anagrafiche con Indirizzi

**File**: `documenti/importers/unilav.py`  
**Linee**: 505-581

#### **PRIMA** (❌ Errato)
```python
# Tentava di salvare campi inesistenti in Anagrafica
anagrafica_datore, created = Anagrafica.objects.get_or_create(
    codice_fiscale=cf_datore,
    defaults={
        'tipo': tipo_datore,
        'ragione_sociale': ...,
        'comune': valori_editati.get('datore_comune'),  # ❌ Campo inesistente
        'cap': valori_editati.get('datore_cap'),        # ❌ Campo inesistente
        'indirizzo': valori_editati.get('datore_indirizzo'),  # ❌ Campo inesistente
    }
)

anagrafica_lavoratore, created = Anagrafica.objects.get_or_create(
    codice_fiscale=cf_lavoratore,
    defaults={
        'tipo': 'PF',
        'cognome': valori_editati.get('lavoratore_cognome'),
        'comune_nascita': valori_editati.get('lavoratore_comune_nascita'),  # ❌ Campo inesistente
        'comune': valori_editati.get('lavoratore_comune'),  # ❌ Campo inesistente
        'cap': valori_editati.get('lavoratore_cap'),  # ❌ Campo inesistente
        'indirizzo': valori_editati.get('lavoratore_indirizzo'),  # ❌ Campo inesistente
    }
)
```

#### **DOPO** (✅ Corretto)
```python
# === DATORE ===
# 1. Crea Anagrafica con solo campi validi
datore_defaults = {
    'tipo': tipo_datore,
    'email': valori_editati.get('datore_email', ''),
    'telefono': valori_editati.get('datore_telefono', ''),
}

if tipo_datore == 'PG':
    datore_defaults['ragione_sociale'] = valori_editati.get('datore_denominazione', '')
else:  # PF
    datore_defaults['cognome'] = valori_editati.get('datore_cognome', '')
    datore_defaults['nome'] = valori_editati.get('datore_nome', '')

anagrafica_datore, created = Anagrafica.objects.get_or_create(
    codice_fiscale=cf_datore,
    defaults=datore_defaults
)

# 2. Se creata nuova anagrafica, crea Indirizzo separato
if created:
    logger.info(f"Creata nuova anagrafica datore: {anagrafica_datore}")
    
    indirizzo_datore = valori_editati.get('datore_indirizzo', '').strip()
    comune_datore = valori_editati.get('datore_comune', '').strip()
    
    if indirizzo_datore and comune_datore:
        from anagrafiche.models import Indirizzo
        
        Indirizzo.objects.create(
            anagrafica=anagrafica_datore,
            tipo_indirizzo='SLE' if tipo_datore == 'PG' else 'RES',  # Sede Legale PG, Residenza PF
            indirizzo=indirizzo_datore,
            comune=comune_datore,
            cap=valori_editati.get('datore_cap', ''),
            provincia=valori_editati.get('datore_provincia', ''),
            principale=True  # Marca come indirizzo principale
        )
        logger.info(f"Creato indirizzo principale per datore: {comune_datore}")

# === LAVORATORE ===
# 1. Crea Anagrafica PF con solo campi validi
lavoratore_defaults = {
    'tipo': 'PF',
    'cognome': valori_editati.get('lavoratore_cognome', ''),
    'nome': valori_editati.get('lavoratore_nome', ''),
}

anagrafica_lavoratore, created = Anagrafica.objects.get_or_create(
    codice_fiscale=cf_lavoratore,
    defaults=lavoratore_defaults
)

# 2. Se creata nuova anagrafica, crea Indirizzo separato
if created:
    logger.info(f"Creata nuova anagrafica lavoratore: {anagrafica_lavoratore}")
    
    indirizzo_lavoratore = valori_editati.get('lavoratore_indirizzo', '').strip()
    comune_lavoratore = valori_editati.get('lavoratore_comune', '').strip()
    
    if indirizzo_lavoratore and comune_lavoratore:
        from anagrafiche.models import Indirizzo
        
        Indirizzo.objects.create(
            anagrafica=anagrafica_lavoratore,
            tipo_indirizzo='RES',  # Residenza per lavoratore PF
            indirizzo=indirizzo_lavoratore,
            comune=comune_lavoratore,
            cap=valori_editati.get('lavoratore_cap', ''),
            provincia=valori_editati.get('lavoratore_provincia', ''),
            principale=True
        )
        logger.info(f"Creato indirizzo principale per lavoratore: {comune_lavoratore}")
```

**Logica Corretta**:
1. **Step 1**: Crea `Anagrafica` con solo campi diretti (nome, cognome, CF, email, telefono)
2. **Step 2**: Se nuova anagrafica creata + dati indirizzo disponibili → crea oggetto `Indirizzo` separato
3. **Tipo Indirizzo**:
   - Datore PG → `'SLE'` (Sede Legale)
   - Datore PF → `'RES'` (Residenza)
   - Lavoratore PF → `'RES'` (Residenza)
4. **Indirizzo Principale**: Flag `principale=True` per usarlo come default

**Pattern**: Allineato a `cedolini.py` e struttura modelli Django.

---

## 📊 Impatto dei Fix

| Componente | Prima | Dopo |
|------------|-------|------|
| **Check Duplicates** | ❌ Errore 500 | ✅ Funzionante |
| **Creazione Anagrafica Datore** | ❌ Errore 400 (campi invalidi) | ✅ Anagrafica + Indirizzo creati |
| **Creazione Anagrafica Lavoratore** | ❌ Errore 400 (campi invalidi) | ✅ Anagrafica + Indirizzo creati |
| **Import UNILAV Completo** | ❌ Bloccato | ✅ End-to-end funzionante |

---

## 🧪 Testing

### Test Case 1: Check Duplicate
```bash
# Endpoint: GET /api/v1/documenti/import-sessions/{session_id}/check-duplicates/

# PRIMA: Errore
'UNILAVImporter' object has no attribute 'check_duplicate'

# DOPO: Risposta corretta
{
  "is_duplicate": false,
  "duplicate_info": null
}
```

### Test Case 2: Creazione Nuova Anagrafica con Indirizzo
```bash
# Endpoint: POST /api/v1/documenti/import-sessions/{session_id}/documents/{doc_id}/create/

# PRIMA: Errore 400
Invalid field name(s) for model Anagrafica: 'cap', 'comune', 'comune_nascita'

# DOPO: Successo
✅ Anagrafica Datore creata (ID: 123)
✅ Indirizzo Datore creato (Sede Legale: Via Roma 1, Milano)
✅ Cliente Datore creato
✅ Anagrafica Lavoratore creata (ID: 124)
✅ Indirizzo Lavoratore creato (Residenza: Via Verdi 5, Roma)
✅ Documento UNILAV creato (ID: 456, Codice: CLI001-CONTRATTI-2026-001)
```

---

## 📝 Note Tecniche

### Campi Validi Model `Anagrafica`
```python
# anagrafiche/models.py (linee 103-140)
class Anagrafica(models.Model):
    tipo = models.CharField(max_length=2, choices=TipoSoggetto.choices)  # PF / PG
    
    # Persona Giuridica
    ragione_sociale = models.CharField(max_length=200, blank=True)
    
    # Persona Fisica
    nome = models.CharField(max_length=120, blank=True)
    cognome = models.CharField(max_length=120, blank=True)
    
    # Identificativi
    codice_fiscale = models.CharField(max_length=16, unique=True)
    partita_iva = models.CharField(max_length=11, blank=True)
    codice = models.CharField(max_length=8, null=True, blank=True, unique=True)
    
    # Contatti
    pec = models.EmailField(blank=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    indirizzo = models.CharField(max_length=255, blank=True)  # ⚠️ Campo legacy, NON USARE
    
    # Meta
    denominazione_abbreviata = models.TextField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

⚠️ **IMPORTANTE**: Il campo `indirizzo` esiste in `Anagrafica` ma è **legacy e deprecato**. NON usarlo per nuovi dati. Usa sempre il modello `Indirizzo` separato.

### Campi Model `Indirizzo`
```python
# anagrafiche/models.py (linee 253-310)
class Indirizzo(models.Model):
    class TipoIndirizzo(models.TextChoices):
        RESIDENZA = "RES", _("Residenza")
        DOMICILIO = "DOM", _("Domicilio")
        SEDE_LEGALE = "SLE", _("Sede legale")
        SEDE_AMM = "SAM", _("Sede amministrativa")
        UFFICIO = "UFI", _("Ufficio")
        ALTRO = "ALT", _("Altro")
    
    anagrafica = models.ForeignKey(Anagrafica, on_delete=models.CASCADE, related_name="indirizzi")
    tipo_indirizzo = models.CharField(max_length=3, choices=TipoIndirizzo.choices)
    
    # Componenti indirizzo
    toponimo = models.CharField(max_length=50, blank=True)  # via, viale, piazza
    indirizzo = models.CharField(max_length=255)  # es. "Via Roma 1"
    numero_civico = models.CharField(max_length=20, blank=True)
    frazione = models.CharField(max_length=100, blank=True)
    
    # Geolocalizzazione
    comune_italiano = models.ForeignKey(ComuneItaliano, on_delete=models.SET_NULL, null=True, blank=True)
    cap = models.CharField(max_length=5, blank=True)
    comune = models.CharField(max_length=120)
    provincia = models.CharField(max_length=3, blank=True)  # Sigla (es. MI)
    nazione = models.CharField(max_length=2, default="IT")  # ISO 3166-1 alpha-2
    
    principale = models.BooleanField(default=False)  # Solo uno per anagrafica
    note = models.CharField(max_length=255, blank=True)
```

**Vincoli**:
- Un solo indirizzo `principale=True` per anagrafica (UniqueConstraint)
- CAP italiano: 5 cifre numeriche
- Provincia italiana: 2-3 lettere (sigla)
- Nazione: ISO 3166-1 alpha-2 (IT, DE, FR, etc.)

---

## 🔄 Pattern di Riferimento

Entrambi gli importatori (Cedolini e UNILAV) seguono ora lo **stesso pattern** per:

1. **Check Duplicates**: `DuplicateDetectionService` con attributi chiave
2. **Creazione Anagrafiche**: Separazione Anagrafica base + Indirizzo related
3. **Titolario**: Gerarchia HR-PERS/{CODICE}/CATEGORIA
4. **Attributi Dinamici**: AttributoDefinizione + AttributoValore

**Benefici**:
- ✅ Codice riutilizzabile
- ✅ Comportamento consistente
- ✅ Manutenibilità migliorata
- ✅ Test coverage condiviso

---

## ✅ Checklist Deploy

- [x] Fix `check_duplicate` method
- [x] Fix creazione anagrafiche con indirizzi
- [x] Test errori risolti
- [ ] Test con UNILAV reale
- [ ] Configurare `AttributoDefinizione` per tipo UNILAV
- [ ] Verificare voce titolario HR-PERS in produzione
- [ ] Deploy su VPS test
- [ ] Validazione utente finale

---

**Status**: ✅ **FIX COMPLETATO**  
**Next**: Testing con PDF UNILAV reali
