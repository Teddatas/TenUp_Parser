"""
Configuration du projet TenUp Parser
"""

import os
from pathlib import Path

# Chemins
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
DOCS_DIR = PROJECT_ROOT / "docs"

# Créer les répertoires s'ils n'existent pas
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Colonnes attendues en sortie
OUTPUT_COLUMNS = [
    "Club",
    "Tournoi",
    "Date début",
    "Date fin",
    "JUGE-ARBITRE",
    "SURFACE(S)",
    "PRIX EN ESPÈCE",
    "PRIX EN LOTS",
    "INSCRIPTIONS",
    "PAIEMENT EN LIGNE",
    "CODE",
    "ENGAGEMENTS",
    "INSTALLATIONS",
    "Téléphone",
    "Catégorie",
    "Epreuve",
    "Classement",
    "Droits",
]

# Formats acceptés
ACCEPTED_FORMATS = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
}

# Configuration du logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
