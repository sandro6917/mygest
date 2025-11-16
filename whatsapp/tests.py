from __future__ import annotations

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import WhatsAppBusinessAccount, WhatsAppContact, WhatsAppMessage
from .services import ingest_webhook_payload


class WhatsAppWebhookTests(TestCase):
    def setUp(self) -> None:
        self.account = WhatsAppBusinessAccount.objects.create(
            name="Test Account",
            phone_number_id="1234567890",
            business_account_id="123",
            access_token="token",
            verify_token="verify",
            api_version="v20.0",
            is_default=True,
        )

    def test_ingest_incoming_message_creates_contact_and_message(self) -> None:
        payload = {
            "entry": [
                {
                    "id": self.account.business_account_id,
                    "changes": [
                        {
                            "value": {
                                "contacts": [
                                    {
                                        "profile": {"name": "Mario Rossi"},
                                        "wa_id": "393470000000",
                                    }
                                ],
                                "messages": [
                                    {
                                        "from": "393470000000",
                                        "id": "wamid.HBgLMTEyMw==",
                                        "timestamp": str(int(timezone.now().timestamp())),
                                        "text": {"body": "Ciao"},
                                        "type": "text",
                                    }
                                ],
                                "metadata": {"phone_number_id": self.account.phone_number_id},
                            }
                        }
                    ],
                }
            ]
        }
        result = ingest_webhook_payload(payload)
        self.assertEqual(result["messages"], 1)
        contact = WhatsAppContact.objects.get()
        self.assertEqual(contact.display_name, "Mario Rossi")
        message = WhatsAppMessage.objects.get()
        self.assertEqual(message.body, "Ciao")
        self.assertEqual(message.direction, WhatsAppMessage.Direction.INCOMING)

    def test_webhook_get_verification(self) -> None:
        url = reverse("whatsapp:webhook")
        response = self.client.get(url, {"hub.mode": "subscribe", "hub.challenge": "abc", "hub.verify_token": "verify"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"abc")

    @override_settings(WHATSAPP_CLOUD_ACCESS_TOKEN="fallback", WHATSAPP_CLOUD_PHONE_NUMBER_ID="987")
    def test_ingest_without_db_account_uses_settings(self) -> None:
        WhatsAppBusinessAccount.objects.all().delete()
        payload = {"entry": []}
        result = ingest_webhook_payload(payload)
        self.assertEqual(result, {"messages": 0, "statuses": 0})

    def test_status_update_marks_message(self) -> None:
        contact = WhatsAppContact.objects.create(wa_id="393470000000", display_name="Mario")
        message = WhatsAppMessage.objects.create(
            account=self.account,
            contact=contact,
            conversation=None,
            message_id="wamid.HBgLMTEyMw==",
            direction=WhatsAppMessage.Direction.OUTGOING,
            message_type=WhatsAppMessage.MessageType.TEXT,
        )
        payload = {
            "entry": [
                {
                    "id": self.account.business_account_id,
                    "changes": [
                        {
                            "value": {
                                "statuses": [
                                    {
                                        "id": message.message_id,
                                        "status": "delivered",
                                        "timestamp": str(int(timezone.now().timestamp())),
                                    }
                                ]
                            }
                        }
                    ],
                }
            ]
        }
        result = ingest_webhook_payload(payload)
        self.assertEqual(result["statuses"], 1)
        message.refresh_from_db()
        self.assertEqual(message.status, WhatsAppMessage.Status.DELIVERED)
        self.assertIsNotNone(message.delivered_at)
