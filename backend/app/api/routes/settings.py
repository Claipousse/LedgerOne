'''
Router Settings - Endpoints pour la gestion des paramètres globaux
Contient tous les endpoints pour lire & modifier budget mensuel global
'''

from fastapi import APIRouter, Depends, HTTPException, status #Pour création de routeur, injection dépendances, lever erreurs http & codes http (200, 404, ...)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db #Pour fournir session DB
from app.services import get_settings, update_settings #Logique métier, pas de create ni delete car initialisé au début et valeur peut etre None
from app.schemas import SettingsUpdate, SettingsResponse

router = APIRouter( #Créer le router pour les catégories
    prefix="/settings", #Toutes les routes auront /categories au début
    tags=["Settings"] #Groupe les endpoints dans la doc auto
)

#Endpoint : Récupérer paramètres globaux
@router.get("/", response_model=SettingsResponse, status_code=status.HTTP_200_OK)
def get_global_settings(db:Session = Depends(get_db)):
    '''
    Récupère les paramètres globaux de l'application
    Retourne SettingsResponse: contient le budget mensuel global et la date de mise à jour
    '''
    return get_settings(db)

#Endpoint : Modifier les paramètres globaux
@router.patch("/", response_model=SettingsResponse, status_code=status.HTTP_200_OK)
def update_global_settings(settings_data:SettingsUpdate, db:Session = Depends(get_db)):
    '''
    Met à jour les paramètres globaux (budget mensuel global)
    Validation automatique effectuée par le service: global_monthly_budget >= 0 si fourni
    Retourne SettingsResponse : paramètres mis à jour
    Erreur 400 si données invalides
    '''
    try:
        updated_settings = update_settings(db, settings_data)
        return updated_settings
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )