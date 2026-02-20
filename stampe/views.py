from __future__ import annotations
from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.http import FileResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.urls import reverse
from . import registry
from .services import render_modulo_pdf, get_modulo_for_instance, get_lista_for, render_lista_pdf, build_queryset_for_list
from .layouts import layout_generic
from .decorators import login_required_or_jwt

@login_required_or_jwt
def etichetta_view(request, app_label: str, model: str, pk: int):
    normalized_model = model.lower()
    ct = get_object_or_404(ContentType, app_label=app_label, model=normalized_model)
    Model = ct.model_class()
    if not Model:
        raise Http404("Modello non trovato")
    obj = get_object_or_404(Model, pk=pk)

    slug = request.GET.get("module") or request.GET.get("modulo") or None
    modulo = get_modulo_for_instance(obj, slug)

    pdf = render_modulo_pdf(obj, modulo)
    filename = f"{modulo.slug}_{app_label}_{model}_{pk}.pdf"
    return FileResponse(BytesIO(pdf), filename=filename, content_type="application/pdf")

@login_required_or_jwt
def lista_view(request, app_label: str, model: str):
    normalized_model = model.lower()
    ct = ContentType.objects.get(app_label=app_label, model=normalized_model)
    lista_slug = request.GET.get("lista")
    lista = get_lista_for(ct, lista_slug)
    params = request.GET.dict()
    pratica = None
    pratica_id = request.GET.get("pratica_id")
    if pratica_id and app_label == "pratiche" and model == "pratica":
        from pratiche.models import Pratica
        pratica = Pratica.objects.filter(pk=pratica_id).first()
    pdf_bytes = render_lista_pdf(ct, lista, params, extra_context={"pratica": pratica})
    return FileResponse(BytesIO(pdf_bytes), content_type="application/pdf")

def _back_url(app_label: str, model: str, pk: int) -> str:
    candidates = [
        ("documenti", "modifica_dinamico"),
        ("fascicoli", "modifica"),
        ("pratiche", "modifica"),
    ]
    for app, name in candidates:
        if app == app_label:
            try:
                return reverse(f"{app}:{name}", args=[pk])
            except Exception:
                break
    return "/"


@login_required_or_jwt
def stampa_custom_view(request, slug: str):
    """
    Vista per stampe custom basate su slug del modulo.
    Esempi:
    - /etichette/stampa/ET_PROT_DOC/?movimento_id=123
    - /etichette/stampa/REG_PROTOCOLLO/?movimento_ids=1&movimento_ids=2&data_da=2026-01-01
    """
    from .models import StampaModulo, StampaLista
    from protocollo.models import MovimentoProtocollo
    
    # Prova a trovare un modulo di stampa con questo slug
    modulo = StampaModulo.objects.filter(slug=slug).first()
    if modulo:
        # Etichetta singola per movimento protocollo
        if slug == 'ET_PROT_DOC':
            movimento_id = request.GET.get('movimento_id')
            if not movimento_id:
                raise Http404("movimento_id richiesto")
            movimento = get_object_or_404(MovimentoProtocollo, pk=movimento_id)
            pdf = render_modulo_pdf(movimento, modulo)
            filename = f"etichetta_protocollo_{movimento_id}.pdf"
            return FileResponse(BytesIO(pdf), filename=filename, content_type="application/pdf")
    
    # Prova a trovare una lista di stampa con questo slug
    lista = StampaLista.objects.filter(slug=slug).first()
    if lista:
        # Registro protocollo (lista movimenti)
        if slug == 'REG_PROTOCOLLO':
            movimento_ids = request.GET.getlist('movimento_ids')
            if not movimento_ids:
                raise Http404("movimento_ids richiesto")
            
            # Prepara il context per la stampa
            params = request.GET.dict()
            data_da = request.GET.get('data_da')
            data_a = request.GET.get('data_a')
            
            # Aggiungi i movimento_ids ai params per il filtro
            params['id__in'] = movimento_ids
            
            extra_context = {
                'data_da': data_da,
                'data_a': data_a,
                'count': len(movimento_ids),
            }
            
            # Renderizza la lista PDF
            ct = ContentType.objects.get_for_model(MovimentoProtocollo)
            pdf_bytes = render_lista_pdf(ct, lista, params, extra_context=extra_context)
            filename = f"registro_protocollo_{len(movimento_ids)}_movimenti.pdf"
            return FileResponse(BytesIO(pdf_bytes), filename=filename, content_type="application/pdf")
    
    raise Http404(f"Modulo o lista '{slug}' non trovato")
