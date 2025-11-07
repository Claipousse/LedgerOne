'''
Service de gestion des transactions
Contient toute la logique métier pour les opérations CRUD sur les transactions
Gère également les filtres, recherche, calculs et agrégations
'''
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError #Pour gérer les violations de contraintes
from sqlalchemy import func, and_, or_, extract #Fonctions SQL, opérateurs logiques pour combiner filtres & extraire année/mois/jour d'une date
from typing import date, datetime, timedelta #Manipulation de dates, calcul d'intervales (ex: il y a 3 mois)
from calendar import monthrange #Savoir combien de jours dans le mois

from app.models.transaction import Transaction
from app.models.category import Category
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.category_service import category_exists #Pour valider les Foreign Keys

# =================================================================
#                          CRUD DE BASE
# =================================================================

def get_all_transactions(db:Session, skip:int=0, limit:int=100) -> List[Transaction]:
    '''
    Sert à retourner la liste de toutes les transactions de la DB
    Comme il peut y avoir potentiellement énormément de transactions, faut être malin sur le chargement des données
    Sinon si on charge tout d'un coup sur un grand échantillon, ça va prendre beaucoup de temps et les performances vont en patir
    Pour ça, on charge les données par pages de 100 (via limit)
    Puis, on charge la suite en recommençant le procédé mais en incrémentant skip de 100 * n (ignore les 100 * n premiers résultats, soit les résultats déjà chargés)
    On répète ce procédé n fois jusqu'à ce que toutes les données soient chargés, à la fin on retourne une liste de transactions
    '''
    #On cherche toutes les transactions, tri décroissant (pour avoir les plus récentes en première)
    return db.query(Transaction).order_by(Transaction.date.desc()).offset(skip).limit(limit).all()

def get_transaction_by_id(db:Session, transaction_id:int) -> Optional[Transaction]:
    '''
    Récupère une transaction via son ID
    Retourne Transaction si trouvé, sinon None
    '''
    return db.query(Transaction).filter(Transaction.id == transaction_id).first() #First car ID est unique, donc pas besoin de chercher plus dès qu'on a trouvé

def create_transaction(db:Session, transaction_data: TransactionCreate) -> Transaction: #transaction_data = Schéma Pydantic avec données validées
    '''
    Crée une nouvelle transaction dans la BDD
    Retourne un objet Transaction avec son ID généré, ValueError si catégorie FK n'existe pas ou données invalides
    '''
    #Vérification 1 : Vérifier que catégorie existe (si fournie)
    if transaction_data.category_id is not None:
        if not category_exists(db, transaction_data.category_id):
            raise ValueError(f"La catégorie {transaction_data.category_id} n'existe pas")
    
    #Vérification 2 : Date est correcte (pas de date dans le futur)
    if transaction_data.date > date.today():
        raise ValueError(f"La date ne peut pas être dans le futur")
    
    #Vérification 3 : Vérifier que le montant n'est pas exactement 0
    if transaction_data.amount == 0:
        raise ValueError(f"Le montant ne peux pas être égal à 0")
    
    #Si tout bon, on peut créer l'objet Transaction
    new_transaction = Transaction(
        date = transaction_data.date,
        description = transaction_data.description,
        amount = transaction_data.amount,
        category_id = transaction_data.category_id
    )

    try:
        db.add(new_transaction) #Ajouter à la session
        db.commit() #Sauvegarde dans DB
        db.refresh(new_transaction) #Recharger objet pour avoir ID + created_at générés
        return new_transaction
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Erreur lors de la création de la transaction: {str(e)}")
    
def update_transaction(db: Session, transaction_id: int, transaction_data: TransactionUpdate) -> Optional[Transaction]:
    '''
    Met à jour une transaction existante
    Prend en parametre l'ID de la transaction à modifier et les nouvelles données (schéma Pydantic, optionnel)
    Retourne Transaction modifiée, None si pas trouvée
    '''
    #Récupérer la transaction existante
    transaction = get_transaction_by_id(db, transaction_id)
    if not transaction:
        return None
    
    #Vérifier la nouvelle catégorie (si fournie)
    if transaction_data.category_id is not None:
        if not category_exists(db, transaction_data.category_id):
            raise ValueError(f"La catégorie {transaction_data.category_id} n'existe pas")
        
    #Vérifier la nouvelle date (si fournie)
    if transaction_data.date is not None and transaction_data.date > date.today():
        raise ValueError("La date ne peut pas être dans le futur")
    
    #Vérifier le nouveau montant (si fourni)
    if transaction_data.amount is not None and transaction_data.amount == 0:
        raise ValueError("Le montant ne peut pas être exactement 0")
    
    #Met à jour les champs fournis
    update_data = transaction_data.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    try:
        db.commit()
        db.refresh(transaction)
        return transaction
    
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Erreur lors de la mise à jour : {str(e)}")

def delete_transaction(db: Session, transaction_id: int) -> bool:
    """
    Supprime une transaction de la base de données
    Retourne True si suppression réussie, False si transaction non trouvée
    """
    transaction = get_transaction_by_id(db, transaction_id)
    if not transaction:
        return False
    try:
        db.delete(transaction) # Supprimer la transaction
        db.commit() # Sauvegarder la suppression
        return True
        
    except Exception as e:
        db.rollback()
        raise ValueError(f"Erreur lors de la suppression: {str(e)}")
    

# =================================================================
#                       FONCTIONS DE FILTRAGE
# =================================================================

def get_transactions_by_period(db:Session, from_date:date, to_date:date,category_id:Optional[int] = None, skip:int = 0, limit:int = 100) -> List[Transaction]:
    '''
    Récupère transactions d'une période donnée ([from_date, to_date])
    skip & limit pour pagination & categorie_id pour filtre par catégorie (optionnel)
    Retourne liste filtrée de transactions par date décroissante
    '''
    query = db.query(Transaction) #Construire requête de base
    query = query.filter(Transaction.date >= from_date) #Filtre 1 : Date >= from_date (>= date de début incluse)
    query = query.filter(Transaction.date <= to_date) #Filtre 2 : Date <= to_date (<= date de fin incluse)
    if category_id is not None : query = query.filter(Transaction.category_id == category_id) #Filtre 3 : Catégorie (optionnel)
    
    #Tri par date décroissante et pagination
    return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()

def search_transactions(db:Session, search_query:str, skip:int = 0, limit: int = 100) -> List[Transaction]:
    '''
    Recherche transactions par mot-clé dans la description
    search_query: texte à chercher dans les descriptions
    Retourne liste des transactions dont la description contient le texte en paramètre
    '''
    #Retourne liste filtrée par ordre chronologique (+ récent d'abord), avec le texte recherché dans les descriptions
    return db.query(Transaction).filter(Transaction.description.ilike(f"%{search_query}%")).order_by(Transaction.date.desc()).offset(skip).limit(limit).all()

def get_transactions_by_month(db:Session, year:int, month:int, category_id: Optional[int] = None) -> List[Transaction]:
    '''
    Récupère toutes les transactions d'un mois donné (avec la bonne année)
    category_id si on veut aussi filtré selon la catégorie de la transaction (optionnel)
    Retourne liste de transactions du mois spécifié
    '''
    first_day = date(year, month, 1) #Calcul premier jour du mois
    
    _, last_day_num = monthrange(year, month) #Calculer le dernier jour du mois
    last_day = date(year, month, last_day_num)

    #Utiliser get_transactions_by_period()
    return get_transactions_by_period(
        db,
        from_date=first_day,
        to_date=last_day,
        category_id=category_id,
        skip=0,
        limit=5000000 #Pas de limite pour un mois, donc on met une limite très grande pour jamais l'atteindre
    )

