"""
Comando Django management per pulizia file temporanei upload

Uso:
    python manage.py cleanup_tmp
    python manage.py cleanup_tmp --days=7
    python manage.py cleanup_tmp --days=3 --dry-run
    
Schedulazione cron consigliata:
    0 2 * * * cd /path/to/mygest && /path/to/venv/bin/python manage.py cleanup_tmp --days=7
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Pulisce i file temporanei di upload più vecchi di N giorni"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Giorni di retention per file temporanei (default: 7)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra cosa verrebbe eliminato senza eliminare realmente',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Output verboso con lista file eliminati',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        # Determina la directory tmp
        temp_dir = getattr(settings, 'UPLOAD_TEMP_DIR', 'tmp')
        media_root = getattr(settings, 'MEDIA_ROOT', settings.BASE_DIR / 'media')
        tmp_base = Path(media_root) / temp_dir
        
        if not tmp_base.exists():
            self.stdout.write(
                self.style.WARNING(f"Directory temporanea non esiste: {tmp_base}")
            )
            return

        threshold = datetime.now() - timedelta(days=days)
        deleted_count = 0
        deleted_size = 0
        errors = 0

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\n{'[DRY-RUN] ' if dry_run else ''}Pulizia file temporanei"
            )
        )
        self.stdout.write(f"Directory: {tmp_base}")
        self.stdout.write(f"Retention: {days} giorni")
        self.stdout.write(f"Soglia data: {threshold.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Scansione file
        for filepath in tmp_base.rglob("*"):
            if not filepath.is_file():
                continue
            
            try:
                stat = filepath.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                
                if mtime < threshold:
                    size = stat.st_size
                    age_days = (datetime.now() - mtime).days
                    
                    if verbose or dry_run:
                        self.stdout.write(
                            f"  {'[DRY-RUN] ' if dry_run else ''}✓ {filepath.relative_to(tmp_base)}"
                            f" ({size:,} bytes, {age_days} giorni)"
                        )
                    
                    if not dry_run:
                        try:
                            filepath.unlink()
                            logger.info(f"Eliminato file temporaneo: {filepath}")
                        except Exception as e:
                            self.stderr.write(
                                self.style.ERROR(f"  ✗ Errore eliminazione {filepath}: {e}")
                            )
                            errors += 1
                            continue
                    
                    deleted_count += 1
                    deleted_size += size
                    
            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"  ✗ Errore accesso {filepath}: {e}")
                )
                errors += 1

        # Rimuovi directory vuote
        if not dry_run:
            self.stdout.write("\nRimozione directory vuote...")
            removed_dirs = 0
            for dirpath in sorted(tmp_base.rglob("*"), reverse=True):
                if dirpath.is_dir() and not any(dirpath.iterdir()):
                    try:
                        dirpath.rmdir()
                        removed_dirs += 1
                        if verbose:
                            self.stdout.write(f"  ✓ Rimossa directory: {dirpath.relative_to(tmp_base)}")
                    except Exception as e:
                        if verbose:
                            self.stderr.write(f"  ✗ Errore rimozione dir {dirpath}: {e}")
            
            if removed_dirs > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"  Rimosse {removed_dirs} directory vuote")
                )

        # Summary
        size_mb = deleted_size / (1024 * 1024)
        self.stdout.write("\n" + "=" * 60)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY-RUN] Verrebbero eliminati {deleted_count} file ({size_mb:.2f} MB)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Eliminati {deleted_count} file ({size_mb:.2f} MB)"
                )
            )
            if errors > 0:
                self.stdout.write(
                    self.style.ERROR(f"✗ Errori: {errors}")
                )
        
        self.stdout.write("=" * 60 + "\n")
        
        # Log summary
        logger.info(
            f"cleanup_tmp completato: {deleted_count} file eliminati "
            f"({size_mb:.2f} MB), {errors} errori"
        )
