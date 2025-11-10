'''
Router Alerts - Endpoint pour détection des dépassements de budgets
Expose l'enpoint GET /api/alerts pour récupérer les alertes budgétaires
'''

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db #Pour fournir la session DB
from app.services.alert_service import get_budget_alerts #Logique métier

router = APIRouter( #Créer le router pour les alertes
    prefix="/alerts", #Toutes les routes auront /alerts au début
    tags=["Alerts"] #Groupe les endpoints dans le doc auto
)

#Endpoint : Récupérer les alertes budgétaires d'un mois
@router.get("/", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_alerts(
    year:int = Query(..., ge=2000, le=2100, description="Année (ex:2025)"),
    month:int = Query(..., ge=1, le=12, description="Mois (1-12)"),
    db: Session = Depends(get_db)
):
    '''
    Récupère les alertes de dépassement de budget pour un mois donné
    Paramètre obligatoire: year & month
    Retourne disctionnaire contenant liste des alertes (budget global + par catégorie)

    Exemple : GET /api/alerts/?year=2024&month=12
    Réponse si dépassement: 
     {
        "alerts": [
            {
                "scope": "global",
                "budget": 2000.0,
                "actual": 2350.50,
                "delta": 350.50
            },
            {
                "scope": "category",
                "category": "Alimentation",
                "budget": 400.0,
                "actual": 475.30,
                "delta": 75.30
            }
        ]
    }
    
    Réponse si aucun dépassement:
    {
        "alerts": []
    }
    '''
    try:
        alerts = get_budget_alerts(db, year, month) #Appeler le service pour récupérer les alertes
        return alerts
    except Exception as e:
        raise HTTPException(#Erreur serveur inattendue
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des alertes: {str(e)}"
        )
