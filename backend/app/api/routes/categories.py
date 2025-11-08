'''
Router Categories - Endpoints pour la gestion des catégories
Contient tous les endpoints CRUD pour les catégories
'''

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status #Pour création de routeur, injection dépendances, lever erreurs http & codes http (200, 404, ...)
from sqlalchemy.orm import Session #Type de session pour DB

from app.api.dependencies import get_db #Pour fournir session DB
from app.services import ( #Fournit la logique métier pour catégories
    get_all_categories,
    get_category_by_id,
    create_category,
    update_category,
    delete_category
)
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse #Pour validation des données

router = APIRouter( #Créer le router pour les catégories
    prefix="/categories", #Toutes les routes auront /categories au début
    tags=["Categories"] #Groupe les endpoints dans la doc auto
)

#Endpoint : Lister TOUTES les catégories
@router.get("/", response_model=List[CategoryResponse], status_code=status.HTTP_200_OK) #FastAPI valide et convertit en JSON, puis renvoit 200 (succès)
def list_all_categories(db:Session = Depends(get_db)):
    '''
    Liste toutes les catégories
    Retourne List[CategoryResponse]: Liste de toutes les catégories
    '''
    return get_all_categories(db)

#Endpoint : Récupérer UNE catégorie
@router.get("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
def get_one_category(category_id: int, db:Session = Depends(get_db)):
    '''
    Récupère une catégorie par son ID, en prenant en argument l'ID de la catégorie à récupérer
    Retourne CategoryResponse: catégorie demandée
    Raises HTTPException 404 si catégorie n'existe pas
    '''
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catégorie avec l'ID {category_id} introuvable"
        )
    return category

#Endpoint : CREER une nouvelle catégorie
@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_new_category(category_data:CategoryCreate, db:Session = Depends(get_db)):
    '''
    Créer une nouvelle catégorie
    Prend en arguments les données de la catégorie à créer (validées par Pydantic -> category_data)
    Retourne CategoryResponse : catégorie crée avec son ID
    Si nom existe déjà ou données invalides -> Erreur 400
    '''
    try:
        new_category = create_category(db, category_data)
        return new_category
    except ValueError as e:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= str(e) 
        )
    
#Endpoint : MODIFIER une nouvelle catégorie
@router.patch("/{category_id}", response_model=CategoryResponse, status_code=status.HTTP_200_OK)
def update_existing_category(category_id:int, category_data:CategoryUpdate, db:Session = Depends(get_db)):
    '''
    Modifie une catégorie existante (modification partielle)
    Prend en argument ID de la catégorie à modifier, et les nouvelles données à remplacer
    Retourne la catégorie modifiée (CategoryResponse)
    Erreur 404 si catégorie n'existe pas, 400 si les données sont invalides (ex : nom déjà utilisé)
    '''
    try:
        updated_category = update_category(db, category_id, category_data)
        if not updated_category: #Si pas trouvé, alors 404
            raise HTTPException(
                status_code= status.HTTP_404_NOT_FOUND,
                detail=f"Catégorie avec l'ID {category_id} introuvable"
            )
        return updated_category
    
    except ValueError as e: #Si l'erreur ne vient pas du fait que la catégorie soit introuvable, c'est que les nouvelles données ne sont pas bonnes -> 400
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
#Endpoint : SUPPRIMER une catégorie
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_category(category_id:int, db:Session = Depends(get_db)):
    '''
    Supprime une catégorie
    Transactions liées auront leur categoryçid mis à NULL
    Prends en arguments l'ID de la categorie à supprimer
    Retourne None (204)
    Erreur 404 si catégorie existe pas
    '''
    success = delete_category(db, category_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Catégorie avec l'ID {category_id} introuvable"
        )
    #Pas besoin de return pour un 204 No Content
