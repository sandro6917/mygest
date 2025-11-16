from django.urls import path
from . import views

app_name = "documenti"

urlpatterns = [
    path("", views.home, name="home"),
    path("nuovo/", views.documento_nuovo_dinamico, name="nuovo_dinamico"),
    path("nuovo/<int:tipo_id>/", views.documento_nuovo_dinamico_tipo, name="nuovo_dinamico_tipo"),
    path("modifica/<int:pk>/", views.documento_modifica_dinamico, name="modifica_dinamico"),
    path("protocolla/<int:pk>/", views.documento_protocolla, name="protocolla"),
    path("dettaglio/<int:pk>/", views.documento_dettaglio, name="dettaglio"),
    path("collocazione/<int:pk>/", views.documento_collocazione, name="collocazione"),  # nuovo
    path("collocazione/<int:pk>/delete-last/", views.documento_collocazione_delete_last, name="collocazione_delete_last"),  # nuovo
]