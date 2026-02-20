"""Utility per importare comunicazioni da caselle IMAP."""

from __future__ import annotations

import email
import imaplib
import logging
from contextlib import contextmanager
from email.header import decode_header, make_header
from email.utils import getaddresses, parsedate_to_datetime

from django.db import transaction
from django.utils import timezone

from .models import Comunicazione, Mailbox, EmailImport, EmailImportBlacklist

logger = logging.getLogger(__name__)


def _decode_header(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:  # pragma: no cover - fallback in caso di header non standard
        return value


def _clean_addresses(raw: str | None) -> list[str]:
    addresses = []
    for name, addr in getaddresses([raw or ""]):
        addr = (addr or "").strip()
        if not addr:
            continue
        if addr not in addresses:
            addresses.append(addr)
    return addresses


@contextmanager
def _imap_connection(mailbox: Mailbox):
    if mailbox.usa_ssl:
        conn = imaplib.IMAP4_SSL(mailbox.host, mailbox.porta, timeout=mailbox.timeout)
    else:
        conn = imaplib.IMAP4(mailbox.host, mailbox.porta, timeout=mailbox.timeout)
    try:
        if mailbox.usa_starttls and not mailbox.usa_ssl:
            conn.starttls()
        conn.login(mailbox.username, mailbox.password)
        conn.select(mailbox.cartella)
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass
        try:
            conn.logout()
        except Exception:
            pass


def _should_import(
    mailbox: Mailbox,
    mittente: str,
    soggetto: str,
    blacklist: set[str] | None = None,
    reason_holder: dict[str, str | None] | None = None,
) -> bool:
    mittente_lower = (mittente or "").lower()
    if blacklist and mittente_lower in blacklist:
        if reason_holder is not None:
            reason_holder["reason"] = "mittente nella blacklist globale"
        return False
    allowed = mailbox.allowed_from()
    blocked = mailbox.blocked_from()
    if allowed and mittente_lower not in allowed:
        if reason_holder is not None:
            reason_holder["reason"] = "mittente non presente tra gli indirizzi consentiti"
        return False
    if mittente_lower in blocked:
        if reason_holder is not None:
            reason_holder["reason"] = "mittente presente tra quelli esclusi nella casella"
        return False
    tokens = mailbox.subject_tokens()
    if tokens:
        soggetto_low = (soggetto or "").lower()
        matches = any(token in soggetto_low for token in tokens)
        if not matches and reason_holder is not None:
            reason_holder["reason"] = "soggetto non contiene le parole chiave richieste"
        if reason_holder is not None and matches:
            reason_holder["reason"] = None
        return matches
    if reason_holder is not None:
        reason_holder["reason"] = None
    return True


def _extract_bodies(msg: email.message.Message) -> tuple[str, str]:
    text_body = ""
    html_body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            try:
                decoded = payload.decode(charset, errors="replace")
            except LookupError:
                decoded = payload.decode("utf-8", errors="replace")
            content_type = (part.get_content_type() or "").lower()
            if content_type == "text/plain" and not text_body:
                text_body = decoded
            elif content_type == "text/html" and not html_body:
                html_body = decoded
    else:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        try:
            text_body = payload.decode(charset, errors="replace")
        except LookupError:
            text_body = payload.decode("utf-8", errors="replace")
    return text_body, html_body


@transaction.atomic
def _crea_comunicazione_da_email(mailbox: Mailbox, mail: EmailImport) -> Comunicazione:
    if mail.comunicazione_id:
        return mail.comunicazione

    subject = mail.oggetto or "(senza oggetto)"
    destinatari = mail.destinatari.split(",") if mail.destinatari else []

    comunicazione = Comunicazione.objects.create(
        tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
        direzione=Comunicazione.Direzione.IN,
        oggetto=subject,
        corpo=mail.corpo_testo or mail.corpo_html,
        mittente=mail.mittente,
        destinatari=", ".join(addr.strip() for addr in destinatari if addr.strip()),
        stato="bozza",
        email_message_id=mail.message_id,
        importato_il=timezone.now(),
        import_source=mailbox.nome,
    )

    mail.comunicazione = comunicazione
    mail.save(update_fields=["comunicazione"])
    return comunicazione


def sincronizza_mailbox(mailbox: Mailbox, limite: int | None = None) -> int:
    """Scarica nuove email da una casella."""
    processed = 0
    blacklist = {
        (email or "").strip().lower()
        for email in EmailImportBlacklist.objects.values_list("email", flat=True)
    }
    with _imap_connection(mailbox) as conn:
        result, data = conn.uid("search", None, "UNSEEN")
        if result != "OK":
            logger.warning("Mailbox %s, risposta search non OK: %s", mailbox.nome, result)
            return processed
        uids = data[0].split() if data and data[0] else []
        ultimi_uid = mailbox.ultimi_uid.strip()
        if ultimi_uid:
            try:
                last_uid_int = int(ultimi_uid)
                uids = [uid for uid in uids if int(uid) > last_uid_int]
            except ValueError:
                pass
        if limite:
            uids = uids[:limite]
        logger.info("Mailbox %s: trovati %s UID da processare", mailbox.nome, len(uids))
        for uid in uids:
            try:
                result, fetch_data = conn.uid("fetch", uid, "(RFC822)")
                if result != "OK" or not fetch_data or fetch_data[0] is None:
                    logger.warning("Mailbox %s: fetch fallito per UID %s", mailbox.nome, uid)
                    continue
                raw_email = fetch_data[0][1]
                message = email.message_from_bytes(raw_email)
                message_id = (message.get("Message-ID") or "").strip() or f"uid:{uid.decode()}"
                subject = _decode_header(message.get("Subject"))
                sender = _decode_header(message.get("From"))
                sender_addresses = _clean_addresses(message.get("From"))
                sender_email = sender_addresses[0] if sender_addresses else sender
                reason_holder: dict[str, str | None] = {}
                if not _should_import(
                    mailbox,
                    sender_email,
                    subject,
                    blacklist=blacklist,
                    reason_holder=reason_holder,
                ):
                    logger.info(
                        "Mailbox %s: skip Message-ID %s da %s (%s)",
                        mailbox.nome,
                        message_id,
                        sender_email or "sconosciuto",
                        reason_holder.get("reason") or "filtri casella",
                    )
                    continue
                to_header = ", ".join(_clean_addresses(message.get("To")))
                cc_header = ", ".join(_clean_addresses(message.get("Cc")))
                bodies = _extract_bodies(message)
                try:
                    data_msg = parsedate_to_datetime(message.get("Date"))
                    if data_msg.tzinfo is None:
                        data_msg = timezone.make_aware(data_msg, timezone=timezone.utc)
                except Exception:
                    data_msg = None

                headers_dump = "\n".join(f"{k}: {v}" for k, v in message.items()) if mailbox.salva_headers else ""

                email_import, created = EmailImport.objects.get_or_create(
                    mailbox=mailbox,
                    message_id=message_id,
                    defaults={
                        "uid": uid.decode(),
                        "mittente": sender_email,
                        "destinatari": ", ".join(filter(None, [to_header, cc_header])),
                        "oggetto": subject,
                        "data_messaggio": data_msg,
                        "raw_headers": headers_dump,
                        "corpo_testo": bodies[0],
                        "corpo_html": bodies[1],
                        "raw_message": raw_email,
                    },
                )
                if created:
                    processed += 1
                    logger.info(
                        "Mailbox %s: importata nuova email %s (uid=%s)",
                        mailbox.nome,
                        message_id,
                        uid.decode(),
                    )
                else:
                    updates = []
                    if not email_import.raw_message:
                        email_import.raw_message = raw_email
                        updates.append("raw_message")
                    if not email_import.uid:
                        email_import.uid = uid.decode()
                        updates.append("uid")
                    if updates:
                        email_import.save(update_fields=updates)
                        logger.debug(
                            "Mailbox %s: aggiornati campi %s per email %s",
                            mailbox.nome,
                            ", ".join(updates),
                            message_id,
                        )
                mailbox.ultimi_uid = uid.decode()
            except Exception as exc:  # pragma: no cover - logging errori runtime
                logger.exception("Errore durante l'import da %s: %s", mailbox.nome, exc)
        mailbox.ultima_lettura = timezone.now()
        mailbox.save(update_fields=["ultima_lettura", "ultimi_uid", "updated_at"])
        logger.info("Mailbox %s: import concluse, %s nuove email", mailbox.nome, processed)
    return processed


def sincronizza_tutte_mailbox(limite: int | None = None) -> int:
    count = 0
    for mailbox in Mailbox.objects.filter(attiva=True):
        count += sincronizza_mailbox(mailbox, limite=limite)
    return count