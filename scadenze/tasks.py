"""
Task Celery per aggiornamento automatico codici tributo F24.

Configurazione in settings.py:

CELERY_BEAT_SCHEDULE = {
    'aggiorna-codici-tributo': {
        'task': 'scadenze.tasks.aggiorna_codici_tributo_task',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Ogni lunedì alle 3:00
    },
}

Uso manuale:
    from scadenze.tasks import aggiorna_codici_tributo_task
    aggiorna_codici_tributo_task.delay()
"""

from celery import shared_task
from django.core.management import call_command
from django.core.mail import mail_admins
import logging

logger = logging.getLogger(__name__)


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
