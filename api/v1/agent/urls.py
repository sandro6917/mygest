"""
URL configuration per API Agent.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AgentViewSet, agent_status

router = DefaultRouter()
router.register('', AgentViewSet, basename='agent')

urlpatterns = [
    path('status/', agent_status, name='agent-status'),
    path('', include(router.urls)),
]
