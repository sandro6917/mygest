from rest_framework.routers import DefaultRouter

from comunicazioni.api.views import (
    ComunicazioneViewSet,
    EmailContattoViewSet,
    MailingListViewSet,
    EmailImportViewSet,
    TemplateContextFieldViewSet,
)

router = DefaultRouter()
router.register(r"comunicazioni", ComunicazioneViewSet, basename="api-comunicazioni")
router.register(r"contatti", EmailContattoViewSet, basename="api-contatti")
router.register(r"liste", MailingListViewSet, basename="api-liste")
router.register(r"email-import", EmailImportViewSet, basename="api-email-import")
router.register(r"template-fields", TemplateContextFieldViewSet, basename="api-template-fields")

urlpatterns = router.urls
