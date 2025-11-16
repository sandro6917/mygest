from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

class GmailAPIBackend(BaseEmailBackend):
    """
    Esempio di backend custom per invio tramite Gmail API (OAuth2 richiesto).
    Da completare con gestione token e chiamate API reali.
    """
    def send_messages(self, email_messages):
        # TODO: implementa invio tramite Gmail API
        raise NotImplementedError("Invio tramite Gmail API non ancora implementato.")

class OutlookAPIBackend(BaseEmailBackend):
    """
    Esempio di backend custom per invio tramite Outlook API (OAuth2 richiesto).
    Da completare con gestione token e chiamate API reali.
    """
    def send_messages(self, email_messages):
        # TODO: implementa invio tramite Outlook API
        raise NotImplementedError("Invio tramite Outlook API non ancora implementato.")
