from django.db import OperationalError
from django.db.models import Q, Prefetch, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Pratica, PraticheTipo, PraticaNota, PraticaRelazione
from .forms import PraticaForm, PraticaNotaForm
from django.views.decorators.http import require_POST
from fascicoli.models import Fascicolo
from anagrafiche.models import Cliente
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from scadenze.models import Scadenza as AppScadenza, ScadenzaOccorrenza

from mygest.breadcrumbs import set_breadcrumbs

def home(request):
    q = (request.GET.get("q") or "").strip()
    tipo_q = (request.GET.get("tipo_q") or "").strip()

    try:
        base_pratiche = (
            Pratica.objects.select_related("cliente__anagrafica", "tipo")
            .only(
                "id",
                "codice",
                "oggetto",
                "stato",
                "cliente_id",
                "cliente__anagrafica__id",
                "cliente__anagrafica__ragione_sociale",
                "cliente__anagrafica__nome",
                "cliente__anagrafica__cognome",
                "tipo__codice",
                "tipo__nome",
            )
        )

        ultimi_pratiche = base_pratiche.order_by("-id")[:10]

        pratiche_qs = base_pratiche
        if q:
            pratiche_qs = pratiche_qs.filter(
                Q(codice__icontains=q)
                | Q(oggetto__icontains=q)
                | Q(cliente__anagrafica__ragione_sociale__icontains=q)
                | Q(cliente__anagrafica__cognome__icontains=q)
                | Q(cliente__anagrafica__nome__icontains=q)
                | Q(tipo__codice__icontains=q)
                | Q(tipo__nome__icontains=q)
            )
        pratiche_qs = pratiche_qs.exclude(stato="chiusa")
        pratiche_total = pratiche_qs.count()
        pratiche_filtrate = pratiche_qs.order_by("-id")[:50]

        tipi_qs = (
            PraticheTipo.objects.annotate(pratiche_count=Count("pratiche"))
            .order_by("nome", "codice")
        )
        if tipo_q:
            tipi_qs = tipi_qs.filter(
                Q(codice__icontains=tipo_q) | Q(nome__icontains=tipo_q)
            )

        tipi_total = tipi_qs.count()
        tipi_filtrati = list(tipi_qs[:50])

        clienti_recenti = []
        seen_cli = set()
        for p in base_pratiche.order_by("-id")[:100]:
            if p.cliente_id and p.cliente_id not in seen_cli:
                seen_cli.add(p.cliente_id)
                clienti_recenti.append(p.cliente)
            if len(clienti_recenti) >= 10:
                break

        imminenti = (
            ScadenzaOccorrenza.objects.select_related("scadenza")
            .filter(
                inizio__gte=timezone.now() - timedelta(hours=1),
                stato__in=[
                    ScadenzaOccorrenza.Stato.PENDENTE,
                    ScadenzaOccorrenza.Stato.PROGRAMMATA,
                ],
                scadenza__stato__in=[
                    AppScadenza.Stato.ATTIVA,
                    AppScadenza.Stato.BOZZA,
                ],
            )
            .order_by("inizio")[:10]
        )

    except OperationalError:
        ultimi_pratiche = []
        pratiche_filtrate, pratiche_total = [], 0
        clienti_recenti = []
        imminenti = []
        tipi_filtrati, tipi_total = [], 0

    set_breadcrumbs(request, [("Pratiche", None)])
    return render(request, "pratiche/home.html", {
        "q": q,
        "tipo_q": tipo_q,
        "ultimi_pratiche": ultimi_pratiche,
        "pratiche_filtrate": pratiche_filtrate,
        "pratiche_total": pratiche_total,
        "clienti_recenti": clienti_recenti,
        "tipi_filtrati": tipi_filtrati,
        "tipi_total": tipi_total,
        "imminenti": imminenti,
    })


def tipo_dettaglio(request, pk: int):
    tipo = get_object_or_404(PraticheTipo, pk=pk)
    q = (request.GET.get("q") or "").strip()
    pratiche_qs = tipo.pratiche.select_related("cliente__anagrafica").all()
    if q:
        pratiche_qs = pratiche_qs.filter(
            Q(codice__icontains=q)
            | Q(oggetto__icontains=q)
            | Q(cliente__anagrafica__ragione_sociale__icontains=q)
            | Q(cliente__anagrafica__nome__icontains=q)
            | Q(cliente__anagrafica__cognome__icontains=q)
        )
    pratiche_qs = pratiche_qs.order_by("-id")
    pratiche_total = pratiche_qs.count()
    pratiche_filtrate = list(pratiche_qs[:50])
    set_breadcrumbs(
        request,
        [
            ("Pratiche", reverse("pratiche:home")),
            (tipo.nome, None),
        ],
    )
    return render(
        request,
        "pratiche/tipo_dettaglio.html",
        {
            "tipo": tipo,
            "q": q,
            "pratiche_filtrate": pratiche_filtrate,
            "pratiche_total": pratiche_total,
        },
    )


def pratica_dettaglio(request, pk: int):
    pratica = get_object_or_404(
        Pratica.objects.select_related("cliente__anagrafica", "tipo", "responsabile")
        .prefetch_related(
            "note_collegate",
            "fascicoli",
            Prefetch(
                "scadenze",
                queryset=AppScadenza.objects.prefetch_related("occorrenze").filter(
                    stato__in=[AppScadenza.Stato.ATTIVA, AppScadenza.Stato.BOZZA]
                ),
            ),
            Prefetch("relazioni_uscita", queryset=PraticaRelazione.objects.select_related("child")),
            Prefetch("relazioni_entrata", queryset=PraticaRelazione.objects.select_related("parent")),
        ),
        pk=pk,
    )

    # Filtri per documenti
    q_doc = (request.GET.get("q_doc") or "").strip()
    tipo_doc = (request.GET.get("tipo_doc") or "").strip()
    cliente_doc = (request.GET.get("cliente_doc") or "").strip()
    data_da = (request.GET.get("data_da") or "").strip()
    data_a = (request.GET.get("data_a") or "").strip()

    try:
        from documenti.models import Documento
        from datetime import datetime

        documenti = (
            Documento.objects.filter(fascicolo__pratiche=pratica)
            .select_related("cliente", "tipo", "fascicolo")
        )
        
        # Filtro fulltext su codice + descrizione + fascicolo
        if q_doc:
            documenti = documenti.filter(
                Q(codice__icontains=q_doc) |
                Q(descrizione__icontains=q_doc) |
                Q(fascicolo__codice__icontains=q_doc) |
                Q(fascicolo__titolo__icontains=q_doc)
            )
        
        # Filtro per tipo documento
        if tipo_doc:
            documenti = documenti.filter(tipo_id=tipo_doc)
        
        # Filtro per cliente
        if cliente_doc:
            documenti = documenti.filter(cliente_id=cliente_doc)
        
        # Filtro per range date
        if data_da:
            try:
                data_da_parsed = datetime.strptime(data_da, "%Y-%m-%d").date()
                documenti = documenti.filter(data_documento__gte=data_da_parsed)
            except ValueError:
                pass  # Ignora date non valide
        
        if data_a:
            try:
                data_a_parsed = datetime.strptime(data_a, "%Y-%m-%d").date()
                documenti = documenti.filter(data_documento__lte=data_a_parsed)
            except ValueError:
                pass  # Ignora date non valide
        
        documenti = documenti.order_by("-id")
    except Exception:
        documenti = []

    scadenze = pratica.scadenze.all().order_by("titolo")
    note = pratica.note_collegate.all().order_by("-data", "-id")
    relazioni_uscita = pratica.relazioni_uscita.all()
    relazioni_entrata = pratica.relazioni_entrata.all()

    q = (request.GET.get("q") or "").strip()
    fascicoli_risultati = None
    if len(q) >= 2:
        fascicoli_risultati = (
            Fascicolo.objects.prefetch_related("pratiche")
            .filter(Q(codice__icontains=q) | Q(titolo__icontains=q) | Q(note__icontains=q))
            .exclude(pratiche=pratica)
            .order_by("-id")[:25]
        )

    q_pratica = (request.GET.get("q_pratica") or "").strip()
    pratiche_risultati = None
    if len(q_pratica) >= 2:
        pratiche_collegate_ids = set(
            pratica.relazioni_uscita.values_list("child_id", flat=True)
        ) | set(
            pratica.relazioni_entrata.values_list("parent_id", flat=True)
        )
        pratiche_collegate_ids.add(pratica.pk)

        pratiche_risultati = (
            Pratica.objects
            .filter(
                Q(codice__icontains=q_pratica) |
                Q(oggetto__icontains=q_pratica)
            )
            .exclude(pk__in=pratiche_collegate_ids)
            .order_by("-id")[:25]
        )

    # Recupera tipi di documento e clienti per i filtri autocomplete
    try:
        from documenti.models import DocumentiTipo
        tipi_documento = DocumentiTipo.objects.all().order_by("codice")
        
        # Recupera i clienti dai documenti collegati alla pratica
        clienti_documento = (
            Cliente.objects.filter(
                documenti__fascicolo__pratiche=pratica
            )
            .distinct()
            .select_related("anagrafica")
            .order_by("anagrafica__ragione_sociale", "anagrafica__cognome")
        )
    except Exception:
        tipi_documento = []
        clienti_documento = []

    ctx = {
        "pratica": pratica,
        "fascicoli": pratica.fascicoli.all(),
        "documenti": documenti,
        "scadenze": scadenze,
        "note": note,
        "relazioni_uscita": relazioni_uscita,
        "relazioni_entrata": relazioni_entrata,
        "q": q,
        "fascicoli_risultati": fascicoli_risultati,
        "q_pratica": q_pratica,
        "pratiche_risultati": pratiche_risultati,
        "q_doc": q_doc,
        "tipo_doc": tipo_doc,
        "cliente_doc": cliente_doc,
        "data_da": data_da,
        "data_a": data_a,
        "tipi_documento": tipi_documento,
        "clienti_documento": clienti_documento,
    }
    pratica_label = pratica.oggetto or pratica.codice or f"Pratica #{pratica.pk}"
    set_breadcrumbs(
        request,
        [
            ("Pratiche", reverse("pratiche:home")),
            (pratica_label, None),
        ],
    )
    return render(request, "pratiche/dettaglio.html", ctx)

@login_required
@transaction.atomic
def pratica_nuova(request):
    if request.method == "POST":
        form = PraticaForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Pratica creata correttamente.")
            return redirect("pratiche:dettaglio", pk=obj.pk)
    else:
        form = PraticaForm()
    context = {"form": form, "obj": None}
    set_breadcrumbs(
        request,
        [
            ("Pratiche", reverse("pratiche:home")),
            ("Nuova pratica", None),
        ],
    )
    return render(request, "pratiche/form.html", context)

@login_required
@transaction.atomic
def pratica_modifica(request, pk: int):
    obj = get_object_or_404(Pratica, pk=pk)
    if request.method == "POST":
        form = PraticaForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Pratica aggiornata correttamente.")
            return redirect("pratiche:dettaglio", pk=obj.pk)
        else:
            error_msgs = []
            error_data = form.errors.get_json_data(escape_html=True)
            for field, errors in error_data.items():
                if field == "__all__":
                    error_msgs.extend(err.get("message") for err in errors if err.get("message"))
                    continue
                field_obj = form.fields.get(field)
                label = str(field_obj.label) if field_obj and field_obj.label else field.replace("_", " ").capitalize()
                for err in errors:
                    message = err.get("message")
                    if message:
                        error_msgs.append(f"{label}: {message}")
            if not error_msgs and form.errors:
                error_msgs.append(form.errors.as_text())
            if error_msgs:
                messages.error(request, " • ".join(error_msgs))
            else:
                messages.error(request, "Correggi gli errori evidenziati.")
    else:
        form = PraticaForm(instance=obj)
    context = {"form": form, "obj": obj}
    pratica_label = obj.oggetto or obj.codice or f"Pratica #{obj.pk}"
    set_breadcrumbs(
        request,
        [
            ("Pratiche", reverse("pratiche:home")),
            (pratica_label, reverse("pratiche:dettaglio", args=[obj.pk])),
            ("Modifica", None),
        ],
    )
    return render(request, "pratiche/form.html", context)

@login_required
@transaction.atomic
def nota_nuova(request, pratica_pk: int):
    pratica = get_object_or_404(Pratica, pk=pratica_pk)
    nota = PraticaNota(pratica=pratica)
    if request.method == "POST":
        form = PraticaNotaForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, "Nota creata.")
            return redirect("pratiche:dettaglio", pk=pratica.pk)
    else:
        form = PraticaNotaForm(instance=nota)
    context = {"form": form, "pratica": pratica, "obj": None, "is_create": True}
    pratica_label = pratica.oggetto or pratica.codice or f"Pratica #{pratica.pk}"
    set_breadcrumbs(
        request,
        [
            ("Pratiche", reverse("pratiche:home")),
            (pratica_label, reverse("pratiche:dettaglio", args=[pratica.pk])),
            ("Nuova nota", None),
        ],
    )
    return render(request, "pratiche/note/form.html", context)

@login_required
@transaction.atomic
def nota_modifica(request, pk: int):
    nota = get_object_or_404(PraticaNota, pk=pk)
    if request.method == "POST":
        form = PraticaNotaForm(request.POST, instance=nota)
        if form.is_valid():
            form.save()
            messages.success(request, "Nota aggiornata.")
            return redirect("pratiche:dettaglio", pk=nota.pratica_id)
    else:
        form = PraticaNotaForm(instance=nota)
    pratica = nota.pratica
    context = {"form": form, "pratica": pratica, "obj": nota, "is_create": False}
    pratica_label = pratica.oggetto or pratica.codice or f"Pratica #{pratica.pk}"
    set_breadcrumbs(
        request,
        [
            ("Pratiche", reverse("pratiche:home")),
            (pratica_label, reverse("pratiche:dettaglio", args=[pratica.pk])),
            ("Modifica nota", None),
        ],
    )
    return render(request, "pratiche/note/form.html", context)

@require_POST
def collega_fascicolo(request, pk: int):
    pratica = get_object_or_404(Pratica, pk=pk)
    fid = request.POST.get("fascicolo_id")
    if not fid:
        messages.error(request, "Seleziona un fascicolo.")
        return redirect("pratiche:dettaglio", pk=pk)
    fascicolo = get_object_or_404(Fascicolo, pk=fid)
    fascicolo.pratiche.add(pratica)
    messages.success(request, "Fascicolo collegato alla pratica.")
    return redirect("pratiche:dettaglio", pk=pk)

@require_POST
@login_required
def collega_pratica(request, pk: int):
    pratica = get_object_or_404(Pratica, pk=pk)
    pratica_id = request.POST.get("pratica_id")
    tipo = request.POST.get("tipo", "collaborazione")
    if not pratica_id:
        messages.error(request, "Seleziona una pratica.")
        return redirect("pratiche:dettaglio", pk=pk)
    altra = get_object_or_404(Pratica, pk=pratica_id)
    if pratica.pk == altra.pk:
        messages.error(request, "Non puoi collegare la pratica a se stessa.")
        return redirect("pratiche:dettaglio", pk=pk)
    # Evita doppioni
    PraticaRelazione.objects.get_or_create(parent=pratica, child=altra, tipo=tipo)
    messages.success(request, "Pratica collegata.")
    return redirect("pratiche:dettaglio", pk=pk)


def stampa_lista(request, pk: int, slug: str):
    pratica = get_object_or_404(Pratica, pk=pk)
    if slug == "EL_PR_COLL":
        relazioni_uscita = pratica.relazioni_uscita.select_related("child").all()
        relazioni_entrata = pratica.relazioni_entrata.select_related("parent").all()
        pratica_label = pratica.oggetto or pratica.codice or f"Pratica #{pratica.pk}"
        set_breadcrumbs(
            request,
            [
                ("Pratiche", reverse("pratiche:home")),
                (pratica_label, reverse("pratiche:dettaglio", args=[pratica.pk])),
                ("Stampa pratiche collegate", None),
            ],
        )
        return render(request, "pratiche/stampa_pratiche_collegate.html", {
            "pratica": pratica,
            "relazioni_uscita": relazioni_uscita,
            "relazioni_entrata": relazioni_entrata,
        })
    # Altri slug...
    return redirect("pratiche:dettaglio", pk=pk)
