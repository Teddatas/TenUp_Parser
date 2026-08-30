#!/usr/bin/env bash
# Télécharge les données pour le calcul des temps de trajet hors-ligne (r5py) :
#   - extrait OpenStreetMap Île-de-France (Geofabrik)
#   - GTFS Île-de-France Mobilités (transport.data.gouv.fr / opendatasoft)
#
# À relancer ~1x/trimestre pour rafraîchir le GTFS (horaires qui changent).
# Total ~460 Mo.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${SCRIPT_DIR}/../data/r5"
mkdir -p "$DATA_DIR"

OSM_URL="https://download.geofabrik.de/europe/france/ile-de-france-latest.osm.pbf"
OSM_URL_FALLBACK="https://download.openstreetmap.fr/extracts/europe/france/ile_de_france.osm.pbf"
GTFS_URL="https://eu.ftp.opendatasoft.com/stif/GTFS/IDFM-gtfs.zip"

CURL=(curl -fL --progress-bar --retry 5 --retry-delay 10 --retry-all-errors)

echo "→ OSM Île-de-France  ($OSM_URL)"
"${CURL[@]}" -o "${DATA_DIR}/ile-de-france-latest.osm.pbf" "$OSM_URL" || {
    echo "  Geofabrik indisponible, bascule sur download.openstreetmap.fr"
    "${CURL[@]}" -o "${DATA_DIR}/ile-de-france-latest.osm.pbf" "$OSM_URL_FALLBACK"
}

echo "→ GTFS IDFM          ($GTFS_URL)"
"${CURL[@]}" -o "${DATA_DIR}/IDFM-gtfs.zip" "$GTFS_URL"

# r5py reconstruit son graphe si le .pbf change : on invalide le cache réseau
rm -f "${DATA_DIR}"/*.mapdb "${DATA_DIR}"/*.mapdb.p "${DATA_DIR}"/network.dat 2>/dev/null || true

echo "✓ Données prêtes dans ${DATA_DIR}"
ls -lh "${DATA_DIR}"
