from django.urls import path
from .views import protocolla_documento, protocolla_fascicolo

app_name = "protocollo"

urlpatterns = [
    path("documenti/<int:pk>/protocolla/", protocolla_documento, name="protocolla_documento"),
    path("fascicoli/<int:pk>/protocolla/", protocolla_fascicolo, name="protocolla_fascicolo"),
]