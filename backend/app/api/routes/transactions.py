'''
Router Transactions - Endpoints pour la gestion des transactions
Contient tous les endpoints CRUD pour les transactions avec filtres & pagination
'''

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query #Pour création de routeur, injection dépendances, lever erreurs http & codes http (200, 404, ...)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db #Pour fournir la session DB
from app.services import ( #Fournit la logique métier pour transactions
    get_all_transactions,
    get_transaction_by_id,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_transactions_by_period,
    search_transactions
)
from app.schemas import TransactionCreate, TransactionUpdate, TransactionResponse #Pour validation des données

router = APIRouter( #Créer le router pour les transactions
    prefix="/transactions", #Toutes les routes auront /transactions au début
    tags=["Transactions"] #Groupe les endpoints dans la doc auto
)

#Endpoints : Lister TOUTES les transactions avec filtres et pagination
@router.get("/", response_model=List[TransactionResponse], status_code=status.HTTP_200_OK)
def list_transactions(
    skip:int = Query(0, ge=0, description="Nombre de résultats à ignorer (pagination)"),
    limit:int = Query(100, ge=1, description="Nombre max de résultats à retourner"),
    from_date: Optional[date] = Query(None, description="Date de début (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, description="Date de fin (YYYY-MM-DD)"),
    category_id: Optional[int] = Query(None, ge=1, description="Filtrer par ID de catégorie"),
    search: Optional[str] = Query(None, min_length=1, description="Rechercher dans les descriptions"),
    db: Session = Depends(get_db)
    #Avec query on peut avoir ce genre d'url par exemple : GET /api/transactions/?skip=10&limit=50&from_date=2025-01-01&to_date=2025-01-31&category_id=3
):
    '''
    Liste les transactions avec filtres optionnels et pagination

     Paramètres de pagination:
    - skip: nombre de résultats à sauter (défaut: 0)
    - limit: nombre max de résultats (100)
    
    Filtres optionnels:
    - from_date: date de début (incluse)
    - to_date: date de fin (incluse)
    - category_id: filtrer par catégorie
    - search: recherche textuelle dans les descriptions
    
    Retourne List[TransactionResponse]: liste filtrée de transactions
    '''
    #Cas 1: Recherche textuelle (prioritaire)
    if search:
        return search_transactions(db, search, skip, limit)
    
    #Cas 2: Filtrage par période
    if from_date or to_date:
        #Gérer les dates par défaut si une seule est fournie
        if from_date and not to_date:
            to_date = date.today() #Si on précise juste la date de début, la date de fin est la date de aujourd'hui
        if to_date and not from_date:
            from_date = date(1900, 1, 1) #Si on a que la date de fin, on prend toutes les transactions avant cette date

        #Validation: from_date <= to_date
        if from_date > to_date:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail="La date de début doit être antérieure ou égale à la date de fin"
            )
        return get_transactions_by_period(db, from_date, to_date, category_id, skip, limit)
        
    #Cas 3: Filtrage simple par catégorie (sans période)
    if category_id:
        return get_transactions_by_period(
            db,
            date(1900, 1, 1),
            date.today(),
            category_id,
            skip,
            limit
        )
    
    #Cas 4: Pas de filtre, retourner toutes les transactions
    return get_all_transactions(db, skip, limit)

#Endpoint : Récupérer UNE transaction
@router.get("/{transaction_id}", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
def get_one_transaction(transaction_id:int, db:Session = Depends(get_db)):
    '''
    Récupère une transaction par son ID
    Retourne TransactionResponse: transaction demandée avec infos catégorie
    Si transaction existe pas -> Erreur 404
    '''
    transaction = get_transaction_by_id(db, transaction_id)
    if not transaction: #Si pas trouvé
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, #On renvoi erreur 404
            detail=f"Transaction avec l'ID {transaction_id} introuvable"
        )
    return transaction

#Endpoint : CREER une nouvelle transaction
@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_new_transaction(transaction_data:TransactionCreate, db:Session=Depends(get_db)):
    '''
    Créer une nouvelle transaction
    category_id doit exister (si fourni), date ne peut pas être dans le futur, amount ne peut pas être exactement 0
    Retourne TransactionResponse = transaction créée avec son ID, erreur 400 si données invalides
    '''
    try:
        new_transaction = create_transaction(db, transaction_data)
        return new_transaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

#Endpoint : MODIFIER une transaction
@router.patch("/{transaction_id}", response_model=TransactionResponse, status_code=status.HTTP_200_OK)
def update_existing_transaction(transaction_id:int,transaction_data: TransactionUpdate,db:Session = Depends(get_db)):
    '''
    Modifie une transaction existante (modification partielle)
    category_id doit exister (si fourni), date ne peut pas être dans le futur, amount ne peut pas être exactement 0
    Retourne TransactionResponse = transaction modifiée
    404 si transaction n'existe pas, 400 si données invalides
    '''
    try:
        updated_transaction = update_transaction(db, transaction_id, transaction_data)
        if not updated_transaction: #Si pas trouvé alors 404
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction avec l'ID {transaction_id} introuvable"
            )
        return updated_transaction
    
    except ValueError as e: #Si l'erreur ne vient pas du fait que la transaction n'existe pas, alors 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

#Endpoint : SUPPRIMER une transaction
@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_transaction(transaction_id:int, db:Session = Depends(get_db)):
    '''
    Supprime une transaction
    Retourne None (204 No Content)
    Erreur 404 si transaction n'existe pas
    '''
    success = delete_transaction(db, transaction_id)

    if not success: #Si ça a pas marché, c'est qu'on a pas trouvé la transaction à supprimer
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction avec l'ID {transaction_id} introuvable"
        )
    #Pas de return pour un 204 No Content
    