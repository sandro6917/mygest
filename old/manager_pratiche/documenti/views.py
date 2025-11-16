from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import DocumentiTipo, Documento, MovimentoProtocollo
from .forms import DocumentoDinamicoForm, ProtocolloForm
from anagrafiche.models import Anagrafica
from django.db.models import Q
from .services import protocolla
from .forms import AssegnaCollocazioneForm
from archivio_fisico.models import CollocazioneFisica
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django.db import transaction
from django.urls import reverse

@login_required
def documento_nuovo_dinamico(request):
    cliente_id = request.GET.get("cliente") or request.POST.get("cliente") or ""
    # Step 1: selezione tipo
    if request.method == "POST" and request.POST.get("step") == "select_type":
        tipo_id = request.POST.get("tipo_id")
        url = reverse("documenti:nuovo_dinamico_tipo", kwargs={"tipo_id": tipo_id})
        if cliente_id:
            url = f"{url}?cliente={cliente_id}"
        return redirect(url)

    return render(
        request,
        "documenti/nuovo_select_tipo.html",
        {"tipi": DocumentiTipo.objects.filter(attivo=True).order_by("nome"), "cliente_id": cliente_id},
    )

@login_required
def documento_nuovo_dinamico_tipo(request, tipo_id: int):
    tipo = get_object_or_404(DocumentiTipo, pk=tipo_id)
    cliente_id = request.GET.get("cliente") or request.POST.get("cliente")

    if request.method == "POST":
        data = request.POST.copy()
        if cliente_id and not data.get("cliente"):
            data["cliente"] = cliente_id  # preserva il cliente anche se il template non lo invia
        form = DocumentoDinamicoForm(data, request.FILES, tipo=tipo)
        if form.is_valid():
            doc = form.save()
            messages.success(request, f"Documento creato: #{doc.id}")
            return redirect("documenti:dettaglio", pk=doc.pk)
    else:
        initial = {}
        if cliente_id:
            initial["cliente"] = cliente_id
        form = DocumentoDinamicoForm(tipo=tipo, initial=initial)

    return render(request, "documenti/nuovo_dinamico.html", {"form": form, "tipo": tipo, "cliente_id": cliente_id})

@login_required
def documento_modifica_dinamico(request, pk: int):
    doc = get_object_or_404(Documento.objects.select_related("tipo"), pk=pk)
    tipo = getattr(doc, "tipo", None)
    if request.method == "POST":
        form = DocumentoDinamicoForm(request.POST, request.FILES, instance=doc, tipo=tipo)
        if form.is_valid():
            form.save()
            messages.success(request, f"Documento aggiornato: #{doc.id}")
            return redirect("documenti:home")
    else:
        form = DocumentoDinamicoForm(instance=doc, tipo=tipo)
    return render(request, "documenti/modifica_dinamico.html", {"form": form, "doc": doc, "tipo": tipo})

@login_required
def documento_protocolla(request, pk: int):
    doc = get_object_or_404(Documento.objects.select_related("cliente", "tipo"), pk=pk)
    initial_dir = "IN" if doc.movimento_out_aperto else "OUT"
    if request.method == "POST":
        form = ProtocolloForm(request.POST)
        if form.is_valid():
            direzione = form.cleaned_data["direzione"]
            quando = form.cleaned_data["quando"]
            ubicazione = form.cleaned_data.get("ubicazione")
            causale = form.cleaned_data.get("causale", "")
            note = form.cleaned_data.get("note", "")
            if direzione == "IN":
                mov = protocolla(
                    doc, "IN",
                    quando=quando, operatore=request.user,
                    destinatario=form.cleaned_data.get("da_chi", ""),
                    ubicazione=ubicazione, causale=causale, note=note,
                )
                messages.success(request, f"Protocollato IN n. {mov.numero}/{mov.anno}")
            else:
                mov = protocolla(
                    doc, "OUT",
                    quando=quando, operatore=request.user,
                    destinatario=form.cleaned_data.get("a_chi", ""),
                    ubicazione=ubicazione,
                    data_rientro_prevista=form.cleaned_data.get("data_rientro_prevista"),
                    causale=causale, note=note,
                )
                messages.success(request, f"Protocollato OUT n. {mov.numero}/{mov.anno}")
            return redirect("documenti:home")
    else:
        form = ProtocolloForm(initial={"direzione": initial_dir})
    return render(request, "documenti/protocollo.html", {"form": form, "doc": doc})

@login_required
def documento_dettaglio(request, pk: int):
    doc = get_object_or_404(
        Documento.objects.select_related("cliente", "tipo").prefetch_related(),
        pk=pk,
    )
    movimenti = (
        MovimentoProtocollo.objects
        .filter(documento=doc)
        .select_related("ubicazione", "cliente")
        .order_by("-data", "-id")
    )
    return render(request, "documenti/dettaglio.html", {"doc": doc, "movimenti": movimenti})

@login_required
def home(request):
    # Ricerca documenti
    q = (request.GET.get("q") or "").strip()

    # Ultimi 5 documenti
    ultimi_documenti = (
        Documento.objects.select_related("cliente", "tipo")
        .order_by("-id")[:5]
    )

    # Clienti recenti
    recent_docs_for_clients = (
        Documento.objects.select_related("cliente").order_by("-id")[:50]
    )
    clienti_ids = []
    for d in recent_docs_for_clients:
        if d.cliente_id and d.cliente_id not in clienti_ids:
            clienti_ids.append(d.cliente_id)
    if clienti_ids:
        qs_cli = Anagrafica.objects.filter(id__in=clienti_ids)
        lookup_cli = {c.id: c for c in qs_cli}
        clienti_recenti = [lookup_cli[cid] for cid in clienti_ids if cid in lookup_cli][:5]
    else:
        clienti_recenti = []

    # Tipi recenti
    recent_docs_for_types = (
        Documento.objects.select_related("tipo").order_by("-id")[:50]
    )
    tipi_recenti, visti_tipi = [], set()
    for d in recent_docs_for_types:
        if getattr(d, "tipo_id", None) and d.tipo_id not in visti_tipi and d.tipo:
            visti_tipi.add(d.tipo_id)
            tipi_recenti.append(d.tipo)
    tipi_recenti = tipi_recenti[:5]

    # Elenco filtrato (default: alfabetico)
    doc_field_names = {f.name for f in Documento._meta.get_fields() if getattr(f, "concrete", False)}
    if "descrizione" in doc_field_names:
        order_fields = ["descrizione"]
    elif "codice" in doc_field_names:
        order_fields = ["codice"]
    else:
        order_fields = ["id"]

    qs = Documento.objects.select_related("cliente", "tipo").all()

    searchable = [f for f in ("descrizione", "codice", "note") if f in doc_field_names]
    if q and searchable:
        cond = Q()
        for f in searchable:
            cond |= Q(**{f + "__icontains": q})
        qs = qs.filter(cond)

    qs = qs.order_by(*order_fields)
    doc_total = qs.count()
    doc_limit = 25
    documenti_filtrati = list(qs[:doc_limit])

    movimenti_recenti = (
        MovimentoProtocollo.objects
        .select_related("documento", "cliente")
        .order_by("-data")[:20]
    )

    context = {
        "q": q,
        "documenti_filtrati": documenti_filtrati,
        "documenti_total": doc_total,
        "documenti_limit": doc_limit,
        "ultimi_documenti": ultimi_documenti,
        "clienti_recenti": clienti_recenti,
        "tipi_recenti": tipi_recenti,
        "movimenti_recenti": movimenti_recenti,
    }
    return render(request, "documenti/home.html", context)

@login_required
def documento_collocazione(request, pk: int):
    doc = get_object_or_404(Documento.objects.select_related("cliente", "tipo"), pk=pk)
    initial = {}
    if doc.collocazione_fisica:
        initial["unita"] = doc.collocazione_fisica.unita
        initial["note"] = doc.collocazione_fisica.note
    if request.method == "POST":
        form = AssegnaCollocazioneForm(request.POST)
        if form.is_valid():
            unita = form.cleaned_data["unita"]
            note = form.cleaned_data.get("note", "")
            ct_doc = ContentType.objects.get_for_model(Documento)
            CollocazioneFisica.objects.create(
                documento=doc,
                content_type=ct_doc,
                object_id=doc.pk,
                unita=unita,
                note=note,
                attiva=True,
                dal=timezone.now().date(),
            )
            messages.success(request, "Collocazione fisica aggiornata.")
            return redirect("documenti:dettaglio", pk=doc.pk)
    else:
        form = AssegnaCollocazioneForm(initial=initial)
    return render(request, "documenti/collocazione.html", {"form": form, "doc": doc})

@require_POST
@login_required
def documento_collocazione_delete_last(request, pk: int):
    doc = get_object_or_404(Documento, pk=pk)
    with transaction.atomic():
        qs = CollocazioneFisica.objects.filter(documento=doc)
        last = qs.order_by("-dal", "-id").first()
        if not last:
            messages.info(request, "Nessuna collocazione da cancellare.")
            return redirect("documenti:dettaglio", pk=doc.pk)

        last.delete()
        # Se non c'è più una collocazione attiva, riattiva la precedente (ora prima in lista)
        if not qs.filter(attiva=True).exists():
            prev = qs.order_by("-dal", "-id").first()
            if prev:
                prev.attiva = True
                prev.al = None
                prev.save(update_fields=["attiva", "al", "updated_at"])

    messages.success(request, "Ultima collocazione cancellata. Precedente riattivata.")
    return redirect("documenti:dettaglio", pk=doc.pk)
