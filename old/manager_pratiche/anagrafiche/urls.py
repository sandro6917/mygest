from django.urls import path
from core.views import anagrafica_detail
from . import views

app_name = "anagrafiche"

urlpatterns = [
    path("", views.home, name="home"),
    path("anagrafica/add/", views.AnagraficaCreateView.as_view(), name="create"),
    path("anagrafica/<int:pk>/", views.detail, name="detail"),
    path("anagrafica/<int:pk>/edit/", views.AnagraficaUpdateView.as_view(), name="edit"),
    path("anagrafica/<int:pk>/delete/", views.AnagraficaDeleteView.as_view(), name="delete"),
    path("<int:pk>/", anagrafica_detail, name="dettaglio"),
]