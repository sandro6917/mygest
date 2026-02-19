"""
URLs per API Anagrafiche
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnagraficaViewSet, ClienteViewSet, ClientiTipoViewSet, ComuneItalianoViewSet

router = DefaultRouter()
router.register(r'anagrafiche', AnagraficaViewSet, basename='anagrafica')
router.register(r'clienti', ClienteViewSet, basename='cliente')
router.register(r'tipi-cliente', ClientiTipoViewSet, basename='tipo-cliente')
router.register(r'comuni', ComuneItalianoViewSet, basename='comune-italiano')

urlpatterns = router.urls
