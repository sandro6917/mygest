"""
Core Admin - User Profile Management
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, UserRole

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    """Inline per gestire UserProfile direttamente da User Admin"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Profilo e Permessi'
    verbose_name_plural = 'Profilo e Permessi'
    filter_horizontal = ('assigned_clients',)
    fieldsets = (
        ('Ruolo', {
            'fields': ('role',),
            'description': (
                '<strong>ADMIN</strong>: Accesso completo sistema<br>'
                '<strong>MANAGER</strong>: Gestione completa dati (tutti i clienti)<br>'
                '<strong>OPERATORE</strong>: Creazione/modifica dati assegnati<br>'
                '<strong>VIEWER</strong>: Solo lettura dati assegnati'
            )
        }),
        ('Isolamento Dati', {
            'fields': ('assigned_clients',),
            'description': (
                'Clienti visibili per OPERATORE e VIEWER.<br>'
                'Lasciare vuoto per ADMIN/MANAGER (vedono tutti i clienti).'
            )
        }),
    )


# Unregister default User admin
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """User Admin con UserProfile inline"""
    inlines = (UserProfileInline,)
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'profile__role')
    
    def get_role(self, obj):
        """Mostra ruolo utente"""
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return '-'
    get_role.short_description = 'Ruolo'
    get_role.admin_order_field = 'profile__role'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin standalone per UserProfile"""
    list_display = ('user', 'role', 'get_assigned_clients_count', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    filter_horizontal = ('assigned_clients',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Utente', {
            'fields': ('user',)
        }),
        ('Ruolo RBAC', {
            'fields': ('role',),
            'description': (
                '<ul>'
                '<li><strong>ADMIN</strong>: Accesso completo, gestione utenti, configurazione sistema</li>'
                '<li><strong>MANAGER</strong>: Gestione pratiche, documenti, anagrafiche (tutti i dati)</li>'
                '<li><strong>OPERATORE</strong>: Creazione/modifica documenti/pratiche assegnati</li>'
                '<li><strong>VIEWER</strong>: Solo lettura dati assegnati</li>'
                '</ul>'
            )
        }),
        ('Isolamento Dati', {
            'fields': ('assigned_clients',),
            'description': (
                'Seleziona i clienti visibili per OPERATORE/VIEWER.<br>'
                '<strong>Lasciare vuoto per ADMIN/MANAGER</strong> (vedono tutti i clienti).'
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_assigned_clients_count(self, obj):
        """Conta clienti assegnati"""
        count = obj.assigned_clients.count()
        if count == 0 and obj.can_view_all:
            return 'Tutti (no limite)'
        return f'{count} clienti'
    get_assigned_clients_count.short_description = 'Clienti Assegnati'
