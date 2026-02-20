#!/usr/bin/env python
"""
Script di verifica rapida della configurazione storage MyGest.

Uso:
    python scripts/check_storage.py
"""

import os
import sys
from pathlib import Path

# Aggiungi la directory base al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
import django
django.setup()

from django.conf import settings
from django.core.files.base import ContentFile
from mygest.storages import NASPathStorage


def print_header(text):
    """Stampa un header formattato"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_check(passed, message):
    """Stampa il risultato di un check"""
    symbol = "✓" if passed else "✗"
    status = "OK" if passed else "ERRORE"
    print(f"  [{symbol}] {status:8} - {message}")


def main():
    print_header("VERIFICA CONFIGURAZIONE STORAGE MYGEST")
    
    # 1. Verifica configurazione
    print("1. CONFIGURAZIONE")
    print(f"   ARCHIVIO_BASE_PATH: {settings.ARCHIVIO_BASE_PATH}")
    print(f"   MEDIA_ROOT:         {settings.MEDIA_ROOT}")
    print(f"   MEDIA_URL:          {settings.MEDIA_URL}")
    
    # 2. Verifica storage
    print("\n2. STORAGE")
    storage = NASPathStorage()
    print(f"   Storage location:   {storage.location}")
    
    # 3. Verifica directory
    print("\n3. DIRECTORY")
    archivio_path = Path(settings.ARCHIVIO_BASE_PATH)
    
    exists = archivio_path.exists()
    print_check(exists, f"Directory esiste: {archivio_path}")
    
    if exists:
        is_dir = archivio_path.is_dir()
        print_check(is_dir, "È una directory")
        
        if is_dir:
            readable = os.access(archivio_path, os.R_OK)
            print_check(readable, "Permessi di lettura")
            
            writable = os.access(archivio_path, os.W_OK)
            print_check(writable, "Permessi di scrittura")
            
            # Mostra proprietario e permessi
            stat_info = archivio_path.stat()
            from pwd import getpwuid
            owner = getpwuid(stat_info.st_uid).pw_name
            print(f"   Proprietario:       {owner}")
            print(f"   Permessi:           {oct(stat_info.st_mode)[-3:]}")
    
    # 4. Test scrittura (se possibile)
    print("\n4. TEST SCRITTURA")
    if exists and writable:
        try:
            test_name = storage.save('_test_storage/prova.txt', ContentFile(b'Test MyGest Storage'))
            test_path = storage.path(test_name)
            print_check(True, f"File test creato: {test_path}")
            
            # Verifica lettura
            with storage.open(test_name, 'r') as f:
                content = f.read()
            print_check(content == 'Test MyGest Storage', "Contenuto verificato")
            
            # Elimina file test
            storage.delete(test_name)
            print_check(True, "File test eliminato")
            
            # Elimina directory test se vuota
            test_dir = Path(storage.location) / '_test_storage'
            if test_dir.exists() and not list(test_dir.iterdir()):
                test_dir.rmdir()
                print_check(True, "Directory test eliminata")
            
        except Exception as e:
            print_check(False, f"Errore nel test: {e}")
    else:
        print_check(False, "Test scrittura non eseguito (directory non accessibile)")
    
    # 5. Verifica sottodirectory
    print("\n5. STRUTTURA DIRECTORY")
    expected_dirs = ['documenti', 'archivio_fisico', 'fascicoli']
    for dir_name in expected_dirs:
        dir_path = archivio_path / dir_name
        exists = dir_path.exists()
        if exists:
            print(f"   ✓ {dir_name}/")
        else:
            print(f"   - {dir_name}/ (non ancora creata)")
    
    # 6. Statistiche
    print("\n6. STATISTICHE")
    if exists and is_dir:
        total_files = 0
        total_size = 0
        for root, dirs, files in os.walk(archivio_path):
            total_files += len(files)
            for file in files:
                try:
                    total_size += (Path(root) / file).stat().st_size
                except:
                    pass
        
        print(f"   File totali:        {total_files}")
        print(f"   Dimensione totale:  {total_size / 1024 / 1024:.2f} MB")
    
    # Conclusione
    print_header("VERIFICA COMPLETATA")
    
    if exists and writable:
        print("✅ Lo storage è configurato correttamente e funzionante!\n")
        return 0
    elif exists:
        print("⚠️  Lo storage esiste ma non è scrivibile.")
        print("   Verifica i permessi della directory.\n")
        return 1
    else:
        print("❌ Lo storage non è configurato correttamente.")
        print(f"   La directory {archivio_path} non esiste.\n")
        print("   Consulta: docs/setup_archivio_locale.md\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
