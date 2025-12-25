"""
Parser principal pour extraire les tournois de tennis depuis PDF
Utilise l'extraction de tableaux pour une meilleure précision
"""

from typing import List, Dict, Optional, Tuple
import re
import pdfplumber
from src.logger import setup_logger

logger = setup_logger(__name__)


class TournamentParser:
    """Parse les données de tournois de tennis depuis PDF (tableaux)"""
    
    def __init__(self):
        """Initialise le parser"""
        pass
    
    def _clean_text(self, text: str) -> str:
        """
        Nettoie le texte en supprimant les sauts de ligne et espaces superflus
        
        Args:
            text: Texte à nettoyer
        
        Returns:
            str: Texte nettoyé
        """
        if not text:
            return ""
        # Remplacer les sauts de ligne par des espaces
        text = text.replace('\n', ' ')
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def parse_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Parse un fichier PDF pour extraire les tournois depuis les tableaux
        
        Args:
            pdf_path: Chemin vers le fichier PDF
        
        Returns:
            List[Dict]: Liste des tournois trouvés
        """
        logger.info(f"🎾 Ouverture du PDF : {pdf_path}")
        
        tournaments = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"📄 {len(pdf.pages)} pages à traiter")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    logger.debug(f"📄 Page {page_num}/{len(pdf.pages)}")
                    
                    # Extraire les tableaux de la page
                    tables = page.extract_tables()
                    if not tables:
                        continue
                    
                    # Parser chaque tableau comme un tournoi
                    for table in tables:
                        tournament = self._parse_table(table)
                        if tournament and self.validate_tournament(tournament):
                            tournaments.append(tournament)
                
                logger.info(f"✓ {len(tournaments)} tournoi(s) extrait(s)")
        
        except Exception as e:
            logger.error(f"Erreur lors du parsing : {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return tournaments
    
    def _parse_table(self, table: List[List]) -> Optional[Dict]:
        """
        Parse un tableau pour extraire un tournoi
        
        Args:
            table: Tableau au format pdfplumber
        
        Returns:
            Dict: Données du tournoi ou None
        """
        if not table or len(table) < 1:
            return None
        
        # La première ligne contient les infos du tournoi
        first_row = table[0]
        if len(first_row) < 2:
            return None
        
        tournament = {}
        
        # Colonne 0 : Infos principales
        col0 = first_row[0] if first_row[0] else ""
        # Colonne 1 : Email et installations
        col1 = first_row[1] if len(first_row) > 1 and first_row[1] else ""
        
        # Parser la colonne 0
        self._parse_col0(col0, tournament)
        # Parser la colonne 1
        self._parse_col1(col1, tournament)
        
        # Parser les catégories (à partir de la 2ème ligne)
        categories = []
        for row_idx in range(1, len(table)):
            row = table[row_idx]
            if len(row) >= 6:
                # Les colonnes 2-5 contiennent Catégorie, Epreuve, Classement, Droits
                cat = {
                    'Catégorie': self._clean_text(row[2] or ""),
                    'Epreuve': self._clean_text(row[3] or ""),
                    'Classement': self._clean_text(row[4] or ""),
                    'Droits': self._clean_text(row[5] or ""),
                }
                if cat['Catégorie'] and cat['Epreuve']:
                    categories.append(cat)
        
        tournament['_categories'] = categories
        
        return tournament
    
    def _parse_col0(self, text: str, tournament: Dict) -> None:
        """Parse la première colonne (infos principales)"""
        if not text:
            return
        
        lines = text.strip().split('\n')
        
        # Club (première ligne)
        if lines:
            tournament['Club'] = self._clean_text(lines[0])
        
        # Tournoi (deuxième ligne)
        if len(lines) > 1:
            tournament['Tournoi'] = self._clean_text(lines[1])
        
        # Dates
        full_text = '\n'.join(lines)
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+au\s+(\d{2}/\d{2}/\d{4})', full_text)
        if date_match:
            tournament['Date début'] = date_match.group(1)
            tournament['Date fin'] = date_match.group(2)
        
        # Juge-arbitre
        ja = re.search(r'JUGE-ARBITRE\s*:\s*([^\n]+)', full_text)
        if ja:
            tournament['JUGE-ARBITRE'] = self._clean_text(ja.group(1))
        
        # Surface
        surf = re.search(r'SURFACE\(S\)\s*:\s*([^\n]+)', full_text)
        if surf:
            tournament['SURFACE(S)'] = self._clean_text(surf.group(1))
        
        # Prix en espèce
        prix_e = re.search(r'PRIX EN ESPÈCE\s*:\s*([^\n]+)', full_text)
        if prix_e:
            tournament['PRIX EN ESPÈCE'] = self._clean_text(prix_e.group(1))
        
        # Prix en lots
        prix_l = re.search(r'PRIX EN LOTS\s*:\s*([^\n]+)', full_text)
        if prix_l:
            tournament['PRIX EN LOTS'] = self._clean_text(prix_l.group(1))
        
        # Inscriptions / Paiement
        inscr = re.search(r'INSCRIPTIONS / PAIEMENT EN LIGNE\s*:\s*(\w+)\s*/\s*(\w+)', full_text)
        if inscr:
            tournament['INSCRIPTIONS'] = self._clean_text(inscr.group(1))
            tournament['PAIEMENT EN LIGNE'] = self._clean_text(inscr.group(2))
        
        # Code
        code = re.search(r'CODE\s*:\s*([^\n]+)', full_text)
        if code:
            tournament['CODE'] = self._clean_text(code.group(1))
    
    def _parse_col1(self, text: str, tournament: Dict) -> None:
        """Parse la deuxième colonne (email et installations)"""
        if not text:
            return
        
        lines = text.strip().split('\n')
        full_text = '\n'.join(lines)
        
        # Email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', full_text)
        if email_match:
            tournament['ENGAGEMENTS'] = self._clean_text(email_match.group(1))
        
        # Installations (tout après "INSTALLATIONS :")
        inst_match = re.search(r'INSTALLATIONS\s*:\s*(.*?)(?=$|Page)', full_text, re.DOTALL)
        if inst_match:
            inst_text = inst_match.group(1).strip()
            # Nettoyer et formatter l'adresse
            inst_lines = [line.strip() for line in inst_text.split('\n') if line.strip()]
            # Aussi nettoyer les sauts de lignes dans chaque ligne
            inst_lines = [self._clean_text(line) for line in inst_lines]
            tournament['INSTALLATIONS'] = ' & '.join(inst_lines) if inst_lines else ""
        
        # Téléphone
        phone_match = re.search(r'(\d{2}\s+\d{2}\s+\d{2}\s+\d{2}\s+\d{2}|\d{2}\s+\d{2})', full_text)
        if phone_match:
            tournament['Téléphone'] = self._clean_text(phone_match.group(1))
    
    def validate_tournament(self, tournament: Dict) -> bool:
        """
        Valide si un tournoi contient les données essentielles
        
        Args:
            tournament: Dictionnaire du tournoi
        
        Returns:
            bool: True si valide, False sinon
        """
        required_fields = ["Club", "Date début", "Date fin"]
        return all(field in tournament and tournament.get(field) for field in required_fields)
