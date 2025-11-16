from django.core.management.base import BaseCommand
from django.conf import settings
import os
import tempfile
import shutil
import time

class Command(BaseCommand):
    help = "Verifica connessione NAS: esistenza, permessi scrittura, spazio libero."

    def add_arguments(self, parser):
        parser.add_argument("--warn-percent", type=int, default=10,
                            help="Soglia di warning per spazio libero in percentuale (default: 10).")
        parser.add_argument("--verbose", action="store_true", help="Stampa dettagli addizionali.")

    def handle(self, *args, **opts):
        base = getattr(settings, "ARCHIVIO_BASE_PATH", None)
        if not base:
            self.stderr.write(self.style.ERROR("ARCHIVIO_BASE_PATH non configurato in settings.py"))
            self.exitcode = 1
            return

        self.stdout.write(f"🔎 Controllo NAS su: {base}")

        # 1) Esistenza path
        if not os.path.isdir(base):
            self.stderr.write(self.style.ERROR("Percorso NAS inesistente o non montato."))
            self.exitcode = 2
            return

        # 2) Spazio libero
        total, used, free = shutil.disk_usage(base)
        free_pct = (free / total) * 100 if total else 0
        self.stdout.write(f"📦 Spazio: total={total//(1024**3)}GB free={free//(1024**3)}GB ({free_pct:.1f}%)")
        if free_pct < opts["warn_percent"]:
            self.stderr.write(self.style.WARNING(f"Spazio libero sotto soglia {opts['warn_percent']}%"))

        # 3) Scrivibilità + roundtrip file
        try:
            with tempfile.NamedTemporaryFile(prefix="nas_check_", dir=base, delete=False) as tmp:
                tmp.write(b"check")
                tmp_path = tmp.name
            if opts["verbose"]:
                self.stdout.write(f"Creato file test: {tmp_path}")
            os.remove(tmp_path)
            self.stdout.write(self.style.SUCCESS("✅ NAS raggiungibile e scrivibile."))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Errore scrittura su NAS: {exc}"))
            self.exitcode = 3
            return
