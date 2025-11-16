from django.db import migrations, models

def copy_ubicazione_to_unita(apps, schema_editor):
    Fascicolo = apps.get_model("fascicoli", "Fascicolo")
    CollocazioneFisica = apps.get_model("archivio_fisico", "CollocazioneFisica")
    UnitaFisica = apps.get_model("archivio_fisico", "UnitaFisica")

    for f in Fascicolo.objects.all().only("id", "ubicazione_id"):
        if f.ubicazione_id:
            try:
                coll = CollocazioneFisica.objects.select_related("unita").get(pk=f.ubicazione_id)
            except CollocazioneFisica.DoesNotExist:
                continue
            Fascicolo.objects.filter(pk=f.id).update(ubicazione_unita_id=getattr(coll, "unita_id", None))

class Migration(migrations.Migration):
    dependencies = [
        ("fascicoli", "0002_remove_fascicolo_protocollo_data_and_more"),  # aggiorna
        ("archivio_fisico", "0004_ubicazione"),   # assicura che UnitaFisica sia presente
    ]

    operations = [
        # 1) aggiungi campo temporaneo
        migrations.AddField(
            model_name="fascicolo",
            name="ubicazione_unita",
            field=models.ForeignKey(to="archivio_fisico.unitafisica", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"),
        ),
        # 2) copia dati
        migrations.RunPython(copy_ubicazione_to_unita, migrations.RunPython.noop),
        # 3) rimuovi vecchio campo
        migrations.RemoveField(model_name="fascicolo", name="ubicazione"),
        # 4) rinomina campo temporaneo in definitivo
        migrations.RenameField(model_name="fascicolo", old_name="ubicazione_unita", new_name="ubicazione"),
    ]