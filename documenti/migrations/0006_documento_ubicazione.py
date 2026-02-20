from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("archivio_fisico", "0019_alter_operazionearchivio_verbale_scan_and_more"),
        ("documenti", "0005_filedeletionrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="documento",
            name="ubicazione",
            field=models.ForeignKey(
                to="archivio_fisico.unitafisica",
                on_delete=models.SET_NULL,
                related_name="documenti",
                null=True,
                blank=True,
                help_text="Unità fisica corrente (solo per documenti cartacei).",
            ),
        ),
    ]
