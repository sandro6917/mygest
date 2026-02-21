from __future__ import annotations
import os
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, NoReverseMatch
from django.conf import settings

from mygest.breadcrumbs import set_breadcrumbs

# Import corretti delle app top-level
from anagrafiche.models import Anagrafica
from documenti.models import Documento
from pratiche.models import Pratica
from scadenze.models import ScadenzaOccorrenza
from fascicoli.models import Fascicolo

HELP_TOPICS = {
    "guida-principianti": {
        "name": "Guida principianti",
        "summary": "Setup completo e workflow per backend e frontend.",
        "template": "help/guida_principianti.html",
        "order": 0,
    },
    "anagrafiche": {
        "name": "Anagrafiche",
        "summary": "Gestione dei soggetti con dati fiscali e recapiti.",
        "template": "help/anagrafiche.html",
    },
    "documenti": {
        "name": "Documenti",
        "summary": "Archivio digitale con protocollazione e storage NAS.",
        "template": "help/documenti.html",
    },
    "comunicazioni": {
        "name": "Comunicazioni",
        "summary": "Creazione, invio e protocollazione dei messaggi verso i clienti.",
        "template": "help/comunicazioni.html",
    },
    "fascicoli": {
        "name": "Fascicoli",
        "summary": "Pratiche aggreganti documenti e protocolli per cliente.",
        "template": "help/fascicoli.html",
    },
    "pratiche": {
        "name": "Pratiche",
        "summary": "Workflow operativo con scadenze e stato di avanzamento.",
        "template": "help/pratiche.html",
    },
    "archivio_fisico": {
        "name": "Archivio fisico",
        "summary": "Tracciamento collocazione fisica di documenti e fascicoli.",
        "template": "help/archivio_fisico.html",
    },
    "protocollo": {
        "name": "Protocollo",
        "summary": "Movimentazione IN/OUT con numerazione progressiva per cliente.",
        "template": "help/protocollo.html",
    },
    "guida-scadenze": {
        "name": "Guida app Scadenze",
        "summary": "Passaggi essenziali backend/frontend con esempi pratici.",
        "template": "help/guida_scadenze.html",
        "order": 1,
    },
    "guida-deployment": {
        "name": "Guida Deployment e Sincronizzazione",
        "summary": "Deployment automatico/manuale, sincronizzazione DB e gestione archivio NAS.",
        "template": "help/guida_deployment.html",
        "order": 2,
    },
}

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
    """
    Serve React SPA in production.
    In development (DEBUG=True), shows Django debug page with recent entries.
    """
    return react_spa(request)


def react_spa(request):
    """
    Serve React SPA for all non-API routes in production.
    This allows React Router to handle client-side routing.
    """
    if not settings.DEBUG:
        # Production: serve React frontend
        frontend_index = os.path.join(settings.BASE_DIR, 'frontend', 'dist', 'index.html')
        if os.path.exists(frontend_index):
            with open(frontend_index, 'r', encoding='utf-8') as f:
                return HttpResponse(f.read(), content_type='text/html')
        else:
            return HttpResponse(
                '<h1>Frontend not built</h1>'
                '<p>Run: cd frontend && npm install && npm run build</p>',
                status=503
            )
    
    # Development: show Django debug page
    pratiche_qs = _order(Pratica.objects.all())[:10]
    documenti_qs = _order(Documento.objects.all())[:10]
    fascicoli_qs = _order(Fascicolo.objects.all())[:10]
    anagrafiche_qs = _order(Anagrafica.objects.all())[:10]
    scadenze_qs = (
        ScadenzaOccorrenza.objects.select_related("scadenza")
        .prefetch_related("scadenza__pratiche")
        .filter(
            stato__in=[
                ScadenzaOccorrenza.Stato.PENDENTE,
                ScadenzaOccorrenza.Stato.PROGRAMMATA,
            ]
        )
        .order_by("inizio")[:10]
    )

    ctx = {
        "pratiche": [(o, _detail_url(o)) for o in pratiche_qs],
        "documenti": [(o, _detail_url(o)) for o in documenti_qs],
        "fascicoli": [(o, _detail_url(o)) for o in fascicoli_qs],
        "anagrafiche": [(o, _detail_url(o)) for o in anagrafiche_qs],
        "scadenze": [
            (occ, reverse("scadenze:detail", args=[occ.scadenza_id]))
            for occ in scadenze_qs
        ],
    }
    set_breadcrumbs(request, [])
    return render(request, "home.html", ctx)


def help_index(request):
    topics = [
        {
            "slug": slug,
            "name": data["name"],
            "summary": data["summary"],
        }
        for slug, data in sorted(
            HELP_TOPICS.items(),
            key=lambda item: (item[1].get("order", 100), item[1]["name"].lower()),
        )
    ]
    set_breadcrumbs(
        request,
        [
            ("Help", None),
        ],
    )
    return render(request, "help/index.html", {"topics": topics})


def help_topic(request, slug: str):
    topic = HELP_TOPICS.get(slug)
    if not topic:
        raise Http404("Sezione di help non disponibile")
    set_breadcrumbs(
        request,
        [
            ("Help", reverse("help-index")),
            (topic["name"], None),
        ],
    )
    other_topics = [
        {
            "slug": other_slug,
            "name": other_data["name"],
        }
        for other_slug, other_data in HELP_TOPICS.items()
        if other_slug != slug
    ]
    return render(
        request,
        topic["template"],
        {
            "topic": topic,
            "topics": other_topics,
        },
    )

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
    fascicoli = list(_order(Fascicolo.objects.filter(fascicoli_q).prefetch_related("pratiche"))[:10])

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
    set_breadcrumbs(
        request,
        [
            ("Anagrafiche", reverse("anagrafiche:home")),
            (str(obj), None),
        ],
    )
    return render(request, "anagrafiche/detail.html", ctx)

def serve_deployment_guide_html(request):
    """Serve la guida deployment come HTML"""
    html_path = os.path.join(settings.BASE_DIR, 'docs', 'GUIDA_DEPLOYMENT_SYNC.html')
    
    if not os.path.exists(html_path):
        raise Http404("Guida non trovata")
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return HttpResponse(content, content_type='text/html')


def serve_deployment_guide_pdf(request):
    """Serve la guida deployment come PDF"""
    pdf_path = os.path.join(settings.BASE_DIR, 'docs', 'GUIDA_DEPLOYMENT_SYNC.pdf')
    
    if not os.path.exists(pdf_path):
        raise Http404("Guida PDF non trovata")
    
    with open(pdf_path, 'rb') as f:
        content = f.read()
    
    response = HttpResponse(content, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="MyGest_Guida_Deployment.pdf"'
    return response
