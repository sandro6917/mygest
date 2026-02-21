from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from mygest.views import (
    home, 
    help_index, 
    help_topic, 
    react_spa,
    serve_deployment_guide_html,
    serve_deployment_guide_pdf,
)
from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API v1 endpoints (for React SPA)
    path("api/v1/", include("api.v1.urls")),
    
    # Traditional Django URLs (kept for backwards compatibility)
    path("accounts/", include("django.contrib.auth.urls")),
    path("anagrafiche/", include("anagrafiche.urls", namespace="anagrafiche")),
    path("documenti/", include(("documenti.urls", "documenti"), namespace="documenti")),
    path("comunicazioni/", include(("comunicazioni.urls", "comunicazioni"), namespace="comunicazioni")),
    path("fascicoli/", include(("fascicoli.urls", "fascicoli"), namespace="fascicoli")),
    path("etichette/", include("stampe.urls", namespace="stampe")),
    path("archivio-fisico/", include(("archivio_fisico.urls", "archivio_fisico"), namespace="archivio_fisico")),
    path("protocollo/", include("protocollo.urls", namespace="protocollo")),
    path("pratiche/", include(("pratiche.urls", "pratiche"), namespace="pratiche")),
    path("scadenze/", include(("scadenze.urls", "scadenze"), namespace="scadenze")),
    path("api/", include(("comunicazioni.api.urls", "comunicazioni_api"), namespace="comunicazioni-api")),
    path("whatsapp/", include(("whatsapp.urls", "whatsapp"), namespace="whatsapp")),
    path("help/", help_index, name="help-index"),
    path("help/<slug:slug>/", help_topic, name="help-topic"),
    path("guide/deployment.html", serve_deployment_guide_html, name="guide-deployment-html"),
    path("guide/deployment.pdf", serve_deployment_guide_pdf, name="guide-deployment-pdf"),
    path("graphql/", login_required(GraphQLView.as_view(graphiql=True))),
    
    # Home page (for reverse('home') in tests and templates)
    path("", home, name="home"),
    
    # React SPA catch-all (must be last!)
    # Matches all routes not matched above and serves React frontend
    re_path(r'^.*$', react_spa, name="react-spa"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.ARCHIVIO_BASE_PATH)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
