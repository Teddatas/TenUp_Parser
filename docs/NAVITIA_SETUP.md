# Configuration Navitia pour Transports en Commun

## 🎯 Objectif
Ajouter le support des trajets en **métro, bus, RER, tram** (transports en commun d'Île-de-France).

## 📋 Prérequis
- ✅ Code déjà implémenté dans `src/travel_calculator.py`
- ⏳ Clé API Navitia en cours de demande

## 🚀 Étapes pour activer Navitia

### 1. Obtenir votre clé API (gratuit)

**Option A : Navitia (Standard)**
1. Allez sur https://www.navitia.io/
2. Cliquez sur "Sign up" (inscription gratuite)
3. Remplissez le formulaire simple
4. Confirmez votre email
5. Votre clé API sera disponible dans le dashboard

**Option B : IDFM Île-de-France (Recommandé pour Paris/IDF)**
1. Allez sur https://prim.iledefrance-mobilites.fr/
2. Créez un compte gratuit
3. Accédez à vos clés API

### 2. Configurer la clé dans votre projet

**Fichier `.env` :**
```bash
# Clé API Navitia pour les transports en commun
NAVITIA_API_KEY=votre_cle_api_ici
```

### 3. Tester l'intégration

**Via Python directement :**
```python
from src.travel_calculator import TravelTimeCalculator
import os

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Créer le calculateur
calculator = TravelTimeCalculator(
    departure_address="76 rue Sedaine 75011 Paris, France",
    navitia_api_key=os.getenv("NAVITIA_API_KEY")
)

# Tester un trajet en transports
result = calculator.calculate_travel_time(
    destination_address="Versailles, France",
    mode="transit"
)

if result:
    print(f"Durée : {result['duration_text']}")
    print(f"Distance : {result['distance_text']}")
    print(f"Transports : {result.get('transport_modes', [])}")
else:
    print("Erreur lors du calcul")
```

**Via le parseur principal :**
```bash
# Tester avec le parseur complet
export TRANSPORT_MODE=transit
python main.py --output data/output/test_navitia.csv
```

## 🔧 Modes de transport supportés

| Mode | Description | Implémentation |
|------|-------------|-----------------|
| `driving` | Voiture | OSRM ✅ |
| `walking` | À pied | OSRM ✅ |
| `cycling` | Vélo | OSRM ✅ |
| `transit` | Métro, bus, RER, tram | Navitia ✅ |

## 📊 Format de réponse Navitia

Quand un trajet est trouvé, voici ce que vous récupérez :

```python
{
    "duration_seconds": 1560,      # Durée en secondes
    "duration_text": "26min (Métro) (1 changement)",
    "distance_m": 12500,           # Distance approximative en mètres
    "distance_text": "12.5 km",
    "source": "Navitia/IDFM",
    "transport_modes": ["Métro"],  # Liste des transports utilisés
    "num_transfers": 1,            # Nombre de changements
}
```

## ⚙️ Configuration avancée

### Limiter le nombre de changements

Modifiez les paramètres dans `_calculate_with_navitia()` :

```python
params = {
    "from": from_coord,
    "to": to_coord,
    "count": 5,              # Retourner 5 trajets alternatifs
    "max_nb_transfers": 2,   # Maximum 2 changements
    "min_nb_transfers": 0,   # Minimum 0 changement
}
```

### Passer une heure/date spécifique

```python
from datetime import datetime

# Pour un départ demain à 14:30
tomorrow = datetime.now().replace(hour=14, minute=30).strftime("%Y%m%dT%H%M%S")

params = {
    "from": from_coord,
    "to": to_coord,
    "datetime": tomorrow,  # Format : yyyyMMddTHHmmss
}
```

## 🐛 Dépannage

### Erreur "401 Unauthorized"
- ❌ La clé API est invalide ou expirée
- ✅ Solution : Vérifiez votre clé dans `.env`

### Erreur "Pas de trajet trouvé"
- ❌ L'adresse est mal géocodée ou trop loin
- ✅ Solution : Vérifiez que l'adresse est correcte et en Île-de-France

### Timeout de la requête
- ❌ L'API est lente ou pas accessible
- ✅ Solution : La requête utilise un timeout de 10 secondes. Vérifiez votre connexion.

### "Navitia API key non configurée - mode transit indisponible"
- ❌ NAVITIA_API_KEY n'est pas défini
- ✅ Solution : Ajoutez la clé à votre `.env`

## 📖 Ressources officielles

- **Navitia API Documentation** : https://doc.navitia.io/
- **IDFM API** : https://prim.iledefrance-mobilites.fr/
- **Navitia - Getting Started** : https://www.navitia.io/

## 💡 Notes importantes

1. **Gratuit et sans limite** - Navitia est 100% gratuit après inscription simple
2. **Île-de-France optimisée** - Les trajets IDFM sont très précis pour la région parisienne
3. **Fallback automatique** - Si Navitia échoue, le code utilise OSRM automatiquement
4. **Cache intégré** - Les trajets sont mis en cache pour éviter les requêtes répétées
5. **Multi-modal** - Supporte les trajets combinant métro + bus + RER + marche

## 🎉 Prochaines étapes

Une fois la clé API reçue :
1. Ajouter la clé à `.env`
2. Changez `TRANSPORT_MODE=transit` dans `.env`
3. Relancez `python main.py`
4. Le CSV généré aura les temps de trajet en transports publics !
