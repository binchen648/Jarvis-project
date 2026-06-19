#!/bin/bash
# Jarvis Rollback Script
set -euo pipefail

echo "=== Jarvis Rollback ==="

IMAGE_NAME="jarvis-app"
PREVIOUS_TAG="${1:-previous}"
CURRENT_TAG="${2:-latest}"

echo "Step 1: Stopping current services..."
docker compose -f docker-compose.prod.yml down

echo "Step 2: Rolling back to image '${IMAGE_NAME}:${PREVIOUS_TAG}'..."
export JARVIS_IMAGE_TAG="${PREVIOUS_TAG}"
docker compose -f docker-compose.prod.yml up -d

echo "Step 3: Checking health..."
sleep 10
curl -sf http://localhost:8000/health/ && echo " Health check passed" || {
    echo " ERROR: Health check failed! Rolling forward again..."
    docker compose -f docker-compose.prod.yml down
    export JARVIS_IMAGE_TAG="${CURRENT_TAG}"
    docker compose -f docker-compose.prod.yml up -d
    exit 1
}

echo "=== Rollback to ${PREVIOUS_TAG} complete ==="
