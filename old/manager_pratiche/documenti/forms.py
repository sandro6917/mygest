from __future__ import annotations
from django import forms
from django.forms import ModelForm
from django.utils import timezone
from .models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore, Ubicazione
import datetime
from decimal import Decimal
from django.utils.dateparse import parse_date, parse_datetime
from anagrafiche.models import Anagrafica  # <-- importa il modello
from fascicoli.models import Fascicolo  # <-- aggiungi import

class DocumentoDinamicoForm(ModelForm):
    class Meta:
        model = Documento
        fields = [
            "tipo",
            "cliente",
            "fascicolo",          # <-- aggiunto
            "titolario_voce",
            "data_documento",
            "descrizione",
            "file",
            "tracciabile",
            "tags",
            "note",
        ]

    def __init__(self, *args, tipo: DocumentiTipo | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        istanza: Documento | None = self.instance if getattr(self, "instance", None) else None
        tipo_obj = tipo or (istanza.tipo if istanza and getattr(istanza, "tipo_id", None) else None)
        self._tipo = tipo_obj

        if self._tipo and not getattr(self.instance, "tipo_id", None):
            self.instance.tipo = self._tipo

        # Gestione queryset fascicolo (filtra per cliente se noto)
        if "fascicolo" in self.fields:
            qs_fasc = Fascicolo.objects.all().order_by("-id")
            # cliente da istanza o dai dati del form
            cliente_id = None
            if istanza and getattr(istanza, "cliente_id", None):
                cliente_id = istanza.cliente_id
            else:
                raw_cli = (self.data.get("cliente") or self.initial.get("cliente")) if self.data or self.initial else None
                try:
                    cliente_id = int(raw_cli) if raw_cli else None
                except Exception:
                    cliente_id = None
            if cliente_id:
                qs_fasc = qs_fasc.filter(cliente_id=cliente_id)
            self.fields["fascicolo"].queryset = qs_fasc
            self.fields["fascicolo"].required = False  # opzionale
            # se istanza ha fascicolo, assicura che sia selezionato
            if istanza and getattr(istanza, "fascicolo_id", None):
                self.initial.setdefault("fascicolo", istanza.fascicolo_id)

        if tipo_obj:
            self.fields["tipo"].initial = tipo_obj.pk
            self.fields["tipo"].disabled = True
            self.fields["tipo"].required = False

            defs = AttributoDefinizione.objects.filter(tipo_documento=tipo_obj).order_by("ordine", "codice")

            valori = {}
            if istanza and istanza.pk:
                for av in AttributoValore.objects.filter(documento=istanza).select_related("definizione"):
                    valori[av.definizione_id] = av.valore

            for d in defs:
                name = f"attr_{d.codice}"
                field = self._build_attr_field(d)
                self.fields[name] = field

                init_val = None
                if d.id in valori:
                    init_val = self._from_json_safe(d.tipo_dato, valori[d.id], widget=getattr(d, "widget", ""))
                elif istanza and hasattr(istanza, d.codice):
                    # FIX: passa il widget dalla definizione, non dall'istanza
                    init_val = self._from_json_safe(d.tipo_dato, getattr(istanza, d.codice), widget=getattr(d, "widget", ""))

                if init_val is not None:
                    self.initial[name] = init_val
                    self.fields[name].initial = init_val

    def _build_attr_field(self, d: AttributoDefinizione) -> forms.Field:
        common = {"label": d.nome, "required": d.required, "help_text": d.help_text}
        tipo = (d.tipo_dato or "").lower()
        widget = (getattr(d, "widget", "") or "").lower()

        if tipo == "string":
            f = forms.CharField(**common)
            if getattr(d, "max_length", None):
                f.max_length = d.max_length
            if getattr(d, "regex", None):
                f.validators.append(forms.RegexField(regex=d.regex).validators[0])
            return f
        if tipo in ("int", "integer"):
            # se marcato come anagrafica, mostra select su Anagrafica
            if widget in ("anagrafica", "fk_anagrafica", "anag"):
                try:
                    qs = Anagrafica.objects.all().order_by("denominazione")
                except Exception:
                    qs = Anagrafica.objects.all()
                return forms.ModelChoiceField(queryset=qs, **common)
            return forms.IntegerField(**common)
        if tipo == "decimal":
            return forms.DecimalField(max_digits=18, decimal_places=4, **common)
        if tipo in ("date", "data"):
            return forms.DateField(
                input_formats=["%Y-%m-%d", "%d/%m/%Y"],
                widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
                localize=False,
                **common,
            )
        if tipo in ("datetime", "data_ora"):
            return forms.DateTimeField(
                input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"],
                widget=forms.DateTimeInput(format="%Y-%m-%dT%H:%M", attrs={"type": "datetime-local"}),
                localize=False,
                **common,
            )
        if tipo == "bool":
            return forms.BooleanField(**common)
        if tipo == "choice":
            return forms.ChoiceField(choices=d.scelte(), **common)
        return forms.CharField(**common)

    def _from_json_safe(self, tipo_dato: str, value, widget: str = ""):
        tipo = (tipo_dato or "").lower()
        widget = (widget or "").lower()
        if value in (None, ""):
            return None
        if tipo in ("date", "data"):
            if isinstance(value, datetime.datetime):
                return value.date()
            if isinstance(value, datetime.date):
                return value
            if isinstance(value, str):
                d = parse_date(value)
                if d:
                    return d
                dt = parse_datetime(value)
                return dt.date() if dt else None
            return None
        if tipo in ("datetime", "data_ora"):
            if isinstance(value, datetime.datetime):
                return value
            if isinstance(value, str):
                dt = parse_datetime(value)
                if dt:
                    return dt
                d = parse_date(value)
                return datetime.datetime.combine(d, datetime.time.min) if d else None
            return None
        if tipo in ("int", "integer") and widget in ("anagrafica", "fk_anagrafica", "anag"):
            # inizializza ModelChoiceField: serve un'istanza Anagrafica o pk valido
            if isinstance(value, Anagrafica):
                return value
            try:
                # FIX: uso corretto del filtro su pk
                return Anagrafica.objects.filter(pk=int(value)).first()
            except Exception:
                return None
        if tipo == "decimal":
            try:
                return Decimal(str(value))
            except Exception:
                return value
        if tipo in ("int", "integer"):
            try:
                return int(value)
            except Exception:
                return value
        return value

    def clean(self):
        cleaned = super().clean()
        fascicolo = cleaned.get("fascicolo")
        cliente = cleaned.get("cliente")
        # Allinea cliente a quello del fascicolo se scelto e differente
        if fascicolo and (not cliente or cliente.pk != fascicolo.cliente_id):
            cleaned["cliente"] = fascicolo.cliente
            self.cleaned_data["cliente"] = fascicolo.cliente
        return cleaned

    def save(self, commit=True):
        doc: Documento = super().save(commit=False)
        # Se è stato selezionato un fascicolo, forza coerenza cliente (model.clean farà comunque lo stesso)
        if getattr(doc, "fascicolo_id", None):
            doc.cliente = doc.fascicolo.cliente
        if self._tipo and not getattr(doc, "tipo_id", None):
            doc.tipo = self._tipo
        if commit:
            doc.save()

        tipo = self._tipo or getattr(doc, "tipo", None)
        defs = AttributoDefinizione.objects.filter(tipo_documento=tipo)
        for d in defs:
            key = f"attr_{d.codice}"
            if key in self.cleaned_data:
                raw = self.cleaned_data[key]
                val = self._to_json_safe(d.tipo_dato, raw, widget=getattr(d, "widget", ""))
                AttributoValore.objects.update_or_create(
                    documento=doc, definizione=d, defaults={"valore": val}
                )
        return doc

    def _to_json_safe(self, tipo_dato: str, value, widget: str = ""):
        tipo = (tipo_dato or "").lower()
        widget = (widget or "").lower()
        if value in (None, ""):
            return None
        if tipo in ("date", "data"):
            if isinstance(value, (datetime.date, datetime.datetime)):
                return value.isoformat()
            d = parse_date(str(value))
            return d.isoformat() if d else None
        if tipo in ("datetime", "data_ora"):
            if isinstance(value, datetime.datetime):
                return value.isoformat()
            dt = parse_datetime(str(value))
            return dt.isoformat() if dt else None
        if tipo in ("int", "integer") and widget in ("anagrafica", "fk_anagrafica", "anag"):
            # salva come pk int
            if isinstance(value, Anagrafica):
                return int(value.pk)
            try:
                return int(value)
            except Exception:
                return None
        if tipo == "decimal":
            if isinstance(value, Decimal):
                return str(value)
            return str(value)
        if tipo in ("int", "integer"):
            try:
                return int(value)
            except Exception:
                return value
        return value

from .models import Ubicazione  # assicurati che l'import ci sia

class ProtocolloForm(forms.Form):
    DIREZIONI = (("IN", "Entrata"), ("OUT", "Uscita"))
    direzione = forms.ChoiceField(choices=DIREZIONI, initial="IN")
    quando = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    ubicazione = forms.ModelChoiceField(queryset=Ubicazione.objects.none(), required=False)  # <-- no query qui
    causale = forms.CharField(required=False)
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
    da_chi = forms.CharField(required=False)
    a_chi = forms.CharField(required=False)
    data_rientro_prevista = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ubicazione"].queryset = Ubicazione.objects.all().order_by("descrizione")  # <-- fix campo
        self.fields["ubicazione"].label_from_instance = lambda u: f"{u.codice} — {u.descrizione}"

    def clean(self):
        cd = super().clean()
        direzione = (cd.get("direzione") or "").upper()
        if direzione not in ("IN", "OUT"):
            self.add_error("direzione", "Direzione non valida.")
        if direzione == "IN" and not cd.get("da_chi"):
            # opzionale: rendilo obbligatorio
            pass
        if direzione == "OUT" and not cd.get("a_chi"):
            pass
        # default 'quando' a now se vuoto
        if not cd.get("quando"):
            cd["quando"] = timezone.now()
        return cd

from django import forms
from archivio_fisico.models import UnitaFisica

class AssegnaCollocazioneForm(forms.Form):
    unita = forms.ModelChoiceField(queryset=UnitaFisica.objects.none(), label="Unità fisica")
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = UnitaFisica.objects.filter(attivo=True).order_by("full_path", "nome")
        self.fields["unita"].queryset = qs
        # etichetta leggibile con path
        self.fields["unita"].label_from_instance = lambda u: f"{u.get_tipo_display()} — {u.full_path} — {u.nome}"