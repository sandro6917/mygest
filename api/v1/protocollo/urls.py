"""
URL patterns per API Protocollo
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovimentoProtocolloViewSet, ProtocolloCounterViewSet

router = DefaultRouter()
router.register(r'movimenti', MovimentoProtocolloViewSet, basename='movimento-protocollo')
router.register(r'contatori', ProtocolloCounterViewSet, basename='protocollo-counter')

urlpatterns = [
    path('', include(router.urls)),
]
