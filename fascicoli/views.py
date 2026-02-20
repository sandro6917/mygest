from django.db.models import Q, Max
from django.db import DatabaseError, transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.db.utils import OperationalError
from django.views.decorators.http import require_POST
from .models import Fascicolo
from .forms import FascicoloForm
from protocollo.models import MovimentoProtocollo
from archivio_fisico.models import UnitaFisica
from pathlib import Path
from django.http import Http404, FileResponse
from django.utils import timezone
import mimetypes
from pratiche.models import Pratica
from anagrafiche.models import Cliente, Anagrafica
from urllib.parse import urlencode
from django.core.exceptions import ValidationError

from mygest.breadcrumbs import set_breadcrumbs

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
    # pratica di contesto (se si arriva dal dettaglio pratica)
    pratica_ctx = None
    pratica_id = request.GET.get("pratica") or request.POST.get("pratica")
    if pratica_id:
        pratica_ctx = Pratica.objects.select_related("cliente").filter(pk=pratica_id).first()
        if pratica_ctx and pratica_ctx.cliente_id and "cliente" not in initial:
            initial["cliente"] = pratica_ctx.cliente
    if request.method == "POST":
        form = FascicoloForm(request.POST, request.FILES, pratica=pratica_ctx)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Fascicolo creato (#{obj.pk}).")
            return redirect(_fascicolo_success_url(obj))
    else:
        form = FascicoloForm(initial=initial, pratica=pratica_ctx)
    context = {"form": form, "is_create": True, "pratica_ctx": pratica_ctx}
    set_breadcrumbs(
        request,
        [
            ("Fascicoli", reverse("fascicoli:home")),
            ("Nuovo fascicolo", None),
        ],
    )
    return render(request, "fascicoli/form.html", context)

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
        # Movimenti di protocollo recenti
        movimenti_recenti = (
            MovimentoProtocollo.objects
            .select_related("documento", "fascicolo", "cliente")
            .order_by("-data")[:20]
        )

    except OperationalError:
        # DB non allineato: evita il 500
        ultimi_fascicoli = []
        fascicoli_filtrati = []
        fascicoli_total = 0
        ultimi_tipi = []
        movimenti_recenti = []

    set_breadcrumbs(request, [("Fascicoli", None)])
    return render(request, "fascicoli/home.html", {
        "q": q,
        "ultimi_fascicoli": ultimi_fascicoli,
        "fascicoli_filtrati": fascicoli_filtrati,
        "fascicoli_total": fascicoli_total,
        "ultimi_tipi": ultimi_tipi,
        "movimenti_recenti": movimenti_recenti,
    })

class FascicoloDetailView(DetailView):
    model = Fascicolo
    template_name = "fascicoli/fascicolo_detail.html"
    context_object_name = "fascicolo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        f = self.object

        # Documenti collegati
        from documenti.models import Documento
        ctx["documenti"] = (
            Documento.objects.filter(fascicolo=f)
            .select_related("cliente", "titolario_voce", "tipo")
            .order_by("-creato_il")[:50]
        )

        # Gerarchia
        ctx["parent"] = getattr(f, "parent", None)
        # Usa il manager corretto: 'sottofascicoli' è il reverse del FK self-referenziato 'parent'
        children_mgr = getattr(f, "children", None) or getattr(f, "sottofascicoli", f.__class__.objects.none())
        ctx["children"] = children_mgr.all()

        # Fascicoli collegabili: stesso cliente, titolario, anno, nessun parent, escludi se stesso
        ctx["fascicoli_collegabili"] = (
            Fascicolo.objects.filter(
                cliente=f.cliente,
                titolario_voce=f.titolario_voce,
                anno=f.anno,
                parent__isnull=True
            )
            .exclude(pk=f.pk)
            .select_related("titolario_voce")
            .order_by("-progressivo")[:20]
        )

        # Pratiche correlate (M2M)
        ctx["pratiche"] = f.pratiche.select_related("tipo", "cliente").all()[:50]

        # Movimenti di protocollo: sia quelli del fascicolo, sia quelli dei documenti del fascicolo
        from protocollo.models import MovimentoProtocollo
        ctx["movimenti"] = (
            MovimentoProtocollo.objects.filter(Q(fascicolo=f) | Q(documento__fascicolo=f))
            .select_related("documento", "operatore")
            .order_by("-data")
            .distinct()
        )

        search_query = (self.request.GET.get("search") or "").strip()
        ctx["search_query"] = search_query
        ctx["fascicoli_search_results"] = []
        if search_query:
            field_names = {
                field.name for field in Fascicolo._meta.get_fields()
                if getattr(field, "concrete", False)
            }
            searchable = [name for name in ("codice", "titolo", "oggetto") if name in field_names]
            if searchable:
                qs = Fascicolo.objects.exclude(pk=f.pk)
                cond = Q()
                for name in searchable:
                    cond |= Q(**{f"{name}__icontains": search_query})
                qs = qs.filter(cond)
                ctx["fascicoli_search_results"] = list(_order(qs)[:10])
        fascicolo_label = getattr(f, "titolo", "") or getattr(f, "codice", "") or f"Fascicolo #{f.pk}"
        set_breadcrumbs(
            self.request,
            [
                ("Fascicoli", reverse("fascicoli:home")),
                (fascicolo_label, None),
            ],
        )
        ctx["breadcrumbs"] = self.request.breadcrumbs
        return ctx

@require_POST
@login_required
def protocolla_fascicolo(request, pk: int):
    fascicolo = get_object_or_404(Fascicolo, pk=pk)

    direction_raw = (request.POST.get("tipo") or request.POST.get("direzione") or "IN").strip().upper()
    is_uscita = direction_raw in ("OUT", "USCITA")

    quando_raw = request.POST.get("quando")
    quando = timezone.now()
    if quando_raw:
        from datetime import datetime

        try:
            parsed = datetime.fromisoformat(quando_raw)
            if timezone.is_naive(parsed):
                parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
            quando = parsed
        except ValueError:
            messages.warning(request, "Formato data non riconosciuto; uso data/ora corrente.")

    uf = None
    uf_id = request.POST.get("ubicazione")
    if uf_id:
        try:
            uf = UnitaFisica.objects.get(pk=int(uf_id))
        except (ValueError, UnitaFisica.DoesNotExist):
            messages.warning(request, "Ubicazione non trovata; sarà ignorata.")
            uf = None

    try:
        if is_uscita:
            a_chi = request.POST.get("a_chi") or ""
            data_rientro_raw = request.POST.get("data_rientro_prevista") or ""
            data_rientro = None
            if data_rientro_raw:
                from datetime import datetime

                try:
                    data_rientro = datetime.strptime(data_rientro_raw, "%Y-%m-%d").date()
                except ValueError:
                    messages.warning(request, "Data di rientro non valida; sarà ignorata.")

            MovimentoProtocollo.registra_uscita(
                fascicolo=fascicolo,
                quando=quando,
                operatore=request.user,
                a_chi=a_chi,
                data_rientro_prevista=data_rientro,
                causale=request.POST.get("causale") or "",
                note=request.POST.get("note") or "",
                ubicazione=uf,
            )
            messages.success(request, "Uscita registrata.")
        else:
            da_chi = request.POST.get("da_chi") or ""
            MovimentoProtocollo.registra_entrata(
                fascicolo=fascicolo,
                quando=quando,
                operatore=request.user,
                da_chi=da_chi,
                ubicazione=uf,
                causale=request.POST.get("causale") or "",
                note=request.POST.get("note") or "",
            )
            messages.success(request, "Entrata registrata.")
    except Exception as ex:
        messages.error(request, f"Errore nella protocollazione: {ex}")
    return redirect("fascicoli:detail", pk=fascicolo.pk)

def _safe_join(base: Path, sub: str) -> Path:
    base = base.resolve()
    target = (base / (sub or "")).resolve()
    if not str(target).startswith(str(base)):
        raise Http404("Percorso non valido")
    return target

@login_required
def archivio_browse(request, pk: int, subpath: str = ""):
    fascicolo = get_object_or_404(Fascicolo, pk=pk)
    if not fascicolo.path_archivio:
        raise Http404("Archivio non configurato per il fascicolo")
    base_dir = Path(fascicolo.path_archivio)
    if not base_dir.exists() or not base_dir.is_dir():
        raise Http404("Cartella archivio inesistente")

    current_dir = _safe_join(base_dir, subpath)
    if not current_dir.is_dir():
        raise Http404("Percorso non è una cartella")

    entries = []
    try:
        for p in sorted(current_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            stat = p.stat()
            entries.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "size": stat.st_size,
                "mtime": timezone.make_aware(timezone.datetime.fromtimestamp(stat.st_mtime), timezone=timezone.get_current_timezone(), is_dst=None) if timezone.is_naive(timezone.datetime.now()) else timezone.datetime.fromtimestamp(stat.st_mtime, tz=timezone.get_current_timezone()),
                "dir_url": None if not p.is_dir() else (
                    request.build_absolute_uri(
                        request.path.rstrip("/") + "/" + p.name + "/"
                    )
                ),
                "file_url": None if p.is_dir() else (
                    request.build_absolute_uri(
                        request.build_absolute_uri(
                            request.path.rstrip("/")
                        ).replace("/archivio/", "/archivio/file/") + "/" + p.name
                    )
                ),
            })
    except PermissionError:
        entries = []

    up_link = None
    if subpath:
        parent_sub = "/".join(subpath.rstrip("/").split("/")[:-1])
        up_link = request.build_absolute_uri(
            request.path.replace(subpath, parent_sub).rstrip("/") + "/"
        )

    ctx = {
        "fascicolo": fascicolo,
        "base_dir": str(base_dir),
        "current_dir": str(current_dir),
        "subpath": subpath,
        "entries": entries,
        "up_link": up_link,
    }
    fascicolo_label = getattr(fascicolo, "titolo", "") or getattr(fascicolo, "codice", "") or f"Fascicolo #{fascicolo.pk}"
    crumbs = [
        ("Fascicoli", reverse("fascicoli:home")),
        (fascicolo_label, reverse("fascicoli:detail", args=[fascicolo.pk])),
        ("Archivio", reverse("fascicoli:archivio", args=[fascicolo.pk])),
    ]
    if subpath:
        parts = [p for p in subpath.strip("/").split("/") if p]
        cumulative = []
        for part in parts:
            cumulative.append(part)
            partial_path = "/".join(cumulative)
            crumbs.append((part, reverse("fascicoli:archivio_sub", args=[fascicolo.pk, partial_path])))
    set_breadcrumbs(request, crumbs)
    return render(request, "fascicoli/archivio_browse.html", ctx)

@login_required
def archivio_download(request, pk: int, subpath: str):
    fascicolo = get_object_or_404(Fascicolo, pk=pk)
    if not fascicolo.path_archivio:
        raise Http404
    base_dir = Path(fascicolo.path_archivio)
    file_path = _safe_join(base_dir, subpath)
    if not file_path.exists() or not file_path.is_file():
        raise Http404
    ctype, _ = mimetypes.guess_type(file_path.name)
    return FileResponse(open(file_path, "rb"), content_type=ctype or "application/octet-stream")

@login_required
@require_POST
def fascicolo_collega(request, pk: int):
    fascicolo = get_object_or_404(Fascicolo, pk=pk)
    target_id = request.POST.get("target_id")
    redirect_url = reverse("fascicoli:detail", args=[fascicolo.pk])
    search = (request.POST.get("search") or "").strip()
    if search:
        redirect_url = f"{redirect_url}?{urlencode({'search': search})}"

    try:
        target_id = int(target_id)
    except (TypeError, ValueError):
        messages.error(request, "Selezione non valida.")
        return redirect(redirect_url)

    if target_id == fascicolo.pk:
        messages.warning(request, "Non puoi collegare il fascicolo a sé stesso.")
        return redirect(redirect_url)

    target = Fascicolo.objects.filter(pk=target_id).first()
    if not target:
        messages.error(request, "Fascicolo da collegare non trovato.")
        return redirect(redirect_url)

    # Validazione business rules: cliente, titolario, anno devono coincidere
    if target.cliente_id != fascicolo.cliente_id:
        messages.error(request, f"Impossibile collegare: il cliente del fascicolo {target.codice} non coincide.")
        return redirect(redirect_url)
    
    if target.titolario_voce_id != fascicolo.titolario_voce_id:
        messages.error(request, f"Impossibile collegare: la voce di titolario del fascicolo {target.codice} non coincide.")
        return redirect(redirect_url)
    
    if target.anno != fascicolo.anno:
        messages.error(request, f"Impossibile collegare: l'anno del fascicolo {target.codice} non coincide.")
        return redirect(redirect_url)

    # Verifica che il target non abbia già un parent
    if target.parent_id:
        messages.error(request, f"Il fascicolo {target.codice} è già collegato ad un altro fascicolo.")
        return redirect(redirect_url)

    ancestor = fascicolo
    while ancestor.parent_id:
        if ancestor.parent_id == target.pk:
            messages.error(request, "Collegamento non valido: creerebbe un ciclo.")
            return redirect(redirect_url)
        ancestor = ancestor.parent

    updates = {"parent_id": fascicolo.pk}
    refresh_fields = ["parent"]

    if hasattr(target, "progressivo"):
        # reset progressivo to neutral value so the record satisfies NOT NULL constraint
        updates["progressivo"] = 0
        refresh_fields.append("progressivo")

    if hasattr(target, "sub_progressivo"):
        max_sub = (
            Fascicolo.objects.filter(parent=fascicolo)
            .exclude(pk=target.pk)
            .aggregate(Max("sub_progressivo"))
            .get("sub_progressivo__max") or 0
        )
        updates["sub_progressivo"] = max_sub + 1
        refresh_fields.append("sub_progressivo")

    try:
        with transaction.atomic():
            Fascicolo.objects.filter(pk=target.pk).update(**updates)
    except DatabaseError as exc:
        messages.error(request, f"Collegamento non riuscito: {exc}")
        return redirect(redirect_url)

    target.refresh_from_db(fields=refresh_fields)

    codice = getattr(target, "codice", None) or target.pk
    messages.success(request, f"Fascicolo {codice} collegato come sottofascicolo.")
    return redirect(redirect_url)

@login_required
def fascicolo_modifica(request, pk: int):
    fascicolo = get_object_or_404(Fascicolo, pk=pk)
    pratica_ctx = getattr(fascicolo, "pratica", None)
    if request.method == "POST":
        form = FascicoloForm(request.POST, request.FILES, instance=fascicolo)
        if form.is_valid():
            fascicolo = form.save()
            messages.success(request, "Fascicolo aggiornato con successo.")
            return redirect(_fascicolo_success_url(fascicolo))
        messages.error(request, "Correggi gli errori indicati.")
    else:
        form = FascicoloForm(instance=fascicolo)

    context = {"form": form, "is_create": False, "fascicolo": fascicolo, "pratica_ctx": pratica_ctx}
    set_breadcrumbs(
        request,
        [
            ("Fascicoli", reverse("fascicoli:home")),
            (fascicolo, _detail_url(fascicolo)),
            ("Modifica fascicolo", None),
        ],
    )
    return render(request, "fascicoli/form.html", context)
