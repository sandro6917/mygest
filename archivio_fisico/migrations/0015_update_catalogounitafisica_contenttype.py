from django.db import migrations


def _ensure_content_type(apps, model_code: str, *, delete: bool = False) -> None:
    ContentType = apps.get_model("contenttypes", "ContentType")
    lookup = {"app_label": "archivio_fisico", "model": model_code}
    if delete:
        ContentType.objects.filter(**lookup).delete()
    else:
        ContentType.objects.get_or_create(**lookup)


def forwards(apps, schema_editor):
    _ensure_content_type(apps, "catalogounitafisica")


def backwards(apps, schema_editor):
    _ensure_content_type(apps, "catalogounitafisica", delete=True)


class Migration(migrations.Migration):

    dependencies = [
        ("archivio_fisico", "0014_vwcatalogounitafisica"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
