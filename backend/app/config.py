'''
Centre de configuration de l'app, tout est centralisé et facile à modifier via le .env
Le fichier .env est lu en priorité par Pydantic pour importer les variables nécéssaires (DATABASE_URL, DEBUG, ...)
Cela permet de pouvoir changer de config (dev/test/prod), sans devoir toucher au code et seulement via le .env
Cependant, les variables dans ce fichiers servent si jamais il n'y a pas de .env fournit, pour avoir des valeurs par défauts
'''
from pathlib import Path
from pydantic_settings import BaseSettings #Sert à gérer la configuration via variables d'environnements/.env par exemple

#Chemin jusqu'a la racine du projet
BASE_DIR =  Path(__file__).resolve().parent.parent.parent #3x parent pour remonter à la racine

class Settings(BaseSettings): #Hérite de BaseSettings (Pydantic)
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/ledgerone.db" #Chemin vers la BDD
    DEBUG: bool = True #Debug On/Off, en prod penser à mettre False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:8080", "http://127.0.0.1:8080"] #CROS, autorise front à communiquer avec l'api

    #Config de l'API
    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "LedgerOne API"
    VERSION: str = "1.0.0" #v1 pour le moment, si jamais on fait des patch/mises à jour on peut mettre 1.0.1 par exemple

    class Config:
        env_file = ".env" #Fichier à lire pour changer les variables
        case_sensitive = True #Sensible à la casse

settings = Settings() #Pydantic lit le .env et charge les valeurs