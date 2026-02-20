from django.urls import path

from . import views

app_name = "scadenze"

urlpatterns = [
    path("", views.home, name="home"),
    path("scadenziario/", views.scadenziario, name="scadenziario"),
    path("scadenziario/export/pdf/", views.export_scadenziario_pdf, name="export_scadenziario_pdf"),
    path("scadenziario/export/excel/", views.export_scadenziario_excel, name="export_scadenziario_excel"),
    path("calendario/", views.calendario_visual, name="calendario_visual"),
    path("calendario/events.json", views.calendario_events_json, name="calendario_events_json"),
    path("statistiche/", views.statistiche, name="statistiche"),
    path("nuova/", views.create, name="create"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/modifica/", views.update, name="update"),
    path("<int:pk>/bulk/", views.bulk_generate, name="bulk_generate"),
    path("occorrenze/<int:occorrenza_pk>/trigger-alert/", views.trigger_alert, name="trigger_alert"),
]
