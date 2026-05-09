# MyGest - RBAC System Documentation

## 📋 Panoramica

MyGest implementa un sistema di **Role-Based Access Control (RBAC)** per gestire permessi utente e isolamento dati.

## 🎯 Architettura

### Modello Dati

```python
# core/models.py

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'Amministratore'
    MANAGER = 'MANAGER', 'Manager'
    OPERATORE = 'OPERATORE', 'Operatore'
    VIEWER = 'VIEWER', 'Visualizzatore'

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')
    role = models.CharField(max_length=20, choices=UserRole.choices)
    assigned_clients = models.ManyToManyField('anagrafiche.Cliente')
```

### Gerarchia Ruoli

```
ADMIN (Amministratore)
  ├─ Accesso completo sistema
  ├─ Gestione utenti e ruoli
  ├─ Tutti i dati (CRUD)
  └─ Eliminazione risorse
  
MANAGER
  ├─ Accesso a tutti i dati
  ├─ Creazione/modifica risorse
  ├─ Eliminazione risorse
  └─ NO gestione utenti
  
OPERATORE
  ├─ Accesso solo dati assegnati
  ├─ Creazione risorse
  ├─ Modifica risorse
  └─ NO eliminazione
  
VIEWER (Visualizzatore)
  ├─ Accesso solo dati assegnati
  ├─ Solo lettura
  └─ NO creazione/modifica/eliminazione
```

## 🔐 Matrice Permessi

| Azione | ADMIN | MANAGER | OPERATORE | VIEWER |
|--------|-------|---------|-----------|--------|
| **Visualizzazione** |
| Tutti i dati | ✅ | ✅ | ❌ | ❌ |
| Dati assegnati | ✅ | ✅ | ✅ | ✅ |
| **Creazione** |
| Crea documenti | ✅ | ✅ | ✅ | ❌ |
| Crea fascicoli | ✅ | ✅ | ✅ | ❌ |
| Crea pratiche | ✅ | ✅ | ✅ | ❌ |
| **Modifica** |
| Modifica qualsiasi | ✅ | ✅ | Solo assegnati | ❌ |
| **Eliminazione** |
| Elimina qualsiasi | ✅ | ✅ | ❌ | ❌ |
| **Gestione Utenti** |
| Crea/modifica utenti | ✅ | ❌ | ❌ | ❌ |
| Assegna ruoli | ✅ | ❌ | ❌ | ❌ |

## 📊 Isolamento Dati

### Logica Filtro

#### ADMIN & MANAGER
```python
# Accesso COMPLETO - nessun filtro
queryset = Model.objects.all()
```

#### OPERATORE & VIEWER
```python
# Solo dati dei clienti assegnati
accessible_clients_ids = user.profile.get_accessible_clients_ids()
queryset = Model.objects.filter(cliente_id__in=accessible_clients_ids)
```

### Caso Speciale: Pratiche

Gli OPERATORI vedono anche pratiche dove sono **responsabile**:

```python
queryset = Pratica.objects.filter(
    Q(cliente_id__in=accessible_clients_ids) |
    Q(responsabile=user)
)
```

## 🛠️ Implementazione Tecnica

### Permission Classes

```python
# core/permissions.py

from rest_framework import permissions

class RBACPermission(permissions.BasePermission):
    """
    Permesso principale RBAC.
    
    - GET/HEAD/OPTIONS: tutti gli autenticati
    - POST: ADMIN, MANAGER, OPERATORE
    - PUT/PATCH: ADMIN, MANAGER, OPERATORE (solo propri dati)
    - DELETE: ADMIN, MANAGER
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if not hasattr(request.user, 'profile'):
            return False
        
        profile = request.user.profile
        
        # Lettura: tutti
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Creazione/Modifica
        if request.method in ['POST', 'PUT', 'PATCH']:
            return profile.can_create and profile.can_edit
        
        # Eliminazione: solo ADMIN/MANAGER
        if request.method == 'DELETE':
            return profile.can_delete
        
        return True
    
    def has_object_permission(self, request, view, obj):
        profile = request.user.profile
        
        # ADMIN/MANAGER: accesso completo
        if profile.can_view_all:
            return True
        
        # Lettura: se dato è visibile nel queryset
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Modifica: solo se cliente assegnato
        if request.method in ['PUT', 'PATCH']:
            if not profile.can_edit:
                return False
            
            accessible_ids = profile.get_accessible_clients_ids()
            if accessible_ids is None:
                return True
            
            return getattr(obj, 'cliente_id', None) in accessible_ids
        
        # Eliminazione: solo ADMIN/MANAGER
        if request.method == 'DELETE':
            return profile.can_delete
        
        return False
```

### ViewSet Integration

```python
# api/v1/documenti/views.py

from core.permissions import RBACPermission
from rest_framework import viewsets

class DocumentoViewSet(viewsets.ModelViewSet):
    permission_classes = [RBACPermission]
    
    def get_queryset(self):
        qs = super().get_queryset()
        
        if not hasattr(self.request.user, 'profile'):
            return qs.none()
        
        profile = self.request.user.profile
        
        # ADMIN/MANAGER: tutti i documenti
        if profile.can_view_all:
            return qs
        
        # OPERATORE/VIEWER: solo documenti assegnati
        accessible_clients_ids = profile.get_accessible_clients_ids()
        if accessible_clients_ids is not None:
            qs = qs.filter(cliente_id__in=accessible_clients_ids)
        
        return qs
```

## 👤 Gestione Utenti

### Creazione Automatica Profile

Ogni nuovo utente riceve automaticamente un `UserProfile` con ruolo **VIEWER** (principio least privilege):

```python
# core/models.py

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(
            user=instance,
            role=UserRole.VIEWER  # Default: minimo privilegio
        )
```

### Assegnazione Ruolo (Django Admin)

1. Accedi a `/admin/`
2. Vai a **Authentication and Authorization > Users**
3. Seleziona utente
4. Modifica **Profilo utente**:
   - **Ruolo**: Scegli da dropdown (ADMIN/MANAGER/OPERATORE/VIEWER)
   - **Clienti assegnati**: Seleziona clienti (solo per OPERATORE/VIEWER)

### Assegnazione Clienti

Per OPERATORE e VIEWER:

1. Apri utente in Django admin
2. Sezione **Profilo utente**
3. Campo **Clienti assegnati**:
   - Usa filtro orizzontale per selezionare clienti
   - Puoi assegnare multipli clienti

**Nota**: ADMIN e MANAGER non necessitano client assegnati (vedono tutto).

## 🧪 Testing

### Unit Test

```bash
# Run all RBAC tests
pytest core/tests/test_rbac.py -v

# Run specific test class
pytest core/tests/test_rbac.py::TestRBACDocumenti -v

# Run with coverage
pytest core/tests/test_rbac.py --cov=core --cov=api
```

### Test Scenari

#### Scenario 1: VIEWER non vede documenti non assegnati
```python
@pytest.mark.django_db
def test_viewer_vede_solo_documenti_assegnati(setup_users, setup_data):
    client = APIClient()
    client.force_authenticate(user=setup_users['viewer'])
    
    response = client.get('/api/v1/documenti/')
    
    doc_ids = [doc['id'] for doc in response.data['results']]
    assert setup_data['doc_assegnato'].id in doc_ids
    assert setup_data['doc_non_assegnato'].id not in doc_ids  # ✓ Isolamento
```

#### Scenario 2: VIEWER non può creare
```python
@pytest.mark.django_db
def test_viewer_non_puo_creare_documento(setup_users, setup_data):
    client = APIClient()
    client.force_authenticate(user=setup_users['viewer'])
    
    data = {'tipo': 1, 'cliente': 1, 'descrizione': 'Test'}
    response = client.post('/api/v1/documenti/', data)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN  # ✓ Protetto
```

#### Scenario 3: OPERATORE non può eliminare
```python
@pytest.mark.django_db
def test_operatore_non_puo_eliminare(setup_users, setup_data):
    client = APIClient()
    client.force_authenticate(user=setup_users['operatore'])
    
    response = client.delete(f'/api/v1/documenti/{doc_id}/')
    
    assert response.status_code == status.HTTP_403_FORBIDDEN  # ✓ Solo ADMIN/MANAGER
```

## 🔧 Setup Iniziale

### 1. Migrazione Database

```bash
# Crea migration
python manage.py makemigrations core

# Applica migration
python manage.py migrate core
```

### 2. Crea Primo Admin

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
from core.models import UserRole

User = get_user_model()

# Crea superuser (se non esiste)
admin = User.objects.create_superuser(
    username='admin',
    email='admin@mygest.local',
    password='admin_password'
)

# Imposta ruolo ADMIN
admin.profile.role = UserRole.ADMIN
admin.profile.save()

print(f"✓ Admin creato: {admin.username} (Ruolo: {admin.profile.role})")
```

### 3. Crea Utenti Test

```python
from django.contrib.auth import get_user_model
from core.models import UserRole
from anagrafiche.models import Cliente

User = get_user_model()

# Manager
manager = User.objects.create_user('manager', password='manager123')
manager.profile.role = UserRole.MANAGER
manager.profile.save()

# Operatore
operatore = User.objects.create_user('operatore', password='operatore123')
operatore.profile.role = UserRole.OPERATORE
# Assegna clienti
cliente = Cliente.objects.first()
operatore.profile.assigned_clients.add(cliente)

# Viewer
viewer = User.objects.create_user('viewer', password='viewer123')
viewer.profile.role = UserRole.VIEWER
viewer.profile.assigned_clients.add(cliente)

print("✓ Utenti test creati")
```

## 🚨 Security Best Practices

### 1. Principio Least Privilege
- Nuovo utente = VIEWER (default)
- Promozione esplicita ruoli superiori
- Revisione periodica accessi

### 2. Audit Trail
```python
# Traccia chi crea/modifica (già implementato)
documento.utente_creazione = request.user
documento.utente_modifica = request.user
```

### 3. Validazione Doppia
- **Backend**: Permission classes + queryset filtering
- **Frontend**: UI nasconde azioni non permesse (extra sicurezza)

### 4. API Endpoint Protetti
```python
# ❌ MAI fare questo
queryset = Documento.objects.all()  # Espone tutti i dati!

# ✅ SEMPRE filtra per ruolo
if profile.can_view_all:
    return qs
else:
    return qs.filter(cliente_id__in=accessible_ids)
```

## 📱 Frontend Integration

### React - Verifica Permessi

```typescript
// src/hooks/usePermissions.ts
import { useAuthStore } from '@/store/authStore';

export const usePermissions = () => {
  const user = useAuthStore((state) => state.user);
  
  const canCreate = ['ADMIN', 'MANAGER', 'OPERATORE'].includes(user?.profile?.role);
  const canEdit = ['ADMIN', 'MANAGER', 'OPERATORE'].includes(user?.profile?.role);
  const canDelete = ['ADMIN', 'MANAGER'].includes(user?.profile?.role);
  const isAdmin = user?.profile?.role === 'ADMIN';
  
  return { canCreate, canEdit, canDelete, isAdmin };
};
```

### Conditional Rendering

```typescript
// Example: Document Actions
import { usePermissions } from '@/hooks/usePermissions';

const DocumentActions = ({ documento }) => {
  const { canEdit, canDelete } = usePermissions();
  
  return (
    <Stack direction="row" spacing={2}>
      {canEdit && (
        <Button onClick={handleEdit}>Modifica</Button>
      )}
      {canDelete && (
        <Button onClick={handleDelete} color="error">Elimina</Button>
      )}
    </Stack>
  );
};
```

## 🐛 Troubleshooting

### Problema: Utente non vede dati

**Causa**: Nessun cliente assegnato a OPERATORE/VIEWER

**Soluzione**:
```bash
python manage.py shell
```
```python
from django.contrib.auth import get_user_model
from anagrafiche.models import Cliente

user = User.objects.get(username='nome_utente')
clienti = Cliente.objects.filter(id__in=[1, 2, 3])  # IDs clienti
user.profile.assigned_clients.set(clienti)

print(f"✓ Assegnati {user.profile.assigned_clients.count()} clienti a {user.username}")
```

### Problema: 403 Forbidden su API

**Causa 1**: Ruolo insufficiente per azione (es. VIEWER tenta POST)

**Soluzione**: Verifica ruolo utente:
```python
user = User.objects.get(username='nome_utente')
print(f"Ruolo: {user.profile.role}")
print(f"Può creare: {user.profile.can_create}")
print(f"Può modificare: {user.profile.can_edit}")
print(f"Può eliminare: {user.profile.can_delete}")
```

**Causa 2**: OPERATORE accede a dati non assegnati

**Soluzione**: Verifica clienti assegnati:
```python
user = User.objects.get(username='operatore_user')
print(f"Clienti assegnati: {list(user.profile.assigned_clients.values_list('id', flat=True))}")
```

### Problema: ADMIN non ha accesso completo

**Causa**: UserProfile non esistente o ruolo errato

**Soluzione**:
```python
from django.contrib.auth import get_user_model
from core.models import UserRole

user = User.objects.get(username='admin_user')

# Verifica profile
if not hasattr(user, 'profile'):
    from core.models import UserProfile
    UserProfile.objects.create(user=user, role=UserRole.ADMIN)
    print("✓ Profile creato")
else:
    user.profile.role = UserRole.ADMIN
    user.profile.save()
    print("✓ Ruolo aggiornato")
```

## 📚 API Behavior Examples

### GET /api/v1/documenti/

**ADMIN**:
```json
{
  "count": 1500,
  "results": [
    { "id": 1, "cliente": 10, "descrizione": "Doc Cliente 10" },
    { "id": 2, "cliente": 20, "descrizione": "Doc Cliente 20" },
    { "id": 3, "cliente": 30, "descrizione": "Doc Cliente 30" }
  ]
}
```

**OPERATORE** (assegnato cliente 10):
```json
{
  "count": 45,
  "results": [
    { "id": 1, "cliente": 10, "descrizione": "Doc Cliente 10" }
  ]
}
```

### POST /api/v1/documenti/

**OPERATORE** (assegnato cliente 10):
```bash
# ✅ Success - cliente assegnato
curl -X POST /api/v1/documenti/ \
  -H "Authorization: Bearer <token>" \
  -d '{"tipo": 1, "cliente": 10, "descrizione": "Nuovo doc"}'

# ❌ 403 Forbidden - cliente non assegnato
curl -X POST /api/v1/documenti/ \
  -H "Authorization: Bearer <token>" \
  -d '{"tipo": 1, "cliente": 20, "descrizione": "Nuovo doc"}'
```

**VIEWER**:
```bash
# ❌ 403 Forbidden - viewer non può creare
curl -X POST /api/v1/documenti/ \
  -H "Authorization: Bearer <token>" \
  -d '{"tipo": 1, "cliente": 10, "descrizione": "Nuovo doc"}'
```

### DELETE /api/v1/documenti/123/

**ADMIN/MANAGER**:
```bash
# ✅ 204 No Content
curl -X DELETE /api/v1/documenti/123/ \
  -H "Authorization: Bearer <token>"
```

**OPERATORE**:
```bash
# ❌ 403 Forbidden
curl -X DELETE /api/v1/documenti/123/ \
  -H "Authorization: Bearer <token>"
```

## 📖 Riferimenti

- **Modello**: `core/models.py` (UserProfile, UserRole)
- **Permissions**: `core/permissions.py` (RBACPermission)
- **Admin**: `core/admin.py` (UserProfileAdmin)
- **Tests**: `core/tests/test_rbac.py`
- **ViewSets**: `api/v1/*/views.py` (Documenti, Fascicoli, Pratiche, Anagrafiche)

---

**Versione**: 1.0  
**Data**: Gennaio 2026  
**Autore**: Sandro Chimenti
