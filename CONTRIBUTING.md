# Guide de contribution

Merci de votre intérêt pour contribuer à Tedata Tennis !

## Avant de commencer

- Vérifiez que votre contribution n'a pas déjà été proposée dans les Issues
- Lisez le README.md pour comprendre le projet
- Assurez-vous d'avoir Python 3.9+ installé

## Étapes pour contribuer

### 1. Fork et cloner

```bash
git clone https://github.com/YOUR_USERNAME/tedata-tennis.git
cd tedata-tennis
```

### 2. Créer une branche

```bash
git checkout -b feature/ma-feature
```

Noms de branche recommandés :
- `feature/nouvelle-fonctionnalite`
- `fix/correction-bug`
- `docs/amelioration-documentation`
- `refactor/refonte-code`

### 3. Développer et tester

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
pip install pytest pytest-cov

# Développer votre feature
# ...

# Tester votre code
pytest tests/ -v
```

### 4. Commit et push

```bash
git add .
git commit -m "Description claire de vos changements"
git push origin feature/ma-feature
```

Messages de commit recommandés :
- `feat: ajouter la fonctionnalité X`
- `fix: corriger le bug Y`
- `docs: améliorer la documentation de Z`
- `refactor: nettoyer le code de X`
- `test: ajouter les tests pour X`

### 5. Ouvrir une Pull Request

Décrivez :
- Quels changements vous avez faits
- Pourquoi cette modification est nécessaire
- Comment on peut tester votre changement

## Standards de code

### Style Python

Nous suivons PEP 8 :

```bash
pip install flake8
flake8 src/ tests/ main.py
```

### Type hints

Utilisez les type hints autant que possible :

```python
from typing import List, Dict, Optional

def parse_pdf(self, pdf_path: str) -> List[Dict]:
    """Description"""
    pass
```

### Docstrings

Utilisez le format Google :

```python
def extract_tournaments(self, pdf_path: str) -> List[Dict]:
    """
    Extrait les tournois d'un PDF.
    
    Args:
        pdf_path: Chemin vers le fichier PDF
    
    Returns:
        List[Dict]: Liste des tournois trouvés
    
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
    """
```

### Tests

- Ajoutez des tests pour chaque nouvelle fonctionnalité
- Maintenez une couverture de code > 80%
- Nommez les tests clairement : `test_nom_de_la_fonction_cas`

```python
def test_parse_pdf_with_valid_file(self):
    """Test parsing d'un PDF valide"""
    result = self.parser.parse_pdf("valid.pdf")
    self.assertIsNotNone(result)
    self.assertGreater(len(result), 0)
```

## Reporte d'un bug

Si vous trouvez un bug :

1. Vérifiez que le bug n'a pas déjà été reporté
2. Créez une Issue avec :
   - Un titre clair
   - Une description détaillée
   - Les étapes pour reproduire
   - Le résultat attendu
   - Le résultat obtenu
   - Votre environnement (OS, version Python, etc.)

## Suggestions de fonctionnalités

Avant de développer une grande feature :
1. Ouvrez une Issue pour discuter
2. Attendez le feedback de la communauté
3. Développez une fois approuvé

## Questions ?

- Ouvrez une Discussion sur GitHub
- Contactez le mainteneur via email

---

Merci pour votre contribution ! 🎾
