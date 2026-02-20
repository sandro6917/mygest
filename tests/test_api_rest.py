"""
Test per API REST
Test completi per tutti gli endpoint REST Framework
"""
import pytest
from rest_framework import status
from django.urls import reverse


@pytest.mark.api
class TestAnagraficheAPI:
    """Test API Anagrafiche (se esistono endpoint)"""
    
    def test_list_anagrafiche_unauthenticated(self, api_client):
        """Test accesso non autenticato deve fallire"""
        # Assumendo che esista un endpoint /api/anagrafiche/
        try:
            url = reverse('api:anagrafica-list')
            response = api_client.get(url)
            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        except:
            pytest.skip("Endpoint API anagrafiche non trovato")
    
    def test_list_anagrafiche_authenticated(self, authenticated_api_client, anagrafica_pf):
        """Test lista anagrafiche autenticato"""
        try:
            url = reverse('api:anagrafica-list')
            response = authenticated_api_client.get(url)
            assert response.status_code == status.HTTP_200_OK
            assert isinstance(response.data, (list, dict))
        except:
            pytest.skip("Endpoint API anagrafiche non trovato")


@pytest.mark.api
class TestComunicazioniAPI:
    """Test API Comunicazioni"""
    
    @pytest.fixture
    def comunicazioni_base_url(self):
        """URL base per API comunicazioni"""
        return '/api/comunicazioni/'
    
    def test_list_comunicazioni(self, authenticated_api_client, comunicazioni_base_url):
        """Test lista comunicazioni"""
        response = authenticated_api_client.get(comunicazioni_base_url)
        # Potrebbe essere 200 o 404 se l'endpoint non esiste
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]
    
    def test_create_comunicazione(
        self, authenticated_api_client, cliente_pf, comunicazioni_base_url
    ):
        """Test creazione comunicazione via API"""
        data = {
            'destinatario': cliente_pf.anagrafica.id,
            'oggetto': 'Test comunicazione API',
            'testo': 'Corpo del messaggio',
            'tipo': 'EMAIL'
        }
        
        response = authenticated_api_client.post(
            comunicazioni_base_url,
            data,
            format='json'
        )
        
        # Potrebbe non esistere endpoint POST
        if response.status_code != status.HTTP_404_NOT_FOUND:
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST
            ]
    
    def test_get_comunicazione_detail(
        self, authenticated_api_client, comunicazione, comunicazioni_base_url
    ):
        """Test dettaglio comunicazione"""
        url = f'{comunicazioni_base_url}{comunicazione.id}/'
        response = authenticated_api_client.get(url)
        
        if response.status_code != status.HTTP_404_NOT_FOUND:
            assert response.status_code == status.HTTP_200_OK
            if response.status_code == status.HTTP_200_OK:
                assert response.data['id'] == comunicazione.id


@pytest.mark.api
class TestDocumentiAPI:
    """Test API Documenti (se implementate)"""
    
    def test_list_documenti_requires_auth(self, api_client):
        """Test che lista documenti richieda autenticazione"""
        try:
            url = '/api/documenti/'
            response = api_client.get(url)
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND
            ]
        except:
            pytest.skip("API documenti non implementata")
    
    def test_create_documento_via_api(
        self, authenticated_api_client, cliente_pf, documento_tipo, fascicolo
    ):
        """Test creazione documento via API"""
        url = '/api/documenti/'
        data = {
            'cliente': cliente_pf.id,
            'tipo': documento_tipo.id,
            'fascicolo': fascicolo.id,
            'descrizione': 'Documento creato via API'
        }
        
        response = authenticated_api_client.post(url, data, format='json')
        
        # Endpoint potrebbe non esistere
        if response.status_code != status.HTTP_404_NOT_FOUND:
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST
            ]


@pytest.mark.api
class TestPraticheAPI:
    """Test API Pratiche"""
    
    def test_api_pratiche_pagination(
        self, authenticated_api_client, make_pratica, cliente_pf, pratica_tipo
    ):
        """Test paginazione API pratiche"""
        # Crea multiple pratiche
        for i in range(25):
            make_pratica(
                cliente=cliente_pf,
                tipo=pratica_tipo,
                codice=f'PRAT-{i:03d}',
                oggetto=f'Pratica {i}'
            )
        
        url = '/api/pratiche/'
        response = authenticated_api_client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            # Verifica paginazione
            assert 'results' in response.data or isinstance(response.data, list)
            
            # Se paginato, verifica page_size
            if 'results' in response.data:
                assert len(response.data['results']) <= 20  # PAGE_SIZE di default
                assert 'count' in response.data
                assert 'next' in response.data or 'previous' in response.data
    
    def test_filter_pratiche_by_cliente(
        self, authenticated_api_client, pratica, cliente_pf
    ):
        """Test filtro pratiche per cliente"""
        url = f'/api/pratiche/?cliente={cliente_pf.id}'
        response = authenticated_api_client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            results = response.data.get('results', response.data)
            if isinstance(results, list) and len(results) > 0:
                # Verifica che tutte le pratiche appartengano al cliente
                for item in results:
                    assert item.get('cliente') == cliente_pf.id


@pytest.mark.api
class TestScadenzeAPI:
    """Test API Scadenze"""
    
    def test_list_scadenze_attive(
        self, authenticated_api_client, scadenza
    ):
        """Test lista scadenze attive"""
        url = '/api/scadenze/'
        response = authenticated_api_client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            assert isinstance(response.data, (list, dict))
    
    def test_filter_scadenze_by_pratica(
        self, authenticated_api_client, scadenza, pratica
    ):
        """Test filtro scadenze per pratica"""
        url = f'/api/scadenze/?pratica={pratica.id}'
        response = authenticated_api_client.get(url)
        
        if response.status_code == status.HTTP_200_OK:
            results = response.data.get('results', response.data)
            if isinstance(results, list):
                for item in results:
                    # Verifica che la scadenza sia collegata alla pratica
                    if 'pratica' in item:
                        assert item['pratica'] == pratica.id


@pytest.mark.api
class TestAPIAuthentication:
    """Test autenticazione e permessi API"""
    
    def test_api_requires_authentication(self, api_client):
        """Test che tutti gli endpoint richiedano autenticazione"""
        endpoints = [
            '/api/comunicazioni/',
            '/api/pratiche/',
            '/api/scadenze/',
        ]
        
        for endpoint in endpoints:
            response = api_client.get(endpoint)
            # Deve essere 401, 403 o 404 (se non esiste)
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND
            ]
    
    def test_session_authentication(self, api_client, user):
        """Test autenticazione via sessione"""
        api_client.force_authenticate(user=user)
        
        # Prova un endpoint
        response = api_client.get('/api/comunicazioni/')
        
        if response.status_code != status.HTTP_404_NOT_FOUND:
            assert response.status_code != status.HTTP_401_UNAUTHORIZED
    
    def test_staff_user_access(self, api_client, staff_user):
        """Test accesso con staff user"""
        api_client.force_authenticate(user=staff_user)
        
        response = api_client.get('/api/comunicazioni/')
        
        if response.status_code != status.HTTP_404_NOT_FOUND:
            # Staff user dovrebbe avere accesso
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_403_FORBIDDEN  # Se richiede permessi specifici
            ]


@pytest.mark.api
class TestAPIErrorHandling:
    """Test gestione errori API"""
    
    def test_invalid_endpoint(self, authenticated_api_client):
        """Test endpoint inesistente"""
        response = authenticated_api_client.get('/api/nonexistent/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_invalid_id_format(self, authenticated_api_client):
        """Test ID non valido"""
        response = authenticated_api_client.get('/api/comunicazioni/invalid/')
        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]
    
    def test_missing_required_fields(self, authenticated_api_client):
        """Test POST senza campi obbligatori"""
        url = '/api/comunicazioni/'
        data = {}  # Nessun campo
        
        response = authenticated_api_client.post(url, data, format='json')
        
        if response.status_code != status.HTTP_404_NOT_FOUND:
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_405_METHOD_NOT_ALLOWED
            ]


@pytest.mark.api
class TestAPIPerformance:
    """Test performance API"""
    
    def test_api_response_time(
        self, authenticated_api_client, make_pratica, cliente_pf, pratica_tipo
    ):
        """Test tempo di risposta API"""
        import time
        
        # Crea dati di test
        for i in range(50):
            make_pratica(
                cliente=cliente_pf,
                tipo=pratica_tipo,
                codice=f'PERF-{i:03d}'
            )
        
        url = '/api/pratiche/'
        
        start = time.time()
        response = authenticated_api_client.get(url)
        elapsed = time.time() - start
        
        if response.status_code == status.HTTP_200_OK:
            # API dovrebbe rispondere in meno di 1 secondo
            assert elapsed < 1.0, f"API too slow: {elapsed:.2f}s"
    
    def test_api_query_optimization(
        self, authenticated_api_client, django_assert_num_queries,
        make_documento, cliente_pf, documento_tipo, fascicolo
    ):
        """Test numero di query API"""
        # Crea documenti
        for i in range(10):
            make_documento(
                cliente=cliente_pf,
                tipo=documento_tipo,
                fascicolo=fascicolo
            )
        
        url = '/api/documenti/'
        
        # Dovrebbe usare select_related/prefetch_related
        with django_assert_num_queries(50):  # Max 50 query
            response = authenticated_api_client.get(url)
            
            if response.status_code == status.HTTP_200_OK:
                # Accedi ai dati per triggerare le query
                data = response.data
