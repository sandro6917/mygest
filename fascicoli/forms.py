# filepath: /home/sandro/mygest/fascicoli/forms.py
from django import forms
from django.db import transaction
from datetime import date
from django.contrib.contenttypes.models import ContentType
from .models import Fascicolo
from archivio_fisico.models import UnitaFisica, CollocazioneFisica
from anagrafiche.models import Cliente as ClienteModel

class FascicoloForm(forms.ModelForm):
    class Meta:
        model = Fascicolo
        # Non gestiamo il collegamento alle pratiche nel form (gestito dal contesto o da azioni dedicate)
        exclude = ("pratiche",)

    def __init__(self, *args, **kwargs):
        # pratica di contesto (opzionale), usata per ereditare cliente e collegare M2M post-save
        self._pratica = kwargs.pop("pratica", None)
        super().__init__(*args, **kwargs)
        self.fields["ubicazione"].queryset = UnitaFisica.objects.all().order_by("full_path", "nome")
        self.fields["ubicazione"].label_from_instance = lambda u: f"{u.codice} — {u.full_path or u.nome}"

    def _link_pratica(self, instance: Fascicolo):
        # Collega la pratica M2M solo se presente e se l'istanza ha già un pk
        if self._pratica and getattr(instance, "pk", None):
            instance.pratiche.add(self._pratica)

    @transaction.atomic
    def save(self, commit=True):
        instance = super().save(commit=False)
        # il campo del form è "ubicazione" (FK a UnitaFisica)
        uf: UnitaFisica | None = self.cleaned_data.get("ubicazione")

        # Eredita cliente dalla pratica di contesto, se presente e se il cliente non è già impostato
        if self._pratica and not instance.cliente_id and getattr(self._pratica, "cliente_id", None):
            cli = None
            # se pratica.cliente è già Cliente, usa quello; altrimenti risali da anagrafica_id
            if isinstance(getattr(self._pratica, "cliente", None), ClienteModel):
                cli = self._pratica.cliente
            else:
                cli = ClienteModel.objects.filter(anagrafica_id=self._pratica.cliente_id).order_by("-id").first()
            if cli:
                instance.cliente = cli

        if commit:
            instance.save()
            # Collega la pratica ora che c'è il pk
            self._link_pratica(instance)

            # Trova/aggiorna la CollocazioneFisica attiva per questo fascicolo.
            ct = ContentType.objects.get_for_model(Fascicolo)
            coll = CollocazioneFisica.objects.filter(
                content_type=ct, object_id=instance.pk, attiva=True
            ).select_related("unita").first()

            if uf:
                if coll:
                    if coll.unita_id != uf.id:
                        coll.unita = uf
                        coll.dal = coll.dal or date.today()
                        coll.al = None
                        coll.save(update_fields=["unita", "dal", "al"])
                else:
                    coll = CollocazioneFisica.objects.create(
                        content_type=ct,
                        object_id=instance.pk,
                        unita=uf,
                        attiva=True,
                        dal=date.today(),
                    )
                # collega al model Fascicolo (FK a UnitaFisica)
                if instance.ubicazione_id != uf.id:
                    instance.ubicazione = uf
                    instance.save(update_fields=["ubicazione"])
            else:
                # Nessuna unità selezionata: sgancia la collocazione attiva dal fascicolo
                if instance.ubicazione_id:
                    instance.ubicazione = None
                    instance.save(update_fields=["ubicazione"])

        return instance

    def save_m2m(self):
        # Supporta il flusso save(commit=False) + save_m2m()
        super().save_m2m()
        self._link_pratica(self.instance)


class ProtocolloFascicoloForm(forms.Form):
    numero = forms.CharField(label="Numero di protocollo", max_length=50)
    data = forms.DateField(label="Data", widget=forms.DateInput(attrs={"type": "date"}))