"""
Test di carico e stress testing con Locust
Esegui con: locust -f tests/test_load.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between, TaskSet
import random
import json


class UserBehavior(TaskSet):
    """Comportamento utente simulato"""
    
    def on_start(self):
        """Eseguito all'inizio - Login"""
        self.login()
    
    def login(self):
        """Login utente"""
        response = self.client.post("/accounts/login/", {
            "username": "testuser",
            "password": "testpass123",
        })
        if response.status_code == 200:
            print("Login successful")
        else:
            print(f"Login failed: {response.status_code}")
    
    @task(3)
    def view_home(self):
        """Visualizza home page"""
        self.client.get("/")
    
    @task(5)
    def view_pratiche_list(self):
        """Visualizza lista pratiche"""
        self.client.get("/pratiche/")
    
    @task(2)
    def view_pratica_detail(self):
        """Visualizza dettaglio pratica"""
        # Simula visualizzazione pratica random
        pratica_id = random.randint(1, 100)
        self.client.get(f"/pratiche/{pratica_id}/", name="/pratiche/[id]")
    
    @task(4)
    def view_documenti_list(self):
        """Visualizza lista documenti"""
        self.client.get("/documenti/")
    
    @task(2)
    def view_documento_detail(self):
        """Visualizza dettaglio documento"""
        documento_id = random.randint(1, 100)
        self.client.get(f"/documenti/{documento_id}/", name="/documenti/[id]")
    
    @task(3)
    def view_fascicoli_list(self):
        """Visualizza lista fascicoli"""
        self.client.get("/fascicoli/")
    
    @task(1)
    def view_scadenze(self):
        """Visualizza scadenze"""
        self.client.get("/scadenze/")
    
    @task(2)
    def search_pratiche(self):
        """Ricerca pratiche"""
        search_terms = ["test", "pratica", "cliente", "2024"]
        query = random.choice(search_terms)
        self.client.get(f"/pratiche/?q={query}", name="/pratiche/?q=[query]")


class APIUserBehavior(TaskSet):
    """Comportamento API user"""
    
    def on_start(self):
        """Setup autenticazione API"""
        self.client.headers.update({
            "Content-Type": "application/json"
        })
        # Login per ottenere session
        self.client.post("/accounts/login/", {
            "username": "testuser",
            "password": "testpass123"
        })
    
    @task(5)
    def api_list_comunicazioni(self):
        """GET /api/comunicazioni/"""
        self.client.get("/api/comunicazioni/")
    
    @task(3)
    def api_get_comunicazione(self):
        """GET /api/comunicazioni/{id}/"""
        com_id = random.randint(1, 50)
        self.client.get(f"/api/comunicazioni/{com_id}/", name="/api/comunicazioni/[id]")
    
    @task(2)
    def api_create_comunicazione(self):
        """POST /api/comunicazioni/"""
        data = {
            "destinatario": random.randint(1, 10),
            "oggetto": f"Test load {random.randint(1000, 9999)}",
            "testo": "Messaggio di test per load testing",
            "tipo": "EMAIL"
        }
        self.client.post(
            "/api/comunicazioni/",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
    
    @task(4)
    def api_list_pratiche(self):
        """GET /api/pratiche/"""
        page = random.randint(1, 5)
        self.client.get(f"/api/pratiche/?page={page}", name="/api/pratiche/?page=[n]")
    
    @task(1)
    def api_filter_pratiche(self):
        """GET /api/pratiche/ con filtri"""
        cliente_id = random.randint(1, 20)
        self.client.get(
            f"/api/pratiche/?cliente={cliente_id}",
            name="/api/pratiche/?cliente=[id]"
        )


class GraphQLUserBehavior(TaskSet):
    """Comportamento GraphQL user"""
    
    def on_start(self):
        """Setup"""
        self.client.post("/accounts/login/", {
            "username": "testuser",
            "password": "testpass123"
        })
    
    @task(5)
    def graphql_query_pratiche(self):
        """Query GraphQL pratiche"""
        query = """
        query {
            allPratiche(first: 10) {
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
        self.client.post(
            "/graphql/",
            json={"query": query},
            headers={"Content-Type": "application/json"}
        )
    
    @task(3)
    def graphql_query_with_filter(self):
        """Query GraphQL con filtro"""
        query = """
        query($clienteId: ID!) {
            allPratiche(cliente: $clienteId, first: 5) {
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
        variables = {"clienteId": str(random.randint(1, 20))}
        self.client.post(
            "/graphql/",
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"}
        )


class WebUser(HttpUser):
    """Utente web standard"""
    tasks = [UserBehavior]
    wait_time = between(1, 3)  # Attesa tra 1 e 3 secondi tra le richieste
    weight = 3  # Peso relativo rispetto ad altri user types


class APIUser(HttpUser):
    """Utente API"""
    tasks = [APIUserBehavior]
    wait_time = between(0.5, 2)
    weight = 2


class GraphQLUser(HttpUser):
    """Utente GraphQL"""
    tasks = [GraphQLUserBehavior]
    wait_time = between(0.5, 2)
    weight = 1


# ====================================
# SCENARI DI TEST SPECIFICI
# ====================================

class PeakLoadUser(HttpUser):
    """Simula carico di picco"""
    wait_time = between(0.1, 0.5)  # Richieste molto frequenti
    
    @task
    def rapid_fire_requests(self):
        """Richieste rapide"""
        endpoints = [
            "/pratiche/",
            "/documenti/",
            "/fascicoli/",
            "/api/comunicazioni/",
        ]
        for endpoint in endpoints:
            self.client.get(endpoint)


class HeavyQueryUser(HttpUser):
    """Simula query pesanti"""
    wait_time = between(2, 5)
    
    @task
    def heavy_list_query(self):
        """Query lista completa senza filtri"""
        self.client.get("/pratiche/?page_size=100")
    
    @task
    def complex_search(self):
        """Ricerca complessa"""
        self.client.get("/documenti/?q=test&tipo=1&anno=2024&fascicolo__isnull=False")
    
    @task
    def nested_graphql_query(self):
        """Query GraphQL nested complessa"""
        query = """
        query {
            allPratiche(first: 50) {
                edges {
                    node {
                        id
                        codice
                        cliente {
                            id
                            anagrafica {
                                nome
                                cognome
                                email
                            }
                        }
                        tipo {
                            nome
                        }
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
            }
        }
        """
        self.client.post(
            "/graphql/",
            json={"query": query},
            headers={"Content-Type": "application/json"}
        )


class ReadOnlyUser(HttpUser):
    """Utente solo lettura (più comune)"""
    wait_time = between(1, 4)
    weight = 5  # Molto comune
    
    @task(10)
    def view_lists(self):
        """Visualizza liste"""
        endpoints = [
            "/pratiche/",
            "/documenti/",
            "/fascicoli/",
            "/scadenze/",
        ]
        self.client.get(random.choice(endpoints))
    
    @task(3)
    def view_details(self):
        """Visualizza dettagli"""
        entity_type = random.choice(["pratiche", "documenti", "fascicoli"])
        entity_id = random.randint(1, 100)
        self.client.get(f"/{entity_type}/{entity_id}/", name=f"/{entity_type}/[id]")
    
    @task(2)
    def search(self):
        """Ricerche"""
        query = random.choice(["test", "cliente", "2024", "pratica"])
        entity_type = random.choice(["pratiche", "documenti"])
        self.client.get(f"/{entity_type}/?q={query}", name=f"/{entity_type}/?q=[query]")


class CreateUpdateUser(HttpUser):
    """Utente che crea/modifica dati"""
    wait_time = between(3, 8)
    weight = 1  # Meno comune
    
    def on_start(self):
        self.client.post("/accounts/login/", {
            "username": "testuser",
            "password": "testpass123"
        })
    
    @task(5)
    def create_comunicazione(self):
        """Crea comunicazione"""
        self.client.post("/api/comunicazioni/", json={
            "destinatario": random.randint(1, 10),
            "oggetto": f"Test {random.randint(1000, 9999)}",
            "testo": "Test message",
            "tipo": "EMAIL"
        })
    
    @task(2)
    def update_pratica(self):
        """Aggiorna pratica"""
        pratica_id = random.randint(1, 50)
        self.client.patch(f"/api/pratiche/{pratica_id}/", json={
            "oggetto": f"Updated {random.randint(1000, 9999)}"
        })
