from __future__ import annotations
from typing import Optional
from django.db import models, transaction
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

class UnitaFisica(models.Model):
    class Tipo(models.TextChoices):
        UFFICIO = "ufficio", "Ufficio"
        STANZA = "stanza", "Stanza"
        SCAFFALE = "scaffale", "Scaffale"
        MOBILE ="mobile", "Mobile"
        ANTA = "anta", "Anta"
        RIPIANO = "ripiano", "Ripiano"
        CONTENITORE = "contenitore", "Contenitore"
        CARTELLINA = "cartellina", "Cartellina"

    # Mappa: tipo padre -> insiemi di tipi figli ammessi
    TIPO_FIGLI_AMMESSI = {
        Tipo.UFFICIO: {Tipo.STANZA},
        Tipo.STANZA: {Tipo.SCAFFALE, Tipo.MOBILE, Tipo.RIPIANO},
        Tipo.MOBILE: {Tipo.ANTA, Tipo.RIPIANO},
        Tipo.ANTA: {Tipo.RIPIANO},
        Tipo.SCAFFALE: {Tipo.RIPIANO},
        Tipo.RIPIANO: {Tipo.CONTENITORE},
        Tipo.CONTENITORE: {Tipo.CARTELLINA},
        Tipo.CARTELLINA: set(),
    }

    codice = models.SlugField(max_length=50, help_text="Codice univoco per il padre", db_index=True)
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="figli", on_delete=models.PROTECT)
    ordine = models.PositiveIntegerField(default=0)
    attivo = models.BooleanField(default=True)
    note = models.TextField(blank=True)
    full_path = models.CharField(max_length=500, blank=True, editable=False)  # es. UFF/U01/ST/01/SF/A/...

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Unità fisica"
        verbose_name_plural = "Unità fisiche"
        ordering = ["parent__id", "ordine", "nome"]
        constraints = [
            models.UniqueConstraint(fields=["parent", "codice"], name="uniq_unita_by_parent_codice"),
        ]

    def __str__(self):
        return f"{self.tipo_label()} {self.nome}"

    def tipo_label(self) -> str:
        return self.get_tipo_display()

    def ancestors(self) -> list["UnitaFisica"]:
        cur, chain = self.parent, []
        while cur:
            chain.append(cur)
            cur = cur.parent
        return list(reversed(chain))

    def build_full_path(self) -> str:
        parts = [u.codice for u in self.ancestors()] + [self.codice]
        return "/".join(parts)

    def clean(self):
        super().clean()
        # vincolo radice: solo UFFICIO può non avere parent
        if self.parent is None and self.tipo != self.Tipo.UFFICIO:
            raise ValidationError({"tipo": "Le unità radice devono essere di tipo UFFICIO."})
        # vincolo figli ammessi in base al tipo del parent
        if self.parent is not None:
            ammessi = self.TIPO_FIGLI_AMMESSI.get(self.parent.tipo, set())
            if self.tipo not in ammessi:
                labels = ", ".join(sorted(self.get_tipo_display() for t in ammessi)) if ammessi else "nessuno"
                raise ValidationError({
                    "tipo": f"Per un {self.parent.get_tipo_display()} sono ammessi solo figli: {labels}."
                })
        # anti-ciclo semplice
        cur = self.parent
        while cur:
            if cur.pk == self.pk and self.pk is not None:
                raise ValidationError({"parent": "Relazione ciclica non consentita."})
            cur = cur.parent

    def save(self, *args, **kwargs):
        # valida sempre prima del salvataggio
        self.full_clean()
        self.full_path = self.build_full_path()
        super().save(*args, **kwargs)
        # aggiorna path dei figli se cambia qualcosa
        for child in self.figli.all():
            if child.full_path != child.build_full_path():
                child.save(update_fields=["full_path", "updated_at"])

class CollocazioneFisica(models.Model):
    # target generico (Documento, Fascicolo, …)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # nuovo: collegamento diretto 1:N con Documento
    documento = models.ForeignKey(
        "documenti.Documento",
        on_delete=models.CASCADE,
        related_name="collocazioni_fisiche",
        null=True, blank=True, db_index=True,
        help_text="Se valorizzato, la collocazione è riferita a un Documento specifico."
    )

    unita = models.ForeignKey(UnitaFisica, on_delete=models.PROTECT, related_name="collocazioni")
    attiva = models.BooleanField(default=True)
    dal = models.DateField(default=timezone.now)
    al = models.DateField(null=True, blank=True)
    note = models.CharField(max_length=250, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Collocazione fisica"
        verbose_name_plural = "Collocazioni fisiche"
        ordering = ["-attiva", "-dal", "-id"]
        indexes = [
            models.Index(fields=["content_type", "object_id", "attiva"]),
            models.Index(fields=["documento", "attiva"]),  # per lookup veloci sul documento
        ]

    def __str__(self):
        target = self.documento or self.content_object
        return f"{target} -> {self.unita} ({'attiva' if self.attiva else 'storico'})"

    def clean(self):
        # vincolo: una sola collocazione attiva per oggetto
        from django.core.exceptions import ValidationError
        if self.attiva:
            if self.documento_id:
                qs = CollocazioneFisica.objects.filter(documento_id=self.documento_id, attiva=True)
            else:
                qs = CollocazioneFisica.objects.filter(
                    content_type=self.content_type,
                    object_id=self.object_id,
                    attiva=True,
                )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Esiste già una collocazione attiva per questo oggetto.")

    def save(self, *args, **kwargs):
        # se è legata a Documento, sincronizza anche la GFK
        if self.documento_id and (not self.content_type_id or not self.object_id):
            self.content_type = ContentType.objects.get_for_model(type(self.documento))
            self.object_id = self.documento_id
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.attiva:
                if self.documento_id:
                    type(self).objects.filter(documento_id=self.documento_id, attiva=True)\
                        .exclude(pk=self.pk).update(attiva=False, al=timezone.now().date())
                else:
                    type(self).objects.filter(content_type=self.content_type, object_id=self.object_id, attiva=True)\
                        .exclude(pk=self.pk).update(attiva=False, al=timezone.now().date())
