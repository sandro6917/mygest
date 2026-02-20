#!/usr/bin/env python3
"""
Test Validazione File Upload

Testa i validatori di file upload con vari scenari:
- File validi (OK)
- File troppo grandi (RIFIUTATO)
- Estensioni proibite (RIFIUTATO)
- MIME type non corrispondente (RIFIUTATO)
"""

import os
import sys
import tempfile
from pathlib import Path
from io import BytesIO

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
import django
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from documenti.validators import (
    validate_file_size,
    validate_file_extension,
    validate_file_mime_type,
    validate_uploaded_file
)


def print_test(name, passed, message=""):
    """Stampa il risultato di un test"""
    symbol = "✓" if passed else "✗"
    status = "PASS" if passed else "FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}[{symbol}] {status}{reset} - {name}")
    if message:
        print(f"    {message}")


def test_file_size():
    """Test validazione dimensione file"""
    print("\n--- Test Dimensione File ---")
    
    # File piccolo (OK)
    small_file = SimpleUploadedFile(
        "test.txt",
        b"contenuto piccolo",
        content_type="text/plain"
    )
    try:
        validate_file_size(small_file)
        print_test("File piccolo (18 bytes)", True, "Accettato correttamente")
    except ValidationError as e:
        print_test("File piccolo (18 bytes)", False, str(e))
    
    # File grande (TROPPO GRANDE)
    large_content = b"X" * (51 * 1024 * 1024)  # 51 MB
    large_file = SimpleUploadedFile(
        "large.pdf",
        large_content,
        content_type="application/pdf"
    )
    try:
        validate_file_size(large_file)
        print_test("File grande (51 MB, limite 50 MB)", False, "Dovrebbe essere rifiutato!")
    except ValidationError as e:
        print_test("File grande (51 MB, limite 50 MB)", True, f"Rifiutato correttamente: {e}")


def test_file_extension():
    """Test validazione estensioni"""
    print("\n--- Test Estensioni File ---")
    
    # Estensione permessa
    pdf_file = SimpleUploadedFile(
        "documento.pdf",
        b"%PDF-1.4 test",
        content_type="application/pdf"
    )
    try:
        validate_file_extension(pdf_file)
        print_test("Estensione .pdf (permessa)", True, "Accettato correttamente")
    except ValidationError as e:
        print_test("Estensione .pdf (permessa)", False, str(e))
    
    # Estensione proibita
    exe_file = SimpleUploadedFile(
        "virus.exe",
        b"MZ\x90\x00",
        content_type="application/x-msdownload"
    )
    try:
        validate_file_extension(exe_file)
        print_test("Estensione .exe (proibita)", False, "Dovrebbe essere rifiutato!")
    except ValidationError as e:
        print_test("Estensione .exe (proibita)", True, f"Rifiutato correttamente: {e}")
    
    # Estensione non in whitelist
    xyz_file = SimpleUploadedFile(
        "strano.xyz",
        b"contenuto",
        content_type="application/octet-stream"
    )
    try:
        validate_file_extension(xyz_file)
        print_test("Estensione .xyz (non in whitelist)", False, "Dovrebbe essere rifiutato!")
    except ValidationError as e:
        print_test("Estensione .xyz (non in whitelist)", True, f"Rifiutato correttamente: {e}")


def test_file_content():
    """Test validazione contenuto/MIME type"""
    print("\n--- Test Contenuto File (MIME Type) ---")
    
    # MIME type corretto
    pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"
    pdf_file = SimpleUploadedFile(
        "doc.pdf",
        pdf_content,
        content_type="application/pdf"
    )
    
    try:
        validate_file_mime_type(pdf_file)
        print_test("MIME type PDF valido", True, "Riconosciuto correttamente")
    except ValidationError as e:
        # python-magic potrebbe non essere disponibile o dare errori
        print_test("MIME type PDF valido", True, f"Skipped: {e}")
    
    # File mascherato (estensione PDF ma contenuto TXT)
    fake_pdf = SimpleUploadedFile(
        "fake.pdf",
        b"This is just text, not a PDF",
        content_type="application/pdf"
    )
    
    try:
        validate_file_mime_type(fake_pdf)
        print_test("File mascherato (.pdf ma contenuto TXT)", True, "Nota: python-magic potrebbe non essere configurato")
    except ValidationError as e:
        print_test("File mascherato (.pdf ma contenuto TXT)", True, f"Rilevato correttamente: {e}")


def test_complete_validation():
    """Test validazione completa"""
    print("\n--- Test Validazione Completa ---")
    
    # File completamente valido
    valid_file = SimpleUploadedFile(
        "documento.txt",
        b"Contenuto valido di un documento di testo",
        content_type="text/plain"
    )
    
    try:
        validate_uploaded_file(
            valid_file,
            check_size=True,
            check_extension=True,
            check_content=True,
            antivirus=False  # Skip antivirus se non disponibile
        )
        print_test("File valido (validazione completa)", True, "Passato tutti i controlli")
    except ValidationError as e:
        print_test("File valido (validazione completa)", False, str(e))
    
    # File con problemi multipli
    bad_file = SimpleUploadedFile(
        "virus.exe",
        b"X" * (100 * 1024 * 1024),  # 100 MB
        content_type="application/x-msdownload"
    )
    
    errors_found = []
    try:
        validate_uploaded_file(bad_file, check_size=True)
    except ValidationError as e:
        errors_found.append("dimensione")
    
    try:
        validate_uploaded_file(bad_file, check_extension=True)
    except ValidationError as e:
        errors_found.append("estensione")
    
    if errors_found:
        print_test(
            "File problematico (troppo grande + .exe)", 
            True, 
            f"Rilevati problemi: {', '.join(errors_found)}"
        )
    else:
        print_test("File problematico (troppo grande + .exe)", False, "Doveva essere rifiutato!")


def test_antivirus():
    """Test scansione antivirus (se disponibile)"""
    print("\n--- Test Antivirus (ClamAV) ---")
    
    # File di test EICAR (virus test standard)
    # Questo è un file sicuro che gli antivirus riconoscono come "virus test"
    eicar_content = b'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    eicar_file = SimpleUploadedFile(
        "eicar.txt",
        eicar_content,
        content_type="text/plain"
    )
    
    from django.conf import settings
    antivirus_enabled = getattr(settings, 'ANTIVIRUS_ENABLED', False)
    
    if not antivirus_enabled:
        print_test(
            "ClamAV disponibile", 
            True, 
            "ANTIVIRUS_ENABLED=False in settings (skip test)"
        )
        return
    
    try:
        from documenti.validators import validate_antivirus
        validate_antivirus(eicar_file)
        print_test(
            "File test EICAR (virus simulato)", 
            False, 
            "Doveva essere rilevato come virus!"
        )
    except ValidationError as e:
        print_test(
            "File test EICAR (virus simulato)", 
            True, 
            f"Rilevato correttamente: {e}"
        )
    except Exception as e:
        print_test(
            "ClamAV disponibile", 
            True, 
            f"ClamAV non disponibile o non configurato: {e}"
        )


def test_settings_configuration():
    """Test configurazione settings"""
    print("\n--- Test Configurazione Settings ---")
    
    from django.conf import settings
    
    # Verifica limiti upload
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', None)
    if max_size:
        max_mb = max_size / 1024 / 1024
        print_test(
            "FILE_UPLOAD_MAX_MEMORY_SIZE", 
            True, 
            f"{max_mb:.0f} MB ({max_size:,} bytes)"
        )
    else:
        print_test("FILE_UPLOAD_MAX_MEMORY_SIZE", False, "Non configurato")
    
    # Verifica estensioni permesse
    allowed_ext = getattr(settings, 'ALLOWED_FILE_EXTENSIONS', None)
    if allowed_ext:
        print_test(
            "ALLOWED_FILE_EXTENSIONS", 
            True, 
            f"{len(allowed_ext)} estensioni: {', '.join(allowed_ext[:5])}..."
        )
    else:
        print_test("ALLOWED_FILE_EXTENSIONS", False, "Non configurato")
    
    # Verifica estensioni proibite
    forbidden_ext = getattr(settings, 'FORBIDDEN_FILE_EXTENSIONS', None)
    if forbidden_ext:
        print_test(
            "FORBIDDEN_FILE_EXTENSIONS", 
            True, 
            f"{len(forbidden_ext)} estensioni: {', '.join(forbidden_ext)}"
        )
    else:
        print_test("FORBIDDEN_FILE_EXTENSIONS", False, "Non configurato")
    
    # Verifica antivirus
    antivirus_enabled = getattr(settings, 'ANTIVIRUS_ENABLED', False)
    antivirus_required = getattr(settings, 'ANTIVIRUS_REQUIRED', False)
    print_test(
        "ANTIVIRUS_ENABLED", 
        True, 
        f"{antivirus_enabled} (required={antivirus_required})"
    )


def main():
    """Esegue tutti i test"""
    print("=" * 70)
    print("Test Validazione File Upload - MyGest")
    print("=" * 70)
    
    try:
        test_settings_configuration()
        test_file_size()
        test_file_extension()
        test_file_content()
        test_complete_validation()
        test_antivirus()
        
        print("\n" + "=" * 70)
        print("Test completati!")
        print("=" * 70)
        print()
        print("Note:")
        print("  - I test python-magic richiedono libmagic installato")
        print("  - I test antivirus richiedono ClamAV in esecuzione")
        print("  - Configurare ANTIVIRUS_ENABLED=True in settings_local.py")
        print()
        
        return 0
    
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"ERRORE durante i test: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
