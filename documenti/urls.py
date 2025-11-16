from django.urls import path
from . import views

app_name = "documenti"

urlpatterns = [
    path("", views.home, name="home"),
    path("nuovo/", views.nuovo_dinamico, name="nuovo_dinamico"),
    path("modifica/<int:pk>/", views.documento_modifica_dinamico, name="modifica_dinamico"),
    path("dettaglio/<int:pk>/", views.documento_dettaglio, name="dettaglio"),
    path("collocazione/<int:pk>/", views.documento_collocazione, name="collocazione"),
    path("collocazione/<int:pk>/delete-last/", views.documento_collocazione_delete_last, name="collocazione_delete_last"),
    # nuovo: protocollazione documento (POST)
    path("protocolla/<int:pk>/", views.protocolla_documento, name="protocolla"),
]