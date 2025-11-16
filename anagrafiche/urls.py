from django.urls import path
from . import views

app_name = "anagrafiche"

urlpatterns = [
    path("", views.home, name="home"),
    path("anagrafica/add/", views.anagrafica_create, name="anagrafica_create"),
    path("anagrafica/<int:pk>/edit/", views.anagrafica_update, name="anagrafica_edit"),
    path("anagrafica/<int:pk>/", views.detail, name="detail"),

    # Gestione indirizzi (pagine dedicate)
    path("anagrafica/<int:pk>/indirizzi/", views.indirizzi_list, name="indirizzi_list"),
    path("anagrafica/<int:anagrafica_pk>/indirizzi/add/", views.IndirizzoCreateView.as_view(), name="indirizzo_add_for_anagrafica"),
    path("indirizzi/<int:pk>/edit/", views.IndirizzoUpdateView.as_view(), name="indirizzo_edit"),

    # Importazione e facsimile CSV
    path("import/", views.import_anagrafiche, name="import"),
    path("facsimile-csv/", views.facsimile_csv, name="facsimile_csv"),
    path("ricalcola-codici/", views.ricalcola_codici, name="ricalcola_codici"),
    path("anagrafica/<int:pk>/ricalcola-codice/", views.ricalcola_codice_anagrafica, name="anagrafica_ricalcola_codice"),
]