#!/usr/bin/env python3
"""
Carte interactive des tournois de tennis proches, colorée par temps de trajet.

Le pipeline récupère *tous* les tournois du rayon (à venir) avec le détail de
chaque épreuve, calcule les temps de trajet hors-ligne (r5py), et produit une
carte HTML autonome où l'on filtre en direct : sexe, simple/double, catégorie
d'âge, classement, mode de transport, temps max, date.

    python main_carte.py                      # valeurs de .env / config.py
    python main_carte.py --radius 20 --window 90
    python main_carte.py --address "12 rue X, 75012 Paris"
    python main_carte.py --no-travel-time     # rapide, sans r5py
    python -m src.serve                       # sert la carte + changement d'adresse
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()

from src.config import (  # noqa: E402
    CACHE_DIR,
    DEPARTURE_ADDRESS,
    DEPARTURE_LAT,
    DEPARTURE_LNG,
    SEARCH_RADIUS_KM,
    SEARCH_WINDOW_DAYS,
)
from src.export import write_json  # noqa: E402
from src.logger import setup_logger  # noqa: E402
from src.map_builder import write_map  # noqa: E402
from src.pipeline import attach_travel_times, fetch_all  # noqa: E402

logger = setup_logger("main_carte")


def resolve_home(address: str | None = None) -> tuple[float, float]:
    address = address or DEPARTURE_ADDRESS
    if not address and DEPARTURE_LAT is not None and DEPARTURE_LNG is not None:
        return DEPARTURE_LAT, DEPARTURE_LNG

    from src.geocode import geocode_ban
    from src.tenup_api import TenUpClient

    coords = geocode_ban(address) or TenUpClient(CACHE_DIR).geocode_city(address)
    if not coords:
        logger.error(
            f"Impossible de géocoder « {address} ». "
            "Renseigner DEPARTURE_LAT / DEPARTURE_LNG dans .env."
        )
        sys.exit(1)
    return coords


def generate(
    *,
    address: str | None = None,
    radius_km: int = SEARCH_RADIUS_KM,
    window_days: int = SEARCH_WINDOW_DAYS,
    travel_times: bool = True,
    enrich: bool = True,
) -> int:
    """Exécute le pipeline complet. Renvoie le nombre de tournois."""
    home = resolve_home(address)
    logger.info(f"Départ {home} · rayon {radius_km} km · fenêtre {window_days} j")

    tournaments = fetch_all(
        home, radius_km=radius_km, window_days=window_days, enrich=enrich
    )
    if not tournaments:
        logger.warning("Aucun tournoi.")
        return 0

    if travel_times:
        from src.travel_matrix import compute_travel_times

        clubs = list({t.club.code: t.club for t in tournaments}.values())
        attach_travel_times(tournaments, compute_travel_times(home, clubs))

    write_json(tournaments, home)
    write_map(tournaments, home)
    return len(tournaments)


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--address", default=None, help="adresse de départ (sinon .env)")
    p.add_argument("--radius", type=int, default=SEARCH_RADIUS_KM, help="rayon km")
    p.add_argument("--window", type=int, default=SEARCH_WINDOW_DAYS, help="fenêtre jours")
    p.add_argument("--no-enrich", action="store_true", help="sans détail par épreuve")
    p.add_argument("--no-travel-time", action="store_true", help="sans calcul r5py")
    args = p.parse_args()

    n = generate(
        address=args.address,
        radius_km=args.radius,
        window_days=args.window,
        travel_times=not args.no_travel_time,
        enrich=not args.no_enrich,
    )
    logger.info(f"Terminé — {n} tournois.")


if __name__ == "__main__":
    main()
