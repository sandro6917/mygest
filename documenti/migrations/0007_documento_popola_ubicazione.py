from django.db import migrations


def copia_ubicazioni(apps, schema_editor):
    Documento = apps.get_model("documenti", "Documento")
    qs = (
        Documento.objects
        .select_related("fascicolo")
        .filter(digitale=False, fascicolo__isnull=False, fascicolo__ubicazione__isnull=False)
    )
    for documento in qs.iterator(chunk_size=500):
        ubicazione_id = documento.fascicolo.ubicazione_id
        if ubicazione_id and documento.ubicazione_id != ubicazione_id:
            documento.ubicazione_id = ubicazione_id
            documento.save(update_fields=["ubicazione"])


def svuota_ubicazioni(apps, schema_editor):
    Documento = apps.get_model("documenti", "Documento")
    Documento.objects.update(ubicazione=None)


class Migration(migrations.Migration):

    dependencies = [
        ("documenti", "0006_documento_ubicazione"),
    ]

    operations = [
        migrations.RunPython(copia_ubicazioni, svuota_ubicazioni),
    ]
