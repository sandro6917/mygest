"""
Test per verificare che il token {attr:dipendente.codice} funzioni
correttamente con attributi dinamici che referenziano anagrafiche.
"""

from datetime import date
from django.test import TestCase
from anagrafiche.models import Anagrafica, Cliente
from documenti.models import DocumentiTipo, Documento, AttributoDefinizione, AttributoValore
from documenti.utils import build_document_filename


class TestAttrAnagraficaNavigation(TestCase):
    """Test per la navigazione dotted-path negli attributi dinamici con FK Anagrafica."""
    
    def setUp(self):
        """Setup comune per tutti i test."""
        # Crea un'anagrafica cliente
        self.anagrafica_cliente = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="Azienda Test S.r.l.",
            codice_fiscale="12345678901",
            partita_iva="12345678901",
        )
        self.cliente = Cliente.objects.create(anagrafica=self.anagrafica_cliente)
        
        # Crea un'anagrafica dipendente
        self.dipendente = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_FISICA,
            cognome="Rossi",
            nome="Mario",
            codice_fiscale="RSSMRA80A01H501Z",
            codice="DIP001"
        )
    
    def test_attr_anagrafica_dotted_path_codice(self):
        """Test {attr:dipendente.codice} per accedere al codice dell'anagrafica."""
        tipo = DocumentiTipo.objects.create(
            codice="CED",
            nome="Cedolino",
            nome_file_pattern="Cedolino_{attr:dipendente.codice}_{data_documento:%Y%m%d}",
        )
        
        # Crea definizione attributo con widget anagrafica
        attr_dipendente = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="dipendente",
            nome="Dipendente",
            tipo_dato="int",  # FK salvata come int
            widget="anagrafica",  # Specifica che è un FK verso Anagrafica
            required=False,
        )
        
        # Crea documento
        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Cedolino dicembre 2024",
            data_documento=date(2024, 12, 15)
        )
        
        # Salva il valore dell'attributo (ID dell'anagrafica dipendente)
        AttributoValore.objects.create(
            documento=documento,
            definizione=attr_dipendente,
            valore=self.dipendente.pk  # Salva l'ID
        )
        
        # Test rinomina file
        filename = build_document_filename(documento, "original.pdf")
        
        # Il nome file dovrebbe includere il codice del dipendente
        self.assertEqual(filename, "Cedolino_DIP001_20241215.pdf")
    
    def test_attr_anagrafica_dotted_path_codice_fiscale(self):
        """Test {attr:dipendente.codice_fiscale} per accedere al CF dell'anagrafica."""
        tipo = DocumentiTipo.objects.create(
            codice="CED2",
            nome="Cedolino 2",
            nome_file_pattern="CED_{attr:dipendente.codice_fiscale}_{data_documento:%Y%m}",
        )
        
        # Crea definizione attributo con widget anagrafica
        attr_dipendente = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="dipendente",
            nome="Dipendente",
            tipo_dato="int",
            widget="fk_anagrafica",  # Altra variante del widget
            required=False,
        )
        
        # Crea documento
        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Cedolino gennaio 2025",
            data_documento=date(2025, 1, 15)
        )
        
        # Salva il valore dell'attributo
        AttributoValore.objects.create(
            documento=documento,
            definizione=attr_dipendente,
            valore=self.dipendente.pk
        )
        
        # Test rinomina file
        filename = build_document_filename(documento, "original.pdf")
        
        # Il nome file dovrebbe includere il codice fiscale del dipendente
        self.assertEqual(filename, "CED_RSSMRA80A01H501Z_202501.pdf")
    
    def test_attr_anagrafica_dotted_path_denominazione(self):
        """Test {attr:dipendente.codice_fiscale} per accedere al CF tramite property."""
        tipo = DocumentiTipo.objects.create(
            codice="CED3",
            nome="Cedolino 3",
            nome_file_pattern="Cedolino_{attr:anno}_{attr:mese}_{attr:dipendente.codice_fiscale}",
        )
        
        # Crea definizioni attributo
        attr_dipendente = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="dipendente",
            nome="Dipendente",
            tipo_dato="int",
            widget="anagrafica",
            required=False,
        )
        attr_anno = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="anno",
            nome="Anno",
            tipo_dato="string",
            required=False,
        )
        attr_mese = AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="mese",
            nome="Mese",
            tipo_dato="string",
            required=False,
        )
        
        # Crea documento
        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Cedolino test",
            data_documento=date(2024, 12, 15)
        )
        
        # Salva i valori degli attributi
        AttributoValore.objects.create(documento=documento, definizione=attr_dipendente, valore=self.dipendente.pk)
        AttributoValore.objects.create(documento=documento, definizione=attr_anno, valore="2024")
        AttributoValore.objects.create(documento=documento, definizione=attr_mese, valore="12")
        
        # Test rinomina file
        filename = build_document_filename(documento, "original.pdf")
        
        # Il nome file dovrebbe includere il codice fiscale del dipendente
        self.assertEqual(filename, "Cedolino_2024_12_RSSMRA80A01H501Z.pdf")
    
    def test_attr_anagrafica_missing_value(self):
        """Test {attr:dipendente.codice} quando l'attributo non ha valore."""
        tipo = DocumentiTipo.objects.create(
            codice="CED4",
            nome="Cedolino 4",
            nome_file_pattern="Cedolino_{attr:dipendente.codice}_{data_documento:%Y%m%d}",
        )
        
        # Crea definizione attributo ma NON salva il valore
        AttributoDefinizione.objects.create(
            tipo_documento=tipo,
            codice="dipendente",
            nome="Dipendente",
            tipo_dato="int",
            widget="anagrafica",
            required=False,
        )
        
        # Crea documento senza salvare l'attributo dipendente
        documento = Documento.objects.create(
            tipo=tipo,
            cliente=self.cliente,
            descrizione="Cedolino senza dipendente",
            data_documento=date(2024, 12, 15)
        )
        
        # Test rinomina file
        filename = build_document_filename(documento, "original.pdf")
        
        # Il token {attr:dipendente.codice} dovrebbe restituire stringa vuota
        # quindi il nome file sarà "Cedolino__20241215.pdf" ma verrà pulito in "Cedolino_20241215.pdf"
        self.assertEqual(filename, "Cedolino_20241215.pdf")


if __name__ == "__main__":
    import django
    import os
    import sys
    
    # Setup Django
    sys.path.insert(0, '/home/sandro/mygest')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mygest.settings')
    django.setup()
    
    # Run test
    import unittest
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAttrAnagraficaNavigation)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
