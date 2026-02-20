from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import DocumentiTipo, Documento
from .forms import DocumentoDinamicoForm, DocumentoForm
from anagrafiche.models import Anagrafica, Cliente
from protocollo.models import MovimentoProtocollo
from django.db.models import Q
from .forms import AssegnaCollocazioneForm
from archivio_fisico.models import CollocazioneFisica, UnitaFisica
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django.db import transaction
from django.urls import reverse
from pratiche.models import Pratica
from fascicoli.models import Fascicolo
from urllib.parse import urlencode

from mygest.breadcrumbs import set_breadcrumbs

def _compute_cliente_param(fascicolo_id: int | None, pratica_id: int | None) -> dict:
    """
    Ritorna {"cliente": <pk coerente con Documento.cliente>} se determinabile da fascicolo/pratica.
    """
    if not (fascicolo_id or pratica_id):
        return {}
    fk_model = Documento._meta.get_field("cliente").remote_field.model
    target_name = fk_model._meta.model_name  # "anagrafica" o "cliente"
    # Sorgente: fascicolo o pratica
    src_cli = None
    if fascicolo_id:
        f = (
            Fascicolo.objects.select_related("cliente", "cliente__anagrafica")
            .prefetch_related("pratiche__cliente", "pratiche__cliente__anagrafica")
            .filter(pk=fascicolo_id)
            .first()
        )
        if f:
            # 1) cliente del fascicolo
            src_cli = getattr(f, "cliente", None)
            # 2) cliente della prima pratica collegata (property compat)
            if not src_cli:
                p = getattr(f, "pratica", None)
                src_cli = getattr(p, "cliente", None) if p else None
            # 3) fallback: prima pratica con cliente
            if not src_cli:
                for p in f.pratiche.all():
                    if getattr(p, "cliente", None):
                        src_cli = p.cliente
                        break
    if not src_cli and pratica_id:
        p = Pratica.objects.select_related("cliente", "cliente__anagrafica").filter(pk=pratica_id).first()
        if p:
            src_cli = getattr(p, "cliente", None)
    if not src_cli:
        return {}
    # Converte Cliente<->Anagrafica in base al FK di Documento
    if target_name == "anagrafica":
        anag_id = getattr(src_cli, "anagrafica_id", None) or getattr(src_cli, "id", None)  # già Anagrafica?
        return {"cliente": anag_id} if anag_id else {}
    else:
        cli_id = getattr(src_cli, "id", None)  # già Cliente?
        return {"cliente": cli_id} if cli_id else {}

def _preserve_params(request) -> dict:
    fascicolo = request.GET.get("fascicolo") or request.POST.get("fascicolo")
    pratica = request.GET.get("pratica") or request.POST.get("pratica")
    params = {}
    if fascicolo:
        params["fascicolo"] = fascicolo
    if pratica:
        params["pratica"] = pratica
    params.update(_compute_cliente_param(fascicolo, pratica))
    return params

def _get_tipo_from_request(request):
    """Recupera il tipo documento da POST/GET (tipo_id o tipo)."""
    tid = (
        request.POST.get("tipo_id")
        or request.POST.get("tipo")
        or request.GET.get("tipo_id")
        or request.GET.get("tipo")
    )
    if not tid:
        return None
    try:
        return DocumentiTipo.objects.get(pk=int(tid))
    except Exception:
        return None

@login_required
def nuovo_dinamico(request):
    preserved = _preserve_params(request)
    breadcrumb_chain = [
        ("Documenti", reverse("documenti:home")),
        ("Nuovo documento", None),
    ]
    set_breadcrumbs(request, breadcrumb_chain)

    # STEP 1: selezione tipo -> mostra direttamente il form (no redirect)
    if request.method == "POST" and request.POST.get("step") == "select_type":
        tipo_id = request.POST.get("tipo_id")
        if not tipo_id:
            return render(
                request,
                "documenti/nuovo_dinamico.html",
                {
                    "tipi": DocumentiTipo.objects.filter(attivo=True).order_by("nome"),
                    "preserved": preserved,
                    "error": "Seleziona un tipo.",
                },
            )
        tipo = get_object_or_404(DocumentiTipo, pk=tipo_id)
        initial = {}
        if preserved.get("cliente"):
            initial["cliente"] = preserved["cliente"]
        if preserved.get("fascicolo"):
            initial["fascicolo"] = preserved["fascicolo"]
        form = DocumentoDinamicoForm(tipo=tipo, initial=initial)
        return render(request, "documenti/nuovo_dinamico.html", {"form": form, "tipo": tipo, "preserved": preserved})

    # STEP 2: salvataggio form dinamico
    if request.method == "POST":
        tipo = _get_tipo_from_request(request) or getattr(getattr(request, "doc", None), "tipo", None)
        if not tipo:
            return render(
                request,
                "documenti/nuovo_dinamico.html",
                {"tipi": DocumentiTipo.objects.filter(attivo=True).order_by("nome"), "preserved": preserved},
            )
        data = request.POST.copy()
        data.setdefault("tipo", str(tipo.pk))
        if preserved.get("cliente") and not data.get("cliente"):
            data["cliente"] = preserved["cliente"]
        if preserved.get("fascicolo") and not data.get("fascicolo"):
            data["fascicolo"] = preserved["fascicolo"]

        form = DocumentoDinamicoForm(data, request.FILES, tipo=tipo)
        if form.is_valid():
            doc = form.save()
            messages.success(request, f"Documento creato: #{doc.id}")
            return redirect("documenti:dettaglio", pk=doc.pk)
        return render(
            request,
            "documenti/nuovo_dinamico.html",
            {"form": form, "tipo": tipo, "preserved": preserved},
        )

    # GET: senza tipo -> selezione; con tipo in query -> mostra form
    tipo = _get_tipo_from_request(request)
    if tipo:
        initial = {}
        if preserved.get("cliente"):
            initial["cliente"] = preserved["cliente"]
        if preserved.get("fascicolo"):
            initial["fascicolo"] = preserved["fascicolo"]
        form = DocumentoDinamicoForm(tipo=tipo, initial=initial)
        return render(
            request,
            "documenti/nuovo_dinamico.html",
            {"form": form, "tipo": tipo, "preserved": preserved},
        )

    fascicoli_qs = (
        Fascicolo.objects.select_related("cliente", "cliente__anagrafica", "titolario_voce")
        .prefetch_related("pratiche")
        .order_by("-id")
    )

    docs = (
        Documento.objects.select_related("cliente", "cliente__anagrafica", "tipo", "fascicolo")
        .prefetch_related("fascicolo__pratiche")
        .order_by("-id")[:25]
    )

    return render(
        request,
        "documenti/nuovo_dinamico.html",
        {"tipi": DocumentiTipo.objects.filter(attivo=True).order_by("nome"), "preserved": preserved},
    )

@login_required
def documento_nuovo_dinamico_tipo(request, tipo_id: int):
    tipo = get_object_or_404(DocumentiTipo, pk=tipo_id)
    set_breadcrumbs(
        request,
        [
            ("Documenti", reverse("documenti:home")),
            ("Nuovo documento", reverse("documenti:nuovo_dinamico")),
            (tipo.nome or str(tipo), None),
        ],
    )
    # Parametri preservati
    cliente_id = request.GET.get("cliente") or request.POST.get("cliente")
    fascicolo_id = request.GET.get("fascicolo") or request.POST.get("fascicolo")
    pratica_id = request.GET.get("pratica") or request.POST.get("pratica")

    if request.method == "POST":
        data = request.POST.copy()
        # preserva cliente se non presente nel POST
        if cliente_id and not data.get("cliente"):
            data["cliente"] = cliente_id
        if fascicolo_id and not data.get("fascicolo"):
            data["fascicolo"] = fascicolo_id
        form = DocumentoDinamicoForm(data, request.FILES, tipo=tipo)
        if form.is_valid():
            doc = form.save()
            messages.success(request, f"Documento creato: #{doc.id}")
            return redirect("documenti:dettaglio", pk=doc.pk)
    else:
        initial = {}
        if cliente_id:
            initial["cliente"] = cliente_id
        if fascicolo_id:
            initial["fascicolo"] = fascicolo_id
        # opzionale: se arrivi solo con pratica, puoi precompilare il fascicolo dopo scelta utente
        form = DocumentoDinamicoForm(tipo=tipo, initial=initial)

    return render(
        request,
        "documenti/nuovo_dinamico_tipo.html",
        {"form": form, "tipo": tipo, "cliente_id": cliente_id, "fascicolo_id": fascicolo_id, "pratica_id": pratica_id},
    )

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
    doc_label = doc.descrizione or f"Documento #{doc.pk}"
    set_breadcrumbs(
        request,
        [
            ("Documenti", reverse("documenti:home")),
            (doc_label, reverse("documenti:dettaglio", args=[doc.pk])),
            ("Modifica", None),
        ],
    )
    return render(request, "documenti/modifica_dinamico.html", {"form": form, "doc": doc, "tipo": tipo})

@login_required
def documento_dettaglio(request, pk: int):
    cliente_field = Documento._meta.get_field("cliente")
    cliente_rel_model = getattr(getattr(cliente_field, "remote_field", None), "model", None)
    doc_cliente_select = ["cliente"]
    if cliente_rel_model is Cliente:
        doc_cliente_select.append("cliente__anagrafica")

    doc = get_object_or_404(
        Documento.objects.select_related(*[*doc_cliente_select, "tipo"]),
        pk=pk,
    )

    mov_select = ["ubicazione"]
    try:
        mov_cliente_field = MovimentoProtocollo._meta.get_field("cliente")
        mov_cliente_model = getattr(getattr(mov_cliente_field, "remote_field", None), "model", None)
    except Exception:
        mov_cliente_field = None
        mov_cliente_model = None
    if mov_cliente_field:
        mov_select.append("cliente")
        if mov_cliente_model is Cliente:
            mov_select.append("cliente__anagrafica")

    movimenti = (
        MovimentoProtocollo.objects
        .filter(documento=doc)
        .select_related(*mov_select)
        .order_by("-data", "-id")
    )
    doc_label = doc.descrizione or f"Documento #{doc.pk}"
    set_breadcrumbs(
        request,
        [
            ("Documenti", reverse("documenti:home")),
            (doc_label, None),
        ],
    )
    return render(request, "documenti/dettaglio.html", {"doc": doc, "movimenti": movimenti})

@login_required
def home(request):
    # Ricerca documenti
    q = (request.GET.get("q") or "").strip()

    cliente_field = Documento._meta.get_field("cliente")
    cliente_rel_model = getattr(getattr(cliente_field, "remote_field", None), "model", None)
    doc_cliente_select = ["cliente"]
    if cliente_rel_model is Cliente:
        doc_cliente_select.append("cliente__anagrafica")

    # Ultimi 5 documenti
    ultimi_documenti = (
        Documento.objects.select_related(*[*doc_cliente_select, "tipo"])
        .order_by("-id")[:5]
    )

    # Clienti recenti
    recent_docs_for_clients = (
        Documento.objects.select_related(*doc_cliente_select).order_by("-id")[:50]
    )
    clienti_ids = []
    for d in recent_docs_for_clients:
        if d.cliente_id and d.cliente_id not in clienti_ids:
            clienti_ids.append(d.cliente_id)
    if clienti_ids:
        if cliente_rel_model is Cliente:
            qs_cli = Cliente.objects.select_related("anagrafica").filter(id__in=clienti_ids)
        else:
            qs_cli = Anagrafica.objects.filter(id__in=clienti_ids)
        lookup_cli = {c.id: c for c in qs_cli}
        clienti_recenti = []
        for cid in clienti_ids:
            cli = lookup_cli.get(cid)
            if not cli:
                continue
            if cliente_rel_model is Cliente:
                denominazione = getattr(cli, "denominazione", None)
                if not denominazione:
                    ana = getattr(cli, "anagrafica", None)
                    if ana and hasattr(ana, "display_name"):
                        denominazione = ana.display_name()
                clienti_recenti.append(denominazione or str(cli))
            else:
                denominazione = None
                if hasattr(cli, "display_name"):
                    denominazione = cli.display_name()
                elif hasattr(cli, "denominazione"):
                    denominazione = cli.denominazione
                clienti_recenti.append(denominazione or str(cli))
            if len(clienti_recenti) >= 5:
                break
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

    qs = Documento.objects.select_related(*[*doc_cliente_select, "tipo"]).all()

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

    mov_select_related = ["documento"]
    mov_cliente_field = None
    mov_cliente_model = None
    try:
        mov_cliente_field = MovimentoProtocollo._meta.get_field("cliente")
        mov_cliente_model = getattr(getattr(mov_cliente_field, "remote_field", None), "model", None)
    except Exception:
        mov_cliente_field = None
        mov_cliente_model = None
    if mov_cliente_field:
        mov_select_related.append("cliente")
        if mov_cliente_model is Cliente:
            mov_select_related.append("cliente__anagrafica")
    movimenti_recenti = (
        MovimentoProtocollo.objects
        .select_related(*mov_select_related)
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
    set_breadcrumbs(request, [("Documenti", None)])
    return render(request, "documenti/home.html", context)

@login_required
def documento_collocazione(request, pk: int):
    doc = get_object_or_404(Documento.objects.select_related("cliente", "cliente__anagrafica", "tipo"), pk=pk)
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
    doc_label = doc.descrizione or f"Documento #{doc.pk}"
    set_breadcrumbs(
        request,
        [
            ("Documenti", reverse("documenti:home")),
            (doc_label, reverse("documenti:dettaglio", args=[doc.pk])),
            ("Collocazione fisica", None),
        ],
    )
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

@require_POST
def protocolla_documento(request, pk: int):
    """
    Protocolla un documento:
    - tipo=entrata (default) accetta: da_chi, ubicazione (id UnitaFisica), causale, note
    - tipo=uscita accetta: a_chi, data_rientro_prevista (YYYY-MM-DD), causale, note
    """
    doc = get_object_or_404(Documento, pk=pk)
    tipo = (request.POST.get("tipo") or "entrata").lower()
    uf = None
    uf_id = request.POST.get("ubicazione")
    if uf_id:
        try:
            uf = UnitaFisica.objects.get(pk=int(uf_id))
        except Exception:
            uf = None

    def resolve_anagrafica(key: str):
        anagrafica_id = request.POST.get(key)
        if not anagrafica_id:
            return None
        try:
            return Anagrafica.objects.get(pk=int(anagrafica_id))
        except (Anagrafica.DoesNotExist, ValueError, TypeError):
            return None
    try:
        if tipo == "uscita":
            from datetime import datetime
            a_chi = request.POST.get("a_chi") or ""
            a_chi_anagrafica = resolve_anagrafica("a_chi_anagrafica")
            data_rp = request.POST.get("data_rientro_prevista") or ""
            data_rp = datetime.strptime(data_rp, "%Y-%m-%d").date() if data_rp else None
            MovimentoProtocollo.registra_uscita(
                documento=doc,
                quando=timezone.now(),
                operatore=request.user,
                a_chi=a_chi,
                destinatario_anagrafica=a_chi_anagrafica,
                data_rientro_prevista=data_rp,
                causale=request.POST.get("causale") or "",
                note=request.POST.get("note") or "",
                ubicazione=uf,
            )
            messages.success(request, "Uscita registrata.")
        else:
            da_chi = request.POST.get("da_chi") or ""
            da_chi_anagrafica = resolve_anagrafica("da_chi_anagrafica")
            MovimentoProtocollo.registra_entrata(
                documento=doc,
                quando=timezone.now(),
                operatore=request.user,
                da_chi=da_chi,
                destinatario_anagrafica=da_chi_anagrafica,
                ubicazione=uf,
                causale=request.POST.get("causale") or "",
                note=request.POST.get("note") or "",
            )
            messages.success(request, "Entrata registrata.")
    except Exception as ex:
        messages.error(request, f"Errore di protocollazione: {ex}")
    return redirect("documenti:dettaglio", pk=doc.pk)

@login_required
def nuovo(request, pk=None):
    initial = {}
    # Precompila da pratica/fascicolo (da URL o querystring)
    pratica_id = request.GET.get("pratica")
    fascicolo_id = request.GET.get("fascicolo") or pk  # se la tua URL è /documenti/nuovo/<fascicolo_pk>/
    src = None
    if pratica_id:
        src = Pratica.objects.select_related("cliente", "cliente__anagrafica").filter(pk=pratica_id).first()
    elif fascicolo_id:
        src = (
            Fascicolo.objects.select_related("cliente", "cliente__anagrafica")
            .prefetch_related("pratiche__cliente", "pratiche__cliente__anagrafica")
            .filter(pk=fascicolo_id)
            .first()
        )

    if src:
        initial["pratica"] = getattr(src, "pratica", src) if isinstance(src, Fascicolo) else src
        # Adatta il tipo del campo cliente del Documento
        try:
            fk_model = Documento._meta.get_field("cliente").remote_field.model
            src_cli = getattr(src, "cliente", None)
            if not src_cli and isinstance(src, Fascicolo):
                p = getattr(src, "pratica", None)
                src_cli = getattr(p, "cliente", None) if p else None
            if not src_cli and isinstance(src, Fascicolo):
                for p in src.pratiche.all():
                    if getattr(p, "cliente", None):
                        src_cli = p.cliente
                        break
            if src_cli:
                initial["cliente"] = src_cli if fk_model._meta.model_name == "cliente" else getattr(src_cli, "anagrafica", None)
        except Exception:
            pass
        if isinstance(src, Fascicolo):
            initial["fascicolo"] = src

    if request.method == "POST":
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            messages.success(request, "Documento creato.")
            return redirect(obj.get_absolute_url() if hasattr(obj, "get_absolute_url") else reverse("documenti:dettaglio", args=[obj.pk]))
    else:
        form = DocumentoForm(initial=initial)
    return render(request, "documenti/form.html", {"form": form})


# ============================================================================
# IMPORTAZIONE UNILAV
# ============================================================================

@login_required
def importa_unilav(request):
    """
    View per importazione UNILAV - Step 1: Upload PDF e anteprima dati estratti
    """
    breadcrumb_chain = [
        ("Documenti", reverse("documenti:home")),
        ("Importa UNILAV", None),
    ]
    set_breadcrumbs(request, breadcrumb_chain)
    
    if request.method == "POST" and request.FILES.get("file"):
        # Step 1: Analizza PDF e mostra anteprima
        pdf_file = request.FILES["file"]
        
        # Validazione file
        if not pdf_file.name.lower().endswith('.pdf'):
            messages.error(request, "Il file deve essere in formato PDF")
            return render(request, "documenti/importa_unilav.html", {"error": "Il file deve essere in formato PDF"})
        
        max_size = 10 * 1024 * 1024  # 10MB
        if pdf_file.size > max_size:
            messages.error(request, f"Il file è troppo grande ({pdf_file.size / 1024 / 1024:.1f}MB). Massimo 10MB")
            return render(request, "documenti/importa_unilav.html", {
                "error": f"Il file è troppo grande ({pdf_file.size / 1024 / 1024:.1f}MB). Dimensione massima: 10MB"
            })
        
        # Salva temporaneamente il file
        import tempfile
        import os
        
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, pdf_file.name)
        
        with open(temp_path, 'wb+') as destination:
            for chunk in pdf_file.chunks():
                destination.write(chunk)
        
        try:
            # Parse PDF
            from .parsers.unilav_parser import parse_unilav_pdf
            parsed_data = parse_unilav_pdf(temp_path)
            
            # Prepara dati per il template
            datore_data = parsed_data['datore']
            cf_datore = datore_data['codice_fiscale']
            tipo_datore = 'PF' if len(cf_datore) == 16 else 'PG'
            
            datore_preview = {
                'codice_fiscale': cf_datore,
                'tipo': tipo_datore,
                'crea_se_non_esiste': True,
                'crea_cliente': True,
            }
            
            if tipo_datore == 'PG':
                datore_preview['ragione_sociale'] = datore_data['denominazione']
            else:
                parti = datore_data['denominazione'].split(' ', 1)
                datore_preview['cognome'] = parti[0] if len(parti) > 0 else datore_data['denominazione']
                datore_preview['nome'] = parti[1] if len(parti) > 1 else ''
            
            datore_preview.update({
                'email': datore_data.get('email'),
                'telefono': datore_data.get('telefono'),
                'comune': datore_data.get('comune_sede_legale'),
                'cap': datore_data.get('cap_sede_legale'),
                'indirizzo': datore_data.get('indirizzo_sede_legale'),
            })
            
            # Verifica esistenza datore
            try:
                anagrafica_datore = Anagrafica.objects.get(codice_fiscale=cf_datore)
                datore_preview['esiste'] = True
                datore_preview['anagrafica_id'] = anagrafica_datore.id
                try:
                    cliente_datore = Cliente.objects.get(anagrafica=anagrafica_datore)
                    datore_preview['cliente_id'] = cliente_datore.id
                except Cliente.DoesNotExist:
                    datore_preview['cliente_id'] = None
            except Anagrafica.DoesNotExist:
                datore_preview['esiste'] = False
                datore_preview['anagrafica_id'] = None
                datore_preview['cliente_id'] = None
            
            # Lavoratore
            lavoratore_data = parsed_data['lavoratore']
            cf_lavoratore = lavoratore_data['codice_fiscale']
            
            lavoratore_preview = {
                'codice_fiscale': cf_lavoratore,
                'tipo': 'PF',
                'cognome': lavoratore_data['cognome'],
                'nome': lavoratore_data['nome'],
                'sesso': lavoratore_data.get('sesso'),
                'data_nascita': lavoratore_data.get('data_nascita'),
                'comune_nascita': lavoratore_data.get('comune_nascita'),
                'comune': lavoratore_data.get('comune_domicilio'),
                'cap': lavoratore_data.get('cap_domicilio'),
                'indirizzo': lavoratore_data.get('indirizzo_domicilio'),
                'crea_se_non_esiste': True,
                'crea_cliente': False,
            }
            
            # Verifica esistenza lavoratore
            try:
                anagrafica_lavoratore = Anagrafica.objects.get(codice_fiscale=cf_lavoratore)
                lavoratore_preview['esiste'] = True
                lavoratore_preview['anagrafica_id'] = anagrafica_lavoratore.id
            except Anagrafica.DoesNotExist:
                lavoratore_preview['esiste'] = False
                lavoratore_preview['anagrafica_id'] = None
            
            # Documento UNILAV
            unilav_data = parsed_data['unilav']
            
            documento_preview = {
                'codice_comunicazione': unilav_data['codice_comunicazione'],
                'tipo_comunicazione': unilav_data.get('tipo_comunicazione'),
                'data_comunicazione': unilav_data['data_comunicazione'],
                'dipendente': lavoratore_preview.get('anagrafica_id'),
                'tipo': unilav_data.get('tipologia_contrattuale'),
                'data_da': unilav_data.get('data_inizio_rapporto'),
                'data_a': unilav_data.get('data_fine_rapporto'),
                'qualifica': unilav_data.get('qualifica_professionale'),
                'contratto_collettivo': unilav_data.get('contratto_collettivo'),
                'livello': unilav_data.get('livello_inquadramento'),
                'retribuzione': unilav_data.get('retribuzione'),
                'ore_settimanali': unilav_data.get('ore_settimanali'),
                'tipo_orario': unilav_data.get('tipo_orario'),
            }
            
            preview_data = {
                'datore': datore_preview,
                'lavoratore': lavoratore_preview,
                'documento': documento_preview,
                'file_temp_path': temp_path,
            }
            
            return render(request, "documenti/importa_unilav.html", {
                "preview_data": preview_data
            })
            
        except Exception as e:
            # Pulizia file temporaneo in caso di errore
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
            
            messages.error(request, f"Errore nell'analisi del PDF: {str(e)}")
            return render(request, "documenti/importa_unilav.html", {
                "error": f"Errore nell'analisi del PDF: {str(e)}"
            })
    
    # GET: Mostra form upload
    return render(request, "documenti/importa_unilav.html", {})


@login_required
@require_POST
def importa_unilav_confirm(request):
    """
    View per importazione UNILAV - Step 2: Conferma e salvataggio definitivo
    """
    import os
    from datetime import datetime
    
    file_path = request.POST.get('file_path')
    
    # Verifica che il file temporaneo esista ancora
    if not file_path or not os.path.exists(file_path):
        messages.error(request, "File temporaneo non trovato. Ricarica il PDF.")
        return redirect("documenti:importa_unilav")
    
    try:
        # Estrai dati dal form
        datore_data = {
            'codice_fiscale': request.POST.get('datore_codice_fiscale'),
            'tipo': request.POST.get('datore_tipo'),
            'ragione_sociale': request.POST.get('datore_ragione_sociale', ''),
            'cognome': request.POST.get('datore_cognome', ''),
            'nome': request.POST.get('datore_nome', ''),
            'email': request.POST.get('datore_email', ''),
            'telefono': request.POST.get('datore_telefono', ''),
            'comune': request.POST.get('datore_comune', ''),
            'cap': request.POST.get('datore_cap', ''),
            'indirizzo': request.POST.get('datore_indirizzo', ''),
        }
        
        lavoratore_data = {
            'codice_fiscale': request.POST.get('lavoratore_codice_fiscale'),
            'tipo': 'PF',
            'cognome': request.POST.get('lavoratore_cognome'),
            'nome': request.POST.get('lavoratore_nome'),
            'sesso': request.POST.get('lavoratore_sesso', ''),
            'data_nascita': request.POST.get('lavoratore_data_nascita') or None,
            'comune_nascita': request.POST.get('lavoratore_comune_nascita', ''),
            'comune': request.POST.get('lavoratore_comune', ''),
            'cap': request.POST.get('lavoratore_cap', ''),
            'indirizzo': request.POST.get('lavoratore_indirizzo', ''),
        }
        
        documento_data = {
            'codice_comunicazione': request.POST.get('doc_codice_comunicazione'),
            'tipo_comunicazione': request.POST.get('doc_tipo_comunicazione', ''),
            'data_comunicazione': request.POST.get('doc_data_comunicazione'),
            'tipo': request.POST.get('doc_tipo', ''),
            'data_da': request.POST.get('doc_data_da') or None,
            'data_a': request.POST.get('doc_data_a') or None,
            'qualifica': request.POST.get('doc_qualifica', ''),
            'contratto_collettivo': request.POST.get('doc_contratto_collettivo', ''),
            'livello': request.POST.get('doc_livello', ''),
            'retribuzione': request.POST.get('doc_retribuzione', ''),
            'ore_settimanali': request.POST.get('doc_ore_settimanali', ''),
            'tipo_orario': request.POST.get('doc_tipo_orario', ''),
        }
        
        with transaction.atomic():
            # 1. Crea/Aggiorna datore
            anagrafica_datore, _ = Anagrafica.objects.get_or_create(
                codice_fiscale=datore_data['codice_fiscale'],
                defaults={
                    'tipo': datore_data['tipo'],
                    'ragione_sociale': datore_data['ragione_sociale'],
                    'cognome': datore_data['cognome'],
                    'nome': datore_data['nome'],
                }
            )
            
            cliente_datore, _ = Cliente.objects.get_or_create(
                anagrafica=anagrafica_datore
            )
            
            # 2. Crea/Aggiorna lavoratore
            anagrafica_lavoratore, _ = Anagrafica.objects.get_or_create(
                codice_fiscale=lavoratore_data['codice_fiscale'],
                defaults={
                    'tipo': 'PF',
                    'cognome': lavoratore_data['cognome'],
                    'nome': lavoratore_data['nome'],
                    'sesso': lavoratore_data['sesso'],
                    'data_nascita': lavoratore_data['data_nascita'],
                }
            )
            
            # 3. Verifica tipo UNILAV
            try:
                tipo_unilav = DocumentiTipo.objects.get(codice='UNILAV')
            except DocumentiTipo.DoesNotExist:
                messages.error(request, "Tipo documento UNILAV non configurato. Contatta l'amministratore.")
                return redirect("documenti:importa_unilav")
            
            # 4. Crea documento
            descrizione = f"UNILAV {documento_data['codice_comunicazione']} - {anagrafica_lavoratore.denominazione}"
            
            documento = Documento.objects.create(
                tipo=tipo_unilav,
                cliente=cliente_datore,
                descrizione=descrizione,
                data_documento=documento_data['data_comunicazione'],
                digitale=True,
                tracciabile=True,
                stato='definitivo',
            )
            
            # 5. Salva file PDF
            with open(file_path, 'rb') as f:
                from django.core.files import File
                documento.file.save(
                    os.path.basename(file_path),
                    File(f),
                    save=True
                )
            
            # 6. Salva attributi dinamici
            from .models import AttributoValore, AttributoDefinizione
            
            attributi_map = {
                'dipendente': anagrafica_lavoratore.id,
                'tipo': documento_data.get('tipo'),
                'data_comunicazione': documento_data.get('data_comunicazione'),
                'data_da': documento_data.get('data_da'),
                'data_a': documento_data.get('data_a'),
            }
            
            for codice_attr, valore in attributi_map.items():
                if valore is not None:
                    try:
                        definizione = AttributoDefinizione.objects.get(
                            tipo_documento=tipo_unilav,
                            codice=codice_attr
                        )
                        
                        AttributoValore.objects.create(
                            documento=documento,
                            definizione=definizione,
                            valore=valore
                        )
                    except AttributoDefinizione.DoesNotExist:
                        pass
            
            # Aggiungi dati extra nelle note
            note_extra = []
            if documento_data.get('qualifica'):
                note_extra.append(f"Qualifica: {documento_data['qualifica']}")
            if documento_data.get('contratto_collettivo'):
                note_extra.append(f"CCNL: {documento_data['contratto_collettivo']}")
            if documento_data.get('livello'):
                note_extra.append(f"Livello: {documento_data['livello']}")
            if documento_data.get('retribuzione'):
                note_extra.append(f"Retribuzione: {documento_data['retribuzione']}")
            if documento_data.get('ore_settimanali'):
                note_extra.append(f"Ore settimanali: {documento_data['ore_settimanali']}")
            if documento_data.get('tipo_orario'):
                note_extra.append(f"Tipo orario: {documento_data['tipo_orario']}")
            
            if note_extra:
                documento.note = '\n'.join(note_extra)
                documento.save()
            
            # Pulizia file temporaneo
            try:
                os.remove(file_path)
                temp_dir = os.path.dirname(file_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass
            
            messages.success(request, f"✓ UNILAV importato con successo! Documento #{documento.id}")
            return render(request, "documenti/importa_unilav.html", {
                "success": True,
                "documento_id": documento.id
            })
            
    except Exception as e:
        # Pulizia file temporaneo in caso di errore
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            temp_dir = os.path.dirname(file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass
        
        messages.error(request, f"Errore nell'importazione: {str(e)}")
        return redirect("documenti:importa_unilav")

