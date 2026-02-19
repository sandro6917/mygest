"""
URL routing per AI Classifier app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_filesystem import FileSystemViewSet

app_name = 'ai_classifier'

# DRF Router
router = DefaultRouter()
router.register(r'jobs', views.ClassificationJobViewSet, basename='job')
router.register(r'results', views.ClassificationResultViewSet, basename='result')
router.register(r'config', views.ClassifierConfigViewSet, basename='config')
router.register(r'import', views.ImportViewSet, basename='import')
router.register(r'filesystem', FileSystemViewSet, basename='filesystem')

urlpatterns = [
    path('', include(router.urls)),
]
