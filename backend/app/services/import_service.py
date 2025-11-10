'''
Service d'import CSV - Gestion de l'import en masse de transactions
Permet de parser, valider et importer des transactions depuis un fichier CSV
'''

import csv #Pour lire/écrire CSV
import io #Input/Output, pour simuler un ficher en mémoire
import typing import List, Dict, Any, Tuple, Optional
from datetime import date, datetime #Pour manipuler dates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError #Si contrainte SQL relevée

from app.models.category import Category #Modèle Catégory
from app.models.transaction import Transaction #Modèle Transaction
from app.services.category_service import get_category_by_name #Fonction pour chercher catégorie selon son nom

#Constantes pour création automatique des catégories
DEFAULT_CATEGORY_COLOR = "#505050" #Gris foncé par défaut pour les catégories auto-créées
DEFAULT_CATEGORY_BUDGET = None #Pas de budget défini par défaut

#Parsing du fichier CSV
def parse_csv_file(file_content:str) -> List[Dict[str, str]]:
    '''
    Parse le contenu d'un fichier CSV et le transforme en liste de dictionnaires
    Prend en paramètre le contenu brut du CSV (str), retourne liste de dictionnaires, chaque dict = une ligne du CSV
    Format des colonnes : date, description, amount, category (optionnel)
    Exemple de retour :
    [
        {"date": "2025-01-15", "description": "Courses", "amount": "45.50", "category": "Alimentation"},
        {"date": "2025-01-16", "description": "Essence", "amount": "60.00", "category": "Transport"}
    ]
    '''
    # Créer un objet StringIO pour simuler un fichier à partir du string
    # (csv.DictReader a besoin d'un objet file-like)
    csv_file = io.StringIO(file_content)

    # DictReader lit le CSV et crée un dict pour chaque ligne
    # Les clés du dictionnaire sont les noms des colonnes (premiere ligne du CSV)
    reader = csv.DictReader(csv_file)

    # Convertir le reader en liste de dictionnaires
    rows = list(reader)

    return rows


#Validation des données
def validate_row(row: Dict[str, str], line_number:int) -> Tuple[bool, Optional[str]]:
    '''
    Valide une ligne CSV avant de l'importer
    Prend en paramètres :
    - row : dictionnaire contenant les données d'une ligne
    - line_number : numéro de la ligne (pour le message d'erreur)

    Retourne tuple (est_valide, message_erreur)
    - Si valide : (True, None)
    - Si invalide : (False, "Ligne X: message d'erreur")

    Validations effectuées :
    1. Date existe au format ISO (YYYY-MM-DD)
    2. Date <= date actuelle
    3. Description existe et non vide (car obligatoire)
    4. Amount existe et est un nombre
    5. Amount != 0
    '''
    #Validation 1 : Vérifier que date existe
    if not row.get('date') or row['date'].strip() == '':
        return (False, f"Ligne {line_number}: La date est obligatoire")
    
    #Puis vérifier le format de la date (YYYY-MM-DD)
    try:
        transaction_date = datetime.strptime(row['date'].strip(), '%Y-%m-%d').date
    except ValueError:
        return (False, f"Ligne {line_number}: La date doit être au format YYYY-MM-DD")
    
    #Validation 2 : Vérifier que la date ne soit pas dans le futur
    if transaction_date > date.today():
        return (False, f"Ligne {line_number}: La date ne peut pas être dans le futur")
    
    #Validation 3 : Vérifier que description existe
    if not row.get('description') or row['description'].strip() == '':
        return (False, f"Ligne {line_number}: La description est obligatoire")
    
    #Validation 4 : Vérifier que le montant existe
    if not row.get('amount') or row['amount'].strip() == '':
        return (False, f"Ligne {line_number}: Le montant est obligatoire")
    
    #Validation 5 : Vérifier que le montant est un nombre (> 0)
    try:
        amount = float(row['amount'].strip())
    except ValueError:
        return (False, f"Ligne {line_number}: Le montant doit être un nombre (ex: 45.99)")
    if amount == 0:
        return (False, f"Ligne {line_number}: Le montant ne peut être égal à 0")
    
    #Si tout est ok, ligne validée
    return (True, None)

def get_or_create_category(db: Session, category_name:str) -> Category:
    '''
    Récupère une catéégorie existante ou la crée si elle n'existe pas
    Prends en paramètres session SQLAlchemy & nom de la catégorie à récupérer/créer
    Retourne l'objet Category (existant ou nouvellement créé)

    Logique:
    1. Chercher si la catégorie existe déjà (par nom)
    2. Si oui -> retourner la catégorie existante
    3. Si non -> créer une nouvelle catégorie avec :
        - name : category_name
        - color = #505050 (gris foncé)
        - monthly_budget = None
    4. Retourner la catégorie
    '''

    #Etape 1: Chercher si la catégorie existe déjà
    existing_category = get_category_by_name(db, category_name)

    # Étape 2 : Si elle existe, la retourner directement
    if existing_category:
        return existing_category

    # Étape 3 : Sinon, créer une nouvelle catégorie
    new_category = Category(
        name=category_name,
        color=DEFAULT_CATEGORY_COLOR,
        monthly_budget=DEFAULT_CATEGORY_BUDGET
    )

    db.add(new_category) # Ajouter la catégorie à la base de données
    db.flush()  # flush() pour obtenir l'ID sans faire de commit final
    # (le commit se fera à la fin de l'import complet)
    
    return new_category

#Fonction principale de l'import
def import_transactions_from_csv(db:Session, file) -> Dict[str, Any]:
    '''
    Fonction principale qui orchestre l'import complet d'un fichier CSV
    Prends en paramètres : session SQLAlchemy & fichier uploadé (UploadFile de FastAPI)

    Retourne un dictionnaire avec le rapport d'import :
    {
        "inserted": 15,    # Nombre de transactions importées avec succès
        "skipped": 2,      # Nombre de lignes ignorées (erreurs de validation)
        "errors": [        # Liste des erreurs rencontrées
            "Ligne 3: La date doit être au format YYYY-MM-DD",
            "Ligne 7: Le montant doit être un nombre"
        ]
    }
    
    Processus :
    1. Lire le contenu du fichier
    2. Parser le CSV
    3. Pour chaque ligne :
       a. Valider les données
       b. Si invalide → ajouter à errors[] et skip++
       c. Si valide :
          - Gérer la catégorie (get_or_create)
          - Créer la transaction
          - Si succès → inserted++
          - Si échec → errors[] et skip++
    4. Commit final de toutes les transactions valides
    5. Retourner le rapport
    '''

    #Compteurs pour le rapport final
    inserted = 0 #Les lignes qui sont passés
    skipped = 0 #Celles qui sont pas passés (ignorés)
    errors = [] #Détail de l'erreur (via validate_row)

    try:
        #Etape 1 : Lire le contenu du fichier CSV
        file_content = file.decode('utf-8') #Décoder fichier en UTF-8

