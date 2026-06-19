.PHONY: install migrate collectstatic deploy rollback backup restore

# Variables
DOCKER_COMPOSE = docker compose
MANAGE = .venv\Scripts\python manage.py

# Installation
install:
	pip install -r requirements.txt
	pip install -r requirements.lock

# Database
migrate:
	$(MANAGE) migrate --run-syncdb

migrate-check:
	$(MANAGE) migrate --check

# Static files
collectstatic:
	$(MANAGE) collectstatic --noinput

# Docker
up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

build:
	$(DOCKER_COMPOSE) build

# Full deployment
deploy: migrate collectstatic
	$(DOCKER_COMPOSE) up -d --build web celery

# Rollback
rollback:
	@echo "Stopping current services..."
	$(DOCKER_COMPOSE) down
	@echo "Reverting to previous Docker image tag..."
	$(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d

# Backup
backup:
	@echo "Creating database backup..."
	docker exec jarvisproject-db-1 pg_dump -U postgres jarvis > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created."

# Test
test:
	$(MANAGE) test apps.accounts apps.userprofile

check:
	$(MANAGE) check

# Frontend (Tailwind CSS + DaisyUI)
css-dev:
	npx tailwindcss -i static/css/tailwind-input.css -o static/css/tailwind.css --watch

css-build:
	npx tailwindcss -i static/css/tailwind-input.css -o static/css/tailwind.css --minify

# All-in-one dev
dev: css-dev &
	$(MANAGE) runserver

# Note: On Windows, `make` may need Chocolatey (choco install make) or WSL.
# Without make, use the .bat wrappers or run commands directly.
