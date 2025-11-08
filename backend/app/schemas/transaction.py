'''
Schémas Pydantic pour la validation des données de Transaction
Définit les formats de donnéees pour création/modification & lecture des transactions
'''

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import datetime
from datetime import datetime as dt

class TransactionBase(BaseModel):
    '''
    Schéma de base/parent, contenant les champs communs à tous les schémas Transaction
    Jamais utilisé directement dans l'API, permet d'éviter répétitions
    '''
    date: datetime.date = Field(...)
    description: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(...)
    category_id: Optional[int] = Field(None, ge=1) #Supérieur ou égal à 1

class TransactionCreate(TransactionBase):
    '''
    Schéma pour créer une transaction (via POST)
    Hérite de TransactionBase, nécéssite une date, description et montant, accepte id catégorie
    '''
    pass

class TransactionUpdate(BaseModel):
    '''
    Schéma pour modification d'une transaction (via PATCH)
    Tous les champs sont optionnel pour permettre une modif partielle
    Par exemple, si on veut juste modifier nom/couleur/budget, on peut mettre le terme qu'on veut changer et laisser vide le reste 
    '''
    date: Optional[datetime.date] = None
    description: Optional[str] = Field(None, min_length=1, max_length=255)
    amount: Optional[float] = None
    category_id: Optional[int] = Field(None, ge=1)

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        """
        Validateur personnalisé pour amount
        Vérifie que le montant n'est pas exactement 0 (sans sens économique)
        Les montants négatifs sont autorisés (remboursements)
        """
        if v is not None and v == 0:
            raise ValueError('Le montant ne peut pas être exactement 0')
        return v
    
class CategoryInResponse(BaseModel):
    """
    Schéma imbriqué (nested) pour afficher les infos de catégorie dans une transaction
    Permet d'éviter de faire un appel API supplémentaire pour récupérer les infos de la catégorie associé au paiement
    """
    id: int
    name: str
    color: Optional[str] = None
    
    model_config = {
        "from_attributes": True
    }


class TransactionResponse(TransactionBase):
    """
    Schéma pour la LECTURE d'une transaction (GET)
    Hérite de TransactionBase et ajoute l'ID + created_at + infos catégorie
    """
    id: int
    created_at: dt
    category: Optional[CategoryInResponse] = None
    
    model_config = {
        "from_attributes": True
    }