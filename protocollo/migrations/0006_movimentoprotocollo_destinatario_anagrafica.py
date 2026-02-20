from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("anagrafiche", "0007_alter_indirizzo_provincia_comuneitaliano_and_more"),
        ("protocollo", "0005_remove_movimentoprotocollo_chk_one_target_set_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="movimentoprotocollo",
            name="destinatario_anagrafica",
            field=models.ForeignKey(
                blank=True,
                help_text="Anagrafica collegata al destinatario/mittente.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="movimenti_protocollo_destinatario",
                to="anagrafiche.anagrafica",
            ),
        ),
    ]
