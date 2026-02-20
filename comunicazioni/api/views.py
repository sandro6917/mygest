from __future__ import annotations

from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend

from comunicazioni.api.serializers import (
    ComunicazioneSerializer,
    EmailContattoSerializer,
    MailingListSerializer,
    EmailImportSerializer,
    TemplateContextFieldSerializer,
    TemplateComunicazioneSerializer,
    FirmaComunicazioneSerializer,
    CodiceTributoF24Serializer,
    AllegatoComunicazioneSerializer,
)
from comunicazioni.models import Comunicazione, EmailImport, AllegatoComunicazione
from comunicazioni.models_template import TemplateContextField, TemplateComunicazione, FirmaComunicazione
from anagrafiche.models import EmailContatto, MailingList
from scadenze.models import CodiceTributoF24


class ComunicazioneViewSet(viewsets.ModelViewSet):
    queryset = (
        Comunicazione.objects.select_related("documento_protocollo", "protocollo_movimento")
        .prefetch_related("contatti_destinatari", "liste_destinatari")
        .all()
    )
    serializer_class = ComunicazioneSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["direzione", "stato", "tipo", "anagrafica"]
    search_fields = ["oggetto", "corpo", "mittente", "destinatari"]
    ordering_fields = ["data_creazione", "data_invio"]
    ordering = ["-data_creazione"]

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None):
        """
        Invia la comunicazione via email.
        
        POST /api/comunicazioni/{id}/send/
        """
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives, get_connection
        from django.utils.html import strip_tags
        from django.utils import timezone
        from smtplib import SMTPException, SMTPServerDisconnected
        import socket
        
        comunicazione = self.get_object()
        
        # Verifica che sia in stato bozza
        if comunicazione.stato != "bozza":
            return Response(
                {"error": "La comunicazione può essere inviata solo se è in stato bozza."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prepara l'email
        connection_kwargs = {}
        email_timeout = getattr(settings, "EMAIL_TIMEOUT", None)
        if email_timeout:
            connection_kwargs["timeout"] = email_timeout
        
        connection = get_connection(**connection_kwargs)
        corpo_testo = comunicazione.corpo or strip_tags(comunicazione.corpo_html or "")
        
        email = EmailMultiAlternatives(
            subject=comunicazione.oggetto,
            body=corpo_testo,
            from_email=comunicazione.mittente or settings.DEFAULT_FROM_EMAIL,
            to=comunicazione.get_destinatari_lista(),
            connection=connection,
        )
        
        if comunicazione.corpo_html:
            email.attach_alternative(comunicazione.corpo_html, "text/html")
        
        # Allegati - gestisce documento, fascicolo e file
        import os
        temp_files = []  # Track temporary files to clean up
        
        for allegato in comunicazione.allegati.all():
            try:
                file_path = allegato.get_file_path()
                filename = allegato.get_filename()
                
                if file_path and os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        email.attach(filename, f.read())
                    
                    # Se è un fascicolo (ZIP temporaneo), traccia per pulizia
                    if allegato.fascicolo and file_path.endswith('.zip'):
                        temp_files.append(file_path)
            except Exception as e:
                # Log error but continue with other attachments
                print(f"Errore allegato {allegato.id}: {e}")
                continue
        
        # Invio
        try:
            connection.open()
            connection.send_messages([email])
            
            # Archiviazione (opzionale)
            try:
                from comunicazioni.email_archiver import EmailAppendError, append_to_sent_folder
                append_to_sent_folder(email.message())
            except (EmailAppendError, ImportError):
                pass  # Non bloccare l'invio se l'archiviazione fallisce
            
            comunicazione.stato = "inviata"
            comunicazione.data_invio = timezone.now()
            comunicazione.save(update_fields=["stato", "data_invio"])
            
            serializer = self.get_serializer(comunicazione)
            return Response(serializer.data)
            
        except (ConnectionRefusedError, SMTPServerDisconnected, socket.timeout, OSError) as exc:
            # Fallback a console backend se configurato
            if getattr(settings, "EMAIL_FAILOVER_TO_CONSOLE", settings.DEBUG):
                try:
                    email.connection = get_connection("django.core.mail.backends.console.EmailBackend")
                    email.send()
                    comunicazione.stato = "inviata"
                    comunicazione.data_invio = timezone.now()
                    comunicazione.log_errore = f"Inviata via backend console: {type(exc).__name__} - {exc}"
                    comunicazione.save(update_fields=["stato", "data_invio", "log_errore"])
                    
                    serializer = self.get_serializer(comunicazione)
                    response_data = serializer.data
                    response_data['warning'] = (
                        "⚠️ Email non inviata realmente (server SMTP non raggiungibile). "
                        "L'email è stata stampata nel terminale del server. "
                        "Verifica la configurazione SMTP per invii reali."
                    )
                    return Response(response_data)
                except Exception:
                    pass
            
            comunicazione.stato = "errore"
            comunicazione.log_errore = str(exc)
            comunicazione.save(update_fields=["stato", "log_errore"])
            return Response(
                {"error": f"Errore nell'invio: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        except (SMTPException, Exception) as exc:
            comunicazione.stato = "errore"
            comunicazione.log_errore = str(exc)
            comunicazione.save(update_fields=["stato", "log_errore"])
            return Response(
                {"error": f"Errore nell'invio: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            # Pulizia file temporanei (ZIP fascicoli)
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except Exception:
                    pass

    @action(detail=True, methods=["post"])
    def rigenera(self, request, pk=None):
        """
        Rigenera il contenuto della comunicazione dal template originale.
        Ri-sostituisce tutti i placeholder con i valori aggiornati dal contesto.
        
        POST /api/comunicazioni/{id}/rigenera/
        
        ATTENZIONE: Questa operazione sovrascrive eventuali modifiche manuali
        al corpo e oggetto della comunicazione.
        """
        comunicazione = self.get_object()
        
        # Verifica che la comunicazione abbia un template
        if not comunicazione.template:
            return Response(
                {"error": "Questa comunicazione non è stata creata da un template."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verifica che la comunicazione non sia già stata inviata
        if comunicazione.stato == "inviata":
            return Response(
                {"error": "Non è possibile rigenerare una comunicazione già inviata."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Chiama render_content() per ri-sostituire i placeholder
            comunicazione.render_content()
            comunicazione.save(update_fields=['oggetto', 'corpo', 'corpo_html'])
            
            serializer = self.get_serializer(comunicazione)
            return Response({
                "message": "✅ Contenuto rigenerato dal template con successo",
                "data": serializer.data
            })
            
        except Exception as e:
            return Response(
                {"error": f"Errore durante la rigenerazione: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EmailContattoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = EmailContatto.objects.filter(attivo=True).select_related("anagrafica")
    serializer_class = EmailContattoSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["email", "nominativo", "anagrafica__ragione_sociale", "anagrafica__cognome", "anagrafica__nome"]
    ordering_fields = ["nominativo", "email"]
    ordering = ["nominativo"]


class MailingListViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = MailingList.objects.filter(attiva=True).select_related("proprietario")
    serializer_class = MailingListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
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


class TemplateComunicazioneViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = TemplateComunicazione.objects.filter(attivo=True).prefetch_related("context_fields")
    serializer_class = TemplateComunicazioneSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["nome", "oggetto"]
    ordering_fields = ["nome", "data_modifica"]
    ordering = ["nome"]

    @action(detail=True, methods=["post"])
    def render_preview(self, request, pk=None):
        """
        Renderizza un'anteprima del template con i valori forniti.
        
        POST /api/comunicazioni/templates/{id}/render_preview/
        Body: {
            "dati_template": {
                "primo_tributo_descrizione": "1",  // ID del codice tributo
                "primo_tributo_importo": "100.00",
                ...
            },
            "anagrafica_id": 123,  // opzionale
            ...
        }
        
        Response: {
            "oggetto": "...",
            "corpo_testo": "...",
            "corpo_html": "..."
        }
        """
        from comunicazioni.utils_template import render_template_comunicazione
        from comunicazioni.models import Comunicazione
        from anagrafiche.models import Anagrafica
        from django.utils import timezone
        
        template = self.get_object()
        dati_template = request.data.get("dati_template", {})
        
        # Costruisco il context processando i valori attraverso i context_fields
        context = {
            "user": request.user,
            "utente": request.user,
            "operatore": request.user,
            "oggi": timezone.now(),
        }
        
        # Aggiungo anagrafica se fornita
        anagrafica_id = request.data.get("anagrafica_id")
        if anagrafica_id:
            try:
                context["anagrafica"] = Anagrafica.objects.get(pk=anagrafica_id)
            except (Anagrafica.DoesNotExist, ValueError):
                pass
        
        # Processo i campi del template usando parse_raw_input per convertire gli ID
        for ctx_field in template.context_fields.filter(active=True):
            if ctx_field.key in dati_template:
                raw_value = dati_template[ctx_field.key]
                parsed_value = ctx_field.parse_raw_input(raw_value)
                if parsed_value is not None:
                    context[ctx_field.key] = parsed_value
        
        # Renderizza il template
        rendered = render_template_comunicazione(template, context)
        
        return Response({
            "oggetto": rendered.oggetto or "",
            "corpo_testo": rendered.corpo_testo or "",
            "corpo_html": rendered.corpo_html or "",
        })


class FirmaComunicazioneViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = FirmaComunicazione.objects.filter(attivo=True)
    serializer_class = FirmaComunicazioneSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["nome"]
    ordering = ["nome"]


class CodiceTributoF24ViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """API per i codici tributo F24 con autocomplete."""
    queryset = CodiceTributoF24.objects.filter(attivo=True)
    serializer_class = CodiceTributoF24Serializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ["codice", "descrizione", "causale"]
    filterset_fields = ["sezione"]
    ordering_fields = ["codice", "sezione"]
    ordering = ["sezione", "codice"]


class AllegatoComunicazioneViewSet(viewsets.ModelViewSet):
    """
    API per gestire gli allegati delle comunicazioni.
    Supporta documento, fascicolo e file upload.
    """
    from comunicazioni.models import AllegatoComunicazione
    from comunicazioni.api.serializers import AllegatoComunicazioneSerializer
    
    serializer_class = AllegatoComunicazioneSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from comunicazioni.models import AllegatoComunicazione
        comunicazione_id = self.kwargs.get('comunicazione_id')
        if comunicazione_id:
            return AllegatoComunicazione.objects.filter(
                comunicazione_id=comunicazione_id
            ).select_related('documento', 'fascicolo')
        return AllegatoComunicazione.objects.none()
    
    def perform_create(self, serializer):
        """Assegna automaticamente la comunicazione dall'URL"""
        from comunicazioni.models import Comunicazione
        comunicazione_id = self.kwargs.get('comunicazione_id')
        comunicazione = Comunicazione.objects.get(id=comunicazione_id)
        serializer.save(comunicazione=comunicazione)
