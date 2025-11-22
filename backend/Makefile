.PHONY: install run test lint clean init-db reset-db seed

# Installation des dépendances
install:
	pip install -r requirements.txt

# Lancer l'application
run:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Initialiser la base de données
init-db:
	python scripts/init_db.py

# Réinitialiser la base de données (Attention ça supprime les données)
reset-db:
	python scripts/init_db.py --reset

# Générer des données de test
seed:
	python scripts/generation_csv.py
	# Importer le CSV via l'API ou un script d'import

# Lancer les tests
test:
	pytest tests/ -v --cov=app --cov-report=html

# Linter le code
lint:
	flake8 app/ tests/
	black app/ tests/ --check
	isort app/ tests/ --check

# Formater le code
format:
	black app/ tests/
	isort app/ tests/

# Nettoyer les fichiers temporaires
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# Aide
help:
	@echo "Commandes disponibles :"
	@echo "  make install    - Installer les dépendances"
	@echo "  make run        - Lancer l'application"
	@echo "  make init-db    - Initialiser la base de données"
	@echo "  make reset-db   - Réinitialiser la base de données"
	@echo "  make seed       - Générer des données de test"
	@echo "  make test       - Lancer les tests"
	@echo "  make lint       - Vérifier la qualité du code"
	@echo "  make format     - Formater le code"
	@echo "  make clean      - Nettoyer les fichiers temporaires"