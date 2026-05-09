"""
URL Configuration per AI Classifier API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MLModelViewSet,
    DocumentPredictionViewSet,
    PredictViewSet,
    TrainingJobViewSet,
)
from .views_ai_import import (
    AIImportViewSet,
    TemplateManagementViewSet,
)

# Router per viewsets
router = DefaultRouter()
router.register(r'models', MLModelViewSet, basename='ml-models')
router.register(r'predictions', DocumentPredictionViewSet, basename='predictions')
router.register(r'predict', PredictViewSet, basename='predict')
router.register(r'training-jobs', TrainingJobViewSet, basename='training-jobs')

# AI Import endpoints
router.register(r'ai-import', AIImportViewSet, basename='ai-import')
router.register(r'templates', TemplateManagementViewSet, basename='templates')

urlpatterns = [
    path('', include(router.urls)),
]
