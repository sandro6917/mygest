# Test Validators File Upload

## Esecuzione Test

### Tutti i test
```bash
python manage.py test documenti.tests.test_validators
```

### Test specifici
```bash
# Solo test dimensione file
python manage.py test documenti.tests.test_validators.FileSizeValidatorTest

# Solo test antivirus
python manage.py test documenti.tests.test_validators.AntivirusValidatorTest

# Solo test integrazione
python manage.py test documenti.tests.test_validators.IntegrationTest
```

### Con coverage
```bash
pip install coverage
coverage run --source='documenti' manage.py test documenti.tests.test_validators
coverage report
coverage html  # Genera report HTML
```

## Prerequisiti Test

### ClamAV (per test antivirus)
I test antivirus richiedono ClamAV in esecuzione:
```bash
sudo systemctl start clamav-daemon
```

Se ClamAV non è disponibile, i test antivirus saranno skippati automaticamente.

### EICAR Test File
I test usano la stringa EICAR standard per testare la rilevazione virus.
EICAR è un file di test NON pericoloso, riconosciuto da tutti gli antivirus.

## Test Coverage

I test coprono:

- ✅ Validazione dimensione file (limite superato/ok)
- ✅ Validazione estensioni (whitelist/blacklist)
- ✅ Path traversal prevention
- ✅ Scansione antivirus (file pulito/infetto)
- ✅ Validator combinato
- ✅ Integrazione con models Django
- ✅ Performance validation
- ✅ Configurazioni settings

## Esecuzione in CI/CD

### GitHub Actions
```yaml
- name: Run validator tests
  run: |
    python manage.py test documenti.tests.test_validators
  env:
    ANTIVIRUS_ENABLED: false  # Skip antivirus in CI
```

### GitLab CI
```yaml
test_validators:
  script:
    - python manage.py test documenti.tests.test_validators
  variables:
    ANTIVIRUS_ENABLED: "false"
```

## Test Manuali

### Test upload reale
```python
python manage.py shell

from django.core.files.uploadedfile import SimpleUploadedFile
from documenti.validators import validate_file_content

# Test file valido
file = SimpleUploadedFile("test.pdf", b"PDF content")
validate_file_content(file)  # Dovrebbe passare

# Test file troppo grande (>50MB con default settings)
large = SimpleUploadedFile("large.pdf", b"x" * (60 * 1024 * 1024))
validate_file_content(large)  # Dovrebbe fallire

# Test estensione proibita
exe = SimpleUploadedFile("malware.exe", b"content")
validate_file_content(exe)  # Dovrebbe fallire
```

## Note

- Test antivirus richiedono ~1 secondo per file
- Test con ANTIVIRUS_ENABLED=false sono molto più veloci
- EICAR test string è sicura, non è un virus reale
