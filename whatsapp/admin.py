from __future__ import annotations

from django.contrib import admin

from .models import WhatsAppBusinessAccount, WhatsAppContact, WhatsAppConversation, WhatsAppMessage


@admin.register(WhatsAppBusinessAccount)
class WhatsAppBusinessAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "phone_number_id",
        "business_account_id",
        "is_default",
        "active",
        "api_version",
    )
    list_filter = ("active", "is_default")
    search_fields = ("name", "phone_number_id", "business_account_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = ("label", "wa_id", "anagrafica", "blocked", "updated_at")
    list_filter = ("blocked",)
    search_fields = ("wa_id", "display_name", "verified_name", "phone_number")
    raw_id_fields = ("anagrafica",)
    readonly_fields = ("created_at", "updated_at", "last_seen_at")


@admin.register(WhatsAppConversation)
class WhatsAppConversationAdmin(admin.ModelAdmin):
    list_display = (
        "contact",
        "account",
        "conversation_id",
        "status",
        "last_message_at",
        "opened_at",
        "closed_at",
    )
    list_filter = ("status", "account")
    search_fields = ("conversation_id", "contact__display_name", "contact__wa_id")
    raw_id_fields = ("contact", "account")
    readonly_fields = ("opened_at", "closed_at", "last_message_at", "created_at", "updated_at")


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = (
        "message_id",
        "direction",
        "message_type",
        "status",
        "contact",
        "account",
        "created_at",
    )
    list_filter = ("direction", "message_type", "status", "account")
    search_fields = ("message_id", "body", "contact__display_name", "contact__wa_id")
    raw_id_fields = ("conversation", "contact", "account")
    readonly_fields = (
        "created_at",
        "updated_at",
        "sent_at",
        "delivered_at",
        "read_at",
        "received_at",
    )
