"""
RBAC Permissions for DRF ViewSets
"""
from rest_framework import permissions


class IsAdminOrManager(permissions.BasePermission):
    """
    Permission: Solo ADMIN o MANAGER possono accedere.
    """
    message = 'Solo ADMIN o MANAGER possono eseguire questa operazione.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'profile'):
            return False
        
        return request.user.profile.can_view_all


class CanCreate(permissions.BasePermission):
    """
    Permission: ADMIN, MANAGER, OPERATORE possono creare.
    VIEWER: NO.
    """
    message = 'I VIEWER non possono creare nuove risorse.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'profile'):
            return False
        
        # Safe methods (GET, HEAD, OPTIONS) sempre consentiti
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Create, Update, Patch: solo se can_create
        if request.method in ['POST', 'PUT', 'PATCH']:
            return request.user.profile.can_create
        
        # Delete: solo se can_delete
        if request.method == 'DELETE':
            return request.user.profile.can_delete
        
        return True


class CanEdit(permissions.BasePermission):
    """
    Permission: ADMIN, MANAGER, OPERATORE possono modificare.
    VIEWER: NO.
    """
    message = 'I VIEWER non possono modificare risorse.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'profile'):
            return False
        
        # Safe methods sempre consentiti
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Update/Patch: solo se can_edit
        return request.user.profile.can_edit


class CanDelete(permissions.BasePermission):
    """
    Permission: Solo ADMIN e MANAGER possono eliminare.
    OPERATORE/VIEWER: NO.
    """
    message = 'Solo ADMIN e MANAGER possono eliminare risorse.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'profile'):
            return False
        
        # Solo DELETE controllato
        if request.method == 'DELETE':
            return request.user.profile.can_delete
        
        return True


class RBACPermission(permissions.BasePermission):
    """
    Permission completa RBAC che combina tutte le regole:
    
    - GET/HEAD/OPTIONS: Tutti (autenticati)
    - POST: ADMIN, MANAGER, OPERATORE
    - PUT/PATCH: ADMIN, MANAGER, OPERATORE
    - DELETE: ADMIN, MANAGER
    
    Isolamento dati implementato in get_queryset() dei ViewSet.
    """
    message = 'Non hai i permessi per questa operazione.'
    
    def has_permission(self, request, view):
        # Deve essere autenticato
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Deve avere profile
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # Safe methods: tutti
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # POST/PUT/PATCH: solo chi può creare/modificare
        if request.method in ['POST', 'PUT', 'PATCH']:
            return profile.can_create and profile.can_edit
        
        # DELETE: solo ADMIN/MANAGER
        if request.method == 'DELETE':
            return profile.can_delete
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Permission a livello oggetto.
        
        ADMIN/MANAGER: sempre OK
        OPERATORE/VIEWER: solo se oggetto è assegnato (controllo in get_queryset)
        """
        if not request.user or not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # ADMIN/MANAGER: accesso completo
        if profile.can_view_all:
            return True
        
        # Safe methods: OK se oggetto è nel queryset (già filtrato)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # OPERATORE: può modificare solo se ha permessi create/edit
        if request.method in ['POST', 'PUT', 'PATCH']:
            return profile.can_edit
        
        # VIEWER: no modifica/delete
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return False
        
        return True
