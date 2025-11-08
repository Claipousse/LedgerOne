'''
Dépendances communes pour les endpoints de l'API
Contient fonctions réutilisables pour tous les routers qui seront dans le sous dossier routers/
'''
from typing import Generator #Generator[YieldType, SendType, ReturnType] : YieldType=ce que yield produit (Session), SendType:ce qu'on peut envoyer au générateur (None), ReturnType: Ce que la fonction retourne à la fin (None)
from sqlalchemy.orm import Session
from app.database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    '''
    Fournit une session de base de données pour chaque requête
    Objet Generator remplace return: là où return peut renvoyer seulement 1 objet, Generator peut en retourner plusieurs et les séparer (yield)
    Utilisé avec Depends() dans les endpoints FastAPI
    Session automatiquement fermée après la requête (finally)
    Yields: retourne session sqlalchemy connectée à la DB

    Exemple d'utilisation:
        @router.get("/categories")
        def get_categories(db: Session = Depends(get_db)):
            return db.query(Category).all()
    '''
    db = SessionLocal()
    try:
        yield db #yield crée la session DB, Fast API récup la session et la passe à l'endpoint, puis fonction se met en pause
    finally:
        db.close() #Puis fonction reprend pour fermer la session à la fin