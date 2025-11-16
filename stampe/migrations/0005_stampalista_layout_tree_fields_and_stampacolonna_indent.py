from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stampe", "0004_stampalista_intestazione_font_size_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="stampalista",
            name="layout",
            field=models.CharField(
                choices=[("table", "Tabella"), ("tree", "Albero")],
                default="table",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="stampalista",
            name="tree_children_attr",
            field=models.CharField(
                blank=True,
                default="figli",
                help_text="Percorso attributo per accedere ai figli (es. 'figli' oppure 'children.all').",
                max_length=200,
            ),
        ),
        migrations.AddField(
            model_name="stampalista",
            name="tree_indent_mm",
            field=models.FloatField(
                default=6.0,
                help_text="Indentazione in millimetri per livello (solo layout albero).",
            ),
        ),
        migrations.AddField(
            model_name="stampalista",
            name="tree_max_depth",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Profondità massima dell'albero (0 = solo radici, lascia vuoto per nessun limite).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="stampalista",
            name="tree_order_by",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Ordine per radici e figli, es. ["ordine", "nome"]. Se vuoto usa order_by.',
            ),
        ),
        migrations.AddField(
            model_name="stampalista",
            name="tree_parent_field",
            field=models.CharField(
                blank=True,
                default="parent",
                help_text="Nome del campo FK al padre (usato per filtrare le radici con parent__isnull=True se non configurato diversamente).",
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name="stampalista",
            name="tree_root_filter",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Filtri specifici per le radici, es. {"parent__isnull": true}. Supporta placeholder :param.',
            ),
        ),
        migrations.AddField(
            model_name="stampalista",
            name="tree_roots",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text="Elenco di ID (o placeholder) da usare come nodi radice. Se valorizzato, prevale su tree_root_filter.",
            ),
        ),
        migrations.AddField(
            model_name="stampacolonna",
            name="indent_tree",
            field=models.BooleanField(
                default=False,
                help_text="Indenta il contenuto in base al livello del nodo (solo per layout albero).",
            ),
        ),
    ]
