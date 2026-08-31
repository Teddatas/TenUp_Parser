"""
Configuration du projet TenUp Parser
"""

import os
from pathlib import Path


def _env_float(name: str):
    """Lit une variable d'environnement en float, ou None si absente/vide."""
    raw = os.getenv(name, "").strip()
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


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
    "Temps de trajet",  # Nouvelle colonne
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


# ======================================================================
# CARTE DES TOURNOIS  (branche feat/carte-tournois)
# Pipeline : API publique Ten'Up -> filtres -> temps de trajet (r5py) -> carte
# ======================================================================

CACHE_DIR = DATA_DIR / "cache"
R5_DATA_DIR = DATA_DIR / "r5"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
R5_DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Point de départ ---------------------------------------------------
# Adresse affichée + coordonnées. Si les coords sont None, elles sont
# résolues via l'autocomplétion Ten'Up / Nominatim au 1er run et mises en cache.
DEPARTURE_ADDRESS = os.getenv("DEPARTURE_ADDRESS", "Paris, France")
DEPARTURE_LAT = _env_float("DEPARTURE_LAT")
DEPARTURE_LNG = _env_float("DEPARTURE_LNG")

# --- Étendue de la recherche Ten'Up --------------------------------------
# On récupère TOUS les tournois du rayon (à venir) ; sexe / simple-double /
# catégorie d'âge / classement sont filtrés en direct dans la carte.
SEARCH_RADIUS_KM = int(os.getenv("SEARCH_RADIUS_KM", "30"))
# Rayon élargi pour les zones hors Île-de-France (villes moins denses en tournois).
SEARCH_RADIUS_KM_WIDE = int(os.getenv("SEARCH_RADIUS_KM_WIDE", "60"))
SEARCH_WINDOW_DAYS = int(os.getenv("SEARCH_WINDOW_DAYS", "120"))

# Bbox large de l'Île-de-France (+ marge). Sert à deux choses : borner r5py
# (réseau IDF only) et choisir le rayon de recherche (IDF = 30 km, ailleurs = 60).
IDF_BBOX = (48.00, 49.35, 1.30, 3.75)  # lat_min, lat_max, lng_min, lng_max


def in_idf(lat: float, lng: float) -> bool:
    return IDF_BBOX[0] <= lat <= IDF_BBOX[1] and IDF_BBOX[2] <= lng <= IDF_BBOX[3]


def radius_for(lat: float, lng: float, base: int = SEARCH_RADIUS_KM) -> int:
    """Rayon de recherche pour un point : ``base`` en IDF, élargi ailleurs."""
    return base if in_idf(lat, lng) else max(base, SEARCH_RADIUS_KM_WIDE)

# --- r5py / temps de trajet ------------------------------------------------
# Fichiers de données (voir scripts/download_r5_data.sh)
R5_OSM_PBF = R5_DATA_DIR / os.getenv("R5_OSM_PBF", "ile-de-france-latest.osm.pbf")
R5_GTFS_ZIP = R5_DATA_DIR / os.getenv("R5_GTFS_ZIP", "IDFM-gtfs.zip")
# Créneau représentatif pour le calcul transports en commun (prochain samedi 10h
# par défaut : cas d'usage tournois amateurs = week-ends + soirs).
R5_DEPARTURE_WEEKDAY = int(os.getenv("R5_DEPARTURE_WEEKDAY", "5"))  # 0=lundi … 5=samedi
R5_DEPARTURE_TIME = os.getenv("R5_DEPARTURE_TIME", "10:00")
R5_MAX_TRIP_MINUTES = int(os.getenv("R5_MAX_TRIP_MINUTES", "150"))
R5_SPEED_CYCLING_KMH = float(os.getenv("R5_SPEED_CYCLING_KMH", "16"))
R5_SPEED_WALKING_KMH = float(os.getenv("R5_SPEED_WALKING_KMH", "4.8"))

# --- Carte ---------------------------------------------------------------
# Bornes (minutes) des tranches de couleur : <=15 vert, <=30 …, >60 rouge foncé
TRAVEL_TIME_BUCKETS = [15, 30, 45, 60]
CARTE_HTML = OUTPUT_DIR / "carte_tournois.html"
TOURNOIS_JSON = OUTPUT_DIR / "tournois.json"
