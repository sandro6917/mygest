# nel Python shell
from documenti.models import Documento
from titolario.models import TitolarioVoce
print("doc(8).titolario_voce_id =", Documento.objects.get(pk=8).titolario_voce_id)
print("esiste titolario id=9?   =", TitolarioVoce.objects.filter(id=9).exists())