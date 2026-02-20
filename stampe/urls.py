from __future__ import annotations
from django.urls import path
from .views import etichetta_view, lista_view, stampa_custom_view

app_name = "stampe"
urlpatterns = [
    path("<str:app_label>/<str:model>/<int:pk>/", etichetta_view, name="etichetta"),
    path("lista/<str:app_label>/<str:model>/", lista_view, name="lista"),
    path("stampa/<str:slug>/", stampa_custom_view, name="stampa-custom"),
]