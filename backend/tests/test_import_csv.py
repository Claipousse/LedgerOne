"""
test_import_csv.py - Tests de l'endpoint d'importation CSV
Vérifie le parsing, les validations et la gestion des erreurs
"""

import pytest
from io import BytesIO

@pytest.fixture(scope="function")
def test_client():
    """Fixture avec DB temporaire et client de test"""
    from app.database import Base
    from app.models import Settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    from app.main import app
    from app.api.dependencies import get_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Initialiser Settings
    db = TestingSessionLocal()
    try:
        settings = Settings(id=1, global_monthly_budget=None)
        db.add(settings)
        db.commit()
    except:
        db.rollback()
    finally:
        db.close()
    
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    yield client
    
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_import_csv_valid(test_client):
    """
    Test 1: Import CSV valide avec toutes les colonnes
    POST /api/import/csv → 200 OK
    """
    csv_content = """date,description,amount,category
    2025-01-15,Courses Carrefour,45.50,Alimentation
    2025-01-16,Essence Shell,60.00,Transport
    2025-01-17,Cinéma UGC,15.00,Loisirs"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 3
    assert data["skipped"] == 0
    assert len(data["errors"]) == 0


def test_import_csv_without_category(test_client):
    """
    Test 2: Import CSV sans colonne category (optionnelle)
    POST /api/import/csv → 200 OK
    """
    csv_content = """date,description,amount
    2025-01-15,Achat divers,25.00
    2025-01-16,Paiement,30.00"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 2
    assert data["skipped"] == 0


def test_import_csv_creates_categories(test_client):
    """
    Test 3: Vérifie que les catégories inexistantes sont créées automatiquement
    POST /api/import/csv → 200 OK + nouvelles catégories
    """
    csv_content = """date,description,amount,category
    2025-01-15,Achat,50.00,NouvelleCatégorie"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    
    # Vérifier que la catégorie existe
    categories_response = test_client.get("/api/categories/")
    categories = categories_response.json()
    
    assert any(cat["name"] == "NouvelleCatégorie" for cat in categories)


def test_import_csv_invalid_date(test_client):
    """
    Test 4: Ligne avec date invalide doit être skippée
    POST /api/import/csv → 200 OK avec errors
    """
    csv_content = """date,description,amount,category
    2025-13-45,Achat invalide,50.00,Test
    2025-01-15,Achat valide,30.00,Test"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 1  # Seule la 2ème ligne
    assert data["skipped"] == 1
    assert len(data["errors"]) == 1
    assert "Ligne 2" in data["errors"][0]


def test_import_csv_future_date(test_client):
    """
    Test 5: Date dans le futur doit être rejetée
    POST /api/import/csv → 200 OK avec errors
    """
    csv_content = """date,description,amount,category
    2099-12-31,Achat futur,50.00,Test"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 0
    assert data["skipped"] == 1
    assert "futur" in data["errors"][0].lower()


def test_import_csv_zero_amount(test_client):
    """
    Test 6: Montant = 0 doit être rejeté
    POST /api/import/csv → 200 OK avec errors
    """
    csv_content = """date,description,amount,category
    2025-01-15,Achat zéro,0.00,Test"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 0
    assert data["skipped"] == 1
    assert "0" in data["errors"][0]


def test_import_csv_invalid_amount(test_client):
    """
    Test 7: Montant non numérique doit être rejeté
    POST /api/import/csv → 200 OK avec errors
    """
    csv_content = """date,description,amount,category
    2025-01-15,Achat invalide,INVALIDE,Test"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 0
    assert data["skipped"] == 1
    assert "nombre" in data["errors"][0].lower()


def test_import_csv_missing_columns(test_client):
    """
    Test 8: Colonnes obligatoires manquantes
    POST /api/import/csv → 200 OK avec errors
    """
    csv_content = """date,description
    2025-01-15,Description sans montant"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 0
    assert data["skipped"] >= 1


def test_import_csv_empty_file(test_client):
    """
    Test 9: Fichier CSV vide doit être rejeté
    POST /api/import/csv → 400 Bad Request
    """
    files = {'file': ('test.csv', BytesIO(b''), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 400
    assert "vide" in response.json()["detail"].lower()


def test_import_csv_not_csv(test_client):
    """
    Test 10: Fichier non-CSV doit être rejeté
    POST /api/import/csv → 400 Bad Request
    """
    files = {'file': ('test.txt', BytesIO(b'test'), 'text/plain')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 400
    assert "csv" in response.json()["detail"].lower()


def test_import_csv_negative_amounts(test_client):
    """
    Test 11: Montants négatifs (remboursements) doivent être acceptés
    POST /api/import/csv → 200 OK
    """
    csv_content = """date,description,amount,category
    2025-01-15,Remboursement Sécu,-50.00,Santé
    2025-01-16,Remboursement,-25.00,Divers"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 2
    assert data["skipped"] == 0


def test_import_csv_mixed_valid_invalid(test_client):
    """
    Test 12: Fichier mixte (lignes valides + invalides)
    POST /api/import/csv → 200 OK avec rapport détaillé
    """
    csv_content = """date,description,amount,category
    2025-01-15,Valide 1,50.00,Test
    INVALIDE,Invalide,50.00,Test
    2025-01-16,Valide 2,30.00,Test
    2099-12-31,Date future,20.00,Test
    2025-01-17,Valide 3,40.00,Test"""
    
    files = {'file': ('test.csv', BytesIO(csv_content.encode('utf-8')), 'text/csv')}
    
    response = test_client.post("/api/import/csv", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["inserted"] == 3  # Lignes 2, 4, 6
    assert data["skipped"] == 2   # Lignes 3, 5
    assert len(data["errors"]) == 2