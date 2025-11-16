from django.urls import path
from . import views

app_name = "fascicoli"

urlpatterns = [
    path("", views.home, name="home"),
    path("nuovo/", views.fascicolo_nuovo, name="nuovo"),
    path("<int:pk>/modifica/", views.fascicolo_modifica, name="modifica"),
    path("<int:pk>/protocolla/", views.fascicolo_protocolla, name="protocolla"),  # NEW
]