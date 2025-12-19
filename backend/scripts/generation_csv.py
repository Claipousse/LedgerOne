"""
generate_transactions_v2.py - Script de generation de transactions CSV realistes
Genere des transactions sur les 2 dernieres annees avec distribution temporelle precise
"""

import csv
import random
from datetime import date, timedelta
from collections import defaultdict

# ============================================
#              CONFIGURATION
# ============================================

# Date de reference (dynamique)
TODAY = date.today()

# Periode de generation : 2 dernieres annees
END_DATE = TODAY
START_DATE = date(TODAY.year - 2, TODAY.month, TODAY.day)

# Nombre total de transactions a generer
TOTAL_TRANSACTIONS = 1500

# ============================================
#              CATEGORIES
# ============================================

CATEGORIES = {
    "Alimentation": {
        "descriptions": [
            "Courses Carrefour", "Supermarche Auchan", "Marche local",
            "Boulangerie", "Primeur", "Boucherie", "Fromagerie",
            "Courses Lidl", "Intermarche", "Casino"
        ],
        "amount_range": (5, 150),
        "weight": 25  # Frequence relative
    },
    "Transport": {
        "descriptions": [
            "Essence Shell", "Station Total", "Peage autoroute",
            "Parking centre-ville", "Ticket metro", "Uber",
            "Taxi", "Revision voiture", "Controle technique"
        ],
        "amount_range": (5, 120),
        "weight": 15
    },
    "Loisirs": {
        "descriptions": [
            "Cinema UGC", "Concert", "Theatre",
            "Restaurant Le Gourmet", "Bar entre amis", "Bowling",
            "Escape Game", "Musee", "Parc d'attractions"
        ],
        "amount_range": (10, 200),
        "weight": 15
    },
    "Streaming": {
        "descriptions": [
            "Abonnement Netflix", "Spotify Premium", "Disney+",
            "Amazon Prime", "Apple Music", "YouTube Premium",
            "Deezer", "OCS"
        ],
        "amount_range": (5, 20),
        "weight": 5
    },
    "Soins": {
        "descriptions": [
            "Coiffeur", "Pharmacie", "Dentiste",
            "Osteopathe", "Massage", "Manucure",
            "Opticien", "Medecin generaliste"
        ],
        "amount_range": (10, 100),
        "weight": 10
    },
    "Shopping": {
        "descriptions": [
            "Vetements Zara", "Chaussures", "H&M",
            "Decathlon", "Fnac", "Sephora",
            "Bijouterie", "Librairie", "Electronique"
        ],
        "amount_range": (15, 300),
        "weight": 15
    },
    "Logement": {
        "descriptions": [
            "Loyer appartement", "Electricite EDF", "Eau",
            "Internet SFR", "Assurance habitation", "Charges copropriete",
            "Taxe fonciere", "Bricolage Leroy Merlin"
        ],
        "amount_range": (30, 1200),
        "weight": 10
    },
    "Education": {
        "descriptions": [
            "Frais de scolarite", "Livres scolaires", "Fournitures",
            "Cours particuliers", "Formation en ligne", "Udemy",
            "Materiel informatique etudes"
        ],
        "amount_range": (20, 500),
        "weight": 5
    }
}

# ============================================
#              FONCTIONS UTILITAIRES
# ============================================

def calculate_date_distribution():
    """
    Calcule les bornes de dates pour la distribution temporelle :
    - 25% sur l'annee N-2 (plus ancienne)
    - 75% sur l'annee N-1 jusqu'a aujourd'hui
      - Dont 40% sur les 3 derniers mois
    """
    total_days = (END_DATE - START_DATE).days
    
    # Annee la plus ancienne (25% des transactions)
    one_year_ago = date(TODAY.year - 1, TODAY.month, TODAY.day)
    
    # 3 derniers mois
    three_months_ago = TODAY - timedelta(days=90)
    
    return {
        "old_period": (START_DATE, one_year_ago),      # 25%
        "recent_period": (one_year_ago, three_months_ago),  # 75% - 40% = 35%
        "very_recent_period": (three_months_ago, END_DATE)  # 40% des 75% = 30%
    }

def generate_random_date(start_date, end_date):
    """Genere une date aleatoire entre start_date et end_date (incluses)"""
    delta = (end_date - start_date).days
    if delta <= 0:
        return start_date
    random_days = random.randint(0, delta)
    return start_date + timedelta(days=random_days)

def select_category():
    """Selectionne une categorie selon les poids definis"""
    categories = list(CATEGORIES.keys())
    weights = [CATEGORIES[cat]["weight"] for cat in categories]
    return random.choices(categories, weights=weights)[0]

def generate_amount(category):
    """
    Genere un montant realiste pour une categorie.
    Mix de petites transactions frequentes et grosses occasionnelles.
    """
    min_amount, max_amount = CATEGORIES[category]["amount_range"]
    
    # 80% petites transactions, 20% grosses transactions
    if random.random() < 0.8:
        # Petite transaction (dans le tiers inferieur de la plage)
        range_third = (max_amount - min_amount) / 3
        amount = random.uniform(min_amount, min_amount + range_third)
    else:
        # Grosse transaction (dans les deux tiers superieurs)
        range_third = (max_amount - min_amount) / 3
        amount = random.uniform(min_amount + range_third, max_amount)
    
    # Arrondir au centime
    amount = round(amount, 2)
    
    return amount

def generate_transaction(transaction_date):
    """Genere une transaction complete"""
    category = select_category()
    description = random.choice(CATEGORIES[category]["descriptions"])
    amount = generate_amount(category)
    
    return {
        "date": transaction_date.isoformat(),
        "description": description,
        "amount": amount,
        "category": category
    }

# ============================================
#              GENERATION PRINCIPALE
# ============================================

def generate_transactions():
    """Genere toutes les transactions selon la distribution temporelle"""
    
    print("=" * 60)
    print("GENERATION DE TRANSACTIONS CSV")
    print("=" * 60)
    print(f"Date d'execution : {TODAY.isoformat()}")
    print(f"Periode : {START_DATE.isoformat()} -> {END_DATE.isoformat()}")
    print(f"Nombre de transactions : {TOTAL_TRANSACTIONS}")
    print()
    
    # Calculer distribution
    date_ranges = calculate_date_distribution()
    
    # Distribution temporelle
    num_old = int(TOTAL_TRANSACTIONS * 0.25)  # 25% annee ancienne
    num_recent = int(TOTAL_TRANSACTIONS * 0.35)  # 35% annee recente (hors 3 derniers mois)
    num_very_recent = TOTAL_TRANSACTIONS - num_old - num_recent  # 40% des 3 derniers mois
    
    print("Distribution temporelle :")
    print(f"   - {START_DATE.isoformat()} -> {date_ranges['old_period'][1].isoformat()} : {num_old} transactions (25%)")
    print(f"   - {date_ranges['recent_period'][0].isoformat()} -> {date_ranges['recent_period'][1].isoformat()} : {num_recent} transactions (35%)")
    print(f"   - {date_ranges['very_recent_period'][0].isoformat()} -> {TODAY.isoformat()} : {num_very_recent} transactions (40%)")
    print()
    
    transactions = []
    
    # Generer transactions anciennes (25%)
    for _ in range(num_old):
        tx_date = generate_random_date(*date_ranges["old_period"])
        transactions.append(generate_transaction(tx_date))
    
    # Generer transactions recentes (35%)
    for _ in range(num_recent):
        tx_date = generate_random_date(*date_ranges["recent_period"])
        transactions.append(generate_transaction(tx_date))
    
    # Generer transactions tres recentes (40%)
    for _ in range(num_very_recent):
        tx_date = generate_random_date(*date_ranges["very_recent_period"])
        transactions.append(generate_transaction(tx_date))
    
    # Trier par date
    transactions.sort(key=lambda x: x["date"])
    
    return transactions

# ============================================
#              STATISTIQUES
# ============================================

def display_statistics(transactions):
    """Affiche les statistiques des transactions generees"""
    
    print("=" * 60)
    print("STATISTIQUES")
    print("=" * 60)
    
    # Stats par categorie
    category_stats = defaultdict(lambda: {"count": 0, "total": 0})
    
    for tx in transactions:
        cat = tx["category"]
        category_stats[cat]["count"] += 1
        category_stats[cat]["total"] += tx["amount"]
    
    print("\nPar categorie :")
    print(f"{'Categorie':<20} {'Nombre':<10} {'Total':<15} {'Moyenne':<15}")
    print("-" * 60)
    
    for cat in sorted(category_stats.keys()):
        count = category_stats[cat]["count"]
        total = category_stats[cat]["total"]
        avg = total / count if count > 0 else 0
        
        print(f"{cat:<20} {count:<10} {total:>12.2f} EUR {avg:>12.2f} EUR")
    
    # Stats globales
    total_amount = sum(tx["amount"] for tx in transactions)
    
    print("\nMontants :")
    print(f"   - Total depenses : {total_amount:,.2f} EUR")
    print(f"   - Depense moyenne : {total_amount / len(transactions):,.2f} EUR")
    
    # Stats par periode
    print("\nPar periode :")
    
    date_ranges = calculate_date_distribution()
    
    for period_name, (start, end) in [
        ("Ancienne (25%)", date_ranges["old_period"]),
        ("Recente (35%)", date_ranges["recent_period"]),
        ("Tres recente (40%)", date_ranges["very_recent_period"])
    ]:
        count = sum(1 for tx in transactions if start <= date.fromisoformat(tx["date"]) <= end)
        period_total = sum(tx["amount"] for tx in transactions if start <= date.fromisoformat(tx["date"]) <= end)
        print(f"   - {period_name} : {count} transactions - {period_total:,.2f} EUR")
    
    # Repartition montants
    small = sum(1 for tx in transactions if 0 < tx["amount"] <= 50)
    medium = sum(1 for tx in transactions if 50 < tx["amount"] <= 100)
    large = sum(1 for tx in transactions if tx["amount"] > 100)
    
    print("\nRepartition des montants :")
    print(f"   - Petites (5-50 EUR) : {small} transactions ({small/len(transactions)*100:.1f}%)")
    print(f"   - Moyennes (50-100 EUR) : {medium} transactions ({medium/len(transactions)*100:.1f}%)")
    print(f"   - Grosses (>100 EUR) : {large} transactions ({large/len(transactions)*100:.1f}%)")

# ============================================
#              EXPORT CSV
# ============================================

def export_to_csv(transactions, base_filename="transactions_generated.csv"):
    """Exporte les transactions en CSV dans le dossier tests/"""
    import csv
    import os
    from pathlib import Path
    
    # Le script est dans /backend/scripts, on veut aller dans /backend/tests
    script_dir = Path(__file__).resolve().parent
    backend_dir = script_dir.parent
    tests_dir = backend_dir / "tests"
    
    # Créer le dossier tests s'il n'existe pas
    tests_dir.mkdir(exist_ok=True)
    
    # Gestion des doublons : ajouter un numéro si le fichier existe
    base_name = Path(base_filename).stem  # transactions_generated
    extension = Path(base_filename).suffix  # .csv
    
    filename = base_filename
    counter = 1
    full_path = tests_dir / filename
    
    while full_path.exists():
        filename = f"{base_name}_{counter}{extension}"
        full_path = tests_dir / filename
        counter += 1
    
    # Écrire le CSV
    with open(full_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['date', 'description', 'amount', 'category']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for tx in transactions:
            writer.writerow(tx)
    
    print("\n" + "=" * 60)
    print(f"EXPORT REUSSI : {full_path}")
    print(f"{len(transactions)} transactions generees")
    print("=" * 60)

# ============================================
#              MAIN
# ============================================

if __name__ == "__main__":
    # Generer transactions
    transactions = generate_transactions()
    
    # Afficher statistiques
    display_statistics(transactions)
    
    # Exporter en CSV
    export_to_csv(transactions)
    
    print("\nScript termine avec succes !")
