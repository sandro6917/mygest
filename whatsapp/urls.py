from django.urls import path

from .views import WhatsAppWebhookView

app_name = "whatsapp"

urlpatterns = [
    path("webhook/", WhatsAppWebhookView.as_view(), name="webhook"),
]
