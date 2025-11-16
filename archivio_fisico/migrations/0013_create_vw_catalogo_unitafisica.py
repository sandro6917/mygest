from django.db import migrations

VIEW_NAME = "vw_catalogo_unitafisica"

CREATE_VIEW_SQL = """
CREATE VIEW vw_catalogo_unitafisica AS
WITH movimenti_con_ubicazione AS (
    SELECT
        mp.id AS movimento_id,
        mp.documento_id,
        mp.fascicolo_id,
        mp.anno,
        mp.numero,
        mp.direzione,
        mp.data,
        mp.cliente_id,
        mp.destinatario,
        mp.ubicazione_id,
        uf.codice AS ubicazione_codice,
        uf.nome AS ubicazione_nome
    FROM protocollo_movimentoprotocollo mp
    INNER JOIN archivio_fisico_unitafisica uf
        ON uf.id = mp.ubicazione_id
)
SELECT
    'documento'::text AS entity_type,
    d.id AS entity_id,
    d.codice AS entity_codice,
    d.descrizione AS entity_descrizione,
    d.cliente_id AS cliente_id,
    m.movimento_id,
    m.anno AS movimento_anno,
    m.numero AS movimento_numero,
    m.direzione AS movimento_direzione,
    m.data AS movimento_data,
    m.destinatario,
    m.ubicazione_id,
    m.ubicazione_codice,
    m.ubicazione_nome
FROM documenti_documento d
INNER JOIN movimenti_con_ubicazione m
    ON m.documento_id = d.id

UNION ALL

SELECT
    'fascicolo'::text AS entity_type,
    f.id AS entity_id,
    f.codice AS entity_codice,
    f.titolo AS entity_descrizione,
    f.cliente_id AS cliente_id,
    m.movimento_id,
    m.anno AS movimento_anno,
    m.numero AS movimento_numero,
    m.direzione AS movimento_direzione,
    m.data AS movimento_data,
    m.destinatario,
    m.ubicazione_id,
    m.ubicazione_codice,
    m.ubicazione_nome
FROM fascicoli_fascicolo f
INNER JOIN movimenti_con_ubicazione m
    ON m.fascicolo_id = f.id;
"""

DROP_VIEW_SQL = "DROP VIEW IF EXISTS vw_catalogo_unitafisica;"


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
        ("archivio_fisico", "0012_remove_operazionearchivio_unita_fisica_destinazione_and_more"),
    ]

    operations = [
        migrations.RunPython(create_view, drop_view),
    ]
