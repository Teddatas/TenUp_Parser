"""
Client de l'API publique de Ten'Up (tenup.fft.fr).

Endpoints publics, sans authentification, sans blocage anti-bot
(contrairement à /back/v1/* qui est réservé aux comptes connectés) :

  POST /back/public/v1/tournois                  -> recherche + filtres
  GET  /back/public/v1/clubs/{code}/details      -> installations + coords GPS
  GET  /back/public/v1/tournois/{homId}          -> détail (épreuves, tarif, surface…)
  GET  /back/public/v1/autocompletion/villes     -> géocodage ville / code postal

Un cache disque (JSON) évite de retaper les endpoints club/détail à chaque run.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import requests

from src.logger import setup_logger

logger = setup_logger(__name__)

BASE_URL = "https://tenup.fft.fr"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


class TenUpClient:
    def __init__(self, cache_dir: Path, throttle_s: float = 0.3):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.throttle_s = throttle_s
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": USER_AGENT, "Accept": "application/json"}
        )

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------
    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def _cache_get(self, key: str, max_age_days: Optional[int]) -> Optional[Any]:
        path = self._cache_path(key)
        if not path.exists():
            return None
        if max_age_days is not None:
            age = time.time() - path.stat().st_mtime
            if age > max_age_days * 86400:
                return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _cache_put(self, key: str, value: Any) -> None:
        self._cache_path(key).write_text(
            json.dumps(value, ensure_ascii=False), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------
    def _get(self, path: str, **kwargs) -> requests.Response:
        time.sleep(self.throttle_s)
        r = self.session.get(f"{BASE_URL}{path}", timeout=20, **kwargs)
        r.raise_for_status()
        return r

    def _post(self, path: str, payload: dict) -> requests.Response:
        time.sleep(self.throttle_s)
        r = self.session.post(
            f"{BASE_URL}{path}",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        r.raise_for_status()
        return r

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------
    def geocode_city(self, query: str) -> Optional[tuple[float, float]]:
        """Résout une ville / code postal en (lat, lng) via l'autocomplétion Ten'Up."""
        try:
            data = self._get(
                "/back/public/v1/autocompletion/villes", params={"recherche": query}
            ).json()
        except requests.RequestException as e:
            logger.warning(f"Autocomplétion ville a échoué pour '{query}': {e}")
            return None
        for item in data or []:
            lat = item.get("latitude") or item.get("lat")
            lng = item.get("longitude") or item.get("lng")
            if lat and lng:
                return float(lat), float(lng)
        return None

    def search_tournaments(
        self,
        lat: float,
        lng: float,
        radius_km: int,
        date_debut: datetime,
        date_fin: datetime,
        natures_epreuves: list[str],
        classement_echelon: Optional[int] = None,
        size: int = 500,
    ) -> list[dict]:
        """POST /back/public/v1/tournois — renvoie la liste brute des `cards`."""
        payload = {
            "pratique": "TENNIS",
            "from": 0,
            "size": size,
            "lat": lat,
            "lng": lng,
            "distance": radius_km,
            "type": [],
            "codeClub": None,
            "ligues": [],
            "comites": [],
            "dateDebut": _iso_z(date_debut),
            "dateFin": _iso_z(date_fin),
            "utiliserMesDonnees": False,
            "naturesEpreuves": natures_epreuves,
            "typesEpreuves": [],
            "naturesTerrains": [],
            "categoriesJeu": [],
            "categoriesAge": [],
            "familles": [],
            "tournoiInterne": False,
            "classements": [classement_echelon] if classement_echelon else [],
            "inscriptionEnLigne": None,
            "paiementEnLigne": None,
            "filtres": False,
            "sort": "DISTANCE",
        }
        data = self._post("/back/public/v1/tournois", payload).json()
        cards = data.get("cards", [])
        logger.info(
            f"Ten'Up : {data.get('nbResultats')} résultats, {len(cards)} cartes reçues"
        )
        return cards

    def club_details(self, code: str, max_age_days: int = 30) -> Optional[dict]:
        """GET /back/public/v1/clubs/{code}/details (avec cache)."""
        key = f"club_{code}"
        cached = self._cache_get(key, max_age_days)
        if cached is not None:
            return cached
        try:
            data = self._get(f"/back/public/v1/clubs/{code}/details").json()
        except requests.RequestException as e:
            logger.warning(f"clubs/{code}/details a échoué : {e}")
            return None
        self._cache_put(key, data)
        return data

    def tournament_detail(self, hom_id: int, max_age_days: int = 7) -> Optional[dict]:
        """GET /back/public/v1/tournois/{homId} (avec cache)."""
        key = f"tournoi_{hom_id}"
        cached = self._cache_get(key, max_age_days)
        if cached is not None:
            return cached
        try:
            data = self._get(f"/back/public/v1/tournois/{hom_id}").json()
        except requests.RequestException as e:
            logger.warning(f"tournois/{hom_id} a échoué : {e}")
            return None
        self._cache_put(key, data)
        return data

    def tournament_epreuves(self, hom_id: int, max_age_days: int = 3) -> list[dict]:
        """GET /back/public/v1/tournois/{homId}/epreuves (avec cache).

        Riche : tarifAdulte, classementMin/Max, dates de clôture, quotas…
        """
        key = f"epreuves_{hom_id}"
        cached = self._cache_get(key, max_age_days)
        if cached is not None:
            return cached
        try:
            data = self._get(f"/back/public/v1/tournois/{hom_id}/epreuves").json()
        except requests.RequestException as e:
            logger.warning(f"tournois/{hom_id}/epreuves a échoué : {e}")
            return []
        self._cache_put(key, data)
        return data


def _iso_z(dt: datetime) -> str:
    """datetime -> 'YYYY-MM-DDTHH:MM:SS.000Z' (format attendu par l'API)."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def default_window(days: int) -> tuple[datetime, datetime]:
    """Fenêtre (maintenant, maintenant + days)."""
    now = datetime.now(timezone.utc)
    return now, now + timedelta(days=days)
