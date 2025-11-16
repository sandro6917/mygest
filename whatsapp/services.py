from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import (
    WhatsAppBusinessAccount,
    WhatsAppContact,
    WhatsAppConversation,
    WhatsAppMessage,
)

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = int(getattr(settings, "WHATSAPP_CLOUD_TIMEOUT", 10))


class WhatsAppAPIError(Exception):
    """Raised when the WhatsApp Cloud API returns an error response."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def get_default_account() -> WhatsAppBusinessAccount:
    account = WhatsAppBusinessAccount.objects.filter(active=True).order_by("-is_default", "name").first()
    if account:
        return account
    # Fallback to settings-defined configuration if DB empty
    token = getattr(settings, "WHATSAPP_CLOUD_ACCESS_TOKEN", "")
    phone_id = getattr(settings, "WHATSAPP_CLOUD_PHONE_NUMBER_ID", "")
    if token and phone_id:
        logger.debug("Using fallback settings-defined WhatsApp account")
        existing = WhatsAppBusinessAccount.objects.filter(phone_number_id=phone_id).first()
        if existing:
            return existing
        return WhatsAppBusinessAccount.objects.create(
            name="Default",
            phone_number_id=phone_id,
            business_account_id=getattr(settings, "WHATSAPP_CLOUD_BUSINESS_ACCOUNT_ID", ""),
            access_token=token,
            verify_token=getattr(settings, "WHATSAPP_CLOUD_VERIFY_TOKEN", ""),
            app_secret=getattr(settings, "WHATSAPP_CLOUD_APP_SECRET", ""),
            api_version=getattr(settings, "WHATSAPP_CLOUD_API_VERSION", "v20.0"),
            is_default=True,
            active=True,
        )
    raise WhatsAppAPIError("Nessun account WhatsApp configurato")


def _normalize_phone(number: str) -> str:
    number = number.strip()
    if number.startswith("+"):
        return number[1:]
    return number


@dataclass
class SendResult:
    messages: list[dict[str, Any]]
    raw_response: dict[str, Any]


class WhatsAppCloudClient:
    def __init__(self, account: WhatsAppBusinessAccount | None = None) -> None:
        self.account = account or get_default_account()
        self.base_url = self.account.graph_endpoint
        self.phone_number_id = self.account.phone_number_id
        self.access_token = self.account.access_token or getattr(settings, "WHATSAPP_CLOUD_ACCESS_TOKEN", "")
        if not self.access_token:
            raise WhatsAppAPIError("Token di accesso WhatsApp non impostato")

    # ---------------------------------------------------------------------
    # HTTP helpers
    # ---------------------------------------------------------------------
    def _request(self, method: str, path: str, *, json_payload: Mapping[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                json=json_payload,
                timeout=DEFAULT_TIMEOUT,
            )
        except requests.RequestException as exc:  # pragma: no cover - network failure
            logger.exception("Errore di rete verso WhatsApp Cloud API")
            raise WhatsAppAPIError(str(exc)) from exc
        if response.status_code >= 400:
            try:
                data = response.json()
            except ValueError:
                data = {"error": response.text}
            logger.warning("WhatsApp API error %s: %s", response.status_code, data)
            raise WhatsAppAPIError(
                "Errore dalla WhatsApp Cloud API",
                status_code=response.status_code,
                payload=data,
            )
        return response.json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def send_text_message(
        self,
        to: str,
        body: str,
        *,
        preview_url: bool = False,
        metadata: Optional[MutableMapping[str, Any]] = None,
        contact: WhatsAppContact | None = None,
    ) -> SendResult:
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": _normalize_phone(to),
            "type": "text",
            "text": {"body": body, "preview_url": preview_url},
        }
        response_data = self._request("POST", f"/{self.phone_number_id}/messages", json_payload=payload)
        self._log_outgoing_message(
            response_data,
            to=_normalize_phone(to),
            message_type=WhatsAppMessage.MessageType.TEXT,
            body=body,
            metadata=metadata,
            contact=contact,
        )
        return SendResult(messages=response_data.get("messages", []), raw_response=response_data)

    def send_template_message(
        self,
        to: str,
        template_name: str,
        *,
        language: str = "it",
        components: Optional[Iterable[Mapping[str, Any]]] = None,
        metadata: Optional[MutableMapping[str, Any]] = None,
        contact: WhatsAppContact | None = None,
    ) -> SendResult:
        template: dict[str, Any] = {
            "name": template_name,
            "language": {"code": language},
        }
        if components:
            template["components"] = list(components)
        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": _normalize_phone(to),
            "type": "template",
            "template": template,
        }
        response_data = self._request("POST", f"/{self.phone_number_id}/messages", json_payload=payload)
        self._log_outgoing_message(
            response_data,
            to=_normalize_phone(to),
            message_type=WhatsAppMessage.MessageType.TEMPLATE,
            body="",
            metadata=metadata,
            contact=contact,
        )
        return SendResult(messages=response_data.get("messages", []), raw_response=response_data)

    def mark_message_read(self, message_id: str) -> None:
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        self._request("POST", f"/{self.phone_number_id}/messages", json_payload=payload)

    # ------------------------------------------------------------------
    # Internal logging helpers
    # ------------------------------------------------------------------
    def _log_outgoing_message(
        self,
        response_data: Mapping[str, Any],
        *,
        to: str,
        message_type: WhatsAppMessage.MessageType,
        body: str,
        metadata: Optional[MutableMapping[str, Any]] = None,
        contact: WhatsAppContact | None = None,
    ) -> None:
        message_items = response_data.get("messages", [])
        if not message_items:
            logger.warning("Risposta invio WhatsApp senza messages: %s", response_data)
            return
        message_data = message_items[0]
        message_id = message_data.get("id")
        if not message_id:
            logger.warning("Messaggio WhatsApp senza ID in risposta: %s", response_data)
            return
        status = message_data.get("message_status", WhatsAppMessage.Status.ACCEPTED)
        contact_obj = contact or _get_or_create_contact(wa_id=_normalize_phone(to))
        conversation = _get_or_create_conversation(self.account, contact_obj, external_id=None)
        metadata_payload = dict(metadata or {})
        WhatsAppMessage.objects.update_or_create(
            message_id=message_id,
            defaults={
                "account": self.account,
                "conversation": conversation,
                "contact": contact_obj,
                "direction": WhatsAppMessage.Direction.OUTGOING,
                "message_type": message_type,
                "status": status,
                "body": body,
                "metadata": metadata_payload,
                "raw_payload": response_data,
                "sent_at": timezone.now() if status != WhatsAppMessage.Status.ACCEPTED else None,
            },
        )
        conversation.touch()


# ----------------------------------------------------------------------
# Webhook ingestion
# ----------------------------------------------------------------------

def verify_signature(body: bytes, sent_signature: str | None, app_secret: str | None) -> bool:
    if not app_secret:
        return True
    if not sent_signature:
        return False
    try:
        method, signature = sent_signature.split("=", 1)
    except ValueError:
        return False
    if method.lower() != "sha256":
        return False
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def ingest_webhook_payload(payload: Mapping[str, Any], *, account_hint: WhatsAppBusinessAccount | None = None) -> dict[str, Any]:
    processed_messages = 0
    processed_statuses = 0
    entries = payload.get("entry", [])
    if not isinstance(entries, list):
        logger.debug("Entry payload non valido: %s", payload)
        return {"messages": processed_messages, "statuses": processed_statuses}
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        business_id = entry.get("id")
        account = account_hint
        if not account and business_id:
            account = WhatsAppBusinessAccount.objects.filter(business_account_id=business_id, active=True).first()
        if not account:
            try:
                account = get_default_account()
            except WhatsAppAPIError:
                logger.warning("Nessun account configurato per l'entry %s", business_id)
                continue
        for change in entry.get("changes", []):
            value = change.get("value") if isinstance(change, Mapping) else None
            if not isinstance(value, Mapping):
                continue
            processed_messages += _handle_incoming_messages(account, value)
            processed_statuses += _handle_status_updates(account, value)
    return {"messages": processed_messages, "statuses": processed_statuses}


def _handle_incoming_messages(account: WhatsAppBusinessAccount, value: Mapping[str, Any]) -> int:
    messages = value.get("messages")
    contacts = value.get("contacts") or []
    metadata = value.get("metadata") or {}
    if not messages:
        return 0
    messages_processed = 0
    for message in messages:
        if not isinstance(message, Mapping):
            continue
        wa_id = message.get("from")
        if not wa_id:
            continue
        contact_info = _extract_contact_info(wa_id, contacts)
        contact = _get_or_create_contact(
            wa_id=_normalize_phone(wa_id),
            phone_number=contact_info.get("wa_id", ""),
            display_name=contact_info.get("profile", {}).get("name", ""),
            verified_name=contact_info.get("profile", {}).get("name", ""),
        )
        conversation = _get_or_create_conversation(
            account,
            contact,
            external_id=None,
        )
        conversation.touch(_parse_timestamp(message.get("timestamp")))
        msg_type_name = message.get("type", "unknown")
        if msg_type_name not in WhatsAppMessage.MessageType.values:
            msg_type_name = WhatsAppMessage.MessageType.UNKNOWN
        body = _extract_message_body(message)
        context = message.get("context") or {}
        meta_copy = dict(metadata) if isinstance(metadata, Mapping) else metadata
        context_copy = dict(context) if isinstance(context, Mapping) else context
        with transaction.atomic():
            _msg, created = WhatsAppMessage.objects.update_or_create(
                message_id=message.get("id"),
                defaults={
                    "account": account,
                    "conversation": conversation,
                    "contact": contact,
                    "direction": WhatsAppMessage.Direction.INCOMING,
                    "message_type": msg_type_name,
                    "status": WhatsAppMessage.Status.RECEIVED,
                    "body": body,
                    "metadata": {"metadata": meta_copy, "context": context_copy},
                    "raw_payload": message,
                    "received_at": _parse_timestamp(message.get("timestamp")),
                },
            )
            if created:
                messages_processed += 1
    return messages_processed


def _handle_status_updates(account: WhatsAppBusinessAccount, value: Mapping[str, Any]) -> int:
    statuses = value.get("statuses")
    if not statuses:
        return 0
    updates = 0
    for status_info in statuses:
        if not isinstance(status_info, Mapping):
            continue
        message_id = status_info.get("id")
        if not message_id:
            continue
        status_value = status_info.get("status")
        timestamp = _parse_timestamp(status_info.get("timestamp"))
        errors = status_info.get("errors", []) or []
        conversation_data = status_info.get("conversation") or {}
        pricing_data = status_info.get("pricing") or {}
        with transaction.atomic():
            try:
                message = WhatsAppMessage.objects.select_for_update().get(message_id=message_id)
            except WhatsAppMessage.DoesNotExist:
                logger.debug("Status ricevuto per messaggio sconosciuto %s", message_id)
                continue
            if status_value:
                message.mark_status(status_value, when=timestamp)
            if errors:
                err = errors[0]
                message.error_code = err.get("code")
                message.error_title = err.get("title", "")
                message.error_message = err.get("message", "")
            else:
                message.error_code = None
                message.error_title = ""
                message.error_message = ""
            metadata = dict(message.metadata)
            metadata.setdefault("status_history", []).append(status_info)
            if pricing_data:
                metadata["pricing"] = pricing_data
            message.metadata = metadata
            message.save(update_fields=["error_code", "error_title", "error_message", "metadata", "updated_at"])
            conversation_id = conversation_data.get("id")
            if conversation_id and message.conversation:
                message.conversation.conversation_id = conversation_id
                expiration = conversation_data.get("expiration_timestamp")
                if expiration:
                    message.conversation.closed_at = _parse_timestamp(expiration)
                message.conversation.last_message_at = timestamp or timezone.now()
                message.conversation.save(update_fields=["conversation_id", "closed_at", "last_message_at", "updated_at"])
        updates += 1
    return updates


def _extract_contact_info(wa_id: str, contacts: Iterable[Any]) -> Mapping[str, Any]:
    for contact in contacts:
        if isinstance(contact, Mapping) and contact.get("wa_id") == wa_id:
            return contact
    return {"wa_id": wa_id}


def _get_or_create_contact(
    *,
    wa_id: str,
    phone_number: str | None = None,
    display_name: str | None = None,
    verified_name: str | None = None,
) -> WhatsAppContact:
    defaults = {
        "phone_number": phone_number or wa_id,
        "display_name": display_name or "",
        "verified_name": verified_name or "",
    }
    contact, _ = WhatsAppContact.objects.get_or_create(wa_id=wa_id, defaults=defaults)
    updated = False
    for field, value in defaults.items():
        if value and getattr(contact, field) != value:
            setattr(contact, field, value)
            updated = True
    if updated:
        contact.save(update_fields=["phone_number", "display_name", "verified_name", "updated_at"])
    return contact


def _get_or_create_conversation(
    account: WhatsAppBusinessAccount,
    contact: WhatsAppContact,
    external_id: str | None,
) -> WhatsAppConversation:
    conversation = (
        WhatsAppConversation.objects.filter(account=account, contact=contact, status=WhatsAppConversation.Status.OPEN)
        .order_by("-opened_at")
        .first()
    )
    if conversation:
        if external_id and conversation.conversation_id != external_id:
            conversation.conversation_id = external_id
            conversation.save(update_fields=["conversation_id", "updated_at"])
        return conversation
    conversation = WhatsAppConversation.objects.create(
        account=account,
        contact=contact,
        conversation_id=external_id or "",
        status=WhatsAppConversation.Status.OPEN,
    )
    return conversation


def _extract_message_body(message: Mapping[str, Any]) -> str:
    msg_type = message.get("type")
    if msg_type == "text":
        text = message.get("text") or {}
        return text.get("body", "")
    if msg_type == "button":
        button = message.get("button") or {}
        return button.get("text", "")
    if msg_type in {"interactive", "template"}:
        interactive = message.get("interactive") or {}
        body = interactive.get("body") or {}
        return body.get("text", "")
    if msg_type == "document":
        document = message.get("document") or {}
        return document.get("filename", "")
    return message.get("id", "")


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if isinstance(value, str) and value.isdigit():
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
    except Exception:  # pragma: no cover - fallback in caso di formato imprevisto
        logger.debug("Impossibile parse timestamp %s", value)
    return None
    
