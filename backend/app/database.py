'''
Sert à gérer & établir la connexion à la base de donnée
Evite qu'on doive le faire à chaque fichier, et donc évite les répétitions, un import suffit
'''
#SQL Alchemy
from sqlalchemy import create_engine #Sert à créer la connexion à la bdd
from sqlalchemy.orm import sessionmaker, DeclarativeBase #Crée une session (= conversation avec une bdd en gros) & Crée la classe de base de tous les modèles

#On veut récup des infos de config.py
from app.config import settings

#Création de l'engine (= moteur de connexion à la base de données)
engine = create_engine(
    settings.DATABASE_URL, #Se connecte au fichier SQLite situé sur ce chemin
    connect_args={"check_same_thread" : False}, #Permet d'avoir plusieurs requêtes en même temps
    echo=settings.DEBUG #On reprends les paramètres de debug de config (True/false)
)

#On initialise la session
SessionLocal = sessionmaker(
    autocommit=False, #Pas de sauvegarde auto, on le fait à la fin pour éviter les mauvaises manip et pouvoir rollback
    autoflush=False, #On décide quand synchroniser (=préparer) les objets python & la DB
    bind=engine #On utilise le moteur de connexion crée au dessus
)

class Base(DeclarativeBase): #Classe mère pour les modèles
    pass

def get_db():
    db = SessionLocal() #Ouvre session
    try:
        yield db
    finally:
        db.close() #On ferme la session à la fin si pas déjà fait