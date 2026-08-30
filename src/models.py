"""
Modèles de données pour la carte des tournois.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


@dataclass
class Club:
    """Un club organisateur, avec l'installation où se joue le tournoi."""

    code: str
    libelle: str
    ville: str = ""
    adresse: str = ""
    code_postal: str = ""
    lat: Optional[float] = None
    lng: Optional[float] = None

    @property
    def has_coords(self) -> bool:
        return self.lat is not None and self.lng is not None

    @property
    def adresse_complete(self) -> str:
        bits = [self.adresse, f"{self.code_postal} {self.ville}".strip()]
        return ", ".join(b for b in bits if b)


@dataclass
class Epreuve:
    """Une épreuve d'un tournoi (ex : Simple Messieurs Senior).

    Les filtres (sexe / simple-double / âge / classement) sont appliqués
    côté client à partir de ces champs.
    """

    libelle: str
    nature: str = ""              # SM, SD, DM, DD, DX
    sexe: str = ""               # H, F, mixte
    double: bool = False
    categorie_age: str = ""      # "Senior", "35 ans", "13/14 ans"…
    id_categorie_age: Optional[int] = None
    classement_min: str = ""     # libellé ("NC", "30/1")
    classement_max: str = ""
    echelon_min: Optional[int] = None   # échelon numérique (NC=60 … 30=120 …)
    echelon_max: Optional[int] = None
    tarif_adulte: Optional[float] = None
    date_cloture: Optional[date] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["date_cloture"] = self.date_cloture.isoformat() if self.date_cloture else None
        return d


@dataclass
class Tournament:
    """Un tournoi Ten'Up enrichi (coords club + temps de trajet)."""

    id_homologation: str          # ex "MOJA_285136"
    hom_id: int                   # ex 285136
    libelle: str
    date_debut: date
    date_fin: date
    natures_epreuves: list[str]   # ex ["SM", "SD"]
    club: Club
    distance_m: float             # distance à vol d'oiseau depuis le point de départ
    inscription_en_ligne: bool = False
    paiement_en_ligne: bool = False

    # Enrichissements optionnels (détail tournoi + épreuves)
    epreuves: list["Epreuve"] = field(default_factory=list)  # épreuves SM
    surfaces: str = ""
    prix_espece: Optional[float] = None
    prix_lots: Optional[float] = None
    mail_ja: str = ""
    infos: str = ""

    # Temps de trajet (minutes) depuis le point de départ
    minutes_velo: Optional[int] = None
    minutes_transit: Optional[int] = None

    @property
    def url(self) -> str:
        return f"https://tenup.fft.fr/tournoi/{self.id_homologation}"

    @property
    def minutes_best(self) -> Optional[int]:
        vals = [m for m in (self.minutes_velo, self.minutes_transit) if m is not None]
        return min(vals) if vals else None

    @property
    def tarif_min(self) -> Optional[float]:
        vals = [e.tarif_adulte for e in self.epreuves if e.tarif_adulte]
        return min(vals) if vals else None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["date_debut"] = self.date_debut.isoformat()
        d["date_fin"] = self.date_fin.isoformat()
        d["epreuves"] = [e.to_dict() for e in self.epreuves]
        d["url"] = self.url
        d["minutes_best"] = self.minutes_best
        d["tarif_min"] = self.tarif_min
        return d
