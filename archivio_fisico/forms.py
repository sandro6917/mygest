from __future__ import annotations

from itertools import chain

from django import forms
from django.db.models import OuterRef, Q, Subquery

try:  # Django >= 5 rimuove il simbolo da django.forms.fields
    from django.forms.fields import BLANK_CHOICE_DASH  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - fallback per versioni senza costante
    BLANK_CHOICE_DASH = (("", "---------"),)

from documenti.models import Documento
from fascicoli.models import Fascicolo
from protocollo.models import MovimentoProtocollo

from .models import OperazioneArchivio, RigaOperazioneArchivio, UnitaFisica


def _build_default_status_choices() -> list[tuple[str, str]]:
    seen: set[str] = set()
    merged: list[tuple[str, str]] = []
    for code, label in chain(Documento.Stato.choices, Fascicolo.Stato.choices):
        if code in seen:
            continue
        seen.add(code)
        merged.append((code, label))
    return merged


class OperazioneArchivioForm(forms.ModelForm):
    class Meta:
        model = OperazioneArchivio
        fields = [
            "tipo_operazione",
            "referente_interno",
            "referente_esterno",
            "verbale_scan",
            "note",
        ]


class FlexibleChoiceField(forms.ChoiceField):
    def validate(self, value):  # noqa: D401
        """Applica solo la validazione base, ignorando l'elenco delle scelte."""
        forms.Field.validate(self, value)


class RigaOperazioneArchivioForm(forms.ModelForm):
    stato_precedente = FlexibleChoiceField(required=False)
    stato_successivo = FlexibleChoiceField(required=False)

    _default_status_choices = _build_default_status_choices()

    def __init__(
        self,
        *args,
        tipo_operazione=None,
        referente_esterno_id=None,
        **kwargs,
    ):
        self.tipo_operazione = tipo_operazione
        self.referente_esterno_id = referente_esterno_id
        super().__init__(*args, **kwargs)
        fascicolo_field = self.fields["fascicolo"]
        documento_field = self.fields["documento"]

        queryset_fascicoli = fascicolo_field.queryset
        queryset_documenti = documento_field.queryset

        if referente_esterno_id:
            queryset_fascicoli = queryset_fascicoli.filter(
                cliente__anagrafica_id=referente_esterno_id
            )
            queryset_documenti = queryset_documenti.filter(cliente_id=referente_esterno_id)

        queryset_documenti = queryset_documenti.filter(
            digitale=False,
            tracciabile=True,
            movimenti__isnull=False,
        )
        queryset_fascicoli = queryset_fascicoli.filter(
            movimenti_protocollo__isnull=False,
        )

        operation_type = self.tipo_operazione or getattr(
            getattr(self.instance, "operazione", None), "tipo_operazione", None
        )

        documento_last_operazione = RigaOperazioneArchivio.objects.filter(
            Q(documento=OuterRef("pk"))
            | Q(documento__isnull=True, movimento_protocollo__documento=OuterRef("pk")),
            operazione__tipo_operazione__in=["entrata", "uscita"],
        ).order_by("-operazione__data_ora", "-operazione_id", "-id")

        fascicolo_last_operazione = RigaOperazioneArchivio.objects.filter(
            Q(fascicolo=OuterRef("pk"))
            | Q(fascicolo__isnull=True, movimento_protocollo__fascicolo=OuterRef("pk")),
            operazione__tipo_operazione__in=["entrata", "uscita"],
        ).order_by("-operazione__data_ora", "-operazione_id", "-id")

        queryset_documenti = queryset_documenti.annotate(
            ultima_operazione_archivio=Subquery(
                documento_last_operazione.values("operazione__tipo_operazione")[:1]
            )
        )

        queryset_fascicoli = queryset_fascicoli.annotate(
            ultima_operazione_archivio=Subquery(
                fascicolo_last_operazione.values("operazione__tipo_operazione")[:1]
            )
        )

        if operation_type == "entrata":
            queryset_documenti = queryset_documenti.filter(
                Q(ultima_operazione_archivio="uscita") | Q(ultima_operazione_archivio__isnull=True)
            )
            queryset_fascicoli = queryset_fascicoli.filter(
                Q(ultima_operazione_archivio="uscita") | Q(ultima_operazione_archivio__isnull=True)
            )
        elif operation_type in {"uscita", "interna"}:
            queryset_documenti = queryset_documenti.filter(
                Q(ultima_operazione_archivio="entrata") | Q(ultima_operazione_archivio__isnull=True)
            )
            queryset_fascicoli = queryset_fascicoli.filter(
                Q(ultima_operazione_archivio="entrata") | Q(ultima_operazione_archivio__isnull=True)
            )

        unita_sorgente = self._resolve_unita("unita_fisica_sorgente") if operation_type in {"uscita", "interna"} else None
        if unita_sorgente:
            queryset_fascicoli = queryset_fascicoli.filter(ubicazione=unita_sorgente)
            queryset_documenti = queryset_documenti.filter(
                collocazioni_fisiche__unita=unita_sorgente,
                collocazioni_fisiche__attiva=True,
            )

        target_obj = self._resolve_target_object()
        if isinstance(target_obj, Documento):
            documento_qs = Documento.objects.filter(pk=target_obj.pk)
            queryset_documenti = (documento_qs | queryset_documenti).distinct()
        if isinstance(target_obj, Fascicolo):
            fascicolo_qs = Fascicolo.objects.filter(pk=target_obj.pk)
            queryset_fascicoli = (fascicolo_qs | queryset_fascicoli).distinct()

        fascicolo_field.queryset = queryset_fascicoli.distinct()
        documento_field.queryset = queryset_documenti.distinct()

        movimento_field = self.fields["movimento_protocollo"]
        movimento_queryset = movimento_field.queryset.order_by("-data")
        if isinstance(target_obj, Documento):
            movimento_queryset = movimento_queryset.filter(documento=target_obj)
        elif isinstance(target_obj, Fascicolo):
            movimento_queryset = movimento_queryset.filter(fascicolo=target_obj)
        else:
            movimento_queryset = movimento_queryset.none()
        movimento_field.queryset = movimento_queryset
        status_choices = self._build_status_choices(target_obj)
        self._state_code_map = {}
        self._state_label_map = {}
        self._populate_state_maps(status_choices)
        self._configure_status_field("stato_precedente", status_choices)
        self._configure_status_field("stato_successivo", status_choices)

        if not self.is_bound:
            current_state = self._resolve_current_state(target_obj)
            if current_state:
                self._set_initial_if_absent("stato_precedente", current_state)
                self._set_initial_if_absent("stato_successivo", current_state)

            if operation_type == "entrata":
                destination = self._resolve_default_destination(target_obj)
                if destination:
                    self._set_initial_if_absent("unita_fisica_destinazione", destination.pk)
            elif operation_type in {"uscita", "interna"}:
                source = self._resolve_default_source(target_obj)
                if source:
                    self._set_initial_if_absent("unita_fisica_sorgente", source.pk)

            preferred_movimento = self._resolve_preferred_movimento(target_obj)
            if preferred_movimento:
                self._set_initial_if_absent("movimento_protocollo", preferred_movimento.pk)

    def _resolve_unita(self, field_name: str) -> UnitaFisica | None:
        raw_value = None
        if self.data:
            raw_value = self.data.get(self.add_prefix(field_name))
        if not raw_value and self.initial:
            raw_value = self.initial.get(field_name)
        if not raw_value and getattr(self.instance, f"{field_name}_id", None):
            raw_value = getattr(self.instance, f"{field_name}_id")
        if not raw_value:
            return None
        try:
            return UnitaFisica.objects.filter(pk=raw_value).first()
        except (ValueError, TypeError):
            return None

    def _populate_state_maps(self, choices: list[tuple[str, str]]) -> None:
        self._state_code_map = {}
        self._state_label_map = {}
        for code, label in choices or self._default_status_choices:
            if code:
                normalized_code = str(code)
                self._state_code_map[normalized_code.casefold()] = normalized_code
            if label:
                self._state_label_map[str(label).casefold()] = str(code)

    def _configure_status_field(self, field_name: str, choices: list[tuple[str, str]]) -> None:
        field = self.fields[field_name]
        base_choices: list[tuple[str, str]] = []
        if not field.required:
            base_choices.extend(BLANK_CHOICE_DASH)
        base_choices.extend(choices or self._default_status_choices)
        current_value = (
            self.initial.get(field_name)
            or getattr(self.instance, field_name, None)
            or None
        )
        if current_value and current_value not in {code for code, _ in base_choices if code}:
            base_choices.append((current_value, current_value))
        field.choices = base_choices

    def _set_initial_if_absent(self, field_name: str, value):
        if field_name not in self.initial or self.initial[field_name] in (None, ""):
            self.initial[field_name] = value
        field = self.fields.get(field_name)
        if field and (field.initial in (None, "")):
            field.initial = value

    def _resolve_target_object(self):
        if hasattr(self, "_cached_target_obj"):
            return self._cached_target_obj

        def _to_int(raw):
            try:
                return int(raw)
            except (TypeError, ValueError):
                return None

        documento = getattr(self.instance, "documento", None)
        fascicolo = getattr(self.instance, "fascicolo", None)

        if documento is None:
            doc_id = None
            if self.data:
                doc_id = _to_int(self.data.get(self.add_prefix("documento")))
            if doc_id is None and self.initial:
                doc_id = _to_int(self.initial.get("documento"))
            if doc_id:
                documento = (
                    Documento.objects.select_related("fascicolo", "fascicolo__ubicazione")
                    .filter(pk=doc_id)
                    .first()
                )

        if fascicolo is None and documento is None:
            fas_id = None
            if self.data:
                fas_id = _to_int(self.data.get(self.add_prefix("fascicolo")))
            if fas_id is None and self.initial:
                fas_id = _to_int(self.initial.get("fascicolo"))
            if fas_id:
                fascicolo = (
                    Fascicolo.objects.select_related("ubicazione")
                    .filter(pk=fas_id)
                    .first()
                )

        target = documento or fascicolo
        self._cached_target_obj = target
        return target

    def _resolve_movimento_protocollo(self):
        if hasattr(self, "_cached_movimento"):
            return self._cached_movimento

        movimento = getattr(self.instance, "movimento_protocollo", None)

        if movimento is None:
            raw_value = None
            if self.data:
                raw_value = self.data.get(self.add_prefix("movimento_protocollo"))
            if raw_value is None and self.initial:
                raw_value = self.initial.get("movimento_protocollo")
            try:
                movimento_id = int(raw_value) if raw_value not in (None, "") else None
            except (TypeError, ValueError):
                movimento_id = None
            if movimento_id:
                movimento = (
                    MovimentoProtocollo.objects.select_related("ubicazione")
                    .filter(pk=movimento_id)
                    .first()
                )

        self._cached_movimento = movimento
        return movimento

    def _resolve_current_state(self, target_obj) -> str | None:
        stato = getattr(target_obj, "stato", None) if target_obj is not None else None
        if stato:
            return str(stato)
        return None

    def _resolve_default_destination(self, target_obj) -> UnitaFisica | None:
        movimento = self._resolve_movimento_protocollo()
        if movimento and movimento.ubicazione_id:
            return movimento.ubicazione
        if isinstance(target_obj, Documento):
            collocazione = getattr(target_obj, "collocazione_fisica", None)
            if collocazione and getattr(collocazione, "unita", None):
                return collocazione.unita
            fascicolo = getattr(target_obj, "fascicolo", None)
            if fascicolo and getattr(fascicolo, "ubicazione", None):
                return fascicolo.ubicazione
        if isinstance(target_obj, Fascicolo):
            if getattr(target_obj, "ubicazione", None):
                return target_obj.ubicazione
        return None

    def _resolve_default_source(self, target_obj) -> UnitaFisica | None:
        movimento = self._resolve_movimento_protocollo()
        if movimento and movimento.ubicazione_id:
            return movimento.ubicazione
        if isinstance(target_obj, Fascicolo):
            return getattr(target_obj, "ubicazione", None)
        if isinstance(target_obj, Documento):
            collocazione = getattr(target_obj, "collocazione_fisica", None)
            if collocazione and getattr(collocazione, "unita", None):
                return collocazione.unita
            fascicolo = getattr(target_obj, "fascicolo", None)
            if fascicolo and getattr(fascicolo, "ubicazione", None):
                return fascicolo.ubicazione
        return None

    def _build_status_choices(self, target_obj) -> list[tuple[str, str]]:
        if isinstance(target_obj, Documento):
            return list(Documento.Stato.choices)
        if isinstance(target_obj, Fascicolo):
            return list(Fascicolo.Stato.choices)
        return self._default_status_choices

    def _resolve_preferred_movimento(self, target_obj):
        if target_obj is None:
            return None
        qs = MovimentoProtocollo.objects.select_related("ubicazione").order_by("-data")
        if isinstance(target_obj, Documento):
            return qs.filter(documento=target_obj).first()
        if isinstance(target_obj, Fascicolo):
            return qs.filter(fascicolo=target_obj).first()
        return None

    def _resolve_unita_scarico_default(self) -> UnitaFisica | None:
        from django.conf import settings

        unita_id = getattr(settings, "ARCHIVIO_FISICO_UNITA_SCARICO_ID", None)
        if not unita_id:
            return None
        try:
            return UnitaFisica.objects.get(pk=unita_id)
        except UnitaFisica.DoesNotExist:
            return None

    def _default_stato_scarico(self, target_obj) -> str | None:
        if isinstance(target_obj, Documento):
            return Documento.Stato.SCARICATO
        if isinstance(target_obj, Fascicolo):
            return Fascicolo.Stato.SCARICATO
        return None

    def clean(self):
        cleaned_data = super().clean()
        tipo = self.tipo_operazione or getattr(getattr(self.instance, "operazione", None), "tipo_operazione", None)
        target_obj = self._resolve_target_object()

        preferred_movimento = self._resolve_preferred_movimento(target_obj)
        movimento = cleaned_data.get("movimento_protocollo") or preferred_movimento
        if preferred_movimento:
            cleaned_data["movimento_protocollo"] = preferred_movimento
            self.cleaned_data["movimento_protocollo"] = preferred_movimento
            movimento = preferred_movimento

        if target_obj and movimento is None:
            self.add_error("movimento_protocollo", "L'oggetto selezionato deve essere collegato a un movimento di protocollo.")

        corrente = self._resolve_current_state(target_obj) or ""

        def _set_value(field: str, value):
            cleaned_data[field] = value
            self.cleaned_data[field] = value

        if tipo == "entrata":
            _set_value("unita_fisica_sorgente", None)
            _set_value("stato_precedente", "")
            destinazione = None
            if movimento and movimento.ubicazione_id:
                destinazione = movimento.ubicazione
            if destinazione is None:
                self.add_error("unita_fisica_destinazione", "Impossibile determinare l'unità di arrivo dal protocollo associato.")
            _set_value("unita_fisica_destinazione", destinazione)
        elif tipo == "uscita":
            sorgente = None
            if movimento and movimento.ubicazione_id:
                sorgente = movimento.ubicazione
            if sorgente is None:
                self.add_error("unita_fisica_sorgente", "Impossibile determinare l'unità di partenza dal protocollo associato.")
            _set_value("unita_fisica_sorgente", sorgente)
            destinazione = self._resolve_unita_scarico_default()
            if destinazione is None:
                self.add_error("unita_fisica_destinazione", "Configura l'unità di scarico predefinita nelle impostazioni.")
            _set_value("unita_fisica_destinazione", destinazione)
            _set_value("stato_precedente", corrente)
            stato_scarico = self._default_stato_scarico(target_obj)
            if stato_scarico:
                _set_value("stato_successivo", stato_scarico)
            else:
                self.add_error("stato_successivo", "Impossibile determinare lo stato di scarico per l'oggetto selezionato.")
        elif tipo == "interna":
            sorgente = None
            if movimento and movimento.ubicazione_id:
                sorgente = movimento.ubicazione
            if sorgente is None:
                self.add_error("unita_fisica_sorgente", "Impossibile determinare l'unità di partenza dal protocollo associato.")
            _set_value("unita_fisica_sorgente", sorgente)
            _set_value("stato_precedente", corrente)
            if not cleaned_data.get("unita_fisica_destinazione"):
                self.add_error("unita_fisica_destinazione", "Seleziona l'unità di arrivo della movimentazione interna.")

        stato_successivo = cleaned_data.get("stato_successivo")
        normalized_successivo = self._normalize_state_input(stato_successivo, allow_unknown=False)
        if stato_successivo and normalized_successivo is None:
            self.add_error("stato_successivo", "Seleziona un valore di stato valido.")
        elif normalized_successivo is not None:
            _set_value("stato_successivo", normalized_successivo)

        if tipo == "entrata" and not cleaned_data.get("stato_successivo"):
            self.add_error("stato_successivo", "Seleziona lo stato successivo dell'oggetto in entrata.")

        return cleaned_data

    class Meta:
        model = RigaOperazioneArchivio
        fields = [
            "unita_fisica_sorgente",
            "unita_fisica_destinazione",
            "fascicolo",
            "documento",
            "movimento_protocollo",
            "stato_precedente",
            "stato_successivo",
            "note",
        ]

    def _normalize_state_input(self, value, *, allow_unknown: bool) -> str | None:
        if value in (None, ""):
            return None
        raw = str(value).strip()
        if not raw:
            return None
        key = raw.casefold()
        if key in self._state_code_map:
            return self._state_code_map[key]
        if key in self._state_label_map:
            return self._state_label_map[key]
        if allow_unknown:
            return raw
        return None
