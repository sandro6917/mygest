from django.urls import path
from . import views

app_name = "archivio_fisico"
urlpatterns = [
    path("", views.unita_list, name="unita_list"),
    path("inventario/tree/", views.unita_inventory_tree, name="unita_inventory_tree"),
    path("<int:pk>/", views.unita_detail, name="unita_detail"),
    path("<int:pk>/etichette/", views.unita_etichette, name="unita_etichette"),

    # Operazioni archivio fisico
    path("operazioni/", views.operazionearchivio_list, name="operazionearchivio_list"),
    path("operazioni/nuova/", views.operazionearchivio_create, name="operazionearchivio_create"),
    path(
        "operazioni/ajax/riga-options/",
        views.operazionearchivio_riga_options,
        name="operazionearchivio_riga_options",
    ),
    path(
        "operazioni/<int:pk>/verbale/",
        views.operazionearchivio_verbale_docx,
        name="operazionearchivio_verbale_docx",
    ),
    path(
        "operazioni/<int:pk>/verbale/<slug:template_slug>/",
        views.operazionearchivio_verbale_docx,
        name="operazionearchivio_verbale_docx_slug",
    ),
    path("operazioni/<int:pk>/", views.operazionearchivio_detail, name="operazionearchivio_detail"),
    path("operazioni/<int:pk>/modifica/", views.operazionearchivio_update, name="operazionearchivio_update"),
    path("operazioni/<int:pk>/elimina/", views.operazionearchivio_delete, name="operazionearchivio_delete"),
]