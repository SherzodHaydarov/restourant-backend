.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrations

help:
	@echo "Restaurant Backend - Available commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install          Install dependencies"
	@echo "  make requirements      Generate requirements.txt"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Run development server"
	@echo "  make init-db          Initialize database"
	@echo "  make create-data      Create default data"
	@echo "  make reset-db         Reset database"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo "  make lint             Run linting (flake8)"
	@echo "  make format           Format code with black"
	@echo "  make type-check       Run type checking (mypy)"
	@echo ""
	@echo "Database:"
	@echo "  make migrations       Create new migration"
	@echo "  make migrate          Apply migrations"
	@echo "  make downgrade        Downgrade migrations"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-up        Start all services"
	@echo "  make docker-down      Stop all services"
	@echo "  make docker-logs      View Docker logs"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Remove generated files"
	@echo "  make shell            Open Python shell"
	@echo ""

install:
	pip install -r requirements.txt
	pip install -e .

requirements:
	pip freeze > requirements.txt

dev:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

init-db:
	python manage.py init

create-data:
	python manage.py create-data

reset-db:
	python manage.py reset

test:
	pytest -v

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

lint:
	flake8 app tests --max-line-length=100

format:
	black app tests

type-check:
	mypy app --ignore-missing-imports

migrations:
	alembic revision --autogenerate -m "$(message)"

migrate:
	alembic upgrade head

downgrade:
	alembic downgrade -1

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Services starting. Check logs with: make docker-logs"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info

shell:
	python -i -c "from app.core.database import *; from app.models.models import *; import asyncio"
