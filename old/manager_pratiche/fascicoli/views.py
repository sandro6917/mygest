from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.decorators import login_required  # <-- AGGIUNTO
from .models import Fascicolo
from .forms import FascicoloForm, ProtocolloFascicoloForm
from django.db.utils import OperationalError

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
    for name in (f"{app}:{model}_detail", f"{app}:{model}-detail", f"{app}:dettaglio", f"{app}:detail"):
        try:
            return reverse(name, args=[obj.pk])
        except NoReverseMatch:
            pass
    if hasattr(obj, "get_absolute_url"):
        try:
            return obj.get_absolute_url()
        except Exception:
            pass
    try:
        return reverse(f"admin:{app}_{model}_change", args=[obj.pk])
    except NoReverseMatch:
        return f"/admin/{app}/{model}/{obj.pk}/change/"

def _fascicolo_success_url(obj):
    # prova URL di dettaglio, altrimenti home
    for name in ("fascicoli:dettaglio", "fascicoli:detail", "fascicoli:fascicolo_detail"):
        try:
            return reverse(name, args=[obj.pk])
        except NoReverseMatch:
            continue
    if hasattr(obj, "get_absolute_url"):
        try:
            return obj.get_absolute_url()
        except Exception:
            pass
    return reverse("fascicoli:home")

@login_required
def fascicolo_nuovo(request):
    initial = request.GET.dict()  # consente precompilazione via querystring (es. ?tipo=1&cliente=3)
    if request.method == "POST":
        form = FascicoloForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Fascicolo creato (#{obj.pk}).")
            return redirect(_fascicolo_success_url(obj))
    else:
        form = FascicoloForm(initial=initial)
    return render(request, "fascicoli/form.html", {"form": form, "is_create": True})

@login_required
def fascicolo_modifica(request, pk: int):
    obj = get_object_or_404(Fascicolo, pk=pk)
    if request.method == "POST":
        form = FascicoloForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Fascicolo aggiornato.")
            return redirect(_fascicolo_success_url(obj))
    else:
        form = FascicoloForm(instance=obj)
    return render(request, "fascicoli/form.html", {"form": form, "obj": obj, "is_create": False})

@login_required
def fascicolo_protocolla(request, pk: int):
    obj = get_object_or_404(Fascicolo, pk=pk)
    if request.method == "POST":
        form = ProtocolloFascicoloForm(request.POST)
        if form.is_valid():
            obj.protocolla(form.cleaned_data["numero"], form.cleaned_data["data"])
            messages.success(request, "Fascicolo protocollato.")
            return redirect(_fascicolo_success_url(obj))
    else:
        form = ProtocolloFascicoloForm(
            initial={"numero": obj.protocollo_numero, "data": obj.protocollo_data}
        )
    return render(request, "fascicoli/protocolla.html", {"form": form, "obj": obj})

def home(request):
    q = (request.GET.get("q") or "").strip()
    try:
        qs_all = Fascicolo.objects.all()

        # Box 1: ultimi 10 (niente select_related per evitare join a tabelle mancanti)
        ultimi_qs = _order(qs_all)[:10]
        ultimi_fascicoli = [(f, _detail_url(f)) for f in ultimi_qs]

        # Box 2: ricerca
        field_names = {f.name for f in Fascicolo._meta.get_fields() if getattr(f, "concrete", False)}
        searchable = [f for f in ("codice", "titolo", "oggetto", "descrizione", "note") if f in field_names]
        filtrati_qs = qs_all
        if q and searchable:
            cond = Q()
            for f in searchable:
                cond |= Q(**{f + "__icontains": q})
            filtrati_qs = filtrati_qs.filter(cond)
        if "codice" in field_names:
            filtrati_qs = filtrati_qs.order_by("codice")
        elif "titolo" in field_names:
            filtrati_qs = filtrati_qs.order_by("titolo")
        else:
            filtrati_qs = filtrati_qs.order_by("id")
        fascicoli_filtrati = [(f, _detail_url(f)) for f in filtrati_qs[:25]]
        fascicoli_total = filtrati_qs.count() if q else qs_all.count()

        # Box 3: tipi recenti senza select_related
        tipo_field = next((n for n in ("tipo", "tipo_fascicolo", "tipologia") if n in field_names), None)
        ultimi_tipi = []
        if tipo_field:
            visti = set()
            for f in _order(qs_all)[:50]:
                t = getattr(f, tipo_field, None)
                tid = getattr(t, "pk", None)
                if t and tid and tid not in visti:
                    visti.add(tid)
                    ultimi_tipi.append(t)
                if len(ultimi_tipi) >= 5:
                    break

    except OperationalError:
        # DB non allineato: evita il 500
        ultimi_fascicoli = []
        fascicoli_filtrati = []
        fascicoli_total = 0
        ultimi_tipi = []

    return render(request, "fascicoli/home.html", {
        "q": q,
        "ultimi_fascicoli": ultimi_fascicoli,
        "fascicoli_filtrati": fascicoli_filtrati,
        "fascicoli_total": fascicoli_total,
        "ultimi_tipi": ultimi_tipi,
    })
