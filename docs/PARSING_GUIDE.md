# Guide de parsing personnalisé

Ce guide vous aidera à adapter le parser à votre format de PDF spécifique.

## Étape 1 : Analyser la structure du PDF

### Inspectez d'abord votre PDF

```python
from src.pdf_handler import PDFHandler

pdf = "data/input/your_pdf.pdf"
handler = PDFHandler()

# Voir le texte brut
text = handler.extract_text(pdf)
print(text)

# Voir les tableaux détectés
tables = handler.extract_tables(pdf)
print(f"Tableaux trouvés: {len(tables)}")
for i, table in enumerate(tables):
    print(f"\nTableau {i}:")
    for row in table[:5]:  # Afficher les 5 premières lignes
        print(row)
```

## Étape 2 : Identifier les patterns

Les informations des tournois peuvent être organisées comme :

### Format A : Ligne d'en-tête suivie de détails
```
CLUB NAME - TOURNOI NAME
Date: 01/01/2026 - 02/01/2026
Judge: John Doe
Surface: Terre battue
...
```

### Format B : Tableau structuré
```
| Club | Tournoi | Date début | Date fin | ... |
|------|---------|-----------|---------|-----|
| TC X | T1      | 01/01/2026 | 02/01/2026 |... |
```

### Format C : Répétitions multiples de la même structure
```
Club; Tournoi; Date; ...
Catégorie; Epreuve; Droits
```

## Étape 3 : Implémenter la logique de parsing

Modifiez `src/parser.py` selon votre format :

### Exemple pour Format A (texte structuré)

```python
def parse_text(self, text: str) -> List[Dict]:
    """Parse du texte au format A"""
    tournaments = []
    
    # Regex pour détecter le début d'un tournoi
    tournament_pattern = r'^([A-Z\s]+)\s*-\s*(.+)$'
    
    lines = text.split('\n')
    current_tournament = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Nouvelle tournoi ?
        match = re.match(tournament_pattern, line)
        if match:
            if current_tournament:
                tournaments.append(current_tournament)
            
            current_tournament = {
                'Club': match.group(1).strip(),
                'Tournoi': match.group(2).strip(),
            }
        
        elif current_tournament:
            # Parser les détails
            if line.startswith('Date:'):
                dates = line.replace('Date:', '').strip().split('-')
                current_tournament['Date début'] = dates[0].strip()
                current_tournament['Date fin'] = dates[1].strip()
            
            elif line.startswith('Judge:'):
                current_tournament['JUGE-ARBITRE'] = line.replace('Judge:', '').strip()
            
            elif line.startswith('Surface:'):
                current_tournament['SURFACE(S)'] = line.replace('Surface:', '').strip()
    
    if current_tournament:
        tournaments.append(current_tournament)
    
    return tournaments
```

### Exemple pour Format B (tableau)

```python
def parse_text(self, text: str) -> List[Dict]:
    """Parse du texte au format tableau"""
    tournaments = []
    
    tables = self.pdf_handler.extract_tables(self.current_pdf)
    if not tables:
        return []
    
    # Supposer la première ligne est l'en-tête
    headers = tables[0][0]
    
    for row in tables[0][1:]:
        tournament = {}
        for header, value in zip(headers, row):
            # Nettoyer les espaces
            tournament[header.strip()] = value.strip() if value else ""
        
        tournaments.append(tournament)
    
    return tournaments
```

## Étape 4 : Tester votre parser

Créez un fichier de test `tests/test_custom_parser.py` :

```python
import unittest
from src.parser import TournamentParser

class TestCustomParsing(unittest.TestCase):
    
    def setUp(self):
        self.parser = TournamentParser()
    
    def test_parse_your_pdf(self):
        """Test parsing de votre PDF spécifique"""
        tournaments = self.parser.parse_pdf("data/input/your_pdf.pdf")
        
        # Vérifier qu'au moins un tournoi a été trouvé
        self.assertGreater(len(tournaments), 0)
        
        # Vérifier les champs essentiels
        for tournament in tournaments:
            self.assertIn('Club', tournament)
            self.assertIn('Tournoi', tournament)
            self.assertIn('Date début', tournament)
            self.assertIn('Date fin', tournament)
    
    def test_tournament_fields(self):
        """Test les champs d'un tournoi"""
        tournaments = self.parser.parse_pdf("data/input/your_pdf.pdf")
        first = tournaments[0] if tournaments else {}
        
        # Afficher le premier tournoi pour vérifier
        print("\nPremier tournoi trouvé:")
        for key, value in first.items():
            print(f"  {key}: {value}")
```

Lancez le test :
```bash
pytest tests/test_custom_parser.py -v -s
```

## Étape 5 : Valider et refiner

1. **Vérifiez les résultats** : Assurez-vous que les données extraites sont correctes
2. **Gérez les cas limites** : Dates incomplètes, noms spéciaux, caractères accentués
3. **Adaptez les regex** : Si le pattern varie entre les pages
4. **Nettoyez les données** : Supprimez les espaces inutiles, standardisez les formats

## Astuces pratiques

### Nettoyage des dates

```python
from datetime import datetime

def parse_date(date_str: str) -> str:
    """Convertit différents formats de date"""
    # DD/MM/YYYY
    try:
        parsed = datetime.strptime(date_str.strip(), '%d/%m/%Y')
        return parsed.strftime('%d/%m/%Y')
    except:
        return date_str.strip()
```

### Extraction des prix

```python
import re

def extract_price(text: str) -> str:
    """Extrait le montant d'une chaîne"""
    match = re.search(r'(\d+)\s*€', text)
    if match:
        return f"{match.group(1)} €"
    return ""
```

### Gestion des accents

```python
import unicodedata

def normalize_text(text: str) -> str:
    """Normalise le texte (supprime accents)"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
```

## Déboguer le parsing

Ajoutez des logs détaillés :

```python
from src.logger import setup_logger

logger = setup_logger(__name__)

# Dans votre parsing
logger.debug(f"Processing line: {line}")
logger.info(f"Found tournament: {tournament.get('Tournoi')}")
```

Lancez avec mode verbeux :
```bash
python main.py data/input/your_pdf.pdf -v
```

## Ressources

- [Regex101.com](https://regex101.com) - Testez vos expressions régulières
- [pdfplumber docs](https://github.com/jsvine/pdfplumber) - Documentation de pdfplumber
- [Python datetime](https://docs.python.org/3/library/datetime.html) - Manipulation des dates
