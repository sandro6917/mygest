from __future__ import annotations
from typing import Optional

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
    cliente = models.ForeignKey("anagrafiche.Anagrafica", on_delete=models.PROTECT, related_name="movimenti")
    direzione = models.CharField(max_length=3, choices=DIREZIONE)
    data = models.DateTimeField(default=timezone.now, db_index=True)

    anno = models.PositiveIntegerField(db_index=True)
    numero = models.PositiveIntegerField(db_index=True)

    operatore = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    destinatario = models.CharField(max_length=255, blank=True, help_text=_("A chi consegni in uscita / da chi ricevi in entrata"))
    ubicazione = models.ForeignKey("archivio_fisico.UnitaFisica", on_delete=models.SET_NULL, null=True, blank=True, help_text=_("Collocazione fisica in entrata"))

    chiuso = models.BooleanField(default=False, help_text=_("Per OUT: flaggato True quando rientra"))
    rientro_di = models.OneToOneField("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="rientrato_con")
    data_rientro_prevista = models.DateField(null=True, blank=True)

    causale = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["cliente", "anno", "direzione", "numero"]
        indexes = [
            models.Index(fields=["documento", "direzione", "chiuso"]),
            models.Index(fields=["fascicolo", "direzione", "chiuso"]),
            models.Index(fields=["cliente", "anno", "direzione", "numero"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["cliente", "anno", "direzione", "numero"], name="uniq_protocollo_per_cliente_anno_dir_num"),
            # esattamente uno tra documento e fascicolo
            models.CheckConstraint(
                check=(models.Q(documento__isnull=False, fascicolo__isnull=True) | models.Q(documento__isnull=True, fascicolo__isnull=False)),
                name="chk_one_target_set",
            ),
            models.CheckConstraint(check=models.Q(direzione="IN") | models.Q(rientro_di__isnull=True), name="rientro_di_solo_per_IN"),
            models.CheckConstraint(check=models.Q(numero__gt=0), name="numero_maggiore_zero"),
        ]
        verbose_name = _("Movimento di protocollo")
        verbose_name_plural = _("Movimenti di protocollo")

    def __str__(self) -> str:
        target = self.documento or self.fascicolo
        return f"{target} - {self.anno}/{self.numero:06d} ({self.get_direzione_display()})"

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
    def _ensure_univoco(cls, *, documento=None, fascicolo=None):
        if documento is not None and cls.objects.filter(documento=documento).exists():
            raise ValidationError(_("Il documento risulta già protocollato."))
        if fascicolo is not None and cls.objects.filter(fascicolo=fascicolo).exists():
            raise ValidationError(_("Il fascicolo risulta già protocollato."))

    @classmethod
    def _get_protocollo_fascicolo(cls, fascicolo):
        return cls.objects.filter(fascicolo=fascicolo).order_by("data").first()

    @classmethod
    def _get_protocollo_documento(cls, documento):
        return cls.objects.filter(documento=documento).order_by("data").first()

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

    @classmethod
    @transaction.atomic
    def registra_uscita(cls, *, documento=None, fascicolo=None, quando=None, operatore=None,
                        a_chi: str = "", data_rientro_prevista=None,
                        causale: str = "", note: str = "",
                        ubicazione=None) -> "MovimentoProtocollo":
        # valida target
        if bool(documento) == bool(fascicolo):
            raise ValidationError(_("Specificare solo documento OPPURE fascicolo"))
        quando = quando or timezone.now()
        anno = quando.year
        if documento:
            from documenti.models import Documento as DocumentoModel
            if not documento.tracciabile:
                raise ValidationError(_("Documento non tracciabile: impossibile registrare uscita"))
            cls._ensure_univoco(documento=documento)
            resolved_ubicazione = cls._resolve_documento_ubicazione(documento, ubicazione)
            updated = DocumentoModel.objects.filter(pk=documento.pk, out_aperto=False).update(out_aperto=True)
            if updated == 0:
                raise ValidationError(_("Esiste già una uscita aperta per questo documento"))
            cliente = cls._normalize_cliente(documento.cliente)
            try:
                numero = cls._next_progressivo(cliente, anno, "OUT")
                return cls.objects.create(
                    documento=documento, cliente=cliente,
                    direzione="OUT", data=quando, anno=anno, numero=numero,
                    operatore=operatore, destinatario=a_chi or "",
                    data_rientro_prevista=data_rientro_prevista, causale=causale, note=note,
                    chiuso=False, ubicazione=resolved_ubicazione
                )
            except Exception:
                DocumentoModel.objects.filter(pk=documento.pk, out_aperto=True).update(out_aperto=False)
                raise
        else:
            cliente = cls._normalize_cliente(fascicolo.cliente)
            cls._ensure_univoco(fascicolo=fascicolo)
            resolved_ubicazione = cls._resolve_fascicolo_ubicazione(fascicolo, ubicazione, direzione="OUT")
            numero = cls._next_progressivo(cliente, anno, "OUT")
            movimento = cls.objects.create(
                fascicolo=fascicolo, cliente=cliente,
                direzione="OUT", data=quando, anno=anno, numero=numero,
                operatore=operatore, destinatario=a_chi or "",
                data_rientro_prevista=data_rientro_prevista, causale=causale, note=note,
                chiuso=False, ubicazione=resolved_ubicazione
            )
            if resolved_ubicazione is not None:
                type(fascicolo).objects.filter(pk=fascicolo.pk).update(ubicazione=resolved_ubicazione)
            return movimento

    @classmethod
    @transaction.atomic
    def registra_entrata(cls, *, documento=None, fascicolo=None, quando=None, operatore=None,
                         da_chi: str = "", ubicazione=None,
                         causale: str = "", note: str = "") -> "MovimentoProtocollo":
        if bool(documento) == bool(fascicolo):
            raise ValidationError(_("Specificare solo documento OPPURE fascicolo"))
        quando = quando or timezone.now()
        anno = quando.year
        if documento:
            out_aperto = cls.objects.filter(documento=documento, direzione="OUT", chiuso=False).order_by("-data").first()
            cliente = cls._normalize_cliente(documento.cliente)
            cls._ensure_univoco(documento=documento)
            resolved_ubicazione = cls._resolve_documento_ubicazione(documento, ubicazione)
            numero = cls._next_progressivo(cliente, anno, "IN")
            mov_in = cls.objects.create(
                documento=documento, cliente=cliente,
                direzione="IN", data=quando, anno=anno, numero=numero,
                operatore=operatore, destinatario=da_chi or "",
                ubicazione=resolved_ubicazione, causale=causale, note=note
            )
            if out_aperto:
                out_aperto.chiuso = True
                out_aperto.save(update_fields=["chiuso"])
                mov_in.rientro_di = out_aperto
                mov_in.save(update_fields=["rientro_di"])
                from documenti.models import Documento as DocumentoModel
                DocumentoModel.objects.filter(pk=documento.pk, out_aperto=True).update(out_aperto=False)
            return mov_in
        else:
            out_aperto = cls.objects.filter(fascicolo=fascicolo, direzione="OUT", chiuso=False).order_by("-data").first()
            cliente = cls._normalize_cliente(fascicolo.cliente)
            cls._ensure_univoco(fascicolo=fascicolo)
            resolved_ubicazione = cls._resolve_fascicolo_ubicazione(fascicolo, ubicazione, direzione="IN")
            numero = cls._next_progressivo(cliente, anno, "IN")
            mov_in = cls.objects.create(
                fascicolo=fascicolo, cliente=cliente,
                direzione="IN", data=quando, anno=anno, numero=numero,
                operatore=operatore, destinatario=da_chi or "",
                ubicazione=resolved_ubicazione, causale=causale, note=note
            )
            if out_aperto:
                out_aperto.chiuso = True
                out_aperto.save(update_fields=["chiuso"])
                mov_in.rientro_di = out_aperto
                mov_in.save(update_fields=["rientro_di"])
            if resolved_ubicazione is not None:
                type(fascicolo).objects.filter(pk=fascicolo.pk).update(ubicazione=resolved_ubicazione)
            return mov_in
