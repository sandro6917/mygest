from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from .forms import ProtocolloForm
from .models import MovimentoProtocollo
from fascicoli.models import Fascicolo
from documenti.models import Documento
from archivio_fisico.models import UnitaFisica

@require_http_methods(["GET", "POST"])
@login_required
def protocolla_fascicolo(request, pk: int):
    f = get_object_or_404(Fascicolo, pk=pk)
    post_url = reverse("fascicoli:protocolla", args=[f.pk])

    if request.method == "POST":
        data = request.POST.copy()
        data.setdefault("direzione", "IN")
        form = ProtocolloForm(data=data, target=f)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                if cd["direzione"] == "OUT":
                    MovimentoProtocollo.registra_uscita(
                        fascicolo=f,
                        quando=cd["quando"],
                        operatore=request.user,
                        a_chi=cd.get("a_chi") or "",
                        data_rientro_prevista=cd.get("data_rientro_prevista"),
                        causale=cd.get("causale") or "",
                        note=cd.get("note") or "",
                        ubicazione=cd.get("ubicazione") if isinstance(cd.get("ubicazione"), UnitaFisica) else None,
                    )
                    messages.success(request, "Uscita registrata.")
                else:
                    MovimentoProtocollo.registra_entrata(
                        fascicolo=f,
                        quando=cd["quando"],
                        operatore=request.user,
                        da_chi=cd.get("da_chi") or "",
                        ubicazione=cd.get("ubicazione") if isinstance(cd.get("ubicazione"), UnitaFisica) else None,
                        causale=cd.get("causale") or "",
                        note=cd.get("note") or "",
                    )
                    messages.success(request, "Entrata registrata.")
                return redirect("fascicoli:detail", pk=f.pk)
            except Exception as ex:
                messages.error(request, f"Errore nella protocollazione: {ex}")
    else:
        form = ProtocolloForm(initial={"direzione": "IN"}, target=f)
    return render(request, "fascicoli/protocolla.html", {"form": form, "obj": f, "post_url": post_url})

@require_http_methods(["GET", "POST"])
@login_required
def protocolla_documento(request, pk: int):
    doc = get_object_or_404(Documento, pk=pk)
    if request.method == "POST":
        data = request.POST.copy()
        data.setdefault("direzione", "IN")
        form = ProtocolloForm(data=data, target=doc)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                if cd["direzione"] == "OUT":
                    MovimentoProtocollo.registra_uscita(
                        documento=doc,
                        quando=cd["quando"],
                        operatore=request.user,
                        a_chi=cd.get("a_chi") or "",
                        data_rientro_prevista=cd.get("data_rientro_prevista"),
                        causale=cd.get("causale") or "",
                        note=cd.get("note") or "",
                        ubicazione=cd.get("ubicazione") if isinstance(cd.get("ubicazione"), UnitaFisica) else None,
                    )
                    messages.success(request, "Uscita registrata.")
                else:
                    MovimentoProtocollo.registra_entrata(
                        documento=doc,
                        quando=cd["quando"],
                        operatore=request.user,
                        da_chi=cd.get("da_chi") or "",
                        ubicazione=cd.get("ubicazione") if isinstance(cd.get("ubicazione"), UnitaFisica) else None,
                        causale=cd.get("causale") or "",
                        note=cd.get("note") or "",
                    )
                    messages.success(request, "Entrata registrata.")
                return redirect("documenti:dettaglio", pk=doc.pk)
            except Exception as ex:
                messages.error(request, f"Errore nella protocollazione: {ex}")
    else:
        form = ProtocolloForm(initial={"direzione": "IN"}, target=doc)
    context = {"doc": doc, "form": form}
    return render(request, "documenti/protocollo.html", context)
