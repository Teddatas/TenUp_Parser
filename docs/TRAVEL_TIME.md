# Estimateur de temps de trajet

## Vue d'ensemble

Cette feature ajoute une colonne "Temps de trajet" au CSV exporté, qui estime le temps nécessaire pour se rendre de votre adresse (définie) jusqu'au lieu du tournoi.

## ✅ 100% Gratuit

L'estimateur utilise **OSRM (Open Source Routing Machine)**, complètement gratuit et sans clé API.

- ✅ Aucune clé API requise
- ✅ Pas de limite de requêtes
- ✅ Open-source
- ✅ Fonctionne hors-ligne (si vous hébergez OSRM vous-même)

## Configuration

### Définir votre adresse de départ

Dans le fichier `.env` :

```
DEPARTURE_ADDRESS=Paris, France
```

Vous pouvez utiliser :
- Un arrondissement : `75012 Paris`
- Une adresse complète : `156 rue de la Nouvelle France, 93100 Montreuil, France`
- Une ville : `Versailles, France`

### Mode de transport

```
TRANSPORT_MODE=driving
```

Options disponibles :
- `driving` - Voiture (itinéraire routier)
- `walking` - À pied
- `cycling` - Vélo

**Note** : Le mode `transit` (métro/bus) n'est pas disponible avec OSRM gratuit. Utilisez `driving` comme approximation pour les transports en commun.

## Utilisation

### Via la CLI

```bash
# Parser et ajouter les temps de trajet
python main.py data/input/tournois.pdf -o data/output/result.csv

# Le CSV aura une colonne "Temps de trajet"
```

### Via le code

```python
from src.travel_calculator import TravelTimeCalculator

calculator = TravelTimeCalculator("Paris, France")

# Calculer un trajet
result = calculator.calculate_travel_time("Versailles, France", mode="driving")

# Résultat
if result:
    print(f"Durée : {result['duration_text']}")
    print(f"Distance : {result['distance_text']}")
    
    # Formater proprement
    formatted = calculator.format_travel_info(result)
    print(f"Trajet : {formatted}")
```

## Performance

- Les résultats sont **mis en cache** pour éviter les requêtes répétées
- Première requête : ~2-3 secondes
- Requêtes suivantes (même destination) : instantané

## Limitations

1. **Pas de transit (métro/bus)** : OSRM ne supporte que voiture/marche/vélo
2. **Trafic en temps réel** : Impossible sans API payante
3. **Horaires de transports** : Non disponible
4. **Accessibilité** : Routage basique

## Solutions pour améliorer

Si vous avez besoin de transports en commun avec trajets réels :

### Option 1 : OpenRouteService (gratuit avec inscription)
```bash
pip install openrouteservice geopy
```

### Option 2 : Heures d'arrivée estimées
Ajouter une colonne calculant l'heure d'arrivée si le match commence à une heure donnée.

### Option 3 : Tapis roulant (Mapbox)
Utilisateurs premium seulement.

## Données de sortie

Exemple de résultat dans le CSV :

```
Club | Tournoi | Installations | Temps de trajet
-----|---------|---------------|----------------
TC X | Tournoi | Versailles... | 45min (56.2 km)
```

## Troubleshooting

**"Adresse non trouvée"** : Nominatim n'a pas pu géolocaliser l'adresse
- Solution : Spécifier plus de détails (code postal + ville)

**"Trajet impossible"** : OSRM n'a pas trouvé de route
- Solution : Vérifier que les deux adresses sont valides et accessibles

**Temps très long (~10 requêtes/seconde)** : Rate-limiting de Nominatim
- Solution : Augmenter les délais ou mettre en cache les résultats

## Contribuer

Pour améliorer le calcul des trajets, voir [CONTRIBUTING.md](../CONTRIBUTING.md)
