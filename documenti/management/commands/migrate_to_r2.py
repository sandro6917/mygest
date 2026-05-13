"""
Management command: migrate_to_r2

Migra i file esistenti dal filesystem locale a Cloudflare R2.
Mantiene la stessa struttura di path (cliente/titolario/anno/file).

Utilizzo:
    # Dry run (nessuna modifica, solo report)
    python manage.py migrate_to_r2 --dry-run

    # Migrazione reale
    python manage.py migrate_to_r2

    # Solo una sottodirectory
    python manage.py migrate_to_r2 --subdir SALREM01

    # Verifica che tutti i file DB siano su R2
    python manage.py migrate_to_r2 --verify-only
"""

import os
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Migra i file dell'archivio dal filesystem locale a Cloudflare R2"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Simula la migrazione senza caricare nulla",
        )
        parser.add_argument(
            '--subdir',
            type=str,
            default='',
            help="Migra solo questa sottodirectory (es. SALREM01)",
        )
        parser.add_argument(
            '--verify-only',
            action='store_true',
            help="Verifica che i file nel DB esistano su R2 (non carica)",
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help="Salta i file già presenti su R2 (default: True)",
        )

    def handle(self, *args, **options):
        r2_config = getattr(settings, 'CLOUDFLARE_R2', {})
        if not r2_config.get('BUCKET_NAME') or not r2_config.get('ACCOUNT_ID'):
            raise CommandError(
                "Cloudflare R2 non configurato.\n"
                "Imposta R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, "
                "R2_BUCKET_NAME nel file .env"
            )

        archivio_base = getattr(settings, 'ARCHIVIO_BASE_PATH', '')
        if not archivio_base or not Path(archivio_base).exists():
            raise CommandError(
                f"ARCHIVIO_BASE_PATH non trovato: {archivio_base}\n"
                "Il filesystem locale deve essere accessibile per la migrazione."
            )

        dry_run = options['dry_run']
        verify_only = options['verify_only']
        subdir = options['subdir']
        skip_existing = options['skip_existing']

        s3 = boto3.client(
            's3',
            endpoint_url=f"https://{r2_config['ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=r2_config['ACCESS_KEY_ID'],
            aws_secret_access_key=r2_config['SECRET_ACCESS_KEY'],
            region_name='auto',
        )
        bucket = r2_config['BUCKET_NAME']

        if verify_only:
            self._verify_db_files(s3, bucket)
            return

        source_root = Path(archivio_base)
        if subdir:
            source_root = source_root / subdir
            if not source_root.exists():
                raise CommandError(f"Sottodirectory non trovata: {source_root}")

        self.stdout.write(f"\nSorgente: {source_root}")
        self.stdout.write(f"Destinazione: R2 bucket '{bucket}'")
        if dry_run:
            self.stdout.write(self.style.WARNING("MODALITÀ DRY-RUN: nessun file verrà caricato\n"))

        stats = {'uploaded': 0, 'skipped': 0, 'errors': 0, 'total': 0}
        start_time = time.time()

        for local_path in sorted(source_root.rglob('*')):
            if not local_path.is_file():
                continue

            stats['total'] += 1
            rel_key = local_path.relative_to(Path(settings.ARCHIVIO_BASE_PATH)).as_posix()

            if skip_existing and not dry_run:
                try:
                    s3.head_object(Bucket=bucket, Key=rel_key)
                    stats['skipped'] += 1
                    self.stdout.write(f"  SKIP  {rel_key}")
                    continue
                except ClientError as e:
                    if e.response['Error']['Code'] != '404':
                        self.stderr.write(self.style.ERROR(f"  ERR   {rel_key}: {e}"))
                        stats['errors'] += 1
                        continue

            if dry_run:
                self.stdout.write(f"  DRY   {rel_key} ({self._fmt_size(local_path.stat().st_size)})")
                stats['uploaded'] += 1
                continue

            try:
                s3.upload_file(
                    str(local_path),
                    bucket,
                    rel_key,
                    ExtraArgs={'ContentType': self._guess_content_type(local_path.name)},
                )
                stats['uploaded'] += 1
                self.stdout.write(self.style.SUCCESS(f"  OK    {rel_key}"))
            except (ClientError, BotoCoreError, OSError) as e:
                stats['errors'] += 1
                self.stderr.write(self.style.ERROR(f"  ERR   {rel_key}: {e}"))

        elapsed = time.time() - start_time
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(f"Completato in {elapsed:.1f}s")
        self.stdout.write(f"  Totale file: {stats['total']}")
        self.stdout.write(self.style.SUCCESS(f"  Caricati:    {stats['uploaded']}"))
        self.stdout.write(f"  Saltati:     {stats['skipped']}")
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f"  Errori:      {stats['errors']}"))
        else:
            self.stdout.write(f"  Errori:      0")

        if stats['errors'] == 0 and not dry_run:
            self.stdout.write(self.style.SUCCESS(
                "\nMigrazione completata. Ora aggiorna il .env con le variabili R2_* "
                "e riavvia gunicorn."
            ))

    def _verify_db_files(self, s3, bucket):
        from documenti.models import Documento
        self.stdout.write("Verifica file documenti DB su R2...\n")
        qs = Documento.objects.exclude(file='').only('id', 'file')
        ok = missing = 0
        for doc in qs.iterator(chunk_size=200):
            key = doc.file.name
            try:
                s3.head_object(Bucket=bucket, Key=key)
                ok += 1
            except ClientError:
                missing += 1
                self.stderr.write(self.style.ERROR(f"  MANCANTE  doc.id={doc.id}  {key}"))
        self.stdout.write(f"\nPresenti: {ok}  Mancanti: {missing}")

    def _fmt_size(self, size_bytes):
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def _guess_content_type(self, filename):
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        return {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
            'png': 'image/png',
            'tif': 'image/tiff', 'tiff': 'image/tiff',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'p7m': 'application/pkcs7-mime',
            'xml': 'application/xml',
            'zip': 'application/zip',
        }.get(ext, 'application/octet-stream')
