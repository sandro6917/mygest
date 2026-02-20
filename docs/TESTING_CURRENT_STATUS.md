# Testing - Status Attuale

**Data**: 17 Novembre 2025  
**Coverage Globale**: **48.90%**  
**Test Eseguiti**: 106 totali (79 ✅ passati, 27 ❌ falliti)

---

## 📊 Coverage per App

| App | Coverage | Stmts | Miss | Status |
|-----|----------|-------|------|--------|
| **anagrafiche** | 54.22% | 332 | 152 | 🟡 Medio |
| **documenti** | 44.86% | 321 | 177 | 🟠 Basso |
| **pratiche** | 82.89% | 152 | 26 | 🟢 Buono |
| **fascicoli** | 41.81% | 177 | 103 | 🟠 Basso |
| **protocollo** | 70.05% | 197 | 59 | 🟢 Buono |
| **scadenze** | 80.95% | 168 | 32 | 🟢 Buono |
| **comunicazioni** | 61.20% | 183 | 71 | 🟡 Medio |
| **archivio_fisico** | 60.42% | 331 | 131 | 🟡 Medio |
| **whatsapp** | 91.03% | 145 | 13 | ✅ Ottimo |
| **stampe** | 8.04% | 709 | 652 | 🔴 Critico |

---

## 🔴 Test Falliti (27)

### Categoria 1: Validatori CF/PIVA (12 fallimenti)

**Problema**: Il validatore CF è più restrittivo del previsto nei test

```
FAILED anagrafiche/tests/test_validators.py::TestCodiceFiscaleValidator::test_codice_fiscale_case_insensitive
FAILED anagrafiche/tests/test_validators.py::TestCodiceFiscaleValidator::test_codici_fiscali_validi_vari[BNCGNN85T10A944S]
FAILED anagrafiche/tests/test_validators.py::TestCodiceFiscaleValidator::test_codici_fiscali_validi_vari[VRDDNC90D41F205X]
FAILED anagrafiche/tests/test_validators.py::TestCodiceFiscaleValidator::test_codici_fiscali_validi_vari[GLLMHL88M70D969P]
FAILED anagrafiche/tests/test_validators.py::TestPartitaIVAValidator::test_partita_iva_valida
FAILED anagrafiche/tests/test_validators.py::TestPartitaIVAValidator::test_partite_iva_valide_varie[12345678901]
FAILED anagrafiche/tests/test_validators.py::TestPartitaIVAValidator::test_partite_iva_valide_varie[00000000000]
FAILED anagrafiche/tests/test_validators.py::TestPartitaIVAValidator::test_partite_iva_valide_varie[99999999999]
FAILED anagrafiche/tests/test_validators.py::TestPartitaIVAValidator::test_partita_iva_obbligatoria_per_pg
FAILED anagrafiche/tests/test_validators.py::TestUtilsGeneratoreCodiceCliente::test_build_cli_base6_persona_fisica
FAILED anagrafiche/tests/test_validators.py::TestUtilsGeneratoreCodiceCliente::test_get_or_generate_cli_incremental_suffix
FAILED anagrafiche/tests/test_validators.py::TestAnagraficaModel::test_create_persona_fisica
```

**Causa**: 
- CF checksum reale richiesto (non solo formato)
- P.IVA richiede checksum valido
- CF obbligatorio anche per PG
- `__str__` include CF nel formato

**Fix Necessario**: Aggiornare test con CF/PIVA reali e validi

---

### Categoria 2: Static Files (11 fallimenti)

**Problema**: `ValueError: Missing staticfiles manifest entry for 'css/app.css'`

```
FAILED anagrafiche/tests.py::AnagraficaDetailCommunicationsTests::test_comunicazioni_in_context_ordered_desc
FAILED archivio_fisico/tests.py::UnitaListViewTests::test_clienti_tree_present_in_context
FAILED archivio_fisico/tests.py::UnitaListViewTests::test_clienti_tree_with_corrente_data
FAILED archivio_fisico/tests.py::UnitaListViewTests::test_fascicolo_without_ubicazione_included_via_document_collocazione
FAILED archivio_fisico/tests.py::UnitaInventoryTreeViewTests::test_inventory_tree_empty
FAILED archivio_fisico/tests.py::UnitaInventoryTreeViewTests::test_inventory_tree_with_fascicoli_and_documents
FAILED archivio_fisico/tests.py::OperazioneArchivioViewTests::test_operazione_create_with_verbale_scan
FAILED comunicazioni/tests/test_templates.py::ComunicazioniTemplateViewTests::test_applica_template_popola_corpo
FAILED pratiche/tests.py::PraticheAppTests::test_home_view_orders_scadenze
FAILED pratiche/tests.py::PraticheAppTests::test_modifica_pratica_dalla_dettaglio_action
```

**Causa**: django-compressor abilitato in test senza manifest

**Fix Necessario**: 
```python
# pytest.ini o conftest.py
@pytest.fixture(autouse=True)
def disable_compression(settings):
    settings.COMPRESS_ENABLED = False
    settings.COMPRESS_OFFLINE = False
```

---

### Categoria 3: Redis/Hiredis (1 fallimento)

```
FAILED comunicazioni/tests/test_rubrica.py::ComunicazioniApiTests::test_lista_comunicazioni_api
ImportError: Module "redis.connection" does not define a "HiredisParser" attribute/class
```

**Causa**: Hiredis non installato o incompatibile

**Fix**: Opzionale in settings Redis
```python
"OPTIONS": {
    "PARSER_CLASS": "redis.connection.DefaultParser",  # Invece di HiredisParser
}
```

---

### Categoria 4: Antivirus Validator (2 fallimenti)

```
FAILED documenti/tests/test_validators.py::AntivirusValidatorTest::test_eicar_virus
FAILED documenti/tests/test_validators.py::IntegrationTest::test_documento_file_field_has_validator
```

**Causa**: ClamAV non configurato in ambiente test

**Fix**: Mock ClamAV in test o skip se non disponibile

---

### Categoria 5: Altri (2 fallimenti)

```
FAILED documenti/tests/test_validators.py::IntegrationTest::test_upload_invalid_file_raises_validation_error
TypeError: Cliente() got unexpected keyword arguments: 'attivo'

FAILED titolario/tests.py::SeedTest::test_seed_titolario_roots_present
AssertionError: False is not true
```

---

## ✅ Test Passati Correttamente (79)

- ✅ **pratiche/tests.py**: 76 test passati (82.89% coverage)
- ✅ **protocollo/tests.py**: 100% test passati (70.05% coverage)
- ✅ **whatsapp/tests.py**: 100% test passati (91.03% coverage!)
- ✅ **scadenze**: 80.95% coverage
- ✅ Test integrazione base funzionanti

---

## 🎯 Prossimi Step (in ordine di priorità)

### 1. Fix Test Validators (Alta Priorità)

```bash
# Fix CF/PIVA con checksum reali
# File: anagrafiche/tests/test_validators.py
```

**Azione**: Sostituire CF/PIVA fake con valori reali o usare libreria generatrice

### 2. Fix Static Files in Test (Alta Priorità)

```bash
# Aggiungi a conftest.py
@pytest.fixture(autouse=True)
def disable_static_compression(settings):
    settings.COMPRESS_ENABLED = False
    settings.COMPRESS_OFFLINE = False
    settings.STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
```

### 3. Fix Redis/Hiredis (Media Priorità)

```bash
pip install hiredis
# oppure cambia parser in settings
```

### 4. Mock ClamAV (Bassa Priorità)

```python
@pytest.fixture
def mock_clamav(monkeypatch):
    def fake_scan(*args, **kwargs):
        return {'stream': ('OK', None)}
    monkeypatch.setattr('pyclamd.ClamdUnixSocket.scan_stream', fake_scan)
```

### 5. Aumentare Coverage Stampe (Media Priorità)

**Target**: da 8.04% → 60%+  
**Focus**: Test per layouts e services (709 statements, 652 miss)

---

## 📈 Roadmap Coverage

| Milestone | Target | Azioni |
|-----------|--------|--------|
| **Fase 1** | 60% | Fix test falliti + static files |
| **Fase 2** | 70% | Test documenti views/forms |
| **Fase 3** | 75% | Test stampe services |
| **Fase 4** | 80% | Test views mancanti |
| **Fase 5** | 85%+ | Edge cases + error handling |

---

## 🔧 Comandi Utili

```bash
# Run solo test passati (veloce)
pytest -v --lf

# Run solo test specifici
pytest -v anagrafiche/tests/test_validators.py

# Coverage dettagliato per app
pytest --cov=anagrafiche --cov-report=term-missing

# Skip test lenti/problematici
pytest -m "not slow" -v

# Test in parallelo
pytest -n auto

# Stop al primo errore
pytest -x
```

---

## 📌 Note Importanti

1. **Coverage è aumentato significativamente**: da 22.54% → 48.90%
2. **79 test funzionano correttamente** - buona base!
3. **Problemi principali**: Validators e Static Files (facilmente risolvibili)
4. **WhatsApp ha 91% coverage** - ottimo esempio da seguire
5. **Stampe necessita attenzione** - solo 8% coverage

---

## 🎓 Lessons Learned

1. ✅ Fixture globali in conftest.py funzionano perfettamente
2. ✅ pytest markers utili per organizzazione
3. ⚠️ Static files compression va disabilitata in test
4. ⚠️ Validatori reali più restrittivi dei test fake
5. ⚠️ Dipendenze esterne (ClamAV, Redis) vanno mockate

---

**Prossima azione consigliata**: Fix static files (impatto su 11 test) poi validators (impatto su 12 test)
