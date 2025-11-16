from __future__ import annotations

from rest_framework import serializers

from comunicazioni.models import Comunicazione, EmailImport
from comunicazioni.models_template import (
    FirmaComunicazione,
    TemplateComunicazione,
    TemplateContextField,
)
from anagrafiche.models import EmailContatto, MailingList


class EmailContattoSerializer(serializers.ModelSerializer):
    anagrafica_display = serializers.CharField(source="anagrafica.__str__", read_only=True)

    class Meta:
        model = EmailContatto
        fields = [
            "id",
            "email",
            "nominativo",
            "tipo",
            "is_preferito",
            "attivo",
            "anagrafica",
            "anagrafica_display",
        ]
        read_only_fields = ["is_preferito", "attivo"]


class MailingListSerializer(serializers.ModelSerializer):
    proprietario_display = serializers.CharField(source="proprietario.__str__", read_only=True)
    contatti_count = serializers.IntegerField(source="contatti.count", read_only=True)

    class Meta:
        model = MailingList
        fields = [
            "id",
            "nome",
            "slug",
            "descrizione",
            "attiva",
            "proprietario",
            "proprietario_display",
            "contatti_count",
        ]
        read_only_fields = ["slug", "attiva", "contatti_count"]


class TemplateContextFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateContextField
        fields = [
            "id",
            "template",
            "key",
            "label",
            "field_type",
            "required",
            "help_text",
            "default_value",
            "choices",
            "source_path",
            "ordering",
            "active",
        ]
        read_only_fields = fields


class ComunicazioneSerializer(serializers.ModelSerializer):
    contatti_destinatari = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EmailContatto.objects.filter(attivo=True),
        required=False,
    )
    liste_destinatari = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MailingList.objects.filter(attiva=True),
        required=False,
    )
    template = serializers.PrimaryKeyRelatedField(
        queryset=TemplateComunicazione.objects.all(),
        required=False,
        allow_null=True,
    )
    firma = serializers.PrimaryKeyRelatedField(
        queryset=FirmaComunicazione.objects.all(),
        required=False,
        allow_null=True,
    )
    protocollo_label = serializers.CharField(read_only=True)
    destinatari_calcolati = serializers.SerializerMethodField()

    class Meta:
        model = Comunicazione
        fields = [
            "id",
            "tipo",
            "direzione",
            "oggetto",
            "corpo",
            "corpo_html",
            "mittente",
            "destinatari",
            "destinatari_calcolati",
            "anagrafica",
            "contatti_destinatari",
            "liste_destinatari",
            "template",
            "firma",
            "dati_template",
            "stato",
            "log_errore",
            "data_creazione",
            "data_invio",
            "documento_protocollo",
            "protocollo_movimento",
            "protocollo_label",
            "email_message_id",
            "importato_il",
            "import_source",
        ]
        read_only_fields = [
            "stato",
            "log_errore",
            "data_creazione",
            "data_invio",
            "protocollo_movimento",
            "protocollo_label",
            "email_message_id",
            "importato_il",
            "import_source",
        ]

    def get_destinatari_calcolati(self, obj: Comunicazione) -> list[str]:
        return obj.get_destinatari_lista()

    def create(self, validated_data):
        contatti = validated_data.pop("contatti_destinatari", [])
        liste = validated_data.pop("liste_destinatari", [])
        dati_template = validated_data.pop("dati_template", {})
        comunicazione = Comunicazione.objects.create(**validated_data)
        if dati_template:
            comunicazione.dati_template = dati_template
            comunicazione.save(update_fields=["dati_template"])
        if contatti:
            comunicazione.contatti_destinatari.set(contatti)
        if liste:
            comunicazione.liste_destinatari.set(liste)
        comunicazione.sync_destinatari_testo()
        return comunicazione

    def update(self, instance, validated_data):
        contatti = validated_data.pop("contatti_destinatari", None)
        liste = validated_data.pop("liste_destinatari", None)
        dati_template = validated_data.pop("dati_template", None)
        if instance.is_protocollata:
            if "direzione" in validated_data and validated_data["direzione"] != instance.direzione:
                raise serializers.ValidationError("Impossibile modificare la direzione dopo la protocollazione.")
            if "documento_protocollo" in validated_data and validated_data["documento_protocollo"] != instance.documento_protocollo:
                raise serializers.ValidationError("Impossibile modificare il documento dopo la protocollazione.")
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if dati_template is not None:
            instance.dati_template = dati_template
            instance.save(update_fields=["dati_template"])
        if contatti is not None:
            instance.contatti_destinatari.set(contatti)
        if liste is not None:
            instance.liste_destinatari.set(liste)
        instance.sync_destinatari_testo()
        return instance


class EmailImportSerializer(serializers.ModelSerializer):
    comunicazione = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EmailImport
        fields = [
            "id",
            "mailbox",
            "uid",
            "message_id",
            "mittente",
            "destinatari",
            "oggetto",
            "data_messaggio",
            "importato_il",
            "comunicazione",
        ]
        read_only_fields = fields
