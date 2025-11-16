from django.test import TestCase
from .models import TitolarioVoce

class SeedTest(TestCase):
    databases = {"default"}

    def test_seed_20_voci(self):
        self.assertEqual(TitolarioVoce.objects.count(), 20)
