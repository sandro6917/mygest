from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("pratiche", "0007_pratica_genitori_alter_pratica_figli"),
        ("fascicoli", "0007_alter_fascicolo_stato"),
        ("documenti", "0004_alter_documento_cliente_and_more"),
        ("comunicazioni", "0003_mailbox_comunicazione_contatti_destinatari_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Scadenza",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titolo", models.CharField(max_length=255)),
                ("descrizione", models.TextField(blank=True)),
                (
                    "stato",
                    models.CharField(
                        choices=[
                            ("bozza", "Bozza"),
                            ("attiva", "Attiva"),
                            ("completata", "Completata"),
                            ("archiviata", "Archiviata"),
                        ],
                        db_index=True,
                        default="attiva",
                        max_length=20,
                    ),
                ),
                (
                    "priorita",
                    models.CharField(
                        choices=[
                            ("low", "Bassa"),
                            ("medium", "Media"),
                            ("high", "Alta"),
                            ("critical", "Critica"),
                        ],
                        db_index=True,
                        default="medium",
                        max_length=20,
                    ),
                ),
                ("categoria", models.CharField(blank=True, max_length=120)),
                ("note_interne", models.TextField(blank=True)),
                (
                    "comunicazione_destinatari",
                    models.TextField(
                        blank=True,
                        help_text="Destinatari predefiniti per l'avviso via app Comunicazioni.",
                    ),
                ),
                (
                    "comunicazione_modello",
                    models.CharField(
                        blank=True,
                        help_text="Codice o slug di modello applicativo per generare il corpo della comunicazione.",
                        max_length=120,
                    ),
                ),
                (
                    "periodicita",
                    models.CharField(
                        choices=[
                            ("none", "Senza periodicità"),
                            ("daily", "Giornaliera"),
                            ("weekly", "Settimanale"),
                            ("monthly", "Mensile"),
                            ("yearly", "Annuale"),
                            ("custom", "Personalizzata (config JSON)"),
                        ],
                        default="none",
                        help_text="Impostazione generica utilizzata dalle procedure massive.",
                        max_length=20,
                    ),
                ),
                (
                    "periodicita_intervallo",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="Intervallo della periodicità (es: ogni 2 settimane).",
                    ),
                ),
                (
                    "periodicita_config",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Parametri aggiuntivi per la generazione delle occorrenze.",
                    ),
                ),
                (
                    "google_calendar_calendar_id",
                    models.CharField(
                        blank=True,
                        help_text="Identificativo del calendario Google da usare (lascia vuoto per default).",
                        max_length=255,
                    ),
                ),
                ("google_calendar_synced_at", models.DateTimeField(blank=True, null=True)),
                ("creato_il", models.DateTimeField(auto_now_add=True)),
                ("aggiornato_il", models.DateTimeField(auto_now=True)),
                (
                    "assegnatari",
                    models.ManyToManyField(
                        blank=True,
                        related_name="scadenze_assegnate",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "creato_da",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="scadenze_create",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "documenti",
                    models.ManyToManyField(blank=True, related_name="scadenze", to="documenti.documento"),
                ),
                (
                    "fascicoli",
                    models.ManyToManyField(blank=True, related_name="scadenze", to="fascicoli.fascicolo"),
                ),
                (
                    "pratiche",
                    models.ManyToManyField(blank=True, related_name="scadenze", to="pratiche.pratica"),
                ),
            ],
            options={
                "ordering": ["-aggiornato_il", "titolo"],
            },
        ),
        migrations.CreateModel(
            name="ScadenzaOccorrenza",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titolo", models.CharField(blank=True, max_length=255)),
                ("descrizione", models.TextField(blank=True)),
                ("inizio", models.DateTimeField(db_index=True)),
                ("fine", models.DateTimeField(blank=True, null=True)),
                (
                    "metodo_alert",
                    models.CharField(
                        choices=[("email", "Email"), ("webhook", "Webhook")],
                        db_index=True,
                        default="email",
                        max_length=20,
                    ),
                ),
                (
                    "offset_alert_minuti",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Minuti di anticipo per la notifica.",
                    ),
                ),
                (
                    "alert_config",
                    models.JSONField(blank=True, default=dict),
                ),
                ("alert_programmata_il", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("alert_inviata_il", models.DateTimeField(blank=True, null=True)),
                (
                    "stato",
                    models.CharField(
                        choices=[
                            ("pending", "In attesa"),
                            ("scheduled", "Programmato per invio alert"),
                            ("alerted", "Alert inviato"),
                            ("completed", "Completa"),
                            ("cancelled", "Annullata"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("google_calendar_event_id", models.CharField(blank=True, max_length=255)),
                ("google_calendar_synced_at", models.DateTimeField(blank=True, null=True)),
                ("creato_il", models.DateTimeField(auto_now_add=True)),
                ("aggiornato_il", models.DateTimeField(auto_now=True)),
                (
                    "comunicazione",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="scadenze_occorrenze",
                        to="comunicazioni.comunicazione",
                    ),
                ),
                (
                    "scadenza",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="occorrenze",
                        to="scadenze.scadenza",
                    ),
                ),
            ],
            options={
                "ordering": ["inizio"],
            },
        ),
        migrations.CreateModel(
            name="ScadenzaNotificaLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "evento",
                    models.CharField(
                        choices=[
                            ("calendar_sync", "Sincronizzazione calendario"),
                            ("alert_scheduled", "Alert programmato"),
                            ("alert_sent", "Alert inviato"),
                            ("webhook_error", "Errore webhook"),
                            ("email_error", "Errore email"),
                            ("bulk_generation", "Generazione massiva"),
                        ],
                        db_index=True,
                        max_length=40,
                    ),
                ),
                ("esito", models.BooleanField(default=True)),
                ("messaggio", models.TextField(blank=True)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("registrato_il", models.DateTimeField(auto_now_add=True)),
                (
                    "occorrenza",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="log_eventi",
                        to="scadenze.scadenzaoccorrenza",
                    ),
                ),
            ],
            options={
                "ordering": ["-registrato_il"],
            },
        ),
        migrations.CreateModel(
            name="ScadenzaWebhookPayload",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("inviato_il", models.DateTimeField(auto_now_add=True)),
                ("destinazione", models.URLField()),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("risposta_status", models.PositiveIntegerField(blank=True, null=True)),
                ("risposta_body", models.TextField(blank=True)),
                (
                    "occorrenza",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payload_webhook",
                        to="scadenze.scadenzaoccorrenza",
                    ),
                ),
            ],
            options={
                "ordering": ["-inviato_il"],
            },
        ),
        migrations.AddIndex(
            model_name="scadenza",
            index=models.Index(fields=["stato", "priorita"], name="scadenza_stato_priorita_idx"),
        ),
        migrations.AddIndex(
            model_name="scadenza",
            index=models.Index(fields=["creato_il"], name="scadenza_creato_il_idx"),
        ),
        migrations.AddConstraint(
            model_name="scadenza",
            constraint=models.CheckConstraint(
                check=models.Q(periodicita_intervallo__gte=1),
                name="scadenza_periodicita_intervallo_gte_1",
            ),
        ),
        migrations.AddIndex(
            model_name="scadenzaoccorrenza",
            index=models.Index(fields=["scadenza", "inizio"], name="occ_scadenza_inizio_idx"),
        ),
        migrations.AddIndex(
            model_name="scadenzaoccorrenza",
            index=models.Index(fields=["stato"], name="occ_stato_idx"),
        ),
        migrations.AddIndex(
            model_name="scadenzaoccorrenza",
            index=models.Index(fields=["alert_programmata_il"], name="occ_alert_programmata_idx"),
        ),
        migrations.AddIndex(
            model_name="scadenzanotificalog",
            index=models.Index(fields=["evento", "registrato_il"], name="occ_log_evento_idx"),
        ),
    ]
