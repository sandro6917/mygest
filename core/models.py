"""
Core Models - User Profile with RBAC
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class UserRole(models.TextChoices):
    """Ruoli utente RBAC"""
    ADMIN = 'ADMIN', 'Amministratore'
    MANAGER = 'MANAGER', 'Manager'
    OPERATORE = 'OPERATORE', 'Operatore'
    VIEWER = 'VIEWER', 'Visualizzatore'


class UserProfile(models.Model):
    """
    Profilo utente con RBAC (Role-Based Access Control).
    
    Ruoli:
    - ADMIN: Accesso completo, gestione utenti, configurazione sistema
    - MANAGER: Gestione pratiche, documenti, anagrafiche (tutti i dati)
    - OPERATORE: Creazione/modifica documenti/pratiche assegnati
    - VIEWER: Solo lettura dati assegnati
    
    Isolamento dati:
    - ADMIN/MANAGER: vedono tutti i dati
    - OPERATORE: vedono solo dati dove sono assegnati (responsabile/owner)
    - VIEWER: solo lettura dati assegnati
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Utente'
    )
    
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.VIEWER,
        verbose_name='Ruolo',
        db_index=True
    )
    
    # Clienti assegnati (per OPERATORE/VIEWER)
    # Se vuoto, può vedere tutti i clienti (ADMIN/MANAGER)
    assigned_clients = models.ManyToManyField(
        'anagrafiche.Cliente',
        blank=True,
        related_name='assigned_users',
        verbose_name='Clienti Assegnati',
        help_text='Clienti visibili per OPERATORE/VIEWER. Vuoto = tutti i clienti (ADMIN/MANAGER)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Creato il')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Aggiornato il')
    
    class Meta:
        verbose_name = 'Profilo Utente'
        verbose_name_plural = 'Profili Utente'
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        """Utente è ADMIN"""
        return self.role == UserRole.ADMIN
    
    @property
    def is_manager(self):
        """Utente è MANAGER"""
        return self.role == UserRole.MANAGER
    
    @property
    def is_operatore(self):
        """Utente è OPERATORE"""
        return self.role == UserRole.OPERATORE
    
    @property
    def is_viewer(self):
        """Utente è VIEWER"""
        return self.role == UserRole.VIEWER
    
    @property
    def can_create(self):
        """Può creare nuove risorse"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATORE]
    
    @property
    def can_edit(self):
        """Può modificare risorse"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER, UserRole.OPERATORE]
    
    @property
    def can_delete(self):
        """Può eliminare risorse"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    @property
    def can_view_all(self):
        """Può vedere tutti i dati (no isolamento)"""
        return self.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    def get_accessible_clients_ids(self):
        """
        Ritorna IDs dei clienti accessibili dall'utente.
        
        - ADMIN/MANAGER: None (tutti i clienti)
        - OPERATORE/VIEWER: lista IDs clienti assegnati
        """
        if self.can_view_all:
            return None  # Tutti i clienti
        
        return list(self.assigned_clients.values_list('id', flat=True))


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crea automaticamente UserProfile quando viene creato un User"""
    if created:
        # Default role = VIEWER (principio least privilege)
        UserProfile.objects.create(user=instance, role=UserRole.VIEWER)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva UserProfile quando viene salvato User"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
