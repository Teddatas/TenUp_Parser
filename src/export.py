"""Export JSON des tournois (consommé par la carte et par tedata.fr)."""

from __future__ import annotations

import datetime as dt
import json

from src.classements import LADDER
from src.config import SEARCH_RADIUS_KM, TOURNOIS_JSON
from src.logger import setup_logger
from src.models import Tournament

logger = setup_logger(__name__)


def build_payload(
    tournaments: list[Tournament],
    origines: list[dict],
    radius_km: int = SEARCH_RADIUS_KM,
) -> dict:
    """``origines`` : [{"id", "label", "lat", "lng"}, …] — la 1re est le défaut."""
    cats: dict[int, str] = {}
    for t in tournaments:
        for e in t.epreuves:
            if e.id_categorie_age:
                cats[e.id_categorie_age] = e.categorie_age
    return {
        "genere_le": dt.datetime.now().isoformat(timespec="seconds"),
        "parametres": {"rayon_km": radius_km},
        "origines": origines,
        "referentiel": {
            "classements": [{"label": lbl, "echelon": ech} for lbl, ech in LADDER],
            "categories_age": [
                {"id": cid, "libelle": lib} for cid, lib in sorted(cats.items())
            ],
        },
        "tournois": [t.to_dict() for t in tournaments],
    }


def write_json(
    tournaments: list[Tournament],
    origines: list[dict],
    radius_km: int = SEARCH_RADIUS_KM,
) -> None:
    TOURNOIS_JSON.parent.mkdir(parents=True, exist_ok=True)
    TOURNOIS_JSON.write_text(
        json.dumps(
            build_payload(tournaments, origines, radius_km),
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    logger.info(
        f"JSON écrit : {TOURNOIS_JSON} "
        f"({len(tournaments)} tournois, {len(origines)} origine(s))"
    )
