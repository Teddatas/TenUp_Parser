"""
Table des classements tennis FFT <-> échelons de l'API Ten'Up.

Échelon croissant = joueur plus fort (NC = 60, -15 = 245, N* au-dessus).
"""

from __future__ import annotations

# Depuis filtres.classements de POST /back/public/v1/tournois
LABEL_TO_ECHELON = {
    "NC": 60,
    "40/2": 63, "40/1": 64, "40": 65,
    "30/5": 70, "30/4": 80, "30/3": 90, "30/2": 100, "30/1": 110, "30": 120,
    "15/5": 130, "15/4": 140, "15/3": 150, "15/2": 160, "15/1": 170, "15": 180,
    "5/6": 190, "4/6": 200, "3/6": 210, "2/6": 220, "1/6": 230,
    "0": 240, "-2/6": 243, "-4/6": 244, "-15": 245,
}
ECHELON_TO_LABEL = {v: k for k, v in LABEL_TO_ECHELON.items()}

# Ordre du plus faible au plus fort, pour un menu déroulant
LADDER = sorted(LABEL_TO_ECHELON.items(), key=lambda kv: kv[1])  # [(label, echelon), …]

# Les classements "Numéroté" (N1, N2, …) sont au-dessus de -15
_N_ECHELON = 999


def label_to_echelon(label: str | None) -> int | None:
    if not label:
        return None
    label = label.strip().upper()
    if label.startswith("N") and label[1:].isdigit():
        return _N_ECHELON
    return LABEL_TO_ECHELON.get(label)


def echelon_to_label(echelon: int | None) -> str:
    if echelon is None:
        return ""
    if echelon >= _N_ECHELON:
        return "N"
    return ECHELON_TO_LABEL.get(echelon, str(echelon))


def is_eligible(target_echelon: int, classement_min: str, classement_max: str) -> bool:
    """Le classement cible est-il dans la fourchette [min, max] d'une épreuve ?

    classement_min = joueur le plus FAIBLE accepté (échelon bas)
    classement_max = joueur le plus FORT accepté (échelon haut)
    """
    lo = label_to_echelon(classement_min)
    hi = label_to_echelon(classement_max)
    if lo is not None and target_echelon < lo:
        return False
    if hi is not None and target_echelon > hi:
        return False
    return True
