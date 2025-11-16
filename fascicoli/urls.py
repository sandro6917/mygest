from django.urls import path
from django.views.generic.base import RedirectView
from . import views
from .views import FascicoloDetailView

app_name = "fascicoli"

urlpatterns = [
    path("", views.home, name="home"),
    path("nuovo/", views.fascicolo_nuovo, name="nuovo"),
    path("<int:pk>/modifica/", views.fascicolo_modifica, name="modifica"),
    path("<int:pk>/protocolla/", views.protocolla_fascicolo, name="protocolla"),
    path("fascicoli/<int:pk>/", FascicoloDetailView.as_view(), name="detail"),
    path("<int:pk>/archivio/", views.archivio_browse, name="archivio"),
    path("<int:pk>/archivio/<path:subpath>/", views.archivio_browse, name="archivio_sub"),
    path("<int:pk>/archivio/file/<path:subpath>", views.archivio_download, name="archivio_file"),
    path("<int:pk>/collega/", views.fascicolo_collega, name="collega"),
]