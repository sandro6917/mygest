"""Utility per l'invio programmatico di comunicazioni email (senza richiesta HTTP)."""

from __future__ import annotations

import socket
from email.utils import make_msgid
from smtplib import SMTPException, SMTPServerDisconnected

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone
from django.utils.html import strip_tags


class EmailSendError(Exception):
    """Sollevata quando l'invio dell'email fallisce definitivamente."""


def invia_comunicazione_programmatica(comunicazione) -> None:
    """Invia una Comunicazione via SMTP senza richiesta HTTP.

    Aggiorna comunicazione.stato a "inviata" o "errore" e salva.
    Solleva EmailSendError in caso di fallimento permanente.
    """
    connection_kwargs = {}
    email_timeout = getattr(settings, "EMAIL_TIMEOUT", None)
    if email_timeout:
        connection_kwargs["timeout"] = email_timeout

    connection = get_connection(**connection_kwargs)
    corpo_testo = comunicazione.corpo or strip_tags(comunicazione.corpo_html or "")
    from_email = comunicazione.mittente or settings.DEFAULT_FROM_EMAIL
    message_id = make_msgid(domain=from_email.split("@")[-1] if "@" in from_email else None)

    destinatari = comunicazione.get_destinatari_lista()
    if not destinatari:
        comunicazione.stato = "errore"
        comunicazione.log_errore = "Nessun destinatario trovato"
        comunicazione.save(update_fields=["stato", "log_errore"])
        raise EmailSendError("Nessun destinatario trovato")

    email = EmailMultiAlternatives(
        subject=comunicazione.oggetto,
        body=corpo_testo,
        from_email=from_email,
        to=destinatari,
        headers={"Message-ID": message_id},
        connection=connection,
    )
    if comunicazione.corpo_html:
        email.attach_alternative(comunicazione.corpo_html, "text/html")

    try:
        connection.open()
        connection.send_messages([email])
        email_message = email.message()
        message_id_header = email_message.get("Message-ID")
        if message_id_header:
            message_id = message_id_header
        comunicazione.stato = "inviata"
        comunicazione.data_invio = timezone.now()
        comunicazione.email_message_id = message_id
        comunicazione.save(update_fields=["stato", "data_invio", "email_message_id"])
    except (ConnectionRefusedError, SMTPServerDisconnected, socket.timeout) as exc:
        if getattr(settings, "EMAIL_FAILOVER_TO_CONSOLE", settings.DEBUG):
            try:
                fallback_conn = get_connection("django.core.mail.backends.console.EmailBackend")
                email.connection = fallback_conn
                email.send()
                comunicazione.stato = "inviata"
                comunicazione.data_invio = timezone.now()
                comunicazione.email_message_id = message_id
                comunicazione.save(update_fields=["stato", "data_invio", "email_message_id"])
                return
            except Exception:
                pass
        comunicazione.stato = "errore"
        comunicazione.log_errore = str(exc)
        comunicazione.save(update_fields=["stato", "log_errore"])
        raise EmailSendError(str(exc)) from exc
    except (SMTPException, OSError) as exc:
        comunicazione.stato = "errore"
        comunicazione.log_errore = str(exc)
        comunicazione.save(update_fields=["stato", "log_errore"])
        raise EmailSendError(str(exc)) from exc
    except Exception as exc:
        comunicazione.stato = "errore"
        comunicazione.log_errore = str(exc)
        comunicazione.save(update_fields=["stato", "log_errore"])
        raise EmailSendError(str(exc)) from exc
    finally:
        try:
            connection.close()
        except Exception:
            pass
