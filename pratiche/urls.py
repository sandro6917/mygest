from django.urls import path
from . import views

app_name = "pratiche"

urlpatterns = [
    path("", views.home, name="home"),
    path("tipi/<int:pk>/", views.tipo_dettaglio, name="tipo_dettaglio"),
    path("nuova/", views.pratica_nuova, name="nuova"),
    path("modifica/<int:pk>/", views.pratica_modifica, name="modifica"),
    path("dettaglio/<int:pk>/", views.pratica_dettaglio, name="dettaglio"),
    path("<int:pk>/collega-fascicolo/", views.collega_fascicolo, name="collega_fascicolo"),
    path("<int:pk>/collega-pratica/", views.collega_pratica, name="collega_pratica"),
    path("note/nuova/<int:pratica_pk>/", views.nota_nuova, name="nota_nuova"),
    path("note/<int:pk>/modifica/", views.nota_modifica, name="nota_modifica"),
    path('<int:pk>/stampa/<slug:slug>/', views.stampa_lista, name='stampa_lista'),
]