from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone
from django.utils.html import strip_tags

from .models import AllegatoComunicazione, Comunicazione
from .models_template import TemplateComunicazione
from .utils_template import RenderedComunicazione, merge_contenuti, render_template_comunicazione

def invio_massivo(comunicazioni, context_list, template_id=None, use_gmail=False, use_outlook=False):
    """
    Invio massivo di comunicazioni.
    - comunicazioni: queryset/lista di Comunicazione (o destinatari)
    - context_list: lista di dict con variabili per template (uno per destinatario)
    - template_id: se fornito, usa il template indicato
    - use_gmail/use_outlook: se True, usa backend/email API specifico
    """
    results = []
    if template_id:
        template = TemplateComunicazione.objects.get(pk=template_id)
    else:
        template = None

    # Scegli backend
    if use_gmail:
        backend = 'django.core.mail.backends.smtp.EmailBackend'  # Da sostituire con backend custom Gmail
    elif use_outlook:
        backend = 'django.core.mail.backends.smtp.EmailBackend'  # Da sostituire con backend custom Outlook
    else:
        backend = None

    connection = get_connection(backend=backend) if backend else get_connection()

    for comunicazione, ctx in zip(comunicazioni, context_list):
        try:
            if template:
                contenuto_renderizzato = merge_contenuti(
                    render_template_comunicazione(template, ctx, comunicazione=comunicazione)
                )
            else:
                contenuto_renderizzato = merge_contenuti(
                    RenderedComunicazione(
                        oggetto=comunicazione.oggetto,
                        corpo_testo=comunicazione.corpo or "",
                        corpo_html=comunicazione.corpo_html or None,
                    )
                )

            oggetto = contenuto_renderizzato.oggetto or comunicazione.oggetto
            corpo_html = contenuto_renderizzato.corpo_html
            corpo_testo = contenuto_renderizzato.corpo_testo or strip_tags(corpo_html or "")

            email = EmailMultiAlternatives(
                subject=oggetto,
                body=corpo_testo,
                from_email=comunicazione.mittente or settings.DEFAULT_FROM_EMAIL,
                to=[x.strip() for x in comunicazione.destinatari.split(",") if x.strip()],
                connection=connection,
            )
            if corpo_html:
                email.attach_alternative(corpo_html, "text/html")
            for allegato in comunicazione.allegati.select_related("documento"):
                doc = allegato.documento
                if doc.file:
                    email.attach(doc.file.name.split("/")[-1], doc.file.read())
            email.send()
            comunicazione.stato = "inviata"
            comunicazione.data_invio = timezone.now()
            comunicazione.log_errore = ""
            comunicazione.save(update_fields=["stato", "data_invio", "log_errore"])
            results.append((comunicazione.pk, True, None))
        except ConnectionRefusedError as exc:
            fallback_error = exc
            if settings.DEBUG:
                try:
                    email.connection = get_connection("django.core.mail.backends.console.EmailBackend")
                    email.send()
                    comunicazione.stato = "inviata"
                    comunicazione.data_invio = timezone.now()
                    comunicazione.log_errore = "Inviata via backend console: server SMTP non raggiungibile"
                    comunicazione.save(update_fields=["stato", "data_invio", "log_errore"])
                    results.append((comunicazione.pk, True, str(exc)))
                    continue
                except Exception as console_exc:
                    fallback_error = console_exc
            comunicazione.stato = "errore"
            comunicazione.log_errore = str(fallback_error)
            comunicazione.save(update_fields=["stato", "log_errore"])
            results.append((comunicazione.pk, False, str(fallback_error)))
        except Exception as e:
            comunicazione.stato = "errore"
            comunicazione.log_errore = str(e)
            comunicazione.save(update_fields=["stato", "log_errore"])
            results.append((comunicazione.pk, False, str(e)))
    return results
