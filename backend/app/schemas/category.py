'''
Schémas Pydantic pour la validation des données de Category
Définit les formats de données pour création, modification et lecture des catégories
'''

from pydantic import BaseModel, Field, field_validator
from typing import Optional #Pour faire des champs optionnels (couleur, budget, ...)

class CategoryBase(BaseModel): #Classe parente
    '''
    Schéma de base/parent, contenant les champs communs à tous les schémas Category
    Jamais utilisé directement dans l'API
    Permet d'éviter les répétitions
    '''
    name:str = Field(..., min_length=1, max_length=100) #Titre : Obligatoire, composé de min 1 lettre max 100
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$') #Couleur, facultatif, composé d'un code hexadécimal (ex: #000000)
    monthly_budget: Optional[float] = Field(None, ge=0) #Budget mensuel, facultatif, supérieur ou égal à 0

class CategoryCreate(CategoryBase):
    '''
    Schéma pour créer une catégorie (via POST)
    Hérite de CategoryBase, nécéssite un name, et accepte color/monthly_budget
    '''
    pass

class CategoryUpdate(BaseModel):
    '''
    Schéma pour modification d'une catégorie (via PATCH)
    Tous les champs sont optionnel pour permettre une modif partielle
    Par exemple, si on veut juste modifier nom/couleur/budget, on peut mettre le terme qu'on veut changer et laisser vide le reste 
    '''
    name:Optional[str] = Field(None, min_length=1, max_length=100)
    color:Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    monthly_budget: Optional[float] = Field(None, ge=0)

    @field_validator('monthly_budget')
    @classmethod

    def validate_budget(cls, v):
        '''
        Validateur personnalisé pour monthly_budget
        Vérifie que valeur fournie est bien >= 0
        '''
        if v is not None and v < 0:
            raise ValueError('Le budget mensuel doit être positif ou nul')
        return v
    
class CategoryResponse(CategoryBase):
    '''
    Schéma pour la LECTURE d'une catégorie (via GET)
    Hérite de CategoryBase et ajoute l'ID généré par la base de données
    '''
    id:int
    model_config = {
        "from_attributes": True
    }