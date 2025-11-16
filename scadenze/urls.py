from django.urls import path

from . import views

app_name = "scadenze"

urlpatterns = [
    path("", views.home, name="home"),
    path("nuova/", views.create, name="create"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/modifica/", views.update, name="update"),
    path("<int:pk>/bulk/", views.bulk_generate, name="bulk_generate"),
    path("occorrenze/<int:occorrenza_pk>/trigger-alert/", views.trigger_alert, name="trigger_alert"),
]
