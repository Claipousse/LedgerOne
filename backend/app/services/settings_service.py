'''
Service de gestion des paramètres globaux
Gère la l'unique ligne (id=1) contenant le budget mensuel global
Comme la ligne est initialisée automatiquement par init_db.py, pas de Create ou Delete
'''

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from app.models.settings import Settings
from app.schemas.settings import SettingsUpdate

def get_settings(db:Session) -> Settings: #On récupère les settings
    settings = db.query(Settings).filter(Settings.id == 1).first()
    if not settings: #Si la ligne existe pas on la crée (ce qui serait anormal)
        settings = Settings(id=1, global_monthly_budget=None)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

def update_settings(db:Session, settings_data:SettingsUpdate) -> Settings:
    '''
    Met à jour les settings
    Prend en paramètre la session et les nouvelles données
    Retourne settings mis à jour
    '''
    settings = get_settings(db) #On récup les settings
    update_data = settings_data.dict(exclude_unset=True) #On extrait les champs fournis
    
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    try:
        db.commit() #Sauvegarder dans le DB
        db.refresh(settings) #Rafraichir la DB
        return settings
    
    except IntegrityError as e: #Si ya une erreur, comme un budget <0, on annule
        db.rollback()
        raise ValueError(f"Erreur lors de la mise à jour des paramètres : {str(e)}")


def get_global_budget(db:Session) -> Optional[float]: #Récupère le budget mensuel global, et le retourne (ou None si yen a pas)
    settings = get_settings(db)
    return settings.global_monthly_budget


def reset_global_budget(db:Session) -> Settings: #Réinitialise le budget global à None
    settings = get_settings(db)
    settings.global_monthly_budget = None
    try:
        db.commit()
        db.refresh(settings)
        return settings
     except Exception as e:
        db.rollback()
        raise ValueError(f"Erreur lors de la réinitialisation: {str(e)}")


def settings_exists(db:Session) -> bool: #Vérifie si la ligne de paramètre existe (True/False) normalement toujours True
    return db.query(Settings).filter(Settings.id == 1).first() is not None
