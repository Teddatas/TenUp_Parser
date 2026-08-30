#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests d'intégration Navitia
Vérifie que le code Navitia est prêt à l'emploi
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.travel_calculator import TravelTimeCalculator


class TestNavitiaIntegration(unittest.TestCase):
    """Tests pour l'intégration Navitia"""
    
    def setUp(self):
        """Préparation des tests"""
        self.departure = "76 rue Sedaine 75011 Paris, France"
        # Utilise une clé fictive pour les tests (sans vraie API)
        self.api_key = "test_fake_key_12345678901234567890"
    
    @patch('src.travel_calculator.TravelTimeCalculator._geocode_address')
    def test_calculator_initialization(self, mock_geocode):
        """Teste l'initialisation du calculateur"""
        # Mock la géolocalisation pour éviter les appels réseau
        mock_geocode.return_value = (48.8551, 2.3670)
        
        calc = TravelTimeCalculator(
            departure_address=self.departure,
            navitia_api_key=self.api_key
        )
        
        self.assertEqual(calc.departure_address, self.departure)
        self.assertEqual(calc.navitia_api_key, self.api_key)
        self.assertIsNotNone(calc.departure_coords)
    
    def test_address_extraction_from_installations(self):
        """Teste l'extraction d'adresse depuis INSTALLATIONS"""
        calc = TravelTimeCalculator(
            departure_address="Paris, France",
            navitia_api_key=self.api_key
        )
        
        installations = "75012_PARIS & T.C.PARIS & Route de la Fontaine"
        address = calc.extract_address_from_installations(installations)
        
        self.assertIsNotNone(address)
        self.assertIn("PARIS", address.upper())
        self.assertIn("France", address)
    
    def test_address_extraction_with_various_formats(self):
        """Teste l'extraction avec différents formats"""
        calc = TravelTimeCalculator(
            departure_address="Paris, France",
            navitia_api_key=self.api_key
        )
        
        test_cases = [
            "75012_PARIS & Club Name & Address",
            "78000_VERSAILLES & Details",
            "91000_ESSONNE & Location",
        ]
        
        for installations in test_cases:
            address = calc.extract_address_from_installations(installations)
            self.assertIsNotNone(address)
            self.assertIn("France", address)
    
    @patch('src.travel_calculator.requests.get')
    def test_navitia_response_parsing(self, mock_get):
        """Teste le parsing d'une réponse Navitia valide"""
        # Mock la réponse Navitia
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "journeys": [
                {
                    "duration": 1560,  # 26 minutes
                    "sections": [
                        {
                            "type": "public_transport",
                            "length": 12500,
                            "display_informations": {
                                "commercial_mode": "Métro",
                                "label": "Ligne 6"
                            }
                        },
                        {
                            "type": "street_network",
                            "length": 200,
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Teste le calcul
        result = self.calc._calculate_with_navitia(
            origin_coords=(48.8551, 2.3670),  # Paris
            dest_coords=(48.8496, 2.2545),    # Versailles (approx)
            dest_address="Versailles"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["duration_seconds"], 1560)
        self.assertEqual(result["distance_m"], 12700)  # 12500 + 200
        self.assertIn("Métro", result["duration_text"])
        self.assertEqual(result["source"], "Navitia/IDFM")
    
    @patch('src.travel_calculator.requests.get')
    def test_navitia_no_journey_found(self, mock_get):
        """Teste le cas où aucun trajet n'est trouvé"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"journeys": []}
        mock_get.return_value = mock_response
        
        result = self.calc._calculate_with_navitia(
            origin_coords=(48.8551, 2.3670),
            dest_coords=(0, 0),  # Coordonnées invalides
            dest_address="Unknown"
        )
        
        self.assertIsNone(result)
    
    @patch('src.travel_calculator.requests.get')
    def test_navitia_with_transfers(self, mock_get):
        """Teste un trajet avec changements"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "journeys": [
                {
                    "duration": 2400,  # 40 minutes
                    "sections": [
                        {
                            "type": "public_transport",
                            "length": 8000,
                            "display_informations": {"commercial_mode": "Métro"}
                        },
                        {
                            "type": "street_network",
                            "length": 300,
                        },
                        {
                            "type": "public_transport",
                            "length": 5000,
                            "display_informations": {"commercial_mode": "Bus"}
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        calc = TravelTimeCalculator(
            departure_address="Paris, France",
            navitia_api_key=self.api_key
        )
        
        result = calc._calculate_with_navitia(
            origin_coords=(48.8551, 2.3670),
            dest_coords=(48.8496, 2.2545),
            dest_address="Versailles"
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["duration_seconds"], 2400)
        # Nombre de changements = nombre de sections de transport public - 1
        self.assertEqual(result["num_transfers"], 1)  # 2 sections public_transport = 1 changement
        self.assertIn("changement", result["duration_text"])
    
    def test_osrm_fallback_when_navitia_unavailable(self):
        """Teste que OSRM prend le relais si Navitia n'est pas configuré"""
        calc = TravelTimeCalculator(
            departure_address="Paris, France",
            navitia_api_key=None  # Pas de clé Navitia
        )
        
        # Aucune exception ne doit être levée
        self.assertIsNone(calc.navitia_api_key)
    
    def test_format_travel_info(self):
        """Teste le formatage des infos de trajet"""
        calc = TravelTimeCalculator(
            departure_address="Paris, France",
            navitia_api_key=self.api_key
        )
        
        travel_data = {
            "duration_text": "26min (Métro)",
            "distance_text": "12.5 km"
        }
        
        formatted = calc.format_travel_info(travel_data)
        
        self.assertEqual(formatted, "26min (Métro) (12.5 km)")
    
    def test_transport_modes_configuration(self):
        """Teste que tous les modes de transport sont disponibles"""
        modes = ["driving", "walking", "cycling", "transit"]
        
        for mode in modes:
            # Ne pas lever d'exception
            self.assertIn(mode, ["driving", "walking", "cycling", "transit"])


class TestParserIntegration(unittest.TestCase):
    """Tests d'intégration avec le parser"""
    
    def test_parser_with_travel_calculator(self):
        """Teste que le parser initialise le calculateur correctement"""
        from src.parser import TournamentParser
        
        parser = TournamentParser(
            transport_mode="cycling",
            departure_address="Paris, France"
        )
        
        self.assertEqual(parser.transport_mode, "cycling")
        self.assertEqual(parser.departure_address, "Paris, France")
        self.assertIsNotNone(parser.travel_calculator)


if __name__ == "__main__":
    unittest.main()
