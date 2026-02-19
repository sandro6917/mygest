"""
URLs per API Pratiche
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PraticaViewSet, PraticheTipoViewSet, PraticaNotaViewSet

router = DefaultRouter()
router.register(r'tipi', PraticheTipoViewSet, basename='pratiche-tipo')
router.register(r'note', PraticaNotaViewSet, basename='pratica-nota')
router.register(r'', PraticaViewSet, basename='pratica')

urlpatterns = [
    path('', include(router.urls)),
]
