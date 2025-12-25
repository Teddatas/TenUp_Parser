# Architecture de TenUp Parser

## Vue d'ensemble

TenUp Parser est organisé selon une architecture modulaire avec séparation des responsabilités.

## Modules principaux

### `src/config.py`
- **Responsabilité** : Configuration centralisée du projet
- **Contient** : Chemins, colonnes de sortie, formats acceptés, logging
- **Utilisation** : Importé par tous les autres modules

### `src/logger.py`
- **Responsabilité** : Gestion du logging uniforme
- **Contient** : Configuration des handlers (console et fichier)
- **Utilisation** : `from src.logger import setup_logger`

### `src/pdf_handler.py`
- **Responsabilité** : Gestion des fichiers PDF
- **Classe** : `PDFHandler` (méthodes statiques)
- **Méthodes** :
  - `extract_text()` : Extraire tout le texte
  - `extract_tables()` : Extraire les tableaux
  - `get_pdf_info()` : Récupérer les métadonnées

### `src/parser.py`
- **Responsabilité** : Parsing des données de tournois
- **Classe** : `TournamentParser`
- **Méthodes** :
  - `parse_pdf()` : Parser un fichier PDF complet
  - `parse_text()` : Parser du texte brut
  - `validate_tournament()` : Valider un tournoi

### `src/csv_exporter.py`
- **Responsabilité** : Export des données en CSV
- **Classe** : `CSVExporter` (méthodes statiques)
- **Méthodes** :
  - `export_tournaments()` : Export en un seul fichier
  - `export_by_category()` : Export en fichiers par catégorie

### `main.py`
- **Responsabilité** : Point d'entrée et CLI
- **Contient** : `argparse` pour les arguments en ligne de commande
- **Flux** : Parse les args → initialise parser → traite PDF → exporte CSV

## Flux de données

```
main.py
├── Argumenter les paramètres CLI
├── Vérifier le fichier PDF
│
└─→ TournamentParser
    ├── Initialiser PDFHandler
    ├── Extraire le texte via PDFHandler.extract_text()
    │
    └─→ parse_text()
        └── Retourner la liste des tournois
│
└─→ CSVExporter
    ├── Valider les données
    ├── Grouper (optionnel)
    │
    └─→ Exporter en CSV
        └── Sauvegarder le fichier
```

## Dépendances

```
main.py
├── src.config
├── src.logger
└── src.parser
    └── src.pdf_handler
        └── pdfplumber (externe)
└── src.csv_exporter
    └── src.config
```

## Extensibilité

### Ajouter un nouveau format de sortie

1. Créer `src/json_exporter.py` ou `src/xlsx_exporter.py`
2. Implémenter une classe `JSONExporter` avec méthode `export_tournaments()`
3. Importer dans `main.py` et ajouter une option CLI

### Améliorer le parsing

Modifier `src/parser.py` :
- Affiner `parse_text()` selon la structure de vos PDFs
- Ajouter des regex ou des patterns de reconnaissance
- Valider les données extraites

### Supporter un nouveau type de fichier

1. Créer `src/excel_handler.py` pour les fichiers Excel
2. Implémenter les méthodes d'extraction
3. Adapter `TournamentParser` pour utiliser le handler approprié

## Considérations de performance

- **Fichiers volumineux** : Traiter page par page pour réduire la mémoire
- **Logging** : Utiliser `logger.debug()` pour les infos détaillées
- **CSV** : Écrire les lignes au fur et à mesure plutôt que tout en mémoire

## Tests

Structure des tests :
```
tests/
├── test_parser.py        # TournamentParser
├── test_csv_exporter.py  # CSVExporter
├── test_pdf_handler.py   # PDFHandler
└── test_config.py        # Vérifier les chemins
```

Chaque module doit avoir des tests unitaires.

## Erreurs et exceptions

Gestion centralisée via `logger` :
- Exceptions capturées
- Messages d'erreur clairs
- Enregistrement dans les logs
- Retour de codes d'erreur appropriés
