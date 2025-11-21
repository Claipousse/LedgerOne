'''
test_models.py - Tests pour les modèles SQLAlchemy
Vérifie que les tables, contraintes et relations fonctionnent bien
'''

# IMPORTS

import pytest # framework de tests Python, permet de créer des fonctions de tests et d'utiliser des assertions
from sqlalchemy import create_engine # Crée une connexion à la DB, crée une DB temporaire pour le test
from sqlalchemy.orm import sessionmaker # Fabrique sessions pour intéragir avec DB, session = conversation avec DB
from sqlalchemy.exc import IntegrityError # Erreur levée quand une contrainte SQL violée, Ex : UNIQUE, CHECK, NOT NULL, FK
from app.database import Base # Base = class parente de tous les modèles, permet de créer tables à partir des modèles
from app.models import Category, Transaction, Settings # Les 3 modèles SQLAlchemy crées
from datetime import date #Pour manipuler dates dans les tests


# CONFIGURATION DU PYTEST

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture pytest qui crée une base de données temporaire pour chaque test
    
    @pytest.fixture = fonction spéciale pytest appelée avant chaque test
    scope="function" = une nouvelle DB pour CHAQUE test (isolation complète)
    
    Workflow:
    1. Créer une DB SQLite en mémoire (très rapide)
    2. Créer toutes les tables
    3. Donner la session au test
    4. Après le test : tout supprimer
    """
    
    # Créer un moteur SQLite EN MÉMOIRE (pas de fichier)
    # :memory: = base de données temporaire, disparaît après l'exécution
    engine = create_engine("sqlite:///:memory:")
    
    # Créer toutes les tables définies dans nos modèles
    # Base.metadata contient la définition de toutes les tables
    Base.metadata.create_all(engine)
    
    # Créer une fabrique de sessions liée à ce moteur
    Session = sessionmaker(bind=engine)
    
    # Créer une session concrète
    session = Session()
    
    # yield = "pause" la fonction et donne la session au test
    # Le test s'exécute ici avec la session
    yield session
    
    # Après le test, on reprend ici (cleanup)
    session.close()  # Fermer la session
    Base.metadata.drop_all(engine)  # Supprimer toutes les tables


# TESTS CATEGORY

def test_create_category_success(db_session):
    """
    Test 1: Vérifie qu'on peut créer une catégorie valide
    
    db_session = la session de DB fournie par la fixture ci-dessus
    """
    
    # ARRANGE (Préparer)
    # Créer un objet Category avec des valeurs valides
    category = Category(
        name="Alimentation",          # Nom unique
        color="#FF0000",               # Couleur rouge
        monthly_budget=500.0           # Budget positif
    )
    
    # ACT (Agir)
    # Ajouter la catégorie à la session (file d'attente)
    db_session.add(category)
    
    # Sauvegarder dans la base de données
    # commit() = exécute l'INSERT SQL
    db_session.commit()
    
    # Recharger l'objet depuis la DB pour obtenir l'ID généré
    db_session.refresh(category)
    
    # ASSERT (Vérifier)
    # assert = si False, le test échoue
    
    # Vérifier que l'ID a été généré automatiquement
    assert category.id is not None, "L'ID devrait être généré automatiquement"
    
    # Vérifier que les valeurs sont bien enregistrées
    assert category.name == "Alimentation"
    assert category.color == "#FF0000"
    assert category.monthly_budget == 500.0
    
def test_category_name_unique(db_session):
    """
    Test 2: Vérifie qu'on ne peut pas créer 2 catégories avec le même nom
    Teste la contrainte: name UNIQUE
    """
    # Créer la première catégorie
    category1 = Category(name="Transport")
    db_session.add(category1)
    db_session.commit()  # ✅ Succès
    
    # Créer une deuxième catégorie avec le MÊME nom
    category2 = Category(name="Transport")  # Doublon
    db_session.add(category2)
    
    # with pytest.raises(IntegrityError) = "je m'attends à une erreur"
    # Si aucune erreur n'est levée, le test échoue
    with pytest.raises(IntegrityError):
        db_session.commit()  # Doit lever IntegrityError (UNIQUE violation)


def test_category_budget_cannot_be_negative(db_session):
    """
    Test 3: Vérifie qu'on ne peut pas créer une catégorie avec un budget négatif
    Teste la contrainte: CHECK (monthly_budget >= 0)
    """
    
    # Créer une catégorie avec un budget négatif
    category = Category(
        name="Test",
        monthly_budget=-100.0  # Négatif interdit
    )
    db_session.add(category)
    
    # La contrainte CHECK doit bloquer
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_category_budget_can_be_null(db_session):
    """
    Test 4: Vérifie qu'on peut créer une catégorie SANS budget
    monthly_budget est optionnel (nullable=True)
    """
    category = Category(
        name="Loisirs",
        monthly_budget=None  # NULL autorisé
    )
    
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    
    assert category.id is not None
    assert category.monthly_budget is None  # Budget non défini


def test_category_color_optional(db_session):
    """
    Test 5: Vérifie que la couleur est optionnelle
    """
    
    category = Category(
        name="Divers",
        color=None  # Couleur optionnelle
    )
    
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    
    assert category.id is not None
    assert category.color is None
    

# TESTS TRANSACTION

def test_create_transaction_success(db_session):
    """
    Test 6: Vérifie qu'on peut créer une transaction valide
    """
    # D'abord créer une catégorie (pour la FK)
    category = Category(name="Transport")
    db_session.add(category)
    db_session.commit()
    
    # Créer une transaction liée à cette catégorie
    transaction = Transaction(
        date=date(2025, 1, 15),         # Date ISO
        description="Essence Shell",
        amount=60.50,                   # Montant positif
        category_id=category.id         # FK vers categories
    )
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    assert transaction.id is not None
    assert transaction.date == date(2025, 1, 15)
    assert transaction.description == "Essence Shell"
    assert transaction.amount == 60.50
    assert transaction.category_id == category.id
    assert transaction.created_at is not None  # Auto-généré


def test_transaction_without_category(db_session):
    """
    Test 7: Vérifie qu'on peut créer une transaction SANS catégorie
    category_id est optionnel (nullable=True)
    """
    
    transaction = Transaction(
        date=date(2025, 1, 15),
        description="Paiement divers",
        amount=25.0,
        category_id=None  # Pas de catégorie
    )
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    assert transaction.id is not None
    assert transaction.category_id is None


def test_transaction_negative_amount_allowed(db_session):
    """
    Test 8: Vérifie qu'on peut créer une transaction avec un montant négatif
    Les montants négatifs = remboursements (valide)
    """
    
    transaction = Transaction(
        date=date(2025, 1, 15),
        description="Remboursement Sécu",
        amount=-50.0  # Négatif autorisé (remboursement)
    )
    
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    
    assert transaction.id is not None
    assert transaction.amount == -50.0


def test_delete_category_sets_transaction_null(db_session):
    """
    Test 9: Vérifie que supprimer une catégorie met les transactions à NULL
    Teste la contrainte: FK avec ondelete="SET NULL"
    """
    # Créer une catégorie et une transaction
    category = Category(name="Loisirs")
    db_session.add(category)
    db_session.commit()
    
    transaction = Transaction(
        date=date(2025, 1, 15),
        description="Cinéma",
        amount=15.0,
        category_id=category.id
    )
    db_session.add(transaction)
    db_session.commit()
    
    # Vérifier que la transaction a bien une catégorie
    assert transaction.category_id == category.id
    
    # Supprimer la catégorie
    db_session.delete(category)
    db_session.commit()
    
    # Recharger la transaction depuis la DB
    db_session.refresh(transaction)
    
    # La transaction doit toujours exister
    assert transaction.id is not None
    
    # Mais la catégorie est NULL (ondelete="SET NULL")
    assert transaction.category_id is None


def test_transaction_relationship_with_category(db_session):
    """
    Test 10: Vérifie que la relation bidirectionnelle fonctionne
    Transaction.category <-> Category.transactions
    """
    category = Category(name="Alimentation")
    db_session.add(category)
    db_session.commit()
    
    # Créer 2 transactions pour cette catégorie
    tx1 = Transaction(
        date=date(2025, 1, 10),
        description="Courses",
        amount=50.0,
        category_id=category.id
    )
    tx2 = Transaction(
        date=date(2025, 1, 15),
        description="Restaurant",
        amount=35.0,
        category_id=category.id
    )
    db_session.add_all([tx1, tx2])
    db_session.commit()
    
    # Accès depuis la transaction vers la catégorie
    db_session.refresh(tx1)
    assert tx1.category.name == "Alimentation"  # Relation fonctionne
    
    # Accès depuis la catégorie vers les transactions
    db_session.refresh(category)
    assert len(category.transactions) == 2  # 2 transactions liées
    assert tx1 in category.transactions
    assert tx2 in category.transactions
    

# TESTS SETTINGS

def test_create_settings_success(db_session):
    """
    Test 11: Vérifie qu'on peut créer l'enregistrement Settings
    """
    settings = Settings(
        id=1,  # ID forcé à 1
        global_monthly_budget=2000.0
    )
    
    db_session.add(settings)
    db_session.commit()
    db_session.refresh(settings)
    
    assert settings.id == 1
    assert settings.global_monthly_budget == 2000.0
    assert settings.updated_at is not None  # Auto-généré


def test_settings_budget_cannot_be_negative(db_session):
    """
    Test 12: Vérifie que le budget global ne peut pas être négatif
    Teste la contrainte: CHECK (global_monthly_budget >= 0)
    """
    settings = Settings(
        id=1,
        global_monthly_budget=-500.0  # Négatif interdit
    )
    db_session.add(settings)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_settings_only_one_row(db_session):
    """
    Test 13: Vérifie qu'on ne peut créer qu'UNE SEULE ligne de settings
    Teste la contrainte: CHECK (id = 1)
    """
    # Première ligne avec id=1
    settings1 = Settings(id=1, global_monthly_budget=2000.0)
    db_session.add(settings1)
    db_session.commit()
    
    # Deuxième ligne avec id=2
    settings2 = Settings(id=2, global_monthly_budget=3000.0)
    db_session.add(settings2)
    
    # La contrainte CHECK (id = 1) doit bloquer
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_settings_budget_can_be_null(db_session):
    """
    Test 14: Vérifie que le budget global peut être NULL
    """
    settings = Settings(
        id=1,
        global_monthly_budget=None  # NULL autorisé
    )
    db_session.add(settings)
    db_session.commit()
    db_session.refresh(settings)
    
    assert settings.id == 1
    assert settings.global_monthly_budget is None


#TESTS DES INDEX

def test_category_name_indexed(db_session):
    """
    Test 15: Vérifie que l'index sur category.name accélère les recherches
    Note: Test conceptuel, SQLite gère les index automatiquement
    """
    # Créer 100 catégories
    for i in range(100):
        cat = Category(name=f"Categorie_{i}")
        db_session.add(cat)
    db_session.commit()
    
    # Rechercher par nom (utilise l'index)
    result = db_session.query(Category).filter(
        Category.name == "Categorie_50"
    ).first()
    
    assert result is not None
    assert result.name == "Categorie_50"


def test_transaction_date_indexed(db_session):
    """
    Test 16: Vérifie que l'index sur transaction.date accélère les recherches
    """
    # Créer 100 transactions avec des dates différentes
    for i in range(100):
        tx = Transaction(
            date=date(2025, 1, i % 28 + 1),  # Jours de 1 à 28
            description=f"Transaction {i}",
            amount=50.0
        )
        db_session.add(tx)
    db_session.commit()
    
    # Rechercher par date (utilise l'index)
    results = db_session.query(Transaction).filter(
        Transaction.date == date(2025, 1, 15)
    ).all()
    
    assert len(results) > 0
    assert all(tx.date == date(2025, 1, 15) for tx in results)