'''
Schémas Pydantic pour validation des données de Settings
Contient une ligne unique (id =1) 
'''
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class SettingsBase(BaseModel):
    '''
    Schéma de base contenant le champ commun à tous les schémas Settings
    N'est jamais utilisé directement dans l'API, sert de classe parente
    '''
    global_monthly_budget:Optional[float] = Field(None, ge=0)

#Pas de SettingsCreate car ligne initialisé automatiquement par init_db.py

class SettingsUpdate(SettingsBase):
    '''
    Schéma pour modification des paramètres globaux (patch)
    '''
    @field_validator('global_monthly_budget')
    @classmethod
    def validate_budget(cls, v):
        #On check que le budget ne soit pas négatif
        if v is not None and v < 0:
            raise ValueError("Le budget mensuel doit être positif ou nul")
        return v

class SettingsResponse(SettingsBase):
    '''
    Schéma pour lecture des paramètres globaux (get)
    Hérite de SettingsBase & ajoute updated_at
    Comme c'est toujours le même id, on sait ou chercher 
    donc pas besoin de le préciser pour trouver le budget
    '''
    updated_at = datetime
    model_config = {
        "from_attributes": True
    }