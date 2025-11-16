from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from pratiche.models import Scadenza
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

class Command(BaseCommand):
    help = "Invia gli alert di scadenza programmati (email/webhook)."

    def handle(self, *args, **options):
        now = timezone.now()
        qs = (
            Scadenza.objects
            .select_related("pratica", "pratica__cliente", "pratica__tipo")
            .filter(completata=False, alert_inviato_il__isnull=True, alert_at__lte=now)
            .order_by("alert_at")
        )
        count = 0
        for s in qs:
            try:
                with transaction.atomic():
                    ok = self._notify(s)
                    if ok:
                        s.alert_inviato_il = timezone.now()
                        s.save(update_fields=["alert_inviato_il", "aggiornato_il"])
                        count += 1
            except Exception as ex:
                self.stderr.write(self.style.ERROR(f"Errore alert scadenza {s.id}: {ex}"))
        self.stdout.write(self.style.SUCCESS(f"Alert inviati: {count}"))

    def _notify(self, s: Scadenza) -> bool:
        subject = f"Scadenza pratica {s.pratica.codice}: {s.titolo}"
        when_local = timezone.localtime(s.scadenza_at)
        body = (
            f"Pratica: {s.pratica.codice} — {s.pratica.oggetto}\n"
            f"Cliente: {s.pratica.cliente}\n"
            f"Scadenza: {when_local.strftime('%d/%m/%Y %H:%M')}\n"
            f"\n{(s.descrizione or '').strip()}\n"
        )

        if s.alert_method == s.MetodoAlert.EMAIL:
            to_list = []
            if s.alert_email_to:
                to_list = [e.strip() for e in s.alert_email_to.split(",") if e.strip()]
            elif hasattr(settings, "NOTIFICATION_EMAILS"):
                to_list = list(settings.NOTIFICATION_EMAILS)
            elif hasattr(settings, "DEFAULT_FROM_EMAIL"):
                to_list = [settings.DEFAULT_FROM_EMAIL]
            if not to_list:
                return False
            send_mail(subject, body, getattr(settings, "DEFAULT_FROM_EMAIL", None), to_list, fail_silently=False)
            return True

        if s.alert_method == s.MetodoAlert.WEBHOOK and s.alert_webhook_url:
            payload = {
                "pratica": s.pratica.codice,
                "titolo": s.titolo,
                "scadenza_at": s.scadenza_at.isoformat(),
                "descrizione": s.descrizione,
                "cliente": str(s.pratica.cliente),
            }
            data = json.dumps(payload).encode("utf-8")
            req = Request(s.alert_webhook_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urlopen(req, timeout=5) as resp:
                    return 200 <= resp.getcode() < 300
            except (URLError, HTTPError):
                return False

        return False