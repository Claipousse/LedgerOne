# LedgerOne - Gestionnaire de Dépenses Personnelles

Application web de gestion financière personnelle permettant de suivre, analyser et budgétiser ses dépenses au quotidien.

---

## Table des matières

1. [Présentation](#présentation)
2. [Fonctionnalités](#fonctionnalités)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Lancement](#lancement)
6. [Structure du projet](#structure-du-projet)
7. [Documentation API](#documentation-api)
8. [Import CSV](#import-csv)
9. [Tests](#tests)
10. [Technologies](#technologies)
11. [Licence](#licence)

---

## Présentation

LedgerOne est une application web complète de gestion financière développée dans le cadre d'un test technique pour JEECE. Elle offre une interface moderne et intuitive pour gérer ses dépenses personnelles avec un suivi budgétaire précis.

### Objectifs du projet

- Permettre la saisie manuelle et l'import en masse (CSV) de transactions
- Organiser les dépenses par catégories personnalisables
- Définir et suivre des budgets mensuels (global et par catégorie)
- Visualiser des statistiques et tendances financières
- Recevoir des alertes en cas de dépassement de budget

### Caractéristiques techniques

- Architecture 3 couches (Modèles / Services / Routes)
- API REST complète (16 endpoints)
- Base de données SQLite avec SQLAlchemy ORM
- Interface web responsive en HTML/CSS/JavaScript vanilla
- Visualisations avec Chart.js
- 79 tests automatisés (couverture complète)

---

## Fonctionnalités

### Gestion des catégories

- Création, modification et suppression de catégories
- Attribution d'une couleur et d'un budget mensuel par catégorie
- Visualisation des dépenses par catégorie
- Navigation temporelle (mois actuel, 3 derniers mois, année)

### Gestion des transactions

- Ajout, modification et suppression de transactions
- Recherche en temps réel par description
- Filtrage multi-critères (catégories, dates, montants)
- Pagination intelligente
- Tri personnalisable

### Import CSV

- Import en masse de transactions via fichier CSV
- Drag & drop ou sélection de fichier
- Création automatique des catégories manquantes
- Rapport détaillé (succès, échecs, erreurs)
- Validation stricte des données

### Budget et alertes

- Définition d'un budget mensuel global
- Budgets mensuels par catégorie
- Alertes visuelles en cas de dépassement
- Barre de progression en temps réel
- Comparaison budget vs réalité

### Tableaux de bord et statistiques

- Indicateurs clés (total, nombre d'opérations, moyenne)
- Graphiques interactifs (camembert, barres, lignes)
- Top 5 des catégories les plus dépensières
- Évolution mensuelle et tendances
- Moyenne glissante sur 3 mois

---

## Architecture

### Schéma général
```
┌─────────────────────────────────────────────────────────────┐
│                       FRONTEND (HTML/CSS/JS)                │
│  - Dashboard  - Catégories  - Transactions  - Budget        │
│  - Import CSV  - Navigation  - Visualisations (Chart.js)    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP REST (JSON)
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    API FASTAPI (Backend)                    │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              COUCHE ROUTES (API)                     │   │
│  │  - categories.py  - transactions.py  - settings.py   │   │
│  │  - insights.py    - alerts.py        - import_csv.py │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │           COUCHE SERVICES (Logique métier)           │   │
│  │  - category_service.py   - transaction_service.py    │   │
│  │  - settings_service.py   - alert_service.py          │   │
│  │  - import_service.py                                 │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                   │
│  ┌──────────────────────▼───────────────────────────────┐   │
│  │         COUCHE MODÈLES (Base de données)             │   │
│  │  - category.py    - transaction.py    - settings.py  │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         │                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                ┌─────────▼─────────┐
                │  SQLite Database  │
                │  (ledgerone.db)   │
                └───────────────────┘
```

### Architecture 3 couches

**1. Couche Modèles (Models)**
- Définition des tables SQL avec SQLAlchemy
- Contraintes d'intégrité (UNIQUE, CHECK, FK)
- Relations entre entités (Category ↔ Transaction)

**2. Couche Services (Business Logic)**
- Logique métier et calculs
- Validations avancées
- Agrégations et statistiques
- Gestion des erreurs

**3. Couche Routes (API)**
- Endpoints REST
- Validation des entrées (Pydantic)
- Codes de statut HTTP
- Documentation automatique

---

## Installation

### Prérequis

- Python 3.12 ou supérieur
- pip (gestionnaire de paquets Python)
- Un navigateur web moderne

### Étapes d'installation

1. Cloner le dépôt
```bash
git clone <url-du-depot>
cd LedgerOne
```

2. Créer un environnement virtuel (recommandé)
```bash
cd backend
python -m venv venv

# Activation (Windows)
venv\Scripts\activate

# Activation (Linux/Mac)
source venv/bin/activate
```

3. Installer les dépendances
```bash
pip install -r requirements.txt
```

4. Initialiser la base de données
```bash
python scripts/init_db.py
```

La base de données SQLite sera créée dans `data/ledgerone.db`.

5. (Optionnel) Générer des données de test
```bash
cd scripts
python generation_csv.py
```

Cela créera un fichier `transactions_generated.csv` avec 2000 transactions fictives.

---

## Lancement

### Backend (API)

Depuis le dossier `backend/` :
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur `http://localhost:8000`

Documentation interactive disponible sur :
- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

### Frontend

Ouvrir simplement le fichier `frontend/index.html` dans un navigateur web.

Ou utiliser un serveur HTTP local :
```bash
cd frontend
python -m http.server 8080
```

L'interface sera accessible sur `http://localhost:8080`

### Vérification

1. Ouvrir `http://localhost:8080` dans le navigateur
2. Le dashboard devrait s'afficher avec les KPIs
3. Naviguer vers les différentes pages via la sidebar
4. Tester l'import CSV avec le fichier généré

---

## Structure du projet
```
LedgerOne/
│
├── backend/                          # Code serveur Python
│   ├── app/                          # Application FastAPI
│   │   ├── api/                      # Couche API
│   │   │   ├── dependencies.py       # Dépendances (get_db)
│   │   │   └── routes/               # Endpoints REST
│   │   │       ├── categories.py     # CRUD catégories
│   │   │       ├── transactions.py   # CRUD transactions
│   │   │       ├── settings.py       # Paramètres globaux
│   │   │       ├── insights.py       # Statistiques
│   │   │       ├── alerts.py         # Alertes budgétaires
│   │   │       └── import_csv.py     # Import CSV
│   │   │
│   │   ├── models/                   # Couche Modèles (ORM)
│   │   │   ├── category.py           # Modèle Category
│   │   │   ├── transaction.py        # Modèle Transaction
│   │   │   └── settings.py           # Modèle Settings
│   │   │
│   │   ├── schemas/                  # Schémas Pydantic
│   │   │   ├── category.py           # Validation Category
│   │   │   ├── transaction.py        # Validation Transaction
│   │   │   └── settings.py           # Validation Settings
│   │   │
│   │   ├── services/                 # Couche Services (logique)
│   │   │   ├── category_service.py   # Logique catégories
│   │   │   ├── transaction_service.py# Logique transactions
│   │   │   ├── settings_service.py   # Logique paramètres
│   │   │   ├── alert_service.py      # Calcul alertes
│   │   │   └── import_service.py     # Import CSV
│   │   │
│   │   ├── config.py                 # Configuration (.env)
│   │   ├── database.py               # Connexion SQLAlchemy
│   │   └── main.py                   # Point d'entrée FastAPI
│   │
│   ├── scripts/                      # Scripts utilitaires
│   │   ├── init_db.py                # Initialisation DB
│   │   └── generation_csv.py         # Génération données test
│   │
│   ├── tests/                        # Tests automatisés
│   │   ├── test_models.py            # Tests modèles (18)
│   │   ├── test_services.py          # Tests services (24)
│   │   ├── test_endpoints.py         # Tests API (25)
│   │   └── test_import_csv.py        # Tests import (12)
│   │
│   └── requirements.txt              # Dépendances Python
│
├── frontend/                         # Interface utilisateur
│   ├── css/
│   │   └── styles.css                # Styles globaux (dark theme)
│   │
│   ├── js/
│   │   ├── api.js                    # Client API (fetch)
│   │   ├── sidebar-loader.js         # Chargement sidebar
│   │   ├── dashboard.js              # Logique dashboard
│   │   ├── categories.js             # Logique catégories
│   │   ├── transactions.js           # Logique transactions
│   │   ├── budget.js                 # Logique budget
│   │   └── detail_categorie.js       # Détail catégorie
│   │
│   ├── includes/
│   │   └── sidebar.html              # Menu de navigation
│   │
│   ├── index.html                    # Dashboard principal
│   ├── categories.html               # Page catégories
│   ├── transactions.html             # Page transactions
│   ├── budget.html                   # Page budget
│   ├── import.html                   # Page import CSV
│   └── detail_categorie.html         # Détail catégorie
│
├── data/                             # Base de données
│   └── ledgerone.db                  # SQLite (créé au 1er lancement)
│
└── README.md                         # Ce fichier
```

---

## Documentation API

L'API REST expose 16 endpoints organisés par ressource.

### Base URL
```
http://localhost:8000/api
```

### Endpoints Catégories

**Liste toutes les catégories**
```http
GET /api/categories/
```

Réponse :
```json
[
  {
    "id": 1,
    "name": "Alimentation",
    "color": "#FF6B6B",
    "monthly_budget": 400.00
  }
]
```

**Récupérer une catégorie**
```http
GET /api/categories/{id}
```

**Créer une catégorie**
```http
POST /api/categories/
Content-Type: application/json

{
  "name": "Transport",
  "color": "#4ECDC4",
  "monthly_budget": 200.00
}
```

**Modifier une catégorie**
```http
PATCH /api/categories/{id}
Content-Type: application/json

{
  "monthly_budget": 250.00
}
```

**Supprimer une catégorie**
```http
DELETE /api/categories/{id}
```

### Endpoints Transactions

**Liste toutes les transactions (avec filtres)**
```http
GET /api/transactions/?skip=0&limit=100&from_date=2025-01-01&to_date=2025-01-31&category_id=3&search=courses
```

Paramètres :
- `skip` : Pagination (défaut: 0)
- `limit` : Nombre max de résultats (défaut: 100)
- `from_date` : Date début (format ISO: YYYY-MM-DD)
- `to_date` : Date fin
- `category_id` : Filtrer par catégorie
- `search` : Recherche textuelle dans descriptions

**Récupérer une transaction**
```http
GET /api/transactions/{id}
```

**Créer une transaction**
```http
POST /api/transactions/
Content-Type: application/json

{
  "date": "2025-01-15",
  "description": "Courses Carrefour",
  "amount": 45.50,
  "category_id": 1
}
```

**Modifier une transaction**
```http
PATCH /api/transactions/{id}
Content-Type: application/json

{
  "amount": 50.00
}
```

**Supprimer une transaction**
```http
DELETE /api/transactions/{id}
```

### Endpoints Paramètres

**Récupérer les paramètres globaux**
```http
GET /api/settings/
```

Réponse :
```json
{
  "global_monthly_budget": 2000.00,
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Modifier le budget global**
```http
PATCH /api/settings/
Content-Type: application/json

{
  "global_monthly_budget": 2500.00
}
```

### Endpoints Statistiques

**Résumé mensuel complet**
```http
GET /api/insights/summary?year=2025&month=1
```

Réponse :
```json
{
  "total": 1543.75,
  "count": 48,
  "average": 32.16,
  "by_category": {
    "Alimentation": {
      "total": 432.50,
      "percentage": 28.0,
      "count": 15
    },
    "Transport": {
      "total": 287.30,
      "percentage": 18.6,
      "count": 8
    }
  }
}
```

**Total mensuel**
```http
GET /api/insights/monthly-total?year=2025&month=1&category_id=3
```

**Répartition par catégorie**
```http
GET /api/insights/category-breakdown?year=2025&month=1
```

### Endpoints Alertes

**Alertes budgétaires du mois**
```http
GET /api/alerts/?year=2025&month=1
```

Réponse :
```json
{
  "alerts": [
    {
      "scope": "global",
      "budget": 2000.00,
      "actual": 2350.50,
      "delta": 350.50
    },
    {
      "scope": "category",
      "category": "Alimentation",
      "budget": 400.00,
      "actual": 475.30,
      "delta": 75.30
    }
  ]
}
```

### Endpoints Import

**Importer un fichier CSV**
```http
POST /api/import/csv
Content-Type: multipart/form-data

file=@transactions.csv
```

Réponse :
```json
{
  "inserted": 15,
  "skipped": 2,
  "errors": [
    "Ligne 3: La date doit être au format YYYY-MM-DD",
    "Ligne 7: Le montant doit être un nombre"
  ]
}
```

---

## Import CSV

### Format attendu

Le fichier CSV doit contenir les colonnes suivantes :

**Colonnes obligatoires :**
- `date` : Date au format ISO (YYYY-MM-DD)
- `description` : Description de la transaction (texte)
- `amount` : Montant en euros (nombre décimal, peut être négatif)

**Colonne optionnelle :**
- `category` : Nom de la catégorie (texte)

### Exemple de fichier CSV
```csv
date,description,amount,category
2025-01-15,Courses Carrefour,45.50,Alimentation
2025-01-16,Essence Shell,60.00,Transport
2025-01-17,Cinéma UGC,15.00,Loisirs
2025-01-18,Remboursement Sécu,-30.00,Santé
2025-01-19,Restaurant,42.00,Alimentation
```

### Règles de validation

**Date :**
- Format strict : YYYY-MM-DD
- Ne peut pas être dans le futur
- Erreur si format invalide

**Description :**
- Obligatoire
- Maximum 255 caractères
- Ne peut pas être vide

**Amount :**
- Obligatoire
- Doit être un nombre (entier ou décimal)
- Ne peut pas être exactement 0
- Peut être négatif (remboursements)

**Category :**
- Optionnelle
- Si la catégorie n'existe pas, elle est créée automatiquement avec :
  - Couleur par défaut : `#818cf8`
  - Budget mensuel : `None`

### Comportement de l'import

1. **Parsing du CSV**
   - Détection automatique de l'encodage (UTF-8)
   - Lecture des headers (première ligne)
   - Validation de la structure

2. **Validation ligne par ligne**
   - Chaque ligne est validée individuellement
   - Les erreurs sont collectées avec leur numéro de ligne
   - Les lignes valides sont importées
   - Les lignes invalides sont ignorées

3. **Création automatique des catégories**
   - Si une catégorie n'existe pas, elle est créée
   - Pas de doublon (vérification par nom)
   - Couleur et budget par défaut

4. **Rapport d'import**
   - `inserted` : Nombre de transactions importées avec succès
   - `skipped` : Nombre de lignes ignorées
   - `errors` : Liste détaillée des erreurs avec numéros de lignes

### Exemple d'utilisation

**Via l'interface web :**
1. Accéder à la page "Importation"
2. Glisser-déposer le fichier CSV ou cliquer pour le sélectionner
3. Cliquer sur "Importer les transactions"
4. Consulter le rapport d'import

**Via l'API :**
```bash
curl -X POST http://localhost:8000/api/import/csv \
  -F "file=@transactions.csv"
```

### Gestion des erreurs courantes

| Erreur | Cause | Solution |
|--------|-------|----------|
| "La date doit être au format YYYY-MM-DD" | Format de date invalide | Utiliser YYYY-MM-DD (ex: 2025-01-15) |
| "La date ne peut pas être dans le futur" | Date > aujourd'hui | Vérifier les dates |
| "Le montant doit être un nombre" | Texte au lieu d'un nombre | Utiliser des nombres (ex: 45.50) |
| "Le montant ne peut être égal à 0" | amount = 0.00 | Supprimer la ligne ou mettre un montant |
| "La description est obligatoire" | Champ vide | Remplir la description |
| "Le fichier est vide" | CSV sans données | Vérifier le fichier |

---

## Tests

Le projet contient une suite complète de 79 tests automatisés couvrant tous les aspects du backend.

### Structure des tests
```
tests/
├── test_models.py         # 18 tests - Modèles SQLAlchemy
├── test_services.py       # 24 tests - Logique métier
├── test_endpoints.py      # 25 tests - Routes API
└── test_import_csv.py     # 12 tests - Import CSV
```

### Lancer les tests

**Tous les tests :**
```bash
cd backend
pytest tests/ -v
```

**Tests spécifiques :**
```bash
# Tests des modèles uniquement
pytest tests/test_models.py -v

# Tests des services uniquement
pytest tests/test_services.py -v

# Tests des endpoints uniquement
pytest tests/test_endpoints.py -v

# Tests de l'import CSV uniquement
pytest tests/test_import_csv.py -v
```

**Avec couverture de code :**
```bash
pytest tests/ -v --cov=app --cov-report=html
```

Le rapport HTML sera généré dans `htmlcov/index.html`

### Catégories de tests

**Tests Modèles (18 tests)**
- Création et validation des entités
- Contraintes SQL (UNIQUE, CHECK, FK)
- Relations bidirectionnelles
- Index de performance

**Tests Services (24 tests)**
- Logique CRUD complète
- Calculs financiers (totaux, moyennes, répartition)
- Validations métier (dates, montants, budgets)
- Gestion des cas limites

**Tests Endpoints (25 tests)**
- Codes de statut HTTP corrects
- Validation des entrées/sorties
- Gestion des erreurs (400, 404, 422, 500)
- Filtres et pagination

**Tests Import CSV (12 tests)**
- Parsing de fichiers valides
- Détection d'erreurs (dates, montants)
- Création automatique de catégories
- Gestion des fichiers invalides
- Cas limites (montants négatifs, données manquantes)

### Exemples de tests

**Test de validation de date :**
```python
def test_create_transaction_future_date(test_client):
    transaction_data = {
        "date": "2099-12-31",
        "description": "Test",
        "amount": 50.0
    }
    response = test_client.post("/api/transactions/", json=transaction_data)
    assert response.status_code == 400
    assert "futur" in response.json()["detail"].lower()
```

**Test de calcul d'agrégat :**
```python
def test_get_monthly_total_calculation(db_session):
    # Créer 3 transactions en janvier
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10), description="Achat 1", amount=100.0
    ))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 15), description="Achat 2", amount=50.50
    ))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 20), description="Achat 3", amount=25.25
    ))
    
    total = get_monthly_total(db_session, 2025, 1)
    assert total == 175.75  # 100 + 50.50 + 25.25
```

### Couverture de code

La suite de tests vise une couverture complète du code backend :

- Modèles : 100%
- Services : 95%
- Routes : 90%
- Global : 93%

---

## Technologies

### Backend

| Technologie | Version | Usage |
|-------------|---------|-------|
| Python | 3.12 | Langage principal |
| FastAPI | 0.115.0 | Framework web API REST |
| Uvicorn | 0.32.0 | Serveur ASGI |
| SQLAlchemy | 2.0.35 | ORM base de données |
| Pydantic | 2.9.2 | Validation de données |
| SQLite | 3.x | Base de données |
| Pytest | - | Tests automatisés |

### Frontend

| Technologie | Version | Usage |
|-------------|---------|-------|
| HTML5 | - | Structure des pages |
| CSS3 | - | Styles et design |
| JavaScript | ES6+ | Logique client |
| Chart.js | 4.4.0 | Graphiques interactifs |

### Outils de développement

- Git : Gestion de version
- VS Code : Éditeur de code (recommandé)
- Chrome DevTools : Débogage frontend

## Informations

Ce projet a été développé dans le cadre d'un test technique pour JEECE (Junior-Entreprise de l'ECE).
Pour toute question ou remarque concernant ce projet, vous pouvez me contacter