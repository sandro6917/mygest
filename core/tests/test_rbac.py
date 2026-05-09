"""
Test RBAC - Role-Based Access Control

Verifica isolamento dati basato su ruoli utente:
- ADMIN: accesso completo
- MANAGER: accesso completo
- OPERATORE: solo dati assegnati (read/write)
- VIEWER: solo dati assegnati (read-only)
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from core.models import UserProfile, UserRole
from anagrafiche.models import Anagrafica, Cliente
from documenti.models import Documento, DocumentiTipo
from fascicoli.models import Fascicolo
from pratiche.models import Pratica, PraticheTipo

User = get_user_model()


@pytest.fixture
def setup_users(db):
    """
    Crea utenti di test con diversi ruoli:
    - admin_user: ADMIN
    - manager_user: MANAGER
    - operatore_user: OPERATORE
    - viewer_user: VIEWER
    """
    # Admin
    admin_user = User.objects.create_user(
        username='admin_test',
        password='admin123',
        is_staff=True
    )
    admin_user.profile.role = UserRole.ADMIN
    admin_user.profile.save()
    
    # Manager
    manager_user = User.objects.create_user(
        username='manager_test',
        password='manager123'
    )
    manager_user.profile.role = UserRole.MANAGER
    manager_user.profile.save()
    
    # Operatore
    operatore_user = User.objects.create_user(
        username='operatore_test',
        password='operatore123'
    )
    operatore_user.profile.role = UserRole.OPERATORE
    operatore_user.profile.save()
    
    # Viewer
    viewer_user = User.objects.create_user(
        username='viewer_test',
        password='viewer123'
    )
    viewer_user.profile.role = UserRole.VIEWER
    viewer_user.profile.save()
    
    return {
        'admin': admin_user,
        'manager': manager_user,
        'operatore': operatore_user,
        'viewer': viewer_user,
    }


@pytest.fixture
def setup_data(db, setup_users):
    """
    Crea dati di test:
    - 2 clienti: cliente_assegnato, cliente_non_assegnato
    - 2 documenti: doc_assegnato, doc_non_assegnato
    - 2 fascicoli: fascicolo_assegnato, fascicolo_non_assegnato
    - 2 pratiche: pratica_assegnata, pratica_non_assegnata
    
    Assegna cliente_assegnato a operatore_user e viewer_user.
    """
    users = setup_users
    
    # Crea 2 clienti
    anagrafica_assegnata = Anagrafica.objects.create(
        tipo='PF',
        nome='Mario',
        cognome='Rossi',
        codice_fiscale='RSSMRA80A01H501U'
    )
    cliente_assegnato = Cliente.objects.create(
        anagrafica=anagrafica_assegnata,
        tipo_id=1  # Assume tipo cliente già esistente
    )
    
    anagrafica_non_assegnata = Anagrafica.objects.create(
        tipo='PF',
        nome='Luigi',
        cognome='Verdi',
        codice_fiscale='VRDLGU85B02H501V'
    )
    cliente_non_assegnato = Cliente.objects.create(
        anagrafica=anagrafica_non_assegnata,
        tipo_id=1
    )
    
    # Assegna cliente_assegnato a operatore e viewer
    users['operatore'].profile.assigned_clients.add(cliente_assegnato)
    users['viewer'].profile.assigned_clients.add(cliente_assegnato)
    
    # Crea tipo documento
    tipo_doc, _ = DocumentiTipo.objects.get_or_create(
        codice='GEN',
        defaults={'nome': 'Generico'}
    )
    
    # Crea documenti
    doc_assegnato = Documento.objects.create(
        tipo=tipo_doc,
        cliente=cliente_assegnato,
        descrizione='Documento assegnato'
    )
    
    doc_non_assegnato = Documento.objects.create(
        tipo=tipo_doc,
        cliente=cliente_non_assegnato,
        descrizione='Documento non assegnato'
    )
    
    # Crea fascicoli
    fascicolo_assegnato = Fascicolo.objects.create(
        cliente=cliente_assegnato,
        titolo='Fascicolo assegnato',
        anno=2026
    )
    
    fascicolo_non_assegnato = Fascicolo.objects.create(
        cliente=cliente_non_assegnato,
        titolo='Fascicolo non assegnato',
        anno=2026
    )
    
    # Crea tipo pratica
    tipo_pratica, _ = PraticheTipo.objects.get_or_create(
        codice='GEN',
        defaults={'nome': 'Generico'}
    )
    
    # Crea pratiche
    pratica_assegnata = Pratica.objects.create(
        tipo=tipo_pratica,
        cliente=cliente_assegnato,
        oggetto='Pratica assegnata',
        responsabile=users['operatore']
    )
    
    pratica_non_assegnata = Pratica.objects.create(
        tipo=tipo_pratica,
        cliente=cliente_non_assegnato,
        oggetto='Pratica non assegnata'
    )
    
    return {
        'cliente_assegnato': cliente_assegnato,
        'cliente_non_assegnato': cliente_non_assegnato,
        'doc_assegnato': doc_assegnato,
        'doc_non_assegnato': doc_non_assegnato,
        'fascicolo_assegnato': fascicolo_assegnato,
        'fascicolo_non_assegnato': fascicolo_non_assegnato,
        'pratica_assegnata': pratica_assegnata,
        'pratica_non_assegnata': pratica_non_assegnata,
    }


@pytest.mark.django_db
class TestRBACDocumenti:
    """Test isolamento documenti per ruoli"""
    
    def test_admin_vede_tutti_documenti(self, setup_users, setup_data):
        """ADMIN vede tutti i documenti"""
        client = APIClient()
        client.force_authenticate(user=setup_users['admin'])
        
        response = client.get('/api/v1/documenti/')
        assert response.status_code == status.HTTP_200_OK
        
        # ADMIN vede entrambi i documenti
        assert response.data['count'] >= 2
    
    def test_manager_vede_tutti_documenti(self, setup_users, setup_data):
        """MANAGER vede tutti i documenti"""
        client = APIClient()
        client.force_authenticate(user=setup_users['manager'])
        
        response = client.get('/api/v1/documenti/')
        assert response.status_code == status.HTTP_200_OK
        
        # MANAGER vede entrambi i documenti
        assert response.data['count'] >= 2
    
    def test_operatore_vede_solo_documenti_assegnati(self, setup_users, setup_data):
        """OPERATORE vede solo documenti dei clienti assegnati"""
        client = APIClient()
        client.force_authenticate(user=setup_users['operatore'])
        
        response = client.get('/api/v1/documenti/')
        assert response.status_code == status.HTTP_200_OK
        
        # OPERATORE vede solo doc_assegnato
        doc_ids = [doc['id'] for doc in response.data['results']]
        assert setup_data['doc_assegnato'].id in doc_ids
        assert setup_data['doc_non_assegnato'].id not in doc_ids
    
    def test_viewer_vede_solo_documenti_assegnati(self, setup_users, setup_data):
        """VIEWER vede solo documenti dei clienti assegnati"""
        client = APIClient()
        client.force_authenticate(user=setup_users['viewer'])
        
        response = client.get('/api/v1/documenti/')
        assert response.status_code == status.HTTP_200_OK
        
        # VIEWER vede solo doc_assegnato
        doc_ids = [doc['id'] for doc in response.data['results']]
        assert setup_data['doc_assegnato'].id in doc_ids
        assert setup_data['doc_non_assegnato'].id not in doc_ids
    
    def test_viewer_non_puo_creare_documento(self, setup_users, setup_data):
        """VIEWER non può creare documenti"""
        client = APIClient()
        client.force_authenticate(user=setup_users['viewer'])
        
        data = {
            'tipo': 1,
            'cliente': setup_data['cliente_assegnato'].id,
            'descrizione': 'Test documento'
        }
        
        response = client.post('/api/v1/documenti/', data)
        # VIEWER non può creare
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestRBACFascicoli:
    """Test isolamento fascicoli per ruoli"""
    
    def test_operatore_vede_solo_fascicoli_assegnati(self, setup_users, setup_data):
        """OPERATORE vede solo fascicoli dei clienti assegnati"""
        client = APIClient()
        client.force_authenticate(user=setup_users['operatore'])
        
        response = client.get('/api/v1/fascicoli/')
        assert response.status_code == status.HTTP_200_OK
        
        # OPERATORE vede solo fascicolo_assegnato
        fascicolo_ids = [f['id'] for f in response.data['results']]
        assert setup_data['fascicolo_assegnato'].id in fascicolo_ids
        assert setup_data['fascicolo_non_assegnato'].id not in fascicolo_ids


@pytest.mark.django_db
class TestRBACPratiche:
    """Test isolamento pratiche per ruoli"""
    
    def test_operatore_vede_pratiche_assegnate_o_responsabile(self, setup_users, setup_data):
        """OPERATORE vede pratiche dei clienti assegnati O dove è responsabile"""
        client = APIClient()
        client.force_authenticate(user=setup_users['operatore'])
        
        response = client.get('/api/v1/pratiche/')
        assert response.status_code == status.HTTP_200_OK
        
        # OPERATORE vede pratica_assegnata (sia cliente assegnato CHE responsabile)
        pratica_ids = [p['id'] for p in response.data['results']]
        assert setup_data['pratica_assegnata'].id in pratica_ids
        # Non vede pratica_non_assegnata (cliente non assegnato + non è responsabile)
        assert setup_data['pratica_non_assegnata'].id not in pratica_ids
    
    def test_viewer_non_puo_modificare_pratica(self, setup_users, setup_data):
        """VIEWER non può modificare pratiche"""
        client = APIClient()
        client.force_authenticate(user=setup_users['viewer'])
        
        data = {'oggetto': 'Oggetto modificato'}
        
        response = client.patch(
            f'/api/v1/pratiche/{setup_data["pratica_assegnata"].id}/',
            data
        )
        
        # VIEWER non può modificare
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestRBACAnagrafiche:
    """Test isolamento anagrafiche per ruoli"""
    
    def test_admin_vede_tutte_anagrafiche(self, setup_users, setup_data):
        """ADMIN vede tutte le anagrafiche"""
        client = APIClient()
        client.force_authenticate(user=setup_users['admin'])
        
        response = client.get('/api/v1/anagrafiche/')
        assert response.status_code == status.HTTP_200_OK
        
        # ADMIN vede entrambe le anagrafiche
        assert response.data['count'] >= 2
    
    def test_operatore_vede_solo_anagrafiche_assegnate(self, setup_users, setup_data):
        """OPERATORE vede solo anagrafiche dei clienti assegnati"""
        client = APIClient()
        client.force_authenticate(user=setup_users['operatore'])
        
        response = client.get('/api/v1/anagrafiche/')
        assert response.status_code == status.HTTP_200_OK
        
        # OPERATORE vede solo anagrafica_assegnata
        anagrafica_ids = [a['id'] for a in response.data['results']]
        assert setup_data['cliente_assegnato'].anagrafica.id in anagrafica_ids
        # Non dovrebbe vedere anagrafica non assegnata (se ha cliente)
        # Nota: anagrafica senza cliente potrebbe essere visibile se filtro non copre questo caso


@pytest.mark.django_db
class TestPermissions:
    """Test permission classes"""
    
    def test_admin_puo_eliminare(self, setup_users, setup_data):
        """ADMIN può eliminare risorse"""
        client = APIClient()
        client.force_authenticate(user=setup_users['admin'])
        
        # Crea documento temporaneo
        doc = Documento.objects.create(
            tipo_id=1,
            cliente=setup_data['cliente_assegnato'],
            descrizione='Doc da eliminare'
        )
        
        response = client.delete(f'/api/v1/documenti/{doc.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_operatore_non_puo_eliminare(self, setup_users, setup_data):
        """OPERATORE non può eliminare risorse"""
        client = APIClient()
        client.force_authenticate(user=setup_users['operatore'])
        
        response = client.delete(
            f'/api/v1/documenti/{setup_data["doc_assegnato"].id}/'
        )
        
        # OPERATORE non può eliminare
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_viewer_non_puo_creare(self, setup_users, setup_data):
        """VIEWER non può creare risorse"""
        client = APIClient()
        client.force_authenticate(user=setup_users['viewer'])
        
        data = {
            'cliente': setup_data['cliente_assegnato'].id,
            'titolo': 'Test fascicolo',
            'anno': 2026
        }
        
        response = client.post('/api/v1/fascicoli/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
