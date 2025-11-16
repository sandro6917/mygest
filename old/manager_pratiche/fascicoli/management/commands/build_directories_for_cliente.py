from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from anagrafiche.models import Anagrafica
from fascicoli.models import TitolarioVoce
from fascicoli.utils import ensure_archivio_path

class Command(BaseCommand):
    help = "Crea l'albero directory del titolario nel NAS per uno o più clienti."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--cliente-id", type=int, help="ID cliente singolo")
        group.add_argument("--all", action="store_true", help="Tutti i clienti")
        parser.add_argument("--anno", type=int, help="Se impostato, crea anche il livello 'anno' sotto ogni voce.")
        parser.add_argument("--dry-run", action="store_true", help="Mostra cosa verrebbe creato.")

    @staticmethod
    def _cliente_code(cli: Anagrafica) -> str:
        cf = (cli.codice_fiscale or "").upper()
        if cli.tipo == "PG":
            base = cf[-5:] if cf.isdigit() and len(cf) >= 5 else (cli.ragione_sociale or "CLI").split()[0][:8].upper()
        else:
            base = f"{(cli.cognome or 'CLI')[:6]}{(cli.nome or '')[:1]}".upper()
        return base.replace(" ", "")

    @staticmethod
    def _tit_parts(voce: TitolarioVoce) -> list[str]:
        parts, node = [], voce
        while node:
            # "01.03.02 - Oggetto"
            parts.insert(0, f"{node.codice_gerarchico()} - {node.titolo}")
            node = node.parent
        return parts

    def handle(self, *args, **opts):
        if not getattr(settings, "ARCHIVIO_BASE_PATH", None):
            raise CommandError("ARCHIVIO_BASE_PATH non configurato in settings.")

        # Clienti target
        if opts["all"]:
            clienti = Anagrafica.objects.all()
        else:
            clienti = Anagrafica.objects.filter(pk=opts["cliente-id"])

        if not clienti.exists():
            raise CommandError("Nessun cliente trovato per i criteri passati.")

        voci = TitolarioVoce.objects.all()
        if not voci.exists():
            raise CommandError("Nessuna voce di titolario presente.")

        dry = opts["dry_run"]
        anno = opts.get("anno")

        created = 0
        for cli in clienti:
            cli_code = self._cliente_code(cli)
            for voce in voci:
                tit_parts = self._tit_parts(voce)
                if dry:
                    self.stdout.write(f"[DRY] {cli_code} / {' / '.join(tit_parts)}{(' / '+str(anno)) if anno else ''}")
                else:
                    ensure_archivio_path(cli_code, tit_parts, anno)
                    created += 1

        if dry:
            self.stdout.write(self.style.WARNING("DRY-RUN terminato. Nessuna directory creata."))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Directory verificate/creare: {created}"))
