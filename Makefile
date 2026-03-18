.PHONY: help install dev test lint format clean docker-up docker-down

help:
	@echo "Policy-Aware AI Gateway - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies"
	@echo "  make dev              Run development server"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linter (flake8)"
	@echo "  make format           Format code (black)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker images"
	@echo "  make docker-up        Start containers"
	@echo "  make docker-down      Stop containers"
	@echo "  make docker-logs      View container logs"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts and cache"

install:
	cd backend && pip install -r requirements.txt

dev:
	cd backend && python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	cd backend && python -m pytest tests/ -v

test-cov:
	cd backend && python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

lint:
	cd backend && python -m flake8 src/ tests/ --max-line-length=100

format:
	cd backend && python -m black src/ tests/

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f gateway

docker-test:
	docker-compose run gateway python -m pytest tests/ -v

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -delete
	find . -type d -name '.coverage' -delete
	find . -type d -name 'htmlcov' -delete
	rm -rf build/ dist/ *.egg-info
