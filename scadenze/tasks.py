"""
Task Celery per scadenze: alert periodici e aggiornamento codici tributo F24.

Configurazione in settings.py:

CELERY_BEAT_SCHEDULE = {
    'invia-alert-scadenze': {
        'task': 'scadenze.tasks.invia_alert_scadenze_task',
        'schedule': crontab(minute='*/5'),  # Ogni 5 minuti
    },
    'aggiorna-codici-tributo': {
        'task': 'scadenze.tasks.aggiorna_codici_tributo_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Ogni lunedì alle 3:00
    },
}
"""

from celery import shared_task
from django.core.management import call_command
from django.core.mail import mail_admins
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def invia_alert_scadenze_task(self):
    """Controlla e invia tutti gli ScadenzaAlert con alert_programmata_il <= adesso."""
    from django.utils import timezone
    from .models import ScadenzaAlert
    from .services import AlertDispatcher

    from django.conf import settings as django_settings
    now = timezone.now()
    qs = ScadenzaAlert.objects.filter(
        stato=ScadenzaAlert.Stato.PENDENTE,
        alert_programmata_il__lte=now,
    ).select_related("occorrenza__scadenza")

    if not getattr(django_settings, "WHATSAPP_ALERTS_ENABLED", False):
        qs = qs.exclude(metodo_alert=ScadenzaAlert.MetodoAlert.WHATSAPP)
    if not getattr(django_settings, "TELEGRAM_ALERTS_ENABLED", False):
        qs = qs.exclude(metodo_alert=ScadenzaAlert.MetodoAlert.TELEGRAM)

    alerts = qs

    dispatcher = AlertDispatcher()
    inviati = 0
    falliti = 0

    for alert in alerts:
        try:
            dispatcher.dispatch_alert(alert)
            inviati += 1
        except Exception as exc:
            logger.error(
                "Errore invio alert %s (metodo=%s, occorrenza=%s): %s",
                alert.pk, alert.metodo_alert,
                getattr(alert, 'occorrenza_id', '?'), exc,
            )
            falliti += 1

    if falliti:
        logger.warning("Alert scadenze: %d inviati, %d FALLITI", inviati, falliti)
        try:
            mail_admins(
                subject=f"[MyGest] {falliti} alert scadenze falliti",
                message=(
                    f"Il task Celery 'invia_alert_scadenze_task' ha riportato {falliti} "
                    f"alert falliti su {inviati + falliti} totali.\n\n"
                    "Controllare ScadenzaNotificaLog nel pannello admin per i dettagli."
                ),
                fail_silently=True,
            )
        except Exception:
            pass
    else:
        logger.info("Alert scadenze: %d inviati, %d falliti", inviati, falliti)

    return {"inviati": inviati, "falliti": falliti}


@shared_task(bind=True, max_retries=3)
def aggiorna_codici_tributo_task(self, force=False, export=False):
    """
    Task Celery per aggiornare i codici tributo F24 dall'Agenzia delle Entrate.
    
    Args:
        force (bool): Forza l'aggiornamento anche se recente
        export (bool): Esporta anche CSV/JSON
    
    Returns:
        dict: Risultato dell'operazione
    """
    try:
        logger.info("🔄 Inizio aggiornamento codici tributo F24")
        
        # Esegui il command Django
        options = {
            'force': force,
            'export': export,
            'verbose': False,
        }
        
        call_command('aggiorna_codici_tributo', **options)
        
        logger.info("✅ Aggiornamento codici tributo completato")
        
        return {
            'status': 'success',
            'message': 'Codici tributo aggiornati con successo',
        }
    
    except Exception as e:
        logger.error(f"❌ Errore aggiornamento codici tributo: {e}")
        
        # Notifica gli admin
        try:
            mail_admins(
                subject='Errore aggiornamento codici tributo F24',
                message=f'Si è verificato un errore durante l\'aggiornamento automatico:\n\n{str(e)}',
                fail_silently=True,
            )
        except:
            pass
        
        # Retry con backoff esponenziale
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def verifica_codici_obsoleti_task():
    """
    Verifica codici tributo obsoleti e invia notifica.
    
    Returns:
        dict: Risultato della verifica
    """
    from scadenze.models import CodiceTributoF24
    
    obsoleti = CodiceTributoF24.objects.filter(attivo=False)
    count = obsoleti.count()
    
    if count > 0:
        logger.warning(f"⚠️  Trovati {count} codici tributo obsoleti")
        
        # Invia notifica agli admin
        codici_list = '\n'.join([
            f"- {c.codice} ({c.sezione}): {c.descrizione[:50]}..."
            for c in obsoleti[:20]  # Max 20
        ])
        
        try:
            mail_admins(
                subject=f'Codici tributo obsoleti: {count}',
                message=f'Sono presenti {count} codici tributo marcati come obsoleti:\n\n{codici_list}',
                fail_silently=True,
            )
        except:
            pass
    
    return {
        'status': 'success',
        'codici_obsoleti': count,
    }
