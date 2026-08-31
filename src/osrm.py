"""
Temps de trajet **voiture** via OSRM (router.project-osrm.org) — gratuit, sans
clé, couvre toute l'Europe. Complète r5py (qui, lui, ne couvre que l'Île-de-France
et fait vélo + transports).

Cache disque : une seule requête par couple (origine, club) sur toute la durée
de vie du cache.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterable, Optional

import requests

from src.logger import setup_logger
from src.models import Club

logger = setup_logger(__name__)

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"


def compute_car_times(
    origins: list[tuple[str, float, float]],
    clubs: Iterable[Club],
    cache_dir: Path,
    throttle_s: float = 0.4,
) -> dict[str, dict[str, Optional[int]]]:
    """Renvoie {code_club: {origin_id: minutes_voiture|None}}."""
    clubs = [c for c in clubs if c.has_coords]
    cache_path = Path(cache_dir) / "osrm_car.json"
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}

    results: dict[str, dict[str, Optional[int]]] = {
        c.code: {oid: None for oid, _, _ in origins} for c in clubs
    }
    session = requests.Session()
    session.headers["User-Agent"] = "tedata-carte-tournois/1.0"
    calls = 0

    for oid, olat, olng in origins:
        for c in clubs:
            key = f"{olat:.5f},{olng:.5f}|{c.lat:.5f},{c.lng:.5f}"
            if key in cache:
                results[c.code][oid] = cache[key]
                continue
            url = f"{OSRM_URL}/{olng},{olat};{c.lng},{c.lat}"
            try:
                time.sleep(throttle_s)
                r = session.get(url, params={"overview": "false"}, timeout=15)
                r.raise_for_status()
                data = r.json()
                mins = None
                if data.get("code") == "Ok" and data.get("routes"):
                    mins = int(round(data["routes"][0]["duration"] / 60))
                cache[key] = mins
                results[c.code][oid] = mins
                calls += 1
            except requests.RequestException as e:
                logger.warning(f"OSRM {oid}->{c.code} : {e}")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache), encoding="utf-8")
    n_ok = sum(1 for cl in results.values() for v in cl.values() if v is not None)
    logger.info(
        f"OSRM voiture : {n_ok}/{len(results) * len(origins)} trajets "
        f"({calls} appels, reste en cache)"
    )
    return results
