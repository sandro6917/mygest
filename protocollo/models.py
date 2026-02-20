from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from django.utils.translation import gettext_lazy as _
from anagrafiche.models import Anagrafica

User = get_user_model()

class ProtocolloCounter(models.Model):
    DIREZIONE = (("IN", "Entrata"), ("OUT", "Uscita"))
    cliente = models.ForeignKey("anagrafiche.Anagrafica", on_delete=models.CASCADE, related_name="protocol_counters")
    anno = models.PositiveIntegerField()
    direzione = models.CharField(max_length=3, choices=DIREZIONE)
    last_number = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (("cliente", "anno", "direzione"),)
        indexes = [models.Index(fields=["cliente", "anno", "direzione"])]
        verbose_name = _("Contatore protocollo")
        verbose_name_plural = _("Contatori protocollo")

    def __str__(self) -> str:
        return f"{self.cliente} {self.anno} {self.direzione}: {self.last_number}"

class MovimentoProtocollo(models.Model):
    DIREZIONE = (("IN", "Entrata"), ("OUT", "Uscita"))

    documento = models.ForeignKey("documenti.Documento", on_delete=models.CASCADE, null=True, blank=True, related_name="movimenti")
    fascicolo = models.ForeignKey("fascicoli.Fascicolo", on_delete=models.CASCADE, null=True, blank=True, related_name="movimenti_protocollo")
    target_content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    target_object_id = models.CharField(max_length=64, null=True, blank=True)
    target_tipo = models.CharField(max_length=50, blank=True, db_index=True)
    target_label = models.CharField(max_length=255, blank=True)
    target_object = GenericForeignKey("target_content_type", "target_object_id")
    cliente = models.ForeignKey("anagrafiche.Anagrafica", on_delete=models.PROTECT, related_name="movimenti")
    direzione = models.CharField(max_length=3, choices=DIREZIONE)
    data = models.DateTimeField(default=timezone.now, db_index=True)

    anno = models.PositiveIntegerField(db_index=True)
    numero = models.PositiveIntegerField(db_index=True)

    operatore = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    destinatario = models.CharField(max_length=255, blank=True, help_text=_("A chi consegni in uscita / da chi ricevi in entrata"))
    destinatario_anagrafica = models.ForeignKey(
        "anagrafiche.Anagrafica",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimenti_protocollo_destinatario",
        help_text=_("Anagrafica collegata al destinatario/mittente."),
    )
    ubicazione = models.ForeignKey("archivio_fisico.UnitaFisica", on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Collocazione fisica in entrata"))

    chiuso = models.BooleanField(default=False, help_text=_("Per OUT: flaggato True quando rientra"))
    rientro_di = models.OneToOneField("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="rientrato_con")
    data_rientro_prevista = models.DateField(null=True, blank=True)

    causale = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["cliente", "anno", "direzione", "numero"]
        indexes = [
            models.Index(fields=["cliente", "anno", "direzione", "numero"]),
            models.Index(fields=["target_tipo", "target_content_type", "target_object_id"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["cliente", "anno", "direzione", "numero"], name="uniq_protocollo_per_cliente_anno_dir_num"),
            models.CheckConstraint(
                check=~models.Q(documento__isnull=False, fascicolo__isnull=False),
                name="chk_doc_fascicolo_xor",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(documento__isnull=False)
                    | models.Q(fascicolo__isnull=False)
                    | models.Q(target_content_type__isnull=False)
                ),
                name="chk_target_presente",
            ),
            models.CheckConstraint(check=models.Q(direzione="IN") | models.Q(rientro_di__isnull=True), name="rientro_di_solo_per_IN"),
            models.CheckConstraint(check=models.Q(numero__gt=0), name="numero_maggiore_zero"),
        ]
        verbose_name = _("Movimento di protocollo")
        verbose_name_plural = _("Movimenti di protocollo")

    def __str__(self) -> str:
        target = self.target_label or self.documento or self.fascicolo or self.target_object or _("Oggetto")
        return f"{target} - {self.anno}/{self.numero:06d} ({self.get_direzione_display()})"

    @dataclass
    class TargetMetadata:
        obj: object
        kind: str
        cliente: Anagrafica
        content_type: ContentType
        object_id: str
        label: str
        tipo: str
        documento: Optional[object] = None
        fascicolo: Optional[object] = None

    @classmethod
    def _build_target_metadata(cls, *, target=None, documento=None, fascicolo=None) -> "MovimentoProtocollo.TargetMetadata":
        if target is not None and (documento is not None or fascicolo is not None):
            raise ValidationError(_("Specificare il target generico oppure documento/fascicolo, non entrambi."))

        obj = target or documento or fascicolo
        if obj is None:
            raise ValidationError(_("È necessario specificare un oggetto da protocollare."))

        obj = cls._force_evaluate(obj)
        content_type = ContentType.objects.get_for_model(obj, for_concrete_model=False)
        object_id = str(getattr(obj, "pk", None) or getattr(obj, "id", None))
        if not object_id:
            raise ValidationError(_("L'oggetto indicato non ha un identificativo valido."))

        label = getattr(obj, "protocollo_label", None) or str(obj)
        tipo = getattr(obj, "protocollo_tipo", None) or content_type.model

        cliente_attr = getattr(obj, "cliente", None) or getattr(obj, "anagrafica", None)
        if cliente_attr is None:
            raise ValidationError(_("L'oggetto indicato non espone un cliente associato."))
        cliente = cls._normalize_cliente(cliente_attr)

        from documenti.models import Documento as DocumentoModel
        from fascicoli.models import Fascicolo as FascicoloModel

        if isinstance(obj, DocumentoModel):
            return cls.TargetMetadata(
                obj=obj,
                kind="documento",
                cliente=cliente,
                content_type=content_type,
                object_id=object_id,
                label=label,
                tipo="documento",
                documento=obj,
            )

        if isinstance(obj, FascicoloModel):
            return cls.TargetMetadata(
                obj=obj,
                kind="fascicolo",
                cliente=cliente,
                content_type=content_type,
                object_id=object_id,
                label=label,
                tipo="fascicolo",
                fascicolo=obj,
            )

        return cls.TargetMetadata(
            obj=obj,
            kind="generico",
            cliente=cliente,
            content_type=content_type,
            object_id=object_id,
            label=label,
            tipo=tipo,
        )

    @staticmethod
    @transaction.atomic
    def _next_progressivo(cliente, anno: int, direzione: str) -> int:
        for _ in range(5):
            try:
                counter, _ = ProtocolloCounter.objects.get_or_create(
                    cliente=cliente, anno=anno, direzione=direzione, defaults={"last_number": 0}
                )
                ProtocolloCounter.objects.filter(pk=counter.pk).update(last_number=F("last_number") + 1)
                counter.refresh_from_db(fields=["last_number"])
                return counter.last_number
            except IntegrityError:
                continue
        raise RuntimeError("Impossibile generare progressivo protocollo")

    @staticmethod
    def _force_evaluate(obj):
        """Forza la valutazione di SimpleLazyObject senza introdurre dipendenze runtime."""
        if isinstance(obj, SimpleLazyObject):
            if getattr(obj, "_wrapped", SimpleLazyObject.empty) is SimpleLazyObject.empty:
                obj._setup()
            return obj._wrapped
        return obj

    @classmethod
    def _normalize_cliente(cls, cliente):
        cliente = cls._force_evaluate(cliente)
        if cliente is None:
            raise ValidationError(_("Cliente associato non valido: attesa un'anagrafica."))

        if isinstance(cliente, Anagrafica):
            return cliente

        related = cls._force_evaluate(getattr(cliente, "anagrafica", None))
        if isinstance(related, Anagrafica):
            return related

        anagrafica_id = getattr(cliente, "anagrafica_id", None)
        if anagrafica_id:
            try:
                return Anagrafica.objects.get(pk=anagrafica_id)
            except Anagrafica.DoesNotExist:
                raise ValidationError(_("Cliente associato non valido: attesa un'anagrafica.")) from None

        raise ValidationError(_("Cliente associato non valido: attesa un'anagrafica."))

    @classmethod
    def _get_protocollo_fascicolo(cls, fascicolo):
        return cls.objects.filter(fascicolo=fascicolo).order_by("data").first()

    @classmethod
    def _get_protocollo_documento(cls, documento):
        return cls.objects.filter(documento=documento).order_by("data").first()

    @classmethod
    def _get_out_aperto(cls, metadata: "MovimentoProtocollo.TargetMetadata"):
        return cls.objects.filter(
            target_content_type=metadata.content_type,
            target_object_id=metadata.object_id,
            direzione="OUT",
            chiuso=False,
        ).order_by("-data").first()

    @classmethod
    def _resolve_documento_ubicazione(cls, documento, ubicazione):
        from documenti.models import Documento as DocumentoModel
        if not isinstance(documento, DocumentoModel):
            return ubicazione
        if documento.digitale:
            if ubicazione is not None:
                raise ValidationError(_("Per i documenti digitali non va indicata l'ubicazione."))
            return None
        # Documento cartaceo
        if documento.fascicolo_id:
            fascicolo_mov = cls._get_protocollo_fascicolo(documento.fascicolo)
            fascicolo_ubicazione = None
            if fascicolo_mov and fascicolo_mov.ubicazione:
                fascicolo_ubicazione = fascicolo_mov.ubicazione
            elif getattr(documento.fascicolo, "ubicazione", None):
                fascicolo_ubicazione = documento.fascicolo.ubicazione

            if fascicolo_ubicazione:
                if ubicazione and ubicazione != fascicolo_ubicazione:
                    raise ValidationError(_("L'ubicazione del documento cartaceo deve coincidere con quella del fascicolo."))
                return fascicolo_ubicazione

            if ubicazione is None:
                raise ValidationError(_("Per i documenti cartacei collegati a un fascicolo senza protocollo è obbligatorio indicare l'ubicazione."))
            return ubicazione
        if ubicazione is None:
            raise ValidationError(_("Per i documenti cartacei non fascicolati è obbligatorio indicare l'ubicazione."))
        return ubicazione

    @classmethod
    def _resolve_fascicolo_ubicazione(cls, fascicolo, ubicazione, *, direzione: str):
        from fascicoli.models import Fascicolo as FascicoloModel
        if not isinstance(fascicolo, FascicoloModel):
            return ubicazione
        ha_ubicazione = bool(fascicolo.ubicazione_id)
        if ha_ubicazione or ubicazione is not None:
            if ubicazione is None:
                raise ValidationError(_("Per i fascicoli cartacei è obbligatorio indicare l'ubicazione."))
            return ubicazione
        # fascicolo digitale: l'ubicazione deve restare vuota
        return None

    @staticmethod
    def _sync_documento_ubicazione(documento, ubicazione):
        from documenti.models import Documento as DocumentoModel

        nuova_ubicazione = None if documento.digitale else ubicazione
        nuova_id = getattr(nuova_ubicazione, "pk", None)
        current_id = getattr(documento, "ubicazione_id", None)
        if current_id != nuova_id:
            DocumentoModel.objects.filter(pk=documento.pk).update(ubicazione_id=nuova_id)
            documento.ubicazione_id = nuova_id
        documento.ubicazione = nuova_ubicazione

    @staticmethod
    def _sync_fascicolo_ubicazione(fascicolo, ubicazione, *, sincronizza_documenti: bool = True):
        from fascicoli.models import Fascicolo as FascicoloModel
        from documenti.models import Documento as DocumentoModel

        nuova_id = getattr(ubicazione, "pk", None)
        current_id = getattr(fascicolo, "ubicazione_id", None)
        if current_id != nuova_id:
            FascicoloModel.objects.filter(pk=fascicolo.pk).update(ubicazione_id=nuova_id)
            fascicolo.ubicazione_id = nuova_id
        fascicolo.ubicazione = ubicazione
        if sincronizza_documenti:
            DocumentoModel.objects.filter(fascicolo_id=fascicolo.pk, digitale=False).update(ubicazione_id=nuova_id)

    @staticmethod
    def _normalize_destinatario_label(label: str, anagrafica: Optional[Anagrafica]) -> str:
        normalized = (label or "").strip()
        if normalized:
            return normalized
        if anagrafica:
            display_name = getattr(anagrafica, "display_name", None)
            if callable(display_name):
                return display_name()
            return str(anagrafica)
        return ""

    @classmethod
    @transaction.atomic
    def registra_uscita(cls, *, target=None, documento=None, fascicolo=None, quando=None, operatore=None,
                        a_chi: str = "", data_rientro_prevista=None,
                        causale: str = "", note: str = "",
                        ubicazione=None, destinatario_anagrafica: Optional[Anagrafica] = None) -> "MovimentoProtocollo":
        metadata = cls._build_target_metadata(target=target, documento=documento, fascicolo=fascicolo)
        documento = metadata.documento
        fascicolo = metadata.fascicolo
        quando = quando or timezone.now()
        anno = quando.year
        cliente = metadata.cliente
        target_kwargs = dict(
            target_content_type=metadata.content_type,
            target_object_id=metadata.object_id,
            target_tipo=metadata.tipo,
            target_label=metadata.label,
        )

        if documento:
            from documenti.models import Documento as DocumentoModel
            if not documento.tracciabile:
                raise ValidationError(_("Documento non tracciabile: impossibile registrare uscita"))
            resolved_ubicazione = cls._resolve_documento_ubicazione(documento, ubicazione)
            updated = DocumentoModel.objects.filter(pk=documento.pk, out_aperto=False).update(out_aperto=True)
            if updated == 0:
                raise ValidationError(_("Esiste già una uscita aperta per questo documento"))
            try:
                numero = cls._next_progressivo(cliente, anno, "OUT")
                movimento = cls.objects.create(
                    documento=documento,
                    cliente=cliente,
                    direzione="OUT", data=quando, anno=anno, numero=numero,
                    operatore=operatore,
                    destinatario=cls._normalize_destinatario_label(a_chi, destinatario_anagrafica),
                    destinatario_anagrafica=destinatario_anagrafica,
                    data_rientro_prevista=data_rientro_prevista, causale=causale, note=note,
                    chiuso=False, ubicazione=resolved_ubicazione,
                    **target_kwargs,
                )
                cls._sync_documento_ubicazione(documento, resolved_ubicazione)
                if not documento.digitale and documento.fascicolo_id:
                    cls._sync_fascicolo_ubicazione(documento.fascicolo, resolved_ubicazione)
                return movimento
            except Exception:
                DocumentoModel.objects.filter(pk=documento.pk, out_aperto=True).update(out_aperto=False)
                raise

        if fascicolo:
            resolved_ubicazione = cls._resolve_fascicolo_ubicazione(fascicolo, ubicazione, direzione="OUT")
            numero = cls._next_progressivo(cliente, anno, "OUT")
            movimento = cls.objects.create(
                fascicolo=fascicolo,
                cliente=cliente,
                direzione="OUT", data=quando, anno=anno, numero=numero,
                operatore=operatore,
                destinatario=cls._normalize_destinatario_label(a_chi, destinatario_anagrafica),
                destinatario_anagrafica=destinatario_anagrafica,
                data_rientro_prevista=data_rientro_prevista, causale=causale, note=note,
                chiuso=False, ubicazione=resolved_ubicazione,
                **target_kwargs,
            )
            cls._sync_fascicolo_ubicazione(fascicolo, resolved_ubicazione)
            return movimento

        numero = cls._next_progressivo(cliente, anno, "OUT")
        return cls.objects.create(
            cliente=cliente,
            direzione="OUT", data=quando, anno=anno, numero=numero,
            operatore=operatore,
            destinatario=cls._normalize_destinatario_label(a_chi, destinatario_anagrafica),
            destinatario_anagrafica=destinatario_anagrafica,
            data_rientro_prevista=data_rientro_prevista, causale=causale, note=note,
            chiuso=False, ubicazione=ubicazione,
            **target_kwargs,
        )

    @classmethod
    @transaction.atomic
    def registra_entrata(cls, *, target=None, documento=None, fascicolo=None, quando=None, operatore=None,
                         da_chi: str = "", ubicazione=None,
                         causale: str = "", note: str = "",
                         destinatario_anagrafica: Optional[Anagrafica] = None) -> "MovimentoProtocollo":
        metadata = cls._build_target_metadata(target=target, documento=documento, fascicolo=fascicolo)
        documento = metadata.documento
        fascicolo = metadata.fascicolo
        quando = quando or timezone.now()
        anno = quando.year
        cliente = metadata.cliente
        target_kwargs = dict(
            target_content_type=metadata.content_type,
            target_object_id=metadata.object_id,
            target_tipo=metadata.tipo,
            target_label=metadata.label,
        )
        if documento:
            out_aperto = cls._get_out_aperto(metadata)
            resolved_ubicazione = cls._resolve_documento_ubicazione(documento, ubicazione)
            numero = cls._next_progressivo(cliente, anno, "IN")
            mov_in = cls.objects.create(
                documento=documento,
                cliente=cliente,
                direzione="IN", data=quando, anno=anno, numero=numero,
                operatore=operatore,
                destinatario=cls._normalize_destinatario_label(da_chi, destinatario_anagrafica),
                destinatario_anagrafica=destinatario_anagrafica,
                ubicazione=resolved_ubicazione, causale=causale, note=note,
                **target_kwargs,
            )
            if out_aperto:
                out_aperto.chiuso = True
                out_aperto.save(update_fields=["chiuso"])
                mov_in.rientro_di = out_aperto
                mov_in.save(update_fields=["rientro_di"])
                from documenti.models import Documento as DocumentoModel
                DocumentoModel.objects.filter(pk=documento.pk, out_aperto=True).update(out_aperto=False)
            cls._sync_documento_ubicazione(documento, resolved_ubicazione)
            if not documento.digitale and documento.fascicolo_id:
                cls._sync_fascicolo_ubicazione(documento.fascicolo, resolved_ubicazione)
            return mov_in

        if fascicolo:
            out_aperto = cls._get_out_aperto(metadata)
            resolved_ubicazione = cls._resolve_fascicolo_ubicazione(fascicolo, ubicazione, direzione="IN")
            numero = cls._next_progressivo(cliente, anno, "IN")
            mov_in = cls.objects.create(
                fascicolo=fascicolo,
                cliente=cliente,
                direzione="IN", data=quando, anno=anno, numero=numero,
                operatore=operatore,
                destinatario=cls._normalize_destinatario_label(da_chi, destinatario_anagrafica),
                destinatario_anagrafica=destinatario_anagrafica,
                ubicazione=resolved_ubicazione, causale=causale, note=note,
                **target_kwargs,
            )
            if out_aperto:
                out_aperto.chiuso = True
                out_aperto.save(update_fields=["chiuso"])
                mov_in.rientro_di = out_aperto
                mov_in.save(update_fields=["rientro_di"])
            cls._sync_fascicolo_ubicazione(fascicolo, resolved_ubicazione)
            return mov_in

        out_aperto = cls._get_out_aperto(metadata)
        numero = cls._next_progressivo(cliente, anno, "IN")
        mov_in = cls.objects.create(
            cliente=cliente,
            direzione="IN", data=quando, anno=anno, numero=numero,
            operatore=operatore,
            destinatario=cls._normalize_destinatario_label(da_chi, destinatario_anagrafica),
            destinatario_anagrafica=destinatario_anagrafica,
            ubicazione=ubicazione, causale=causale, note=note,
            **target_kwargs,
        )
        if out_aperto:
            out_aperto.chiuso = True
            out_aperto.save(update_fields=["chiuso"])
            mov_in.rientro_di = out_aperto
            mov_in.save(update_fields=["rientro_di"])
        return mov_in
