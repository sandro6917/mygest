from __future__ import annotations
from django import forms
from django.forms import ModelForm
from django.utils import timezone
from .models import Documento, DocumentiTipo, AttributoDefinizione, AttributoValore, Ubicazione
import datetime
from decimal import Decimal
from django.utils.dateparse import parse_date, parse_datetime
from anagrafiche.models import Anagrafica, Cliente  # <-- aggiungi Cliente all'import in alto
from fascicoli.models import Fascicolo
import os

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
            "digitale",
            "file",
            "stato",
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
            qs_fasc = Fascicolo.objects.select_related("cliente", "titolario_voce").prefetch_related("pratiche").order_by("-id")
            # cliente da istanza o dai dati del form
            cliente_id = None
            if istanza and getattr(istanza, "cliente_id", None):
                cliente_id = istanza.cliente_id
            else:
                raw_cli = (self.data.get("cliente") or self.initial.get("cliente")) if (self.data or self.initial) else None
                try:
                    cliente_id = int(raw_cli) if raw_cli else None
                except Exception:
                    cliente_id = None

            # Se Documento.cliente punta ad Anagrafica, filtra i fascicoli su cliente__anagrafica_id
            try:
                target_fk = Documento._meta.get_field("cliente").remote_field.model
                if cliente_id:
                    if target_fk is Anagrafica:
                        qs_fasc = qs_fasc.filter(cliente__anagrafica_id=cliente_id)
                    else:
                        qs_fasc = qs_fasc.filter(cliente_id=cliente_id)
            except Exception:
                if cliente_id:
                    qs_fasc = qs_fasc.filter(cliente_id=cliente_id)

            self.fields["fascicolo"].queryset = qs_fasc
            self.fields["fascicolo"].required = False
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

    def _coerce_cliente_value(self, value):
        """Converte value al modello target del FK Documento.cliente (Anagrafica o Cliente)."""
        if value is None:
            return None
        target_fk = Documento._meta.get_field("cliente").remote_field.model
        if target_fk is Anagrafica:
            if isinstance(value, Anagrafica):
                return value
            if isinstance(value, Cliente):
                return getattr(value, "anagrafica", None)
        if target_fk is Cliente:
            if isinstance(value, Cliente):
                return value
            if isinstance(value, Anagrafica):
                cliente = getattr(value, "cliente", None)
                if cliente:
                    return cliente
                cliente, _ = Cliente.objects.get_or_create(anagrafica=value)
                return cliente
        return value

    def clean(self):
        cleaned = super().clean()
        fascicolo = cleaned.get("fascicolo")
        cliente = cleaned.get("cliente")
        # Allinea cliente al fascicolo, con coercizione sul target corretto
        if fascicolo and (not cliente or getattr(cliente, "pk", None) != getattr(fascicolo, "cliente_id", None)):
            src_cli = getattr(fascicolo, "cliente", None) or getattr(getattr(fascicolo, "pratica", None), "cliente", None)
            coerced = self._coerce_cliente_value(src_cli)
            if coerced:
                cleaned["cliente"] = coerced
                self.cleaned_data["cliente"] = coerced
        if not cleaned.get("digitale") and fascicolo and not getattr(fascicolo, "ubicazione_id", None):
            self.add_error("fascicolo", "I documenti cartacei richiedono un fascicolo con ubicazione fisica.")
        is_digitale = cleaned.get("digitale")
        uploaded_file = cleaned.get("file") or (self.instance.file if getattr(self.instance, "file", None) else None)
        if is_digitale and not uploaded_file:
            self.add_error("file", "Per i documenti digitali è necessario allegare un file.")
        return cleaned

    def save(self, commit=True):
        doc: Documento = super().save(commit=False)
        # Coerenza cliente/fascicolo con coercizione
        if getattr(doc, "fascicolo_id", None):
            src_cli = getattr(doc.fascicolo, "cliente", None) or getattr(getattr(doc.fascicolo, "pratica", None), "cliente", None)
            doc.cliente = self._coerce_cliente_value(src_cli) or doc.cliente

        if self._tipo and not getattr(doc, "tipo_id", None):
            doc.tipo = self._tipo

        if commit:
            doc.save()

        # Salva attributi dinamici
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

        # Dopo aver salvato gli attributi, forza la rinomina con il pattern aggiornato
        if getattr(doc, "file", None):
            try:
                # aggiorna il percorso archivio (se dipende da campi del documento)
                doc.percorso_archivio = doc._build_path()
                doc.save(update_fields=["percorso_archivio"])
                current_basename = os.path.basename(doc.file.name)
                # only_new=False per rinominare anche dopo la creazione
                doc._rename_file_if_needed(current_basename, only_new=False)
                doc._move_file_into_archivio()
            except Exception:
                # evita di bloccare il salvataggio in caso di problemi di I/O
                pass

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

    def __init__(self, *args, target=None, **kwargs):
        self.target = target
        super().__init__(*args, **kwargs)
        self.fields["ubicazione"].queryset = Ubicazione.objects.all().order_by("descrizione")  # <-- fix campo
        self.fields["ubicazione"].label_from_instance = lambda u: f"{u.codice} — {u.descrizione}"
        target = self.target
        if isinstance(target, Documento):
            if target.digitale:
                self.fields["ubicazione"].disabled = True
                self.fields["ubicazione"].required = False
            elif target.fascicolo_id:
                from protocollo.models import MovimentoProtocollo
                mov = MovimentoProtocollo.objects.filter(fascicolo=target.fascicolo).order_by("data").first()
                resolved_ubicazione = None
                if mov and mov.ubicazione:
                    resolved_ubicazione = mov.ubicazione
                elif getattr(target.fascicolo, "ubicazione", None):
                    resolved_ubicazione = target.fascicolo.ubicazione
                if resolved_ubicazione:
                    self.fields["ubicazione"].initial = resolved_ubicazione
                    self.fields["ubicazione"].disabled = True
                    self.fields["ubicazione"].required = False
                else:
                    self.fields["ubicazione"].disabled = False
                    self.fields["ubicazione"].required = True
            else:
                self.fields["ubicazione"].required = True
        elif isinstance(target, Fascicolo):
            if target.ubicazione_id:
                self.fields["ubicazione"].initial = target.ubicazione
                self.fields["ubicazione"].required = True
            else:
                self.fields["ubicazione"].required = False

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
        target = getattr(self, "target", None)
        ubicazione = cd.get("ubicazione")
        if isinstance(target, Documento):
            if target.digitale and ubicazione:
                self.add_error("ubicazione", "I documenti digitali non prevedono un'ubicazione fisica.")
                cd["ubicazione"] = None
            elif not target.digitale:
                if target.fascicolo_id:
                    from protocollo.models import MovimentoProtocollo

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
                self.add_error("ubicazione", "Per i fascicoli cartacei è obbligatorio specificare l'ubicazione.")
            if not is_cartaceo and ubicazione is not None:
                # fascicolo digitale: azzera l'ubicazione
                self.add_error("ubicazione", "I fascicoli digitali non prevedono ubicazione.")
                cd["ubicazione"] = None
        return cd

from django import forms
from django.db import transaction
from .models import Documento
from anagrafiche.models import Anagrafica, Cliente  # usati per la coercizione

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        # Coerce dell'initial: se FK è Anagrafica ma arriva un Cliente, usa cliente.anagrafica_id
        initial = kwargs.get("initial") or {}
        try:
            fk_model = Documento._meta.get_field("cliente").remote_field.model
            if "cliente" in initial and initial["cliente"]:
                val = initial["cliente"]
                if fk_model is Anagrafica and isinstance(val, Cliente):
                    initial = dict(initial)  # copia
                    initial["cliente"] = getattr(val, "anagrafica_id", None)
                elif fk_model is Cliente and isinstance(val, Anagrafica):
                    # opzionale: se serve risolvere Cliente da Anagrafica
                    initial = dict(initial)
                    initial["cliente"] = getattr(val, "cliente_id", None) or None
            kwargs["initial"] = initial
        except Exception:
            pass
        super().__init__(*args, **kwargs)

    def _coerce_cliente_value(self, value):
        """Ritorna il valore coerente con il FK 'cliente' di Documento."""
        if value is None:
            return None
        fk_model = Documento._meta.get_field("cliente").remote_field.model
        # Target: Anagrafica
        if fk_model is Anagrafica:
            if isinstance(value, Anagrafica):
                return value
            if isinstance(value, Cliente):
                return getattr(value, "anagrafica", None)
        # Target: Cliente
        if fk_model is Cliente:
            if isinstance(value, Cliente):
                return value
            if isinstance(value, Anagrafica):
                # opzionale: risali a Cliente se presente relazione 1-1
                return getattr(value, "cliente", None)
        return value

    @transaction.atomic
    def save(self, commit=True):
        obj: Documento = super().save(commit=False)
        # Coerce del cliente dal form
        obj.cliente = self._coerce_cliente_value(getattr(obj, "cliente", None))

        # Se assente, eredita da pratica/fascicolo (coerzionato)
        if not obj.cliente_id:
            src = getattr(obj, "pratica", None) or getattr(obj, "fascicolo", None)
            src_cli = None
            if src is not None:
                src_cli = getattr(src, "cliente", None) or getattr(getattr(src, "pratica", None), "cliente", None)
            if src_cli:
                obj.cliente = self._coerce_cliente_value(src_cli)

        if commit:
            obj.save()
            self.save_m2m()
        return obj

    def clean(self):
        cleaned = super().clean()
        documento: Documento | None = getattr(self, "instance", None)
        fascicolo = cleaned.get("fascicolo")
        is_digitale = cleaned.get("digitale")
        current_file = cleaned.get("file") or (documento.file if documento and getattr(documento, "file", None) else None)
        if not is_digitale and fascicolo and not getattr(fascicolo, "ubicazione_id", None):
            self.add_error("fascicolo", "I documenti cartacei richiedono un fascicolo con ubicazione fisica.")
        if is_digitale and not current_file:
            self.add_error("file", "Per i documenti digitali è necessario allegare un file.")
        return cleaned

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