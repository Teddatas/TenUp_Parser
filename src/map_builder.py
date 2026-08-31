"""
Génère la carte interactive : un template HTML autonome (Leaflet + panneau de
filtres) dans lequel on injecte les tournois en JSON. Tout le filtrage
(sexe / simple-double / catégorie d'âge / classement / mode / temps / date) est
fait côté client — pas besoin de relancer le pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.config import CARTE_HTML, SEARCH_RADIUS_KM
from src.export import build_payload
from src.logger import setup_logger
from src.models import Tournament

logger = setup_logger(__name__)

_TEMPLATE = Path(__file__).parent / "carte_template.html"
_PLACEHOLDER = "/*__DATA__*/"


def render_html(
    tournaments: list[Tournament],
    origines: list[dict],
    radius_km: int = SEARCH_RADIUS_KM,
) -> str:
    payload = build_payload(tournaments, origines, radius_km)
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # Neutralise une éventuelle fermeture de balise script dans les données
    data_json = data_json.replace("</", "<\\/")
    template = _TEMPLATE.read_text(encoding="utf-8")
    return template.replace(_PLACEHOLDER, data_json)


def write_map(
    tournaments: list[Tournament],
    origines: list[dict],
    radius_km: int = SEARCH_RADIUS_KM,
) -> None:
    CARTE_HTML.parent.mkdir(parents=True, exist_ok=True)
    CARTE_HTML.write_text(
        render_html(tournaments, origines, radius_km), encoding="utf-8"
    )
    size_kb = CARTE_HTML.stat().st_size / 1024
    logger.info(f"Carte écrite : {CARTE_HTML} ({size_kb:.0f} Ko)")
