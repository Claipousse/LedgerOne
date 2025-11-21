'''
test_services.py - Tests unitaires pour les services (logique métier)
Vérifie que tous les calculs et validations fonctionnent correctement
'''

# SOMMAIRE DES TESTS

"""
CATEGORY SERVICE (7 tests)
1. Création valide
2. Nom dupliqué
3. Recherche par nom (trouvé)
4. Recherche par nom (non trouvé)
5. Modification
6. Suppression
7. Vérification existence

TRANSACTION SERVICE (10 tests)
8. Création valide
9. Catégorie invalide
10. Date future
11. Montant zéro
12. Calcul total mensuel
13. Filtre par catégorie
14. Répartition pourcentages
15. Transactions sans catégorie
16. Résumé mensuel complet
17. Pagination

SETTINGS SERVICE (3 tests)
18. Lecture paramètres
19. Modification budget
20. Budget négatif interdit

ALERT SERVICE (4 tests)
21. Aucune alerte
22. Alerte globale
23. Alerte catégorie
24. Alertes multiples
"""

# IMPORTS

import pytest # Framework de tests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker # Pour créer une DB temporaire
from app.database import Base
from app.models import Category, Transaction, Settings # Nos modèles
from datetime import date, datetime # Pour manipuler les dates

# Import de TOUS les services à tester
from app.services.category_service import (
    get_all_categories,
    get_category_by_id,
    get_category_by_name,
    create_category,
    update_category,
    delete_category,
    category_exists
)

from app.services.transaction_service import (
    get_all_transactions,
    get_transaction_by_id,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_monthly_total,
    get_category_breakdown,
    get_monthly_summary,
    get_transactions_by_month
)

from app.services.settings_service import (
    get_settings,
    update_settings,
    get_global_budget
)

from app.services.alert_service import (
    get_budget_alerts
)

from app.schemas import (
    CategoryCreate,
    CategoryUpdate,
    TransactionCreate,
    TransactionUpdate,
    SettingsUpdate
)


# CONFIGURATION PYTEST

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture qui crée une base de données temporaire pour chaque test
    Identique à test_models.py
    """
    # Créer DB en mémoire
    engine = create_engine("sqlite:///:memory:")
    
    # Créer toutes les tables
    Base.metadata.create_all(engine)
    
    # Créer session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Initialiser Settings (obligatoire pour les tests d'alertes)
    # Settings doit avoir l'ID 1 par défaut
    settings = Settings(id=1, global_monthly_budget=None)
    session.add(settings)
    session.commit()
    
    # Donner la session au test
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(engine)


# TESTS CATEGORY SERVICE
def test_create_category_service(db_session):
    """
    Test 1: Vérifie que create_category() crée correctement une catégorie
    Ce test vérifie la LOGIQUE, pas juste la DB
    """
    # Créer un schéma Pydantic valide
    category_data = CategoryCreate(
        name="Alimentation",
        color="#FF0000",
        monthly_budget=500.0
    )
    # Appeler le service (pas directement le modèle)
    category = create_category(db_session, category_data)
    
    # Vérifier que le service a bien créé la catégorie
    assert category.id is not None  # ID généré
    assert category.name == "Alimentation"
    assert category.color == "#FF0000"
    assert category.monthly_budget == 500.0


def test_create_category_duplicate_name(db_session):
    """
    Test 2: Vérifie qu'on ne peut pas créer 2 catégories avec le même nom
    Le service doit lever une ValueError (pas IntegrityError)
    """
    # Créer la première catégorie
    category_data1 = CategoryCreate(name="Transport")
    create_category(db_session, category_data1)
    
    # Créer une deuxième avec le même nom
    category_data2 = CategoryCreate(name="Transport")
    
    # Le service doit lever ValueError avec un message clair
    with pytest.raises(ValueError) as exc_info:
        create_category(db_session, category_data2)
    
    # Vérifier le message d'erreur
    assert "existe déjà" in str(exc_info.value)


def test_get_category_by_name(db_session):
    """
    Test 3: Vérifie que get_category_by_name() trouve une catégorie
    """
    category_data = CategoryCreate(name="Loisirs")
    created = create_category(db_session, category_data)
    
    found = get_category_by_name(db_session, "Loisirs")
    
    assert found is not None
    assert found.id == created.id
    assert found.name == "Loisirs"


def test_get_category_by_name_not_found(db_session):
    """
    Test 4: Vérifie que get_category_by_name() retourne None si pas trouvé
    """
    found = get_category_by_name(db_session, "Inexistant")
    
    assert found is None


def test_update_category_service(db_session):
    """
    Test 5: Vérifie que update_category() modifie correctement
    """
    # Créer une catégorie
    category_data = CategoryCreate(name="Transport", monthly_budget=200.0)
    category = create_category(db_session, category_data)
    
    # Préparer les modifications
    update_data = CategoryUpdate(
        name="Transport Modifié",
        monthly_budget=300.0
    )
    updated = update_category(db_session, category.id, update_data)
    
    assert updated is not None
    assert updated.id == category.id  # Même ID
    assert updated.name == "Transport Modifié"  # Nom changé
    assert updated.monthly_budget == 300.0  # Budget changé


def test_delete_category_service(db_session):
    """
    Test 6: Vérifie que delete_category() supprime correctement
    """
    category_data = CategoryCreate(name="Divers")
    category = create_category(db_session, category_data)
    
    success = delete_category(db_session, category.id)
    
    assert success is True
    
    # Vérifier que la catégorie n'existe plus
    found = get_category_by_id(db_session, category.id)
    assert found is None


def test_category_exists_service(db_session):
    """
    Test 7: Vérifie que category_exists() détecte correctement
    """
    category_data = CategoryCreate(name="Test")
    category = create_category(db_session, category_data)
    
    assert category_exists(db_session, category.id) is True
    assert category_exists(db_session, 99999) is False


# ============================================
#              TESTS TRANSACTION SERVICE
# ============================================

def test_create_transaction_service(db_session):
    """
    Test 8: Vérifie que create_transaction() crée correctement
    """
    # Créer une catégorie d'abord
    category = create_category(db_session, CategoryCreate(name="Alimentation"))
    
    # Créer les données de transaction
    transaction_data = TransactionCreate(
        date=date(2025, 1, 15),
        description="Courses Carrefour",
        amount=45.50,
        category_id=category.id
    )
    
    transaction = create_transaction(db_session, transaction_data)
    
    assert transaction.id is not None
    assert transaction.date == date(2025, 1, 15)
    assert transaction.description == "Courses Carrefour"
    assert transaction.amount == 45.50
    assert transaction.category_id == category.id
    assert transaction.created_at is not None


def test_create_transaction_invalid_category(db_session):
    """
    Test 9: Vérifie qu'on ne peut pas créer une transaction avec une catégorie inexistante
    Le service doit valider la FK avant d'insérer
    """
    transaction_data = TransactionCreate(
        date=date(2025, 1, 15),
        description="Test",
        amount=50.0,
        category_id=99999  # ❌ Catégorie inexistante
    )
    with pytest.raises(ValueError) as exc_info:
        create_transaction(db_session, transaction_data)
    
    assert "n'existe pas" in str(exc_info.value)


def test_create_transaction_future_date(db_session):
    """
    Test 10: Vérifie qu'on ne peut pas créer une transaction dans le futur
    """
    transaction_data = TransactionCreate(
        date=date(2099, 12, 31),  # ❌ Date future
        description="Test",
        amount=50.0
    )
    with pytest.raises(ValueError) as exc_info:
        create_transaction(db_session, transaction_data)
    
    assert "futur" in str(exc_info.value).lower()


def test_create_transaction_zero_amount(db_session):
    """
    Test 11: Vérifie qu'on ne peut pas créer une transaction avec montant = 0
    """
    transaction_data = TransactionCreate(
        date=date(2025, 1, 15),
        description="Test",
        amount=0.0  # ❌ Montant nul interdit
    )
    
    with pytest.raises(ValueError) as exc_info:
        create_transaction(db_session, transaction_data)
    
    assert "0" in str(exc_info.value)


def test_get_monthly_total_calculation(db_session):
    """
    Test 12: Vérifie que get_monthly_total() calcule correctement le total
    
    TEST CRITIQUE pour les calculs financiers
    """
    # Créer une catégorie
    category = create_category(db_session, CategoryCreate(name="Test"))
    
    # Créer 3 transactions en janvier 2025
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Achat 1",
        amount=100.0,
        category_id=category.id
    ))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 15),
        description="Achat 2",
        amount=50.50,
        category_id=category.id
    ))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 20),
        description="Achat 3",
        amount=25.25,
        category_id=category.id
    ))
    
    # Créer 1 transaction en février (ne doit PAS être comptée)
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 2, 5),
        description="Achat 4",
        amount=999.0,  # <- Ne doit PAS être dans le total
        category_id=category.id
    ))
    
    total = get_monthly_total(db_session, 2025, 1)
    
    # 100.0 + 50.50 + 25.25 = 175.75 (pas 999 de février)
    assert total == 175.75


def test_get_monthly_total_with_category_filter(db_session):
    """
    Test 13: Vérifie que le filtre par catégorie fonctionne
    """
    
    # Créer 2 catégories
    cat1 = create_category(db_session, CategoryCreate(name="Alimentation"))
    cat2 = create_category(db_session, CategoryCreate(name="Transport"))
    
    # Transactions catégorie 1
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Courses",
        amount=100.0,
        category_id=cat1.id
    ))
    
    # Transactions catégorie 2
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 15),
        description="Essence",
        amount=50.0,
        category_id=cat2.id
    ))
    
    total_cat1 = get_monthly_total(db_session, 2025, 1, cat1.id)
    total_cat2 = get_monthly_total(db_session, 2025, 1, cat2.id)
    total_all = get_monthly_total(db_session, 2025, 1)
    
    assert total_cat1 == 100.0  # Seulement catégorie 1
    assert total_cat2 == 50.0   # Seulement catégorie 2
    assert total_all == 150.0   # Les deux


def test_get_category_breakdown_percentages(db_session):
    """
    Test 14: Vérifie que les pourcentages sont corrects
    TEST CRITIQUE pour l'affichage du camembert
    """
    
    # Créer 3 catégories
    cat1 = create_category(db_session, CategoryCreate(name="Alimentation"))
    cat2 = create_category(db_session, CategoryCreate(name="Transport"))
    cat3 = create_category(db_session, CategoryCreate(name="Loisirs"))
    
    # Total = 1000€
    # Alimentation: 500€ (50%)
    # Transport: 300€ (30%)
    # Loisirs: 200€ (20%)
    
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Courses",
        amount=500.0,
        category_id=cat1.id
    ))
    
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 15),
        description="Essence",
        amount=300.0,
        category_id=cat2.id
    ))
    
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 20),
        description="Cinéma",
        amount=200.0,
        category_id=cat3.id
    ))
    
    breakdown = get_category_breakdown(db_session, 2025, 1)
    
    assert breakdown["Alimentation"]["total"] == 500.0
    assert breakdown["Alimentation"]["percentage"] == 50.0
    
    assert breakdown["Transport"]["total"] == 300.0
    assert breakdown["Transport"]["percentage"] == 30.0
    
    assert breakdown["Loisirs"]["total"] == 200.0
    assert breakdown["Loisirs"]["percentage"] == 20.0


def test_get_category_breakdown_with_uncategorized(db_session):
    """
    Test 15: Vérifie que les transactions sans catégorie sont dans "Sans catégorie"
    """
    
    # Transaction avec catégorie
    cat = create_category(db_session, CategoryCreate(name="Test"))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Avec catégorie",
        amount=100.0,
        category_id=cat.id
    ))
    
    # Transaction SANS catégorie
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 15),
        description="Sans catégorie",
        amount=50.0,
        category_id=None  # <- Pas de catégorie
    ))
    
    breakdown = get_category_breakdown(db_session, 2025, 1)
    
    assert "Test" in breakdown
    assert "Sans catégorie" in breakdown
    
    assert breakdown["Test"]["total"] == 100.0
    assert breakdown["Sans catégorie"]["total"] == 50.0


def test_get_monthly_summary(db_session):
    """
    Test 16: Vérifie que get_monthly_summary() retourne toutes les infos
    """
    
    cat = create_category(db_session, CategoryCreate(name="Alimentation"))
    
    # Créer 3 transactions
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Achat 1",
        amount=100.0,
        category_id=cat.id
    ))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 15),
        description="Achat 2",
        amount=200.0,
        category_id=cat.id
    ))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 20),
        description="Achat 3",
        amount=300.0,
        category_id=cat.id
    ))
    
    summary = get_monthly_summary(db_session, 2025, 1)
    
    assert summary["total"] == 600.0  # 100 + 200 + 300
    assert summary["count"] == 3
    assert summary["average"] == 200.0  # 600 / 3
    assert "by_category" in summary
    assert "Alimentation" in summary["by_category"]


# TESTS SETTINGS SERVICE

def test_get_settings_service(db_session):
    """
    Test 17: Vérifie que get_settings() retourne les paramètres
    """
    settings = get_settings(db_session)
    
    assert settings is not None
    assert settings.id == 1
    assert settings.global_monthly_budget is None  # Valeur par défaut


def test_update_settings_service(db_session):
    """
    Test 18: Vérifie que update_settings() modifie le budget global
    """
    update_data = SettingsUpdate(global_monthly_budget=2000.0)
    
    updated = update_settings(db_session, update_data)
    
    assert updated.global_monthly_budget == 2000.0
    
    # Vérifier que c'est bien persisté
    settings = get_settings(db_session)
    assert settings.global_monthly_budget == 2000.0


def test_update_settings_negative_budget(db_session):
    """
    Test 19: Vérifie qu'on ne peut pas mettre un budget négatif
    """
    from pydantic import ValidationError
    with pytest.raises(ValueError):
        update_data = SettingsUpdate(global_monthly_budget=-500.0)


# TESTS ALERT SERVICE

def test_get_budget_alerts_no_alerts(db_session):
    """
    Test 20: Vérifie qu'aucune alerte n'est retournée si pas de dépassement
    """
    # Définir un budget global de 1000€
    update_settings(db_session, SettingsUpdate(global_monthly_budget=1000.0))
    
    # Créer une catégorie avec budget de 500€
    cat = create_category(db_session, CategoryCreate(
        name="Alimentation",
        monthly_budget=500.0
    ))
    
    # Dépenser seulement 400€ (pas de dépassement)
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Courses",
        amount=400.0,
        category_id=cat.id
    ))
    alerts = get_budget_alerts(db_session, 2025, 1)

    assert len(alerts["alerts"]) == 0  # Aucune alerte


def test_get_budget_alerts_global_exceeded(db_session):
    """
    Test 21: Vérifie que l'alerte globale est détectée
    TEST CRITIQUE pour le système d'alertes
    """
    # Budget global: 1000€
    update_settings(db_session, SettingsUpdate(global_monthly_budget=1000.0))
    
    cat = create_category(db_session, CategoryCreate(name="Test"))
    
    # Dépenser 1200€ (dépassement de 200€)
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Grosse dépense",
        amount=1200.0,
        category_id=cat.id
    ))
    
    alerts = get_budget_alerts(db_session, 2025, 1)
    
    assert len(alerts["alerts"]) == 1
    
    alert = alerts["alerts"][0]
    assert alert["scope"] == "global"
    assert alert["budget"] == 1000.0
    assert alert["actual"] == 1200.0
    assert alert["delta"] == 200.0


def test_get_budget_alerts_category_exceeded(db_session):
    """
    Test 22: Vérifie que l'alerte par catégorie est détectée
    """
    # Catégorie avec budget de 500€
    cat = create_category(db_session, CategoryCreate(
        name="Loisirs",
        monthly_budget=500.0
    ))
    
    # Dépenser 650€ (dépassement de 150€)
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Dépense 1",
        amount=400.0,
        category_id=cat.id
    ))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 15),
        description="Dépense 2",
        amount=250.0,
        category_id=cat.id
    ))
    
    alerts = get_budget_alerts(db_session, 2025, 1)
    
    assert len(alerts["alerts"]) == 1
    
    alert = alerts["alerts"][0]
    assert alert["scope"] == "category"
    assert alert["category"] == "Loisirs"
    assert alert["budget"] == 500.0
    assert alert["actual"] == 650.0
    assert alert["delta"] == 150.0


def test_get_budget_alerts_multiple_alerts(db_session):
    """
    Test 23: Vérifie que plusieurs alertes peuvent être retournées
    """
    # Budget global: 1000€
    update_settings(db_session, SettingsUpdate(global_monthly_budget=1000.0))
    
    # 2 catégories avec budgets dépassés
    cat1 = create_category(db_session, CategoryCreate(
        name="Alimentation",
        monthly_budget=300.0
    ))
    cat2 = create_category(db_session, CategoryCreate(
        name="Transport",
        monthly_budget=200.0
    ))
    
    # Dépasser tous les budgets
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 10),
        description="Courses",
        amount=400.0,  # Dépasse 300€
        category_id=cat1.id
    ))
    create_transaction(db_session, TransactionCreate(
        date=date(2025, 1, 15),
        description="Essence",
        amount=700.0,  # Dépasse 200€ + dépasse global
        category_id=cat2.id
    ))
    
    alerts = get_budget_alerts(db_session, 2025, 1)
    
    # 3 alertes: global + 2 catégories
    assert len(alerts["alerts"]) == 3
    
    scopes = [a["scope"] for a in alerts["alerts"]]
    assert "global" in scopes
    assert scopes.count("category") == 2


# TESTS DE PAGINATION

def test_get_all_transactions_pagination(db_session):
    """
    Test 24: Vérifie que la pagination fonctionne
    """
    cat = create_category(db_session, CategoryCreate(name="Test"))
    
    # Créer 25 transactions
    for i in range(25):
        create_transaction(db_session, TransactionCreate(
            date=date(2025, 1, 1),
            description=f"Transaction {i}",
            amount=10.0,
            category_id=cat.id
        ))
    
    # Page 1 (10 premiers)
    page1 = get_all_transactions(db_session, skip=0, limit=10)
    
    # Page 2 (10 suivants)
    page2 = get_all_transactions(db_session, skip=10, limit=10)
    
    # Page 3 (5 derniers)
    page3 = get_all_transactions(db_session, skip=20, limit=10)
    
    # ASSERT
    assert len(page1) == 10
    assert len(page2) == 10
    assert len(page3) == 5


# ============================================
#              RÉSUMÉ DES TESTS
# ============================================

"""
RÉSUMÉ DES 24 TESTS :

CATEGORY SERVICE (7 tests)
1. Création valide
2. Nom dupliqué
3. Recherche par nom (trouvé)
4. Recherche par nom (non trouvé)
5. Modification
6. Suppression
7. Vérification existence

TRANSACTION SERVICE (10 tests)
8. Création valide
9. Catégorie invalide
10. Date future
11. Montant zéro
12. Calcul total mensuel
13. Filtre par catégorie
14. Répartition pourcentages
15. Transactions sans catégorie
16. Résumé mensuel complet
17. Pagination

SETTINGS SERVICE (3 tests)
18. Lecture paramètres
19. Modification budget
20. Budget négatif interdit

ALERT SERVICE (4 tests)
21. Aucune alerte
22. Alerte globale
23. Alerte catégorie
24. Alertes multiples
"""