from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import UnitaFisica

@login_required
def unita_list(request):
    radici = UnitaFisica.objects.filter(parent__isnull=True).order_by("ordine", "nome")
    return render(request, "archivio_fisico/unita_list.html", {"radici": radici})

@login_required
def unita_detail(request, pk: int):
    u = get_object_or_404(UnitaFisica.objects.select_related("parent"), pk=pk)
    figli = u.figli.all().order_by("ordine", "nome")
    return render(request, "archivio_fisico/unita_detail.html", {"u": u, "figli": figli})
