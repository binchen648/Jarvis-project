#!/bin/bash
# Jarvis Production Deployment Script
set -euo pipefail

echo "=== Jarvis Deployment ==="

echo "Step 1: Running database migrations..."
.venv/bin/python manage.py migrate --run-syncdb

echo "Step 2: Collecting static files..."
.venv/bin/python manage.py collectstatic --noinput

echo "Step 3: Building and starting services..."
docker compose -f docker-compose.prod.yml up -d --build

echo "Step 4: Checking health..."
sleep 5
curl -f http://localhost:8000/health/ || {
    echo "Health check failed!"
    exit 1
}

echo "=== Deployment complete ==="
