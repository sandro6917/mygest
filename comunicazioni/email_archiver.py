import imaplib
import logging
import time
from email.generator import BytesGenerator
from email.message import EmailMessage
from io import BytesIO
from socket import timeout as SocketTimeout
from typing import Iterable, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class EmailAppendError(Exception):
    """Raised when the IMAP append operation fails."""


def _build_raw_message(message: EmailMessage) -> bytes:
    buffer = BytesIO()
    generator = BytesGenerator(buffer, policy=message.policy)
    generator.flatten(message)
    return buffer.getvalue()


def _candidate_folders(folder: Optional[str]) -> Iterable[str]:
    seen = set()
    if folder:
        yield folder
        seen.add(folder)

    configured = getattr(settings, "EMAIL_IMAP_SENT_FOLDERS", None)
    if configured:
        for candidate in configured:
            if candidate and candidate not in seen:
                seen.add(candidate)
                yield candidate
    else:
        default_folder = getattr(settings, "EMAIL_IMAP_SENT_FOLDER", "Sent")
        if default_folder and default_folder not in seen:
            seen.add(default_folder)
            yield default_folder

    fallbacks = [
        "Sent",
        "INBOX.Sent",
        "Sent Items",
        "INBOX.Sent Items",
        "Posta inviata",
        "INBOX.Posta inviata",
    ]
    for candidate in fallbacks:
        if candidate and candidate not in seen:
            seen.add(candidate)
            yield candidate


def _format_response_data(data) -> str:
    parts = []
    if not data:
        return ""
    for item in data:
        if isinstance(item, (bytes, bytearray)):
            parts.append(item.decode("utf-8", errors="replace"))
        else:
            parts.append(str(item))
    return " ".join(parts)


def append_to_sent_folder(message: EmailMessage, *, folder: Optional[str] = None) -> None:
    """Append the given email message to the configured IMAP folder."""

    imap_host = getattr(settings, "EMAIL_IMAP_HOST", None)
    imap_port = getattr(settings, "EMAIL_IMAP_PORT", 993)
    username = getattr(settings, "EMAIL_IMAP_USER", settings.EMAIL_HOST_USER)
    password = getattr(settings, "EMAIL_IMAP_PASSWORD", settings.EMAIL_HOST_PASSWORD)

    if not imap_host:
        logger.warning("IMAP host not configured; skipping append to sent folder.")
        return

    raw_message = _build_raw_message(message)
    internal_date = imaplib.Time2Internaldate(time.localtime())

    imap_timeout = getattr(settings, "EMAIL_IMAP_TIMEOUT", getattr(settings, "EMAIL_TIMEOUT", None))

    try:
        with imaplib.IMAP4_SSL(imap_host, imap_port, timeout=imap_timeout) as imap:
            imap.login(username, password)
            last_error: Optional[EmailAppendError] = None
            for target_folder in _candidate_folders(folder):
                status, data = imap.append(target_folder, "(\\Seen)", internal_date, raw_message)
                if status == "OK":
                    logger.debug("Email appended to IMAP folder '%s'", target_folder)
                    return

                response = _format_response_data(data)
                logger.debug(
                    "IMAP append to folder '%s' failed with status %s: %s",
                    target_folder,
                    status,
                    response,
                )

                if status == "NO" and any(
                    isinstance(item, (bytes, bytearray)) and b"TRYCREATE" in item for item in (data or [])
                ):
                    create_status, create_data = imap.create(target_folder)
                    if create_status == "OK":
                        status, data = imap.append(target_folder, "(\\Seen)", internal_date, raw_message)
                        if status == "OK":
                            logger.debug(
                                "IMAP folder '%s' created and email appended successfully", target_folder
                            )
                            return
                        response = _format_response_data(data)
                        logger.debug(
                            "IMAP append to newly created folder '%s' failed with status %s: %s",
                            target_folder,
                            status,
                            response,
                        )
                    else:
                        logger.debug(
                            "Failed to create IMAP folder '%s': %s %s",
                            target_folder,
                            create_status,
                            _format_response_data(create_data),
                        )

                last_error = EmailAppendError(
                    f"IMAP append status {status} for folder '{target_folder}': {response or 'No details'}"
                )

            if last_error:
                raise last_error
            raise EmailAppendError("Nessuna cartella IMAP valida configurata per l'archiviazione della posta inviata.")
    except EmailAppendError:
        raise
    except SocketTimeout as exc:
        raise EmailAppendError(
            f"Timeout nella connessione IMAP dopo {imap_timeout or 'un tempo indefinito'} secondi"
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive logging branch
        logger.exception("Failed to append email to IMAP sent folder: %s", exc)
        raise EmailAppendError(str(exc)) from exc
