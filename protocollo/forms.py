from django import forms
from django.utils import timezone
from archivio_fisico.models import UnitaFisica
from anagrafiche.models import Anagrafica
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, Div

class ProtocolloForm(forms.Form):
    DIREZIONI = (("IN", "Entrata"), ("OUT", "Uscita"))

    direzione = forms.ChoiceField(choices=DIREZIONI, initial="IN", required=False)
    quando = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))

    # Campi ENTRATA
    da_chi = forms.CharField(required=False, label="Da chi")
    da_chi_anagrafica = forms.ModelChoiceField(
        required=False,
        queryset=Anagrafica.objects.none(),
        label="Da chi (Anagrafica)",
    )
    ubicazione = forms.ModelChoiceField(
        queryset=UnitaFisica.objects.all().order_by("full_path", "nome"),
        required=False,
        label="Ubicazione (Unità fisica)",
    )

    # Campi USCITA
    a_chi = forms.CharField(required=False, label="A chi")
    a_chi_anagrafica = forms.ModelChoiceField(
        required=False,
        queryset=Anagrafica.objects.none(),
        label="A chi (Anagrafica)",
    )
    data_rientro_prevista = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}), label="Data rientro prevista")

    # Comuni
    causale = forms.CharField(required=False)
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, target=None, **kwargs):
        self.target = target
        super().__init__(*args, **kwargs)
        self.fields["ubicazione"].queryset = UnitaFisica.objects.all().order_by("full_path", "nome")
        self.fields["ubicazione"].label_from_instance = lambda u: f"{u.codice} — {u.full_path or u.nome}"

        anagrafiche_qs = Anagrafica.objects.all().order_by("ragione_sociale", "cognome", "nome")
        for field_name in ("da_chi_anagrafica", "a_chi_anagrafica"):
            self.fields[field_name].queryset = anagrafiche_qs
            self.fields[field_name].label_from_instance = self._format_anagrafica_label

        from documenti.models import Documento
        from fascicoli.models import Fascicolo

        if isinstance(self.target, Documento):
            if self.target.digitale:
                self.fields["ubicazione"].disabled = True
                self.fields["ubicazione"].required = False
            elif self.target.fascicolo_id:
                from protocollo.models import MovimentoProtocollo

                mov = MovimentoProtocollo.objects.filter(fascicolo=self.target.fascicolo).order_by("data").first()
                resolved_ubicazione = None
                if mov and mov.ubicazione:
                    resolved_ubicazione = mov.ubicazione
                elif getattr(self.target.fascicolo, "ubicazione", None):
                    resolved_ubicazione = self.target.fascicolo.ubicazione

                if resolved_ubicazione:
                    self.fields["ubicazione"].initial = resolved_ubicazione
                    self.fields["ubicazione"].disabled = True
                    self.fields["ubicazione"].required = False
                else:
                    self.fields["ubicazione"].disabled = False
                    self.fields["ubicazione"].required = True
            else:
                self.fields["ubicazione"].required = True
        elif isinstance(self.target, Fascicolo):
            if self.target.ubicazione_id:
                self.fields["ubicazione"].initial = self.target.ubicazione
                self.fields["ubicazione"].required = True
            else:
                self.fields["ubicazione"].required = False

        self.helper = FormHelper()
        self.helper.form_tag = False  # il tag <form> è nel template
        self.helper.layout = Layout(
            Row(Column("direzione", css_class="col-3"), Column("quando", css_class="col-4"), Column("ubicazione", css_class="col")),
            Row(Column("causale", css_class="col"),),
            Row(Column("da_chi", css_class="col-md-6"), Column("a_chi", css_class="col-md-6")),
            Row(Column("da_chi_anagrafica", css_class="col-md-6"), Column("a_chi_anagrafica", css_class="col-md-6")),
            Row(Column("data_rientro_prevista", css_class="col-4")),
            Row(Column(Field("note"), css_class="col")),
        )

    @staticmethod
    def _format_anagrafica_label(anagrafica: Anagrafica) -> str:
        base = anagrafica.display_name()
        if anagrafica.codice_fiscale:
            return f"{base} — {anagrafica.codice_fiscale}"
        return base

    def clean(self):
        cd = super().clean()
        d = (cd.get("direzione") or "IN").upper()
        cd["direzione"] = d
        if d not in ("IN", "OUT"):
            self.add_error("direzione", "Direzione non valida.")
        if not cd.get("quando"):
            cd["quando"] = timezone.now()
        target = getattr(self, "target", None)
        ubicazione = cd.get("ubicazione")
        if cd.get("da_chi_anagrafica") and not cd.get("da_chi"):
            cd["da_chi"] = cd["da_chi_anagrafica"].display_name()
        if cd.get("a_chi_anagrafica") and not cd.get("a_chi"):
            cd["a_chi"] = cd["a_chi_anagrafica"].display_name()
        if target is not None:
            from documenti.models import Documento
            from fascicoli.models import Fascicolo
            from protocollo.models import MovimentoProtocollo

            if isinstance(target, Documento):
                if target.digitale and ubicazione:
                    self.add_error("ubicazione", "I documenti digitali non prevedono un'ubicazione.")
                    cd["ubicazione"] = None
                elif not target.digitale:
                    if target.fascicolo_id:
                        mov = MovimentoProtocollo.objects.filter(fascicolo=target.fascicolo).order_by("data").first()
                        resolved_ubicazione = None
                        if mov and mov.ubicazione:
                            resolved_ubicazione = mov.ubicazione
                        elif getattr(target.fascicolo, "ubicazione", None):
                            resolved_ubicazione = target.fascicolo.ubicazione
                        if resolved_ubicazione:
                            cd["ubicazione"] = resolved_ubicazione
                            self.cleaned_data["ubicazione"] = resolved_ubicazione
                        elif ubicazione is None:
                            self.add_error(
                                "ubicazione",
                                "Indica l'ubicazione per il documento cartaceo: il fascicolo collegato non è ancora protocollato.",
                            )
                    else:
                        if ubicazione is None:
                            self.add_error("ubicazione", "Indica l'ubicazione per il documento cartaceo.")
            elif isinstance(target, Fascicolo):
                is_cartaceo = bool(target.ubicazione_id) or ubicazione is not None
                if is_cartaceo and ubicazione is None:
                    self.add_error("ubicazione", "Per i fascicoli cartacei è obbligatorio indicare l'ubicazione.")
                if not is_cartaceo and ubicazione is not None:
                    self.add_error("ubicazione", "I fascicoli digitali non prevedono ubicazione.")
                    cd["ubicazione"] = None
        return cd