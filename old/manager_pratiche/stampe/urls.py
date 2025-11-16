from __future__ import annotations
from django.urls import path
from .views import etichetta_view, lista_view

app_name = "stampe"
urlpatterns = [
    path("<str:app_label>/<str:model>/<int:pk>/", etichetta_view, name="etichetta"),
    path("lista/<str:app_label>/<str:model>/", lista_view, name="lista"),
]