from django.db import migrations, models

VIEW_NAME = "vw_archivio_fisico_lista_stampa"

CREATE_VIEW_SQL = f"""
CREATE VIEW {VIEW_NAME} AS
WITH RECURSIVE
ct_fascicolo AS (
    SELECT id AS content_type_id
    FROM django_content_type
    WHERE app_label = 'fascicoli'
      AND model = 'fascicolo'
    LIMIT 1
),
fascicoli_raw AS (
    SELECT
        cf.unita_id,
        f.id AS fascicolo_id,
        f.parent_id,
        f.codice,
        f.titolo,
        f.anno,
        f.stato,
        f.progressivo,
        f.sub_progressivo,
        f.cliente_id,
        CASE
            WHEN anag.ragione_sociale IS NOT NULL AND anag.ragione_sociale <> '' THEN anag.ragione_sociale
            WHEN anag.cognome IS NOT NULL OR anag.nome IS NOT NULL THEN NULLIF(trim(CONCAT_WS(' ', anag.cognome, anag.nome)), '')
            ELSE NULL
        END AS cliente_label,
        proto.anno AS protocollo_anno,
        proto.numero AS protocollo_numero,
        proto.data::date AS protocollo_data,
        proto.direzione AS protocollo_direzione,
        CASE
            WHEN f.codice IS NOT NULL AND f.codice <> '' THEN f.codice
            WHEN f.parent_id IS NOT NULL AND f.sub_progressivo IS NOT NULL AND f.sub_progressivo > 0 THEN LPAD(f.sub_progressivo::text, 6, '0')
            WHEN f.progressivo IS NOT NULL AND f.progressivo > 0 THEN LPAD(f.progressivo::text, 6, '0')
            ELSE LPAD(f.id::text, 6, '0')
        END AS order_token
    FROM archivio_fisico_collocazionefisica cf
    JOIN ct_fascicolo ct ON ct.content_type_id = cf.content_type_id
    JOIN fascicoli_fascicolo f ON f.id = cf.object_id
    LEFT JOIN anagrafiche_cliente cli ON cli.id = f.cliente_id
    LEFT JOIN anagrafiche_anagrafica anag ON anag.id = cli.anagrafica_id
    LEFT JOIN LATERAL (
        SELECT mp.anno, mp.numero, mp.data, mp.direzione
        FROM protocollo_movimentoprotocollo mp
        WHERE mp.fascicolo_id = f.id
        ORDER BY mp.data
        LIMIT 1
    ) proto ON TRUE
    WHERE cf.attiva
),
fascicoli_tree AS (
    SELECT
        fr.unita_id,
        fr.fascicolo_id,
        fr.parent_id AS fascicolo_parent_id,
        1 AS level,
        '10F' || fr.order_token AS sort_path,
        'F:' || fr.order_token AS path_tokens,
        'UNIT'::text AS parent_node_type,
        fr.unita_id AS parent_node_id,
        fr.codice,
        fr.titolo,
        fr.anno,
        fr.stato,
        fr.cliente_id,
        fr.cliente_label,
        fr.protocollo_anno,
        fr.protocollo_numero,
        fr.protocollo_data,
        fr.protocollo_direzione
    FROM fascicoli_raw fr
    WHERE NOT EXISTS (
        SELECT 1
        FROM fascicoli_raw p
        WHERE p.unita_id = fr.unita_id
          AND p.fascicolo_id = fr.parent_id
    )
    UNION ALL
    SELECT
        child.unita_id,
        child.fascicolo_id,
        child.parent_id AS fascicolo_parent_id,
        parent.level + 1 AS level,
        parent.sort_path || '.10F' || child.order_token AS sort_path,
        parent.path_tokens || '|F:' || child.order_token AS path_tokens,
        'FASCICOLO'::text AS parent_node_type,
        parent.fascicolo_id AS parent_node_id,
        child.codice,
        child.titolo,
        child.anno,
        child.stato,
        child.cliente_id,
        child.cliente_label,
        child.protocollo_anno,
        child.protocollo_numero,
        child.protocollo_data,
        child.protocollo_direzione
    FROM fascicoli_raw child
    JOIN fascicoli_tree parent
      ON parent.unita_id = child.unita_id
     AND parent.fascicolo_id = child.parent_id
),
documenti_raw AS (
    SELECT
        cf.unita_id,
        d.id AS documento_id,
        d.fascicolo_id,
        d.codice,
        d.descrizione,
        d.data_documento,
        d.stato,
        d.digitale,
        d.tracciabile,
        d.cliente_id,
        CASE
            WHEN anag.ragione_sociale IS NOT NULL AND anag.ragione_sociale <> '' THEN anag.ragione_sociale
            WHEN anag.cognome IS NOT NULL OR anag.nome IS NOT NULL THEN NULLIF(trim(CONCAT_WS(' ', anag.cognome, anag.nome)), '')
            ELSE NULL
        END AS cliente_label,
        proto.anno AS protocollo_anno,
        proto.numero AS protocollo_numero,
        proto.data::date AS protocollo_data,
        proto.direzione AS protocollo_direzione,
        CASE
            WHEN d.codice IS NOT NULL AND d.codice <> '' THEN d.codice
            ELSE LPAD(d.id::text, 8, '0')
        END AS order_token
    FROM archivio_fisico_collocazionefisica cf
    JOIN documenti_documento d ON d.id = cf.documento_id
    LEFT JOIN anagrafiche_cliente cli ON cli.id = d.cliente_id
    LEFT JOIN anagrafiche_anagrafica anag ON anag.id = cli.anagrafica_id
    LEFT JOIN LATERAL (
        SELECT mp.anno, mp.numero, mp.data, mp.direzione
        FROM protocollo_movimentoprotocollo mp
        WHERE mp.documento_id = d.id
        ORDER BY mp.data
        LIMIT 1
    ) proto ON TRUE
    WHERE cf.attiva
),
documenti_tree AS (
    SELECT
        dr.unita_id,
        dr.documento_id,
        dr.fascicolo_id,
        COALESCE(ft.level + 1, 1) AS level,
        CASE
            WHEN ft.fascicolo_id IS NOT NULL THEN ft.sort_path || '.20D' || dr.order_token
            ELSE '20D' || dr.order_token
        END AS sort_path,
        CASE
            WHEN ft.path_tokens IS NOT NULL THEN ft.path_tokens || '|D:' || dr.order_token
            ELSE 'D:' || dr.order_token
        END AS path_tokens,
        CASE
            WHEN ft.fascicolo_id IS NOT NULL THEN 'FASCICOLO'::text
            ELSE 'UNIT'::text
        END AS parent_node_type,
        CASE
            WHEN ft.fascicolo_id IS NOT NULL THEN ft.fascicolo_id
            ELSE dr.unita_id
        END AS parent_node_id,
        dr.codice,
        dr.descrizione,
        dr.data_documento,
        dr.stato,
        dr.digitale,
        dr.tracciabile,
        dr.cliente_id,
        dr.cliente_label,
        dr.protocollo_anno,
        dr.protocollo_numero,
        dr.protocollo_data,
        dr.protocollo_direzione
    FROM documenti_raw dr
    LEFT JOIN fascicoli_tree ft
      ON ft.unita_id = dr.unita_id
     AND ft.fascicolo_id = dr.fascicolo_id
)
SELECT
    combined.node_key,
    combined.unit_id,
    combined.unit_parent_id,
    combined.unit_codice,
    combined.unit_nome,
    combined.unit_tipo,
    combined.unit_attivo,
    combined.unit_archivio_fisso,
    combined.unit_full_path,
    combined.unit_progressivo,
    combined.node_type,
    combined.node_id,
    combined.node_label,
    combined.parent_node_type,
    combined.parent_node_id,
    combined.level,
    combined.tree_sort_key,
    combined.tree_path,
    combined.codice,
    combined.titolo,
    combined.descrizione,
    combined.anno,
    combined.data_documento,
    combined.cliente_label,
    combined.protocollo_anno,
    combined.protocollo_numero,
    combined.protocollo_direzione,
    combined.protocollo_data,
    combined.digitale,
    combined.tracciabile,
    combined.fascicolo_parent_id,
    combined.documento_fascicolo_id
FROM (
    SELECT
        ('UNIT:' || u.id)::text AS node_key,
        u.id::bigint AS unit_id,
        u.parent_id::bigint AS unit_parent_id,
        u.codice AS unit_codice,
        u.nome AS unit_nome,
        u.tipo AS unit_tipo,
        u.attivo AS unit_attivo,
        u.archivio_fisso AS unit_archivio_fisso,
        u.full_path AS unit_full_path,
        u.progressivo AS unit_progressivo,
        'UNIT'::text AS node_type,
        u.id::bigint AS node_id,
        u.nome AS node_label,
        CASE WHEN u.parent_id IS NULL THEN NULL ELSE 'UNIT'::text END AS parent_node_type,
        u.parent_id::bigint AS parent_node_id,
        0 AS level,
        ('00U|' || COALESCE(u.full_path, u.codice, ''))::text AS tree_sort_key,
        ('UNIT:' || COALESCE(u.full_path, u.codice, ''))::text AS tree_path,
        u.codice AS codice,
        u.nome AS titolo,
        NULL::text AS descrizione,
        NULL::integer AS anno,
        NULL::date AS data_documento,
        NULL::text AS cliente_label,
        NULL::integer AS protocollo_anno,
        NULL::integer AS protocollo_numero,
        NULL::varchar(3) AS protocollo_direzione,
        NULL::date AS protocollo_data,
        NULL::boolean AS digitale,
        NULL::boolean AS tracciabile,
        NULL::bigint AS fascicolo_parent_id,
        NULL::bigint AS documento_fascicolo_id
    FROM archivio_fisico_unitafisica u

    UNION ALL

    SELECT
        ('FASCICOLO:' || ft.fascicolo_id)::text AS node_key,
        ft.unita_id::bigint AS unit_id,
        u.parent_id::bigint AS unit_parent_id,
        u.codice AS unit_codice,
        u.nome AS unit_nome,
        u.tipo AS unit_tipo,
        u.attivo AS unit_attivo,
        u.archivio_fisso AS unit_archivio_fisso,
        u.full_path AS unit_full_path,
        u.progressivo AS unit_progressivo,
        'FASCICOLO'::text AS node_type,
        ft.fascicolo_id::bigint AS node_id,
        COALESCE(NULLIF(ft.codice, ''), ft.titolo, 'Fascicolo ' || ft.fascicolo_id) AS node_label,
        ft.parent_node_type,
        ft.parent_node_id::bigint AS parent_node_id,
        ft.level,
        ('10F|' || ft.sort_path)::text AS tree_sort_key,
        (COALESCE(u.full_path, '') || '|' || ft.path_tokens)::text AS tree_path,
        ft.codice AS codice,
        ft.titolo AS titolo,
        NULL::text AS descrizione,
        ft.anno AS anno,
        NULL::date AS data_documento,
        ft.cliente_label AS cliente_label,
        ft.protocollo_anno,
        ft.protocollo_numero,
        ft.protocollo_direzione::varchar(3),
        ft.protocollo_data,
        NULL::boolean AS digitale,
        NULL::boolean AS tracciabile,
        ft.fascicolo_parent_id::bigint AS fascicolo_parent_id,
        NULL::bigint AS documento_fascicolo_id
    FROM fascicoli_tree ft
    JOIN archivio_fisico_unitafisica u ON u.id = ft.unita_id

    UNION ALL

    SELECT
        ('DOCUMENTO:' || dt.documento_id)::text AS node_key,
        dt.unita_id::bigint AS unit_id,
        u.parent_id::bigint AS unit_parent_id,
        u.codice AS unit_codice,
        u.nome AS unit_nome,
        u.tipo AS unit_tipo,
        u.attivo AS unit_attivo,
        u.archivio_fisso AS unit_archivio_fisso,
        u.full_path AS unit_full_path,
        u.progressivo AS unit_progressivo,
        'DOCUMENTO'::text AS node_type,
        dt.documento_id::bigint AS node_id,
        COALESCE(NULLIF(dt.codice, ''), dt.descrizione, 'Documento ' || dt.documento_id) AS node_label,
        dt.parent_node_type,
        dt.parent_node_id::bigint AS parent_node_id,
        dt.level,
        ('20D|' || dt.sort_path)::text AS tree_sort_key,
        (COALESCE(u.full_path, '') || '|' || dt.path_tokens)::text AS tree_path,
        dt.codice AS codice,
        NULL::text AS titolo,
        dt.descrizione AS descrizione,
        NULL::integer AS anno,
        dt.data_documento,
        dt.cliente_label,
        dt.protocollo_anno,
        dt.protocollo_numero,
        dt.protocollo_direzione::varchar(3),
        dt.protocollo_data,
        dt.digitale,
        dt.tracciabile,
        NULL::bigint AS fascicolo_parent_id,
        dt.fascicolo_id::bigint AS documento_fascicolo_id
    FROM documenti_tree dt
    JOIN archivio_fisico_unitafisica u ON u.id = dt.unita_id
) AS combined
ORDER BY combined.unit_full_path, combined.tree_sort_key, combined.node_key;
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
        ("archivio_fisico", "0017_create_vw_unitafisica_subunita"),
        ("documenti", "0003_documento_digitale_alter_documento_stato"),
    ]

    operations = [
        migrations.RunPython(create_view, drop_view),
        migrations.CreateModel(
            name="ArchivioFisicoListaStampa",
            fields=[
                ("node_key", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("unit_id", models.BigIntegerField()),
                ("unit_parent_id", models.BigIntegerField(blank=True, null=True)),
                ("unit_codice", models.CharField(max_length=60)),
                ("unit_nome", models.CharField(max_length=120)),
                ("unit_tipo", models.CharField(max_length=20)),
                ("unit_attivo", models.BooleanField()),
                ("unit_archivio_fisso", models.BooleanField()),
                ("unit_full_path", models.CharField(max_length=500)),
                ("unit_progressivo", models.CharField(max_length=300)),
                ("node_type", models.CharField(max_length=20)),
                ("node_id", models.BigIntegerField()),
                ("node_label", models.CharField(max_length=255)),
                ("parent_node_type", models.CharField(blank=True, max_length=20, null=True)),
                ("parent_node_id", models.BigIntegerField(blank=True, null=True)),
                ("level", models.IntegerField()),
                ("tree_sort_key", models.TextField()),
                ("tree_path", models.TextField()),
                ("codice", models.CharField(blank=True, max_length=120, null=True)),
                ("titolo", models.CharField(blank=True, max_length=255, null=True)),
                ("descrizione", models.CharField(blank=True, max_length=255, null=True)),
                ("anno", models.IntegerField(blank=True, null=True)),
                ("data_documento", models.DateField(blank=True, null=True)),
                ("cliente_label", models.CharField(blank=True, max_length=255, null=True)),
                ("protocollo_anno", models.IntegerField(blank=True, null=True)),
                ("protocollo_numero", models.IntegerField(blank=True, null=True)),
                ("protocollo_direzione", models.CharField(blank=True, max_length=3, null=True)),
                ("protocollo_data", models.DateField(blank=True, null=True)),
                ("digitale", models.BooleanField(blank=True, null=True)),
                ("tracciabile", models.BooleanField(blank=True, null=True)),
                ("fascicolo_parent_id", models.BigIntegerField(blank=True, null=True)),
                ("documento_fascicolo_id", models.BigIntegerField(blank=True, null=True)),
            ],
            options={
                "db_table": VIEW_NAME,
                "managed": False,
                "ordering": ["unit_full_path", "tree_sort_key", "node_key"],
            },
        ),
    ]
