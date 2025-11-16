from django.db import migrations, models

VIEW_NAME = "vw_unitafisica_subunita_primo_livello"

CREATE_VIEW_SQL = f"""
CREATE VIEW {VIEW_NAME} AS
SELECT
    parent.id AS unita_id,
    parent.codice AS unita_codice,
    parent.nome AS unita_nome,
    parent.tipo AS unita_tipo,
    parent.attivo AS unita_attivo,
    parent.archivio_fisso AS unita_archivio_fisso,
    parent.full_path AS unita_full_path,
    parent.progressivo AS unita_progressivo,
    child.id AS subunita_id,
    child.codice AS subunita_codice,
    child.nome AS subunita_nome,
    child.tipo AS subunita_tipo,
    child.ordine AS subunita_ordine,
    child.attivo AS subunita_attivo,
    child.archivio_fisso AS subunita_archivio_fisso,
    child.full_path AS subunita_full_path,
    child.progressivo AS subunita_progressivo
FROM archivio_fisico_unitafisica parent
INNER JOIN archivio_fisico_unitafisica child ON child.parent_id = parent.id;
"""

DROP_VIEW_SQL = f"DROP VIEW IF EXISTS {VIEW_NAME};"


def create_view(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(DROP_VIEW_SQL)
    schema_editor.execute(CREATE_VIEW_SQL)


def drop_view(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute(DROP_VIEW_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ("archivio_fisico", "0016_catalogounitafisica_delete_vwcatalogounitafisica"),
    ]

    operations = [
        migrations.RunPython(create_view, drop_view),
        migrations.CreateModel(
            name="UnitaFisicaSubunita",
            fields=[
                ("unita_id", models.BigIntegerField()),
                ("unita_codice", models.CharField(max_length=60)),
                ("unita_nome", models.CharField(max_length=120)),
                ("unita_tipo", models.CharField(max_length=20)),
                ("unita_attivo", models.BooleanField()),
                ("unita_archivio_fisso", models.BooleanField()),
                ("unita_full_path", models.CharField(max_length=500)),
                ("unita_progressivo", models.CharField(max_length=300)),
                ("subunita_id", models.BigIntegerField(primary_key=True, serialize=False)),
                ("subunita_codice", models.CharField(max_length=60)),
                ("subunita_nome", models.CharField(max_length=120)),
                ("subunita_tipo", models.CharField(max_length=20)),
                ("subunita_ordine", models.IntegerField()),
                ("subunita_attivo", models.BooleanField()),
                ("subunita_archivio_fisso", models.BooleanField()),
                ("subunita_full_path", models.CharField(max_length=500)),
                ("subunita_progressivo", models.CharField(max_length=300)),
            ],
            options={
                "db_table": VIEW_NAME,
                "managed": False,
                "ordering": ["unita_codice", "subunita_ordine", "subunita_codice"],
            },
        ),
    ]
