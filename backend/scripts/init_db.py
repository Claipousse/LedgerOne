'''
Script qui crée toutes les tables de la DB SQLite
'''
import sys #Pour pythonpath, chemin de recherche des modules
from pathlib import Path #Manipuler chemins de fichiers

#Ajouter dossier parent au PythonPath
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) #On remonte de 2 niveau vers /backend, sys.path = liste des dossiers ou python cherche modules

from app.database import engine, Base #Moteur SQLAlchemy pour se connecter à la DB
from app.models import Category, Transaction, Settings #Les 3 modèles dans /models
from app.config import settings as app_settings #Config de config.py

def init_db(): #On crée toutes les tables de la base de données

    print("Initialisation de la base de données...")
    print(f"Emplacement : {app_settings.DATABASE_URL}") #le 'f' avant les guillemets permet d'utiliser {}, DATABASE_URL correspond au chemin définit dans config.py

    #Si pas de dossier data, on le crée
    db_path = Path(app_settings.DATABASE_URL.replace("sqlite:///", "")) #Donne ./data/ledgerone.db
    db_path.parent.mkdir(parents=True, exist_ok=True)

    #Crée toutes les tables
    Base.metadata.create_all(bind=engine) #Base.metadata contient definition de toutes les tables qui héritent de Base, create_all fait le SQL

    print("Tables créées:")
    print("   - categories")
    print("   - transactions")
    print("   - settings")

    #Initialiser la ligne unique dans settings
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        existing_settings = session.query(Settings).filter(Settings.id == 1).first() #On cherche le setting avec l'ID 1 (par défaut dans models/settings.py)
        if not existing_settings:
            default_settings = Settings(id=1, global_monthly_budget=None) #Si pas trouvé, on initialise des paramètres par défaut
            session.add(default_settings) #File d'attente
            session.commit() #On éxécute dans le DB
            print("Paramètres par défaut initialisés")
        else:
            print("Paramètres déjà existants")
    print("\n Base de données initialisée avec succès!")
    print(f"Fichier DB : {db_path}")

def reset_db(): #On supprime puis recrée toutes les tables, permettant de faire des tables vierges
    
    print("ATTENTION : Cette opération va supprimer toutes les données !")
    while(1):
        response = input("Êtes-vous sur de votre choix (o/n): ")
        if response.lower() == 'o':
            print("Suppresion des tables...")
            Base.metadata.drop_all(bind=engine)
            print("Tables supprimées")

            print("Recréation des tables...")
            init_db()
            break

        elif response.lower() == 'n':
            print("Opération annulée")
            break

        else:
            print("Erreur : Veuillez saisir une valeur correcte")

if __name__ == "__main__": #Executé seulement si le fichier est lancé directement, et pas importé
    import argparse #Permet de passer des arguments
    
    parser = argparse.ArgumentParser(description="Gestion de la base de données")
    parser.add_argument(
        "--reset", #Nom de l'argument, en mettant --reset on peut appeler reset_db()
        action="store_true",
        help="Réinitialiser complètement la DB (supprime les données!)" #Description avec --help
    )
    
    args = parser.parse_args()
    
    if args.reset:
        reset_db() #Si l'utilisateur a mit --reset, on reset
    else:
        init_db() #Sinon initialisation normale