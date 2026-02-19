"""
URLs per API Documenti v1
"""
from rest_framework.routers import DefaultRouter
from .views import DocumentoViewSet, DocumentiTipoViewSet, ImportSessionViewSet

router = DefaultRouter()
# IMPORTANTE: registra prima i path più specifici
router.register(r'import-sessions', ImportSessionViewSet, basename='import-session')
router.register(r'tipi', DocumentiTipoViewSet, basename='tipo-documento')
router.register(r'', DocumentoViewSet, basename='documento')

urlpatterns = router.urls


