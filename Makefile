.PHONY: help build up down logs clean test docs env

help:
	@echo "Log Management System - Available Commands"
	@echo "=========================================="
	@echo "make env          - Create .env file from .env.example"
	@echo "make build        - Build Docker images"
	@echo "make up           - Start all services"
	@echo "make down         - Stop all services"
	@echo "make logs         - View service logs"
	@echo "make clean        - Remove containers and volumes"
	@echo "make test         - Run tests"
	@echo "make seed-data    - Load sample data"
	@echo "make docs         - Generate API documentation"

env:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ .env file created from .env.example"; \
	else \
		echo "⚠️  .env already exists"; \
	fi

build:
	docker-compose build

up: env
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "📊 Dashboard: http://localhost:3000"
	@echo "📡 API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"

down:
	docker-compose down
	@echo "✅ Services stopped"

logs:
	docker-compose logs -f

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned up"

test:
	docker-compose exec backend pytest -v

seed-data:
	docker-compose exec backend python -m collector.sample_sender

docs:
	@echo "📚 API Documentation available at: http://localhost:8000/docs"

shell-backend:
	docker-compose exec backend bash

shell-postgres:
	docker-compose exec postgres psql -U postgres -d logs_db
