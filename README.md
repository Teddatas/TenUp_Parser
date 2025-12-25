# 🎾 TenUp Parser

Parser de tournois de tennis depuis PDF vers CSV

## Description

Ce projet automatise l'extraction des informations de tournois de tennis à partir de fichiers PDF (notamment les documents TenUp) et les exporte dans des fichiers CSV structurés.

### Fonctionnalités

- ✅ Extraction de texte depuis PDF
- ✅ Parsing des données de tournois
- ✅ Export en CSV avec colonnes standardisées
- ✅ Export groupé par catégorie
- ✅ Gestion complète des erreurs avec logging
- ✅ Structure de projet professionnelle

## Structure du projet

```
TenUp_Parser/
├── src/                      # Code source principal
│   ├── __init__.py
│   ├── config.py             # Configuration et chemins
│   ├── logger.py             # Système de logging
│   ├── pdf_handler.py        # Gestion des fichiers PDF
│   ├── parser.py             # Logique de parsing principal
│   └── csv_exporter.py       # Export des données en CSV
├── tests/                    # Tests unitaires
│   ├── __init__.py
│   └── test_parser.py
├── data/
│   ├── input/               # Fichiers PDF à parser (à ajouter)
│   └── output/              # Fichiers CSV générés
├── docs/                    # Documentation
├── logs/                    # Fichiers de log
├── main.py                  # Point d'entrée de l'application
├── requirements.txt         # Dépendances Python
├── .gitignore              # Fichiers à ignorer dans Git
└── README.md               # Ce fichier
```

## Installation

### Prérequis

- Python 3.9+
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner le repository**
   ```bash
   git clone https://github.com/Teddatas/TenUp_Parser.git
   cd TenUp_Parser
   ```

2. **Créer un environnement virtuel** (recommandé)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Sur macOS/Linux
   # ou
   venv\Scripts\activate  # Sur Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

### Commande basique

```bash
python main.py data/input/tournaments.pdf
```

### Avec fichier de sortie personnalisé

```bash
python main.py data/input/tournaments.pdf -o data/output/my_tournaments.csv
```

### Export groupé par catégorie

```bash
python main.py data/input/tournaments.pdf --by-category
```

### Aide

```bash
python main.py --help
```

## Format de sortie

Les tournois sont exportés avec les colonnes suivantes :

| Colonne | Description |
|---------|-------------|
| Club | Nom du club organisateur |
| Tournoi | Nom du tournoi |
| Date début | Date de début du tournoi |
| Date fin | Date de fin du tournoi |
| JUGE-ARBITRE | Juge-arbitre du tournoi |
| SURFACE(S) | Type(s) de surface(s) |
| PRIX EN ESPÈCE | Montant des prix en espèces |
| PRIX EN LOTS | Montant des prix en lots |
| INSCRIPTIONS | Accepte les inscriptions ? |
| PAIEMENT EN LIGNE | Paiement en ligne disponible ? |
| CODE | Code du tournoi |
| ENGAGEMENTS | Détails des engagements |
| INSTALLATIONS | Adresse et détails du lieu |
| Téléphone | Numéro de téléphone |
| Catégorie | Catégorie d'âge |
| Epreuve | Type d'épreuve (Simple, Double, etc.) |
| Classement | Classement requis |
| Droits | Droits d'engagement |

## Configuration

Modifiez `src/config.py` pour :
- Ajouter ou modifier les colonnes attendues
- Changer les formats acceptés
- Ajuster le niveau de logging
- Définir les chemins personnalisés

## Fichiers d'exemple

- `tenup_example.csv` - Exemple des données sources
- `tournois_output.csv` - Exemple de la sortie attendue

## Logging

Les logs sont enregistrés dans :
- Console : affichage en temps réel
- Fichier : `logs/tenup_parser.log`

Niveau de log configurable via `src/config.py`

## Tests

Exécuter les tests unitaires :

```bash
pytest tests/ -v
```

Avec rapport de couverture :

```bash
pytest tests/ -v --cov=src
```

## Améliorations futures

- [ ] Support des fichiers Excel (.xlsx)
- [ ] Interface graphique
- [ ] Configuration via fichier YAML
- [ ] Validation avancée des données
- [ ] Détection automatique de la structure PDF
- [ ] Base de données pour stocker les tournois
- [ ] API REST pour requêtes distantes

## Contribution

Les contributions sont bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Problèmes courants

### PDF non parsé correctement

Le parsing dépend de la structure du PDF. Pour les PDFs complexes :
1. Vérifiez que le PDF n'est pas protégé
2. Essayez de convertir en texte d'abord (voir `src/pdf_handler.py`)
3. Adaptez la logique de parsing pour votre format spécifique

### Colonnes manquantes en sortie

Certaines données peuvent ne pas être présentes dans le PDF. Elles apparaîtront vides en sortie. Modifiez `src/parser.py` pour affiner l'extraction.

## License

Ce projet est sous license MIT. Voir le fichier LICENSE pour plus de détails.

## Auteur

**Teddy** - [GitHub](https://github.com/Teddatas)

## Contact

Pour toute question ou suggestion : [your-email@example.com](mailto:your-email@example.com)

---

**Dernière mise à jour** : 25 décembre 2025
