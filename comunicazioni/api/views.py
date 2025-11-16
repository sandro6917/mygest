from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from comunicazioni.api.serializers import (
    ComunicazioneSerializer,
    EmailContattoSerializer,
    MailingListSerializer,
    EmailImportSerializer,
    TemplateContextFieldSerializer,
)
from comunicazioni.models import Comunicazione, EmailImport
from comunicazioni.models_template import TemplateContextField
from anagrafiche.models import EmailContatto, MailingList


class ComunicazioneViewSet(viewsets.ModelViewSet):
    queryset = (
        Comunicazione.objects.select_related("anagrafica", "documento_protocollo", "protocollo_movimento")
        .prefetch_related("contatti_destinatari", "liste_destinatari")
        .all()
    )
    serializer_class = ComunicazioneSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["direzione", "stato", "tipo", "anagrafica"]
    search_fields = ["oggetto", "corpo", "mittente", "destinatari"]
    ordering_fields = ["data_creazione", "data_invio"]
    ordering = ["-data_creazione"]


class EmailContattoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = EmailContatto.objects.filter(attivo=True).select_related("anagrafica")
    serializer_class = EmailContattoSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["email", "nominativo", "anagrafica__ragione_sociale", "anagrafica__cognome", "anagrafica__nome"]
    ordering_fields = ["nominativo", "email"]
    ordering = ["nominativo"]


class MailingListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = MailingList.objects.filter(attiva=True).select_related("proprietario")
    serializer_class = MailingListSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["nome", "slug"]
    ordering_fields = ["nome"]
    ordering = ["nome"]


class EmailImportViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = EmailImport.objects.select_related("mailbox", "comunicazione")
    serializer_class = EmailImportSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["oggetto", "mittente", "destinatari", "message_id"]
    ordering_fields = ["importato_il", "data_messaggio"]
    ordering = ["-importato_il"]


class TemplateContextFieldViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TemplateContextFieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = TemplateContextField.objects.filter(active=True).order_by("ordering", "id")
        template_id = self.request.query_params.get("template")
        if template_id:
            queryset = queryset.filter(template_id=template_id)
        return queryset.select_related("template")
