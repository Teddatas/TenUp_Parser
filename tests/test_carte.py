"""
Tests de la partie "carte des tournois" (logique pure, sans réseau ni r5py).
"""

import importlib
import unittest

from src.classements import (
    echelon_to_label,
    is_eligible,
    label_to_echelon,
)


class TestClassements(unittest.TestCase):
    def test_label_echelon_roundtrip(self):
        for label in ("NC", "30", "30/1", "15", "0", "-15"):
            self.assertEqual(echelon_to_label(label_to_echelon(label)), label)

    def test_ordre_croissant(self):
        # NC est plus faible que 30, lui-même plus faible que 15
        self.assertLess(label_to_echelon("NC"), label_to_echelon("30"))
        self.assertLess(label_to_echelon("30"), label_to_echelon("15"))
        self.assertLess(label_to_echelon("15"), label_to_echelon("-15"))

    def test_classement_numerote(self):
        self.assertGreater(label_to_echelon("N1"), label_to_echelon("-15"))

    def test_eligibilite(self):
        # un joueur classé 30 : éligible NC->15, pas éligible 15/1->N1
        self.assertTrue(is_eligible(label_to_echelon("30"), "NC", "15"))
        self.assertFalse(is_eligible(label_to_echelon("30"), "15/1", "N1"))
        # bornes vides = pas de contrainte
        self.assertTrue(is_eligible(label_to_echelon("30"), "", ""))


class TestImports(unittest.TestCase):
    """Les modules de la carte s'importent sans r5py/geopandas installés."""

    def test_modules_importables(self):
        for name in (
            "src.models",
            "src.tenup_api",
            "src.geocode",
            "src.pipeline",
            "src.export",
            "src.map_builder",
            "src.travel_matrix",
            "src.osrm",
        ):
            importlib.import_module(name)


if __name__ == "__main__":
    unittest.main()
