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

@login_required
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

@login_required
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
