"""
test_endpoints.py - Tests des endpoints API (routes HTTP)
Vérifie que l'API répond correctement aux requêtes HTTP
"""

# SOMMAIRE DES TESTS

"""
RÉSUMÉ DES 25 TESTS :

ROOT & HEALTH (2 tests)
1. Page d'accueil
2. Health check

CATEGORIES (8 tests)
3. Création valide
4. Nom dupliqué
5. Couleur invalide
6. Liste toutes
7. Récupération par ID
8. Catégorie non trouvée
9. Modification
10. Suppression

TRANSACTIONS (9 tests)
11. Création valide
12. Catégorie invalide
13. Date future
14. Montant zéro
15. Liste toutes
16. Pagination
17. Filtres (période)
18. Modification
19. Suppression

SETTINGS (2 tests)
20. Récupération
21. Modification

INSIGHTS (3 tests)
22. Résumé mensuel
23. Total mensuel
24. Répartition catégories

ALERTS (1 test)
25. Alertes budgétaires
"""

# IMPORTS

import pytest # Framework de tests
from fastapi.testclient import TestClient # TestClient = client HTTP pour tester FastAPI sans lancer le serveur
from app.main import app # Notre application FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker # Pour créer une DB de test
from datetime import date # Pour manipuler les dates


# CONFIGURATION PYTEST

@pytest.fixture(scope="function")
def test_client():
    """
    Fixture qui crée un client de test FastAPI avec une DB temporaire
    """
    
    # CRITIQUE : Importer Base PUIS tous les modèles explicitement
    from app.database import Base
    
    # Importer TOUS les modèles pour les enregistrer dans Base.metadata
    
    # Maintenant importer les classes
    from app.models import Settings
    
    # Créer DB en mémoire
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},  # ← Permet multi-threading
        poolclass=StaticPool,  # ← Garde la même connexion pour tous les threads
        echo=False
    )
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    
    # Créer session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Override la dépendance get_db
    def override_get_db():
        """Remplace get_db() pour utiliser la DB de test"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Importer l'APPLICATION FastAPI
    from app.main import app
    from app.api.dependencies import get_db
    
    # Override
    app.dependency_overrides[get_db] = override_get_db
    
    # Initialiser Settings
    db = TestingSessionLocal()
    try:
        settings = Settings(id=1, global_monthly_budget=None)
        db.add(settings)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
    
    # Créer le client de test
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Donner le client au test
    yield client
    
    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
# TESTS ROOT & HEALTH

def test_read_root(test_client):
    """
    Test 1: Vérifie que la page d'accueil fonctionne
    GET / → 200 OK
    """
    
    response = test_client.get("/")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"


def test_health_check(test_client):
    """
    Test 2: Vérifie que le health check fonctionne
    GET /health → 200 OK
    """
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# TESTS CATEGORIES ENDPOINTS

def test_create_category_success(test_client):
    """
    Test 3: Vérifie qu'on peut créer une catégorie via POST
    POST /api/categories → 201 Created
    """
    
    category_data = {
        "name": "Alimentation",
        "color": "#FF0000",
        "monthly_budget": 500.0
    }
    
    response = test_client.post("/api/categories/", json=category_data)
    
    assert response.status_code == 201  # Created
    
    data = response.json()
    assert data["name"] == "Alimentation"
    assert data["color"] == "#FF0000"
    assert data["monthly_budget"] == 500.0
    assert "id" in data


def test_create_category_duplicate_name(test_client):
    """
    Test 4: Vérifie qu'on ne peut pas créer 2 catégories avec le même nom
    POST /api/categories (2x) → 400 Bad Request
    """
    
    category_data = {"name": "Transport"}
    
    # Première catégorie OK
    response1 = test_client.post("/api/categories/", json=category_data)
    assert response1.status_code == 201
    
    # Deuxième catégorie avec le même nom
    response2 = test_client.post("/api/categories/", json=category_data)
    
    assert response2.status_code == 400  # Bad Request
    assert "existe déjà" in response2.json()["detail"]


def test_create_category_invalid_color(test_client):
    """
    Test 5: Vérifie que Pydantic valide le format de la couleur
    POST /api/categories (couleur invalide) → 422 Unprocessable Entity
    """
    
    category_data = {
        "name": "Test",
        "color": "rouge"  # ❌ Pas un code hexa
    }
    
    response = test_client.post("/api/categories/", json=category_data)
    assert response.status_code == 422  # Validation error


def test_get_all_categories(test_client):
    """
    Test 6: Vérifie qu'on peut récupérer toutes les catégories
    GET /api/categories → 200 OK
    """
    # Créer 3 catégories
    test_client.post("/api/categories/", json={"name": "Cat1"})
    test_client.post("/api/categories/", json={"name": "Cat2"})
    test_client.post("/api/categories/", json={"name": "Cat3"})
    
    response = test_client.get("/api/categories/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Cat1"
    assert data[1]["name"] == "Cat2"
    assert data[2]["name"] == "Cat3"


def test_get_category_by_id(test_client):
    """
    Test 7: Vérifie qu'on peut récupérer une catégorie par son ID
    GET /api/categories/{id} → 200 OK
    """
    # Créer une catégorie
    create_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = create_response.json()["id"]
    
    response = test_client.get(f"/api/categories/{category_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test"


def test_get_category_not_found(test_client):
    """
    Test 8: Vérifie qu'on obtient 404 si la catégorie n'existe pas
    GET /api/categories/99999 → 404 Not Found
    """
    response = test_client.get("/api/categories/99999")
    assert response.status_code == 404
    assert "introuvable" in response.json()["detail"]


def test_update_category(test_client):
    """
    Test 9: Vérifie qu'on peut modifier une catégorie
    PATCH /api/categories/{id} → 200 OK
    """
    # Créer une catégorie
    create_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = create_response.json()["id"]
    
    update_data = {
        "name": "Test Modifié",
        "monthly_budget": 300.0
    }
    response = test_client.patch(f"/api/categories/{category_id}", json=update_data)
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Test Modifié"
    assert data["monthly_budget"] == 300.0


def test_delete_category(test_client):
    """
    Test 10: Vérifie qu'on peut supprimer une catégorie
    DELETE /api/categories/{id} → 204 No Content
    """
    # Créer une catégorie
    create_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = create_response.json()["id"]
    
    response = test_client.delete(f"/api/categories/{category_id}")
    
    assert response.status_code == 204  # No Content
    
    # Vérifier que la catégorie n'existe plus
    get_response = test_client.get(f"/api/categories/{category_id}")
    assert get_response.status_code == 404


# TESTS TRANSACTIONS ENDPOINTS

def test_create_transaction_success(test_client):
    """
    Test 11: Vérifie qu'on peut créer une transaction via POST
    POST /api/transactions → 201 Created
    """
    # Créer une catégorie d'abord
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    transaction_data = {
        "date": "2025-01-15",
        "description": "Courses Carrefour",
        "amount": 45.50,
        "category_id": category_id
    }
    
    response = test_client.post("/api/transactions/", json=transaction_data)
    
    assert response.status_code == 201
    
    data = response.json()
    assert data["description"] == "Courses Carrefour"
    assert data["amount"] == 45.50
    assert "id" in data
    assert "created_at" in data


def test_create_transaction_invalid_category(test_client):
    """
    Test 12: Vérifie qu'on ne peut pas créer une transaction avec une catégorie inexistante
    POST /api/transactions (catégorie invalide) → 400 Bad Request
    """
    
    transaction_data = {
        "date": "2025-01-15",
        "description": "Test",
        "amount": 50.0,
        "category_id": 99999  #N'existe pas
    }
    
    response = test_client.post("/api/transactions/", json=transaction_data)
    assert response.status_code == 400
    assert "n'existe pas" in response.json()["detail"]


def test_create_transaction_future_date(test_client):
    """
    Test 13: Vérifie qu'on ne peut pas créer une transaction dans le futur
    POST /api/transactions (date future) → 400 Bad Request
    """
    transaction_data = {
        "date": "2099-12-31",  #Date future
        "description": "Test",
        "amount": 50.0
    }
    
    response = test_client.post("/api/transactions/", json=transaction_data)
    assert response.status_code == 400
    assert "futur" in response.json()["detail"].lower()


def test_create_transaction_zero_amount(test_client):
    """
    Test 14: Vérifie qu'on ne peut pas créer une transaction avec montant = 0
    POST /api/transactions (montant 0) → 400 Bad Request
    """
    transaction_data = {
        "date": "2025-01-15",
        "description": "Test",
        "amount": 0.0  #Montant nul
    }
    
    response = test_client.post("/api/transactions/", json=transaction_data)
    assert response.status_code == 400
    assert "0" in response.json()["detail"]


def test_get_all_transactions(test_client):
    """
    Test 15: Vérifie qu'on peut récupérer toutes les transactions
    GET /api/transactions → 200 OK
    """
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    # Créer 3 transactions
    for i in range(3):
        test_client.post("/api/transactions/", json={
            "date": "2025-01-15",
            "description": f"Transaction {i}",
            "amount": 10.0 * (i + 1),
            "category_id": category_id
        })
    
    response = test_client.get("/api/transactions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_get_transactions_with_pagination(test_client):
    """
    Test 16: Vérifie que la pagination fonctionne
    GET /api/transactions?limit=2&skip=0 → 200 OK
    """
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    # Créer 5 transactions
    for i in range(5):
        test_client.post("/api/transactions/", json={
            "date": "2025-01-15",
            "description": f"Transaction {i}",
            "amount": 10.0,
            "category_id": category_id
        })
    
    # Page 1 (2 premiers)
    response1 = test_client.get("/api/transactions/?limit=2&skip=0")
    
    # Page 2 (2 suivants)
    response2 = test_client.get("/api/transactions/?limit=2&skip=2")
    
    assert response1.status_code == 200
    assert len(response1.json()) == 2
    
    assert response2.status_code == 200
    assert len(response2.json()) == 2


def test_get_transactions_with_filters(test_client):
    """
    Test 17: Vérifie que les filtres fonctionnent
    GET /api/transactions?from_date=...&to_date=... → 200 OK
    """
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    # Transactions en janvier
    test_client.post("/api/transactions/", json={
        "date": "2025-01-15",
        "description": "Janvier",
        "amount": 100.0,
        "category_id": category_id
    })
    
    # Transaction en février (ne doit pas être retournée)
    test_client.post("/api/transactions/", json={
        "date": "2025-02-15",
        "description": "Février",
        "amount": 200.0,
        "category_id": category_id
    })
    
    response = test_client.get("/api/transactions/?from_date=2025-01-01&to_date=2025-01-31")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["description"] == "Janvier"


def test_update_transaction(test_client):
    """
    Test 18: Vérifie qu'on peut modifier une transaction
    PATCH /api/transactions/{id} → 200 OK
    """
    
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    create_response = test_client.post("/api/transactions/", json={
        "date": "2025-01-15",
        "description": "Original",
        "amount": 50.0,
        "category_id": category_id
    })
    transaction_id = create_response.json()["id"]
    
    update_data = {
        "description": "Modifié",
        "amount": 75.0
    }
    response = test_client.patch(f"/api/transactions/{transaction_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Modifié"
    assert data["amount"] == 75.0


def test_delete_transaction(test_client):
    """
    Test 19: Vérifie qu'on peut supprimer une transaction
    DELETE /api/transactions/{id} → 204 No Content
    """
    
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    create_response = test_client.post("/api/transactions/", json={
        "date": "2025-01-15",
        "description": "Test",
        "amount": 50.0,
        "category_id": category_id
    })
    transaction_id = create_response.json()["id"]
    
    response = test_client.delete(f"/api/transactions/{transaction_id}")
    assert response.status_code == 204
    
    # Vérifier que la transaction n'existe plus
    get_response = test_client.get(f"/api/transactions/{transaction_id}")
    assert get_response.status_code == 404


# TESTS SETTINGS ENDPOINTS

def test_get_settings(test_client):
    """
    Test 20: Vérifie qu'on peut récupérer les paramètres
    GET /api/settings → 200 OK
    """
    
    response = test_client.get("/api/settings/")
    
    assert response.status_code == 200
    data = response.json()
    assert "global_monthly_budget" in data
    assert "updated_at" in data


def test_update_settings(test_client):
    """
    Test 21: Vérifie qu'on peut modifier le budget global
    PATCH /api/settings → 200 OK
    """
    response = test_client.patch("/api/settings/", json={
        "global_monthly_budget": 2000.0
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["global_monthly_budget"] == 2000.0


# TESTS INSIGHTS ENDPOINTS

def test_get_monthly_summary(test_client):
    """
    Test 22: Vérifie qu'on peut récupérer le résumé mensuel
    GET /api/insights/summary?year=2025&month=1 → 200 OK
    """
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    test_client.post("/api/transactions/", json={
        "date": "2025-01-15",
        "description": "Test",
        "amount": 100.0,
        "category_id": category_id
    })
    
    response = test_client.get("/api/insights/summary?year=2025&month=1")
    
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "count" in data
    assert "average" in data
    assert "by_category" in data
    assert data["total"] == 100.0


def test_get_monthly_total(test_client):
    """
    Test 23: Vérifie qu'on peut récupérer le total mensuel
    GET /api/insights/monthly-total?year=2025&month=1 → 200 OK
    """
    
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    test_client.post("/api/transactions/", json={
        "date": "2025-01-15",
        "description": "Test 1",
        "amount": 100.0,
        "category_id": category_id
    })
    test_client.post("/api/transactions/", json={
        "date": "2025-01-20",
        "description": "Test 2",
        "amount": 50.0,
        "category_id": category_id
    })
    
    response = test_client.get("/api/insights/monthly-total?year=2025&month=1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 150.0


def test_get_category_breakdown(test_client):
    """
    Test 24: Vérifie qu'on peut récupérer la répartition par catégorie
    GET /api/insights/category-breakdown?year=2025&month=1 → 200 OK
    """
    
    cat1 = test_client.post("/api/categories/", json={"name": "Alimentation"})
    cat2 = test_client.post("/api/categories/", json={"name": "Transport"})
    
    test_client.post("/api/transactions/", json={
        "date": "2025-01-15",
        "description": "Courses",
        "amount": 200.0,
        "category_id": cat1.json()["id"]
    })
    test_client.post("/api/transactions/", json={
        "date": "2025-01-20",
        "description": "Essence",
        "amount": 100.0,
        "category_id": cat2.json()["id"]
    })
    
    response = test_client.get("/api/insights/category-breakdown?year=2025&month=1")
    
    assert response.status_code == 200
    data = response.json()
    assert "Alimentation" in data
    assert "Transport" in data
    assert data["Alimentation"]["total"] == 200.0
    assert data["Transport"]["total"] == 100.0


# TESTS ALERTS ENDPOINTS

def test_get_budget_alerts(test_client):
    """
    Test 25: Vérifie qu'on peut récupérer les alertes budgétaires
    GET /api/alerts?year=2025&month=1 → 200 OK
    """
    # Définir budget global
    test_client.patch("/api/settings/", json={"global_monthly_budget": 100.0})
    
    cat_response = test_client.post("/api/categories/", json={"name": "Test"})
    category_id = cat_response.json()["id"]
    
    # Dépasser le budget
    test_client.post("/api/transactions/", json={
        "date": "2025-01-15",
        "description": "Grosse dépense",
        "amount": 150.0,
        "category_id": category_id
    })
    
    response = test_client.get("/api/alerts/?year=2025&month=1")
    
    assert response.status_code == 200
    data = response.json()
    assert "alerts" in data
    assert len(data["alerts"]) >= 1  # Au moins l'alerte globale