from __future__ import annotations
from django import forms
from django.db import transaction
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from .models import Anagrafica, Cliente, ClientiTipo, Indirizzo  # Assunto: Cliente OneToOne con Anagrafica

class SearchAnagraficaForm(forms.Form):
    q = forms.CharField(label="Ricerca", required=False)
    tipo = forms.ChoiceField(
        label="Tipo", required=False,
        choices=(("", "Tutti"), ("PF", "Persona fisica"), ("PG", "Persona giuridica"))
    )

class AnagraficaForm(forms.ModelForm):
    class Meta:
        model = Anagrafica
        fields = ["tipo", "ragione_sociale", "nome", "cognome", "codice_fiscale", "partita_iva", "denominazione_abbreviata", "pec", "email", "telefono", "indirizzo", "note"]
        widgets = {
            "ragione_sociale": forms.TextInput(attrs={"autocomplete": "organization"}),
            "nome": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "cognome": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "codice_fiscale": forms.TextInput(attrs={"autocomplete": "off"}),
            "partita_iva": forms.TextInput(attrs={"autocomplete": "off"}),
            "denominazione_abbreviata": forms.TextInput(attrs={"autocomplete": "off", "maxlength": "15", "placeholder": "Max 15 caratteri senza spazi"}),
            "pec": forms.EmailInput(attrs={"autocomplete": "email"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "telefono": forms.TextInput(attrs={"autocomplete": "tel"}),
            "note": forms.Textarea(attrs={"rows": 2, "autocomplete": "off"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "indirizzo" in self.fields:
            self.fields["indirizzo"].disabled = True
            self.fields["indirizzo"].required = False

class ClienteForm(forms.ModelForm):
    cliente_dal = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "autocomplete": "off"}))
    cliente_al = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "autocomplete": "off"}))

    class Meta:
        model = Cliente
        fields = ["tipo_cliente", "codice_destinatario", "cliente_dal", "cliente_al", "indirizzo_fatturazione", "indirizzo_consegna", "note"]
        widgets = {
            "codice_destinatario": forms.TextInput(attrs={"autocomplete": "off"}),
            "note": forms.Textarea(attrs={"rows": 2, "autocomplete": "off"}),
        }

    def __init__(self, *args, **kwargs):
        anagrafica = kwargs.pop("anagrafica", None)
        super().__init__(*args, **kwargs)

        # Popola le select degli indirizzi (se già presenti) ma senza bottoni popup
        from .models import Indirizzo
        qs = Indirizzo.objects.none()
        if anagrafica and anagrafica.pk:
            qs = Indirizzo.objects.filter(anagrafica=anagrafica).order_by("-principale", "id")
        if "indirizzo_fatturazione" in self.fields:
            self.fields["indirizzo_fatturazione"].queryset = qs
        if "indirizzo_consegna" in self.fields:
            self.fields["indirizzo_consegna"].queryset = qs

    def clean(self):
        cleaned = super().clean()
        dal, al = cleaned.get("cliente_dal"), cleaned.get("cliente_al")
        if dal and al and al < dal:
            raise ValidationError({"cliente_al": "La data fine non può essere precedente alla data inizio."})
        return cleaned

class IndirizzoForm(forms.ModelForm):
    class Meta:
        model = Indirizzo
        fields = [
            "tipo_indirizzo", "toponimo", "indirizzo", "numero_civico",
            "frazione", "cap", "comune", "provincia", "nazione",
            "principale", "note",
        ]
        widgets = {
            "toponimo": forms.TextInput(attrs={"autocomplete": "address-line2"}),
            "indirizzo": forms.TextInput(attrs={"autocomplete": "address-line1"}),
            "numero_civico": forms.TextInput(attrs={"autocomplete": "address-line2"}),
            "frazione": forms.TextInput(attrs={"autocomplete": "address-level3"}),
            "cap": forms.TextInput(attrs={"autocomplete": "postal-code", "inputmode": "numeric"}),
            "comune": forms.TextInput(attrs={"autocomplete": "address-level2"}),
            "provincia": forms.TextInput(attrs={"autocomplete": "address-level1"}),
            "nazione": forms.TextInput(attrs={"autocomplete": "country"}),
            "note": forms.Textarea(attrs={"rows": 2, "autocomplete": "off"}),
        }

IndirizzoFormSet = inlineformset_factory(
    Anagrafica, Indirizzo,
    form=IndirizzoForm,
    extra=0,
    can_delete=True,
)

class ImportAnagraficaForm(forms.Form):
    file = forms.FileField(
        label="File CSV",
        help_text="Formato: CSV con separatore ';' (punto e virgola). Encoding UTF-8 o Latin-1.",
        widget=forms.FileInput(attrs={"accept": ".csv"})
    )