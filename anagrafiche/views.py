from __future__ import annotations
from django.db.models import Q, Value, CharField, Case, When
from django.db.models.functions import Concat, Coalesce
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse, NoReverseMatch
from django.views.generic import UpdateView, DeleteView, CreateView, ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib import messages
from django.db import transaction
from collections import Counter
from anagrafiche.models import Anagrafica, AnagraficaDeletion, Cliente
from comunicazioni.models import Comunicazione
from documenti.models import Documento
from pratiche.models import Pratica
from fascicoli.models import Fascicolo
from .forms import SearchAnagraficaForm, AnagraficaForm, ClienteForm, IndirizzoForm
from .models import ClientiTipo, Indirizzo
import csv, io
from django import forms
from django.http import HttpResponse
from .utils import get_or_generate_cli
from mygest.breadcrumbs import set_breadcrumbs

PREFIX_INDIRIZZI = "indirizzi"


def _resolve_cliente_relation(model, field_name: str = "cliente"):
    """Return select_related fields, filter key, and flag if FK points to Cliente."""
    select_fields = []
    filter_key = None
    targets_cliente = False
    try:
        field = model._meta.get_field(field_name)
    except Exception:
        return select_fields, filter_key, targets_cliente

    remote_field = getattr(field, "remote_field", None)
    remote_model = getattr(remote_field, "model", None)

    if remote_model:
        select_fields.append(field_name)

    remote_model_name = getattr(getattr(remote_model, "_meta", None), "model_name", "")
    if remote_model_name == Cliente._meta.model_name:
        select_fields.append(f"{field_name}__anagrafica")
        filter_key = f"{field_name}__anagrafica"
        targets_cliente = True
    else:
        filter_key = field_name

    select_fields = list(dict.fromkeys(select_fields))
    return select_fields, filter_key, targets_cliente


def _extract_anagrafica_id(instance, relation_name: str = "cliente", relation_targets_cliente: bool = False):
    """Safely extract the anagrafica id from related objects."""
    if relation_targets_cliente:
        related = getattr(instance, relation_name, None)
        return getattr(related, "anagrafica_id", None) if related else None
    ident = getattr(instance, f"{relation_name}_id", None)
    if ident is not None:
        return ident
    related = getattr(instance, relation_name, None)
    return getattr(related, "id", None) if related else None

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

    doc_cliente_select, _, doc_cliente_targets_cliente = _resolve_cliente_relation(Documento)
    recent_docs_qs = Documento.objects.all()
    if doc_cliente_select:
        recent_docs_qs = recent_docs_qs.select_related(*doc_cliente_select)
    recent_docs = list(recent_docs_qs.order_by("-id")[:100])
    clienti_recenti_ids = []
    for d in recent_docs:
        anag_id = _extract_anagrafica_id(d, relation_targets_cliente=doc_cliente_targets_cliente)
        if anag_id and anag_id not in clienti_recenti_ids:
            clienti_recenti_ids.append(anag_id)
    lookup = {c.id: c for c in Anagrafica.objects.filter(id__in=clienti_recenti_ids)}
    clienti_recenti = [lookup[cid] for cid in clienti_recenti_ids if cid in lookup][:5]

    counter = Counter(
        anag_id
        for anag_id in (
            _extract_anagrafica_id(d, relation_targets_cliente=doc_cliente_targets_cliente)
            for d in recent_docs
        )
        if anag_id
    )
    top_ids = [cid for cid, _ in counter.most_common(5)]
    top_lookup = {c.id: c for c in Anagrafica.objects.filter(id__in=top_ids)}
    top_clienti = [(top_lookup[cid], counter[cid]) for cid in top_ids if cid in top_lookup]

    context = {
        "q": q,
        "anagrafiche_filtrate": anagrafiche_filtrate,
        "anagrafiche_total": total_count,
        "anagrafiche_limit": limit,
        "ultimi_clienti": ultimi_clienti,
        "clienti_recenti": clienti_recenti,
        "top_clienti": top_clienti,
    }
    set_breadcrumbs(request, [("Anagrafiche", None)])
    return render(request, "anagrafiche/home.html", context)

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

    doc_cliente_select, doc_cliente_filter_key, _ = _resolve_cliente_relation(Documento)
    base_docs_qs = Documento.objects.all()
    if doc_cliente_select:
        base_docs_qs = base_docs_qs.select_related(*doc_cliente_select)
    if doc_cliente_filter_key:
        base_docs = base_docs_qs.filter(**{doc_cliente_filter_key: obj})
    else:
        base_docs = base_docs_qs.none()

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

    # Ultime pratiche per questa anagrafica (Pratica.cliente -> Cliente)
    pratica_select, pratica_filter_key, _ = _resolve_cliente_relation(Pratica)
    pratiche_qs = Pratica.objects.all()
    if pratica_select:
        pratiche_qs = pratiche_qs.select_related(*pratica_select)
    if pratica_filter_key:
        pratiche = list(
            pratiche_qs.filter(**{pratica_filter_key: obj}).order_by("-id")[:10]
        )
    else:
        pratiche = []

    # Ultimi fascicoli per questa anagrafica (Fascicolo.cliente può puntare a Cliente o Anagrafica)
    try:
        fascicolo_select, fascicolo_filter_key, _ = _resolve_cliente_relation(Fascicolo)
        fascicoli_qs = Fascicolo.objects.prefetch_related("pratiche")
        if fascicolo_select:
            fascicoli_qs = fascicoli_qs.select_related(*fascicolo_select)
        if fascicolo_filter_key:
            fascicoli = list(
                fascicoli_qs.filter(**{fascicolo_filter_key: obj}).order_by("-id")[:10]
            )
        else:
            fascicoli = list(fascicoli_qs.order_by("-id")[:10])
    except Exception:
        fascicoli = list(
            Fascicolo.objects.prefetch_related("pratiche").order_by("-id")[:10]
        )

    # Indirizzi dell’anagrafica (per lista e principale)
    indirizzi = Indirizzo.objects.filter(anagrafica=obj).order_by("-principale", "id")
    indirizzo_principale = obj.indirizzo_principale

    comunicazioni_qs = (
        Comunicazione.objects.filter(anagrafica=obj)
        .annotate(data_riferimento=Coalesce("data_invio", "data_creazione"))
        .order_by("-data_riferimento", "-id")
    )
    comunicazioni = list(comunicazioni_qs[:20])

    context = {
        "obj": obj,
        "edit_url": _anagrafica_edit_url(obj),
        "documenti": documenti,
        "q": q,
        "pratiche": pratiche,
        "fascicoli": fascicoli,
        "indirizzi": indirizzi,
        "indirizzo_principale": indirizzo_principale,
        "comunicazioni": comunicazioni,
    }
    set_breadcrumbs(
        request,
        [
            ("Anagrafiche", reverse("anagrafiche:home")),
            (obj.display_name(), obj.get_absolute_url()),
        ],
    )
    return render(request, "anagrafiche/detail.html", context)

def _get_default_clienti_tipo():
    # Usa il primo tipo cliente disponibile come default
    return ClientiTipo.objects.order_by("id").first()

class AnagraficaDeleteView(DeleteView):
    model = Anagrafica
    template_name = "anagrafiche/confirm_delete.html"
    success_url = reverse_lazy("anagrafiche:home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = context.get("object")
        if obj:
            set_breadcrumbs(
                self.request,
                [
                    ("Anagrafiche", reverse("anagrafiche:home")),
                    (obj.display_name(), obj.get_absolute_url()),
                    ("Elimina", None),
                ],
            )
            context["breadcrumbs"] = self.request.breadcrumbs
        return context

def _set_indirizzo_principale(anagrafica: Anagrafica):
    # Prende l’indirizzo marcato come principale, altrimenti il primo disponibile
    principale = (
        Indirizzo.objects
        .filter(anagrafica=anagrafica)
        .order_by("-principale", "id")
        .first()
    )
    anagrafica.indirizzo = str(principale) if principale else ""
    anagrafica.save(update_fields=["indirizzo"])

@login_required
def anagrafica_create(request):
    if request.method == "POST" and request.POST.get("action") == "save":
        a_form = AnagraficaForm(request.POST, request.FILES, prefix="anag")
        c_form = ClienteForm(request.POST, request.FILES, anagrafica=None, prefix="cli")
        if a_form.is_valid() and c_form.is_valid():
            with transaction.atomic():
                anag = a_form.save()
                cli = c_form.save(commit=False)
                cli.anagrafica = anag
                cli.save()
            return redirect(anag.get_absolute_url())
    else:
        a_form = AnagraficaForm(prefix="anag")
        c_form = ClienteForm(anagrafica=None, prefix="cli")
    context = {"is_create": True, "a_form": a_form, "c_form": c_form}
    set_breadcrumbs(
        request,
        [
            ("Anagrafiche", reverse("anagrafiche:home")),
            ("Nuova anagrafica", None),
        ],
    )
    return render(request, "anagrafiche/anagrafica_form.html", context)

@login_required
def anagrafica_update(request, pk):
    anagrafica = get_object_or_404(Anagrafica, pk=pk)
    cliente, _ = Cliente.objects.get_or_create(anagrafica=anagrafica)

    a_form = AnagraficaForm(request.POST or None, request.FILES or None, instance=anagrafica, prefix="anag")
    c_form = ClienteForm(request.POST or None, request.FILES or None, instance=cliente, anagrafica=anagrafica, prefix="cli")

    if request.method == "POST" and request.POST.get("action") == "save":
        if a_form.is_valid() and c_form.is_valid():
            with transaction.atomic():
                a_form.save()
                obj = c_form.save(commit=False)
                obj.anagrafica = anagrafica
                obj.save()
            return redirect(anagrafica.get_absolute_url())
    context = {"is_create": False, "a_form": a_form, "c_form": c_form}
    set_breadcrumbs(
        request,
        [
            ("Anagrafiche", reverse("anagrafiche:home")),
            (anagrafica.display_name(), anagrafica.get_absolute_url()),
            ("Modifica", None),
        ],
    )
    return render(request, "anagrafiche/anagrafica_form.html", context)

@login_required
def indirizzi_list(request, pk: int):
    anag = get_object_or_404(Anagrafica, pk=pk)
    indirizzi = Indirizzo.objects.filter(anagrafica=anag).order_by("-principale", "id")
    context = {"anagrafica": anag, "indirizzi": indirizzi}
    set_breadcrumbs(
        request,
        [
            ("Anagrafiche", reverse("anagrafiche:home")),
            (anag.display_name(), anag.get_absolute_url()),
            ("Indirizzi", None),
        ],
    )
    return render(request, "anagrafiche/indirizzi_list.html", context)

@method_decorator(login_required, name="dispatch")
class IndirizzoCreateView(CreateView):
    model = Indirizzo
    form_class = IndirizzoForm
    template_name = "anagrafiche/indirizzo_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.anag = get_object_or_404(Anagrafica, pk=kwargs["anagrafica_pk"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.anagrafica = self.anag
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("anagrafiche:indirizzi_list", args=[self.anag.pk])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["anagrafica"] = self.anag
        set_breadcrumbs(
            self.request,
            [
                ("Anagrafiche", reverse("anagrafiche:home")),
                (self.anag.display_name(), self.anag.get_absolute_url()),
                ("Nuovo indirizzo", None),
            ],
        )
        ctx["breadcrumbs"] = self.request.breadcrumbs
        return ctx

@method_decorator(login_required, name="dispatch")
class IndirizzoUpdateView(UpdateView):
    model = Indirizzo
    form_class = IndirizzoForm
    template_name = "anagrafiche/indirizzo_form.html"

    def get_success_url(self):
        return reverse("anagrafiche:indirizzi_list", args=[self.object.anagrafica_id])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        anag = self.object.anagrafica
        set_breadcrumbs(
            self.request,
            [
                ("Anagrafiche", reverse("anagrafiche:home")),
                (anag.display_name(), anag.get_absolute_url()),
                ("Modifica indirizzo", None),
            ],
        )
        ctx["breadcrumbs"] = self.request.breadcrumbs
        return ctx

class ImportAnagraficaForm(forms.Form):
    file = forms.FileField(label="File CSV")

def import_anagrafiche(request):
    if request.method == "POST":
        form = ImportAnagraficaForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['file']
            try:
                decoded_file = csv_file.read().decode('utf-8')
            except UnicodeDecodeError:
                csv_file.seek(0)
                decoded_file = csv_file.read().decode('latin-1')
            # Gestione BOM e separatore ;
            decoded_file = decoded_file.lstrip('\ufeff')
            reader = csv.DictReader(io.StringIO(decoded_file), delimiter=';')
            count = 0
            for row in reader:
                try:
                    codice = row.get("codice", "").strip() or None
                    Anagrafica.objects.create(
                        tipo=row.get("tipo", ""),
                        ragione_sociale=row.get("ragione_sociale", ""),
                        nome=row.get("nome", ""),
                        cognome=row.get("cognome", ""),
                        codice_fiscale=row.get("codice_fiscale", ""),
                        partita_iva=row.get("partita_iva", ""),
                        codice=codice,
                        pec=row.get("pec", ""),
                        email=row.get("email", ""),
                        telefono=row.get("telefono", ""),
                        indirizzo=row.get("indirizzo", ""),
                        note=row.get("note", ""),
                    )
                    count += 1
                except Exception as e:
                    messages.error(request, f"Errore riga: {row} - {e}")
            messages.success(request, f"Importate {count} anagrafiche.")
            return redirect("anagrafiche:import")
    else:
        form = ImportAnagraficaForm()
    context = {"form": form}
    set_breadcrumbs(
        request,
        [
            ("Anagrafiche", reverse("anagrafiche:home")),
            ("Importazione", None),
        ],
    )
    return render(request, "anagrafiche/import_anagrafiche.html", context)

def facsimile_csv(request):
    # Genera un CSV di esempio
    header = [
        "tipo", "ragione_sociale", "nome", "cognome", "codice_fiscale",
        "partita_iva", "codice", "pec", "email", "telefono", "indirizzo", "note"
    ]
    example = [
        ["PF", "", "Mario", "Rossi", "RSSMRA80A01H501U", "", "CLI0001", "mario.rossi@pec.it", "mario@email.it", "3331234567", "Via Roma 1, Milano", ""],
        ["PG", "Azienda Srl", "", "", "12345678901", "12345678901", "CLI0002", "azienda@pec.it", "info@azienda.it", "024567890", "Via Milano 10, Milano", "Cliente importante"],
    ]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="facsimile_anagrafiche.csv"'
    writer = csv.writer(response)
    writer.writerow(header)
    for row in example:
        writer.writerow(row)
    return response

@login_required
def ricalcola_codici(request):
    count = 0
    for a in Anagrafica.objects.filter(Q(codice__isnull=True) | Q(codice="" | Q(codice__startswith="CLI")==True)):
        # Esempio: genera codice come 'CLI' + id a 5 cifre
        a.codice = f"CLI{a.id:05d}"
        a.save(update_fields=["codice"])
        count += 1
    messages.success(request, f"Ricalcolati {count} codici anagrafica.")
    return redirect("anagrafiche:home")

@login_required
def ricalcola_codice_anagrafica(request, pk):
    anagrafica = get_object_or_404(Anagrafica, pk=pk)
    nuovo_codice = get_or_generate_cli(anagrafica)
    codice_attuale = anagrafica.codice or ""
    if request.method == "POST" and request.POST.get("conferma") == "yes":
        if nuovo_codice != codice_attuale:
            anagrafica.codice = nuovo_codice
            anagrafica.save(update_fields=["codice"])
            messages.success(request, f"Codice aggiornato a {nuovo_codice}.")
        else:
            messages.info(request, "Il codice era già corretto.")
        return redirect(anagrafica.get_absolute_url())
    context = {
        "obj": anagrafica,
        "codice_attuale": codice_attuale,
        "nuovo_codice": nuovo_codice,
    }
    set_breadcrumbs(
        request,
        [
            ("Anagrafiche", reverse("anagrafiche:home")),
            (anagrafica.display_name(), anagrafica.get_absolute_url()),
            ("Ricalcola codice", None),
        ],
    )
    return render(request, "anagrafiche/ricalcola_codice_confirm.html", context)
