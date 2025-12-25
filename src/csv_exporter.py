"""
Export des données vers CSV
"""

import csv
from pathlib import Path
from typing import List, Dict
from src.logger import setup_logger
from src.config import OUTPUT_COLUMNS

logger = setup_logger(__name__)


class CSVExporter:
    """Classe pour exporter les données vers CSV"""
    
    @staticmethod
    def export_tournaments(tournaments: List[Dict], output_path: str = None) -> bool:
        """
        Exporte une liste de tournois vers un fichier CSV
        Explose les catégories en lignes séparées
        
        Args:
            tournaments: Liste des tournois à exporter
            output_path: Chemin du fichier de sortie
        
        Returns:
            bool: True si succès, False sinon
        """
        if not output_path:
            from src.config import OUTPUT_DIR
            output_path = OUTPUT_DIR / "tournaments_export.csv"
        
        output_path = Path(output_path)
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            rows = []
            
            # Traiter chaque tournoi
            for tournament in tournaments:
                categories = tournament.pop('_categories', [])
                
                base_row = {col: tournament.get(col, "") for col in OUTPUT_COLUMNS[:-4]}  # Tous sauf catégorie/épreuve/classement/droits
                
                if categories:
                    # Créer une ligne par catégorie
                    for cat in categories:
                        row = base_row.copy()
                        row['Catégorie'] = cat.get('Catégorie', '')
                        row['Epreuve'] = cat.get('Epreuve', '')
                        row['Classement'] = cat.get('Classement', '')
                        row['Droits'] = cat.get('Droits', '')
                        rows.append(row)
                else:
                    # Tournoi sans catégories
                    row = base_row.copy()
                    row['Catégorie'] = ''
                    row['Epreuve'] = ''
                    row['Classement'] = ''
                    row['Droits'] = ''
                    rows.append(row)
            
            # Écrire le CSV
            with open(output_path, 'w', newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_COLUMNS, delimiter='\t')
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"✓ {len(rows)} ligne(s) exportée(s) vers {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export CSV : {e}")
            return False
    
    @staticmethod
    def export_by_category(tournaments: List[Dict], output_dir: str = None) -> bool:
        """
        Exporte les tournois dans des fichiers séparés par catégorie
        
        Args:
            tournaments: Liste des tournois
            output_dir: Répertoire de sortie
        
        Returns:
            bool: True si succès, False sinon
        """
        if not output_dir:
            from src.config import OUTPUT_DIR
            output_dir = OUTPUT_DIR
        
        output_dir = Path(output_dir)
        
        try:
            # Grouper par catégorie
            by_category = {}
            for tournament in tournaments:
                categories = tournament.get('_categories', [])
                if not categories:
                    categories = [{'Catégorie': 'Unknown'}]
                
                for cat in categories:
                    category = cat.get('Catégorie', 'Unknown')
                    if category not in by_category:
                        by_category[category] = []
                    
                    # Créer une copie du tournoi avec cette catégorie
                    tour_copy = tournament.copy()
                    tour_copy.pop('_categories', None)
                    tour_copy.update(cat)
                    by_category[category].append(tour_copy)
            
            # Exporter chaque catégorie
            for category, items in by_category.items():
                filename = f"tournaments_{category.replace('/', '_')}.csv"
                output_path = output_dir / filename
                
                with open(output_path, 'w', newline="", encoding="utf-8") as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=OUTPUT_COLUMNS, delimiter='\t')
                    writer.writeheader()
                    for item in items:
                        row = {col: item.get(col, "") for col in OUTPUT_COLUMNS}
                        writer.writerow(row)
                
                logger.info(f"✓ {len(items)} tournoi(s) de '{category}' exporté(s)")
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur lors de l'export par catégorie : {e}")
            return False
