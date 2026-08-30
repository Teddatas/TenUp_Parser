"""
Temps de trajet vélo + transports en commun, calculés **hors-ligne** avec r5py
(moteur R5 de Conveyal) à partir d'un extrait OSM + du GTFS Île-de-France Mobilités.

Aucune API, aucun quota : adapté à un job cron qui régénère la carte.

Données attendues (voir scripts/download_r5_data.sh) :
  data/r5/ile-de-france-latest.osm.pbf
  data/r5/IDFM-gtfs.zip

Si r5py ou les données manquent, :func:`compute_travel_times` renvoie {} et la
carte se rabat sur la distance à vol d'oiseau.
"""

from __future__ import annotations

import datetime as dt
import glob
import os
import shutil
from typing import Iterable, Optional

from src.config import (
    R5_DEPARTURE_TIME,
    R5_DEPARTURE_WEEKDAY,
    R5_GTFS_ZIP,
    R5_MAX_TRIP_MINUTES,
    R5_OSM_PBF,
    R5_SPEED_CYCLING_KMH,
    R5_SPEED_WALKING_KMH,
)
from src.logger import setup_logger
from src.models import Club

logger = setup_logger(__name__)

HOME_ID = "__home__"


def _ensure_java_home() -> None:
    """r5py a besoin d'un JDK 21. Renseigne JAVA_HOME si absent."""
    if os.environ.get("JAVA_HOME") and os.path.isdir(os.environ["JAVA_HOME"]):
        return
    candidates = [
        "/opt/homebrew/opt/openjdk@21",
        "/opt/homebrew/opt/openjdk",
        "/usr/lib/jvm/java-21-openjdk-amd64",
        "/usr/lib/jvm/java-21-openjdk",
    ]
    candidates += sorted(glob.glob("/usr/lib/jvm/*21*"), reverse=True)
    for c in candidates:
        if os.path.isdir(c):
            os.environ["JAVA_HOME"] = c
            logger.info(f"JAVA_HOME = {c}")
            return
    if not shutil.which("java"):
        logger.warning("Aucun JDK trouvé — installer openjdk 21 (voir docs/CARTE_TOURNOIS.md)")


def _next_weekday_at(weekday: int, hhmm: str) -> dt.datetime:
    """Prochaine date à `weekday` (0=lundi) et heure `HH:MM`, au moins J+1."""
    hh, mm = (int(x) for x in hhmm.split(":"))
    today = dt.date.today()
    ahead = (weekday - today.weekday()) % 7
    if ahead == 0:
        ahead = 7
    d = today + dt.timedelta(days=ahead)
    return dt.datetime(d.year, d.month, d.day, hh, mm)


def _points_gdf(rows: list[tuple[str, float, float]]):
    import geopandas as gpd
    from shapely.geometry import Point

    return gpd.GeoDataFrame(
        {"id": [r[0] for r in rows]},
        geometry=[Point(r[2], r[1]) for r in rows],  # Point(lng, lat)
        crs="EPSG:4326",
    )


def _matrix_computer(network, origins, destinations, modes, departure, **extra):
    """Compat entre versions de r5py (TravelTimeMatrixComputer / TravelTimeMatrix)."""
    import r5py

    kwargs = dict(
        origins=origins,
        destinations=destinations,
        departure=departure,
        transport_modes=modes,
        max_time=dt.timedelta(minutes=R5_MAX_TRIP_MINUTES),
        speed_cycling=R5_SPEED_CYCLING_KMH,
        speed_walking=R5_SPEED_WALKING_KMH,
        **extra,
    )
    if hasattr(r5py, "TravelTimeMatrixComputer"):  # r5py < 1.0
        return r5py.TravelTimeMatrixComputer(network, **kwargs).compute_travel_times()
    return r5py.TravelTimeMatrix(network, snap_to_network=True, **kwargs)


def compute_travel_times(
    home: tuple[float, float],
    clubs: Iterable[Club],
    *,
    departure: Optional[dt.datetime] = None,
) -> dict[str, dict[str, Optional[int]]]:
    """Renvoie {code_club: {'velo': minutes|None, 'transit': minutes|None}}."""
    clubs = [c for c in clubs if c.has_coords]
    if not clubs:
        return {}

    import importlib.util

    if any(importlib.util.find_spec(m) is None for m in ("r5py", "geopandas")):
        logger.warning(
            "r5py / geopandas non installés — temps de trajet ignorés "
            "(pip install -r requirements-carte.txt)"
        )
        return {}

    _ensure_java_home()

    if not R5_OSM_PBF.exists() or not R5_GTFS_ZIP.exists():
        logger.warning(
            f"Données r5 manquantes ({R5_OSM_PBF.name} / {R5_GTFS_ZIP.name}) — "
            "lancer scripts/download_r5_data.sh. Temps de trajet ignorés."
        )
        return {}

    import r5py

    departure = departure or _next_weekday_at(R5_DEPARTURE_WEEKDAY, R5_DEPARTURE_TIME)
    logger.info(
        f"r5py : construction du réseau ({R5_OSM_PBF.name} + {R5_GTFS_ZIP.name})…"
    )
    network = r5py.TransportNetwork(str(R5_OSM_PBF), [str(R5_GTFS_ZIP)])

    origin = _points_gdf([(HOME_ID, home[0], home[1])])
    dests = _points_gdf([(c.code, c.lat, c.lng) for c in clubs])

    results: dict[str, dict[str, Optional[int]]] = {
        c.code: {"velo": None, "transit": None} for c in clubs
    }

    modes_by_key = {
        "velo": [r5py.TransportMode.BICYCLE],
        "transit": [r5py.TransportMode.TRANSIT, r5py.TransportMode.WALK],
    }
    for key, modes in modes_by_key.items():
        logger.info(f"r5py : calcul {key}…")
        try:
            extra = {"max_bicycle_traffic_stress": 4} if key == "velo" else {}
            matrix = _matrix_computer(network, origin, dests, modes, departure, **extra)
        except Exception as e:  # pragma: no cover - dépend de l'env r5py
            logger.error(f"r5py {key} a échoué : {e}")
            continue
        for _, row in matrix.iterrows():
            code = row["to_id"]
            tt = row["travel_time"]
            if code in results and tt is not None and tt == tt:  # not NaN
                results[code][key] = int(round(float(tt)))

    n_velo = sum(1 for v in results.values() if v["velo"] is not None)
    n_tr = sum(1 for v in results.values() if v["transit"] is not None)
    logger.info(
        f"r5py : {n_velo}/{len(results)} clubs joignables à vélo, "
        f"{n_tr}/{len(results)} en transports (créneau {departure:%a %d/%m %H:%M})"
    )
    return results
