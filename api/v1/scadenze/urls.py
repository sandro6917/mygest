"""
URLs per API Scadenze
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScadenzaAlertViewSet, ScadenzaViewSet, ScadenzaOccorrenzaViewSet, webhook_alert_receiver

router = DefaultRouter()
router.register(r'alerts', ScadenzaAlertViewSet, basename='scadenza-alert')
router.register(r'occorrenze', ScadenzaOccorrenzaViewSet, basename='scadenza-occorrenza')
router.register(r'', ScadenzaViewSet, basename='scadenza')

urlpatterns = [
    path('webhook/alert/', webhook_alert_receiver, name='webhook-alert-receiver'),
    path('', include(router.urls)),
]
