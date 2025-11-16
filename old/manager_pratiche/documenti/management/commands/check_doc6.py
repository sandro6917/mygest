from __future__ import annotations
import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.forms import ModelChoiceField, BooleanField, DateField, DateTimeField
from documenti.models import Documento, AttributoDefinizione, AttributoValore
from documenti.forms import DocumentoDinamicoForm

class Command(BaseCommand):
    help = "Verifica modifica documento #6 e la gestione delle date negli attributi dinamici."

    def handle(self, *args, **options):
        try:
            doc = Documento.objects.select_related("tipo", "cliente").get(pk=6)
        except Documento.DoesNotExist:
            self.stderr.write("Documento #6 non trovato.")
            return

        tipo = getattr(doc, "tipo", None)
        if not tipo:
            self.stderr.write("Documento #6 non ha un tipo associato.")
            return

        defs_date = list(AttributoDefinizione.objects.filter(
            tipo_documento=tipo,
            tipo_dato__in=["date", "data"]
        ).order_by("ordine", "codice"))

        if not defs_date:
            self.stderr.write("Nessuna definizione di attributo di tipo data trovata per questo tipo documento.")
            return

        # Stampa valori correnti in DB
        self.stdout.write("== Valori attuali in DB (AttributoValore) ==")
        av_map = {}
        for d in defs_date:
            av = AttributoValore.objects.filter(documento=doc, definizione=d).first()
            av_map[d.codice] = av.valore if av else None
            self.stdout.write(f"- {d.codice}: {av_map[d.codice]!r}")

        # Istanzia il form di modifica (GET) e verifica gli initial
        form_get = DocumentoDinamicoForm(instance=doc, tipo=tipo)
        self.stdout.write("\n== Initial del form (GET) ==")
        initial_map = {}
        for d in defs_date:
            key = f"attr_{d.codice}"
            initial_map[d.codice] = form_get.initial.get(key)
            self.stdout.write(f"- {d.codice}: {initial_map[d.codice]!r}")

        # Verifica coerenza: se in DB è 'YYYY-MM-DD', nel form deve essere datetime.date corrispondente
        mismatch = []
        for d in defs_date:
            raw = av_map[d.codice]
            if isinstance(raw, str):
                exp = parse_date(raw)
            elif isinstance(raw, datetime.date):
                exp = raw
            else:
                exp = None
            got = initial_map[d.codice]
            if (exp or got) and exp != got:
                mismatch.append((d.codice, raw, got))
        if mismatch:
            self.stderr.write("\nATTENZIONE: alcune date non sono state precompilate correttamente:")
            for code, raw, got in mismatch:
                self.stderr.write(f"- {code}: DB={raw!r} vs form.initial={got!r}")
        else:
            self.stdout.write("\nOK: le date dinamiche sono precompilate correttamente nel form.")

        # Costruisce una POST di modifica con valori esistenti + date incrementate di 1 giorno (se presenti)
        post_data = {}
        for name, field in form_get.fields.items():
            val = form_get.initial.get(name, None)
            # serializza per POST
            if isinstance(field, ModelChoiceField):
                post_data[name] = "" if val in (None, "") else str(val if isinstance(val, int) else getattr(val, "pk", ""))
            elif isinstance(field, BooleanField):
                if bool(val):
                    post_data[name] = "on"
            elif isinstance(field, DateField):
                if isinstance(val, datetime.date):
                    post_data[name] = val.strftime("%Y-%m-%d")
                elif isinstance(val, str):
                    post_data[name] = val
                else:
                    post_data[name] = ""
            elif isinstance(field, DateTimeField):
                if isinstance(val, datetime.datetime):
                    post_data[name] = val.strftime("%Y-%m-%dT%H:%M")
                else:
                    post_data[name] = ""
            else:
                post_data[name] = "" if val in (None, "") else str(val)

        # aggiorna le due date principali se esistono
        def bump_date_str(s: str | None) -> str:
            if not s:
                return (timezone.now().date()).strftime("%Y-%m-%d")
            d = parse_date(s) or timezone.now().date()
            return (d + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        target_codes = ["data_atto", "data_registrazione_atto"]
        for d in defs_date:
            key = f"attr_{d.codice}"
            if d.codice in target_codes:
                cur = post_data.get(key) or (av_map[d.codice] if isinstance(av_map[d.codice], str) else None)
                post_data[key] = bump_date_str(cur)

        # Esegue salvataggio
        form_post = DocumentoDinamicoForm(post_data, instance=doc, tipo=tipo)
        if not form_post.is_valid():
            self.stderr.write("\nForm non valido in POST:")
            for k, errs in form_post.errors.items():
                self.stderr.write(f"- {k}: {errs}")
            return

        form_post.save()
        self.stdout.write("\nSalvataggio eseguito.")

        # Ricontrolla i valori salvati
        self.stdout.write("\n== Valori dopo salvataggio (AttributoValore) ==")
        changed = []
        for d in defs_date:
            av = AttributoValore.objects.filter(documento=doc, definizione=d).first()
            val = av.valore if av else None
            self.stdout.write(f"- {d.codice}: {val!r}")
            if d.codice in target_codes:
                # confronta con quanto mandato in POST
                att_key = f"attr_{d.codice}"
                if val != post_data.get(att_key):
                    changed.append((d.codice, post_data.get(att_key), val))

        if changed:
            self.stderr.write("\nESITO: le seguenti date non risultano aggiornate correttamente:")
            for code, exp, got in changed:
                self.stderr.write(f"- {code}: atteso {exp!r}, ottenuto {got!r}")
        else:
            self.stdout.write("\nESITO: OK, le date degli attributi dinamici sono state aggiornate e riproposte correttamente.")