# Carte interactive des tournois par temps de trajet

`main_carte.py` — récupère **tous** les tournois proches via l'API publique Ten'Up
(à venir, dans le rayon), avec le détail de chaque épreuve, calcule les temps de
trajet **vélo + transports en commun** hors-ligne (r5py), et produit une carte
HTML autonome où l'on filtre **en direct** :

- Je suis : Homme / Femme
- Format : Simple / Double / Les deux
- Catégorie d'âge : Senior, 35 ans, 45 ans, jeunes…
- Mon classement : NC → -15
- Trajet : le plus rapide / vélo / transports
- Temps de trajet max (curseur)
- Débute dans les N jours (curseur)

Sorties : `data/output/carte_tournois.html` + `data/output/tournois.json`.
Indépendant du parser PDF historique (`main.py`).

## Installation

```bash
python -m venv .venv-carte              # Python >= 3.10
.venv-carte/bin/pip install -r requirements-carte.txt
cp .env.example .env                    # DEPARTURE_ADDRESS, rayon, fenêtre

# temps de trajet (sinon marqueurs « inconnu ») :
brew install openjdk@21                 # macOS  (apt install openjdk-21-jre-headless sous Linux)
scripts/download_r5_data.sh             # ~460 Mo : OSM Île-de-France + GTFS IDFM
```

## Utilisation

```bash
.venv-carte/bin/python main_carte.py                    # tout, params de .env
.venv-carte/bin/python main_carte.py --radius 20 --window 90
.venv-carte/bin/python main_carte.py --address "12 rue X, 75012 Paris"
.venv-carte/bin/python main_carte.py --origins origines.json   # multi-origines
.venv-carte/bin/python main_carte.py --no-travel-time   # rapide, sans r5py
```

**Multi-origines** (`--origins`) : un JSON `[{"id","label","address"}]` (ou
`lat`/`lng` au lieu de `address`). Les temps sont calculés depuis chaque origine ;
l'origine `default` (adresse `.env`) est toujours ajoutée en tête. Le JSON de
sortie porte `origines[]` et, par tournoi, `temps: {origin_id: {velo, transit}}`.
La carte affiche un sélecteur « Point de départ » quand il y a >1 origine.
Côté tedata.fr : `site/bin/refresh-tennis.sh` alimente `--origins` avec les
adresses des comptes (voir `../../tedata-infra`).

1er run : ~5 min (détail de ~650 tournois), ensuite cache (`data/cache/`, TTL 3–30 j).
Construction du réseau R5 : ~2 min au 1er run, puis ~5 s (cache).

## Comment ça marche

| Étape | Module |
|---|---|
| Recherche (rayon + dates, aucun filtre sport) | `tenup_api.search_tournaments` |
| Coordonnées GPS du club | `tenup_api.club_details` |
| Détail + toutes les épreuves (sexe, format, âge, classement, tarif) | `tenup_api.tournament_epreuves` / `tournament_detail` |
| Temps vélo + transports par club (R5, hors-ligne) | `travel_matrix.compute_travel_times` |
| JSON + carte (filtres client-side) | `export.py` / `map_builder.py` + `carte_template.html` |

Le filtrage sport/classement/âge/date est **entièrement côté client** : changer un
filtre ne relance rien. Le **calcul multi-origines** se fait au moment de la génération (option `--origins`).
(via `src/serve.py`).

## Temps de trajet (r5py)

Calcul **hors-ligne** avec le moteur R5 (Conveyal) : aucune API, aucun quota,
reproductible → adapté à un cron. Données OSM + GTFS IDFM dans `data/r5/`.

- Créneau transports : `R5_DEPARTURE_WEEKDAY` / `R5_DEPARTURE_TIME` (défaut samedi 10 h).
- Vélo : `R5_SPEED_CYCLING_KMH` (16), `R5_MAX_TRIP_MINUTES` (150), stress trafic ≤ 4.
- Rafraîchir le GTFS ~1×/trimestre (`scripts/download_r5_data.sh`).

Historique : le projet utilisait Navitia (`src/travel_calculator.py`, conservé),
abandonné car l'offre publique navitia.io ferme.

## API Ten'Up

Endpoints publics, sans authentification (`/back/public/v1/…`) :
`tournois` (POST recherche), `clubs/{code}/details`, `tournois/{homId}`,
`tournois/{homId}/epreuves`, `autocompletion/villes`. Détail dans `src/tenup_api.py`.

## Phase 2 — tedata.fr

`tournois.json` est destiné à une page `@login_required` `/espace/tennis/` de
`tedata-django`, régénérée par cron hebdo sur le Geekom. Non fait.
