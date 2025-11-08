'''
Point d'entrée principal de l'API FastAPI
Configure l'application, les routes et les middlewares (=Interception requêtes HTTP pour vérifier/modifier requetes avant qu'elles passent à l'endpoint)
'''

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware #Import middleware CORS pour autoriser frontend à communiquer
from app.config import settings #Importe config.py, qui permet par exemple de savoir sur sur quelle url lancer le serveur, et d'autres trucs

#Création de l'instance FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME, #Titre de l'API (= "LedgerOne API")
    version=settings.VERSION,
    description="API REST pour la gestion des dépenses personnelles"
)

#Configuration CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware, #Autorise CORS, sinon ça bloquerait les requêtes du Frontend
    allow_origins=settings.ALLOWED_ORIGINS, #Liste URL autorisées à communiquer avec l'API
    allow_credentials=True, #Autorise envoi de cookies & authentifications
    allow_methods=["*"], #Autorise toutes les méthodes HTTP (GET/POST/PATCH/DELETE/...)
    allow_headers=["*"], #Autorise tous les headers HTTP
)

# Route racine (page d'accueil de l'API)
@app.get("/", tags=["Root"])
def read_root():
    '''
    Page d'accueil de l'API
    Retourne un message de bienvenue et les infos de base
    '''
    return {
        "message": "Bienvenue sur l'API LedgerOne",
        "version": settings.VERSION,
        "documentation": "/docs",
        "redoc": "/redoc"
    }

# Route de santé (health check)
@app.get("/health", tags=["Health"])
def health_check():
    '''
    Endpoint de santé pour vérifier que l'API fonctionne
    Utilisé par les outils de monitoring
    '''
    return {"status": "healthy"} #Normalement ça répond ça, si pas de réponse, c'est que ya un problème

# A FAIRE: Inclure les routers quand ils seront créés
# from app.api.routes import categories, transactions, settings, insights
# app.include_router(categories.router, prefix=settings.API_PREFIX)
# app.include_router(transactions.router, prefix=settings.API_PREFIX)
# app.include_router(settings.router, prefix=settings.API_PREFIX)
# app.include_router(insights.router, prefix=settings.API_PREFIX)

# Point d'entrée pour lancement direct du fichier
if __name__ == "__main__":
    import uvicorn #Imporre uvicorn, un serveur pour faire tourner l'app FastAPI, ASGI = Asynchrone, peut gérer plusieurs requêtes à la fois
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", #Ecoute toutes les interfaces réseau
        port=8000,
        reload=True
    )