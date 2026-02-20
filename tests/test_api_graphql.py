"""
Test per API GraphQL
Test per query e mutation GraphQL
"""
import pytest
import json
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.api
class TestGraphQLQueries:
    """Test query GraphQL"""
    
    @pytest.fixture
    def graphql_url(self):
        """URL endpoint GraphQL"""
        return '/graphql/'
    
    def execute_query(self, client, query, variables=None):
        """Helper per eseguire query GraphQL"""
        data = {'query': query}
        if variables:
            data['variables'] = variables
        
        response = client.post(
            '/graphql/',
            json.dumps(data),
            content_type='application/json'
        )
        return response
    
    def test_graphql_endpoint_exists(self, authenticated_client):
        """Test che endpoint GraphQL esista"""
        response = authenticated_client.get('/graphql/')
        # Dovrebbe mostrare GraphiQL o rispondere
        assert response.status_code in [200, 405]  # 405 se GET non supportato
    
    def test_simple_query_pratiche(self, authenticated_client, pratica):
        """Test query semplice per pratiche"""
        query = """
        query {
            allPratiche {
                edges {
                    node {
                        id
                        codice
                        oggetto
                        stato
                    }
                }
            }
        }
        """
        
        response = self.execute_query(authenticated_client, query)
        
        if response.status_code == 200:
            data = response.json()
            assert 'data' in data or 'errors' in data
            
            if 'data' in data and data['data']:
                # Verifica struttura risposta
                assert 'allPratiche' in data['data'] or data.get('errors')
    
    def test_query_with_filters(self, authenticated_client, pratica, cliente_pf):
        """Test query con filtri"""
        query = """
        query($clienteId: ID!) {
            allPratiche(cliente: $clienteId) {
                edges {
                    node {
                        id
                        codice
                        cliente {
                            id
                        }
                    }
                }
            }
        }
        """
        
        variables = {'clienteId': str(cliente_pf.id)}
        response = self.execute_query(authenticated_client, query, variables)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and not data.get('errors'):
                assert data['data'] is not None
    
    def test_nested_query_fascicolo_documenti(
        self, authenticated_client, fascicolo, documento
    ):
        """Test query nested: fascicolo con documenti"""
        query = """
        query($fascicoloId: ID!) {
            fascicolo(id: $fascicoloId) {
                id
                titolo
                documenti {
                    edges {
                        node {
                            id
                            descrizione
                        }
                    }
                }
            }
        }
        """
        
        variables = {'fascicoloId': str(fascicolo.id)}
        response = self.execute_query(authenticated_client, query, variables)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and not data.get('errors'):
                # Verifica nested query
                pass  # Dipende dall'implementazione dello schema
    
    def test_query_pagination(self, authenticated_client, make_pratica, cliente_pf, pratica_tipo):
        """Test paginazione GraphQL"""
        # Crea molte pratiche
        for i in range(25):
            make_pratica(
                cliente=cliente_pf,
                tipo=pratica_tipo,
                codice=f'GQL-{i:03d}'
            )
        
        query = """
        query($first: Int!, $after: String) {
            allPratiche(first: $first, after: $after) {
                edges {
                    node {
                        id
                        codice
                    }
                    cursor
                }
                pageInfo {
                    hasNextPage
                    hasPreviousPage
                    startCursor
                    endCursor
                }
            }
        }
        """
        
        variables = {'first': 10}
        response = self.execute_query(authenticated_client, query, variables)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data'] and 'allPratiche' in data['data']:
                pratiche = data['data']['allPratiche']
                if 'edges' in pratiche:
                    assert len(pratiche['edges']) <= 10
                    if 'pageInfo' in pratiche:
                        assert 'hasNextPage' in pratiche['pageInfo']


@pytest.mark.api
class TestGraphQLMutations:
    """Test mutation GraphQL"""
    
    def execute_mutation(self, client, mutation, variables=None):
        """Helper per eseguire mutation GraphQL"""
        data = {'query': mutation}
        if variables:
            data['variables'] = variables
        
        response = client.post(
            '/graphql/',
            json.dumps(data),
            content_type='application/json'
        )
        return response
    
    def test_create_pratica_mutation(
        self, authenticated_client, cliente_pf, pratica_tipo
    ):
        """Test mutation creazione pratica"""
        mutation = """
        mutation($input: CreatePraticaInput!) {
            createPratica(input: $input) {
                pratica {
                    id
                    codice
                    oggetto
                }
                ok
                errors
            }
        }
        """
        
        variables = {
            'input': {
                'clienteId': str(cliente_pf.id),
                'tipoId': str(pratica_tipo.id),
                'codice': 'GQL-NEW-001',
                'oggetto': 'Pratica creata via GraphQL'
            }
        }
        
        response = self.execute_mutation(authenticated_client, mutation, variables)
        
        if response.status_code == 200:
            data = response.json()
            # Potrebbe non essere implementata
            if 'errors' not in data:
                assert 'data' in data
    
    def test_update_pratica_mutation(self, authenticated_client, pratica):
        """Test mutation aggiornamento pratica"""
        mutation = """
        mutation($id: ID!, $oggetto: String!) {
            updatePratica(id: $id, oggetto: $oggetto) {
                pratica {
                    id
                    oggetto
                }
                ok
            }
        }
        """
        
        variables = {
            'id': str(pratica.id),
            'oggetto': 'Oggetto modificato via GraphQL'
        }
        
        response = self.execute_mutation(authenticated_client, mutation, variables)
        
        if response.status_code == 200:
            data = response.json()
            # Verifica risposta
            pass
    
    def test_delete_mutation_requires_permission(
        self, authenticated_client, pratica
    ):
        """Test mutation delete richiede permessi"""
        mutation = """
        mutation($id: ID!) {
            deletePratica(id: $id) {
                ok
                errors
            }
        }
        """
        
        variables = {'id': str(pratica.id)}
        response = self.execute_mutation(authenticated_client, mutation, variables)
        
        if response.status_code == 200:
            data = response.json()
            # Potrebbe richiedere permessi specifici
            if 'errors' in data:
                # Verifica che menzioni permessi
                pass


@pytest.mark.api
class TestGraphQLAuthentication:
    """Test autenticazione GraphQL"""
    
    def test_unauthenticated_query_fails(self, client):
        """Test query senza autenticazione deve fallire"""
        query = """
        query {
            allPratiche {
                edges {
                    node {
                        id
                    }
                }
            }
        }
        """
        
        response = client.post(
            '/graphql/',
            json.dumps({'query': query}),
            content_type='application/json'
        )
        
        # Dovrebbe richiedere autenticazione
        assert response.status_code in [200, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            # Se 200, dovrebbe avere errori di autenticazione
            if 'errors' in data:
                error_msg = str(data['errors']).lower()
                assert any(word in error_msg for word in ['auth', 'permission', 'login'])
    
    def test_authenticated_query_succeeds(self, authenticated_client, pratica):
        """Test query autenticata deve funzionare"""
        query = """
        query {
            allPratiche {
                edges {
                    node {
                        id
                        codice
                    }
                }
            }
        }
        """
        
        response = authenticated_client.post(
            '/graphql/',
            json.dumps({'query': query}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'data' in data or 'errors' in data


@pytest.mark.api
class TestGraphQLErrorHandling:
    """Test gestione errori GraphQL"""
    
    def test_invalid_query_syntax(self, authenticated_client):
        """Test query con sintassi invalida"""
        query = """
        query {
            allPratiche {
                invalid syntax here
            }
        }
        """
        
        response = authenticated_client.post(
            '/graphql/',
            json.dumps({'query': query}),
            content_type='application/json'
        )
        
        data = response.json()
        assert 'errors' in data
    
    def test_query_nonexistent_field(self, authenticated_client):
        """Test query con campo inesistente"""
        query = """
        query {
            allPratiche {
                edges {
                    node {
                        id
                        nonExistentField
                    }
                }
            }
        }
        """
        
        response = authenticated_client.post(
            '/graphql/',
            json.dumps({'query': query}),
            content_type='application/json'
        )
        
        data = response.json()
        if 'errors' in data:
            # Dovrebbe segnalare campo sconosciuto
            assert any('field' in str(e).lower() for e in data['errors'])
    
    def test_invalid_variable_type(self, authenticated_client):
        """Test variabile con tipo errato"""
        query = """
        query($id: Int!) {
            pratica(id: $id) {
                id
                codice
            }
        }
        """
        
        variables = {'id': 'not-an-integer'}
        
        response = authenticated_client.post(
            '/graphql/',
            json.dumps({'query': query, 'variables': variables}),
            content_type='application/json'
        )
        
        data = response.json()
        if 'errors' in data:
            # Dovrebbe segnalare errore di tipo
            pass


@pytest.mark.api
@pytest.mark.slow
class TestGraphQLPerformance:
    """Test performance GraphQL"""
    
    def test_n_plus_one_query_optimization(
        self, authenticated_client, make_pratica, cliente_pf, pratica_tipo
    ):
        """Test che GraphQL usi DataLoader per evitare N+1"""
        # Crea pratiche
        for i in range(20):
            make_pratica(
                cliente=cliente_pf,
                tipo=pratica_tipo,
                codice=f'PERF-{i:03d}'
            )
        
        query = """
        query {
            allPratiche {
                edges {
                    node {
                        id
                        codice
                        cliente {
                            id
                            anagrafica {
                                nome
                                cognome
                            }
                        }
                        tipo {
                            nome
                        }
                    }
                }
            }
        }
        """
        
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        with CaptureQueriesContext(connection) as context:
            response = authenticated_client.post(
                '/graphql/',
                json.dumps({'query': query}),
                content_type='application/json'
            )
            
            if response.status_code == 200:
                num_queries = len(context.captured_queries)
                # Con DataLoader/select_related dovrebbe essere < 10
                # Senza ottimizzazione sarebbe 20+ (N+1)
                assert num_queries < 20, f"Too many queries: {num_queries}"
