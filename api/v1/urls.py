"""
API v1 URLs
"""
from django.urls import path, include
from .views import dashboard_stats, dashboard_stats_simple
from .health import health_check, ready_check, live_check

urlpatterns = [
    # Health checks (monitoring & deploy)
    path('health/', health_check, name='health-check'),
    path('ready/', ready_check, name='ready-check'),
    path('live/', live_check, name='live-check'),
    
    # Authentication endpoints
    path('auth/', include('api.v1.auth.urls')),
    
    # Dashboard
    path('dashboard/stats/', dashboard_stats, name='dashboard-stats'),
    path('dashboard/stats-simple/', dashboard_stats_simple, name='dashboard-stats-simple'),
    
    # Anagrafiche
    path('', include('api.v1.anagrafiche.urls')),
    
    # Documenti
    path('documenti/', include('api.v1.documenti.urls')),
    
    # Pratiche
    path('pratiche/', include('api.v1.pratiche.urls')),
    
    # Fascicoli
    path('fascicoli/', include('api.v1.fascicoli.urls')),
    
    # Scadenze
    path('scadenze/', include('api.v1.scadenze.urls')),
    
    # Comunicazioni
    path('comunicazioni/', include('comunicazioni.api.urls')),
    
    # Agent Desktop
    path('agent/', include('api.v1.agent.urls')),
    
    # Protocollo
    path('protocollo/', include('api.v1.protocollo.urls')),
    
    # Archivio Fisico
    path('archivio-fisico/', include('api.v1.archivio_fisico.urls')),
    
    # AI Classifier
    path('ai-classifier/', include('ai_classifier.urls')),
    
    # TODO: Add more API endpoints
]
