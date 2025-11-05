'''
Service de gestion des catégories
Contient toutes la logique métier pour les opérations CRUD sur les catégories
'''

from sqlalchemy.orm import Session #Pour prendre en paramètre une session SQL
from sqlalchemy.exc import IntegrityError #Savoir quand une contrainte SQL est violée, permet de capturer erreur comme un nom déjà utilisé, ou budget <0
from typing import List, Optional #Pour liste d'objets Category, Optional pour "un objet category ou none"
from app.models.category import Category #Pour créer/manipuler des catégories
from app.schemas.category import CategoryCreate, CategoryUpdate #Pour valider données lors de création/modification

def get_all_categories(db:Session) -> List[Category]:
    """
    Récupère toutes les catégories de la base de données
    Args: db: Session de base de données SQLAlchemy
    Retourne liste de tous les objets Category
    """
    return db.query(Category).all()

def get_category_by_id(db:Session, category_id:int) -> Optional[Category]:
    # Récupère une catégorie par son ID, retourne None si introuvable
    return db.query(Category).filter(Category.id == category_id).first()

def get_category_by_name(db:Session, category_name:str) -> Optional[Category]:
    #On cherche une catégorie par son nom, return category si trouvé sinon None
    return db.query(Category).filter(Category.name == category_name).first()

def create_category(db:Session, category_data: CategoryCreate) -> Category:
    '''
    Crée une nouvelle catégorie dans la DB
    Prend en paramètre la session & schéma CatgoryCreate
    Retourne l'objet Category crée
    On check aussi si une catégorie du même nom existe déjà
    '''

    #On check si une categorie du même nom existe déjà
    existing_category = get_category_by_name(db, category_data.name)
    if existing_category:
        raise ValueError(f"Une catégorie avec le nom '{category_data.name}' existe déjà")

    #Créer l'objet Category avec les données Pydantic
    new_category = Category(name = category_data.name, color = category_data.color, monthly_budget = category_data.monthly_budget)

    try:
        db.add(new_category) #Ajouter à la session (file d'attente)
        db.commit() #Sauvegarder dans la base de données
        db.refresh(new_category) #Recharger l'objet depuis la DB pour obtenir l'ID généré
        return new_category

    except IntegrityError as e:
        #Si il y a une erreur, comme contrainte violée, on annule les changements (exemple budget saisit <0, limite de caractère dépassé, ...)
        db.rollback()
        raise ValueError(f"Erreur lors de la création de la catégorie: {str(e)}")

def update_category(db:Session, category_id:int, category_data:CategoryUpdate) -> Optional[Category]:
    '''
    Met à jour une catégorie qui existe déjà
    Prend en arguments session, ID de la catégorie à modifier, Nouvelles données
    Return l'objetmodifié si trouvé, None sinon
    '''
    category = get_category_by_id(db, category_id) #On cherche la catégorie par son ID
    if not category:
        return None #Si pas trouvé, on return None
    
    #Vérifier si le nouveau nom existe déjà pour éviter doublon
    if category_data.name is not None and category_data.name != category.name: #On check si on veut changer de nom
        existing_category = get_category_by_name(db, category_data.name)
        if existing_category:
            raise ValueError(f"Une catégorie avec le nom '{category_data.name}' existe déjà")
    
    #Mettre à jour uniquement les champs fournis (exclude_unset=True)
    update_data = category_data.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(category, field, value)
    try:
        db.commit() #Sauvegarder les modif
        db.refresh(category) #Recharger la DB
        return category #Retourne catégorie modifiée
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Erreur lors de la mise à jour: {str(e)}")
    
def delete_category(db:Session, category_id:int) -> bool:
    '''
    Supprime une catégorie
    Prend en paramètre la session et l'id de la catégorie à delete
    True si réussi, False si pas trouvé
    Les transactions liées à la catégorie supprimées auront leur category_id set à NULL (CASCADE SET NULL)
    '''
    category = get_category_by_id(db, category_id)

    if not category:
        return False #Si pas trouvé

    try:
        db.delete(category)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise ValueError(f"Erreur lors de la suppression: {str(e)}")

def category_exists(db: Session, category_id:int) -> bool:
    '''
    Vérifie si une catégorie existe via son ID
    Prend en parametre la session & id de la catégorie à trouver
    True si existe, sinon False
    Sera utilisé pour les transactions, pour pas associer une transaction à une catégorie qui existe pas
    '''
    return get_category_by_id(db, category_id) is not None