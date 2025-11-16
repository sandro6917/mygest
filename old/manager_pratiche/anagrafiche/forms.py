from __future__ import annotations
from django import forms
from django.db import transaction
from .models import Anagrafica, Cliente, ClientiTipo  # Assunto: Cliente OneToOne con Anagrafica

class SearchAnagraficaForm(forms.Form):
    q = forms.CharField(label="Ricerca", required=False)
    tipo = forms.ChoiceField(
        label="Tipo", required=False,
        choices=(("", "Tutti"), ("PF", "Persona fisica"), ("PG", "Persona giuridica"))
    )

class AnagraficaForm(forms.ModelForm):
    class Meta:
        model = Anagrafica
        fields = "__all__"

class ClienteForm(forms.ModelForm):
    # campo facoltativo; mostra una scelta vuota
    tipo_cliente = forms.ModelChoiceField(
        queryset=ClientiTipo.objects.all(),
        required=False,
        label="Tipo cliente",
        empty_label="—",
    )

    class Meta:
        model = Cliente
        fields = ["tipo_cliente", "cliente_dal", "cliente_al", "note"]  # assicurarsi che contenga 'tipo_cliente'