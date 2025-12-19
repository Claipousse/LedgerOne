.PHONY: install run-backend run-frontend test lint clean init-db reset-db seed help format

# Installation des dépendances
install:
	python -m pip install -r requirements.txt

# Lancer backend
run-backend:
	@echo "Backend demarre sur http://localhost:8000"
	@echo "Documentation: http://localhost:8000/docs"
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Lancer frontend
run-frontend:
	@echo "Frontend demarre sur http://localhost:8080"
	cd ../frontend && python -m http.server 8080

# Initialiser la base de données
init-db:
	python scripts/init_db.py

# Réinitialiser la base de données (Attention ça supprime les données)
reset-db:
	python scripts/init_db.py --reset

# Générer des données de test
seed:
	@echo "Generation de donnees de test..."
	python scripts/generation_csv.py
	@echo ""
	@echo "=========================================="
	@echo "Fichier CSV genere dans /backend/tests"
	@echo "Pour importer les donnees:"
	@echo "  1. Lancer le backend (make run-backend)"
	@echo "  2. Aller sur http://localhost:8080/import.html"
	@echo "  3. Uploader le fichier transactions_generated.csv"
	@echo "=========================================="

# Lancer les tests
test:
	python -m pytest tests/ -v --cov=app --cov-report=html

# Linter le code
lint:
	python -m flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203,W503
	python -m black app/ tests/ --check
	python -m isort app/ tests/ --check-only

# Formater le code
format:
	python -m black app/ tests/
	python -m isort app/ tests/

# Nettoyer les fichiers temporaires (compatible Windows)
clean:
	@echo "Nettoyage des fichiers temporaires..."
	@if exist __pycache__ rd /s /q __pycache__
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
	@if exist .pytest_cache rd /s /q .pytest_cache
	@if exist htmlcov rd /s /q htmlcov
	@if exist .coverage del /q .coverage
	@echo "Nettoyage termine"

# Aide
help:
	@echo "Commandes disponibles :"
	@echo "  make install      - Installer les dependances"
	@echo "  make run-backend  - Lancer le backend"
	@echo "  make run-frontend - Lancer le frontend"
	@echo "  make init-db      - Initialiser la base de donnees"
	@echo "  make reset-db     - Reinitialiser la base de donnees"
	@echo "  make seed         - Generer des donnees de test"
	@echo "  make test         - Lancer les tests"
	@echo "  make lint         - Verifier la qualite du code"
	@echo "  make format       - Formater le code"
	@echo "  make clean        - Nettoyer les fichiers temporaires"