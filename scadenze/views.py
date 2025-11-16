from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from mygest.breadcrumbs import set_breadcrumbs

from .forms import (
    ScadenzaBulkOccurrencesForm,
    ScadenzaForm,
    ScadenzaOccorrenzaFormSet,
)
from .models import Scadenza, ScadenzaOccorrenza
from .services import AlertDispatcher


@login_required
def home(request):
    q = (request.GET.get("q") or "").strip()
    stato = (request.GET.get("stato") or "").strip()
    priorita = (request.GET.get("priorita") or "").strip()

    scadenze_qs = Scadenza.objects.prefetch_related("occorrenze", "pratiche", "assegnatari").order_by("titolo")
    if q:
        scadenze_qs = scadenze_qs.filter(Q(titolo__icontains=q) | Q(descrizione__icontains=q))
    if stato:
        scadenze_qs = scadenze_qs.filter(stato=stato)
    if priorita:
        scadenze_qs = scadenze_qs.filter(priorita=priorita)

    scadenze = scadenze_qs[:200]

    set_breadcrumbs(request, [("Scadenze", None)])
    context = {
        "scadenze": scadenze,
        "q": q,
        "stato": stato,
        "priorita": priorita,
        "stato_choices": Scadenza.Stato.choices,
        "priorita_choices": Scadenza.Priorita.choices,
    }
    return render(request, "scadenze/home.html", context)


@login_required
def detail(request, pk: int):
    scadenza = get_object_or_404(
        Scadenza.objects.prefetch_related(
            "pratiche",
            "fascicoli",
            "documenti",
            "occorrenze__log_eventi",
        ),
        pk=pk,
    )
    occorrenze = scadenza.occorrenze.all().order_by("inizio")

    crumbs = [
        ("Scadenze", reverse("scadenze:home")),
        (scadenza.titolo, None),
    ]
    set_breadcrumbs(request, crumbs)
    return render(
        request,
        "scadenze/detail.html",
        {
            "scadenza": scadenza,
            "occorrenze": occorrenze,
        },
    )


@login_required
def create(request):
    pratica_id = request.GET.get("pratica")
    initial = {}
    if pratica_id:
        initial["pratiche"] = [pratica_id]

    if request.method == "POST":
        form = ScadenzaForm(request.POST)
        formset = ScadenzaOccorrenzaFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            scadenza = form.save(commit=False)
            scadenza.creato_da = request.user
            scadenza.save()
            form.save_m2m()
            formset.instance = scadenza
            formset.save()
            messages.success(request, "Scadenza creata correttamente.")
            return redirect("scadenze:detail", scadenza.pk)
    else:
        form = ScadenzaForm(initial=initial)
        formset = ScadenzaOccorrenzaFormSet()
    set_breadcrumbs(request, [("Scadenze", reverse("scadenze:home")), ("Nuova", None)])
    return render(
        request,
        "scadenze/form.html",
        {
            "form": form,
            "formset": formset,
            "obj": None,
        },
    )


@login_required
def update(request, pk: int):
    scadenza = get_object_or_404(Scadenza, pk=pk)
    if request.method == "POST":
        form = ScadenzaForm(request.POST, instance=scadenza)
        formset = ScadenzaOccorrenzaFormSet(request.POST, instance=scadenza)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Scadenza aggiornata.")
            return redirect("scadenze:detail", scadenza.pk)
    else:
        form = ScadenzaForm(instance=scadenza)
        formset = ScadenzaOccorrenzaFormSet(instance=scadenza)
    set_breadcrumbs(request, [("Scadenze", reverse("scadenze:home")), (scadenza.titolo, reverse("scadenze:detail", args=[scadenza.pk])), ("Modifica", None)])
    return render(
        request,
        "scadenze/form.html",
        {
            "form": form,
            "formset": formset,
            "obj": scadenza,
        },
    )


@login_required
@require_POST
def trigger_alert(request, occorrenza_pk: int):
    occorrenza = get_object_or_404(ScadenzaOccorrenza, pk=occorrenza_pk)
    dispatcher = AlertDispatcher(user=request.user)
    try:
        dispatcher.dispatch(occorrenza)
        messages.success(request, "Alert inviato correttamente.")
    except Exception as exc:  # pragma: no cover
        messages.error(request, f"Errore durante l'invio dell'alert: {exc}")
    return redirect("scadenze:detail", occorrenza.scadenza_id)


@login_required
def bulk_generate(request, pk: int):
    scadenza = get_object_or_404(Scadenza, pk=pk)
    if request.method == "POST":
        form = ScadenzaBulkOccurrencesForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            alert_config = data.get("alert_config") or {}
            scadenza.genera_occorrenze_massive(
                start=data["start"],
                end=data.get("end"),
                count=data.get("count"),
                offset_alert_minuti=data["offset_alert_minuti"],
                metodo_alert=data["metodo_alert"],
                alert_config=alert_config,
            )
            messages.success(request, "Occorrenze generate correttamente.")
            return redirect("scadenze:detail", scadenza.pk)
    else:
        form = ScadenzaBulkOccurrencesForm()
    set_breadcrumbs(
        request,
        [
            ("Scadenze", reverse("scadenze:home")),
            (scadenza.titolo, reverse("scadenze:detail", args=[scadenza.pk])),
            ("Generazione massiva", None),
        ],
    )
    return render(
        request,
        "scadenze/bulk_generate.html",
        {
            "form": form,
            "scadenza": scadenza,
        },
    )
