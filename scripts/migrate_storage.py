#!/usr/bin/env python
"""
Script per migrare i file dall'archivio locale media/ alla nuova struttura.

Uso:
    python scripts/migrate_storage.py --dry-run  # Mostra cosa verrà fatto senza eseguire
    python scripts/migrate_storage.py            # Esegue la migrazione
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# Aggiungi la directory base al path per importare Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
import django
django.setup()

from django.conf import settings


def migrate_files(dry_run=False):
    """
    Migra i file da media/ alla directory configurata in ARCHIVIO_BASE_PATH
    """
    old_media = BASE_DIR / 'media'
    new_archivio = Path(settings.ARCHIVIO_BASE_PATH)
    
    print("=" * 80)
    print("MIGRAZIONE STORAGE MYGEST")
    print("=" * 80)
    print(f"Origine:      {old_media}")
    print(f"Destinazione: {new_archivio}")
    print(f"Modalità:     {'DRY-RUN (simulazione)' if dry_run else 'ESECUZIONE REALE'}")
    print("=" * 80)
    print()
    
    # Verifica che la directory di origine esista
    if not old_media.exists():
        print(f"✓ Directory di origine {old_media} non esiste. Nessuna migrazione necessaria.")
        return
    
    # Verifica che la directory di destinazione esista
    if not new_archivio.exists():
        print(f"✗ ERRORE: La directory di destinazione {new_archivio} non esiste!")
        print(f"  Crea la directory o monta il NAS prima di eseguire la migrazione.")
        return
    
    # Conta i file da migrare
    files_to_migrate = []
    for root, dirs, files in os.walk(old_media):
        for filename in files:
            src_path = Path(root) / filename
            rel_path = src_path.relative_to(old_media)
            dst_path = new_archivio / rel_path
            files_to_migrate.append((src_path, dst_path, rel_path))
    
    if not files_to_migrate:
        print("✓ Nessun file da migrare.")
        return
    
    print(f"Trovati {len(files_to_migrate)} file da migrare.\n")
    
    # Mostra i file da migrare
    for src_path, dst_path, rel_path in files_to_migrate:
        size_kb = src_path.stat().st_size / 1024
        print(f"  • {rel_path} ({size_kb:.1f} KB)")
    
    print()
    
    if dry_run:
        print("=" * 80)
        print("DRY-RUN COMPLETATO: Nessun file è stato spostato.")
        print("Esegui senza --dry-run per effettuare la migrazione reale.")
        print("=" * 80)
        return
    
    # Chiedi conferma
    print("=" * 80)
    response = input("Procedere con la migrazione? [s/N]: ")
    if response.lower() != 's':
        print("Migrazione annullata dall'utente.")
        return
    
    print()
    print("Inizio migrazione...")
    print()
    
    # Esegui la migrazione
    migrated = 0
    errors = 0
    
    for src_path, dst_path, rel_path in files_to_migrate:
        try:
            # Crea la directory di destinazione se non esiste
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copia il file (manteniamo l'originale per sicurezza)
            shutil.copy2(src_path, dst_path)
            print(f"✓ Copiato: {rel_path}")
            migrated += 1
            
        except Exception as e:
            print(f"✗ ERRORE copiando {rel_path}: {e}")
            errors += 1
    
    print()
    print("=" * 80)
    print(f"MIGRAZIONE COMPLETATA")
    print(f"  File copiati: {migrated}")
    print(f"  Errori:       {errors}")
    print("=" * 80)
    
    if errors == 0:
        print()
        print("IMPORTANTE:")
        print("1. Verifica che i file siano stati copiati correttamente")
        print("2. Testa l'applicazione per assicurarti che tutto funzioni")
        print("3. Dopo la verifica, puoi eliminare la directory media/ con:")
        print(f"   rm -rf {old_media}")
        print()
    else:
        print()
        print("⚠️  ATTENZIONE: Alcuni file non sono stati copiati correttamente!")
        print("   Controlla gli errori sopra prima di procedere.")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Migra i file da media/ al nuovo archivio"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Mostra cosa verrà fatto senza eseguire la migrazione"
    )
    
    args = parser.parse_args()
    migrate_files(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
