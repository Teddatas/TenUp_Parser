#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TenUp Parser - Parseur de tournois de tennis
Point d'entrée de l'application
"""

import argparse
import sys
from pathlib import Path
from src.logger import setup_logger
from src.parser import TournamentParser
from src.csv_exporter import CSVExporter
from src.config import INPUT_DIR, OUTPUT_DIR

logger = setup_logger(__name__)


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description="Parse les tournois de tennis depuis un PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py                                    # Utilise data/input/tenup.pdf
  python main.py data/input/tournaments.pdf
  python main.py data/input/tournaments.pdf -o data/output/result.csv
  python main.py data/input/tournaments.pdf --by-category
        """
    )
    
    parser.add_argument(
        "pdf_file",
        nargs="?",
        default=str(INPUT_DIR / "tenup.pdf"),
        help="Chemin du fichier PDF à parser (défaut: data/input/tenup.pdf)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=str(OUTPUT_DIR / "tenup.csv"),
        help="Chemin du fichier CSV de sortie (défaut: data/output/tenup.csv)"
    )
    
    parser.add_argument(
        "--by-category",
        action="store_true",
        help="Exporter les résultats dans des fichiers séparés par catégorie"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Mode verbose (plus de détails)"
    )
    
    args = parser.parse_args()
    
    # Vérifier que le fichier existe
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        logger.error(f"❌ Fichier non trouvé : {pdf_path}")
        return False
    
    logger.info("=" * 50)
    logger.info("🎾 TenUp Parser - Démarrage")
    logger.info("=" * 50)
    
    # Parser le PDF
    tournament_parser = TournamentParser()
    tournaments = tournament_parser.parse_pdf(str(pdf_path))
    
    if not tournaments:
        logger.warning("⚠️  Aucun tournoi trouvé dans le PDF")
        return False
    
    # Exporter les résultats
    exporter = CSVExporter()
    
    if args.by_category:
        output_dir = Path(args.output).parent if args.output else OUTPUT_DIR
        success = exporter.export_by_category(tournaments, str(output_dir))
    else:
        output_file = args.output
        success = exporter.export_tournaments(tournaments, output_file)
    
    if success:
        logger.info("=" * 50)
        logger.info("✓ Parsing terminé avec succès")
        logger.info("=" * 50)
        return True
    else:
        logger.error("❌ Erreur lors de l'export")
        return False


if __name__ == "__main__":
    main()
