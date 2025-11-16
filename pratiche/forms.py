from __future__ import annotations

from django import forms

from .models import Pratica, PraticaRelazione, PraticaNota


class PraticaForm(forms.ModelForm):
    class Meta:
        model = Pratica
        fields = "__all__"
        widgets = {
            "data_apertura": forms.DateInput(attrs={"type": "date"}),
            "data_chiusura": forms.DateInput(attrs={"type": "date"}),
            "data_riferimento": forms.DateInput(attrs={"type": "date"}),
            "note": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("data_apertura", "data_chiusura", "data_riferimento"):
            field = self.fields.get(name)
            if field:
                field.input_formats = ["%Y-%m-%d"]
        if "data_apertura" in self.fields:
            self.fields["data_apertura"].disabled = True
        if "cliente" in self.fields:
            old_class = self.fields["cliente"].widget.attrs.get("class", "")
            self.fields["cliente"].widget.attrs["class"] = (old_class + " select2").strip()

        pratica_qs = Pratica.objects.all()
        if self.instance and self.instance.pk:
            pratica_qs = pratica_qs.exclude(pk=self.instance.pk)

        self.fields["padre"] = forms.ModelChoiceField(
            queryset=pratica_qs,
            required=False,
            label="Pratica padre",
        )
        self.fields["padre"].widget = forms.HiddenInput()
        self.fields["tipo_relazione"] = forms.ChoiceField(
            choices=[("", "---------")] + list(PraticaRelazione.TIPI),
            required=False,
            label="Tipo relazione",
        )
        self.fields["tipo_relazione"].widget = forms.HiddenInput()
        self.fields["figli"] = forms.ModelMultipleChoiceField(
            queryset=pratica_qs,
            required=False,
            label="Pratiche figlie",
        )
        self.fields["figli"].widget = forms.MultipleHiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        padre = cleaned_data.get("padre")
        tipo_relazione = cleaned_data.get("tipo_relazione")
        if padre and not tipo_relazione:
            self.add_error("tipo_relazione", "Seleziona il tipo di relazione.")
        return cleaned_data

    def save(self, commit=True):
        pratica = super().save(commit=commit)
        if commit:
            self._sync_parent_relation(pratica)
        else:
            self._pending_parent_sync = pratica  # pragma: no cover
        return pratica

    def save_m2m(self):  # pragma: no cover - executed in commit=False branch
        super().save_m2m()
        pratica = getattr(self, "_pending_parent_sync", None)
        if pratica is not None:
            self._sync_parent_relation(pratica)

    def _sync_parent_relation(self, pratica: Pratica):
        padre = self.cleaned_data.get("padre")
        tipo_relazione = self.cleaned_data.get("tipo_relazione")
        if padre and tipo_relazione:
            rel, created = PraticaRelazione.objects.get_or_create(
                parent=padre,
                child=pratica,
                defaults={"tipo": tipo_relazione},
            )
            if not created and rel.tipo != tipo_relazione:
                rel.tipo = tipo_relazione
                rel.save(update_fields=["tipo"])
        if hasattr(self, "_pending_parent_sync"):
            delattr(self, "_pending_parent_sync")


class PraticaNotaForm(forms.ModelForm):
    class Meta:
        model = PraticaNota
        fields = ["pratica", "tipo", "testo", "data", "stato"]
        widgets = {
            "testo": forms.Textarea(attrs={"rows": 4}),
            "data": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["pratica"].widget = forms.HiddenInput()