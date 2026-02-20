#!/usr/bin/env python3
"""
Script per esecuzione via cron: pulisce i file in una directory staging.

Questo script è progettato per essere eseguito periodicamente via cron.
Elimina i file più vecchi di un certo tempo dalla directory di staging.

Uso:
    python cron_cleanup.py --staging-dir /percorso/staging --max-age 3600
    
Esempio cron (ogni 5 minuti):
    */5 * * * * cd /home/sandro/mygest/scripts && /usr/bin/python3 cron_cleanup.py --staging-dir /home/sandro/upload-staging --max-age 300
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
log_file = os.path.join(os.path.dirname(__file__), 'cron_cleanup.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CronCleanup')


def cleanup_old_files(staging_dir: str, max_age_seconds: int, 
                     extensions: list = None, dry_run: bool = False) -> dict:
    """
    Elimina i file più vecchi di max_age_seconds dalla directory.
    
    Args:
        staging_dir: Directory da pulire
        max_age_seconds: Età massima dei file in secondi
        extensions: Lista di estensioni da considerare (None = tutte)
        dry_run: Se True, simula senza eliminare
        
    Returns:
        Dizionario con statistiche: {deleted: int, errors: int, size_freed: int}
    """
    staging_path = Path(staging_dir).resolve()
    
    if not staging_path.exists():
        logger.error(f"Directory non trovata: {staging_path}")
        return {'deleted': 0, 'errors': 1, 'size_freed': 0}
    
    stats = {
        'deleted': 0,
        'errors': 0,
        'size_freed': 0,
        'skipped': 0
    }
    
    current_time = time.time()
    cutoff_time = current_time - max_age_seconds
    
    logger.info(f"Scansione directory: {staging_path}")
    logger.info(f"Età massima: {max_age_seconds}s ({max_age_seconds/60:.1f} minuti)")
    
    # Scansiona tutti i file
    for file_path in staging_path.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Filtra per estensione se specificato
        if extensions and file_path.suffix.lower() not in extensions:
            stats['skipped'] += 1
            continue
        
        try:
            # Ottieni il tempo di modifica
            mtime = file_path.stat().st_mtime
            
            # Verifica se è abbastanza vecchio
            if mtime < cutoff_time:
                file_size = file_path.stat().st_size
                age_minutes = (current_time - mtime) / 60
                
                logger.info(
                    f"File da eliminare: {file_path.name} "
                    f"(età: {age_minutes:.1f} min, dimensione: {file_size} bytes)"
                )
                
                if not dry_run:
                    file_path.unlink()
                    stats['deleted'] += 1
                    stats['size_freed'] += file_size
                else:
                    logger.info(f"[DRY RUN] Sarebbe stato eliminato: {file_path}")
                    stats['deleted'] += 1
                    stats['size_freed'] += file_size
                    
        except Exception as e:
            logger.error(f"Errore elaborando {file_path}: {e}")
            stats['errors'] += 1
    
    # Pulisci directory vuote
    if not dry_run:
        try:
            for dir_path in sorted(staging_path.rglob('*'), reverse=True):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    logger.info(f"Rimuovo directory vuota: {dir_path}")
                    dir_path.rmdir()
        except Exception as e:
            logger.warning(f"Errore rimuovendo directory vuote: {e}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Pulisce file vecchi da una directory staging'
    )
    parser.add_argument(
        '--staging-dir',
        required=True,
        help='Directory di staging da pulire'
    )
    parser.add_argument(
        '--max-age',
        type=int,
        default=3600,
        help='Età massima dei file in secondi (default: 3600 = 1 ora)'
    )
    parser.add_argument(
        '--extensions',
        help='Estensioni da considerare (separate da virgola, es: .pdf,.docx,.jpg)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simula senza eliminare file'
    )
    
    args = parser.parse_args()
    
    # Converti estensioni
    extensions = None
    if args.extensions:
        extensions = [ext.strip() if ext.startswith('.') else f'.{ext.strip()}'
                     for ext in args.extensions.split(',')]
        logger.info(f"Filtro estensioni: {extensions}")
    
    # Esegui pulizia
    logger.info("=" * 60)
    logger.info("Avvio pulizia automatica file")
    logger.info("=" * 60)
    
    stats = cleanup_old_files(
        staging_dir=args.staging_dir,
        max_age_seconds=args.max_age,
        extensions=extensions,
        dry_run=args.dry_run
    )
    
    # Riporta statistiche
    logger.info("=" * 60)
    logger.info("Pulizia completata")
    logger.info(f"File eliminati: {stats['deleted']}")
    logger.info(f"File saltati: {stats['skipped']}")
    logger.info(f"Spazio liberato: {stats['size_freed']} bytes ({stats['size_freed']/(1024*1024):.2f} MB)")
    logger.info(f"Errori: {stats['errors']}")
    logger.info("=" * 60)
    
    # Exit code
    sys.exit(1 if stats['errors'] > 0 else 0)


if __name__ == '__main__':
    main()
