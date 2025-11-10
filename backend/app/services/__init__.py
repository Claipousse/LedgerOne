'''
Package Services - Centralise tous les services (logique métier: CRUD, Calculs, Recherches, ...)
Permet d'importer facilement tous les services depuis 1 seul endroit
Transforme /services en package python
'''

#Import category_service
from app.services.category_service import (
    get_all_categories,
    get_category_by_id,
    get_category_by_name,
    create_category,
    update_category,
    delete_category,
    category_exists
)

#Import settings_service
from app.services.settings_service import (
    get_settings,
    update_settings,
    get_global_budget,
    reset_global_budget,
    settings_exists
)

#Import transaction_service
from app.services.transaction_service import (
    get_all_transactions,
    get_transaction_by_id,
    create_transaction,
    update_transaction,
    delete_transaction,
    get_transactions_by_period,
    search_transactions,
    get_transactions_by_month,
    get_monthly_total,
    get_total_by_category,
    get_category_breakdown,
    get_monthly_summary,
    get_transaction_count,
    transaction_exists
)

# Import alert_service
from app.services.alert_service import (
    get_budget_alerts
)

#Liste publique des exports
# Définit ce qui est accessible avec "from app.services import *"
# Évite d'exposer les imports internes et garde le package propre

__all__ = [
    #Category service (7 fonctions)
     "get_all_categories",
    "get_category_by_id",
    "get_category_by_name",
    "create_category",
    "update_category",
    "delete_category",
    "category_exists",
    
    # Settings service (5 fonctions)
    "get_settings",
    "update_settings",
    "get_global_budget",
    "reset_global_budget",
    "settings_exists",
    
    # Transaction service (14 fonctions)
    "get_all_transactions",
    "get_transaction_by_id",
    "create_transaction",
    "update_transaction",
    "delete_transaction",
    "get_transactions_by_period",
    "search_transactions",
    "get_transactions_by_month",
    "get_monthly_total",
    "get_total_by_category",
    "get_category_breakdown",
    "get_monthly_summary",
    "get_transaction_count",
    "transaction_exists",

     
    # Alert service (1 fonction)
    "get_budget_alerts",
]