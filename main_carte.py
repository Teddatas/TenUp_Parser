#!/usr/bin/env python3
"""
Carte interactive des tournois de tennis proches, colorée par temps de trajet.

Récupère tous les tournois du rayon (à venir) avec le détail de chaque épreuve,
calcule les temps de trajet hors-ligne (r5py) depuis une ou plusieurs origines,
et produit une carte HTML autonome (filtres client-side : sexe, simple/double,
catégorie d'âge, classement, mode, temps max, date, origine).

    python main_carte.py                       # origine unique depuis .env
    python main_carte.py --address "12 rue X, 75012 Paris"
    python main_carte.py --origins origines.json   # multi-origines (défaut + amis)
    python main_carte.py --no-travel-time      # rapide, sans r5py

Format --origins : [{"id": "u-jean", "label": "Jean",
                     "lat": 48.85, "lng": 2.34}]   (ou "address" au lieu de lat/lng)
L'origine « default » (adresse de .env) est toujours ajoutée en tête.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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
from src.pipeline import attach_car_times, attach_travel_times, fetch_all  # noqa: E402

logger = setup_logger("main_carte")

DEFAULT_ID = "default"


def _geocode(address: str):
    from src.geocode import geocode_ban
    from src.tenup_api import TenUpClient

    return geocode_ban(address) or TenUpClient(CACHE_DIR).geocode_city(address)


def resolve_home(address: str | None = None) -> tuple[float, float]:
    address = address or DEPARTURE_ADDRESS
    if not address and DEPARTURE_LAT is not None and DEPARTURE_LNG is not None:
        return DEPARTURE_LAT, DEPARTURE_LNG
    coords = _geocode(address)
    if not coords:
        logger.error(
            f"Impossible de géocoder « {address} ». "
            "Renseigner DEPARTURE_LAT / DEPARTURE_LNG dans .env."
        )
        sys.exit(1)
    return coords


def _load_extra_origins(path: str | None) -> list[dict]:
    if not path:
        return []
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    out: list[dict] = []
    for item in raw:
        oid = str(item.get("id") or "").strip()
        if not oid or oid == DEFAULT_ID:
            continue
        lat, lng = item.get("lat"), item.get("lng")
        if lat is None or lng is None:
            coords = _geocode(item.get("address", ""))
            if not coords:
                logger.warning(f"Origine « {oid} » : adresse non géocodée, ignorée")
                continue
            lat, lng = coords
        out.append(
            {"id": oid, "label": item.get("label") or oid,
             "lat": float(lat), "lng": float(lng)}
        )
    return out


def generate(
    *,
    address: str | None = None,
    origins_file: str | None = None,
    radius_km: int = SEARCH_RADIUS_KM,
    window_days: int = SEARCH_WINDOW_DAYS,
    travel_times: bool = True,
    enrich: bool = True,
) -> int:
    home = resolve_home(address)
    origines = [
        {"id": DEFAULT_ID, "label": address or DEPARTURE_ADDRESS,
         "lat": home[0], "lng": home[1]}
    ] + _load_extra_origins(origins_file)
    logger.info(
        f"Départ {home} · rayon {radius_km} km · fenêtre {window_days} j · "
        f"{len(origines)} origine(s)"
    )

    tournaments = fetch_all(
        home, radius_km=radius_km, window_days=window_days, enrich=enrich
    )
    if not tournaments:
        logger.warning("Aucun tournoi.")
        return 0

    if travel_times:
        from src.osrm import compute_car_times
        from src.travel_matrix import compute_travel_times

        clubs = list({t.club.code: t.club for t in tournaments}.values())
        origin_tuples = [(o["id"], o["lat"], o["lng"]) for o in origines]
        attach_travel_times(tournaments, compute_travel_times(origin_tuples, clubs))
        attach_car_times(
            tournaments, compute_car_times(origin_tuples, clubs, CACHE_DIR)
        )

    write_json(tournaments, origines, radius_km)
    write_map(tournaments, origines, radius_km)
    return len(tournaments)


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--address", default=None, help="adresse de départ (sinon .env)")
    p.add_argument("--origins", default=None, help="fichier JSON d'origines supplémentaires")
    p.add_argument("--radius", type=int, default=SEARCH_RADIUS_KM, help="rayon km")
    p.add_argument("--window", type=int, default=SEARCH_WINDOW_DAYS, help="fenêtre jours")
    p.add_argument("--no-enrich", action="store_true", help="sans détail par épreuve")
    p.add_argument("--no-travel-time", action="store_true", help="sans calcul r5py")
    args = p.parse_args()

    n = generate(
        address=args.address,
        origins_file=args.origins,
        radius_km=args.radius,
        window_days=args.window,
        travel_times=not args.no_travel_time,
        enrich=not args.no_enrich,
    )
    logger.info(f"Terminé — {n} tournois.")


if __name__ == "__main__":
    main()
