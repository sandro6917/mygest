from __future__ import annotations

import graphene
from graphene_django import DjangoObjectType

from comunicazioni.models import Comunicazione, EmailImport
from anagrafiche.models import EmailContatto, MailingList
from comunicazioni.api.serializers import ComunicazioneSerializer


class EmailContattoType(DjangoObjectType):
    class Meta:
        model = EmailContatto
        fields = ("id", "email", "nominativo", "tipo", "is_preferito", "attivo", "anagrafica")


class MailingListType(DjangoObjectType):
    contatti_count = graphene.Int()

    class Meta:
        model = MailingList
        fields = ("id", "nome", "slug", "descrizione", "proprietario", "attiva", "contatti")

    def resolve_contatti_count(self, info):
        return self.contatti.count()


class EmailImportType(DjangoObjectType):
    class Meta:
        model = EmailImport
        fields = ("id", "mailbox", "message_id", "mittente", "destinatari", "oggetto", "data_messaggio", "importato_il", "comunicazione")


class ComunicazioneType(DjangoObjectType):
    destinatari_calcolati = graphene.List(graphene.String)
    protocollo_label = graphene.String()

    class Meta:
        model = Comunicazione
        fields = (
            "id",
            "tipo",
            "direzione",
            "oggetto",
            "corpo",
            "mittente",
            "destinatari",
            "contatti_destinatari",
            "liste_destinatari",
            "stato",
            "data_creazione",
            "data_invio",
            "documento_protocollo",
            "protocollo_movimento",
            "email_message_id",
            "importato_il",
            "import_source",
        )

    def resolve_destinatari_calcolati(self, info):
        return self.get_destinatari_lista()

    def resolve_protocollo_label(self, info):
        return self.protocollo_label


class ComunicazioneInput(graphene.InputObjectType):
    tipo = graphene.String(required=True)
    direzione = graphene.String(required=True)
    oggetto = graphene.String(required=True)
    corpo = graphene.String()
    mittente = graphene.String()
    destinatari = graphene.String()
    contatti_destinatari = graphene.List(graphene.Int)
    liste_destinatari = graphene.List(graphene.Int)
    documento_protocollo = graphene.Int()


class CreateComunicazione(graphene.Mutation):
    class Arguments:
        input = ComunicazioneInput(required=True)

    comunicazione = graphene.Field(ComunicazioneType)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, input):
        serializer = ComunicazioneSerializer(data=input)
        if serializer.is_valid():
            comunicazione = serializer.save()
            return CreateComunicazione(comunicazione=comunicazione, errors=[])
        errors: list[str] = []
        for field, msgs in serializer.errors.items():
            for msg in msgs:
                errors.append(f"{field}: {msg}")
        return CreateComunicazione(errors=errors)


class UpdateComunicazione(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = ComunicazioneInput(required=True)

    comunicazione = graphene.Field(ComunicazioneType)
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, info, id, input):
        try:
            instance = Comunicazione.objects.get(pk=id)
        except Comunicazione.DoesNotExist:
            return UpdateComunicazione(errors=["Comunicazione non trovata."])
        serializer = ComunicazioneSerializer(instance, data=input, partial=True)
        if serializer.is_valid():
            comunicazione = serializer.save()
            return UpdateComunicazione(comunicazione=comunicazione, errors=[])
        errors: list[str] = []
        for field, msgs in serializer.errors.items():
            for msg in msgs:
                errors.append(f"{field}: {msg}")
        return UpdateComunicazione(errors=errors)


class Query(graphene.ObjectType):
    comunicazione = graphene.Field(ComunicazioneType, id=graphene.ID(required=True))
    tutte_le_comunicazioni = graphene.List(ComunicazioneType)
    contatti = graphene.List(EmailContattoType)
    mailing_list = graphene.List(MailingListType)
    email_importate = graphene.List(EmailImportType)

    def resolve_comunicazione(self, info, id):
        try:
            return (
                Comunicazione.objects.select_related()
                .prefetch_related("contatti_destinatari", "liste_destinatari")
                .get(pk=id)
            )
        except Comunicazione.DoesNotExist:
            return None

    def resolve_tutte_le_comunicazioni(self, info):
        return Comunicazione.objects.select_related().prefetch_related("contatti_destinatari", "liste_destinatari").all()

    def resolve_contatti(self, info):
        return EmailContatto.objects.filter(attivo=True)

    def resolve_mailing_list(self, info):
        return MailingList.objects.filter(attiva=True)

    def resolve_email_importate(self, info):
        return EmailImport.objects.select_related("mailbox", "comunicazione").all()


class Mutation(graphene.ObjectType):
    crea_comunicazione = CreateComunicazione.Field()
    aggiorna_comunicazione = UpdateComunicazione.Field()
