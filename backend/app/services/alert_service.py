'''
Service de détection des dépassements de budget
Vérifie si les dépenses réelles dépassent les budgets configurés (global + par catégorie)
'''
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date

from app.services.settings_service import get_settings #Pour récupérer budget global
from app.services.transaction_service import get_monthly_total, get_total_by_category #Pour calculer les dépenses par catégories
from app.services.category_service import get_all_categories #Pour récupérer toutes les catégories

def get_budget_alerts(db:Session, year:int, month:int) -> Dict[str, List[Dict[str, Any]]]: #Retourne un dictionnaire contenant une liste d'alertes
    '''
    Détecte les dépassements de budget pour un mois donné
    Compare budgets configurés vs. dépenses réelles
    Prends en paramètres la session, le mois et l'année qu'on veut étudier
    Retourne Dictionnaire avec clé "alerts" contenant liste d'alertes
    Chaque alerte contient: scope, budget, actual, delta (=différence) (et category si applicable)
    Exemple de retour:
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
    '''
    alerts = [] #On initialise liste vide pour mettre les alertes détectés dedans

    alerts.extend(_check_global_budget(db, year, month)) #Partie 1 : Vérifier le budget GLOBAL

    alerts.extend(_check_category_budgets(db, year, month)) #Partie 2 : Vérifier les budgets PAR CATEGORIE

    return {"alerts":alerts}

def _check_global_budget(db:Session, year:int, month:int) -> List[Dict[str, Any]]:
    '''
    Vérifie si le budget mensuel GLOBAL est dépassé
    Retourne liste contenant 0 ou 1 alerte (en gros 1 s'il y a dépassement, sinon 0)
    '''
    #Récupérer paramètres globaux (table settings):
    settings = get_settings(db)
    global_budget = settings.global_monthly_budget

    #Si aucun budget global configuré, pas d'alerte possible
    if global_budget is None or global_budget == 0:
        return [] #Retourne liste vide
    
    #Calculer le total réel des dépenses du mois
    actual_spending = get_monthly_total(db, year, month) #Total des dépenses du mois qu'on veut

    #Vérifier si dépassement (dépenses > budget)$
    if actual_spending > global_budget:
        delta = actual_spending - global_budget #On calcule l'écart = montant du dépassement

        return [{
            "scope":"global",
            "budget":round(global_budget, 2), #Budget configuré
            "actual":round(actual_spending, 2), #Dépenses réelles
            "delta":round(delta, 2) #Montant du dépassement
        }]
    
    return [] #Pas de dépassement = pas d'alerte

def _check_category_budgets(db:Session, year:int, month:int) -> List[Dict[str, Any]]:
    '''
    Vérifie si les budgets de chaque CATEGORIE sont dépassés
    Retourne une liste de 0 à n alertes des catégories qui ont un dépassement de budget
    '''
    alerts = [] #On initialise une liste vide
    categories = get_all_categories(db) #Récupérer toutes les catégories de la DB pour les analyser
    actual_by_category = get_total_by_category(db, year, month) #Récupérer les dépenses réelles par catégorie pour le mois donnée

    #Parcourir chaque catégorie pour vérifier son budget
    for category in categories:
        #Vérifier que la catégorie a un budget configuré
        if category.monthly_budget is None or category.monthly_budget == 0:
            continue #Pas de budget = pas de dépassements possible, on passe à la suivante

        #Récupérer les dépenses réelles par catégorie, si aucune transaction dans cette catégorie, on considère 0.0
        actual_spending = actual_by_category.get(category.name, 0.0)

        #Vérif dépassement
        if actual_spending > category.monthly_budget:
            delta = actual_spending - category.monthly_budget
            alerts.append({
                "scope":"category",
                "category": category.name,
                "budget":round(category.monthly_budget, 2), #Budget configuré
                "actual":round(actual_spending, 2), #Dépenses réelles
                "delta":round(delta, 2) #Montant du dépassement
            })
    return alerts
