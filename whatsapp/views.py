from __future__ import annotations

import json
import logging
from typing import Any

from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import WhatsAppBusinessAccount
from .services import ingest_webhook_payload, verify_signature, get_default_account

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class WhatsAppWebhookView(View):
    http_method_names = ["get", "post"]

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        mode = request.GET.get("hub.mode")
        verify_token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        try:
            account = self._resolve_account()
        except Exception:  # pragma: no cover - fallback
            logger.warning("Webhook GET senza account configurato")
            return HttpResponseForbidden("Account non configurato")
        if mode == "subscribe" and challenge and verify_token == account.verify_token:
            return HttpResponse(challenge)
        return HttpResponseForbidden("Verifica fallita")

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        raw_body = request.body
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            logger.warning("Payload webhook non valido")
            return HttpResponse(status=400)

        account = self._resolve_account(payload)
        signature = request.headers.get("X-Hub-Signature-256")
        if not verify_signature(raw_body, signature, account.app_secret or None):
            logger.warning("Signature webhook non valida per account %s", account.pk if account.pk else account.name)
            return HttpResponseForbidden("Signature non valida")

        result = ingest_webhook_payload(payload, account_hint=account)
        logger.debug("Webhook processato: %s", result)
        return JsonResponse({"status": "ok", **result})

    def _resolve_account(self, payload: dict[str, Any] | None = None) -> WhatsAppBusinessAccount:
        if payload:
            entries = payload.get("entry") or []
            for entry in entries:
                business_id = entry.get("id") if isinstance(entry, dict) else None
                if business_id:
                    account = WhatsAppBusinessAccount.objects.filter(business_account_id=business_id, active=True).first()
                    if account:
                        return account
        try:
            return get_default_account()
        except Exception as exc:  # pragma: no cover - se non esiste account
            logger.error("Nessun account WhatsApp configurato: %s", exc)
            raise
