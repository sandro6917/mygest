import io
import logging
import mimetypes
import zipfile

from django.contrib import admin, messages
from django.db import models
from django.db.models.functions import Lower
from django.http import HttpResponse

from .models import (
    AllegatoComunicazione,
    Comunicazione,
    EmailImport,
    EmailImportBlacklist,
    Mailbox,
)
from .models_template import FirmaComunicazione, TemplateComunicazione, TemplateContextField
class TemplateContextFieldInline(admin.TabularInline):
    model = TemplateContextField
    extra = 0
    fields = (
        "ordering",
        "active",
        "key",
        "label",
        "field_type",
        "widget",
        "required",
        "default_value",
        "format_string",
        "choices",
        "source_path",
        "help_text",
    )
    ordering = ("ordering", "id")
    show_change_link = True

from .tasks import sincronizza_mailbox
from django.utils import timezone

logger = logging.getLogger(__name__)

@admin.register(Comunicazione)
class ComunicazioneAdmin(admin.ModelAdmin):
    list_display = (
        "oggetto",
        "tipo",
        "direzione",
        "data_creazione",
        "stato",
        "protocollo_display",
        "import_source",
    )
    search_fields = ("oggetto", "destinatari", "corpo", "protocollo_movimento__numero", "email_message_id")
    list_filter = ("tipo", "direzione", "stato", "data_creazione", "import_source")
    date_hierarchy = "data_creazione"
    autocomplete_fields = ("documento_protocollo",)
    readonly_fields = ("protocollo_movimento", "importato_il", "import_source", "email_message_id")
    filter_horizontal = ("contatti_destinatari", "liste_destinatari")

    def protocollo_display(self, obj):
        return obj.protocollo_label or "—"

    protocollo_display.short_description = "Protocollo"

@admin.register(AllegatoComunicazione)
class AllegatoComunicazioneAdmin(admin.ModelAdmin):
    list_display = ("comunicazione", "documento")
    search_fields = ("comunicazione__oggetto", "documento__codice")


@admin.register(Mailbox)
class MailboxAdmin(admin.ModelAdmin):
    list_display = ("nome", "host", "username", "cartella", "attiva", "ultima_lettura")
    list_filter = ("attiva",)
    search_fields = ("nome", "host", "username")
    actions = ("importa_email",)

    @admin.action(description="Importa nuove email dalle caselle selezionate")
    def importa_email(self, request, queryset):
        total_imported = 0
        for mailbox in queryset:
            try:
                total_imported += sincronizza_mailbox(mailbox)
            except Exception as exc:
                messages.error(request, f"Errore importando {mailbox.nome}: {exc}")
        if total_imported:
            messages.success(request, f"Importate {total_imported} nuove email.")
        else:
            messages.warning(request, "Nessuna nuova email trovata.")


@admin.register(EmailImport)
class EmailImportAdmin(admin.ModelAdmin):
    list_display = ("mailbox", "oggetto", "mittente", "importato_il", "comunicazione", "stato_import")
    list_filter = ("mailbox", "stato_import")
    search_fields = ("oggetto", "mittente", "destinatari", "message_id")
    autocomplete_fields = ("mailbox", "comunicazione")
    actions = (
        "elimina_comunicazioni_collegate",
        "aggiungi_mittenti_blacklist",
        "crea_comunicazione_ricevuta",
        "scarica_eml",
        "elimina_email_blacklist",
    )
    readonly_fields = (
        "mailbox",
        "uid",
        "message_id",
        "mittente",
        "destinatari",
        "oggetto",
        "data_messaggio",
        "raw_headers",
        "corpo_testo",
        "corpo_html",
        "importato_il",
        "raw_message",
        "comunicazione",
        "stato_import",
        "processato_il",
        "processato_da",
    )

    @admin.action(description="Elimina le comunicazioni collegate alle email selezionate")
    def elimina_comunicazioni_collegate(self, request, queryset):
        deleted = 0
        for email_import in queryset.select_related("comunicazione"):
            comunicazione = email_import.comunicazione
            if not comunicazione:
                continue
            try:
                comunicazione.delete()
                deleted += 1
            except Exception as exc:
                messages.error(request, f"Errore eliminando la comunicazione {comunicazione.pk}: {exc}")
        if deleted:
            messages.success(request, f"Eliminate {deleted} comunicazioni collegate.")
            logger.info("EmailImportAdmin: eliminate %s comunicazioni dalla selezione", deleted)
        else:
            messages.warning(request, "Nessuna comunicazione collegata trovata da eliminare.")

    @admin.action(description="Aggiungi i mittenti selezionati alla blacklist")
    def aggiungi_mittenti_blacklist(self, request, queryset):
        mittenti = {
            (email_import.mittente or "").strip().lower()
            for email_import in queryset
            if email_import.mittente
        }
        if not mittenti:
            messages.warning(request, "Nessun mittente valido trovato nelle email selezionate.")
            return

        existing = set(
            EmailImportBlacklist.objects.filter(email__in=mittenti).values_list("email", flat=True)
        )
        to_create = [
            EmailImportBlacklist(email=email, created_by=request.user)
            for email in mittenti
            if email not in existing
        ]
        EmailImportBlacklist.objects.bulk_create(to_create)
        created_count = len(to_create)
        if created_count:
            messages.success(request, f"Aggiunti {created_count} mittenti alla blacklist.")
            logger.info("EmailImportAdmin: aggiunti %s mittenti in blacklist", created_count)
        else:
            messages.info(request, "Tutti i mittenti selezionati erano già in blacklist.")
            logger.info("EmailImportAdmin: nessun nuovo mittente per blacklist")

    @admin.action(description="Elimina email con mittenti in blacklist")
    def elimina_email_blacklist(self, request, queryset):
        blacklist = {
            (email or "").strip().lower()
            for email in EmailImportBlacklist.objects.values_list("email", flat=True)
        }
        if not blacklist:
            messages.info(request, "Blacklist vuota: nessuna email eliminata.")
            return
        to_delete = queryset.annotate(mittente_lower=Lower("mittente")).filter(mittente_lower__in=blacklist)
        mittenti = list(
            to_delete.order_by().values_list("mittente", flat=True)
        )
        count = len(mittenti)
        deleted = to_delete.delete()[0]
        if deleted:
            msg = f"Eliminate {deleted} email con mittente in blacklist."
            messages.success(request, msg)
        else:
            msg = "Nessuna email eliminata perché nessuna selezione coincide con la blacklist."
            messages.info(request, msg)
        logger.info(
            "EmailImportAdmin: eliminate %s email (query count %s) per mittenti %s",
            deleted,
            count,
            ", ".join(sorted(set(mittenti))) or "--",
        )

    @admin.action(description="Scarica file .eml per le email selezionate")
    def scarica_eml(self, request, queryset):
        buffer = io.BytesIO()
        archive = zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED)
        added = 0
        for email_import in queryset:
            if not email_import.raw_message:
                logger.warning("EmailImport %s senza raw_message: esclusa dallo zip", email_import.pk)
                continue
            filename = self._build_eml_filename(email_import, added)
            archive.writestr(filename, email_import.raw_message)
            added += 1
        archive.close()
        if not added:
            messages.warning(request, "Nessuna email con raw_message disponibile tra le selezionate.")
            return None
        buffer.seek(0)
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(buffer.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="email_import_{timestamp}.zip"'
        logger.info("Scaricati %s EML da admin EmailImport", added)
        return response

    def _build_eml_filename(self, email_import, index):
        base = email_import.message_id or f"email-{email_import.pk}"
        base = base.strip().strip("<>") or f"email-{email_import.pk}"
        base = base.replace("/", "_").replace("\\", "_")
        return f"{base or 'email'}-{index + 1}.eml"

    @admin.action(description="Crea comunicazione in entrata dalle email selezionate")
    def crea_comunicazione_ricevuta(self, request, queryset):
        created = 0
        for email_import in queryset.select_related("mailbox").all():
            if email_import.comunicazione_id:
                logger.info(
                    "EmailImport %s già collegata a comunicazione %s, skip",
                    email_import.pk,
                    email_import.comunicazione_id,
                )
                continue
            raw = email_import.raw_message
            if not raw:
                logger.warning("EmailImport %s senza raw_message, impossibile creare comunicazione", email_import.pk)
                messages.error(request, f"Email {email_import.pk} non ha raw_message, skip")
                continue
            try:
                import email as _email
                from django.core.files.base import ContentFile

                msg = _email.message_from_bytes(raw)
                # Bodies
                text_body = ""
                html_body = ""
                for part in msg.walk():
                    ctype = (part.get_content_type() or "").lower()
                    disp = part.get_content_disposition()
                    if ctype == "text/plain" and not text_body and disp is None:
                        text_body = (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8", errors="replace")
                    if ctype == "text/html" and not html_body and disp is None:
                        html_body = (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8", errors="replace")

                comunicazione = Comunicazione.objects.create(
                    tipo=Comunicazione.TipoComunicazione.INFORMATIVA,
                    direzione=Comunicazione.Direzione.IN,
                    oggetto=email_import.oggetto or "(senza oggetto)",
                    corpo=text_body or html_body,
                    corpo_html=html_body,
                    mittente=email_import.mittente,
                    destinatari=email_import.destinatari,
                    stato="ricevuta",
                    email_message_id=email_import.message_id,
                    importato_il=email_import.importato_il,
                    import_source=email_import.mailbox.nome if email_import.mailbox else None,
                    bloccata=True,
                )

                # Allegati: crea AllegatoComunicazione.file per ogni attachment
                attachment_index = 1
                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    if part.get_content_disposition() != "attachment":
                        continue
                    filename = part.get_filename()
                    if not filename:
                        guessed_ext = mimetypes.guess_extension(part.get_content_type() or "") or ".bin"
                        filename = f"allegato-{attachment_index}{guessed_ext}"
                    attachment_index += 1
                    payload = part.get_payload(decode=True) or b""
                    allegato = AllegatoComunicazione(comunicazione=comunicazione, nome_file=filename)
                    allegato.file.save(filename, ContentFile(payload), save=True)
                    logger.debug(
                        "Salvato allegato %s (%s bytes) per comunicazione %s",
                        filename,
                        len(payload),
                        comunicazione.pk,
                    )

                email_import.comunicazione = comunicazione
                email_import.stato_import = "processato"
                email_import.processato_il = timezone.now()
                email_import.processato_da = request.user
                email_import.save(update_fields=["comunicazione", "stato_import", "processato_il", "processato_da"])
                logger.info(
                    "Creata comunicazione %s (message_id=%s) da EmailImport %s",
                    comunicazione.pk,
                    email_import.message_id,
                    email_import.pk,
                )
                created += 1
            except Exception as exc:
                logger.exception("Errore creando comunicazione da EmailImport %s", email_import.pk)
                messages.error(request, f"Errore creando comunicazione da email {email_import.pk}: {exc}")
                continue
        if created:
            messages.success(request, f"Create {created} comunicazioni da email selezionate.")
        else:
            messages.info(request, "Nessuna nuova comunicazione creata dalle email selezionate.")


@admin.register(EmailImportBlacklist)
class EmailImportBlacklistAdmin(admin.ModelAdmin):
    list_display = ("email", "created_at", "created_by")
    search_fields = ("email", "note")
    readonly_fields = ("created_at",)


@admin.register(TemplateComunicazione)
class TemplateComunicazioneAdmin(admin.ModelAdmin):
    list_display = ("nome", "attivo", "data_modifica")
    list_filter = ("attivo", "data_modifica")
    search_fields = ("nome", "oggetto", "corpo_testo", "corpo_html")
    ordering = ("-data_modifica",)
    readonly_fields = ("data_creazione", "data_modifica")
    inlines = [TemplateContextFieldInline]
    actions = ["duplica_template"]
    fieldsets = (
        (None, {"fields": ("nome", "attivo")} ),
        ("Contenuto", {"fields": ("oggetto", "corpo_testo", "corpo_html")} ),
        ("Tracciamento", {"fields": ("data_creazione", "data_modifica"), "classes": ("collapse",)} ),
    )
    formfield_overrides = {
        models.TextField: {
            "widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 10, "cols": 100}),
        }
    }

    @admin.action(description="Duplica template selezionati")
    def duplica_template(self, request, queryset):
        """
        Duplica i template selezionati includendo tutti i context_fields associati.
        """
        duplicati = 0
        for template in queryset:
            # Salva i context_fields prima di duplicare
            context_fields = list(template.context_fields.all())
            
            # Duplica il template
            template.pk = None
            template.id = None
            
            # Aggiungi "(copia)" al nome, gestendo eventuali duplicati multipli
            nome_base = template.nome
            if "(copia)" in nome_base:
                # Rimuovi eventuali "(copia X)" esistenti
                import re
                nome_base = re.sub(r'\s*\(copia\s*\d*\)\s*$', '', nome_base)
            
            # Trova un nome univoco
            counter = 1
            nuovo_nome = f"{nome_base} (copia)"
            while TemplateComunicazione.objects.filter(nome=nuovo_nome).exists():
                counter += 1
                nuovo_nome = f"{nome_base} (copia {counter})"
            
            template.nome = nuovo_nome
            template.save()
            
            # Duplica i context_fields
            for field in context_fields:
                field.pk = None
                field.id = None
                field.template = template
                field.save()
            
            duplicati += 1
        
        self.message_user(
            request,
            f"{duplicati} template duplicato/i con successo.",
            messages.SUCCESS
        )


@admin.register(FirmaComunicazione)
class FirmaComunicazioneAdmin(admin.ModelAdmin):
    list_display = ("nome", "attivo", "data_modifica")
    list_filter = ("attivo",)
    search_fields = ("nome", "corpo_testo", "corpo_html")
    ordering = ("nome",)
    readonly_fields = ("data_creazione", "data_modifica")
    fieldsets = (
        (None, {"fields": ("nome", "attivo")} ),
        ("Contenuto", {"fields": ("corpo_testo", "corpo_html")} ),
        ("Tracciamento", {"fields": ("data_creazione", "data_modifica"), "classes": ("collapse",)} ),
    )
    formfield_overrides = {
        models.TextField: {
            "widget": admin.widgets.AdminTextareaWidget(attrs={"rows": 8, "cols": 100}),
        }
    }
