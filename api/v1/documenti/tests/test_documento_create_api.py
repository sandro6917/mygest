from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from anagrafiche.models import Anagrafica, Cliente
from documenti.models import DocumentiTipo


class DocumentoCreateAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="apiuser",
            password="strong-pass-123",
            email="apiuser@example.com",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

        self.anagrafica = Anagrafica.objects.create(
            tipo=Anagrafica.TipoSoggetto.PERSONA_GIURIDICA,
            ragione_sociale="API Test S.p.A.",
            codice_fiscale="12345678901",
            partita_iva="12345678901",
        )
        self.cliente = Cliente.objects.create(anagrafica=self.anagrafica)
        self.tipo = DocumentiTipo.objects.create(codice="API", nome="Documento API")

        self.url = "/api/v1/documenti/"

    def test_create_document_returns_detail_payload(self):
        payload = {
            "tipo": self.tipo.id,
            "cliente": self.cliente.id,
            "descrizione": "Documento creato via API",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn("id", response.data)
        self.assertIn("data_documento", response.data)
        self.assertRegex(response.data["data_documento"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(response.data["descrizione"], payload["descrizione"])
        self.assertEqual(response.data["cliente"], self.cliente.id)
        self.assertEqual(response.data["tipo"], self.tipo.id)
