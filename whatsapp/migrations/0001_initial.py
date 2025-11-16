# Generated manually for WhatsApp integration
from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def create_initial_account(apps, schema_editor):  # pragma: no cover - helper for deploy
    Account = apps.get_model("whatsapp", "WhatsAppBusinessAccount")
    if Account.objects.exists():
        return
    token = getattr(settings, "WHATSAPP_CLOUD_ACCESS_TOKEN", "")
    phone_id = getattr(settings, "WHATSAPP_CLOUD_PHONE_NUMBER_ID", "")
    verify_token = getattr(settings, "WHATSAPP_CLOUD_VERIFY_TOKEN", "")
    if token and phone_id and verify_token:
        Account.objects.create(
            name="Default",
            phone_number_id=phone_id,
            business_account_id=getattr(settings, "WHATSAPP_CLOUD_BUSINESS_ACCOUNT_ID", ""),
            access_token=token,
            verify_token=verify_token,
            app_secret=getattr(settings, "WHATSAPP_CLOUD_APP_SECRET", ""),
            api_version=getattr(settings, "WHATSAPP_CLOUD_API_VERSION", "v20.0"),
            is_default=True,
            active=True,
        )


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("anagrafiche", "0005_emailcontatto_mailinglist_mailinglistmembership_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsAppBusinessAccount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("phone_number_id", models.CharField(max_length=64, unique=True)),
                ("business_account_id", models.CharField(blank=True, max_length=64)),
                ("access_token", models.TextField()),
                ("verify_token", models.CharField(max_length=128)),
                ("app_secret", models.CharField(blank=True, max_length=128)),
                ("api_version", models.CharField(default="v20.0", max_length=16)),
                ("is_default", models.BooleanField(db_index=True, default=False)),
                ("active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
                "verbose_name": "Account Business WhatsApp",
                "verbose_name_plural": "Account Business WhatsApp",
            },
        ),
        migrations.CreateModel(
            name="WhatsAppContact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("wa_id", models.CharField(max_length=64, unique=True)),
                ("phone_number", models.CharField(blank=True, max_length=32)),
                ("display_name", models.CharField(blank=True, max_length=120)),
                ("verified_name", models.CharField(blank=True, max_length=120)),
                ("blocked", models.BooleanField(default=False)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "anagrafica",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="whatsapp_contacts",
                        to="anagrafiche.anagrafica",
                    ),
                ),
            ],
            options={
                "ordering": ["display_name", "wa_id"],
                "verbose_name": "Contatto WhatsApp",
                "verbose_name_plural": "Contatti WhatsApp",
            },
        ),
        migrations.CreateModel(
            name="WhatsAppConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("conversation_id", models.CharField(blank=True, db_index=True, max_length=64)),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Aperta"), ("closed", "Chiusa"), ("archived", "Archiviata")],
                        default="open",
                        max_length=16,
                    ),
                ),
                ("opened_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("last_message_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="conversations",
                        to="whatsapp.whatsappbusinessaccount",
                    ),
                ),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conversations",
                        to="whatsapp.whatsappcontact",
                    ),
                ),
            ],
            options={
                "ordering": ["-last_message_at", "-opened_at"],
                "verbose_name": "Conversazione WhatsApp",
                "verbose_name_plural": "Conversazioni WhatsApp",
            },
        ),
        migrations.CreateModel(
            name="WhatsAppMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message_id", models.CharField(max_length=128, unique=True)),
                (
                    "direction",
                    models.CharField(
                        choices=[("outgoing", "In uscita"), ("incoming", "In entrata")],
                        max_length=16,
                    ),
                ),
                (
                    "message_type",
                    models.CharField(
                        choices=[
                            ("text", "Testo"),
                            ("template", "Template"),
                            ("image", "Immagine"),
                            ("document", "Documento"),
                            ("audio", "Audio"),
                            ("video", "Video"),
                            ("button", "Pulsante"),
                            ("system", "Sistema"),
                            ("unknown", "Sconosciuto"),
                        ],
                        default="unknown",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("accepted", "Accettato"),
                            ("sent", "Inviato"),
                            ("delivered", "Consegnato"),
                            ("read", "Letto"),
                            ("failed", "Fallito"),
                            ("received", "Ricevuto"),
                        ],
                        default="accepted",
                        max_length=16,
                    ),
                ),
                ("body", models.TextField(blank=True)),
                ("caption", models.TextField(blank=True)),
                ("media_id", models.CharField(blank=True, max_length=128)),
                ("context_message_id", models.CharField(blank=True, max_length=128)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                ("received_at", models.DateTimeField(blank=True, null=True)),
                ("error_code", models.IntegerField(blank=True, null=True)),
                ("error_title", models.CharField(blank=True, max_length=255)),
                ("error_message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "account",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="messages",
                        to="whatsapp.whatsappbusinessaccount",
                    ),
                ),
                (
                    "contact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="whatsapp.whatsappcontact",
                    ),
                ),
                (
                    "conversation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="messages",
                        to="whatsapp.whatsappconversation",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Messaggio WhatsApp",
                "verbose_name_plural": "Messaggi WhatsApp",
            },
        ),
        migrations.AddIndex(
            model_name="whatsappconversation",
            index=models.Index(fields=["account", "contact", "status"], name="whatsapp_co_account_31bad8_idx"),
        ),
        migrations.AddIndex(
            model_name="whatsappconversation",
            index=models.Index(fields=["conversation_id"], name="whatsapp_co_convers_1c75fb_idx"),
        ),
        migrations.AddConstraint(
            model_name="whatsappconversation",
            constraint=models.UniqueConstraint(
                condition=models.Q(status="open"),
                fields=("account", "contact"),
                name="whatsapp_one_open_conversation_per_contact",
            ),
        ),
        migrations.AddIndex(
            model_name="whatsappmessage",
            index=models.Index(fields=["account", "status"], name="whatsapp_me_account_9cfbc7_idx"),
        ),
        migrations.AddIndex(
            model_name="whatsappmessage",
            index=models.Index(fields=["contact", "direction"], name="whatsapp_me_contact_c7622c_idx"),
        ),
        migrations.AddIndex(
            model_name="whatsappmessage",
            index=models.Index(fields=["created_at"], name="whatsapp_me_created_d3385c_idx"),
        ),
        migrations.AddConstraint(
            model_name="whatsappbusinessaccount",
            constraint=models.UniqueConstraint(
                condition=models.Q(is_default=True),
                fields=["is_default"],
                name="unique_whatsapp_default_account",
            ),
        ),
        migrations.RunPython(create_initial_account, migrations.RunPython.noop),
    ]
