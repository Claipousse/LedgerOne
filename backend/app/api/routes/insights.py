'''
Router Insights - Endpoints pour les statistiques et analyses
Contient tous les endpoints pour récupérer agrégations et analyses de dépenses
'''
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query #Pour création routeurs, injection dépendances, erreurs http & code http (200, 404, ...)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db #Pour fournir la session DB
from app.services import (get_monthly_total, get_category_breakdown, get_monthly_summary)

router = APIRouter( #Créer le router pour les statistiques
    prefix="/insights", #Toutes les routes auront /insights au début
    tags=["Insights"] #Groupe les endpoint dans la doc auto
)

#Endpoint : Résumé complet du mois
@router.get("/summary", response_model=Dict[str, Any],status_code=status.HTTP_200_OK)
def get_month_summary(
    year:int = Query(..., ge=2000, le=2100, description="Annee (ex:2025)"),
    month:int = Query(..., ge=1, le=12, description="Mois (1-12)"),
    db:Session = Depends(get_db)
): 
    '''
    Génère résumé complet des dépenses d'un mois donné
    Paramètres obligatoires: année & mois
    Retourne dictionnaire contenant:
    - total : montant total des dépenses
    - count : nombre de transactions
    - average : dépense moyenne par transactions
    - by_category: répartition détaillée par catégorie (montant, %, count)
    Exemple: GET /api/insights/summary?year=2025&month=1
    '''
    try:
        summary = get_monthly_summary(db, year, month)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, #500 car l'erreur viens du serveur / calcul SQL, pas de l'utilisateur
            detail=f"Erreur lors du calcul du résumé: {str(e)}"
        )

#Endpoint : Total des dépenses du mois
@router.get("/monthly-total", response_model=Dict[str, float], status_code=status.HTTP_200_OK)
def get_month_total(
    year:int = Query(..., ge=2000, le=2100, description="Année (ex:2025)"),
    month:int = Query(..., ge=1, le=12, description="Mois (1-12)"),
    category_id:int = Query(None, ge=1, description="Filtrer par catégorie (optionnel)"),
    db:Session = Depends(get_db)
):
    '''
    Calcule total des dépenses pour un mois donnée
    Paramètres obligatoires: year & mois
    Optionnels: category_id:filtrer par catégorie spécifique
    Retourne un dictionnaire contenant total: montant total en float
    Exemple: GET /api/insights/monthly-total?year=2025&month=1
    Exemple avec filtre: GET /api/insights/monthly-total?year=2025&month=1&category_id=3
    '''
    try:
        total = get_monthly_total(db, year, month, category_id)
        return {"total": total}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, #500 car l'erreur vient du serveur pas de l'utilisateur
            detail=f"Erreur lors du calcul du total: {str(e)}"
        )

#Endpoint : Répartition détaillée par catégorie
@router.get("/category-breakdown", response_model=Dict[str, Dict[str, Any]], status_code = status.HTTP_200_OK)
def get_breakdown_by_category(
    year:int = Query(..., ge=2000, le=2100, description="Année (ex:2025)"),
    month:int = Query(..., ge=1, le=12, description="Mois (1-12)"),
    db:Session = Depends(get_db)
):
    '''
    Calcule la répartition détaillée des dépenses PAR CATEGORIE
    Paramètre obligatoires : année & mois
    Retourne dictionnaire o`u chaque clé est un nom de catégorie et la valeur contient:
    - total : montant total pour cette catégorie
    - percentage : pourcentage du total global
    - count : nombre de transactions dans cette categorie
    Exemple : GET /api/insights/category-breakdown?year=2025&month=1
    Exemple Réponse:
    {
        "Alimentation": {"total": 432.50, "percentage": 45.2, "count": 15},
        "Transport": {"total": 87.30, "percentage": 9.1, "count": 8}
    }
    '''
    try:
        breakdown = get_category_breakdown(db, year, month)
        return breakdown
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, #500 car erreur vient du serveur pas de l'utilisateur
            detail=f"Erreur lors du calcul de la répartition: {str(e)}"
        )

