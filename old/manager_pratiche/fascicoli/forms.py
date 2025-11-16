from django import forms
from .models import Fascicolo

class FascicoloForm(forms.ModelForm):
    class Meta:
        model = Fascicolo
        fields = "__all__"

class ProtocolloFascicoloForm(forms.Form):
    numero = forms.CharField(label="Numero di protocollo", max_length=50)
    data = forms.DateField(label="Data", widget=forms.DateInput(attrs={"type": "date"}))