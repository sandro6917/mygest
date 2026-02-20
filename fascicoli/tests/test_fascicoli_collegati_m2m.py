"""
Test per verificare la funzionalità Fascicoli Collegati (M2M)
"""
import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from fascicoli.models import Fascicolo

User = get_user_model()


@pytest.mark.django_db
class TestFascicoliCollegatiM2M:
    """Test relazione M2M fascicoli_collegati"""
    
    def test_fascicolo_has_m2m_field(self):
        """Verifica che il campo fascicoli_collegati esista"""
        fascicolo = baker.make('fascicoli.Fascicolo')
        
        # Il campo deve esistere
        assert hasattr(fascicolo, 'fascicoli_collegati')
        
        # Deve essere un ManyToManyField
        field = Fascicolo._meta.get_field('fascicoli_collegati')
        assert field.many_to_many is True
        
    def test_collega_fascicolo(self):
        """Test collegamento di un fascicolo"""
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')
        
        # Collega B ad A
        fascicolo_a.fascicoli_collegati.add(fascicolo_b)
        
        # Verifica collegamento
        assert fascicolo_a.fascicoli_collegati.count() == 1
        assert fascicolo_a.fascicoli_collegati.first() == fascicolo_b
        
    def test_collegamento_unidirezionale(self):
        """Test che il collegamento sia unidirezionale (non simmetrico)"""
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')
        
        # Collega B ad A
        fascicolo_a.fascicoli_collegati.add(fascicolo_b)
        
        # A ha B collegato
        assert fascicolo_a.fascicoli_collegati.count() == 1
        
        # B NON ha A collegato (unidirezionale)
        assert fascicolo_b.fascicoli_collegati.count() == 0
        
        # Ma B può sapere chi lo ha collegato tramite reverse relation
        assert fascicolo_b.collegato_da.count() == 1
        assert fascicolo_b.collegato_da.first() == fascicolo_a
        
    def test_scollega_fascicolo(self):
        """Test scollegamento di un fascicolo"""
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')
        
        # Collega
        fascicolo_a.fascicoli_collegati.add(fascicolo_b)
        assert fascicolo_a.fascicoli_collegati.count() == 1
        
        # Scollega
        fascicolo_a.fascicoli_collegati.remove(fascicolo_b)
        assert fascicolo_a.fascicoli_collegati.count() == 0
        
    def test_collegamenti_multipli(self):
        """Test collegamento di più fascicoli"""
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')
        fascicolo_c = baker.make('fascicoli.Fascicolo')
        fascicolo_d = baker.make('fascicoli.Fascicolo')
        
        # Collega B, C, D ad A
        fascicolo_a.fascicoli_collegati.add(fascicolo_b, fascicolo_c, fascicolo_d)
        
        # Verifica
        assert fascicolo_a.fascicoli_collegati.count() == 3
        assert set(fascicolo_a.fascicoli_collegati.all()) == {fascicolo_b, fascicolo_c, fascicolo_d}
        

@pytest.mark.django_db
class TestFascicoliCollegatiAPI:
    """Test API endpoints per fascicoli collegati"""
    
    def test_list_serializer_has_counter(self, api_client, user):
        """Test che il serializer list abbia il contatore"""
        api_client.force_authenticate(user=user)
        
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')
        fascicolo_c = baker.make('fascicoli.Fascicolo')
        
        fascicolo_a.fascicoli_collegati.add(fascicolo_b, fascicolo_c)
        
        response = api_client.get('/api/v1/fascicoli/')
        
        assert response.status_code == 200
        
        # Trova fascicolo A nei risultati
        fasc_a_data = next(
            (f for f in response.data['results'] if f['id'] == fascicolo_a.id), 
            None
        )
        
        assert fasc_a_data is not None
        assert 'num_fascicoli_collegati' in fasc_a_data
        assert fasc_a_data['num_fascicoli_collegati'] == 2
        
    def test_detail_serializer_has_details(self, api_client, user):
        """Test che il serializer detail abbia i dettagli collegati"""
        api_client.force_authenticate(user=user)
        
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo', codice='TEST-B')
        
        fascicolo_a.fascicoli_collegati.add(fascicolo_b)
        
        response = api_client.get(f'/api/v1/fascicoli/{fascicolo_a.id}/')
        
        assert response.status_code == 200
        assert 'fascicoli_collegati_details' in response.data
        assert len(response.data['fascicoli_collegati_details']) == 1
        assert response.data['fascicoli_collegati_details'][0]['codice'] == 'TEST-B'
        
    def test_fascicoli_collegabili_endpoint(self, api_client, user):
        """Test endpoint fascicoli collegabili"""
        api_client.force_authenticate(user=user)
        
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')  # Collegabile
        fascicolo_c = baker.make('fascicoli.Fascicolo')  # Già collegato
        fascicolo_d = baker.make('fascicoli.Fascicolo', parent=fascicolo_a)  # Sottofascicolo
        
        # Collega C
        fascicolo_a.fascicoli_collegati.add(fascicolo_c)
        
        response = api_client.get(f'/api/v1/fascicoli/{fascicolo_a.id}/fascicoli_collegabili/')
        
        assert response.status_code == 200
        
        ids_collegabili = [f['id'] for f in response.data]
        
        # B deve essere presente (collegabile)
        assert fascicolo_b.id in ids_collegabili
        
        # A non deve essere presente (self)
        assert fascicolo_a.id not in ids_collegabili
        
        # C non deve essere presente (già collegato)
        assert fascicolo_c.id not in ids_collegabili
        
        # D non deve essere presente (sottofascicolo)
        assert fascicolo_d.id not in ids_collegabili
        
    def test_collega_fascicolo_endpoint(self, api_client, user):
        """Test endpoint per collegare fascicolo"""
        api_client.force_authenticate(user=user)
        
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')
        
        response = api_client.post(
            f'/api/v1/fascicoli/{fascicolo_a.id}/collega_fascicolo/',
            {'fascicolo_id': fascicolo_b.id}
        )
        
        assert response.status_code == 200
        assert response.data['success'] is True
        
        # Verifica collegamento nel DB
        fascicolo_a.refresh_from_db()
        assert fascicolo_a.fascicoli_collegati.count() == 1
        assert fascicolo_a.fascicoli_collegati.first() == fascicolo_b
        
    def test_collega_fascicolo_self_error(self, api_client, user):
        """Test errore collegamento a se stesso"""
        api_client.force_authenticate(user=user)
        
        fascicolo = baker.make('fascicoli.Fascicolo')
        
        response = api_client.post(
            f'/api/v1/fascicoli/{fascicolo.id}/collega_fascicolo/',
            {'fascicolo_id': fascicolo.id}
        )
        
        assert response.status_code == 400
        assert 'se stesso' in response.data['error'].lower()
        
    def test_collega_fascicolo_sottofascicolo_error(self, api_client, user):
        """Test errore collegamento sottofascicolo"""
        api_client.force_authenticate(user=user)
        
        fascicolo_parent = baker.make('fascicoli.Fascicolo')
        fascicolo_child = baker.make('fascicoli.Fascicolo', parent=fascicolo_parent)
        
        response = api_client.post(
            f'/api/v1/fascicoli/{fascicolo_parent.id}/collega_fascicolo/',
            {'fascicolo_id': fascicolo_child.id}
        )
        
        assert response.status_code == 400
        assert 'sottofascicolo' in response.data['error'].lower()
        
    def test_collega_fascicolo_duplicato_error(self, api_client, user):
        """Test errore collegamento duplicato"""
        api_client.force_authenticate(user=user)
        
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')
        
        # Primo collegamento
        fascicolo_a.fascicoli_collegati.add(fascicolo_b)
        
        # Secondo collegamento (duplicato)
        response = api_client.post(
            f'/api/v1/fascicoli/{fascicolo_a.id}/collega_fascicolo/',
            {'fascicolo_id': fascicolo_b.id}
        )
        
        assert response.status_code == 400
        assert 'già collegato' in response.data['error'].lower()
        
    def test_scollega_fascicolo_endpoint(self, api_client, user):
        """Test endpoint per scollegare fascicolo"""
        api_client.force_authenticate(user=user)
        
        fascicolo_a = baker.make('fascicoli.Fascicolo')
        fascicolo_b = baker.make('fascicoli.Fascicolo')
        
        # Collega
        fascicolo_a.fascicoli_collegati.add(fascicolo_b)
        
        # Scollega
        response = api_client.post(
            f'/api/v1/fascicoli/{fascicolo_a.id}/scollega_fascicolo/',
            {'fascicolo_id': fascicolo_b.id}
        )
        
        assert response.status_code == 200
        assert response.data['success'] is True
        
        # Verifica scollegamento nel DB
        fascicolo_a.refresh_from_db()
        assert fascicolo_a.fascicoli_collegati.count() == 0
