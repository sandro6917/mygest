from __future__ import annotations

from django.db import migrations


def _offset_in_minutes(unita: str, valore: int) -> int:
    mapping = {
        "min": 1,
        "h": 60,
        "d": 60 * 24,
        "w": 60 * 24 * 7,
    }
    return valore * mapping.get(unita, 1)


def forwards(apps, schema_editor):  # pragma: no cover - eseguito via migrate
    OldScadenza = apps.get_model("pratiche", "Scadenza")
    OldScadenzaAlert = apps.get_model("pratiche", "ScadenzaAlert")
    NewScadenza = apps.get_model("scadenze", "Scadenza")
    NewOccorrenza = apps.get_model("scadenze", "ScadenzaOccorrenza")

    for old in OldScadenza.objects.select_related("pratica").all():
        stato = "completata" if old.completata else "attiva"
        new_scad = NewScadenza.objects.create(
            id=old.id,
            titolo=old.titolo or "Scadenza migrata",
            descrizione=old.descrizione or "",
            stato=stato,
            priorita="medium",
            comunicazione_destinatari=old.alert_email_to or "",
        )
        if old.pratica_id:
            new_scad.pratiche.add(old.pratica_id)
        # Copia timestamps
        NewScadenza.objects.filter(pk=new_scad.pk).update(
            creato_il=old.creato_il,
            aggiornato_il=old.aggiornato_il,
        )

        alert_config = {}
        if old.alert_method == "email" and old.alert_email_to:
            alert_config = {"destinatari": old.alert_email_to}
        elif old.alert_method == "webhook" and old.alert_webhook_url:
            alert_config = {"url": old.alert_webhook_url}

        occ = NewOccorrenza.objects.create(
            scadenza=new_scad,
            titolo=old.titolo or "Scadenza migrata",
            descrizione=old.descrizione or "",
            inizio=old.scadenza_at,
            metodo_alert=old.alert_method or "email",
            offset_alert_minuti=old.alert_offset_min,
            alert_config=alert_config,
            alert_programmata_il=old.alert_at,
            alert_inviata_il=old.alert_inviato_il,
            stato="alerted" if old.alert_inviato_il else ("completed" if old.completata else "pending"),
        )
        NewOccorrenza.objects.filter(pk=occ.pk).update(
            creato_il=old.creato_il,
            aggiornato_il=old.aggiornato_il,
        )

        extra_alerts = OldScadenzaAlert.objects.filter(scadenza_id=old.id, attivo=True)
        for alert in extra_alerts.iterator():
            extra_config = {}
            if alert.metodo == "email" and alert.email_to:
                extra_config = {"destinatari": alert.email_to}
            elif alert.metodo == "webhook" and alert.webhook_url:
                extra_config = {"url": alert.webhook_url}
            offset_min = _offset_in_minutes(alert.unita, alert.valore)
            occ_extra = NewOccorrenza.objects.create(
                scadenza=new_scad,
                titolo=(old.titolo or "Scadenza migrata") + " (alert)",
                descrizione=old.descrizione or "",
                inizio=old.scadenza_at,
                metodo_alert=alert.metodo or "email",
                offset_alert_minuti=offset_min,
                alert_config=extra_config,
                alert_programmata_il=alert.alert_at,
                alert_inviata_il=alert.inviato_il,
                stato="alerted" if alert.inviato_il else "scheduled",
            )
            NewOccorrenza.objects.filter(pk=occ_extra.pk).update(
                creato_il=alert.creato_il,
                aggiornato_il=alert.aggiornato_il,
            )


def backwards(apps, schema_editor):  # pragma: no cover
    NewScadenza = apps.get_model("scadenze", "Scadenza")
    NewScadenza.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("scadenze", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
