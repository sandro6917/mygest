from __future__ import annotations
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, NoReverseMatch

# Import corretti delle app top-level
from anagrafiche.models import Anagrafica
from documenti.models import Documento
from pratiche.models import Pratica
from fascicoli.models import Fascicolo

ORDER_CANDIDATES = ["updated_at", "modified", "updated", "data_modifica", "created_at", "created", "data"]

def _order(qs):
    for f in ORDER_CANDIDATES:
        try:
            qs.model._meta.get_field(f)
            return qs.order_by(f"-{f}")
        except Exception:
            continue
    return qs.order_by("-id")

def _detail_url(obj) -> str:
    app = obj._meta.app_label
    model = obj._meta.model_name
    candidates = [
        f"{app}:{model}_detail",
        f"{app}:{model}-detail",
        f"{app}:{model}_view",
        f"{app}:detail",
        f"{app}:dettaglio",
        f"{app}:documento_dettaglio",
    ]
    for name in candidates:
        try:
            return reverse(name, args=[obj.pk])
        except NoReverseMatch:
            continue
    if hasattr(obj, "get_absolute_url"):
        try:
            return obj.get_absolute_url()
        except Exception:
            pass
    try:
        return reverse(f"admin:{app}_{model}_change", args=[obj.pk])
    except NoReverseMatch:
        return f"/admin/{app}/{model}/{obj.pk}/change/"

def home(request):
    pratiche_qs = _order(Pratica.objects.all())[:10]
    documenti_qs = _order(Documento.objects.all())[:10]
    fascicoli_qs = _order(Fascicolo.objects.all())[:10]
    anagrafiche_qs = _order(Anagrafica.objects.all())[:10]

    ctx = {
        "pratiche": [(o, _detail_url(o)) for o in pratiche_qs],
        "documenti": [(o, _detail_url(o)) for o in documenti_qs],
        "fascicoli": [(o, _detail_url(o)) for o in fascicoli_qs],
        "anagrafiche": [(o, _detail_url(o)) for o in anagrafiche_qs],
    }
    return render(request, "home.html", ctx)

def anagrafica_detail(request, pk: int):
    obj = get_object_or_404(Anagrafica, pk=pk)

    # Ultime pratiche per l’anagrafica (tenta più campi comuni)
    pratiche_q = Q()
    for fk in ("cliente", "anagrafica", "intestatario"):
        pratiche_q |= Q(**{fk: obj})
    pratiche = list(_order(Pratica.objects.filter(pratiche_q)).select_related()[:10])

    # Ultimi fascicoli relativi (via pratica o FK diretta)
    fascicoli_q = Q(pratica__in=Pratica.objects.filter(pratiche_q))
    for fk in ("cliente", "anagrafica"):
        fascicoli_q |= Q(**{fk: obj})
    fascicoli = list(_order(Fascicolo.objects.filter(fascicoli_q)).select_related("pratica")[:10])

    # Ricerca documenti dell’anagrafica (+ filtro q)
    docs_base_q = Q()
    for fk in ("cliente", "anagrafica", "destinatario", "soggetto"):
        docs_base_q |= Q(**{fk: obj})
    q = (request.GET.get("q") or "").strip()
    docs = Documento.objects.filter(docs_base_q)
    if q:
        docs = docs.filter(
            Q(titolo__icontains=q) |
            Q(numero__icontains=q) |
            Q(descrizione__icontains=q) |
            Q(note__icontains=q) |
            Q(file__icontains=q) |
            Q(nome_file__icontains=q)
        )
    documenti = list(_order(docs).select_related()[:10])

    ctx = {
        "obj": obj,
        "pratiche": pratiche,
        "fascicoli": fascicoli,
        "documenti": documenti,
        "q": q,
    }
    return render(request, "anagrafiche/detail.html", ctx)