import re
from collections import defaultdict
from django.db import migrations, models


def split_prefix_and_progress(code):
    if not code:
        return "", None
    code = code.strip()
    match = re.match(r"^(.*?)(\d+)$", code)
    if match and match.group(1):
        return match.group(1), int(match.group(2))
    return code, None


def assign_codes(apps, schema_editor):
    UnitaFisica = apps.get_model("archivio_fisico", "UnitaFisica")
    state = defaultdict(lambda: {"used": set(), "next": 1})

    for unita in UnitaFisica.objects.order_by("id"):
        original = unita.prefisso_codice or ""
        prefix, progress = split_prefix_and_progress(original)
        prefix = prefix.strip()
        if not prefix:
            prefix = f"UF{unita.pk}"

        bucket = state[prefix]
        used = bucket["used"]
        next_value = bucket["next"]

        if progress and progress not in used:
            assigned = progress
        else:
            assigned = next_value
            while assigned in used:
                assigned += 1

        used.add(assigned)
        bucket["used"] = used
        bucket["next"] = max(bucket.get("next", 1), assigned + 1)

        final_code = f"{prefix}{assigned}"
        parts = [final_code]
        if unita.nome:
            parts.append(unita.nome.strip())
        tipo_display = getattr(unita, "get_tipo_display", lambda: "")()
        if tipo_display:
            parts.append(tipo_display)
        progressivo_label = "-".join(parts)

        UnitaFisica.objects.filter(pk=unita.pk).update(
            prefisso_codice=prefix,
            progressivo_codice=assigned,
            codice=final_code,
            progressivo=progressivo_label,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("archivio_fisico", "0007_unitafisica_progressivo"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="unitafisica",
            name="uniq_unita_by_parent_codice",
        ),
        migrations.RenameField(
            model_name="unitafisica",
            old_name="codice",
            new_name="prefisso_codice",
        ),
        migrations.AlterField(
            model_name="unitafisica",
            name="prefisso_codice",
            field=models.SlugField(db_index=True, help_text="Prefisso utilizzato per il codice", max_length=50),
        ),
        migrations.AddField(
            model_name="unitafisica",
            name="progressivo_codice",
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name="unitafisica",
            name="codice",
            field=models.CharField(blank=True, default="", editable=False, max_length=60),
        ),
        migrations.AddConstraint(
            model_name="unitafisica",
            constraint=models.UniqueConstraint(fields=("parent", "prefisso_codice", "progressivo_codice"), name="uniq_unita_by_parent_prefisso_progressivo"),
        ),
        migrations.RunPython(assign_codes, reverse_code=noop),
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS archivio_fisico_unitafisica_codice_f3252776_like;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name="unitafisica",
            name="codice",
            field=models.CharField(editable=False, max_length=60, unique=True),
        ),
    ]
