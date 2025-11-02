'''
Permet de faire un package, fait en sorte de faire de /models un package
Sans __init__, python reconnait models comme un simple dossier, et non comme un package
Sans package, il faudrait importer manuellement chaque module (category, transaction, settings), la un appel suffira
'''
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.settings import Settings
__all__ = ["Category", "Transaction", "Settings"]