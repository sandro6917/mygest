from __future__ import annotations

import json

from django import forms
from django.apps import apps
from django.forms import inlineformset_factory
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Scadenza, ScadenzaOccorrenza


class ScadenzaForm(forms.ModelForm):
    class Meta:
        model = Scadenza
        fields = [
            "titolo",
            "descrizione",
            "stato",
            "priorita",
            "categoria",
            "note_interne",
            "assegnatari",
            "pratiche",
            "fascicoli",
            "documenti",
            "comunicazione_destinatari",
            "comunicazione_modello",
            "periodicita",
            "periodicita_intervallo",
            "periodicita_config",
            "google_calendar_calendar_id",
        ]
        widgets = {
            "descrizione": forms.Textarea(attrs={"rows": 3}),
            "note_interne": forms.Textarea(attrs={"rows": 2}),
            "periodicita_config": forms.Textarea(
                attrs={"rows": 3, "placeholder": '{"weekday": [0, 2], "dates": []}'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assegnatari"].widget.attrs.update(
            {
                "class": "select2",
                "data-placeholder": _("Seleziona utenti da coinvolgere"),
                "style": "width: 100%;",
            }
        )

        related_fields = [
            {
                "name": "pratiche",
                "model": ("pratiche", "Pratica"),
                "select_related": ["cliente__anagrafica", "tipo"],
                "help_text": _(
                    "Collega le pratiche interessate: puoi cercare per codice, oggetto o cliente."
                ),
                "placeholder": _("Cerca pratica…"),
                "label_builder": self._format_pratica_label,
            },
            {
                "name": "fascicoli",
                "model": ("fascicoli", "Fascicolo"),
                "select_related": ["titolario_voce"],
                "help_text": _(
                    "Associa fascicoli di riferimento per contestualizzare la scadenza."
                ),
                "placeholder": _("Cerca fascicolo…"),
                "label_builder": self._format_fascicolo_label,
            },
            {
                "name": "documenti",
                "model": ("documenti", "Documento"),
                "select_related": ["cliente__anagrafica"],
                "help_text": _(
                    "Linka documenti utili alla gestione o verifica della scadenza."
                ),
                "placeholder": _("Cerca documento…"),
                "label_builder": self._format_documento_label,
            },
        ]

        for config in related_fields:
            field_name = config["name"]
            if field_name not in self.fields:
                continue

            model = apps.get_model(*config["model"])
            queryset = model.objects.all()
            select_related = config.get("select_related")
            if select_related:
                queryset = queryset.select_related(*select_related)
            queryset = queryset.order_by("-id")

            field = self.fields[field_name]
            field.queryset = queryset
            existing_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (
                f"{existing_class} form-select select2 related-m2m".strip()
            )
            field.widget.attrs.setdefault("data-placeholder", config["placeholder"])
            field.widget.attrs.setdefault("data-allow-clear", "true")
            field.widget.attrs.setdefault("style", "width: 100%;")
            field.widget.attrs.setdefault("data-dropdown-parent", "#scadenza-form")
            field.help_text = config["help_text"]
            field.label_from_instance = config["label_builder"]

    @staticmethod
    def _format_pratica_label(obj) -> str:
        parts: list[str] = []
        if getattr(obj, "codice", None):
            parts.append(str(obj.codice))
        if getattr(obj, "oggetto", None):
            parts.append(str(obj.oggetto))
        cliente = getattr(obj, "cliente", None)
        if cliente:
            descr = getattr(cliente, "anagrafica", None)
            parts.append(str(descr or cliente))
        tipo = getattr(obj, "tipo", None)
        if tipo:
            parts.append(f"[{tipo}]")
        if not parts:
            parts.append(f"Pratica #{obj.pk}")
        return " — ".join(parts)

    @staticmethod
    def _format_fascicolo_label(obj) -> str:
        codice = getattr(obj, "codice", None) or f"Fascicolo #{obj.pk}"
        titolo = getattr(obj, "titolo", None)
        stato = getattr(obj, "stato", None)
        titolario = getattr(obj, "titolario_voce", None)
        parts = [codice]
        if titolo:
            parts.append(str(titolo))
        if titolario:
            parts.append(str(titolario))
        if stato:
            parts.append(f"stato: {stato}")
        return " — ".join(parts)

    @staticmethod
    def _format_documento_label(obj) -> str:
        titolo = getattr(obj, "titolo", None) or f"Documento #{obj.pk}"
        numero = getattr(obj, "numero", None)
        cliente = getattr(obj, "cliente", None)
        parts = [titolo]
        if numero:
            parts.append(f"n. {numero}")
        if cliente:
            descr = getattr(cliente, "anagrafica", None)
            parts.append(str(descr or cliente))
        return " — ".join(parts)


class ScadenzaOccorrenzaForm(forms.ModelForm):
    inizio = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
    )
    fine = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
    )

    class Meta:
        model = ScadenzaOccorrenza
        fields = [
            "titolo",
            "descrizione",
            "inizio",
            "fine",
            "metodo_alert",
            "offset_alert_minuti",
            "alert_config",
            "stato",
        ]
        widgets = {
            "descrizione": forms.Textarea(attrs={"rows": 2}),
            "alert_config": forms.Textarea(
                attrs={"rows": 2, "placeholder": '{"destinatari": "email@example.com"}'}
            ),
        }

    def clean_inizio(self):
        value = self.cleaned_data["inizio"]
        if timezone.is_naive(value):
            return timezone.make_aware(value)
        return value

    def clean_fine(self):
        value = self.cleaned_data.get("fine")
        if value and timezone.is_naive(value):
            return timezone.make_aware(value)
        return value


ScadenzaOccorrenzaFormSet = inlineformset_factory(
    Scadenza,
    ScadenzaOccorrenza,
    form=ScadenzaOccorrenzaForm,
    fields=[
        "titolo",
        "descrizione",
        "inizio",
        "fine",
        "metodo_alert",
        "offset_alert_minuti",
        "alert_config",
        "stato",
    ],
    extra=1,
    can_delete=True,
)


class ScadenzaBulkOccurrencesForm(forms.Form):
    start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
    )
    end = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
    )
    count = forms.IntegerField(required=False, min_value=1)
    offset_alert_minuti = forms.IntegerField(min_value=0, initial=0)
    metodo_alert = forms.ChoiceField(
        choices=ScadenzaOccorrenza.MetodoAlert.choices,
        initial=ScadenzaOccorrenza.MetodoAlert.EMAIL,
    )
    alert_config = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={"rows": 2, "placeholder": '{"destinatari": "email@example.com"}'}
        ),
        help_text="JSON opzionale con configurazione alert.",
    )

    def clean_alert_config(self):
        raw = self.cleaned_data.get("alert_config")
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception as exc:
            raise forms.ValidationError(f"JSON non valido: {exc}") from exc
