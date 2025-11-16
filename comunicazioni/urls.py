from django.urls import path

from . import views

app_name = "comunicazioni"

urlpatterns = [
    path("", views.lista_comunicazioni, name="home"),
    path("nuova/", views.crea_comunicazione, name="create"),
    path("<int:pk>/", views.dettaglio_comunicazione, name="detail"),
    path("<int:pk>/modifica/", views.modifica_comunicazione, name="edit"),
    path("<int:pk>/invia/", views.invia_comunicazione, name="send"),
    path("<int:pk>/protocolla/", views.protocolla_comunicazione, name="protocolla"),
    path("<int:pk>/allegati/aggiungi/", views.aggiungi_allegato, name="attachments-add"),
    path(
        "<int:pk>/allegati/<int:allegato_pk>/rimuovi/",
        views.rimuovi_allegato,
        name="attachments-remove",
    ),
    path("api/contatti/", views.autocomplete_contatti, name="api-contatti-autocomplete"),
    path("api/liste/", views.autocomplete_liste, name="api-liste-autocomplete"),
]
