from __future__ import annotations

from django import forms
from django.urls import reverse_lazy

from anagrafiche.models import EmailContatto, MailingList

from .models import Comunicazione, AllegatoComunicazione
from .models_template import TemplateComunicazione, FirmaComunicazione, TemplateContextField

class ComunicazioneForm(forms.ModelForm):
    CONTEXT_FIELD_PREFIX = "ctx__"

    contatti_destinatari = forms.ModelMultipleChoiceField(
        queryset=EmailContatto.objects.none(),
        required=False,
        label="Contatti destinatari",
        widget=forms.SelectMultiple(attrs={"class": "form-select select2", "data-placeholder": "Seleziona contatti"}),
        help_text="Scegli indirizzi dalla rubrica (verranno aggiunti ai destinatari).",
    )
    liste_destinatari = forms.ModelMultipleChoiceField(
        queryset=MailingList.objects.none(),
        required=False,
        label="Liste di distribuzione",
        widget=forms.SelectMultiple(attrs={"class": "form-select select2", "data-placeholder": "Seleziona liste"}),
        help_text="Le liste espandono automaticamente gli indirizzi dei membri e degli extra registrati.",
    )
    template = forms.ModelChoiceField(
        queryset=TemplateComunicazione.objects.none(),
        required=False,
        label="Template",
        widget=forms.Select(attrs={"class": "form-select", "data-allow-clear": "true"}),
        help_text="Seleziona un modello predefinito (solo comunicazioni in uscita).",
    )
    firma = forms.ModelChoiceField(
        queryset=FirmaComunicazione.objects.none(),
        required=False,
        label="Firma",
        widget=forms.Select(attrs={"class": "form-select", "data-allow-clear": "true"}),
        help_text="Firma testuale o HTML da allegare al messaggio (solo comunicazioni in uscita).",
    )

    class Meta:
        model = Comunicazione
        fields = [
            "tipo",
            "direzione",
            "template",
            "firma",
            "oggetto",
            "corpo",
            "corpo_html",
            "mittente",
            "destinatari",
            "anagrafica",
            "documento_protocollo",
            "contatti_destinatari",
            "liste_destinatari",
        ]
        widgets = {
            "tipo": forms.Select(attrs={"class": "form-select"}),
            "direzione": forms.Select(attrs={"class": "form-select"}),
            "oggetto": forms.TextInput(attrs={"class": "form-control"}),
            "corpo": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "corpo_html": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "mittente": forms.EmailInput(attrs={"class": "form-control"}),
            "destinatari": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "anagrafica": forms.Select(attrs={"class": "form-select"}),
            "documento_protocollo": forms.Select(attrs={"class": "form-select"}),
            "template": forms.Select(attrs={"class": "form-select"}),
            "firma": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context_field_map: dict[str, TemplateContextField] = {}
        self._template_instance = self._determine_template_instance()
        self.fields["destinatari"].required = False
        self.fields["contatti_destinatari"].widget.attrs.update(
            {
                "data-autocomplete-url": reverse_lazy("comunicazioni:api-contatti-autocomplete"),
                "data-allow-clear": "true",
            }
        )
        self.fields["liste_destinatari"].widget.attrs.update(
            {
                "data-autocomplete-url": reverse_lazy("comunicazioni:api-liste-autocomplete"),
                "data-allow-clear": "true",
            }
        )
        self.fields["contatti_destinatari"].queryset = EmailContatto.objects.filter(attivo=True)
        self.fields["liste_destinatari"].queryset = MailingList.objects.filter(attiva=True)
        self.fields["template"].queryset = TemplateComunicazione.objects.filter(attivo=True).order_by("nome")
        self.fields["firma"].queryset = FirmaComunicazione.objects.filter(attivo=True).order_by("nome")
        if self.instance.pk:
            self.fields["contatti_destinatari"].initial = self.instance.contatti_destinatari.all()
            self.fields["liste_destinatari"].initial = self.instance.liste_destinatari.all()
            self.fields["template"].initial = self.instance.template
            self.fields["firma"].initial = self.instance.firma
        if self._template_instance:
            self._init_template_context_fields(self._template_instance)

    @classmethod
    def context_field_name(cls, key: str) -> str:
        return f"{cls.CONTEXT_FIELD_PREFIX}{key}"

    def _determine_template_instance(self) -> TemplateComunicazione | None:
        template_field_name = self.add_prefix("template")
        template_pk = None
        if self.is_bound:
            template_pk = self.data.get(template_field_name) or self.data.get("template")
        if not template_pk:
            initial_value = self.initial.get("template")
            if isinstance(initial_value, TemplateComunicazione):
                template_pk = initial_value.pk
            elif initial_value:
                template_pk = initial_value
        if not template_pk and self.instance and self.instance.template_id:
            template_pk = self.instance.template_id
        if not template_pk:
            return None
        try:
            return TemplateComunicazione.objects.filter(attivo=True).get(pk=template_pk)
        except (TemplateComunicazione.DoesNotExist, ValueError):
            return self.instance.template if self.instance and self.instance.template_id else None

    def _init_template_context_fields(self, template: TemplateComunicazione) -> None:
        context_fields = template.context_fields.filter(active=True).order_by("ordering", "id")
        for context_field in context_fields:
            field_name = self.context_field_name(context_field.key)
            form_field = self._build_context_form_field(context_field)
            if not self.is_bound:
                initial_value = self._initial_value_for_context_field(context_field)
                if initial_value is not None:
                    form_field.initial = initial_value
                    self.initial.setdefault(field_name, initial_value)
            self.fields[field_name] = form_field
            self._context_field_map[field_name] = context_field

    def _build_context_form_field(self, context_field: TemplateContextField) -> forms.Field:
        kwargs = {
            "label": context_field.label,
            "required": context_field.required,
            "help_text": context_field.help_text,
        }
        field_type = context_field.field_type
        if field_type == TemplateContextField.FieldType.TEXTAREA:
            return forms.CharField(widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"}), **kwargs)
        if field_type == TemplateContextField.FieldType.INTEGER:
            return forms.IntegerField(widget=forms.NumberInput(attrs={"class": "form-control"}), **kwargs)
        if field_type == TemplateContextField.FieldType.DECIMAL:
            return forms.DecimalField(
                max_digits=18,
                decimal_places=6,
                widget=forms.NumberInput(attrs={"step": "0.01", "class": "form-control"}),
                **kwargs,
            )
        if field_type == TemplateContextField.FieldType.DATE:
            return forms.DateField(widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}), **kwargs)
        if field_type == TemplateContextField.FieldType.DATETIME:
            return forms.DateTimeField(
                widget=forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
                **kwargs,
            )
        if field_type == TemplateContextField.FieldType.BOOLEAN:
            return forms.BooleanField(required=context_field.required, label=context_field.label, help_text=context_field.help_text)
        if field_type == TemplateContextField.FieldType.CHOICE:
            choices = [("", "---")] + context_field.parsed_choices
            return forms.ChoiceField(choices=choices, **kwargs)
        return forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}), **kwargs)

    def _initial_value_for_context_field(self, context_field: TemplateContextField):
        stored = None
        if self.instance and self.instance.dati_template:
            stored = self.instance.dati_template.get(context_field.key)
        coerced = context_field.coerce_value(stored)
        if coerced is not None:
            return coerced
        if self.instance and self.instance.pk:
            source_value = context_field.get_source_value(self.instance)
            if source_value is not None:
                return source_value
        return context_field.get_default_value()

    def _collect_template_context_data(self) -> None:
        context_data: dict[str, object] = {}
        for field_name, context_field in self._context_field_map.items():
            value = self.cleaned_data.get(field_name)
            if context_field.field_type == TemplateContextField.FieldType.BOOLEAN:
                context_data[context_field.key] = bool(value)
                continue
            if value in (None, ""):
                continue
            context_data[context_field.key] = context_field.serialize_value(value)
        self.cleaned_data["_template_context_data"] = context_data

    def clean(self):
        cleaned_data = super().clean()
        manuali = cleaned_data.get("destinatari") or ""
        contatti = cleaned_data.get("contatti_destinatari")
        liste = cleaned_data.get("liste_destinatari")

        def _split_emails(raw: str) -> list[str]:
            tokens = (raw or "").replace(";", ",").split(",")
            emails: list[str] = []
            for token in tokens:
                email = token.strip()
                if email and email not in emails:
                    emails.append(email)
            return emails

        combined: list[str] = _split_emails(manuali)

        contatti_iterable = list(contatti) if contatti is not None else []

        for contatto in contatti_iterable:
            email = (contatto.email or "").strip()
            if email and email not in combined:
                combined.append(email)

        if liste is not None and hasattr(liste, "prefetch_related"):
            # Prefetch per ridurre query durante l'iterazione delle liste.
            liste = liste.prefetch_related("contatti", "indirizzi_extra")
            cleaned_data["liste_destinatari"] = liste

        liste_iterable = list(liste) if liste is not None else []

        for lista in liste_iterable:
            for contatto in lista.contatti.filter(attivo=True):
                email = (contatto.email or "").strip()
                if email and email not in combined:
                    combined.append(email)
            for extra in lista.indirizzi_extra.all():
                email = (extra.email or "").strip()
                if email and email not in combined:
                    combined.append(email)

        if not combined:
            raise forms.ValidationError(
                "Inserire almeno un destinatario manuale oppure scegliere contatti o liste.")

        cleaned_data["destinatari"] = ", ".join(combined)
        self._collect_template_context_data()
        return cleaned_data

    def clean_template(self):
        template = self.cleaned_data.get("template")
        direzione = self.cleaned_data.get("direzione") or (self.instance.direzione if self.instance.pk else None)
        direzione = direzione or Comunicazione.Direzione.OUT
        if template and direzione != Comunicazione.Direzione.OUT:
            raise forms.ValidationError("I template sono disponibili solo per le comunicazioni in uscita.")
        return template

    def clean_firma(self):
        firma = self.cleaned_data.get("firma")
        direzione = self.cleaned_data.get("direzione") or (self.instance.direzione if self.instance.pk else None)
        direzione = direzione or Comunicazione.Direzione.OUT
        if firma and direzione != Comunicazione.Direzione.OUT:
            raise forms.ValidationError("Le firme predefinite sono disponibili solo per le comunicazioni in uscita.")
        return firma

    def clean_documento_protocollo(self):
        documento = self.cleaned_data.get("documento_protocollo")
        if self.instance.pk and self.instance.is_protocollata:
            if documento != self.instance.documento_protocollo:
                raise forms.ValidationError(
                    "Impossibile modificare il documento: la comunicazione è già protocollata.")
        return documento

    def clean_direzione(self):
        direzione = self.cleaned_data.get("direzione")
        if self.instance.pk and self.instance.is_protocollata:
            if direzione != self.instance.direzione:
                raise forms.ValidationError(
                    "Impossibile modificare la direzione: la comunicazione è già protocollata.")
        return direzione

    def save(self, commit=True):
        context_data = self.cleaned_data.get("_template_context_data", {})
        instance = super().save(commit=False)
        instance.dati_template = context_data
        if commit:
            instance.save()
            self._save_m2m()
            instance.sync_destinatari_testo()
        else:
            # Se non si salva subito, memorizza per chiamata successiva
            self._pending_context_data = context_data
        return instance

    def save_m2m(self):
        super().save_m2m()
        instance = self.instance
        if hasattr(self, "_pending_context_data"):
            instance.dati_template = getattr(self, "_pending_context_data")
            instance.save(update_fields=["dati_template"])
            delattr(self, "_pending_context_data")
        instance.sync_destinatari_testo()

class AllegatoComunicazioneForm(forms.ModelForm):
    class Meta:
        model = AllegatoComunicazione
        fields = ["documento"]
        widgets = {
            "documento": forms.Select(attrs={"class": "form-select"}),
        }
