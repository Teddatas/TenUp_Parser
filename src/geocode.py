"""
Géocodage de l'adresse de départ.

Base Adresse Nationale (api-adresse.data.gouv.fr) : gratuit, sans clé,
précis à la rue pour la France. Fallback : autocomplétion ville Ten'Up.
"""

from __future__ import annotations

from typing import Optional

import requests

from src.logger import setup_logger

logger = setup_logger(__name__)

BAN_URL = "https://api-adresse.data.gouv.fr/search/"


def geocode_ban(address: str) -> Optional[tuple[float, float]]:
    try:
        r = requests.get(BAN_URL, params={"q": address, "limit": 1}, timeout=10)
        r.raise_for_status()
        feats = r.json().get("features", [])
        if feats:
            lng, lat = feats[0]["geometry"]["coordinates"]
            score = feats[0]["properties"].get("score", 0)
            logger.info(f"BAN : « {address} » -> ({lat}, {lng}) score={score:.2f}")
            return float(lat), float(lng)
    except requests.RequestException as e:
        logger.warning(f"BAN a échoué pour « {address} » : {e}")
    return None
