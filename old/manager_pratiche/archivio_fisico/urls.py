from django.urls import path
from . import views

app_name = "archivio_fisico"
urlpatterns = [
    path("", views.unita_list, name="unita_list"),
    path("<int:pk>/", views.unita_detail, name="unita_detail"),
]