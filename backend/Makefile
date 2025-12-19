.PHONY: install run test lint clean init-db reset-db seed help run-backend run-frontend

# Installation des dépendances
install:
	pip install -r requirements.txt

# Lancer l'application
run:
	@echo "Backend  : http://localhost:8000/docs"
	@echo "Frontend : http://localhost:8080"
	@$(MAKE) -j2 run-backend run-frontend

# Lancer uniquement le backend
run-backend:
	@echo "Backend demarre sur http://localhost:8000"
	@python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Lancer uniquement le frontend
run-frontend:
	@echo "Frontend demarre sur http://localhost:8080"
	@cd ../frontend && python -m http.server 8080

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
	@echo "  make install      - Installer les dependances"
	@echo "  make run          - Lancer backend + frontend"
	@echo "  make run-backend  - Lancer uniquement le backend"
	@echo "  make run-frontend - Lancer uniquement le frontend"
	@echo "  make init-db      - Initialiser la base de donnees"
	@echo "  make reset-db     - Reinitialiser la base de donnees"
	@echo "  make seed         - Generer des donnees de test"
	@echo "  make test         - Lancer les tests"
	@echo "  make lint         - Verifier la qualite du code"
	@echo "  make format       - Formater le code"
	@echo "  make clean        - Nettoyer les fichiers temporaires"