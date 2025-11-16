from django.db import migrations, models


def build_progressivo(unita):
    parts = []
    if unita.codice:
        parts.append(unita.codice.strip())
    if unita.nome:
        parts.append(unita.nome.strip())
    if unita.tipo:
        parts.append(unita.get_tipo_display())
    return "-".join(parts)


def populate_progressivo(apps, schema_editor):
    UnitaFisica = apps.get_model("archivio_fisico", "UnitaFisica")
    for unita in UnitaFisica.objects.all().iterator():
        progressivo = build_progressivo(unita)
        UnitaFisica.objects.filter(pk=unita.pk).update(progressivo=progressivo)


class Migration(migrations.Migration):

    dependencies = [
        ("archivio_fisico", "0006_alter_operazionearchivio_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="unitafisica",
            name="progressivo",
            field=models.CharField(blank=True, db_index=True, default="", editable=False, max_length=300),
        ),
        migrations.RunPython(populate_progressivo, reverse_code=migrations.RunPython.noop),
    ]
