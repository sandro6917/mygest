"""Views per l'app comunicazioni."""

from __future__ import annotations

import socket
from smtplib import SMTPException, SMTPServerDisconnected

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import Q
from django.forms.utils import ErrorDict, ErrorList
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST, require_http_methods, require_GET

from anagrafiche.models import Anagrafica, EmailContatto, MailingList

from .email_archiver import EmailAppendError, append_to_sent_folder
from .forms import ComunicazioneForm, AllegatoComunicazioneForm
from .models import Comunicazione, AllegatoComunicazione
from .models_template import FirmaComunicazione, TemplateComunicazione
from .services import protocolla_comunicazione as protocolla_comunicazione_service
from .utils_template import merge_contenuti, render_firma_comunicazione, render_template_comunicazione
from protocollo.forms import ProtocolloForm


def _build_detail_context(comunicazione: Comunicazione, allegato_form=None) -> dict:
    return {
        "comunicazione": comunicazione,
        "edit_url": comunicazione.get_update_url(),
        "send_url": comunicazione.get_send_url(),
        "back_url": reverse("comunicazioni:home"),
        "allegato_form": allegato_form or AllegatoComunicazioneForm(),
        "allegato_add_url": reverse("comunicazioni:attachments-add", args=[comunicazione.pk]),
        "protocolla_url": reverse("comunicazioni:protocolla", args=[comunicazione.pk]) if comunicazione.can_protocolla else None,
        "protocollo_movimento": comunicazione.protocollo_movimento,
        "protocollo_label": comunicazione.protocollo_label,
        "contatti_destinatari": comunicazione.contatti_destinatari.select_related("anagrafica").all(),
        "liste_destinatari": comunicazione.liste_destinatari.prefetch_related("contatti", "indirizzi_extra").all(),
    }


def _build_template_context_from_data(
    data,
    request,
    instance: Comunicazione | None = None,
    template: TemplateComunicazione | None = None,
) -> dict:
    context: dict[str, object] = {
        "user": request.user,
        "utente": request.user,
        "operatore": request.user,
        "oggi": timezone.now(),
    }
    anagrafica_id = data.get("anagrafica") or (instance.anagrafica_id if instance else None)
    if anagrafica_id:
        try:
            context["anagrafica"] = Anagrafica.objects.get(pk=anagrafica_id)
        except (Anagrafica.DoesNotExist, ValueError):
            pass
    context["destinatari"] = data.get("destinatari") or ""
    context["oggetto"] = data.get("oggetto") or ""
    if instance is not None:
        context["comunicazione"] = instance
        if instance.template_id and not template:
            template = instance.template
    if template is not None:
        context_fields = template.context_fields.filter(active=True).order_by("ordering", "id")
        existing_data = instance.dati_template if instance else {}
        for ctx_field in context_fields:
            field_name = ComunicazioneForm.context_field_name(ctx_field.key)
            raw_value = data.get(field_name)
            value = ctx_field.parse_raw_input(raw_value)
            if value is None and existing_data:
                stored_raw = existing_data.get(ctx_field.key)
                value = ctx_field.coerce_value(stored_raw)
            if value is not None:
                context[ctx_field.key] = value
                continue
            if instance is not None:
                source_value = ctx_field.get_source_value(instance)
                if source_value is not None:
                    context.setdefault(ctx_field.key, source_value)
                    continue
            default_value = ctx_field.get_default_value()
            if default_value is not None:
                context.setdefault(ctx_field.key, default_value)
    return context


def _apply_template_to_data(data, request, instance: Comunicazione | None = None):
    errors: dict[str, str] = {}
    direzione = data.get("direzione") or (instance.direzione if instance else None)
    direzione = direzione or Comunicazione.Direzione.OUT
    if direzione != Comunicazione.Direzione.OUT:
        errors["direzione"] = "I template sono disponibili solo per comunicazioni in uscita."
        return data, errors

    template_id = data.get("template")
    if not template_id:
        errors["template"] = "Seleziona un template da applicare."
        return data, errors

    try:
        template = TemplateComunicazione.objects.get(pk=template_id, attivo=True)
    except (TemplateComunicazione.DoesNotExist, ValueError):
        errors["template"] = "Template non disponibile o disattivato."
        return data, errors

    firma = None
    firma_id = data.get("firma")
    if firma_id:
        try:
            firma = FirmaComunicazione.objects.get(pk=firma_id, attivo=True)
        except (FirmaComunicazione.DoesNotExist, ValueError):
            errors["firma"] = "Firma non disponibile o disattivata."
            firma = None
    if errors:
        return data, errors

    context = _build_template_context_from_data(data, request, instance, template)
    contenuto = render_template_comunicazione(template, context, comunicazione=instance)
    firma_renderizzata = render_firma_comunicazione(firma, context) if firma else None
    combinato = merge_contenuti(contenuto, firma_renderizzata)
    data["oggetto"] = combinato.oggetto or ""
    data["corpo"] = combinato.corpo_testo or ""
    data["corpo_html"] = combinato.corpo_html or ""
    return data, {}


def _build_form_with_template_application(request, instance: Comunicazione | None = None):
    data = request.POST.copy()
    data.pop("applica_template", None)
    if "corpo_html" not in data:
        data["corpo_html"] = ""
    data, errors = _apply_template_to_data(data, request, instance)
    form = ComunicazioneForm(data=data, instance=instance)
    error_dict = ErrorDict()
    for field, message in errors.items():
        error_dict[field] = ErrorList([message])
    form._errors = error_dict
    form.cleaned_data = {}
    return form, not errors


@login_required
def lista_comunicazioni(request):
    comunicazioni = (
        Comunicazione.objects.select_related("anagrafica", "documento_protocollo", "protocollo_movimento")
        .prefetch_related(
            "allegati__documento",
            "contatti_destinatari__anagrafica",
            "liste_destinatari__contatti",
            "liste_destinatari__indirizzi_extra",
        )
        .all()
    )
    context = {
        "comunicazioni": comunicazioni,
        "create_url": reverse("comunicazioni:create"),
    }
    return render(request, "comunicazioni/home.html", context)


@login_required
def crea_comunicazione(request):
    if request.method == "POST" and "applica_template" in request.POST:
        form, applied = _build_form_with_template_application(request)
        if applied:
            messages.info(request, "Template applicato al contenuto della comunicazione.")
        elif form.errors:
            messages.warning(request, "Impossibile applicare il template selezionato.")
    else:
        form = ComunicazioneForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            comunicazione = form.save()
            messages.success(request, "Comunicazione creata con successo.")
            return redirect(comunicazione.get_absolute_url())
    context = {
        "form": form,
        "cancel_url": reverse("comunicazioni:home"),
        "help_url": None,
    }
    return render(request, "comunicazioni/form.html", context)


@login_required
def modifica_comunicazione(request, pk):
    comunicazione = get_object_or_404(Comunicazione, pk=pk)
    if request.method == "POST" and "applica_template" in request.POST:
        form, applied = _build_form_with_template_application(request, instance=comunicazione)
        if applied:
            messages.info(request, "Template applicato al contenuto della comunicazione.")
        elif form.errors:
            messages.warning(request, "Impossibile applicare il template selezionato.")
    else:
        form = ComunicazioneForm(request.POST or None, instance=comunicazione)
        if request.method == "POST" and form.is_valid():
            comunicazione = form.save()
            messages.success(request, "Comunicazione aggiornata con successo.")
            return redirect(comunicazione.get_absolute_url())
    context = {
        "form": form,
        "cancel_url": comunicazione.get_absolute_url(),
        "help_url": None,
    }
    return render(request, "comunicazioni/form.html", context)


@login_required
def dettaglio_comunicazione(request, pk):
    comunicazione = get_object_or_404(
        Comunicazione.objects.select_related("anagrafica", "documento_protocollo", "protocollo_movimento")
        .prefetch_related(
            "allegati__documento",
            "contatti_destinatari__anagrafica",
            "liste_destinatari__contatti",
            "liste_destinatari__indirizzi_extra",
        ),
        pk=pk,
    )
    return render(request, "comunicazioni/detail.html", _build_detail_context(comunicazione))


@login_required
@require_POST
def aggiungi_allegato(request, pk):
    comunicazione = get_object_or_404(
        Comunicazione.objects.select_related("anagrafica", "documento_protocollo", "protocollo_movimento")
        .prefetch_related(
            "allegati__documento",
            "contatti_destinatari__anagrafica",
            "liste_destinatari__contatti",
            "liste_destinatari__indirizzi_extra",
        ),
        pk=pk,
    )
    form = AllegatoComunicazioneForm(request.POST)
    if form.is_valid():
        documento = form.cleaned_data["documento"]
        allegato, created = AllegatoComunicazione.objects.get_or_create(
            comunicazione=comunicazione,
            documento=documento,
        )
        if created:
            messages.success(request, "Allegato aggiunto alla comunicazione.")
        else:
            messages.info(request, "Il documento è già presente tra gli allegati.")
        return redirect(comunicazione.get_absolute_url())
    messages.error(request, "Impossibile aggiungere l'allegato. Verifica i dati inseriti.")
    context = _build_detail_context(comunicazione, allegato_form=form)
    return render(request, "comunicazioni/detail.html", context)


@login_required
@require_POST
def rimuovi_allegato(request, pk, allegato_pk):
    comunicazione = get_object_or_404(Comunicazione, pk=pk)
    allegato = get_object_or_404(AllegatoComunicazione, pk=allegato_pk, comunicazione=comunicazione)
    allegato.delete()
    messages.success(request, "Allegato rimosso dalla comunicazione.")
    return redirect(comunicazione.get_absolute_url())


@login_required
def invia_comunicazione(request, pk):
    comunicazione = get_object_or_404(
        Comunicazione.objects.select_related("anagrafica", "documento_protocollo", "protocollo_movimento")
        .prefetch_related(
            "allegati__documento",
            "contatti_destinatari__anagrafica",
            "liste_destinatari__contatti",
            "liste_destinatari__indirizzi_extra",
        ),
        pk=pk,
    )
    allegati = comunicazione.allegati.all()
    if request.method == "POST":
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
        for allegato in allegati:
            doc = allegato.documento
            if doc and getattr(doc, "file", None):
                doc.file.open("rb")
                try:
                    email.attach(doc.file.name.split("/")[-1], doc.file.read())
                finally:
                    doc.file.close()
        try:
            connection.open()
            connection.send_messages([email])
            try:
                append_to_sent_folder(email.message())
            except EmailAppendError as archive_exc:
                messages.warning(
                    request,
                    "Email inviata ma non archiviata nella posta inviata dell'account: %s" % archive_exc,
                )
            comunicazione.stato = "inviata"
            comunicazione.data_invio = timezone.now()
            comunicazione.save(update_fields=["stato", "data_invio"])
            messages.success(request, "Comunicazione inviata con successo.")
        except (ConnectionRefusedError, SMTPServerDisconnected, socket.timeout) as exc:
            if getattr(settings, "EMAIL_FAILOVER_TO_CONSOLE", settings.DEBUG):
                try:
                    email.connection = get_connection("django.core.mail.backends.console.EmailBackend")
                    email.send()
                    comunicazione.stato = "inviata"
                    comunicazione.data_invio = timezone.now()
                    comunicazione.save(update_fields=["stato", "data_invio"])
                    messages.warning(
                        request,
                        "Invio SMTP non disponibile: messaggio scritto sul backend console (vedi log del server).",
                    )
                    return redirect(comunicazione.get_absolute_url())
                except Exception as console_exc:
                    exc = console_exc
            comunicazione.stato = "errore"
            comunicazione.log_errore = str(exc)
            comunicazione.save(update_fields=["stato", "log_errore"])
            messages.error(request, f"Errore nell'invio: {exc}")
        except (SMTPException, OSError) as exc:
            comunicazione.stato = "errore"
            comunicazione.log_errore = str(exc)
            comunicazione.save(update_fields=["stato", "log_errore"])
            messages.error(request, f"Errore nell'invio: {exc}")
        except Exception as exc:
            comunicazione.stato = "errore"
            comunicazione.log_errore = str(exc)
            comunicazione.save(update_fields=["stato", "log_errore"])
            messages.error(request, f"Errore nell'invio: {exc}")
        finally:
            try:
                connection.close()
            except Exception:
                pass
        return redirect(comunicazione.get_absolute_url())
    return render(
        request,
        "comunicazioni/invia.html",
        {"comunicazione": comunicazione, "allegati": allegati, "back_url": comunicazione.get_absolute_url()},
    )


@login_required
@require_http_methods(["GET", "POST"])
def protocolla_comunicazione(request, pk):
    comunicazione = get_object_or_404(
        Comunicazione.objects.select_related("anagrafica", "documento_protocollo", "protocollo_movimento")
        .prefetch_related("allegati__documento"),
        pk=pk,
    )


@login_required
@require_GET
def autocomplete_contatti(request):
    query = (request.GET.get("q") or "").strip()
    qs = EmailContatto.objects.filter(attivo=True)
    if query:
        qs = qs.filter(Q(email__icontains=query) | Q(nominativo__icontains=query))
    results = [
        {
            "id": contact.pk,
            "text": f"{contact.nominativo or contact.email} <{contact.email}>",
        }
        for contact in qs.select_related("anagrafica")[:20]
    ]
    return JsonResponse({"results": results})


@login_required
@require_GET
def autocomplete_liste(request):
    query = (request.GET.get("q") or "").strip()
    qs = MailingList.objects.filter(attiva=True)
    if query:
        qs = qs.filter(Q(nome__icontains=query) | Q(slug__icontains=query))
    results = [
        {
            "id": lista.pk,
            "text": f"{lista.nome} ({lista.contatti.count()} contatti)",
        }
        for lista in qs[:20]
    ]
    return JsonResponse({"results": results})

    if comunicazione.is_protocollata:
        messages.info(request, "La comunicazione è già stata protocollata.")
        return redirect(comunicazione.get_absolute_url())

    if not comunicazione.documento_protocollo:
        messages.error(
            request,
            "Imposta prima il documento da protocollare nella comunicazione.",
        )
        return redirect(comunicazione.get_update_url())

    documento = comunicazione.documento_protocollo
    initial = {"direzione": comunicazione.direzione or "IN"}

    if request.method == "POST":
        data = request.POST.copy()
        data.setdefault("direzione", comunicazione.direzione or "IN")
        form = ProtocolloForm(data=data, target=documento)
        if form.is_valid():
            cd = form.cleaned_data
            destinatario = (cd.get("da_chi") if cd["direzione"] == "IN" else cd.get("a_chi")) or ""
            try:
                movimento = protocolla_comunicazione_service(
                    comunicazione,
                    direzione=cd["direzione"],
                    quando=cd["quando"],
                    operatore=request.user,
                    destinatario=destinatario,
                    ubicazione=cd.get("ubicazione"),
                    data_rientro_prevista=cd.get("data_rientro_prevista"),
                    causale=cd.get("causale") or comunicazione.oggetto,
                    note=cd.get("note") or "",
                )
                messages.success(
                    request,
                    f"Comunicazione protocollata con numero {movimento.anno}/{movimento.numero:06d}.",
                )
                return redirect(comunicazione.get_absolute_url())
            except ValidationError as exc:
                form.add_error(None, exc.message)
            except Exception as exc:
                messages.error(request, f"Errore nella protocollazione: {exc}")
    else:
        form = ProtocolloForm(initial=initial, target=documento)

    return render(
        request,
        "comunicazioni/protocolla.html",
        {
            "comunicazione": comunicazione,
            "documento": documento,
            "form": form,
            "cancel_url": comunicazione.get_absolute_url(),
        },
    )
