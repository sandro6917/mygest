from django.db import migrations, models


def copy_fk_to_m2m(apps, schema_editor):
    Fascicolo = apps.get_model("fascicoli", "Fascicolo")
    Through = Fascicolo.pratiche.through
    db = schema_editor.connection.alias

    qs = Fascicolo.objects.using(db).exclude(pratica_id__isnull=True).only("id", "pratica_id")
    for f in qs.iterator():
        # Copia il vecchio FK nella tabella di relazione M2M
        Through.objects.using(db).create(fascicolo_id=f.id, pratica_id=f.pratica_id)


class Migration(migrations.Migration):
    dependencies = [
        ("pratiche", "0001_initial"),
        ("fascicoli", "0004_alter_fascicolo_ubicazione"),
    ]

    operations = [
        migrations.AddField(
            model_name="fascicolo",
            name="pratiche",
            field=models.ManyToManyField(
                to="pratiche.Pratica",
                related_name="fascicoli",
                blank=True,
            ),
        ),
        migrations.RunPython(copy_fk_to_m2m, migrations.RunPython.noop),
        migrations.RemoveField(model_name="fascicolo", name="pratica"),
    ]
