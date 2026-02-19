"""
Test per i filtri API delle scadenze occorrenze.
"""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from scadenze.models import Scadenza, ScadenzaOccorrenza

User = get_user_model()


@pytest.fixture
def api_client():
    """Client API autenticato."""
    return APIClient()


@pytest.fixture
def user(db):
    """Utente di test."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@example.com'
    )


@pytest.fixture
def scadenza_base(db, user):
    """Scadenza di test."""
    return Scadenza.objects.create(
        titolo="Test Scadenza",
        descrizione="Scadenza per test filtri",
        stato=Scadenza.Stato.ATTIVA,
        priorita=Scadenza.Priorita.ALTA,
        creato_da=user
    )


@pytest.fixture
def occorrenze_test(db, scadenza_base):
    """Crea occorrenze di test con vari stati e date."""
    now = timezone.now()
    occorrenze = []
    
    # Occorrenza pending - oggi
    occorrenze.append(ScadenzaOccorrenza.objects.create(
        scadenza=scadenza_base,
        inizio=now,
        fine=now + timedelta(hours=1),
        stato='pending'
    ))
    
    # Occorrenza pending - tra 3 giorni
    occorrenze.append(ScadenzaOccorrenza.objects.create(
        scadenza=scadenza_base,
        inizio=now + timedelta(days=3),
        fine=now + timedelta(days=3, hours=1),
        stato='pending'
    ))
    
    # Occorrenza scheduled - tra 7 giorni
    occorrenze.append(ScadenzaOccorrenza.objects.create(
        scadenza=scadenza_base,
        inizio=now + timedelta(days=7),
        fine=now + timedelta(days=7, hours=1),
        stato='scheduled'
    ))
    
    # Occorrenza completed - ieri
    occorrenze.append(ScadenzaOccorrenza.objects.create(
        scadenza=scadenza_base,
        inizio=now - timedelta(days=1),
        fine=now - timedelta(days=1, hours=-1),
        stato='completed'
    ))
    
    # Occorrenza cancelled - 2 giorni fa
    occorrenze.append(ScadenzaOccorrenza.objects.create(
        scadenza=scadenza_base,
        inizio=now - timedelta(days=2),
        fine=now - timedelta(days=2, hours=-1),
        stato='cancelled'
    ))
    
    return occorrenze


@pytest.mark.django_db
class TestScadenzaOccorrenzaFilters:
    """Test per i filtri delle occorrenze scadenze."""
    
    def test_filter_stato_single(self, api_client, user, occorrenze_test):
        """Test filtro per singolo stato."""
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/v1/scadenze/occorrenze/', {'stato': 'pending'})
        assert response.status_code == 200
        assert response.data['count'] == 2  # 2 occorrenze pending
    
    def test_filter_stato_in_multiple(self, api_client, user, occorrenze_test):
        """Test filtro per multipli stati (stato__in)."""
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'stato__in': 'pending,scheduled'
        })
        assert response.status_code == 200
        assert response.data['count'] == 3  # 2 pending + 1 scheduled
    
    def test_filter_inizio_gte(self, api_client, user, occorrenze_test):
        """Test filtro data inizio >= (inizio__gte)."""
        api_client.force_authenticate(user=user)
        
        # Filtra occorrenze da oggi in poi
        oggi = timezone.now().date().isoformat()
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'inizio__gte': oggi
        })
        assert response.status_code == 200
        # Dovrebbe restituire: oggi + tra 3 giorni + tra 7 giorni = 3
        assert response.data['count'] == 3
    
    def test_filter_inizio_lt(self, api_client, user, occorrenze_test):
        """Test filtro data inizio < (inizio__lt)."""
        api_client.force_authenticate(user=user)
        
        # Filtra occorrenze prima di oggi
        oggi = timezone.now().date().isoformat()
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'inizio__lt': oggi
        })
        assert response.status_code == 200
        # Dovrebbe restituire: ieri + 2 giorni fa = 2
        assert response.data['count'] == 2
    
    def test_filter_date_range(self, api_client, user, occorrenze_test):
        """Test filtro range di date (inizio__gte + inizio__lt)."""
        api_client.force_authenticate(user=user)
        
        # Range: da oggi a 5 giorni
        oggi = timezone.now().date()
        tra_5_giorni = (oggi + timedelta(days=5)).isoformat()
        
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'inizio__gte': oggi.isoformat(),
            'inizio__lt': tra_5_giorni
        })
        assert response.status_code == 200
        # Dovrebbe restituire: oggi + tra 3 giorni = 2
        assert response.data['count'] == 2
    
    def test_filter_combined_date_and_stato(self, api_client, user, occorrenze_test):
        """Test filtro combinato: data + stato (caso reale dalla richiesta API)."""
        api_client.force_authenticate(user=user)
        
        # Range: prossimi 30 giorni con stato pending o scheduled
        oggi = timezone.now().date()
        tra_30_giorni = (oggi + timedelta(days=30)).isoformat()
        
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'inizio__gte': oggi.isoformat(),
            'inizio__lt': tra_30_giorni,
            'stato__in': 'pending,scheduled'
        })
        assert response.status_code == 200
        # Dovrebbe restituire: oggi (pending) + tra 3 giorni (pending) + tra 7 giorni (scheduled) = 3
        assert response.data['count'] == 3
    
    def test_filter_by_scadenza(self, api_client, user, scadenza_base, occorrenze_test):
        """Test filtro per ID scadenza."""
        api_client.force_authenticate(user=user)
        
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'scadenza': scadenza_base.id
        })
        assert response.status_code == 200
        assert response.data['count'] == 5  # Tutte le occorrenze
    
    def test_ordering(self, api_client, user, occorrenze_test):
        """Test ordinamento risultati."""
        api_client.force_authenticate(user=user)
        
        # Ordinamento ascendente
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'ordering': 'inizio'
        })
        assert response.status_code == 200
        results = response.data['results']
        # Verifica che siano in ordine crescente
        for i in range(len(results) - 1):
            assert results[i]['inizio'] <= results[i + 1]['inizio']
        
        # Ordinamento discendente
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'ordering': '-inizio'
        })
        assert response.status_code == 200
        results = response.data['results']
        # Verifica che siano in ordine decrescente
        for i in range(len(results) - 1):
            assert results[i]['inizio'] >= results[i + 1]['inizio']
    
    def test_pagination(self, api_client, user, occorrenze_test):
        """Test paginazione risultati."""
        api_client.force_authenticate(user=user)
        
        # Verifica che la paginazione funzioni se configurata
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'page_size': 2,
            'page': 1
        })
        assert response.status_code == 200
        # Il numero di risultati dipende dalle impostazioni di paginazione
        assert 'results' in response.data
        assert 'count' in response.data
        assert response.data['count'] == 5  # Totale occorrenze
    
    def test_empty_result_with_strict_filters(self, api_client, user, occorrenze_test):
        """Test che filtri stretti restituiscano correttamente risultato vuoto."""
        api_client.force_authenticate(user=user)
        
        # Range futuro senza occorrenze
        tra_30_giorni = (timezone.now().date() + timedelta(days=30)).isoformat()
        tra_60_giorni = (timezone.now().date() + timedelta(days=60)).isoformat()
        
        response = api_client.get('/api/v1/scadenze/occorrenze/', {
            'inizio__gte': tra_30_giorni,
            'inizio__lt': tra_60_giorni,
            'stato__in': 'pending,scheduled'
        })
        assert response.status_code == 200
        assert response.data['count'] == 0
        assert len(response.data['results']) == 0
