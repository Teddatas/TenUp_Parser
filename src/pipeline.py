"""
Orchestration : API Ten'Up -> objets Tournament enrichis (toutes épreuves).

Aucun filtre sport ici : on récupère tout ce qui est dans le rayon et à venir,
avec le détail complet de chaque épreuve. Les filtres (sexe / simple-double /
catégorie d'âge / classement) sont appliqués **côté client** dans la carte.

Le calcul des temps de trajet (r5py) est branché séparément dans
``travel_matrix.py`` puis appliqué via :func:`attach_travel_times`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from src.classements import label_to_echelon
from src.config import CACHE_DIR, SEARCH_RADIUS_KM, SEARCH_WINDOW_DAYS
from src.logger import setup_logger
from src.models import Club, Epreuve, Tournament
from src.tenup_api import TenUpClient, default_window

logger = setup_logger(__name__)


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _build_club(card_club: dict, ville: str, client: TenUpClient) -> Club:
    club = Club(
        code=str(card_club.get("code", "")),
        libelle=card_club.get("libelle", ""),
        ville=ville,
    )
    details = client.club_details(club.code)
    if not details:
        return club
    installations = details.get("installations", [])
    principale = next(
        (i for i in installations if i.get("principale")),
        installations[0] if installations else None,
    )
    if principale:
        adr = principale.get("adresse", {}) or {}
        club.adresse = " ".join(
            b for b in (adr.get("adresse1"), adr.get("adresse2")) if b
        ).strip()
        club.code_postal = adr.get("codePostal", "") or ""
        club.ville = adr.get("ville", ville) or ville
        if adr.get("latitude") and adr.get("longitude"):
            club.lat = float(adr["latitude"])
            club.lng = float(adr["longitude"])
    return club


def _nature(e: dict) -> str:
    d = "D" if e.get("double") else "S"
    if e.get("mixte"):
        return d + "X"
    if e.get("dames"):
        return d + "D"
    return d + "M"


def _epreuves(hom_id: int, client: TenUpClient) -> list[Epreuve]:
    out: list[Epreuve] = []
    for e in client.tournament_epreuves(hom_id):
        cmin = (e.get("classementMin") or "").strip()
        cmax = (e.get("classementMax") or "").strip()
        out.append(
            Epreuve(
                libelle=e.get("libelle", ""),
                nature=_nature(e),
                sexe="mixte" if e.get("mixte") else ("F" if e.get("dames") else "H"),
                double=bool(e.get("double")),
                categorie_age=e.get("libelleCategorieAge", "") or "",
                id_categorie_age=e.get("idCategorieAge"),
                classement_min=cmin,
                classement_max=cmax,
                echelon_min=label_to_echelon(cmin),
                echelon_max=label_to_echelon(cmax),
                tarif_adulte=e.get("tarifAdulte"),
                date_cloture=_parse_date(e.get("dateClotureInscription")),
            )
        )
    return out


def fetch_all(
    departure: tuple[float, float],
    *,
    radius_km: int = SEARCH_RADIUS_KM,
    window_days: int = SEARCH_WINDOW_DAYS,
    enrich: bool = True,
) -> list[Tournament]:
    """Tous les tournois du rayon, à venir, avec le détail de chaque épreuve.

    ``departure`` = (lat, lng).
    """
    lat, lng = departure
    client = TenUpClient(CACHE_DIR)
    d0, d1 = default_window(window_days)

    cards = client.search_tournaments(
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        date_debut=d0,
        date_fin=d1,
        natures_epreuves=[],
        classement_echelon=None,
        size=1000,
    )

    today = date.today()
    tournaments: list[Tournament] = []
    skipped_past = skipped_nocoord = 0

    for i, card in enumerate(cards, 1):
        debut = _parse_date(card.get("dateDebut"))
        fin = _parse_date(card.get("dateFin"))
        if not debut or debut < today:
            skipped_past += 1
            continue

        hom_id = int(str(card["idHomologation"]).split("_")[-1])
        club = _build_club(card.get("club", {}), card.get("ville", ""), client)
        if not club.has_coords:
            skipped_nocoord += 1
            continue

        t = Tournament(
            id_homologation=str(card["idHomologation"]),
            hom_id=hom_id,
            libelle=card.get("libelleTournoi", ""),
            date_debut=debut,
            date_fin=fin or debut,
            natures_epreuves=list(card.get("naturesEpreuves") or []),
            club=club,
            distance_m=float(card.get("distance") or 0.0),
            inscription_en_ligne=bool(card.get("inscriptionEnLigne")),
            paiement_en_ligne=bool(card.get("paiementEnLigne")),
        )

        if enrich:
            t.epreuves = _epreuves(hom_id, client)
            detail = client.tournament_detail(hom_id) or {}
            surfaces = detail.get("codeSurfaces") or []
            t.surfaces = ", ".join(surfaces) if isinstance(surfaces, list) else str(surfaces)
            t.prix_espece = detail.get("prixEspece")
            t.prix_lots = detail.get("prixLots")
            t.mail_ja = detail.get("mailJa", "") or ""
            t.infos = (detail.get("infosComplementaire") or "").strip()
            if i % 50 == 0:
                logger.info(f"  … {i}/{len(cards)} tournois enrichis")

        tournaments.append(t)

    tournaments.sort(key=lambda x: (x.date_debut, x.distance_m))
    logger.info(
        f"{len(tournaments)} tournois retenus — écartés : "
        f"{skipped_past} déjà commencés, {skipped_nocoord} sans coordonnées"
    )
    return tournaments


def attach_travel_times(
    tournaments: list[Tournament], by_club: dict[str, dict]
) -> None:
    """Applique {code_club: {origin_id: {'velo': min, 'transit': min}}} aux tournois."""
    for t in tournaments:
        t.temps = by_club.get(t.club.code) or {}


def attach_car_times(
    tournaments: list[Tournament], by_club_car: dict[str, dict]
) -> None:
    """Fusionne {code_club: {origin_id: minutes_voiture}} dans t.temps[oid]['car']."""
    for t in tournaments:
        car = by_club_car.get(t.club.code) or {}
        for oid, mins in car.items():
            t.temps.setdefault(oid, {"velo": None, "transit": None})["car"] = mins
