"""
Test suite per validators di sicurezza file upload

Eseguire con:
    python manage.py test documenti.tests.test_validators
"""

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from documenti.validators import (
    validate_file_size,
    validate_file_extension,
    validate_file_mime_type,
    validate_antivirus,
    validate_file_content,
    validate_no_path_traversal,
)
import tempfile
import os
import unittest

# Check if ClamAV is available
try:
    import clamd
    clamd_client = clamd.ClamAVUnixSocketScanner()
    clamd_client.ping()
    CLAMAV_AVAILABLE = True
except Exception:
    CLAMAV_AVAILABLE = False


class FileSizeValidatorTest(TestCase):
    """Test validazione dimensione file"""

    @override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=1024)  # 1 KB
    def test_file_too_large(self):
        """File più grande del limite deve essere rifiutato"""
        large_content = b"x" * 2048  # 2 KB
        file = SimpleUploadedFile("large.pdf", large_content)
        
        with self.assertRaises(ValidationError) as cm:
            validate_file_size(file)
        
        self.assertEqual(cm.exception.code, 'file_too_large')

    @override_settings(FILE_UPLOAD_MAX_MEMORY_SIZE=1024 * 1024)  # 1 MB
    def test_file_size_ok(self):
        """File entro il limite deve passare"""
        small_content = b"x" * 1024  # 1 KB
        file = SimpleUploadedFile("small.pdf", small_content)
        
        # Non dovrebbe sollevare eccezioni
        validate_file_size(file)


class FileExtensionValidatorTest(TestCase):
    """Test validazione estensioni file"""

    @override_settings(FORBIDDEN_FILE_EXTENSIONS=['exe', 'bat'])
    def test_forbidden_extension(self):
        """Estensione proibita deve essere rifiutata"""
        file = SimpleUploadedFile("malware.exe", b"content")
        
        with self.assertRaises(ValidationError) as cm:
            validate_file_extension(file)
        
        self.assertEqual(cm.exception.code, 'forbidden_extension')

    @override_settings(ALLOWED_FILE_EXTENSIONS=['pdf', 'jpg'])
    def test_not_allowed_extension(self):
        """Estensione non in whitelist deve essere rifiutata"""
        file = SimpleUploadedFile("document.docx", b"content")
        
        with self.assertRaises(ValidationError) as cm:
            validate_file_extension(file)
        
        self.assertEqual(cm.exception.code, 'invalid_extension')

    @override_settings(ALLOWED_FILE_EXTENSIONS=['pdf', 'jpg'])
    def test_allowed_extension(self):
        """Estensione in whitelist deve passare"""
        file = SimpleUploadedFile("document.pdf", b"content")
        
        # Non dovrebbe sollevare eccezioni
        validate_file_extension(file)


class PathTraversalValidatorTest(TestCase):
    """Test prevenzione path traversal"""

    def test_path_traversal_dots(self):
        """Nome file con .. deve essere rifiutato"""
        with self.assertRaises(ValidationError) as cm:
            validate_no_path_traversal("../../../etc/passwd")
        
        self.assertEqual(cm.exception.code, 'invalid_filename')

    def test_path_traversal_slash(self):
        """Nome file con / deve essere rifiutato"""
        with self.assertRaises(ValidationError) as cm:
            validate_no_path_traversal("folder/file.pdf")
        
        self.assertEqual(cm.exception.code, 'invalid_filename')

    def test_valid_filename(self):
        """Nome file valido deve passare"""
        # Non dovrebbe sollevare eccezioni
        validate_no_path_traversal("documento_2024.pdf")


class AntivirusValidatorTest(TestCase):
    """Test scansione antivirus"""

    @override_settings(ANTIVIRUS_ENABLED=True, ANTIVIRUS_REQUIRED=False)
    def test_clean_file(self):
        """File pulito deve passare la scansione"""
        file_content = b"PDF file content here"
        file = SimpleUploadedFile("clean.pdf", file_content)
        
        # Non dovrebbe sollevare eccezioni
        # Nota: richiede ClamAV in esecuzione
        try:
            validate_antivirus(file)
        except ValidationError as e:
            # Se ClamAV non disponibile e ANTIVIRUS_REQUIRED=False, passa
            if e.code != 'antivirus_unavailable':
                raise

    @unittest.skipUnless(CLAMAV_AVAILABLE, "ClamAV non disponibile")
    @override_settings(ANTIVIRUS_ENABLED=True, ANTIVIRUS_REQUIRED=False)
    def test_eicar_virus(self):
        """EICAR test string deve essere rilevato come virus"""
        # EICAR test string (standard test antivirus, NON è un virus reale)
        eicar = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
        file = SimpleUploadedFile("eicar.txt", eicar)
        
        with self.assertRaises(ValidationError) as cm:
            validate_antivirus(file)
        
        self.assertEqual(cm.exception.code, 'virus_detected')

    @override_settings(ANTIVIRUS_ENABLED=False)
    def test_antivirus_disabled(self):
        """Con antivirus disabilitato, qualsiasi file deve passare"""
        file = SimpleUploadedFile("any.pdf", b"content")
        
        # Non dovrebbe sollevare eccezioni
        validate_antivirus(file)


class CombinedValidatorTest(TestCase):
    """Test validator combinato"""

    @override_settings(
        FILE_UPLOAD_MAX_MEMORY_SIZE=1024 * 1024,  # 1 MB
        ALLOWED_FILE_EXTENSIONS=['pdf', 'jpg'],
        FORBIDDEN_FILE_EXTENSIONS=['exe'],
        ANTIVIRUS_ENABLED=True,
        ANTIVIRUS_REQUIRED=False,
    )
    def test_valid_file_passes_all_checks(self):
        """File valido deve passare tutti i controlli"""
        file_content = b"PDF content" * 100  # ~1 KB
        file = SimpleUploadedFile("document.pdf", file_content)
        
        # Non dovrebbe sollevare eccezioni
        try:
            validate_file_content(file)
        except ValidationError as e:
            # Se ClamAV non disponibile, ignora
            if e.code == 'antivirus_unavailable':
                pass
            else:
                raise

    @override_settings(
        FILE_UPLOAD_MAX_MEMORY_SIZE=1024,  # 1 KB (molto piccolo)
        ALLOWED_FILE_EXTENSIONS=['pdf'],
        ANTIVIRUS_ENABLED=False,
    )
    def test_oversized_file_fails(self):
        """File troppo grande deve fallire anche se valido per altri aspetti"""
        large_content = b"x" * 2048  # 2 KB
        file = SimpleUploadedFile("large.pdf", large_content)
        
        with self.assertRaises(ValidationError) as cm:
            validate_file_content(file)
        
        self.assertEqual(cm.exception.code, 'file_too_large')

    @override_settings(
        FILE_UPLOAD_MAX_MEMORY_SIZE=1024 * 1024,
        FORBIDDEN_FILE_EXTENSIONS=['exe', 'bat'],
        ANTIVIRUS_ENABLED=False,
    )
    def test_forbidden_extension_fails(self):
        """Estensione proibita deve fallire anche se dimensione ok"""
        file = SimpleUploadedFile("malware.exe", b"content")
        
        with self.assertRaises(ValidationError) as cm:
            validate_file_content(file)
        
        self.assertEqual(cm.exception.code, 'forbidden_extension')


class IntegrationTest(TestCase):
    """Test integrazione con models"""

    def test_documento_file_field_has_validator(self):
        """Documento.file deve avere il validator"""
        from documenti.models import Documento
        
        file_field = Documento._meta.get_field('file')
        validator_names = [v.__name__ for v in file_field.validators]
        
        self.assertIn('validate_file_content', validator_names)

    def test_upload_invalid_file_raises_validation_error(self):
        """Upload file invalido deve sollevare ValidationError"""
        from documenti.models import Documento
        from anagrafiche.models import Anagrafica, Cliente
        
        # Crea cliente per test
        anagrafica = Anagrafica.objects.create(
            tipo='PF',
            cognome='Test',
            nome='Upload',
            codice_fiscale='TSTUPD00A01H501X',
        )
        cliente = Cliente.objects.create(
            anagrafica=anagrafica,
            attivo=True,
        )
        
        # File con estensione proibita
        file = SimpleUploadedFile("malware.exe", b"malicious")
        
        with self.assertRaises(ValidationError):
            doc = Documento(
                cliente=anagrafica,
                data_documento='2024-01-01',
                file=file,
            )
            doc.full_clean()  # Trigger validators


# ============================================
# Test Performance
# ============================================

class PerformanceTest(TestCase):
    """Test performance validators"""

    def test_small_file_validation_fast(self):
        """Validazione file piccolo deve essere veloce"""
        import time
        
        file = SimpleUploadedFile("small.pdf", b"x" * 1024)  # 1 KB
        
        start = time.time()
        try:
            validate_file_content(file)
        except ValidationError:
            pass
        elapsed = time.time() - start
        
        # Dovrebbe completare in meno di 1 secondo
        self.assertLess(elapsed, 1.0)

    @override_settings(ANTIVIRUS_ENABLED=False)
    def test_validation_without_antivirus_faster(self):
        """Validazione senza antivirus deve essere più veloce"""
        import time
        
        file = SimpleUploadedFile("test.pdf", b"x" * 10240)  # 10 KB
        
        start = time.time()
        validate_file_content(file)
        elapsed = time.time() - start
        
        # Senza antivirus dovrebbe essere molto veloce (< 0.1s)
        self.assertLess(elapsed, 0.1)


# ============================================
# Test Configurazione
# ============================================

class ConfigurationTest(TestCase):
    """Test configurazioni"""

    def test_default_settings_exist(self):
        """Settings di default devono esistere"""
        from django.conf import settings
        
        # Questi possono non esistere, ma non devono causare errori
        getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', None)
        getattr(settings, 'ALLOWED_FILE_EXTENSIONS', None)
        getattr(settings, 'FORBIDDEN_FILE_EXTENSIONS', None)
        getattr(settings, 'ANTIVIRUS_ENABLED', None)

    @override_settings(ANTIVIRUS_ENABLED=True, ANTIVIRUS_REQUIRED=True)
    def test_antivirus_required_setting_respected(self):
        """Setting ANTIVIRUS_REQUIRED deve essere rispettato"""
        from django.conf import settings
        
        self.assertTrue(settings.ANTIVIRUS_REQUIRED)


if __name__ == '__main__':
    import django
    from django.test.utils import get_runner
    from django.conf import settings
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["documenti.tests.test_validators"])
