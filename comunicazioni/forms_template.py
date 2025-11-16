from django import forms

from .models_template import FirmaComunicazione, TemplateComunicazione

class TemplateComunicazioneForm(forms.ModelForm):
    class Meta:
        model = TemplateComunicazione
        fields = ["nome", "oggetto", "corpo_testo", "corpo_html", "attivo"]


class FirmaComunicazioneForm(forms.ModelForm):
    class Meta:
        model = FirmaComunicazione
        fields = ["nome", "corpo_testo", "corpo_html", "attivo"]
