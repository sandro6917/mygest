from django.test import TestCase

from .models import TitolarioVoce


class SeedTest(TestCase):
    databases = {"default"}

    def test_seed_titolario_roots_present(self):
        expected_root_codes = {
            "GOV",
            "AF",
            "HR",
            "SALES",
            "MKT",
            "PROC",
            "OPS",
            "LOG",
            "IT",
            "LEG",
            "QHSE",
            "RND",
            "PRJ",
        }
        actual_root_codes = set(
            TitolarioVoce.objects.filter(parent__isnull=True).values_list("codice", flat=True)
        )
        self.assertTrue(expected_root_codes.issubset(actual_root_codes))
