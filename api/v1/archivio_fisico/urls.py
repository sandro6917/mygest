"""
URLs per API Archivio Fisico
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UnitaFisicaViewSet,
    OperazioneArchivioViewSet,
    RigaOperazioneArchivioViewSet,
    CollocazioneFisicaViewSet,
    DocumentoTracciabileViewSet,
    FascicoloTracciabileViewSet,
    MovimentoProtocolloViewSet,
)

router = DefaultRouter()
router.register(r'unita', UnitaFisicaViewSet, basename='unita-fisica')
router.register(r'operazioni', OperazioneArchivioViewSet, basename='operazione-archivio')
router.register(r'righe', RigaOperazioneArchivioViewSet, basename='riga-operazione')
router.register(r'collocazioni', CollocazioneFisicaViewSet, basename='collocazione-fisica')
router.register(r'documenti-tracciabili', DocumentoTracciabileViewSet, basename='documento-tracciabile')
router.register(r'fascicoli-tracciabili', FascicoloTracciabileViewSet, basename='fascicolo-tracciabile')
router.register(r'movimenti-protocollo', MovimentoProtocolloViewSet, basename='movimento-protocollo')

urlpatterns = [
    path('', include(router.urls)),
]
