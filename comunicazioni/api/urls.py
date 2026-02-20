from rest_framework.routers import DefaultRouter
from django.urls import path

from comunicazioni.api.views import (
    ComunicazioneViewSet,
    EmailContattoViewSet,
    MailingListViewSet,
    EmailImportViewSet,
    TemplateContextFieldViewSet,
    TemplateComunicazioneViewSet,
    FirmaComunicazioneViewSet,
    CodiceTributoF24ViewSet,
    AllegatoComunicazioneViewSet,
)

router = DefaultRouter()
router.register(r"comunicazioni", ComunicazioneViewSet, basename="api-comunicazioni")
router.register(r"contatti", EmailContattoViewSet, basename="api-contatti")
router.register(r"liste", MailingListViewSet, basename="api-liste")
router.register(r"email-import", EmailImportViewSet, basename="api-email-import")
router.register(r"template-fields", TemplateContextFieldViewSet, basename="api-template-fields")
router.register(r"templates", TemplateComunicazioneViewSet, basename="api-templates")
router.register(r"firme", FirmaComunicazioneViewSet, basename="api-firme")
router.register(r"codici-tributo", CodiceTributoF24ViewSet, basename="api-codici-tributo")

# Nested route per allegati
urlpatterns = router.urls + [
    path('comunicazioni/<int:comunicazione_id>/allegati/', 
         AllegatoComunicazioneViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='api-allegati-list'),
    path('comunicazioni/<int:comunicazione_id>/allegati/<int:pk>/', 
         AllegatoComunicazioneViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='api-allegati-detail'),
]
