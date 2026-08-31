"""
Tests unitaires pour le parser
"""

import unittest
from src.parser import TournamentParser


class TestTournamentParser(unittest.TestCase):
    """Tests pour la classe TournamentParser"""
    
    def setUp(self):
        """Préparation des tests"""
        self.parser = TournamentParser(skip_travel_time=True)
    
    def test_parser_initialization(self):
        """Test que le parser s'initialise correctement"""
        self.assertIsNotNone(self.parser)
    
    def test_validate_tournament_valid(self):
        """Test la validation d'un tournoi valide"""
        tournament = {
            "Club": "TC Test",
            "Tournoi": "Test Tournament",
            "Date début": "01/01/2026",
            "Date fin": "02/01/2026",
        }
        self.assertTrue(self.parser.validate_tournament(tournament))
    
    def test_validate_tournament_invalid(self):
        """Test la validation d'un tournoi invalide"""
        tournament = {
            "Club": "TC Test",
            "Tournoi": "Test Tournament",
        }
        self.assertFalse(self.parser.validate_tournament(tournament))


if __name__ == "__main__":
    unittest.main()
