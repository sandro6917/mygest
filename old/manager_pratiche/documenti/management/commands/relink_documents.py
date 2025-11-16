from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import os
import shutil

from documenti.models import Documento

class Command(BaseCommand):
    help = "Rilinka i documenti ricalcolando percorso_archivio; opzionalmente sposta i file."

    def add_arguments(self, parser):
        parser.add_argument("--cliente-id", type=int, help="Filtra per ID cliente")
        parser.add_argument("--doc-id", type=int, help="Singolo documento per ID")
        parser.add_argument("--move", action="store_true", help="Sposta fisicamente il file nel nuovo percorso")
        parser.add_argument("--dry-run", action="store_true", help="Mostra cosa verrà fatto, senza modificare")
        parser.add_argument("--limit", type=int, help="Limite massimo documenti")

    def handle(self, *args, **opts):
        qs = Documento.objects.select_related("cliente", "titolario_voce")
        if opts.get("cliente_id"):
            qs = qs.filter(cliente_id=opts["cliente_id"])
        if opts.get("doc_id"):
            qs = qs.filter(pk=opts["doc_id"])
        if opts.get("limit"):
            qs = qs.order_by("pk")[: opts["limit"]]

        if not qs.exists():
            raise CommandError("Nessun documento corrispondente ai filtri.")

        dry = opts["dry_run"]
        move = opts["move"]

        moved = 0
        updated = 0
        errors = 0

        for doc in qs:
            try:
                new_path = doc._build_path()
                old_path = doc.percorso_archivio or ""
                if new_path != old_path:
                    if dry:
                        self.stdout.write(f"[DRY] {doc.codice}: {old_path} -> {new_path}")
                    else:
                        os.makedirs(new_path, exist_ok=True)
                        doc.percorso_archivio = new_path
                        doc.save(update_fields=["percorso_archivio", "aggiornato_il"])
                        updated += 1

                # Sposta il file fisico se richiesto e se presente
                if move and doc.file and hasattr(doc.file, "path") and os.path.isfile(doc.file.path):
                    filename = os.path.basename(doc.file.name)
                    desired = os.path.join(new_path, filename)
                    if os.path.abspath(doc.file.path) != os.path.abspath(desired):
                        if dry:
                            self.stdout.write(f"[DRY] MOVE {doc.file.path} -> {desired}")
                        else:
                            os.makedirs(os.path.dirname(desired), exist_ok=True)
                            shutil.move(doc.file.path, desired)
                            # aggiorna FileField
                            doc.file.name = desired
                            doc.save(update_fields=["file", "aggiornato_il"])
                            moved += 1

            except Exception as exc:
                errors += 1
                self.stderr.write(f"❌ {doc.codice}: {exc}")

        if dry:
            self.stdout.write(self.style.WARNING("DRY-RUN terminato. Nessuna modifica eseguita."))
        self.stdout.write(self.style.SUCCESS(f"✅ Aggiornati: {updated}  📦 Spostati: {moved}  ⚠️ Errori: {errors}"))
