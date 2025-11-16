from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Prefetch
from django.forms import inlineformset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from anagrafiche.models import Anagrafica, Cliente
from documenti.models import Documento
from fascicoli.models import Fascicolo
from protocollo.models import MovimentoProtocollo

from .forms import OperazioneArchivioForm, RigaOperazioneArchivioForm
from .models import (
    CollocazioneFisica,
    OperazioneArchivio,
    RigaOperazioneArchivio,
    UnitaFisica,
    VerbaleConsegnaTemplate,
)
from .pdf import render_etichette_unita
from .word_templates import render_verbale_consegna
from .services import process_operazione_archivio


def _extract_cliente_info(subject):
    cliente = None
    anagrafica = None
    if isinstance(subject, Cliente):
        cliente = subject
        anagrafica = getattr(subject, "anagrafica", None)
    elif isinstance(subject, Anagrafica):
        anagrafica = subject
    elif subject is not None:
        maybe_cliente = getattr(subject, "cliente", None)
        if isinstance(maybe_cliente, Cliente):
            cliente = maybe_cliente
            anagrafica = getattr(cliente, "anagrafica", None)
        else:
            maybe_anagrafica = getattr(subject, "anagrafica", None)
            if isinstance(maybe_anagrafica, Anagrafica):
                anagrafica = maybe_anagrafica

    label = None
    if cliente and hasattr(cliente, "denominazione"):
        label = cliente.denominazione
    elif anagrafica and hasattr(anagrafica, "display_name"):
        label = anagrafica.display_name()
    label = label or "Senza cliente"

    code = getattr(anagrafica, "codice", "") or ""
    url = anagrafica.get_absolute_url() if anagrafica and hasattr(anagrafica, "get_absolute_url") else None
    key = None
    if cliente and getattr(cliente, "pk", None) is not None:
        key = cliente.pk
    elif anagrafica and getattr(anagrafica, "pk", None) is not None:
        key = anagrafica.pk

    return cliente, anagrafica, key, label, code, url

# --- CRUD OperazioneArchivio ---
@login_required
def operazionearchivio_list(request):
    operazioni = OperazioneArchivio.objects.select_related("referente_interno", "referente_esterno").order_by("-data_ora")
    return render(request, "archivio_fisico/operazionearchivio_list.html", {"operazioni": operazioni})

@login_required
def operazionearchivio_detail(request, pk):
    operazione = get_object_or_404(
        OperazioneArchivio.objects.select_related(
            "referente_interno",
            "referente_esterno",
        ).prefetch_related(
            "righe__documento",
            "righe__fascicolo",
            "righe__movimento_protocollo",
            "righe__unita_fisica_sorgente",
            "righe__unita_fisica_destinazione",
        ),
        pk=pk,
    )
    templates = VerbaleConsegnaTemplate.objects.filter(attivo=True).order_by("-is_default", "nome")
    righe = list(operazione.righe.all())
    sorgenti_unita = []
    destinazioni_unita = []
    seen_sorgenti = set()
    seen_destinazioni = set()
    for riga in righe:
        sorgente = getattr(riga, "unita_fisica_sorgente", None)
        if sorgente and sorgente.pk not in seen_sorgenti:
            sorgenti_unita.append(sorgente)
            seen_sorgenti.add(sorgente.pk)
        destinazione = getattr(riga, "unita_fisica_destinazione", None)
        if destinazione and destinazione.pk not in seen_destinazioni:
            destinazioni_unita.append(destinazione)
            seen_destinazioni.add(destinazione.pk)
    context = {
        "operazione": operazione,
        "verbale_templates": templates,
        "righe": righe,
        "sorgenti_unita": sorgenti_unita,
        "destinazioni_unita": destinazioni_unita,
    }
    return render(request, "archivio_fisico/operazionearchivio_detail.html", context)

def _build_righe_form_kwargs(data, operazione_instance):
    tipo = data.get("tipo_operazione") or getattr(operazione_instance, "tipo_operazione", None)
    referente_id = data.get("referente_esterno")
    if isinstance(referente_id, str):
        referente_id = referente_id.strip() or None
    if referente_id is not None:
        try:
            referente_id = int(referente_id)
        except (TypeError, ValueError):
            referente_id = None
    if referente_id is None:
        referente_id = getattr(operazione_instance, "referente_esterno_id", None)
    return {
        "tipo_operazione": tipo,
        "referente_esterno_id": referente_id,
    }

@login_required
def operazionearchivio_create(request):
    RigaFormSet = inlineformset_factory(
        OperazioneArchivio,
        RigaOperazioneArchivio,
        form=RigaOperazioneArchivioForm,
        extra=1,
        can_delete=True,
    )
    operazione_instance = OperazioneArchivio(referente_interno=request.user)
    form_initial = {}
    riga_initial = []
    movimento_param = request.GET.get("movimento_protocollo")
    movimento_obj = None
    if movimento_param:
        try:
            movimento_obj = MovimentoProtocollo.objects.select_related("documento", "fascicolo").get(pk=movimento_param)
        except (MovimentoProtocollo.DoesNotExist, ValueError, TypeError):
            movimento_obj = None
    if movimento_obj:
        if movimento_obj.cliente_id:
            form_initial["referente_esterno"] = movimento_obj.cliente_id
            operazione_instance.referente_esterno_id = movimento_obj.cliente_id
        riga_data = {"movimento_protocollo": movimento_obj.pk}
        if movimento_obj.documento_id:
            riga_data["documento"] = movimento_obj.documento_id
        if movimento_obj.fascicolo_id:
            riga_data["fascicolo"] = movimento_obj.fascicolo_id
        riga_initial.append(riga_data)
    fascicolo = request.GET.get("fascicolo")
    if fascicolo:
        if riga_initial:
            riga_initial[0].setdefault("fascicolo", fascicolo)
        else:
            riga_initial.append({"fascicolo": fascicolo})
    documento = request.GET.get("documento")
    if documento:
        if riga_initial:
            riga_initial[0].setdefault("documento", documento)
        else:
            riga_initial.append({"documento": documento})

    data_source = request.POST if request.method == "POST" else request.GET
    form_kwargs = _build_righe_form_kwargs(data_source, operazione_instance)

    if request.method == "POST":
        form = OperazioneArchivioForm(request.POST, request.FILES, instance=operazione_instance)
        formset = RigaFormSet(request.POST, instance=operazione_instance, form_kwargs=form_kwargs)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    operazione = form.save()
                    formset.instance = operazione
                    formset.save()
                    process_operazione_archivio(operazione)
                return HttpResponseRedirect(
                    reverse("archivio_fisico:operazionearchivio_detail", args=[operazione.pk])
                )
            except ValidationError as exc:
                message = "\n".join(exc.messages) if hasattr(exc, "messages") else str(exc)
                form.add_error(None, message)
    else:
        form = OperazioneArchivioForm(instance=operazione_instance, initial=form_initial)
        formset = RigaFormSet(instance=operazione_instance, initial=riga_initial, form_kwargs=form_kwargs)
    return render(
        request,
        "archivio_fisico/operazionearchivio_form.html",
        {"form": form, "formset": formset},
    )

@login_required
def operazionearchivio_update(request, pk):
    operazione = get_object_or_404(OperazioneArchivio, pk=pk)
    RigaFormSet = inlineformset_factory(
        OperazioneArchivio,
        RigaOperazioneArchivio,
        form=RigaOperazioneArchivioForm,
        extra=0,
        can_delete=True,
    )
    data_source = request.POST if request.method == "POST" else request.GET
    form_kwargs = _build_righe_form_kwargs(data_source, operazione)

    if request.method == "POST":
        form = OperazioneArchivioForm(request.POST, request.FILES, instance=operazione)
        formset = RigaFormSet(request.POST, instance=operazione, form_kwargs=form_kwargs)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                    process_operazione_archivio(operazione)
                return HttpResponseRedirect(reverse("archivio_fisico:operazionearchivio_detail", args=[operazione.pk]))
            except ValidationError as exc:
                message = "\n".join(exc.messages) if hasattr(exc, "messages") else str(exc)
                form.add_error(None, message)
    else:
        form = OperazioneArchivioForm(instance=operazione)
        formset = RigaFormSet(instance=operazione, form_kwargs=form_kwargs)
    return render(request, "archivio_fisico/operazionearchivio_form.html", {"form": form, "formset": formset, "operazione": operazione})

@login_required
def operazionearchivio_delete(request, pk):
    operazione = get_object_or_404(OperazioneArchivio, pk=pk)
    if request.method == "POST":
        operazione.delete()
        return HttpResponseRedirect(reverse("archivio_fisico:operazionearchivio_list"))
    return render(request, "archivio_fisico/operazionearchivio_confirm_delete.html", {"operazione": operazione})


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _serialize_choice_list(choices, current_value):
    serialized = []
    value_str = "" if current_value in (None, "") else str(current_value)

    def _flatten(iterable):
        for choice_value, choice_label in iterable:
            if isinstance(choice_label, (list, tuple)):
                yield from _flatten(choice_label)
            else:
                yield choice_value, choice_label

    for option_value, option_label in _flatten(choices):
        option_value = "" if option_value in (None, "") else str(option_value)
        serialized.append(
            {
                "value": option_value,
                "label": str(option_label),
                "selected": option_value == value_str,
            }
        )
    return serialized


@login_required
def operazionearchivio_riga_options(request):
    if request.method != "GET":
        return JsonResponse({"error": "Metodo non supportato."}, status=405)

    operazione_id = request.GET.get("operazione")
    operazione_instance = None
    if operazione_id:
        operazione_instance = get_object_or_404(OperazioneArchivio, pk=operazione_id)
    else:
        operazione_instance = OperazioneArchivio(referente_interno=request.user)

    referente_esterno_raw = request.GET.get("referente_esterno")
    if referente_esterno_raw:
        ref_id = _to_int(referente_esterno_raw)
        if ref_id:
            operazione_instance.referente_esterno_id = ref_id

    data_source = request.GET
    form_kwargs = _build_righe_form_kwargs(data_source, operazione_instance)

    riga_instance = None
    riga_id = request.GET.get("riga")
    if riga_id:
        riga_instance = RigaOperazioneArchivio.objects.select_related(
            "documento",
            "documento__fascicolo",
            "documento__fascicolo__ubicazione",
            "fascicolo",
        ).filter(pk=riga_id).first()

    initial_fields = {}
    for name in (
        "documento",
        "fascicolo",
        "movimento_protocollo",
        "unita_fisica_sorgente",
        "unita_fisica_destinazione",
        "stato_precedente",
        "stato_successivo",
    ):
        value = request.GET.get(name)
        if value not in (None, ""):
            initial_fields[name] = value

    form = RigaOperazioneArchivioForm(
        data=None,
        initial=initial_fields,
        instance=riga_instance,
        tipo_operazione=form_kwargs.get("tipo_operazione"),
        referente_esterno_id=form_kwargs.get("referente_esterno_id"),
    )

    target_obj = form._resolve_target_object()
    tipo_operazione = form_kwargs.get("tipo_operazione") or ""
    preferred_movimento = form._resolve_preferred_movimento(target_obj)
    movimento = preferred_movimento
    if movimento is None:
        mov_value = form.initial.get("movimento_protocollo")
        mov_id = _to_int(mov_value)
        if mov_id:
            movimento = (
                MovimentoProtocollo.objects.select_related("ubicazione")
                .filter(pk=mov_id)
                .first()
            )

    stato_corrente = form._resolve_current_state(target_obj) or ""
    unita_scarico_default = form._resolve_unita_scarico_default()
    scarico_code = form._default_stato_scarico(target_obj)

    if tipo_operazione == "uscita" and scarico_code:
        stato_field = form.fields["stato_successivo"]
        label = next((lbl for val, lbl in stato_field.choices if val == scarico_code), scarico_code)
        stato_field.choices = [(scarico_code, label)]
        stato_field.required = True

    if movimento:
        form.fields["movimento_protocollo"].empty_label = None

    directives: dict[str, dict[str, str | bool]] = {}
    warnings: list[str] = []

    def _force_repr(value):
        if value in (None, ""):
            return ""
        if hasattr(value, "pk"):
            return str(value.pk)
        return str(value)

    def _set_directive(field: str, *, locked: bool | None = None, force=None):
        entry = directives.setdefault(field, {})
        if locked is not None:
            entry["locked"] = bool(locked)
        if force is not None:
            entry["forceValue"] = _force_repr(force)

    if tipo_operazione == "entrata":
        _set_directive("movimento_protocollo", locked=True, force=movimento)
        _set_directive("unita_fisica_sorgente", locked=True, force=None)
        destinazione = movimento.ubicazione if movimento and movimento.ubicazione_id else None
        if destinazione is None:
            warnings.append("Impossibile determinare l'unità di arrivo dal protocollo selezionato.")
        _set_directive("unita_fisica_destinazione", locked=True if destinazione else False, force=destinazione)
        _set_directive("stato_precedente", locked=True, force="")
    elif tipo_operazione == "uscita":
        _set_directive("movimento_protocollo", locked=True, force=movimento)
        sorgente = movimento.ubicazione if movimento and movimento.ubicazione_id else None
        if sorgente is None:
            warnings.append("Impossibile determinare l'unità di partenza dal protocollo selezionato.")
        _set_directive("unita_fisica_sorgente", locked=True if sorgente else False, force=sorgente)
        if unita_scarico_default is None:
            warnings.append("Configura l'unità di scarico predefinita per completare l'operazione di uscita.")
        _set_directive("unita_fisica_destinazione", locked=True if unita_scarico_default else False, force=unita_scarico_default)
        _set_directive("stato_precedente", locked=True, force=stato_corrente)
        _set_directive("stato_successivo", locked=True, force=scarico_code or "")
    elif tipo_operazione == "interna":
        _set_directive("movimento_protocollo", locked=True, force=movimento)
        sorgente = movimento.ubicazione if movimento and movimento.ubicazione_id else None
        if sorgente is None:
            warnings.append("Impossibile determinare l'unità di partenza dal protocollo selezionato.")
        _set_directive("unita_fisica_sorgente", locked=True if sorgente else False, force=sorgente)
        _set_directive("stato_precedente", locked=True, force=stato_corrente)

    metadata = {
        "tipo_operazione": tipo_operazione,
        "stato_corrente": stato_corrente,
    }
    if target_obj is not None:
        metadata["target"] = {
            "type": "documento" if isinstance(target_obj, Documento) else "fascicolo",
            "id": getattr(target_obj, "pk", None),
            "label": str(target_obj),
        }
    if movimento is not None:
        metadata["movimento_protocollo"] = {
            "id": movimento.pk,
            "label": str(movimento),
            "ubicazione_id": movimento.ubicazione_id,
        }
    if unita_scarico_default is not None:
        metadata["unita_scarico"] = {
            "id": unita_scarico_default.pk,
            "label": str(unita_scarico_default),
        }

    fields_payload = {}
    suggested = {}

    for field_name in (
        "documento",
        "fascicolo",
        "movimento_protocollo",
        "unita_fisica_sorgente",
        "unita_fisica_destinazione",
        "stato_precedente",
        "stato_successivo",
    ):
        if field_name not in form.fields:
            continue
        bound = form[field_name]
        value = bound.value()
        if isinstance(value, list):
            value = value[0] if value else ""
        payload = {
            "options": _serialize_choice_list(bound.field.widget.choices, value),
            "value": "" if value in (None, "") else str(value),
        }
        directive = directives.get(field_name)
        if directive:
            payload.update(directive)
        fields_payload[field_name] = payload
        suggested_value = form.initial.get(field_name)
        if suggested_value in (None, ""):
            suggested_value = bound.field.initial
        if suggested_value not in (None, ""):
            suggested[field_name] = str(suggested_value)

    return JsonResponse({
        "fields": fields_payload,
        "suggested": suggested,
        "directives": directives,
        "metadata": metadata,
        "messages": {
            "warnings": warnings,
        },
    })


@login_required
def operazionearchivio_verbale_docx(request, pk: int, template_slug: str | None = None) -> HttpResponse:
    qs_template = VerbaleConsegnaTemplate.objects.filter(attivo=True)
    selected_slug = template_slug or request.GET.get("template") or ""
    template = None
    if selected_slug:
        template = get_object_or_404(qs_template, slug=selected_slug)
    else:
        template = qs_template.filter(is_default=True).first() or qs_template.first()
    if not template:
        raise Http404("Nessun template verbale disponibile.")

    mov_qs = MovimentoProtocollo.objects.select_related("operatore", "ubicazione").order_by("data")
    righe_qs = RigaOperazioneArchivio.objects.select_related(
        "documento",
        "documento__tipo",
        "documento__cliente",
        "documento__fascicolo",
        "documento__fascicolo__cliente",
        "documento__fascicolo__cliente__anagrafica",
        "documento__fascicolo__titolario_voce",
        "documento__titolario_voce",
        "fascicolo",
        "fascicolo__cliente",
        "fascicolo__cliente__anagrafica",
        "fascicolo__titolario_voce",
        "fascicolo__ubicazione",
        "movimento_protocollo",
        "unita_fisica_sorgente",
        "unita_fisica_destinazione",
    ).prefetch_related(
        Prefetch("documento__movimenti", queryset=mov_qs, to_attr="prefetched_movimenti"),
        Prefetch("fascicolo__movimenti_protocollo", queryset=mov_qs, to_attr="prefetched_movimenti"),
    )

    operazione = get_object_or_404(
        OperazioneArchivio.objects.select_related(
            "referente_interno",
            "referente_esterno",
        ).prefetch_related(
            Prefetch("righe", queryset=righe_qs),
        ),
        pk=pk,
    )

    content, filename = render_verbale_consegna(template, operazione)
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

@login_required
def unita_list(request):
    radici = UnitaFisica.objects.filter(parent__isnull=True).order_by("ordine", "nome")

    documenti_in_archivio = Prefetch(
        "documenti",
        queryset=(
            Documento.objects.filter(fascicolo__stato=Fascicolo.Stato.CORRENTE)
            .select_related("cliente")
            .prefetch_related("collocazioni_fisiche__unita")
            .distinct()
        ),
        to_attr="documenti_corrente",
    )

    fascicoli_correnti = (
        Fascicolo.objects.filter(stato=Fascicolo.Stato.CORRENTE)
        .select_related("cliente__anagrafica", "ubicazione")
        .prefetch_related(documenti_in_archivio)
        .distinct()
    )

    documenti_sciolti = (
        Documento.objects.filter(fascicolo__isnull=True)
        .select_related("cliente")
        .prefetch_related("collocazioni_fisiche__unita")
        .distinct()
    )

    clienti_map = {}

    for fascicolo in fascicoli_correnti:
        cliente_obj, anagrafica, key, label, code, url = _extract_cliente_info(getattr(fascicolo, "cliente", None))
        entry = clienti_map.setdefault(
            key,
            {
                "anagrafica": anagrafica or cliente_obj,
                "cliente": cliente_obj,
                "label": label,
                "code": code,
                "url": url,
                "fascicoli": [],
                "documenti_sciolti": [],
                "documenti_count": 0,
            },
        )
        if anagrafica:
            entry["anagrafica"] = anagrafica
        if cliente_obj:
            entry["cliente"] = cliente_obj
        entry["label"] = label
        entry["code"] = code
        entry["url"] = url
        if not hasattr(fascicolo, "documenti_corrente"):
            fascicolo.documenti_corrente = []
        entry["fascicoli"].append(fascicolo)

    for documento in documenti_sciolti:
        cliente_obj, anagrafica, key, label, code, url = _extract_cliente_info(getattr(documento, "cliente", None))
        entry = clienti_map.setdefault(
            key,
            {
                "anagrafica": anagrafica or cliente_obj,
                "cliente": cliente_obj,
                "label": label,
                "code": code,
                "url": url,
                "fascicoli": [],
                "documenti_sciolti": [],
                "documenti_count": 0,
            },
        )
        if anagrafica:
            entry["anagrafica"] = anagrafica
        if cliente_obj:
            entry["cliente"] = cliente_obj
        entry["label"] = label
        entry["code"] = code
        entry["url"] = url
        entry["documenti_sciolti"].append(documento)

    def get_collocazioni_attive(documento):
        manager = getattr(documento, "collocazioni_fisiche", None)
        if manager is None:
            return []
        attive = []
        for collocazione in manager.all():
            if getattr(collocazione, "attiva", False) and getattr(collocazione, "unita_id", None):
                attive.append(collocazione)
        return attive

    clienti_tree = []
    for entry in clienti_map.values():
        entry["fascicoli"].sort(
            key=lambda f: ((f.codice or "").casefold(), (f.titolo or "").casefold())
        )
        entry["documenti_sciolti"].sort(
            key=lambda d: ((d.codice or "").casefold(), (d.descrizione or "").casefold())
        )
        for documento in entry["documenti_sciolti"]:
            documento.collocazioni_attive = get_collocazioni_attive(documento)
        doc_total = len(entry["documenti_sciolti"])
        for fascicolo in entry["fascicoli"]:
            docs = list(getattr(fascicolo, "documenti_corrente", []))
            for documento in docs:
                documento.collocazioni_attive = get_collocazioni_attive(documento)
            docs.sort(
                key=lambda d: ((d.codice or "").casefold(), (d.descrizione or "").casefold())
            )
            fascicolo.documenti_corrente = docs
            doc_total += len(docs)
        entry["documenti_count"] = doc_total
        clienti_tree.append(entry)

    clienti_tree.sort(key=lambda e: e["label"].casefold())

    return render(request, "archivio_fisico/unita_list.html", {"radici": radici, "clienti_tree": clienti_tree})


@login_required
def unita_inventory_tree(request):
    units = list(
        UnitaFisica.objects.filter(attivo=True)
        .select_related("parent")
        .order_by("parent__id", "ordine", "nome", "pk")
    )

    if not units:
        context = {
            "unita_tree": [],
            "generated_at": timezone.now(),
        }
        return render(request, "archivio_fisico/unita_inventory_tree.html", context)

    unit_nodes: dict[int, dict] = {}
    for unit in units:
        unit_nodes[unit.pk] = {
            "unit": unit,
            "children": [],
            "fascicoli_map": {},
            "documenti_sciolti": [],
            "documenti_seen": set(),
        }

    roots: list[dict] = []
    for unit in units:
        node = unit_nodes[unit.pk]
        parent_id = unit.parent_id
        if parent_id and parent_id in unit_nodes:
            unit_nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)

    collocazioni = list(
        CollocazioneFisica.objects.filter(attiva=True, unita_id__in=unit_nodes.keys())
        .select_related(
            "unita",
            "documento",
            "documento__cliente__anagrafica",
            "documento__fascicolo",
            "documento__titolario_voce",
        )
    )

    fascicolo_map: dict[int, Fascicolo] = {}
    if collocazioni:
        fascicolo_ct = ContentType.objects.get_for_model(Fascicolo)
        fascicolo_ct_id = fascicolo_ct.pk

        fascicolo_ids: set[int] = set()
        for coll in collocazioni:
            if coll.content_type_id == fascicolo_ct_id:
                fascicolo_ids.add(coll.object_id)
            documento = getattr(coll, "documento", None)
            fascicolo_id = getattr(documento, "fascicolo_id", None) if documento else None
            if fascicolo_id:
                fascicolo_ids.add(fascicolo_id)

        if fascicolo_ids:
            fascicolo_map = {
                f.pk: f
                for f in Fascicolo.objects.filter(pk__in=fascicolo_ids)
                .select_related("cliente__anagrafica", "titolario_voce", "parent")
            }

        for coll in collocazioni:
            node = unit_nodes.get(coll.unita_id)
            if not node:
                continue

            documento = getattr(coll, "documento", None)
            if documento and documento.pk:
                fascicolo_id = getattr(documento, "fascicolo_id", None)
                if fascicolo_id:
                    fascicolo = fascicolo_map.get(fascicolo_id) or getattr(documento, "fascicolo", None)
                    if not fascicolo:
                        continue
                    fascicolo_map.setdefault(fascicolo.pk, fascicolo)
                    fasc_entry = node["fascicoli_map"].setdefault(
                        fascicolo.pk,
                        {"fascicolo": fascicolo, "documenti": [], "documenti_seen": set()},
                    )
                    if documento.pk not in fasc_entry["documenti_seen"]:
                        fasc_entry["documenti_seen"].add(documento.pk)
                        fasc_entry["documenti"].append(documento)
                else:
                    if documento.pk in node["documenti_seen"]:
                        continue
                    node["documenti_seen"].add(documento.pk)
                    node["documenti_sciolti"].append(documento)
                continue

            if coll.content_type_id != fascicolo_ct_id:
                continue

            fascicolo = fascicolo_map.get(coll.object_id)
            if fascicolo is None:
                try:
                    candidate = coll.content_object
                except Fascicolo.DoesNotExist:  # pragma: no cover - safety guard
                    candidate = None
                else:
                    if not isinstance(candidate, Fascicolo):
                        candidate = None
                fascicolo = candidate
                if fascicolo:
                    fascicolo_map[fascicolo.pk] = fascicolo
            if fascicolo is None:
                continue

            node["fascicoli_map"].setdefault(
                fascicolo.pk,
                {"fascicolo": fascicolo, "documenti": [], "documenti_seen": set()},
            )

    def _unit_order_key(unit: UnitaFisica) -> tuple[str, str, str]:
        return (
            (unit.full_path or unit.codice or "").casefold(),
            (unit.nome or "").casefold(),
            (unit.codice or "").casefold(),
        )

    def _document_order_key(documento: Documento) -> tuple[str, str]:
        return (
            (documento.codice or "").casefold(),
            (documento.descrizione or "").casefold(),
        )

    for node in unit_nodes.values():
        node["documenti_sciolti"].sort(key=_document_order_key)

        fascicoli_list = []
        for fascicolo_data in node["fascicoli_map"].values():
            fascicolo_data["documenti"].sort(key=_document_order_key)
            fascicolo_data.pop("documenti_seen", None)
            fascicoli_list.append(fascicolo_data)

        fascicoli_list.sort(
            key=lambda item: (
                (item["fascicolo"].codice or "").casefold(),
                (item["fascicolo"].titolo or "").casefold(),
            )
        )

        node["fascicoli"] = fascicoli_list
        node.pop("fascicoli_map", None)
        node.pop("documenti_seen", None)
        node["children"].sort(key=lambda child: _unit_order_key(child["unit"]))

    roots.sort(key=lambda node: _unit_order_key(node["unit"]))

    context = {
        "unita_tree": roots,
        "generated_at": timezone.now(),
    }
    return render(request, "archivio_fisico/unita_inventory_tree.html", context)


@login_required
def unita_detail(request, pk: int):
    u = get_object_or_404(UnitaFisica.objects.select_related("parent"), pk=pk)
    figli = u.figli.all().order_by("ordine", "nome")
    collocazioni = (
        u.collocazioni.filter(attiva=True)
        .select_related("documento", "content_type")
        .order_by("documento__id", "object_id")
    )
    fascicoli = []
    documenti = []
    for collocazione in collocazioni:
        if collocazione.documento_id:
            documenti.append(collocazione.documento)
        else:
            obj = collocazione.content_object
            if not isinstance(obj, Fascicolo) or not getattr(obj, "pk", None):
                continue
            fascicoli.append(obj)
    return render(
        request,
        "archivio_fisico/unita_detail.html",
        {"u": u, "figli": figli, "fascicoli": fascicoli, "documenti": documenti},
    )

@login_required
def unita_etichette(request, pk: int) -> HttpResponse:
    unita = get_object_or_404(UnitaFisica.objects.select_related("parent"), pk=pk)
    base_url = request.build_absolute_uri("/").rstrip("/")
    return render_etichette_unita([unita], base_url=base_url)
