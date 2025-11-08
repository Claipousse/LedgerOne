'''
Package Schémas - Centralise tous les schémas Pydantic
Permet d'importer facilement tous les schémas depuis 1 seul endroit
'''

from app.schemas.category import (
    CategoryBase,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse
)

from app.schemas.transaction import (
    TransactionBase,
    TransactionCreate,
    TransactionUpdate,
    TransactionInResponse,
    TransactionResponse
)

from app.schemas.settings import (
    SettingsBase,
    SettingsUpdate,
    SettingsResponse
)

#On liste tous les schémas dispo
# Définit ce qui est accessible avec "from app.schemas import *"
# Évite d'exposer les imports internes et garde le package propre
__all__ = [
    "CategoryBase", "CategoryCreate", "CategoryUpdate", "CategoryResponse",
    "TransactionBase", "TransactionCreate", "TransactionUpdate", "TransactionInResponse", "TransactionResponse",
    "SettingsBase", "SettingsUpdate", "SettingsResponse",
]