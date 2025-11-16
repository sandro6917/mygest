from __future__ import annotations

from django.core.management.color import no_style
from django.db import migrations


def reset_sequences(apps, schema_editor):  # pragma: no cover - depends on DB state
    models = [
        apps.get_model("scadenze", "Scadenza"),
        apps.get_model("scadenze", "ScadenzaOccorrenza"),
        apps.get_model("scadenze", "ScadenzaNotificaLog"),
        apps.get_model("scadenze", "ScadenzaWebhookPayload"),
    ]
    connection = schema_editor.connection
    sql_statements = connection.ops.sequence_reset_sql(no_style(), models)
    if not sql_statements:
        return
    with connection.cursor() as cursor:
        for statement in sql_statements:
            cursor.execute(statement)


class Migration(migrations.Migration):

    dependencies = [
        ("scadenze", "0003_alter_scadenza_options_and_more"),
    ]

    operations = [
        migrations.RunPython(reset_sequences, migrations.RunPython.noop),
    ]
