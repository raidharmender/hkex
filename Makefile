.PHONY: help install test test-unit test-bdd lint format clean build run docker-build docker-up docker-down docker-logs

# Default target
help:
	@echo "HKEX Settlement Parser - Available Commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install     Install dependencies using uv"
	@echo "  build       Build the Docker image"
	@echo ""
	@echo "Testing:"
	@echo "  test        Run all tests (unit + BDD)"
	@echo "  test-unit   Run unit tests with pytest"
	@echo "  test-bdd    Run BDD tests with behave"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black and isort"
	@echo ""
	@echo "Docker:"
	@echo "  docker-up   Start all services with Docker Compose"
	@echo "  docker-down Stop all services"
	@echo "  docker-logs Show logs from all services"
	@echo ""
	@echo "Development:"
	@echo "  run         Run the FastAPI application locally"
	@echo "  clean       Clean up temporary files"
	@echo ""

# Installation
install:
	@echo "Installing dependencies with uv..."
	uv pip install -e .
	@echo "Installation complete!"

# Testing
test: test-unit test-bdd
	@echo "All tests completed!"

test-unit:
	@echo "Running unit tests..."
	pytest tests/ -v --tb=short

test-bdd:
	@echo "Running BDD tests..."
	behave features/ --format=pretty

# Code Quality
lint:
	@echo "Running linting checks..."
	flake8 app/ tests/ --max-line-length=88 --ignore=E203,W503
	mypy app/ --ignore-missing-imports

format:
	@echo "Formatting code..."
	black app/ tests/ --line-length=88
	isort app/ tests/ --profile=black --line-length=88

# Docker Commands
docker-build:
	@echo "Building Docker image..."
	docker-compose build

docker-up:
	@echo "Starting services with Docker Compose..."
	docker-compose up -d
	@echo "Services started! Access the API at http://localhost:15001"
	@echo "Swagger docs: http://localhost:15001/docs"

docker-down:
	@echo "Stopping services..."
	docker-compose down

docker-logs:
	@echo "Showing logs from all services..."
	docker-compose logs -f

# Development
run:
	@echo "Starting FastAPI application..."
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# CLI Commands
cli-download:
	@echo "Downloading settlement data for 2023-08-22..."
	python -m app.cli download 2023-08-22

cli-search-hti:
	@echo "Searching for HTI symbol..."
	python -m app.cli search HTI --date 2023-08-22

cli-health:
	@echo "Checking system health..."
	python -m app.cli health

cli-list-dates:
	@echo "Listing available trading dates..."
	python -m app.cli list-dates

# Cleanup
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	@echo "Cleanup complete!"

# Database setup
setup-databases:
	@echo "Setting up databases..."
	@echo "This will be handled automatically by Docker Compose"
	@echo "Run 'make docker-up' to start all services"

# Quick start
quick-start: install docker-up
	@echo "Quick start complete!"
	@echo "API is available at: http://localhost:15001"
	@echo "Swagger docs: http://localhost:15001/docs"
	@echo "Try: make cli-download"

# Production build
production-build:
	@echo "Building production Docker image..."
	docker build -t hkex-settlement-parser:latest .
	@echo "Production build complete!"

# Health check
health-check:
	@echo "Checking all services..."
	@echo "FastAPI:"
	curl -s http://localhost:15001/health | jq . || echo "FastAPI not responding"
	@echo "Redis:"
	docker-compose exec redis redis-cli ping || echo "Redis not responding"
	@echo "InfluxDB:"
	curl -s http://localhost:15003/health || echo "InfluxDB not responding"
	@echo "Cassandra:"
	docker-compose exec cassandra cqlsh -e "SELECT release_version FROM system.local;" || echo "Cassandra not responding"
