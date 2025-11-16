from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinValueValidator

def migrate_legacy_alerts(apps, schema_editor):
    Scadenza = apps.get_model("pratiche", "Scadenza")
    ScadenzaAlert = apps.get_model("pratiche", "ScadenzaAlert")
    for s in Scadenza.objects.all().only("id", "scadenza_at", "alert_offset_min", "alert_method", "alert_email_to", "alert_webhook_url", "alert_inviato_il"):
        if not s.scadenza_at:
            continue
        # Crea un singolo alert equivalente (se offset > 0)
        if (s.alert_offset_min or 0) > 0:
            ScadenzaAlert.objects.create(
                scadenza_id=s.id,
                unita="d" if s.alert_offset_min % 1440 == 0 else "min",  # best effort
                valore=(s.alert_offset_min // 1440) if s.alert_offset_min % 1440 == 0 else s.alert_offset_min,
                metodo=s.alert_method or "email",
                email_to=s.alert_email_to or "",
                webhook_url=s.alert_webhook_url or "",
                inviato_il=s.alert_inviato_il,
            )

class Migration(migrations.Migration):
    dependencies = [
        ("pratiche", "0003_alter_pratica_cliente"),
    ]
    operations = [
        migrations.AlterField(
            model_name="scadenza",
            name="alert_at",
            field=models.DateTimeField(db_index=True, editable=False, null=True, blank=True),
        ),
        migrations.CreateModel(
            name="ScadenzaAlert",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("unita", models.CharField(max_length=3, choices=[("min","Minuti"),("h","Ore"),("d","Giorni"),("w","Settimane")], db_index=True, default="d")),
                ("valore", models.PositiveIntegerField(validators=[MinValueValidator(1)])),
                ("metodo", models.CharField(max_length=20, choices=[("email","Email"),("webhook","Webhook")], default="email")),
                ("email_to", models.CharField(max_length=500, blank=True)),
                ("webhook_url", models.URLField(blank=True)),
                ("alert_at", models.DateTimeField(db_index=True, editable=False, null=True, blank=True)),
                ("inviato_il", models.DateTimeField(null=True, blank=True)),
                ("attivo", models.BooleanField(default=True, db_index=True)),
                ("creato_il", models.DateTimeField(auto_now_add=True)),
                ("aggiornato_il", models.DateTimeField(auto_now=True)),
                ("scadenza", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="alerts", to="pratiche.scadenza")),
            ],
            options={"ordering": ["alert_at"]},
        ),
        migrations.RunPython(migrate_legacy_alerts, migrations.RunPython.noop),
    ]