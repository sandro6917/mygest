from __future__ import annotations
from django.db.models import Q, Value, CharField, Case, When
from django.db.models.functions import Concat
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse, NoReverseMatch
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db import transaction
from collections import Counter
from anagrafiche.models import Anagrafica, AnagraficaDeletion, Cliente
from documenti.models import Documento
from .forms import SearchAnagraficaForm, AnagraficaForm, ClienteForm
from .models import ClientiTipo

@login_required
def home(request):
    # Ricerca
    q = (request.GET.get("q") or "").strip()

    # Campi disponibili nel modello
    field_names = {f.name for f in Anagrafica._meta.get_fields() if getattr(f, "concrete", False)}

    # Ordinamento alfabetico "intelligente"
    order_by_fields = []
    if {"cognome", "nome"} <= field_names:
        order_by_fields = ["cognome", "nome"]
    elif "denominazione" in field_names:
        order_by_fields = ["denominazione"]
    elif "ragione_sociale" in field_names:
        order_by_fields = ["ragione_sociale"]
    else:
        order_by_fields = ["id"]

    qs = Anagrafica.objects.all()

    # Filtri di ricerca su campi testuali comuni (solo se esistono)
    searchable_candidates = [
        "denominazione", "ragione_sociale", "cognome", "nome",
        "codice_fiscale", "partita_iva", "email", "cf", "piva",
    ]
    searchable_fields = [f for f in searchable_candidates if f in field_names]

    if q and searchable_fields:
        cond = Q()
        for f in searchable_fields:
            cond |= Q(**{f + "__icontains": q})
        qs = qs.filter(cond)

    qs = qs.order_by(*order_by_fields)
    total_count = qs.count()
    limit = 25
    anagrafiche_filtrate = list(qs[:limit])

    # Box esistenti: ultimi/attività/top
    ultimi_clienti = Anagrafica.objects.order_by("-id")[:5]

    recent_docs = Documento.objects.select_related("cliente").order_by("-id")[:100]
    clienti_recenti_ids = []
    for d in recent_docs:
        if d.cliente_id and d.cliente_id not in clienti_recenti_ids:
            clienti_recenti_ids.append(d.cliente_id)
    lookup = {c.id: c for c in Anagrafica.objects.filter(id__in=clienti_recenti_ids)}
    clienti_recenti = [lookup[cid] for cid in clienti_recenti_ids if cid in lookup][:5]

    counter = Counter(d.cliente_id for d in recent_docs if d.cliente_id)
    top_ids = [cid for cid, _ in counter.most_common(5)]
    top_lookup = {c.id: c for c in Anagrafica.objects.filter(id__in=top_ids)}
    top_clienti = [(top_lookup[cid], counter[cid]) for cid in top_ids if cid in top_lookup]

    return render(request, "anagrafiche/home.html", {
        "q": q,
        "anagrafiche_filtrate": anagrafiche_filtrate,
        "anagrafiche_total": total_count,
        "anagrafiche_limit": limit,
        "ultimi_clienti": ultimi_clienti,
        "clienti_recenti": clienti_recenti,
        "top_clienti": top_clienti,
    })

def _anagrafica_edit_url(obj):
    candidates = [
        "anagrafiche:modifica",
        "anagrafiche:edit",
        "anagrafiche:update",
        "anagrafiche:anagrafica_modifica",
        "anagrafiche:anagrafica_edit",
    ]
    for name in candidates:
        try:
            return reverse(name, args=[obj.pk])
        except NoReverseMatch:
            continue
    # fallback admin
    try:
        return reverse("admin:anagrafiche_anagrafica_change", args=[obj.pk])
    except NoReverseMatch:
        return f"/admin/anagrafiche/anagrafica/{obj.pk}/change/"

def detail(request, pk: int):
    obj = get_object_or_404(Anagrafica, pk=pk)
    q = (request.GET.get("q") or "").strip()

    # Documenti collegati all’anagrafica: usa il campo esistente 'cliente'
    base_docs = Documento.objects.filter(cliente=obj)

    # Ricerca parziale case-insensitive su campi esistenti
    if q:
        base_docs = base_docs.filter(
            Q(codice__icontains=q) |
            Q(descrizione__icontains=q) |
            Q(note__icontains=q) |
            Q(file__icontains=q) |
            Q(percorso_archivio__icontains=q)
        )

    documenti = base_docs.order_by("-id")[:10]

    return render(request, "anagrafiche/detail.html", {
        "obj": obj,
        "edit_url": _anagrafica_edit_url(obj),
        "documenti": documenti,
        "q": q,
    })

def _get_default_clienti_tipo():
    # Usa il primo tipo cliente disponibile come default
    return ClientiTipo.objects.order_by("id").first()

@method_decorator(login_required, name="dispatch")
class AnagraficaCreateView(View):
    template_name = "anagrafiche/anagrafica_form.html"

    def get(self, request):
        a_form = AnagraficaForm()
        c_form = ClienteForm(prefix="cliente")
        return render(request, self.template_name, {"a_form": a_form, "c_form": c_form, "is_create": True})

    def post(self, request, *args, **kwargs):
        a_form = AnagraficaForm(request.POST, request.FILES)
        c_form = ClienteForm(request.POST, request.FILES, prefix="cliente")
        if a_form.is_valid() and c_form.is_valid():
            with transaction.atomic():
                anagrafica = a_form.save()
                cliente = c_form.save(commit=False)
                # niente default forzato: 'tipo_cliente' può essere nullo
                cliente.anagrafica = anagrafica
                cliente.save()
            messages.success(request, "Anagrafica e Cliente creati correttamente.")
            return redirect(reverse("anagrafiche:detail", args=[anagrafica.pk]))
        return render(request, self.template_name, {"a_form": a_form, "c_form": c_form, "is_create": True})

@method_decorator(login_required, name="dispatch")
class AnagraficaUpdateView(View):
    template_name = "anagrafiche/anagrafica_form.html"

    def get(self, request, pk: int):
        anagrafica = get_object_or_404(Anagrafica, pk=pk)
        # NON creare qui: mostra il form (vuoto o con instance se c'è)
        cliente = Cliente.objects.filter(anagrafica=anagrafica).first()
        a_form = AnagraficaForm(instance=anagrafica)
        if cliente:
            c_form = ClienteForm(instance=cliente, prefix="cliente")
        else:
            c_form = ClienteForm(prefix="cliente")
        return render(request, self.template_name, {"a_form": a_form, "c_form": c_form, "is_create": False, "obj": anagrafica})

    def post(self, request, pk: int):
        anagrafica = get_object_or_404(Anagrafica, pk=pk)
        cliente = Cliente.objects.filter(anagrafica=anagrafica).first()
        a_form = AnagraficaForm(request.POST, request.FILES, instance=anagrafica)
        c_form = ClienteForm(request.POST, request.FILES, instance=cliente, prefix="cliente") if cliente else ClienteForm(request.POST, request.FILES, prefix="cliente")
        if a_form.is_valid() and c_form.is_valid():
            with transaction.atomic():
                anagrafica = a_form.save()
                cliente = c_form.save(commit=False)
                cliente.anagrafica = anagrafica
                cliente.save()
            messages.success(request, "Anagrafica e Cliente aggiornati correttamente.")
            return redirect(reverse("anagrafiche:detail", args=[anagrafica.pk]))
        return render(request, self.template_name, {"a_form": a_form, "c_form": c_form, "is_create": False, "obj": anagrafica})

class AnagraficaDeleteView(DeleteView):
    model = Anagrafica
    template_name = "anagrafiche/confirm_delete.html"
    success_url = reverse_lazy("anagrafiche:home")
