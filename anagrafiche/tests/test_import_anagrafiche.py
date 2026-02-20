"""
Test per la funzionalità di importazione anagrafiche da CSV.
"""
import io
import csv
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from anagrafiche.models import Anagrafica


class ImportAnagraficheTestCase(TestCase):
    """Test per l'importazione anagrafiche."""
    
    def setUp(self):
        """Setup del test."""
        self.client = Client()
        # Crea un utente per il login
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.import_url = reverse('anagrafiche:import')
    
    def _create_csv_file(self, rows):
        """Utility per creare un file CSV in memoria."""
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        # Header
        writer.writerow([
            'tipo', 'ragione_sociale', 'nome', 'cognome', 'codice_fiscale',
            'partita_iva', 'codice', 'denominazione_abbreviata', 'pec', 
            'email', 'telefono', 'indirizzo', 'note'
        ])
        # Dati
        for row in rows:
            writer.writerow(row)
        
        output.seek(0)
        return output.getvalue().encode('utf-8')
    
    def test_import_persona_fisica_valida(self):
        """Test importazione persona fisica valida."""
        csv_data = self._create_csv_file([
            ['PF', '', 'Mario', 'Rossi', 'RSSMRA80A01H501U', '', '', '', 
             'mario@pec.it', 'mario@email.it', '3331234567', 'Via Roma 1', 'Test']
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Anagrafica.objects.filter(codice_fiscale='RSSMRA80A01H501U').exists())
        
        anagrafica = Anagrafica.objects.get(codice_fiscale='RSSMRA80A01H501U')
        self.assertEqual(anagrafica.tipo, 'PF')
        self.assertEqual(anagrafica.nome, 'Mario')
        self.assertEqual(anagrafica.cognome, 'Rossi')
    
    def test_import_persona_giuridica_valida(self):
        """Test importazione persona giuridica valida."""
        csv_data = self._create_csv_file([
            ['PG', 'Acme S.r.l.', '', '', '12345678901', '12345678901', '', 
             'ACME SRL', 'acme@pec.it', 'info@acme.it', '024567890', 
             'Via Milano 10', 'Cliente importante']
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Anagrafica.objects.filter(codice_fiscale='12345678901').exists())
        
        anagrafica = Anagrafica.objects.get(codice_fiscale='12345678901')
        self.assertEqual(anagrafica.tipo, 'PG')
        self.assertEqual(anagrafica.ragione_sociale, 'Acme S.r.l.')
    
    def test_import_codice_fiscale_duplicato(self):
        """Test scarto per codice fiscale duplicato."""
        # Crea anagrafica esistente
        Anagrafica.objects.create(
            tipo='PF',
            nome='Mario',
            cognome='Rossi',
            codice_fiscale='RSSMRA80A01H501U'
        )
        
        # Tenta importazione duplicato
        csv_data = self._create_csv_file([
            ['PF', '', 'Luigi', 'Bianchi', 'RSSMRA80A01H501U', '', '', '', 
             '', '', '', '', '']
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        # Verifica che ci sia solo una anagrafica con quel CF
        self.assertEqual(
            Anagrafica.objects.filter(codice_fiscale='RSSMRA80A01H501U').count(), 
            1
        )
        # Verifica che il report contenga scarti
        self.assertIn('report', response.context)
        self.assertGreater(response.context['report']['num_scartate'], 0)
    
    def test_import_campi_obbligatori_mancanti_pf(self):
        """Test scarto per campi obbligatori mancanti (PF)."""
        csv_data = self._create_csv_file([
            # PF senza nome
            ['PF', '', '', 'Rossi', 'RSSMRA80A01H501U', '', '', '', '', '', '', '', ''],
            # PF senza cognome
            ['PF', '', 'Mario', '', 'VRDNNA85M45F205X', '', '', '', '', '', '', '', ''],
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        # Verifica che nessuna anagrafica sia stata creata
        self.assertEqual(Anagrafica.objects.count(), 0)
        # Verifica scarti
        self.assertIn('report', response.context)
        self.assertEqual(response.context['report']['num_scartate'], 2)
    
    def test_import_campi_obbligatori_mancanti_pg(self):
        """Test scarto per campi obbligatori mancanti (PG)."""
        csv_data = self._create_csv_file([
            # PG senza ragione sociale
            ['PG', '', '', '', '12345678901', '', '', '', '', '', '', '', ''],
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Anagrafica.objects.count(), 0)
        self.assertIn('report', response.context)
        self.assertEqual(response.context['report']['num_scartate'], 1)
    
    def test_import_tipo_non_valido(self):
        """Test scarto per tipo non valido."""
        csv_data = self._create_csv_file([
            ['XX', '', 'Mario', 'Rossi', 'RSSMRA80A01H501U', '', '', '', '', '', '', '', ''],
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Anagrafica.objects.count(), 0)
        self.assertIn('report', response.context)
        self.assertGreater(response.context['report']['num_scartate'], 0)
    
    def test_import_multiplo_misto(self):
        """Test importazione multipla con righe valide e non valide."""
        # Crea una anagrafica esistente per testare duplicato
        Anagrafica.objects.create(
            tipo='PF',
            nome='Existing',
            cognome='User',
            codice_fiscale='RSSMRA80A01H501U'
        )
        
        csv_data = self._create_csv_file([
            # Valida PF
            ['PF', '', 'Mario', 'Verdi', 'VRDMRA85M01H501Z', '', '', '', '', '', '', '', ''],
            # Duplicato (scartata)
            ['PF', '', 'Luigi', 'Bianchi', 'RSSMRA80A01H501U', '', '', '', '', '', '', '', ''],
            # Valida PG
            ['PG', 'Beta Srl', '', '', '98765432109', '', '', '', '', '', '', '', ''],
            # Tipo non valido (scartata)
            ['XX', '', 'Anna', 'Neri', 'NRENNI90A01H501P', '', '', '', '', '', '', '', ''],
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('report', response.context)
        
        report = response.context['report']
        # 2 importate (Mario Verdi, Beta Srl), 2 scartate (duplicato, tipo invalido)
        self.assertEqual(report['num_importate'], 2)
        self.assertEqual(report['num_scartate'], 2)
        self.assertEqual(report['totale'], 4)
        
        # Verifica che le anagrafiche corrette siano state create
        self.assertTrue(Anagrafica.objects.filter(codice_fiscale='VRDMRA85M01H501Z').exists())
        self.assertTrue(Anagrafica.objects.filter(codice_fiscale='98765432109').exists())
    
    def test_facsimile_csv_download(self):
        """Test download del file CSV di esempio."""
        response = self.client.get(reverse('anagrafiche:facsimile_csv'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('facsimile_anagrafiche.csv', response['Content-Disposition'])
        
        # Verifica che il contenuto sia CSV valido
        content = response.content.decode('utf-8-sig')
        reader = csv.reader(io.StringIO(content), delimiter=';')
        rows = list(reader)
        
        # Verifica header
        self.assertIn('tipo', rows[0])
        self.assertIn('codice_fiscale', rows[0])
        
        # Verifica esempi
        self.assertGreater(len(rows), 1)  # Header + almeno un esempio
    
    def test_report_structure(self):
        """Test struttura del report."""
        csv_data = self._create_csv_file([
            ['PF', '', 'Mario', 'Rossi', 'RSSMRA80A01H501U', '', '', '', '', '', '', '', ''],
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('report', response.context)
        
        report = response.context['report']
        # Verifica chiavi obbligatorie
        self.assertIn('totale', report)
        self.assertIn('num_importate', report)
        self.assertIn('num_scartate', report)
        self.assertIn('importate', report)
        self.assertIn('scartate', report)
        
        # Verifica tipi
        self.assertIsInstance(report['totale'], int)
        self.assertIsInstance(report['num_importate'], int)
        self.assertIsInstance(report['num_scartate'], int)
        self.assertIsInstance(report['importate'], list)
        self.assertIsInstance(report['scartate'], list)
        
        # Verifica struttura item importato
        if report['importate']:
            item = report['importate'][0]
            self.assertIn('riga', item)
            self.assertIn('nome', item)
            self.assertIn('codice_fiscale', item)
            self.assertIn('id', item)
    
    def test_normalizzazione_dati(self):
        """Test normalizzazione automatica dei dati."""
        csv_data = self._create_csv_file([
            # CF minuscolo, spazi extra
            ['PF', '', '  mario  ', '  rossi  ', 'rssmra80a01h501u', '', '', '', 
             'MARIO@PEC.IT', 'MARIO@EMAIL.IT', ' 333 123 4567 ', '  Via Roma 1  ', ''],
        ])
        
        response = self.client.post(
            self.import_url,
            {'file': io.BytesIO(csv_data)},
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        anagrafica = Anagrafica.objects.get(codice_fiscale='RSSMRA80A01H501U')
        
        # Verifica normalizzazione
        self.assertEqual(anagrafica.codice_fiscale, 'RSSMRA80A01H501U')  # Uppercase
        self.assertEqual(anagrafica.nome, 'Mario')  # Title case, trim
        self.assertEqual(anagrafica.cognome, 'Rossi')  # Title case, trim
        self.assertEqual(anagrafica.pec, 'mario@pec.it')  # Lowercase
        self.assertEqual(anagrafica.email, 'mario@email.it')  # Lowercase


class FacsimileCSVTestCase(TestCase):
    """Test per il download del facsimile CSV."""
    
    def setUp(self):
        """Setup del test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_csv_structure(self):
        """Test struttura del CSV di esempio."""
        response = self.client.get(reverse('anagrafiche:facsimile_csv'))
        
        content = response.content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(content), delimiter=';')
        rows = list(reader)
        
        # Verifica che ci siano esempi
        self.assertGreater(len(rows), 0)
        
        # Verifica che ci siano sia PF che PG
        tipi = {row['tipo'] for row in rows}
        self.assertIn('PF', tipi)
        self.assertIn('PG', tipi)
        
        # Verifica campi obbligatori negli esempi
        for row in rows:
            self.assertIn(row['tipo'], ['PF', 'PG'])
            self.assertTrue(row['codice_fiscale'])
            
            if row['tipo'] == 'PF':
                self.assertTrue(row['nome'])
                self.assertTrue(row['cognome'])
            else:
                self.assertTrue(row['ragione_sociale'])
