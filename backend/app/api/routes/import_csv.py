'''
Router Import CSV - Endpoint pour l'import en masse de transactions
Expose l'endpoint POST /api/import/csv pour uploader et traiter fichier CSV
'''

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.api.dependencies import get_db #Pour fournir la session DB
from app.services.import_service import import_transactions_from_csv #Logique métier

router = APIRouter( #Créer le router pour les l'import CSV
    prefix="/import", #Toutes les routes auront /import au début
    tags=["Import"] #Groupe les endpoints dans la doc auto
)

#Endpoint : Importer transactions depuis un fichier CSV
@router.post("/csv", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
async def import_csv(file: UploadFile = File(..., description="Fichier CSV contenant les transactions à importer"), db: Session = Depends(get_db)):
    '''
    Importe transactions en masse depuis un fichier CSV

    Format CSV attendu (avec header) :
    date,description,amount,category
    2025-01-15,Courses Carrefour,45.50,Alimentation
    2025-01-16,Essence Shell,60.00,Transport
    
    Colonnes obligatoires : date, description, amount
    Colonne optionnelle : category

    Validations :
    - Date au format ISO (YYYY-MM-DD) et pas dans le futur
    - Description non vide
    - Amount numérique et différent de 0
    - Les catégories inexistantes sont créées automatiquement (couleur: #505050, budget: None)
    
    Retourne un rapport d'import :
    {
        "inserted": 15,    # Nombre de transactions importées avec succès
        "skipped": 2,      # Nombre de lignes ignorées (erreurs)
        "errors": [        # Liste détaillée des erreurs
            "Ligne 3: La date doit être au format YYYY-MM-DD",
            "Ligne 7: Le montant doit être un nombre"
        ]
    }

    Codes de statut :
    - 200 : Import réussi (même si certaines lignes sont skippées)
    - 400 : Fichier invalide (pas un CSV, vide, mauvais encodage)
    - 500 : Erreur serveur inattendue
    '''

    #Validation 1 : Vérifier que le fichier a bien été uploadé
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun fichier n'a été fourni"
        )
    
    
    #Validation 2 : Vérifier que le fichier est bien un CSV
    if not file.filename.endswith('.csv'): #L'extension doit être .csv
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier doit être au format CSV (.csv)"
        )
    
    #Validation 3 : Vérifier que le fichier n'est pas vide
    #Lire le contenu du fichier (await car opération asynchrone)
    file_content = await file.read() #await attend que la lecture du fichier soit terminée

    if not file_content or len(file_content) == 0: #Si ya rien
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le fichier est vide"
        )
    
    #Appeler service d'import
    try:
        report = import_transactions_from_csv(db, file_content)
        return report #Retourne directement le rapport JSON, fastAPI convertit le dict Python en json
    
    except Exception as e:
        #Erreur inattendue lors de l'import
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'import : {str(e)}"
        )